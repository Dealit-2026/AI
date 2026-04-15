from typing import Protocol

from app.domain.recommendation.models import RecommendationQuery, RecommendationResult


class ItemRecommender(Protocol):
    def recommend(self, query: RecommendationQuery) -> RecommendationResult:
        ...


class RuleBasedItemRecommender:
    def recommend(self, query: RecommendationQuery) -> RecommendationResult:
        normalized_title = (query.title or "").lower()
        normalized_description = (query.description or "").lower()
        combined_text = f"{normalized_title} {normalized_description}"

        smartphone_keywords = ("iphone", "아이폰", "smartphone", "phone", "스마트폰")
        laptop_keywords = ("macbook", "맥북", "laptop", "notebook", "노트북")

        if any(keyword in combined_text for keyword in smartphone_keywords):
            return RecommendationResult(
                category="스마트폰",
                category_confidence=0.91,
                suggested_price_min=300000,
                suggested_price_max=900000,
                price_confidence=0.62,
                reasoning="제목과 설명에서 스마트폰 관련 키워드를 감지했습니다.",
                model_version="rule-based-mvp-v1",
            )

        if any(keyword in combined_text for keyword in laptop_keywords):
            return RecommendationResult(
                category="노트북",
                category_confidence=0.89,
                suggested_price_min=400000,
                suggested_price_max=1500000,
                price_confidence=0.58,
                reasoning="제목과 설명에서 노트북 관련 키워드를 감지했습니다.",
                model_version="rule-based-mvp-v1",
            )

        return RecommendationResult(
            category="기타 전자기기",
            category_confidence=0.45,
            suggested_price_min=50000,
            suggested_price_max=300000,
            price_confidence=0.34,
            reasoning="현재는 규칙 기반 초기 추천만 제공하고 있어 일반 전자기기 범주로 분류했습니다.",
            model_version="rule-based-mvp-v1",
        )

