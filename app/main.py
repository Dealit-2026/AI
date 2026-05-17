from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.application.use_cases.recommend_category import RecommendCategoryUseCase
from app.application.use_cases.recommend_item import RecommendItemUseCase
from app.domain.recommendation.recommenders import (
    RuleBasedCategoryRecommender,
    RuleBasedItemRecommender,
)
from app.infrastructure.config.settings import get_settings
from app.infrastructure.gemini.category_recommender import (
    FallbackCategoryRecommender,
    GeminiCategoryRecommender,
)
from app.infrastructure.openai.category_recommender import OpenAICategoryRecommender
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

if settings.ai_provider.lower() == "openai":
    category_recommender = OpenAICategoryRecommender(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        timeout_seconds=settings.gemini_timeout_seconds,
        max_image_bytes=settings.gemini_max_image_bytes,
    )
else:
    category_recommender = GeminiCategoryRecommender(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.gemini_timeout_seconds,
        max_image_bytes=settings.gemini_max_image_bytes,
    )

app.state.recommend_category_use_case = RecommendCategoryUseCase(
    recommender=FallbackCategoryRecommender(
        primary=category_recommender,
        fallback=RuleBasedCategoryRecommender(),
    )
)

app.include_router(api_router, prefix=settings.api_prefix)
