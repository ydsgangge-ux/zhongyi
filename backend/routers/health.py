from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from models.database import get_db, save_health_record, get_health_records
from .inquiry import inquiry_engine

router = APIRouter()


class HealthRecordCreate(BaseModel):
    session_id: str
    notes: Optional[str] = None


class HealthRecordResponse(BaseModel):
    id: int
    session_id: str
    tcm_analysis: dict
    western_reference: dict
    messages: Optional[List[dict]] = None
    notes: Optional[str]
    created_at: str


@router.post("/health/record")
async def create_record(req: HealthRecordCreate):
    session = inquiry_engine.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    analysis = session.get("last_analysis") or {}
    record = save_health_record(
        req.session_id,
        tcm_analysis=analysis.get("tcm_analysis"),
        western_reference=analysis.get("western_reference"),
        notes=req.notes,
        messages=session.get("messages"),
    )
    return record


@router.get("/health/records", response_model=List[HealthRecordResponse])
async def list_records(limit: int = 20, offset: int = 0):
    records = get_health_records(limit=limit, offset=offset)
    return records
