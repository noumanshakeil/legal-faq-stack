from fastapi import APIRouter
from backend.api import health, legal, ui
api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(legal.router, prefix="/api", tags=["legal"])
api_router.include_router(ui.router, tags=["ui"])
