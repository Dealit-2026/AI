# Dealit AI Server

FastAPI-based AI service for item recommendation experiments. The current implementation exposes a small HTTP API and separates transport, use-case orchestration, business rules, and runtime concerns.

## Endpoints

- `GET /api/v1/health`
- `POST /api/v1/recommendations/items`

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

Request:

```json
{
  "image_url": "https://example.com/item.jpg",
  "title": "iPhone 15 Pro 256GB",
  "description": "Used item in good condition and fully functional."
}
```

Response:

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

## Next Steps

1. Replace the rule-based recommender with an LLM or multimodal inference path.
2. Add pricing logic backed by transaction history or marketplace data.
3. Add infrastructure adapters for storage, cache, and model providers.
