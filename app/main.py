from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.routers.health import router as health_router
from app.routers.recommendation import router as recommendation_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(recommendation_router, prefix=settings.api_prefix)

