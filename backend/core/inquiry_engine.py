import json
import os
from datetime import datetime
from typing import Optional
import httpx

from .config import get_deepseek_config, get_active_llm
from prompts.templates import get_prompt, PROMPTS
from .gender_differentiation import (
    calc_physiological_stage,
    get_round0_intro,
    STAGE_LABELS,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


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
        elif month in [5, 6, 7]:
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
            "messages": [],
            "inquiry_data": {
                "chief_complaint": None,
                "bagang": None,
                "zangfu": None,
                "tongue_desc": None,
                "lifestyle": None,
                "symptom_time": None,
            },
            "tongue_desc": None,
            "menstrual_data": {},
            "pregnancy_status": None,
            "male_fertility_need": False,
            "created_at": datetime.now().isoformat(),
        }
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[dict]:
        return self.sessions.get(session_id)

    async def process_message(self, session: dict, user_message: str):
        locale = session.get("locale", "zh")

        if not session.get("round_0_done") and session.get("gender"):
            prompt = self._build_round0_prompt(session, user_message, locale)
            session["round_0_done"] = True
        else:
            session["round"] += 1
            round_num = session["round"]
            if round_num <= 5:
                prompt = self._build_inquiry_prompt(session, user_message, round_num, locale)
            else:
                prompt = self._build_followup_prompt(session, user_message, locale)

        async for chunk in self._call_llm_stream(prompt):
            session["messages"].append({"role": "assistant", "content": chunk})
            yield chunk

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

        conversation_history = self._format_messages(session["messages"], locale)

        round_0_template = PROMPTS[locale]["inquiry_rounds"][0]
        round_0_instruction_filled = round_0_template.format(
            gender=gender_label,
            round_0_instruction=round_0_instruction,
        )

        intro_msg = get_round0_intro(locale, gender, stage)

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

【当前轮次】第零轮问诊（生理基线采集）
{round_0_instruction_filled}

【对话历史】
{conversation_history}

【用户最新回复】
{user_message}

【要求】
- 在你回复的开头包含上面的开场白（可以自然地融入你的话中）
- 然后根据Round 0的要求，温和地提出2-3个生理基线问题
- 不要跳到后续的主诉追问
- 语气温和专业，像有经验的老中医
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

[Current Round] Round 0 (Physiological Baseline)
{round_0_instruction_filled}

[Conversation History]
{conversation_history}

[User's Latest Response]
{user_message}

[Requirements]
- IMPORTANT: You MUST respond in English only. Never use Chinese.
- Include the opening statement at the beginning of your response (blend it naturally)
- Then, based on Round 0 requirements, gently ask 2-3 physiological baseline questions
- Do not skip ahead to chief complaint follow-up
- Tone should be warm and professional
"""

        return prompt

    def _build_inquiry_prompt(self, session: dict, user_message: str, round_num: int, locale: str) -> str:
        lang_prompts = PROMPTS.get(locale, PROMPTS["zh"])
        round_instruction = lang_prompts["inquiry_rounds"].get(round_num, "")

        conversation_history = self._format_messages(session["messages"], locale)

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
        conversation_history = self._format_messages(session["messages"], locale)

        return get_prompt(locale, "followup_system",
            season=session['season'],
            history=conversation_history,
            user_message=user_message,
        )

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
