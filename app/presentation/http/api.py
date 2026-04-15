from fastapi import APIRouter

from app.presentation.http.routers.health import router as health_router
from app.presentation.http.routers.recommendations import router as recommendation_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(recommendation_router)

