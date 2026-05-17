import base64
import json
import logging
import mimetypes
from dataclasses import asdict
from json import JSONDecodeError

import httpx

from app.domain.recommendation.models import (
    CategoryRecommendationAlternative,
    CategoryRecommendationQuery,
    CategoryRecommendationResult,
)


logger = logging.getLogger(__name__)


class OpenAIRequestError(RuntimeError):
    pass


class OpenAICategoryRecommender:
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_image_bytes: int,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_image_bytes = max_image_bytes

    def recommend_category(
        self,
        query: CategoryRecommendationQuery,
    ) -> CategoryRecommendationResult:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        if not query.candidates:
            raise ValueError("category candidates are required")

        content = [{"type": "input_text", "text": self._build_prompt(query)}]
        content.extend(self._build_image_inputs(query.image_urls))

        payload = {
            "model": self._model,
            "input": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "category_recommendation",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "recommendedCategoryId": {"type": "integer"},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "reason": {"type": "string"},
                            "alternatives": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "categoryId": {"type": "integer"},
                                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                    },
                                    "required": ["categoryId", "confidence"],
                                },
                            },
                        },
                        "required": [
                            "recommendedCategoryId",
                            "confidence",
                            "reason",
                            "alternatives",
                        ],
                    },
                }
            },
        }

        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if response.is_error:
                raise OpenAIRequestError(self._format_error_response(response))

        return self._parse_response(response.json(), query)

    def _build_prompt(self, query: CategoryRecommendationQuery) -> str:
        candidates = [asdict(candidate) for candidate in query.candidates]
        return (
            "You classify secondhand marketplace items into exactly one category.\n"
            "Use the title, description, and images if provided.\n"
            "You must choose only one id from the provided candidates.\n"
            "If no candidate clearly matches, choose the local Others/Other/기타 candidate if present.\n"
            "Never invent a category id.\n"
            "Return only JSON with this exact shape: "
            '{"recommendedCategoryId": number, "confidence": number, '
            '"reason": string, "alternatives": [{"categoryId": number, "confidence": number}]}.\n'
            f"Title: {query.title or ''}\n"
            f"Description: {query.description or ''}\n"
            f"Candidates: {json.dumps(candidates, ensure_ascii=False)}"
        )

    def _build_image_inputs(self, image_urls: tuple[str, ...]) -> list[dict]:
        image_inputs = []
        for image_url in image_urls[:3]:
            image_inputs.append(
                {
                    "type": "input_image",
                    "image_url": self._download_image_data_url(image_url),
                    "detail": "low",
                }
            )
        return image_inputs

    def _download_image_data_url(self, image_url: str) -> str:
        with httpx.Client(timeout=self._timeout_seconds, follow_redirects=True) as client:
            response = client.get(image_url)
            response.raise_for_status()

        content = response.content
        if len(content) > self._max_image_bytes:
            raise ValueError("image is too large")

        mime_type = response.headers.get("content-type", "").split(";")[0].strip()
        if not mime_type.startswith("image/"):
            guessed_mime_type, _ = mimetypes.guess_type(image_url)
            mime_type = guessed_mime_type or "image/jpeg"

        encoded = base64.b64encode(content).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _parse_response(
        self,
        payload: dict,
        query: CategoryRecommendationQuery,
    ) -> CategoryRecommendationResult:
        text = self._extract_text(payload)
        try:
            result = json.loads(text)
        except JSONDecodeError as exception:
            raise ValueError("OpenAI did not return valid JSON") from exception

        allowed_ids = {candidate.id for candidate in query.candidates}
        recommended_category_id = int(result["recommendedCategoryId"])
        if recommended_category_id not in allowed_ids:
            raise ValueError("OpenAI returned a category id outside candidates")

        alternatives = []
        for alternative in result.get("alternatives", [])[:2]:
            category_id = int(alternative["categoryId"])
            if category_id in allowed_ids and category_id != recommended_category_id:
                alternatives.append(
                    CategoryRecommendationAlternative(
                        category_id=category_id,
                        confidence=self._normalize_confidence(alternative.get("confidence", 0)),
                    )
                )

        return CategoryRecommendationResult(
            recommended_category_id=recommended_category_id,
            confidence=self._normalize_confidence(result.get("confidence", 0)),
            reason=str(result.get("reason", ""))[:500],
            alternatives=tuple(alternatives),
            model_version=self._model,
        )

    def _extract_text(self, payload: dict) -> str:
        output_text = payload.get("output_text")
        if output_text:
            return str(output_text).strip()

        text_parts = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if text:
                    text_parts.append(text)
        if not text_parts:
            raise ValueError("OpenAI response has no text")
        return "\n".join(text_parts).strip()

    def _format_error_response(self, response: httpx.Response) -> str:
        try:
            error_body = response.json()
        except JSONDecodeError:
            error_body = response.text[:1000]
        return f"status={response.status_code}, body={error_body}"

    def _normalize_confidence(self, value: object) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.0
        return min(max(confidence, 0.0), 1.0)
