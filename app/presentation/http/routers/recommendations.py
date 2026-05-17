from fastapi import APIRouter, Depends, Request

from app.application.use_cases.recommend_category import RecommendCategoryUseCase
from app.application.use_cases.recommend_item import RecommendItemUseCase
from app.domain.recommendation.models import (
    CategoryCandidate,
    CategoryRecommendationQuery,
    RecommendationQuery,
)
from app.presentation.http.schemas.recommendation import (
    CategoryRecommendationAlternativeResponse,
    CategoryRecommendationRequest,
    CategoryRecommendationResponse,
    RecommendationRequest,
    RecommendationResponse,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommend_item_use_case(request: Request) -> RecommendItemUseCase:
    return request.app.state.recommend_item_use_case


def get_recommend_category_use_case(request: Request) -> RecommendCategoryUseCase:
    return request.app.state.recommend_category_use_case


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


@router.post("/categories", response_model=CategoryRecommendationResponse)
def recommend_category(
    request: CategoryRecommendationRequest,
    use_case: RecommendCategoryUseCase = Depends(get_recommend_category_use_case),
) -> CategoryRecommendationResponse:
    result = use_case.execute(
        CategoryRecommendationQuery(
            title=request.title,
            description=request.description,
            image_urls=tuple(str(image_url) for image_url in request.imageUrls),
            candidates=tuple(
                CategoryCandidate(
                    id=candidate.id,
                    name_ko=candidate.nameKo,
                    name_en=candidate.nameEn,
                )
                for candidate in request.candidates
            ),
        )
    )
    return CategoryRecommendationResponse(
        recommendedCategoryId=result.recommended_category_id,
        confidence=result.confidence,
        reason=result.reason,
        alternatives=[
            CategoryRecommendationAlternativeResponse(
                categoryId=alternative.category_id,
                confidence=alternative.confidence,
            )
            for alternative in result.alternatives
        ],
        modelVersion=result.model_version,
    )
