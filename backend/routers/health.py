from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from models.database import get_db, save_health_record, get_health_records

router = APIRouter()


class HealthRecordCreate(BaseModel):
    session_id: str
    notes: Optional[str] = None


class HealthRecordResponse(BaseModel):
    id: int
    session_id: str
    tcm_analysis: dict
    western_reference: dict
    notes: Optional[str]
    created_at: str


@router.post("/health/record")
async def create_record(req: HealthRecordCreate):
    record = save_health_record(req.session_id, req.notes)
    if not record:
        raise HTTPException(status_code=404, detail="会话不存在")
    return record


@router.get("/health/records", response_model=List[HealthRecordResponse])
async def list_records(limit: int = 20, offset: int = 0):
    records = get_health_records(limit=limit, offset=offset)
    return records
