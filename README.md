# Dealit AI Server

중고 경매 서비스용 AI 서버 초기 세팅입니다. 현재 구조는 아키텍처 이미지에 맞춰 `FastAPI` 기반 독립 서버로 구성되어 있으며, 백엔드(Spring)에서 HTTP로 호출하는 형태를 전제로 합니다.

## 현재 포함된 기능

- `GET /api/v1/health`
- `POST /api/v1/recommendations/items`
- 환경변수 설정 분리
- Docker 빌드 설정
- 카테고리/가격 추천용 서비스 레이어 분리

## 프로젝트 구조

```text
app/
  core/
    config.py
  routers/
    health.py
    recommendation.py
  schemas/
    recommendation.py
  services/
    recommendation_service.py
  main.py
Dockerfile
requirements.txt
.env.example
```

## 실행 방법

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

## API 예시

### 요청

```json
{
  "image_url": "https://example.com/item.jpg",
  "title": "아이폰 15 프로 256GB 판매",
  "description": "생활기스 조금 있고 정상 작동합니다."
}
```

### 응답

```json
{
  "category": "스마트폰",
  "category_confidence": 0.91,
  "suggested_price_min": 300000,
  "suggested_price_max": 900000,
  "price_confidence": 0.62,
  "reasoning": "텍스트 기반 휴대폰 관련 키워드를 감지했습니다.",
  "model_version": "rule-based-mvp-v1"
}
```

## 다음 단계

1. 이미지 임베딩 또는 멀티모달 모델 연동
2. 과거 거래 데이터 기반 가격 추정 로직 추가
3. OpenAI 또는 Gemini 연동
4. S3 이미지 접근 및 전처리 추가
5. Docker Compose 또는 ECS 배포 설정 추가
