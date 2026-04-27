from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.application.use_cases.recommend_item import RecommendItemUseCase
from app.domain.recommendation.recommenders import RuleBasedItemRecommender
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
app.state.recommend_item_use_case = RecommendItemUseCase(
    recommender=RuleBasedItemRecommender()
)

app.include_router(api_router, prefix=settings.api_prefix)
