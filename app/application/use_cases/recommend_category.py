from app.domain.recommendation.models import (
    CategoryRecommendationQuery,
    CategoryRecommendationResult,
)
from app.domain.recommendation.recommenders import CategoryRecommender


class RecommendCategoryUseCase:
    def __init__(self, recommender: CategoryRecommender) -> None:
        self._recommender = recommender

    def execute(
        self,
        query: CategoryRecommendationQuery,
    ) -> CategoryRecommendationResult:
        return self._recommender.recommend_category(query)
