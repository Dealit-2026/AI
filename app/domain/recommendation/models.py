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


@dataclass(frozen=True)
class CategoryCandidate:
    id: int
    name_ko: str
    name_en: str


@dataclass(frozen=True)
class CategoryRecommendationQuery:
    title: str | None
    description: str | None
    image_urls: tuple[str, ...]
    candidates: tuple[CategoryCandidate, ...]


@dataclass(frozen=True)
class CategoryRecommendationAlternative:
    category_id: int
    confidence: float


@dataclass(frozen=True)
class CategoryRecommendationResult:
    recommended_category_id: int
    confidence: float
    reason: str
    alternatives: tuple[CategoryRecommendationAlternative, ...]
    model_version: str

