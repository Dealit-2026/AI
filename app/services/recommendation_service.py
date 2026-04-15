from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)


class RecommendationService:
    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        normalized_title = (request.title or "").lower()
        normalized_description = (request.description or "").lower()
        combined_text = f"{normalized_title} {normalized_description}"

        if any(keyword in combined_text for keyword in ("iphone", "갤럭시", "smartphone", "phone")):
            return RecommendationResponse(
                category="스마트폰",
                category_confidence=0.91,
                suggested_price_min=300000,
                suggested_price_max=900000,
                price_confidence=0.62,
                reasoning="텍스트 기반 휴대폰 관련 키워드를 감지했습니다.",
                model_version="rule-based-mvp-v1",
            )

        if any(keyword in combined_text for keyword in ("macbook", "그램", "laptop", "notebook")):
            return RecommendationResponse(
                category="노트북",
                category_confidence=0.89,
                suggested_price_min=400000,
                suggested_price_max=1500000,
                price_confidence=0.58,
                reasoning="텍스트 기반 노트북 관련 키워드를 감지했습니다.",
                model_version="rule-based-mvp-v1",
            )

        return RecommendationResponse(
            category="기타 디지털기기",
            category_confidence=0.45,
            suggested_price_min=50000,
            suggested_price_max=300000,
            price_confidence=0.34,
            reasoning="현재는 초기 규칙 기반 추천기만 연결되어 있습니다.",
            model_version="rule-based-mvp-v1",
        )

