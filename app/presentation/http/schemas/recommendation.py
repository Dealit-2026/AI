from pydantic import BaseModel, Field, HttpUrl


class RecommendationRequest(BaseModel):
    image_url: HttpUrl | None = Field(
        default=None,
        description="S3 or CDN image URL",
    )
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class RecommendationResponse(BaseModel):
    category: str
    category_confidence: float = Field(ge=0.0, le=1.0)
    suggested_price_min: int = Field(ge=0)
    suggested_price_max: int = Field(ge=0)
    price_confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    model_version: str


class CategoryCandidateRequest(BaseModel):
    id: int = Field(gt=0)
    nameKo: str = Field(min_length=1, max_length=100)
    nameEn: str = Field(min_length=1, max_length=100)


class CategoryRecommendationRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    imageUrls: list[str] = Field(default_factory=list, max_length=5)
    candidates: list[CategoryCandidateRequest] = Field(min_length=1, max_length=100)


class CategoryRecommendationAlternativeResponse(BaseModel):
    categoryId: int
    confidence: float = Field(ge=0.0, le=1.0)


class CategoryRecommendationResponse(BaseModel):
    recommendedCategoryId: int
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    alternatives: list[CategoryRecommendationAlternativeResponse]
    modelVersion: str

