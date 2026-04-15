from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.config.settings import get_settings
from app.presentation.http.api import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.api_prefix)
