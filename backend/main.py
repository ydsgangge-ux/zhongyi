import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models.database import delete_expired_sessions
from routers import inquiry, analysis, health, settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="中医AI健康顾问",
    description="TCM AI Health Advisor - 基于漏斗辨证模型的AI健康咨询系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def cleanup_expired_sessions():
    deleted = delete_expired_sessions(24)
    removed = inquiry.inquiry_engine.cleanup_expired()
    if deleted or removed:
        logger.info("清理过期会话: db=%s memory=%s", deleted, removed)

app.include_router(inquiry.router, prefix="/api", tags=["问诊"])
app.include_router(analysis.router, prefix="/api", tags=["分析"])
app.include_router(health.router, prefix="/api", tags=["健康管理"])
app.include_router(settings.router, prefix="/api", tags=["设置"])

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        file_path = os.path.join(FRONTEND_DIST, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "中医AI健康顾问 API", "version": "1.0.0"}
