from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from core.inquiry_engine import InquiryEngine
from core.safety_guard import SafetyGuard
import uuid

router = APIRouter()
inquiry_engine = InquiryEngine()
safety_guard = SafetyGuard()

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

    danger_check = safety_guard.check_danger_signals(req.message)
    if danger_check["dangerous"]:
        locale = session.get("locale", "zh")
        return {
            "session_id": req.session_id,
            "round": session["round"],
            "response": danger_check["warning"],
            "danger_signal": True,
            "should_see_doctor": True,
            "danger_message": DANGER_MSGS.get(locale, DANGER_MSGS["zh"]),
        }

    session["messages"].append({"role": "user", "content": req.message})

    async def stream_response():
        async for chunk in inquiry_engine.process_message(session, req.message):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@router.post("/safety/check")
async def safety_check(message: MessageRequest):
    result = safety_guard.check_danger_signals(message.message)
    return result
