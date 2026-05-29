import json
import os
from datetime import datetime
import httpx

from .config import get_active_llm
from .inquiry_engine import InquiryEngine
from prompts.templates import get_prompt, PROMPTS

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class TCMEngine:
    def __init__(self):
        self.season_weights = self._load_json("season_weights.json")
        self.shichen_map = self._load_json("shichen_map.json")

    def _load_json(self, filename: str) -> dict:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    async def analyze(self, session: dict) -> dict:
        locale = session.get("locale", "zh")
        prompt = self._build_analysis_prompt(session, locale)
        result = await self._call_llm(prompt, locale)
        return result

    def _build_analysis_prompt(self, session: dict, locale: str) -> str:
        messages_summary = self._format_messages(session.get("messages", []), locale)
        season = session.get("season", "Unknown" if locale == "en" else "未知")
        region = session.get("region", "Unknown" if locale == "en" else "未知")
        age = session.get("age", "Unknown" if locale == "en" else "未知")
        gender = session.get("gender", "Unknown" if locale == "en" else "未知")
        tongue_desc = session.get("tongue_desc", "Not provided" if locale == "en" else "未提供")

        season_info = self.season_weights.get(season, {})
        season_note = ""
        if season_info and locale == "zh":
            season_note = f"当令脏腑：{season_info.get('organ', '未知')}，多见证型：{season_info.get('common_patterns', '未知')}，用药注意：{season_info.get('caution', '未知')}"
        elif season_info and locale == "en":
            season_note = f"Dominant organ: {season_info.get('organ', 'Unknown')}, Common patterns: {season_info.get('common_patterns', 'Unknown')}, Caution: {season_info.get('caution', 'Unknown')}"

        base_prompt = get_prompt(locale, "tcm_diagnosis",
            season=season,
            solar_term="",
            region=region,
            chief_complaint=messages_summary,
            inquiry_summary=messages_summary,
            tongue_desc=tongue_desc,
            symptom_time=session.get('inquiry_data', {}).get('symptom_time', 'Not provided' if locale == 'en' else '未提供'),
        )

        output_format_zh = """【输出格式】请严格按以下JSON格式输出：
{
    "syndrome": {
        "primary": "主证名称",
        "secondary": "兼证名称",
        "confidence": 0.85
    },
    "bagang": {
        "yin_yang": "阴/阳",
        "biao_li": "表/里",
        "han_re": "寒/热",
        "xu_shi": "虚/实"
    },
    "zangfu": "病位脏腑",
    "special_system": "专项辨证体系及结果",
    "etiology": "病因病机分析",
    "treatment_principle": "治则治法",
    "prescription": {
        "decoction": "汤剂方名及组成",
        "patent_medicine": "中成药推荐",
        "diet_therapy": "食疗/代茶饮推荐",
        "safety_level": "green/yellow/red"
    },
    "lifestyle": {
        "diet": "饮食建议",
        "sleep": "作息建议",
        "emotion": "情志调节"
    },
    "confidence_level": "green/yellow/red",
    "disclaimer": "建议结合中医师面诊确认"
}"""

        output_format_en = """[Output Format] Please output strictly in the following JSON format:
{
    "syndrome": {
        "primary": "Primary syndrome name",
        "secondary": "Secondary syndrome name",
        "confidence": 0.85
    },
    "bagang": {
        "yin_yang": "Yin/Yang",
        "biao_li": "Interior/Exterior",
        "han_re": "Cold/Hot",
        "xu_shi": "Deficiency/Excess"
    },
    "zangfu": "Affected Zang-Fu organs",
    "special_system": "Specialized system and result",
    "etiology": "Etiology and pathogenesis analysis",
    "treatment_principle": "Treatment principle",
    "prescription": {
        "decoction": "Decoction formula and ingredients",
        "patent_medicine": "Patent medicine recommendation",
        "diet_therapy": "Diet therapy / Tea recommendation",
        "safety_level": "green/yellow/red"
    },
    "lifestyle": {
        "diet": "Diet advice",
        "sleep": "Sleep advice",
        "emotion": "Emotional regulation"
    },
    "confidence_level": "green/yellow/red",
    "disclaimer": "Please confirm with a licensed TCM practitioner"
}"""

        context_section = ""
        if season_note:
            if locale == "zh":
                context_section = f"\n当前季节：{season}，{season_note}"
            else:
                context_section = f"\nCurrent season: {season}. {season_note}"

        user_info = ""
        if locale == "zh":
            user_info = f"\n用户地区：{region}\n用户年龄：{age}，性别：{gender}"
        else:
            user_info = f"\nUser region: {region}\nUser age: {age}, Gender: {gender}"

        four_diag = ""
        if locale == "zh":
            four_diag = f"\n【四诊信息】\n问诊摘要：{messages_summary}\n舌象：{tongue_desc}"
        else:
            four_diag = f"\n[Four Diagnostic Methods]\nInquiry summary: {messages_summary}\nTongue: {tongue_desc}"

        output_fmt = output_format_en if locale == "en" else output_format_zh

        return base_prompt + context_section + user_info + four_diag + "\n\n" + output_fmt

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

    async def _call_llm(self, prompt: str, locale: str) -> dict:
        llm = get_active_llm("deepseek")
        api_key = llm["api_key"]
        api_url = llm["api_url"]
        provider = llm["provider"]

        err_not_configured = "LLM API Key not configured. Please configure it in settings." if locale == "en" else "LLM API Key 未配置，请在设置中配置"
        err_connect = "Cannot connect to API server. Check network and API URL." if locale == "en" else "无法连接到 API 服务器，请检查网络和 API 地址"
        err_timeout = "API request timed out. Please try again later." if locale == "en" else "API 请求超时，请稍后重试"
        parse_failed_primary = "Parse failed" if locale == "en" else "解析失败"
        confirm_disclaimer = "Please confirm with a licensed TCM practitioner" if locale == "en" else "建议结合中医师面诊确认"

        if provider is None or not api_key:
            return self._error_result(err_not_configured, locale)

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
                "max_tokens": 2000,
            }
        else:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            payload = {
                "model": llm["model"],
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code != 200:
                    try:
                        err = response.json().get("error", {}).get("message", response.text[:200])
                    except Exception:
                        err = response.text[:200]
                    api_failed = f"API request failed [{response.status_code}]: {err}" if locale == "en" else f"API 请求失败 [{response.status_code}]：{err}"
                    return self._error_result(api_failed, locale)
                result = response.json()

                if provider == "deepseek":
                    content = result["choices"][0]["message"]["content"]
                else:
                    content = result["content"][0]["text"]

                try:
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    return json.loads(content.strip())
                except (json.JSONDecodeError, KeyError, IndexError):
                    return {
                        "syndrome": {"primary": parse_failed_primary, "secondary": "", "confidence": 0},
                        "bagang": {"yin_yang": "-", "biao_li": "-", "han_re": "-", "xu_shi": "-"},
                        "zangfu": "-",
                        "special_system": "-",
                        "etiology": content,
                        "treatment_principle": "-",
                        "prescription": {"decoction": "", "patent_medicine": "", "diet_therapy": "", "safety_level": "red"},
                        "lifestyle": {"diet": "", "sleep": "", "emotion": ""},
                        "confidence_level": "red",
                        "disclaimer": confirm_disclaimer,
                    }
        except httpx.ConnectError:
            return self._error_result(err_connect, locale)
        except httpx.TimeoutException:
            return self._error_result(err_timeout, locale)
        except Exception as e:
            err_msg = f"Request error: {type(e).__name__} - {str(e)[:100]}" if locale == "en" else f"请求异常：{type(e).__name__} - {str(e)[:100]}"
            return self._error_result(err_msg, locale)

    @staticmethod
    def _error_result(msg: str, locale: str) -> dict:
        pending = "Pending analysis" if locale == "en" else "待分析"
        confirm = "Please confirm with a licensed TCM practitioner" if locale == "en" else "建议结合中医师面诊确认"
        return {
            "syndrome": {"primary": pending, "secondary": "", "confidence": 0},
            "bagang": {"yin_yang": "-", "biao_li": "-", "han_re": "-", "xu_shi": "-"},
            "zangfu": "-",
            "special_system": "-",
            "etiology": msg,
            "treatment_principle": "-",
            "prescription": {"decoction": "", "patent_medicine": "", "diet_therapy": "", "safety_level": "red"},
            "lifestyle": {"diet": "", "sleep": "", "emotion": ""},
            "confidence_level": "red",
            "disclaimer": confirm,
        }
