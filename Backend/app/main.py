"""FastApi application entry point and router wiring."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import sync, wifi

app = FastAPI(
    title="Wi-Fi Controller Integration Dashboard",
    description="Ingest and exposes mock_data.json wi-fi controller data.",
    version="1.0.0",
)
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sync.router)
app.include_router(wifi.router)

@app.get("/", tags=["health"])
def health_check():
    """Lightweight liveness probe."""
    return {"status": "ok", "service": "wifi-controller-dashboard"}