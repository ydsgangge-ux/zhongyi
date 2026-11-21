import asyncio
import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.tcm_engine import TCMEngine
from core.western_engine import WesternEngine
from core.safety_guard import SafetyGuard
from core.extraction import ensure_structured_fields, compute_completeness
from core.gender_differentiation import get_safety_mode
from core.config import get_system_config
from models.database import save_health_record, get_health_record_by_session
from .inquiry import inquiry_engine

router = APIRouter()
tcm_engine = TCMEngine()
western_engine = WesternEngine()
safety_guard = SafetyGuard()
logger = logging.getLogger(__name__)

MIN_USER_TURNS = 3


def _apply_safety_checks(session: dict, tcm_result: dict, prescription: dict, locale: str) -> None:
    en = locale == "en"
    safety_info = get_safety_mode(session, locale)
    mode = safety_info.get("mode", "standard")
    herb_text = " ".join(
        str(prescription.get(key) or "")
        for key in ("decoction", "patent_medicine", "diet_therapy")
    )
    gender_check = safety_guard.check_gender_safety(herb_text, session, locale)

    warnings = []
    if safety_info.get("safety_mode") and mode != "standard":
        prescription["safety_mode"] = mode
        mode_warnings = " ".join(safety_info.get("warnings", []))
        warnings.append(
            f"Safety mode enabled: {mode}. {mode_warnings}" if en
            else f"已启用安全模式：{mode}。{mode_warnings}"
        )

    violations = gender_check.get("warnings") or []
    if violations:
        prescription["safety_level"] = "red"
        header = (
            "⚠️ Prescription failed the safety check. Do NOT use this formula on your own. "
            "Please consult a licensed TCM practitioner to reformulate."
            if en else
            "⚠️ 处方安全性校验未通过，请勿自行使用此方，建议携带本处方咨询执业中医师重新组方。"
        )
        warnings.insert(0, header)
        warnings[1:1] = violations

    if warnings:
        existing = prescription.get("warning") or ""
        parts = ([existing] if existing else []) + warnings
        prescription["warning"] = "\n".join(parts)

    if safety_guard.check_minor(session.get("age")):
        minor_msg = (
            "This user is a minor. Herbal use must be reviewed by a pediatrician or TCM "
            "practitioner with a guardian present."
            if en else
            "用户为未成年人，草药使用须由监护人陪同并咨询儿科/中医师，不建议自行服用。"
        )
        existing = prescription.get("warning")
        prescription["warning"] = f"{existing}\n{minor_msg}" if existing else minor_msg
        if tcm_result.get("confidence_level") in (None, "green"):
            tcm_result["confidence_level"] = "yellow"


def _apply_western_danger(western: dict, tcm_result: dict, prescription: dict, locale: str) -> None:
    en = locale == "en"
    signals = (western or {}).get("danger_signals") or []
    high = [s for s in signals if str(s.get("urgency", "")).lower() == "high"]
    visit = (western or {}).get("doctor_visit") or {}
    if not high and visit.get("urgency") != "immediate":
        return

    detail = "；".join(str(s.get("signal", "")) for s in high if s.get("signal"))
    if en:
        msg = ("⚠️ Western reference indicates a high-risk signal"
               + (f" ({detail})" if detail else "")
               + ". Please seek medical attention first; this TCM analysis is for reference only.")
    else:
        msg = ("⚠️ 西医参考提示存在高危信号"
               + (f"（{detail}）" if detail else "")
               + "，请优先线下就医，本次中医分析仅供参考。")

    tcm_result["emergency_warning"] = msg
    tcm_result["confidence_level"] = "red"
    prescription["safety_level"] = "red"


def _apply_confidence_cap(session: dict, tcm_result: dict) -> None:
    """用客观信息完整度压制 LLM 自报置信度。"""
    completeness = compute_completeness(session)
    tcm_result["information_completeness"] = completeness

    if completeness < 0.3:
        tcm_result["confidence_level"] = "red"
    elif completeness < 0.6 and tcm_result.get("confidence_level") == "green":
        tcm_result["confidence_level"] = "yellow"

    syndrome = tcm_result.get("syndrome")
    if not isinstance(syndrome, dict):
        return
    try:
        confidence = float(syndrome.get("confidence") or 0)
    except (TypeError, ValueError):
        return
    if completeness >= 0.1 and confidence > 0:
        syndrome["confidence"] = round(min(confidence, completeness), 2)


class AnalyzeRequest(BaseModel):
    session_id: str


@router.post("/inquiry/analyze")
async def analyze(req: AnalyzeRequest):
    session = inquiry_engine.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    locale = session.get("locale", "zh")

    if session.get("danger_signal"):
        msg = "A danger signal was detected. Please seek immediate medical attention." if locale == "en" else "已检测到危险信号，请立即就医，不建议继续在线辨证。"
        raise HTTPException(status_code=400, detail=msg)

    # 第 0 轮（生理基线）不占用 session["round"]，因此按用户实际发言数判断
    user_turns = sum(1 for m in session["messages"] if m.get("role") == "user")
    if user_turns < MIN_USER_TURNS:
        msg = "Insufficient inquiry rounds. Please continue the inquiry." if locale == "en" else "问诊轮次不足，请继续问诊"
        raise HTTPException(status_code=400, detail=msg)

    # 分析前兜底抽取结构化字段（孕产/经期/舌象/服药史），安全过滤依赖这些字段
    await ensure_structured_fields(session)

    started = time.monotonic()
    tcm_result, western_result = await asyncio.gather(
        tcm_engine.analyze(session),
        western_engine.analyze(session),
        return_exceptions=True,
    )
    if isinstance(tcm_result, Exception):
        logger.error("中医分析失败 session=%s: %r", req.session_id, tcm_result)
        raise HTTPException(status_code=502, detail="中医分析失败，请稍后重试")
    if isinstance(western_result, Exception):
        logger.error("西医参考分析失败 session=%s: %r", req.session_id, western_result)
        western_result = {}
    if not isinstance(tcm_result, dict):
        tcm_result = {}

    prescription = tcm_result.get("prescription")
    if not isinstance(prescription, dict):
        prescription = {}
        tcm_result["prescription"] = prescription

    herb_check = safety_guard.check_herb_conflicts(prescription)
    if herb_check["has_conflict"]:
        prescription["warning"] = herb_check["warning"]
        prescription["safety_level"] = "red"

    _apply_safety_checks(session, tcm_result, prescription, locale)
    _apply_western_danger(western_result, tcm_result, prescription, locale)
    _apply_confidence_cap(session, tcm_result)

    disclaimer_zh = "本分析由AI生成，仅供健康参考，不构成医疗诊断。如症状持续或加重，请及时就医。中草药方剂使用前建议咨询执业中医师确认剂量与适应证。"
    disclaimer_en = "This analysis is AI-generated for health reference only and does not constitute medical diagnosis. Please seek professional medical attention if symptoms persist or worsen. Consult a licensed TCM practitioner before using any herbal formulas."

    result = {
        "session_id": req.session_id,
        "tcm_analysis": tcm_result,
        "western_reference": western_result,
        "messages": session["messages"],
        "disclaimer": disclaimer_en if locale == "en" else disclaimer_zh,
    }

    # 缓存到会话，供结果页刷新 / 记录保存复用
    session["last_analysis"] = result
    inquiry_engine.persist_session(session)

    if get_system_config().get("save_history", True):
        try:
            save_health_record(
                req.session_id,
                tcm_analysis=tcm_result,
                western_reference=western_result,
                messages=session["messages"],
            )
        except Exception:
            # 记录保存失败不应影响分析结果返回
            logger.exception("保存健康记录失败 session=%s", req.session_id)

    logger.info(
        "分析完成 session=%s turns=%s 耗时=%.1fs",
        req.session_id, user_turns, time.monotonic() - started,
    )
    return result


@router.get("/inquiry/result/{session_id}")
async def get_result(session_id: str):
    session = inquiry_engine.get_session(session_id)
    if session and "last_analysis" in session:
        return session["last_analysis"]

    # 服务重启后内存会话丢失，从健康记录中恢复已保存的分析
    record = get_health_record_by_session(session_id)
    if record and (record.get("tcm_analysis") or record.get("western_reference")):
        return {
            "session_id": session_id,
            "tcm_analysis": record["tcm_analysis"],
            "western_reference": record["western_reference"],
            "messages": record.get("messages") or [],
            "disclaimer": "本分析由AI生成，仅供健康参考，不构成医疗诊断。如症状持续或加重，请及时就医。中草药方剂使用前建议咨询执业中医师确认剂量与适应证。",
        }

    raise HTTPException(status_code=404, detail="暂无分析结果")
