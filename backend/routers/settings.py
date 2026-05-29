from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from core.config import (
    load_config,
    save_config,
    is_configured,
    update_deepseek_config,
    update_claude_config,
    update_system_config,
)

router = APIRouter()


class DeepSeekConfigRequest(BaseModel):
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ClaudeConfigRequest(BaseModel):
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None


class SystemConfigRequest(BaseModel):
    region_default: Optional[str] = None
    save_history: Optional[bool] = None


@router.get("/settings")
async def get_settings():
    config = load_config()
    ds_key = config["deepseek"]["api_key"]
    claude_key = config["claude"]["api_key"]
    config["deepseek"]["api_key"] = ds_key[:8] + "****" if len(ds_key) > 8 else ("****" if ds_key else "")
    config["claude"]["api_key"] = claude_key[:8] + "****" if len(claude_key) > 8 else ("****" if claude_key else "")
    return {"config": config, "status": is_configured()}


@router.post("/settings/deepseek")
async def update_deepseek(req: DeepSeekConfigRequest):
    result = update_deepseek_config(**req.model_dump(exclude_none=True))
    key = result["api_key"]
    result["api_key"] = key[:8] + "****" if len(key) > 8 else ("****" if key else "")
    return {"message": "DeepSeek 配置已保存", "config": result}


@router.post("/settings/claude")
async def update_claude(req: ClaudeConfigRequest):
    result = update_claude_config(**req.model_dump(exclude_none=True))
    key = result["api_key"]
    result["api_key"] = key[:8] + "****" if len(key) > 8 else ("****" if key else "")
    return {"message": "Claude 配置已保存", "config": result}


@router.post("/settings/system")
async def update_system(req: SystemConfigRequest):
    result = update_system_config(**req.model_dump(exclude_none=True))
    return {"message": "系统配置已保存", "config": result}


@router.get("/settings/status")
async def get_settings_status():
    return is_configured()
