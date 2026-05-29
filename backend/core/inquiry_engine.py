import json
import os
from datetime import datetime
from typing import Optional
import httpx

from .config import get_deepseek_config, get_active_llm
from prompts.templates import get_prompt, PROMPTS

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
        season: Optional[str] = None,
        locale: str = "zh",
    ) -> dict:
        session = {
            "session_id": session_id,
            "region": region,
            "age": age,
            "gender": gender,
            "season": season or self.get_current_season(),
            "locale": locale,
            "round": 0,
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
            "created_at": datetime.now().isoformat(),
        }
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[dict]:
        return self.sessions.get(session_id)

    async def process_message(self, session: dict, user_message: str):
        locale = session.get("locale", "zh")
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
