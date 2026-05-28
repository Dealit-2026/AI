from typing import Protocol

from app.domain.recommendation.models import (
    CategoryRecommendationAlternative,
    CategoryRecommendationQuery,
    CategoryRecommendationResult,
    PriceRecommendationQuery,
    PriceRecommendationResult,
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


class PriceRecommender(Protocol):
    def recommend_price(
        self,
        query: PriceRecommendationQuery,
    ) -> PriceRecommendationResult:
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


class RuleBasedPriceRecommender:
    def recommend_price(
        self,
        query: PriceRecommendationQuery,
    ) -> PriceRecommendationResult:
        recent_prices = tuple(price.price for price in query.recent_prices if price.price > 0)
        if recent_prices:
            return self._recommend_from_recent_prices(query, recent_prices)

        combined_text = f"{query.title or ''} {query.description or ''}".lower()
        base_price = self._estimate_base_price(combined_text, query.category_name)
        condition_multiplier = self._estimate_condition_multiplier(combined_text)
        suggested_price = self._round_price(int(base_price * condition_multiplier))
        return PriceRecommendationResult(
            suggested_price_min=self._round_price(int(suggested_price * 0.85)),
            suggested_price=suggested_price,
            suggested_price_max=self._round_price(int(suggested_price * 1.15)),
            confidence=0.42,
            reason="Rule-based fallback estimated a price from category, keywords, and item condition.",
            factors=("category", "keywords", "condition"),
            model_version="rule-based-price-v1",
        )

    def _recommend_from_recent_prices(
        self,
        query: PriceRecommendationQuery,
        recent_prices: tuple[int, ...],
    ) -> PriceRecommendationResult:
        sorted_prices = sorted(recent_prices)
        lower_bound = self._percentile(sorted_prices, 0.2)
        median = self._percentile(sorted_prices, 0.5)
        upper_bound = self._percentile(sorted_prices, 0.8)
        combined_text = f"{query.title or ''} {query.description or ''}".lower()
        condition_multiplier = self._estimate_condition_multiplier(combined_text)
        suggested_price = self._round_price(int(median * condition_multiplier))

        return PriceRecommendationResult(
            suggested_price_min=min(suggested_price, self._round_price(int(lower_bound * condition_multiplier))),
            suggested_price=suggested_price,
            suggested_price_max=max(suggested_price, self._round_price(int(upper_bound * condition_multiplier))),
            confidence=0.58,
            reason="Rule-based fallback estimated a price from recent comparable prices and item condition.",
            factors=("recentPrices", "condition"),
            model_version="rule-based-price-v1",
        )

    def _estimate_base_price(self, combined_text: str, category_name: str | None) -> int:
        category = (category_name or "").lower()
        if any(keyword in combined_text for keyword in ("iphone", "아이폰", "galaxy", "갤럭시")):
            return 600_000
        if any(keyword in combined_text for keyword in ("macbook", "맥북", "laptop", "노트북")):
            return 900_000
        if any(keyword in combined_text for keyword in ("switch", "닌텐도", "console", "플스", "ps5")):
            return 300_000
        if any(keyword in category for keyword in ("digital", "전자", "디지털")):
            return 250_000
        if any(keyword in category for keyword in ("furniture", "가구", "interior", "인테리어")):
            return 80_000
        return 50_000

    def _estimate_condition_multiplier(self, combined_text: str) -> float:
        if any(keyword in combined_text for keyword in ("새상품", "미개봉", "unused", "sealed", "new")):
            return 1.15
        if any(keyword in combined_text for keyword in ("하자", "파손", "고장", "crack", "broken")):
            return 0.55
        if any(keyword in combined_text for keyword in ("사용감", "스크래치", "scratch")):
            return 0.8
        return 1.0

    def _percentile(self, values: list[int], percentile: float) -> int:
        if not values:
            return 0
        index = round((len(values) - 1) * percentile)
        return values[index]

    def _round_price(self, price: int) -> int:
        normalized = max(price, 1_000)
        unit = 1_000 if normalized < 100_000 else 10_000
        return round(normalized / unit) * unit
