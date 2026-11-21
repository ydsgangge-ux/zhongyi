import json
import logging
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from core.inquiry_engine import InquiryEngine
from core.safety_guard import SafetyGuard

router = APIRouter()
inquiry_engine = InquiryEngine()
safety_guard = SafetyGuard()
logger = logging.getLogger(__name__)

GREETINGS = {
    "zh": "您好，我是中医AI健康顾问。请问您今天哪里不舒服？",
    "en": "Hello, I am your TCM AI health advisor. What brings you here today?",
}

DANGER_MSGS = {
    "zh": "⚠️ 检测到危险信号，已终止辨证。请立即就医！",
    "en": "⚠️ Danger signal detected! Diagnosis terminated. Please seek immediate medical attention!",
}

SESSION_NOT_FOUND = {
    "zh": "会话不存在",
    "en": "Session not found",
}


class SessionStartRequest(BaseModel):
    region: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    locale: str = "zh"


class MessageRequest(BaseModel):
    session_id: str
    message: str


@router.post("/session/start")
async def start_session(req: SessionStartRequest):
    session_id = str(uuid.uuid4())
    season = inquiry_engine.get_current_season()
    locale = req.locale if req.locale in ("zh", "en") else "zh"
    session_data = inquiry_engine.create_session(
        session_id=session_id,
        region=req.region,
        age=req.age,
        gender=req.gender,
        birth_year=req.birth_year,
        season=season,
        locale=locale,
    )
    return {
        "session_id": session_id,
        "season": season,
        "round": 0,
        "greeting": GREETINGS.get(locale, GREETINGS["zh"]),
    }


@router.post("/inquiry/message")
async def send_message(req: MessageRequest):
    session = inquiry_engine.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=SESSION_NOT_FOUND.get("zh"))

    locale = session.get("locale", "zh")

    def danger_response(warning: str):
        payload = json.dumps(
            {
                "danger": True,
                "warning": warning,
                "danger_message": DANGER_MSGS.get(locale, DANGER_MSGS["zh"]),
                "round": session["round"],
            },
            ensure_ascii=False,
        )

        async def danger_stream():
            yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(danger_stream(), media_type="text/event-stream")

    # 已触发危险信号的会话不再继续问诊
    if session.get("danger_signal"):
        return danger_response(session["danger_signal"])

    danger_check = safety_guard.check_danger_signals(req.message, locale)
    if danger_check["dangerous"]:
        logger.warning("检测到危险信号，终止问诊: session=%s", req.session_id)
        session["danger_signal"] = danger_check["warning"]
        inquiry_engine.persist_session(session)
        return danger_response(danger_check["warning"])

    session["messages"].append({"role": "user", "content": req.message})
    inquiry_engine.persist_session(session)

    async def stream_response():
        try:
            async for chunk in inquiry_engine.process_message(session, req.message):
                # JSON 编码后再放进 data 帧，避免文本中的换行破坏 SSE 格式
                yield "data: " + json.dumps({"content": chunk}, ensure_ascii=False) + "\n\n"
        except Exception:
            logger.exception("问诊流式回复异常 session=%s", req.session_id)
            err = "Something went wrong. Please try again." if locale == "en" else "问诊回复生成失败，请重试"
            yield "data: " + json.dumps({"content": f"\n（{err}）"}, ensure_ascii=False) + "\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@router.post("/safety/check")
async def safety_check(message: MessageRequest):
    session = inquiry_engine.get_session(message.session_id)
    locale = session.get("locale", "zh") if session else "zh"
    result = safety_guard.check_danger_signals(message.message, locale)
    return result
