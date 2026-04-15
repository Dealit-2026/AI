# AI Repository Architecture

## Goal

This repository is organized to keep HTTP concerns, business rules, and operational dependencies separate.
The immediate goal is to make future changes predictable:

- replace the rule-based recommender with an LLM or multimodal model
- add persistence, caching, or external integrations
- extend the API without mixing transport code and business logic

## Folder Structure

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
```

## Responsibility Split

### `app/presentation`

Owns HTTP entry points and payload formatting.

- Defines FastAPI routers.
- Validates request and response payloads with Pydantic.
- Converts HTTP payloads into application or domain inputs.
- Must not contain category rules, pricing rules, or model decision logic.

### `app/application`

Owns use-case orchestration.

- Coordinates one business action such as "recommend an item".
- Calls domain services in the required order.
- Keeps workflow logic out of routers.

### `app/domain`

Owns business meaning and recommendation rules.

- Defines recommendation input and output models.
- Contains the recommender contract and the current rule-based implementation.
- Must stay independent from FastAPI, environment loading, and external SDKs.

### `app/infrastructure`

Owns technical runtime concerns.

- Environment settings
- model provider clients
- storage, cache, database, queue adapters

This layer can depend on frameworks and SDKs. The domain layer should not.

### `app/main.py`

Owns bootstrap only.

- Creates the FastAPI app
- loads settings
- registers the API router

Business decisions should not accumulate here.

## Dependency Direction

The intended dependency flow is:

```text
presentation -> application -> domain
main -> infrastructure
main -> presentation
application -> domain
infrastructure -> external systems
```

Keep these rules:

- `domain` must not import `fastapi`, `pydantic_settings`, or external provider SDKs.
- `presentation` may import `application`, but should not implement recommendation logic.
- `application` may coordinate domain services, but should avoid HTTP or infra details.
- `infrastructure` may depend on technical libraries, but should not own business policy.

## Extension Guide

Place code by responsibility first.

- New endpoint: `presentation/http/routers`
- New request or response shape: `presentation/http/schemas`
- New recommendation rule or pricing policy: `domain/recommendation`
- New orchestration flow: `application/use_cases`
- New OpenAI, Gemini, S3, Redis, DB integration: `infrastructure`

## Current Design Decision

The current recommender is still rule-based, but it lives in `domain` because it expresses the business decision logic for category and price guidance.

If the project later calls an external model:

- prompt construction and model client code should live in `infrastructure`
- the use case should orchestrate the call from `application`
- the domain should continue to define business-level inputs, outputs, and policies around the result

This keeps the repo understandable for later AI sessions and for humans working in the same codebase.

