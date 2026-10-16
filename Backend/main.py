import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.core.config import settings
from src.api.routes import router

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "app"

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="DSE Quantitative Market Scanner and Multi-Pane Analytics Engine",
    debug=settings.DEBUG
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount API routes at both /api/v1 and /api for seamless frontend integration
app.include_router(router, prefix=settings.API_PREFIX)
app.include_router(router, prefix="/api")

# Mount Static Frontend at root
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    @app.get("/")
    def home():
        return {
            "project": settings.APP_NAME,
            "status": "running",
            "message": "DSE Signal Unified Backend is ready",
            "docs": "/docs"
        }
