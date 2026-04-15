from fastapi import APIRouter

from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
service = RecommendationService()


@router.post("/items", response_model=RecommendationResponse)
def recommend_item(request: RecommendationRequest) -> RecommendationResponse:
    return service.recommend(request)

