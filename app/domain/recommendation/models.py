from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationQuery:
    image_url: str | None
    title: str | None
    description: str | None


@dataclass(frozen=True)
class RecommendationResult:
    category: str
    category_confidence: float
    suggested_price_min: int
    suggested_price_max: int
    price_confidence: float
    reasoning: str
    model_version: str

