from app.domain.recommendation.models import (
    PriceRecommendationQuery,
    PriceRecommendationResult,
)
from app.domain.recommendation.recommenders import PriceRecommender


class RecommendPriceUseCase:
    def __init__(self, recommender: PriceRecommender) -> None:
        self._recommender = recommender

    def execute(
        self,
        query: PriceRecommendationQuery,
    ) -> PriceRecommendationResult:
        return self._recommender.recommend_price(query)
