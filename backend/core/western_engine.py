import json
import os
import logging
import httpx

from .config import get_active_llm, load_config
from .inquiry_engine import InquiryEngine
from prompts.templates import get_prompt, PROMPTS

# 推理模型的思考过程也计入 max_tokens，需给正文留足额度。
ANALYSIS_MAX_TOKENS = 8000
logger = logging.getLogger(__name__)


class WesternEngine:
    def __init__(self):
        pass

    async def analyze(self, session: dict) -> dict:
        locale = session.get("locale", "zh")
        prompt = self._build_western_prompt(session, locale)
        result = await self._call_llm(prompt)
        return result

    def _build_western_prompt(self, session: dict, locale: str) -> str:
        messages_summary = self._format_messages(session.get("messages", []), locale)
        age = session.get("age", "Unknown" if locale == "en" else "未知")
        gender = session.get("gender", "Unknown" if locale == "en" else "未知")

        base_prompt = get_prompt(locale, "western_reference",
            age=age,
            gender=gender,
            symptoms=messages_summary,
        )

        output_format_zh = """
【危险信号判定规则】
- 只列出用户描述中【已经实际出现】的危险信号，并在 signal 中引用用户的原话要点
- 用户没有描述的危险信号一律不要列出；没有危险信号时必须返回空数组 []
- 不要罗列教科书式的潜在危险清单

【输出格式】请严格按以下JSON格式输出：
{
    "danger_signals": [
        {
            "signal": "危险信号描述",
            "urgency": "high/medium/low",
            "action": "建议行动"
        }
    ],
    "possible_conditions": [
        {
            "condition": "可能疾病名称",
            "probability": "low/medium/high",
            "description": "简要说明"
        }
    ],
    "recommended_tests": [
        {
            "test": "检查项目名称",
            "reason": "检查原因"
        }
    ],
    "doctor_visit": {
        "needed": true/false,
        "urgency": "immediate/soon/routine",
        "department": "建议就诊科室"
    }
}"""

        output_format_en = """
[Danger Signal Rules]
- Only list danger signals that the user has ACTUALLY described, and quote the key user wording in "signal"
- Never list textbook red flags the user did not mention; return an empty array [] when none are present

[Output Format] Please output strictly in the following JSON format:
{
    "danger_signals": [
        {
            "signal": "Danger signal description",
            "urgency": "high/medium/low",
            "action": "Recommended action"
        }
    ],
    "possible_conditions": [
        {
            "condition": "Possible condition name",
            "probability": "low/medium/high",
            "description": "Brief description"
        }
    ],
    "recommended_tests": [
        {
            "test": "Test name",
            "reason": "Reason for test"
        }
    ],
    "doctor_visit": {
        "needed": true/false,
        "urgency": "immediate/soon/routine",
        "department": "Recommended department"
    }
}"""

        output_fmt = output_format_en if locale == "en" else output_format_zh
        return base_prompt + output_fmt

    def _format_messages(self, messages: list, locale: str) -> str:
        lang_prompts = PROMPTS.get(locale, PROMPTS["zh"])
        role_user = lang_prompts["role_user"]
        role_advisor = lang_prompts["role_advisor"]
        sep = ": " if locale == "en" else "："

        formatted = []
        for msg in messages:
            role = role_user if msg["role"] == "user" else role_advisor
            formatted.append(f"{role}{sep}{msg['content']}")
        return "\n".join(formatted)

    async def _call_llm(self, prompt: str) -> dict:
        llm = get_active_llm("claude")
        api_key = llm["api_key"]
        api_url = llm["api_url"]
        provider = llm["provider"]

        if provider is None or not api_key:
            return self._empty_result()

        if provider == "deepseek":
            api_url = InquiryEngine._fix_api_url(api_url)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": llm["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
                "max_tokens": max(int(llm["max_tokens"] or 0), ANALYSIS_MAX_TOKENS),
            }
        else:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            payload = {
                "model": llm["model"],
                "max_tokens": max(int(llm["max_tokens"] or 0), 4000),
                "messages": [{"role": "user", "content": prompt}],
            }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.warning(
                        "西医参考分析请求失败 status=%s body=%s",
                        response.status_code, response.text[:200],
                    )
                    return self._empty_result()
                result = response.json()
                try:
                    if provider == "deepseek":
                        content = result["choices"][0]["message"]["content"]
                    else:
                        content = result["content"][0]["text"]
                    return self._parse_json(content)
                except (json.JSONDecodeError, KeyError, IndexError):
                    logger.warning("西医参考分析结果解析失败: %s", str(result)[:300])
                    return self._empty_result()
        except Exception:
            logger.exception("西医参考分析异常")
            return self._empty_result()

    def _parse_json(self, content: str) -> dict:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())

    def _empty_result(self) -> dict:
        return {
            "danger_signals": [],
            "possible_conditions": [],
            "recommended_tests": [],
            "doctor_visit": {"needed": False, "urgency": "routine", "department": ""},
        }
