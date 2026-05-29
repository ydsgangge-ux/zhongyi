from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.tcm_engine import TCMEngine
from core.western_engine import WesternEngine
from core.safety_guard import SafetyGuard
from .inquiry import inquiry_engine

router = APIRouter()
tcm_engine = TCMEngine()
western_engine = WesternEngine()
safety_guard = SafetyGuard()


class AnalyzeRequest(BaseModel):
    session_id: str


@router.post("/inquiry/analyze")
async def analyze(req: AnalyzeRequest):
    session = inquiry_engine.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    locale = session.get("locale", "zh")

    if session["round"] < 3:
        msg = "Insufficient inquiry rounds. Please continue the inquiry." if locale == "en" else "问诊轮次不足，请继续问诊"
        raise HTTPException(status_code=400, detail=msg)

    tcm_result = await tcm_engine.analyze(session)
    western_result = await western_engine.analyze(session)

    herb_check = safety_guard.check_herb_conflicts(tcm_result.get("prescription", {}))
    if herb_check["has_conflict"]:
        tcm_result["prescription"]["warning"] = herb_check["warning"]

    disclaimer_zh = "本分析由AI生成，仅供健康参考，不构成医疗诊断。如症状持续或加重，请及时就医。中草药方剂使用前建议咨询执业中医师确认剂量与适应证。"
    disclaimer_en = "This analysis is AI-generated for health reference only and does not constitute medical diagnosis. Please seek professional medical attention if symptoms persist or worsen. Consult a licensed TCM practitioner before using any herbal formulas."

    return {
        "session_id": req.session_id,
        "tcm_analysis": tcm_result,
        "western_reference": western_result,
        "disclaimer": disclaimer_en if locale == "en" else disclaimer_zh,
    }
