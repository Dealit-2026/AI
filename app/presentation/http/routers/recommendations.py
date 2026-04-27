from fastapi import APIRouter, Depends, Request

from app.application.use_cases.recommend_item import RecommendItemUseCase
from app.domain.recommendation.models import RecommendationQuery
from app.presentation.http.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommend_item_use_case(request: Request) -> RecommendItemUseCase:
    return request.app.state.recommend_item_use_case


@router.post("/items", response_model=RecommendationResponse)
def recommend_item(
    request: RecommendationRequest,
    use_case: RecommendItemUseCase = Depends(get_recommend_item_use_case),
) -> RecommendationResponse:
    result = use_case.execute(
        RecommendationQuery(
            image_url=str(request.image_url) if request.image_url else None,
            title=request.title,
            description=request.description,
        )
    )
    return RecommendationResponse(
        category=result.category,
        category_confidence=result.category_confidence,
        suggested_price_min=result.suggested_price_min,
        suggested_price_max=result.suggested_price_max,
        price_confidence=result.price_confidence,
        reasoning=result.reasoning,
        model_version=result.model_version,
    )
