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

