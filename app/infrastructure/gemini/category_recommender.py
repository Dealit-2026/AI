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
from app.domain.recommendation.recommenders import CategoryRecommender


logger = logging.getLogger(__name__)


class GeminiRequestError(RuntimeError):
    pass


class GeminiCategoryRecommender:
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
            raise RuntimeError("GEMINI_API_KEY is not configured")
        if not query.candidates:
            raise ValueError("category candidates are required")

        parts = [{"text": self._build_prompt(query)}]
        parts.extend(self._build_image_parts(query.image_urls))

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self._model}:generateContent"
        )
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }

        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.post(
                endpoint,
                params={"key": self._api_key},
                json=payload,
            )
            if response.is_error:
                raise GeminiRequestError(self._format_error_response(response))

        return self._parse_response(response.json(), query)

    def _format_error_response(self, response: httpx.Response) -> str:
        try:
            error_body = response.json()
        except JSONDecodeError:
            error_body = response.text[:1000]
        return f"status={response.status_code}, body={error_body}"

    def _build_prompt(self, query: CategoryRecommendationQuery) -> str:
        candidates = [asdict(candidate) for candidate in query.candidates]
        return (
            "You classify secondhand marketplace items into exactly one category.\n"
            "Use the title, description, and images if provided.\n"
            "You must choose only one id from the provided candidates.\n"
            "If no candidate clearly matches, choose the local Others/Other/기타 candidate if present.\n"
            "Never invent a category id.\n"
            "Return only JSON with this shape: "
            '{"recommendedCategoryId": number, "confidence": number, '
            '"reason": string, "alternatives": [{"categoryId": number, "confidence": number}]}.\n'
            f"Title: {query.title or ''}\n"
            f"Description: {query.description or ''}\n"
            f"Candidates: {json.dumps(candidates, ensure_ascii=False)}"
        )

    def _build_image_parts(self, image_urls: tuple[str, ...]) -> list[dict]:
        image_parts = []
        for image_url in image_urls[:3]:
            image_parts.append(self._download_image_part(image_url))
        return image_parts

    def _download_image_part(self, image_url: str) -> dict:
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

        return {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(content).decode("ascii"),
            }
        }

    def _parse_response(
        self,
        payload: dict,
        query: CategoryRecommendationQuery,
    ) -> CategoryRecommendationResult:
        text = self._extract_text(payload)
        try:
            result = json.loads(text)
        except JSONDecodeError as exception:
            raise ValueError("Gemini did not return valid JSON") from exception

        allowed_ids = {candidate.id for candidate in query.candidates}
        recommended_category_id = int(result["recommendedCategoryId"])
        if recommended_category_id not in allowed_ids:
            raise ValueError("Gemini returned a category id outside candidates")

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
        candidates = payload.get("candidates") or []
        if not candidates:
            raise ValueError("Gemini response has no candidates")

        parts = candidates[0].get("content", {}).get("parts") or []
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        if not text_parts:
            raise ValueError("Gemini response has no text")
        return "\n".join(text_parts).strip()

    def _normalize_confidence(self, value: object) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.0
        return min(max(confidence, 0.0), 1.0)


class FallbackCategoryRecommender:
    def __init__(
        self,
        primary: CategoryRecommender,
        fallback: CategoryRecommender,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    def recommend_category(
        self,
        query: CategoryRecommendationQuery,
    ) -> CategoryRecommendationResult:
        try:
            return self._primary.recommend_category(query)
        except Exception as exception:
            logger.warning("Primary category recommendation failed: %s", exception)
            return self._fallback.recommend_category(query)
