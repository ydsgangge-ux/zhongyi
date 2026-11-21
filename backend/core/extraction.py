"""问诊文本 → 结构化字段抽取。

安全过滤（孕产、经期、生育需求、既往用药）依赖这些字段，因此每轮问诊结束后
做一次轻量抽取，把用户口述的信息回填到会话里；分析前若尚未抽取则再补一次。
抽取失败不影响问诊主流程。
"""

import json
import logging
from typing import Optional

import httpx

from .config import get_active_llm

logger = logging.getLogger(__name__)

EXTRACTION_MAX_TOKENS = 800
EXTRACTION_TIMEOUT = 30.0

_EMPTY_VALUES = {"", "null", "none", "undefined", "未提及", "未知", "不清楚", "unknown", "n/a"}


def _clean_text(value) -> Optional[str]:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or value.lower() in _EMPTY_VALUES:
        return None
    return value


def _normalize_pregnancy(raw) -> Optional[str]:
    """把各种口述归一化为安全模式使用的枚举值。"""
    text = _clean_text(raw)
    if not text:
        return None
    t = text.lower()

    if any(k in t for k in ("哺乳", "喂奶", "母乳", "breastfeed", "nursing", "lactat")):
        return "breastfeeding"

    pregnancy_words = ("已孕", "怀孕", "怀了", "妊娠", "孕早期", "孕中", "孕晚", "早孕",
                       "pregnan", "expecting")
    if any(k in t for k in pregnancy_words):
        # 孕周不明或中晚期均按最严格模式处理
        if any(k in t for k in ("中", "晚", "5个月", "6个月", "7个月", "8个月", "9个月",
                                "second trimester", "third trimester")):
            return "pregnant_late"
        return "pregnant_early"

    if any(k in t for k in ("备孕", "准备怀", "计划怀", "想要孩子", "trying to conceive", "planning")):
        return "planning_pregnancy"

    if any(k in t for k in ("无", "没有", "否", "不需要", "no", "none", "not ")):
        return "none"

    return None


def merge_structured_fields(session: dict, data: dict) -> None:
    """只覆盖有值字段，避免抽取结果把已知信息清空。"""
    if not isinstance(data, dict):
        return

    inquiry = session.setdefault("inquiry_data", {})

    chief = _clean_text(data.get("chief_complaint"))
    if chief:
        inquiry["chief_complaint"] = chief
        session["chief_complaint"] = chief

    symptom_time = _clean_text(data.get("symptom_time"))
    if symptom_time:
        inquiry["symptom_time"] = symptom_time
        session["symptom_time"] = symptom_time

    tongue = _clean_text(data.get("tongue_desc"))
    if tongue:
        inquiry["tongue_desc"] = tongue
        session["tongue_desc"] = tongue

    if session.get("gender") == "女":
        pregnancy = _normalize_pregnancy(data.get("pregnancy_status"))
        if pregnancy:
            session["pregnancy_status"] = pregnancy

        menstrual = data.get("menstrual")
        if isinstance(menstrual, dict):
            target = session.setdefault("menstrual_data", {})
            for key in ("lmp", "cycle", "flow", "color", "symptoms", "leukorrhea"):
                value = _clean_text(menstrual.get(key))
                if value:
                    target[key] = value
            if isinstance(menstrual.get("is_menstruating"), bool):
                target["is_menstruating"] = menstrual["is_menstruating"]

    if session.get("gender") == "男" and isinstance(data.get("male_fertility_need"), bool):
        session["male_fertility_need"] = data["male_fertility_need"]

    for key in ("medications", "allergies", "past_history"):
        value = _clean_text(data.get(key))
        if value:
            session[key] = value


def compute_completeness(session: dict) -> float:
    """按已采集关键字段计算客观信息完整度，用于压制 LLM 自报置信度。"""
    inquiry = session.get("inquiry_data") or {}
    checks = [
        bool(inquiry.get("chief_complaint")),
        bool(inquiry.get("symptom_time")),
        bool(session.get("tongue_desc") or inquiry.get("tongue_desc")),
        bool(session.get("medications")),
        bool(session.get("allergies")),
        bool(session.get("past_history")),
    ]
    if session.get("gender") == "女":
        checks.append(bool(session.get("pregnancy_status")))
        checks.append(bool(session.get("menstrual_data")))
    elif session.get("gender") == "男":
        checks.append(session.get("male_fertility_need") is not None)

    if not checks:
        return 0.0
    return round(sum(1 for c in checks if c) / len(checks), 2)


def _format_history(session: dict) -> str:
    lines = []
    for msg in (session.get("messages") or [])[-20:]:
        role = "用户" if msg.get("role") == "user" else "顾问"
        lines.append(f"{role}：{msg.get('content', '')}")
    return "\n".join(lines)


def _build_extraction_prompt(session: dict) -> str:
    return f"""你是一个中医问诊信息抽取器。请从下面的对话中抽取结构化信息。

【输出格式】只输出 JSON，不要任何解释或代码块标记：
{{
  "chief_complaint": "最主要的不适及持续时间；未提及填 null",
  "symptom_time": "症状加重/缓解的时间规律或时辰；未提及填 null",
  "tongue_desc": "舌质、舌苔、舌体的描述；未提及填 null",
  "pregnancy_status": "备孕中/孕早期/孕中晚期/哺乳期/无；未提及或不明确填 null",
  "menstrual": {{
    "lmp": "末次月经时间；未提及填 null",
    "cycle": "规律/提前/推后/不规律；未提及填 null",
    "flow": "多/正常/少/闭经；未提及填 null",
    "color": "经色，如鲜红/暗红/淡红/有血块；未提及填 null",
    "symptoms": "痛经/腰酸/乳胀/情绪变化等；未提及填 null",
    "is_menstruating": "true 表示当前正在经期，false 表示不是，不确定填 null"
  }},
  "male_fertility_need": "男性是否明确表示有生育需求：true/false，未提及填 null",
  "medications": "长期服用的药物，包括西药和中药；未提及填 null",
  "allergies": "药物或食物过敏史；未提及填 null",
  "past_history": "重要既往疾病或手术史；未提及填 null"
}}

【规则】
- 只抽取用户明确表达过的信息，禁止推测或补全
- 用户明确否认（如"没有""无"）时，该字段填"无"，不要填 null
- 不要因为性别而编造月经或生育信息

【对话】
{_format_history(session)}
"""


async def _call_llm(prompt: str) -> Optional[dict]:
    llm = get_active_llm("deepseek")
    provider = llm.get("provider")
    api_key = llm.get("api_key")
    if not provider or not api_key:
        return None

    if provider == "deepseek":
        from .inquiry_engine import InquiryEngine
        api_url = InquiryEngine._fix_api_url(llm["api_url"])
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": llm["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": min(int(llm.get("max_tokens") or 0) or EXTRACTION_MAX_TOKENS, EXTRACTION_MAX_TOKENS),
        }
    else:
        api_url = llm["api_url"]
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": llm["model"],
            "max_tokens": EXTRACTION_MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }

    async with httpx.AsyncClient(timeout=EXTRACTION_TIMEOUT) as client:
        response = await client.post(api_url, headers=headers, json=payload)
        if response.status_code != 200:
            logger.warning("结构化抽取请求失败 status=%s", response.status_code)
            return None
        result = response.json()

    if provider == "deepseek":
        content = result["choices"][0]["message"]["content"]
    else:
        content = result["content"][0]["text"]

    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    parsed = json.loads(content.strip())
    return parsed if isinstance(parsed, dict) else None


async def extract_structured_fields(session: dict) -> bool:
    """抽取并合并字段，成功返回 True。"""
    if not session.get("messages"):
        return False
    try:
        data = await _call_llm(_build_extraction_prompt(session))
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        logger.warning("结构化抽取解析失败 session=%s", session.get("session_id"))
        return False
    except httpx.TimeoutException:
        logger.warning("结构化抽取超时 session=%s", session.get("session_id"))
        return False
    except Exception:
        logger.exception("结构化抽取异常 session=%s", session.get("session_id"))
        return False

    if not data:
        return False

    merge_structured_fields(session, data)
    session["field_extract_turn"] = _user_turns(session)
    return True


def _user_turns(session: dict) -> int:
    return sum(1 for m in session.get("messages", []) if m.get("role") == "user")


async def ensure_structured_fields(session: dict) -> None:
    """分析前兜底：本轮对话还没抽取过就补一次。"""
    if session.get("field_extract_turn") == _user_turns(session):
        return
    await extract_structured_fields(session)
