from app.domain.recommendation.models import (
    RecommendationQuery,
    RecommendationResult,
)
from app.domain.recommendation.recommenders import ItemRecommender


class RecommendItemUseCase:
    def __init__(self, recommender: ItemRecommender) -> None:
        self._recommender = recommender

    def execute(self, query: RecommendationQuery) -> RecommendationResult:
        return self._recommender.recommend(query)

