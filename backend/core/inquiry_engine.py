import asyncio
import json
import os
import logging
from datetime import date, datetime
from typing import Optional
import httpx

from .config import get_deepseek_config, get_active_llm
from prompts.templates import get_prompt, PROMPTS
from models.database import save_session, load_session
from .extraction import extract_structured_fields
from .gender_differentiation import (
    calc_physiological_stage,
    get_round0_intro,
    STAGE_LABELS,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

SESSION_TTL_HOURS = 24
ROUND0_MIN_TURNS = 2
ROUND0_MAX_TURNS = 3
logger = logging.getLogger(__name__)

# 二十四节气（近似日期），用于辨证 prompt 的时空背景
SOLAR_TERMS = [
    (1, 6, "小寒"), (1, 20, "大寒"), (2, 4, "立春"), (2, 19, "雨水"),
    (3, 6, "惊蛰"), (3, 21, "春分"), (4, 5, "清明"), (4, 20, "谷雨"),
    (5, 6, "立夏"), (5, 21, "小满"), (6, 6, "芒种"), (6, 21, "夏至"),
    (7, 7, "小暑"), (7, 23, "大暑"), (8, 8, "立秋"), (8, 23, "处暑"),
    (9, 8, "白露"), (9, 23, "秋分"), (10, 8, "寒露"), (10, 23, "霜降"),
    (11, 7, "立冬"), (11, 22, "小雪"), (12, 7, "大雪"), (12, 22, "冬至"),
]


def get_current_solar_term() -> str:
    today = date.today()
    current = SOLAR_TERMS[-1][2]
    for month, day, name in SOLAR_TERMS:
        if (today.month, today.day) >= (month, day):
            current = name
        else:
            break
    return current


class InquiryEngine:
    def __init__(self):
        self.sessions = {}
        self.season_weights = self._load_json("season_weights.json")
        self.shichen_map = self._load_json("shichen_map.json")

    def _load_json(self, filename: str) -> dict:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_current_season(self) -> str:
        month = datetime.now().month
        if month in [2, 3, 4]:
            return "春"
        elif month in [5, 6]:
            return "夏"
        elif month in [7, 8]:
            return "长夏"
        elif month in [9, 10, 11]:
            return "秋"
        else:
            return "冬"

    def create_session(
        self,
        session_id: str,
        region: Optional[str] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        birth_year: Optional[int] = None,
        season: Optional[str] = None,
        locale: str = "zh",
    ) -> dict:
        stage = None
        if gender and birth_year:
            stage = calc_physiological_stage(gender, birth_year)

        session = {
            "session_id": session_id,
            "region": region,
            "age": age,
            "gender": gender,
            "birth_year": birth_year,
            "physiological_stage": stage,
            "season": season or self.get_current_season(),
            "locale": locale,
            "round": 0,
            "round_0_done": not bool(gender),
            "round_0_turns": 0,
            "field_extract_turn": 0,
            "solar_term": get_current_solar_term(),
            "messages": [],
            "inquiry_data": {
                "chief_complaint": None,
                "bagang": None,
                "zangfu": None,
                "tongue_desc": None,
                "lifestyle": None,
                "symptom_time": None,
            },
            "chief_complaint": None,
            "symptom_time": None,
            "tongue_desc": None,
            "menstrual_data": {},
            "pregnancy_status": None,
            "male_fertility_need": None,
            "medications": None,
            "allergies": None,
            "past_history": None,
            "created_at": datetime.now().isoformat(),
        }
        self.sessions[session_id] = session
        self.persist_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[dict]:
        session = self.sessions.get(session_id)
        if session:
            if self._is_expired(session):
                self.sessions.pop(session_id, None)
            else:
                return session

        session = load_session(session_id, SESSION_TTL_HOURS)
        if session:
            self.sessions[session_id] = session
        return session

    def persist_session(self, session: dict) -> None:
        try:
            save_session(session)
        except Exception:
            logger.exception("保存会话失败: %s", session.get("session_id"))

    def cleanup_expired(self) -> int:
        expired = [sid for sid, s in self.sessions.items() if self._is_expired(s)]
        for sid in expired:
            self.sessions.pop(sid, None)
        return len(expired)

    @staticmethod
    def _is_expired(session: dict) -> bool:
        created_at = session.get("created_at")
        if not created_at:
            return False
        try:
            age = datetime.now() - datetime.fromisoformat(created_at)
        except ValueError:
            return False
        return age.total_seconds() > SESSION_TTL_HOURS * 3600

    async def process_message(self, session: dict, user_message: str):
        locale = session.get("locale", "zh")
        in_round0 = not session.get("round_0_done") and session.get("gender")

        if in_round0:
            session["round_0_turns"] = session.get("round_0_turns", 0) + 1
            prompt = self._build_round0_prompt(session, user_message, locale)
        else:
            session["round"] += 1
            round_num = session["round"]
            if round_num <= 5:
                prompt = self._build_inquiry_prompt(session, user_message, round_num, locale)
            else:
                prompt = self._build_followup_prompt(session, user_message, locale)

        # 抽取与流式回复并发，用户侧无额外等待
        extract_task = asyncio.create_task(extract_structured_fields(session))

        full_content = ""
        try:
            async for chunk in self._call_llm_stream(prompt):
                full_content += chunk
                yield chunk
        finally:
            await extract_task

        if full_content:
            session["messages"].append({"role": "assistant", "content": full_content})
        if in_round0 and self._round0_complete(session):
            session["round_0_done"] = True
        self.persist_session(session)

    @staticmethod
    def _round0_complete(session: dict) -> bool:
        """基线轮次由字段完整度决定，而不是用户回一条就结束。"""
        turns = session.get("round_0_turns", 0)
        if turns < ROUND0_MIN_TURNS:
            return False
        if turns >= ROUND0_MAX_TURNS:
            return True
        if session.get("gender") == "女":
            # 妊娠状态是安全字段，未明确前不进入主诉轮
            return bool(session.get("pregnancy_status"))
        return session.get("male_fertility_need") is not None

    def _get_locale(self, session: dict) -> str:
        return session.get("locale", "zh")

    def _build_round0_prompt(self, session: dict, user_message: str, locale: str) -> str:
        gender = session.get("gender", "")
        stage = session.get("physiological_stage", "")
        stage_label = STAGE_LABELS.get(locale, STAGE_LABELS["zh"]).get(stage, "") if stage else ""

        if gender == "女":
            round_0_instruction = PROMPTS[locale]["round_0_female"]
            gender_label = {"zh": "女性", "en": "Female"}.get(locale, "Female")
        else:
            round_0_instruction = PROMPTS[locale]["round_0_male"]
            gender_label = {"zh": "男性", "en": "Male"}.get(locale, "Male")

        conversation_history = self._conversation_history(session, locale)

        round_0_template = PROMPTS[locale]["inquiry_rounds"][0]
        round_0_instruction_filled = round_0_template.format(
            gender=gender_label,
            round_0_instruction=round_0_instruction,
        )

        intro_msg = get_round0_intro(locale, gender, stage)
        collected = self._collected_round0_summary(session, locale)
        goal = self._round0_goal(session, locale)

        if locale == "zh":
            prompt = f"""你是一位经验丰富的中医健康顾问，正在进行结构化多轮问诊。

【时空背景】
当前季节：{session['season']}
用户地区：{session.get('region', '未知')}
用户年龄：{session.get('age', '未知')}
用户性别：{gender}，生理阶段：{stage_label}

【开场白】
在回应用户时，请在回复开头使用这段话：
"{intro_msg}"

【当前轮次】第零轮问诊（主诉 + 生理/安全基线）
{round_0_instruction_filled}

【已采集信息】（不要重复询问）
{collected}

【本轮目标】
{goal}

【对话历史】
{conversation_history}

【用户最新回复】
{user_message}

【要求】
- 在你回复的开头包含上面的开场白（可以自然地融入你的话中）
- 只问本轮目标里尚未采集的信息，最多2-3个问题
- 已采集的信息不要重复确认
- 语气温和专业，像有经验的老中医
- 不要给出诊断结论
"""
        else:
            prompt = f"""You are an experienced TCM health advisor conducting a structured multi-round inquiry.

IMPORTANT: You MUST respond in English only. Never use Chinese.

[Context]
Current season: {session['season']}
User region: {session.get('region', 'Unknown')}
User age: {session.get('age', 'Unknown')}
User gender: {gender}, Physiological stage: {stage_label}

[Opening Statement]
At the beginning of your response, use this phrase:
"{intro_msg}"

[Current Round] Round 0 (Chief Complaint + Physiological/Safety Baseline)
{round_0_instruction_filled}

[Collected Information] (do not ask again)
{collected}

[Goal for This Turn]
{goal}

[Conversation History]
{conversation_history}

[User's Latest Response]
{user_message}

[Requirements]
- IMPORTANT: You MUST respond in English only. Never use Chinese.
- Include the opening statement at the beginning of your response (blend it naturally)
- Only ask about the missing items in this turn's goal, at most 2-3 questions
- Do not re-confirm information already collected
- Tone should be warm and professional
- Do not give diagnosis conclusions
"""

        return prompt

    @staticmethod
    def _collected_round0_summary(session: dict, locale: str) -> str:
        inquiry = session.get("inquiry_data") or {}
        menstrual = session.get("menstrual_data") or {}
        items = []
        if inquiry.get("chief_complaint"):
            items.append(f"主诉：{inquiry['chief_complaint']}")
        if session.get("pregnancy_status"):
            labels = {
                "planning_pregnancy": "备孕中",
                "pregnant_early": "孕早期",
                "pregnant_late": "孕中晚期",
                "breastfeeding": "哺乳期",
                "none": "无怀孕/备孕/哺乳",
            }
            items.append(f"孕产状态：{labels.get(session['pregnancy_status'], session['pregnancy_status'])}")
        for key, label in (("lmp", "末次月经"), ("cycle", "周期"), ("flow", "经量"),
                           ("color", "经色"), ("symptoms", "经期症状")):
            if menstrual.get(key):
                items.append(f"{label}：{menstrual[key]}")
        if session.get("male_fertility_need") is not None:
            items.append("生育需求：" + ("有" if session["male_fertility_need"] else "无"))
        if session.get("medications"):
            items.append(f"服药史：{session['medications']}")
        if not items:
            return "暂无"
        return "；".join(items)

    @staticmethod
    def _round0_goal(session: dict, locale: str) -> str:
        inquiry = session.get("inquiry_data") or {}
        # 主诉优先：还不知道哪里不舒服时，先问主诉
        if not inquiry.get("chief_complaint"):
            return "先请用户说明最主要的不适和持续时间（1-2个问题），暂不追问生理基线。"

        if session.get("gender") == "女" and not session.get("pregnancy_status"):
            return ("必须先确认妊娠状态（是否怀孕/备孕/哺乳），这直接决定用药安全；"
                    "确认后再用1-2个问题补充尚未采集的月经信息。")

        if session.get("gender") == "女":
            return "补充尚未采集的月经与带下信息（量/色/伴随症状/带下），已采集的不要重复。"
        return "补充尚未采集的肾系基线（精力、腰膝、睡眠、夜尿、生育需求），已采集的不要重复。"

    def _build_inquiry_prompt(self, session: dict, user_message: str, round_num: int, locale: str) -> str:
        lang_prompts = PROMPTS.get(locale, PROMPTS["zh"])
        round_instruction = lang_prompts["inquiry_rounds"].get(round_num, "")

        conversation_history = self._conversation_history(session, locale)

        return get_prompt(locale, "inquiry_system",
            season=session['season'],
            region=session.get('region', 'Unknown' if locale == 'en' else '未知'),
            age=session.get('age', 'Unknown' if locale == 'en' else '未知'),
            gender=session.get('gender', 'Unknown' if locale == 'en' else '未知'),
            round=round_num,
            round_instruction=round_instruction,
            history=conversation_history,
            user_message=user_message,
        )

    def _build_followup_prompt(self, session: dict, user_message: str, locale: str) -> str:
        conversation_history = self._conversation_history(session, locale)

        return get_prompt(locale, "followup_system",
            season=session['season'],
            history=conversation_history,
            user_message=user_message,
        )

    def _conversation_history(self, session: dict, locale: str) -> str:
        """最新一条用户消息会单独传入，历史里去掉它避免重复。"""
        messages = session["messages"]
        if messages and messages[-1].get("role") == "user":
            messages = messages[:-1]
        return self._format_messages(messages, locale)

    def _format_messages(self, messages: list, locale: str) -> str:
        lang_prompts = PROMPTS.get(locale, PROMPTS["zh"])
        role_user = lang_prompts["role_user"]
        role_advisor = lang_prompts["role_advisor"]

        formatted = []
        for msg in messages[-10:]:
            role = role_user if msg["role"] == "user" else role_advisor
            sep = ": " if locale == "en" else "："
            formatted.append(f"{role}{sep}{msg['content']}")
        return "\n".join(formatted)

    @staticmethod
    def _fix_api_url(url: str) -> str:
        url = url.strip()
        if not url:
            return "https://api.deepseek.com/v1/chat/completions"
        if url.endswith("/v1/chat/completions"):
            return url
        if url.endswith("/v1"):
            return url + "/chat/completions"
        if url.endswith("/"):
            url = url.rstrip("/")
        return url + "/v1/chat/completions"

    async def _call_llm_stream(self, prompt: str):
        llm = get_active_llm("deepseek")
        api_key = llm["api_key"]
        api_url = llm["api_url"]
        provider = llm["provider"]

        if provider is None:
            yield "（DeepSeek / Claude API Key 未配置，请在设置中配置）"
            return

        if provider == "deepseek":
            api_url = self._fix_api_url(api_url)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": llm["model"],
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "temperature": llm["temperature"],
                "max_tokens": llm["max_tokens"],
            }
        else:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            payload = {
                "model": llm["model"],
                "max_tokens": llm["max_tokens"],
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            }

        err_not_configured = "LLM API Key not configured. Please configure it in settings."
        err_connect = "Cannot connect to API server. Check network and API URL."
        err_timeout = "API request timed out. Please try again later."

        if not api_key:
            yield "（DeepSeek / Claude API Key 未配置，请在设置中配置）"
            return

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", api_url, headers=headers, json=payload
                ) as response:
                    if response.status_code != 200:
                        error_body = ""
                        async for chunk in response.aiter_text():
                            error_body += chunk
                        try:
                            err_json = json.loads(error_body)
                            err_msg = err_json.get("error", {}).get("message", error_body[:200])
                        except (json.JSONDecodeError, AttributeError):
                            err_msg = error_body[:200]
                        yield f"（API 请求失败 [{response.status_code}]：{err_msg}）"
                        return

                    full_content = ""
                    if provider == "deepseek":
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    break
                                try:
                                    chunk_data = json.loads(data)
                                    content = chunk_data["choices"][0]["delta"].get("content", "")
                                    if content:
                                        full_content += content
                                        yield content
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    continue
                    else:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                try:
                                    event = json.loads(data)
                                    if event.get("type") == "content_block_delta":
                                        delta = event.get("delta", {})
                                        text = delta.get("text", "")
                                        if text:
                                            full_content += text
                                            yield text
                                    elif event.get("type") == "message_stop":
                                        break
                                except (json.JSONDecodeError, KeyError):
                                    continue

                    if not full_content:
                        yield "（API 返回了空内容，请检查模型名称是否正确）"
        except httpx.ConnectError:
            yield f"（{err_connect}）"
        except httpx.TimeoutException:
            yield f"（{err_timeout}）"
        except Exception as e:
            yield f"（请求异常：{type(e).__name__} - {str(e)[:100]}）"
