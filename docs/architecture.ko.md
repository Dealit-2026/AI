# AI Repository Architecture 번역본

## 목표

이 저장소는 HTTP 처리, 비즈니스 규칙, 운영/기술 의존성을 분리하기 위해 이런 구조로 구성되어 있습니다.
핵심 목적은 추상적인 설계 미학이 아니라, 앞으로의 변경을 예측 가능하게 만드는 것입니다.

- 규칙 기반 추천기를 LLM 또는 멀티모달 모델로 교체하기 쉽도록
- 영속성, 캐시, 외부 연동을 추가하기 쉽도록
- 전송 계층 코드와 비즈니스 로직이 섞이지 않도록 API를 확장하기 위해

## 폴더 구조

```text
app/
  application/
    use_cases/
      recommend_item.py
  domain/
    recommendation/
      models.py
      recommenders.py
  infrastructure/
    config/
      settings.py
  presentation/
    http/
      api.py
      routers/
        health.py
        recommendations.py
      schemas/
        recommendation.py
  main.py
docs/
  architecture.md
  architecture.ko.md
```

## 책임 분리

### `app/presentation`

HTTP 진입점과 페이로드 형식을 담당합니다.

- FastAPI 라우터를 정의합니다.
- Pydantic으로 요청과 응답을 검증합니다.
- HTTP 페이로드를 application 또는 domain 입력으로 변환합니다.
- 카테고리 규칙, 가격 규칙, 모델 판단 로직을 직접 가지면 안 됩니다.

### `app/application`

유스케이스의 실행 흐름을 담당합니다.

- "상품을 추천한다" 같은 하나의 비즈니스 동작을 조합합니다.
- 필요한 순서대로 domain 서비스를 호출합니다.
- 라우터 안에 흐름 제어 로직이 쌓이지 않게 합니다.

### `app/domain`

비즈니스 의미와 추천 규칙을 담당합니다.

- 추천 입력과 출력 모델을 정의합니다.
- 추천기 계약과 현재의 규칙 기반 구현을 포함합니다.
- FastAPI, 환경 설정 로딩, 외부 SDK에 의존하지 않아야 합니다.

### `app/infrastructure`

기술적인 런타임 관심사를 담당합니다.

- 환경 설정
- 모델 제공자 클라이언트
- 스토리지, 캐시, 데이터베이스, 큐 어댑터

이 계층은 프레임워크와 SDK에 의존해도 됩니다. 하지만 domain 계층은 그러면 안 됩니다.

### `app/main.py`

부트스트랩만 담당합니다.

- FastAPI 앱 생성
- 설정 로딩
- API 라우터 등록

비즈니스 의사결정 로직이 여기에 쌓이면 안 됩니다.

## 의존 방향

의도한 의존 흐름은 아래와 같습니다.

```text
presentation -> application -> domain
main -> infrastructure
main -> presentation
application -> domain
infrastructure -> external systems
```

지켜야 할 규칙:

- `domain`은 `fastapi`, `pydantic_settings`, 외부 모델 SDK를 import 하면 안 됩니다.
- `presentation`은 `application`을 import 해도 되지만, 추천 로직을 직접 구현하면 안 됩니다.
- `application`은 domain 서비스를 조합할 수 있지만, HTTP나 infra 세부사항에 얽매이면 안 됩니다.
- `infrastructure`는 기술 라이브러리에 의존할 수 있지만, 비즈니스 정책을 소유하면 안 됩니다.

## 확장 가이드

코드는 기술 종류보다 책임 기준으로 배치합니다.

- 새 엔드포인트: `presentation/http/routers`
- 새 요청/응답 스키마: `presentation/http/schemas`
- 새 추천 규칙이나 가격 정책: `domain/recommendation`
- 새 실행 흐름: `application/use_cases`
- 새 OpenAI, Gemini, S3, Redis, DB 연동: `infrastructure`

## 현재 설계 판단

현재 추천기는 여전히 규칙 기반이지만, 카테고리와 가격 가이드를 결정하는 비즈니스 판단이기 때문에 `domain`에 두었습니다.

나중에 외부 모델을 호출하게 되면:

- 프롬프트 구성과 모델 클라이언트 코드는 `infrastructure`
- 그 호출 흐름을 조합하는 코드는 `application`
- 비즈니스 수준의 입력, 출력, 후처리 정책은 계속 `domain`

이렇게 나누면 이후의 AI 세션이나 다른 개발자도 구조를 빠르게 이해하고 안전하게 확장할 수 있습니다.

