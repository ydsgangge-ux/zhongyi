from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import inquiry, analysis, health, settings

app = FastAPI(
    title="TCM AI Health Advisor API",
    description="TCM AI Health Advisor - Backend API Service (Funnel Syndrome Differentiation Model)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inquiry.router, prefix="/api", tags=["Inquiry"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(settings.router, prefix="/api", tags=["Settings"])


@app.get("/")
async def root():
    return {
        "name": "TCM AI Health Advisor API",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "This is a backend API service. Please develop your own frontend or use the API directly.",
    }
