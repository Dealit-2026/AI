from typing import Protocol

from app.domain.recommendation.models import (
    CategoryRecommendationAlternative,
    CategoryRecommendationQuery,
    CategoryRecommendationResult,
    RecommendationQuery,
    RecommendationResult,
)


class ItemRecommender(Protocol):
    def recommend(self, query: RecommendationQuery) -> RecommendationResult:
        ...


class CategoryRecommender(Protocol):
    def recommend_category(
        self,
        query: CategoryRecommendationQuery,
    ) -> CategoryRecommendationResult:
        ...


class RuleBasedItemRecommender:
    def recommend(self, query: RecommendationQuery) -> RecommendationResult:
        normalized_title = (query.title or "").lower()
        normalized_description = (query.description or "").lower()
        combined_text = f"{normalized_title} {normalized_description}"

        smartphone_keywords = ("iphone", "smartphone", "phone")
        laptop_keywords = ("macbook", "laptop", "notebook")

        if any(keyword in combined_text for keyword in smartphone_keywords):
            return RecommendationResult(
                category="Smartphone",
                category_confidence=0.91,
                suggested_price_min=300000,
                suggested_price_max=900000,
                price_confidence=0.62,
                reasoning="The title or description contains smartphone-related keywords.",
                model_version="rule-based-mvp-v1",
            )

        if any(keyword in combined_text for keyword in laptop_keywords):
            return RecommendationResult(
                category="Laptop",
                category_confidence=0.89,
                suggested_price_min=400000,
                suggested_price_max=1500000,
                price_confidence=0.58,
                reasoning="The title or description contains laptop-related keywords.",
                model_version="rule-based-mvp-v1",
            )

        return RecommendationResult(
            category="Other Electronics",
            category_confidence=0.45,
            suggested_price_min=50000,
            suggested_price_max=300000,
            price_confidence=0.34,
            reasoning="No strong rule matched, so a generic fallback category was selected.",
            model_version="rule-based-mvp-v1",
        )


class RuleBasedCategoryRecommender:
    def recommend_category(
        self,
        query: CategoryRecommendationQuery,
    ) -> CategoryRecommendationResult:
        if not query.candidates:
            raise ValueError("category candidates are required")

        combined_text = f"{query.title or ''} {query.description or ''}".lower()
        scored_candidates: list[tuple[int, float]] = []

        for candidate in query.candidates:
            names = (candidate.name_ko.lower(), candidate.name_en.lower())
            score = 0.72 if any(name and name in combined_text for name in names) else 0.0
            scored_candidates.append((candidate.id, score))

        best_category_id, best_score = max(scored_candidates, key=lambda item: item[1])
        if best_score <= 0:
            best_category_id = self._find_others_category_id(query) or query.candidates[0].id
            best_score = 0.35

        alternatives = tuple(
            CategoryRecommendationAlternative(category_id=category_id, confidence=score)
            for category_id, score in sorted(
                scored_candidates,
                key=lambda item: item[1],
                reverse=True,
            )
            if category_id != best_category_id and score > 0
        )

        return CategoryRecommendationResult(
            recommended_category_id=best_category_id,
            confidence=best_score,
            reason="Rule-based fallback selected a matching category or the local Others candidate.",
            alternatives=alternatives[:2],
            model_version="rule-based-category-v1",
        )

    def _find_others_category_id(self, query: CategoryRecommendationQuery) -> int | None:
        for candidate in query.candidates:
            normalized_names = {candidate.name_ko.strip().lower(), candidate.name_en.strip().lower()}
            if normalized_names & {"기타", "others", "other"}:
                return candidate.id
        return None
