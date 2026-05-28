# Dealit AI Server

FastAPI-based AI service for item recommendation experiments. The current implementation exposes a small HTTP API and separates transport, use-case orchestration, business rules, and runtime concerns.

## Endpoints

- `GET /api/v1/health`
- `POST /api/v1/recommendations/items`
- `POST /api/v1/recommendations/categories`
- `POST /api/v1/recommendations/prices`

## Project Structure

```text
app/
  application/
    use_cases/
  domain/
    recommendation/
  infrastructure/
    config/
  presentation/
    http/
      routers/
      schemas/
  main.py
docs/
  architecture.md
Dockerfile
requirements.txt
.env.example
```

Detailed architecture notes live in [docs/architecture.md](docs/architecture.md).
Korean translation: [docs/architecture.ko.md](docs/architecture.ko.md).

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

## API Example

Item recommendation request:

```json
{
  "image_url": "https://example.com/item.jpg",
  "title": "iPhone 15 Pro 256GB",
  "description": "Used item in good condition and fully functional."
}
```

Item recommendation response:

```json
{
  "category": "스마트폰",
  "category_confidence": 0.91,
  "suggested_price_min": 300000,
  "suggested_price_max": 900000,
  "price_confidence": 0.62,
  "reasoning": "제목과 설명에서 스마트폰 관련 키워드를 감지했습니다.",
  "model_version": "rule-based-mvp-v1"
}
```

Category recommendation request:

```json
{
  "title": "아이폰 15 프로",
  "description": "배터리 성능 90%이고 상태 좋습니다.",
  "imageUrls": ["https://example.com/item.jpg"],
  "candidates": [
    {"id": 200, "nameKo": "디지털/전자기기", "nameEn": "Digital/Electronics"},
    {"id": 300, "nameKo": "가구/인테리어", "nameEn": "Furniture/Interior"},
    {"id": 999, "nameKo": "기타", "nameEn": "Others"}
  ]
}
```

Category recommendation response:

```json
{
  "recommendedCategoryId": 200,
  "confidence": 0.91,
  "reason": "상품명과 이미지가 스마트폰으로 판단됩니다.",
  "alternatives": [
    {"categoryId": 999, "confidence": 0.12}
  ],
  "modelVersion": "gemini-2.0-flash"
}
```

Price recommendation request:

```json
{
  "title": "아이폰 15 프로 256GB",
  "description": "상태 좋은 중고폰입니다. 배터리 성능 90%입니다.",
  "categoryId": 200,
  "categoryName": "디지털/전자기기",
  "saleType": "REGULAR",
  "imageUrls": ["https://example.com/item.jpg"],
  "recentPrices": [
    {"price": 580000, "title": "아이폰 15 프로 256GB", "soldAt": "2026-05-01"}
  ]
}
```

Price recommendation response:

```json
{
  "suggestedPriceMin": 520000,
  "suggestedPrice": 610000,
  "suggestedPriceMax": 700000,
  "confidence": 0.78,
  "reason": "상품명, 설명, 이미지와 최근 거래가를 기준으로 중고 시세 범위를 산정했습니다.",
  "factors": ["모델명", "저장용량", "상품상태", "최근거래가"],
  "modelVersion": "gemini-2.0-flash"
}
```

Gemini-backed category and price recommendation falls back to rule-based logic
when `GEMINI_API_KEY` is missing or the upstream request fails.

## Next Steps

1. Replace the rule-based recommender with an LLM or multimodal inference path.
2. Add pricing logic backed by transaction history or marketplace data.
3. Add infrastructure adapters for storage, cache, and model providers.
