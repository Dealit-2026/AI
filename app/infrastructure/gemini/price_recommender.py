import asyncio
import base64
import json
import logging
import mimetypes
from dataclasses import asdict
from json import JSONDecodeError

import httpx

from app.domain.recommendation.models import (
    PriceRecommendationQuery,
    PriceRecommendationResult,
)
from app.domain.recommendation.recommenders import PriceRecommender
from app.infrastructure.gemini.category_recommender import GeminiRequestError


logger = logging.getLogger(__name__)


class GeminiPriceRecommender:
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

    def recommend_price(
        self,
        query: PriceRecommendationQuery,
    ) -> PriceRecommendationResult:
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        parts = [{"text": self._build_prompt(query)}]
        parts.extend(asyncio.run(self._build_image_parts(query.image_urls)))

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self._model}:generateContent"
        )
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": 0,
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

        return self._parse_response(response.json())

    def _format_error_response(self, response: httpx.Response) -> str:
        try:
            error_body = response.json()
        except JSONDecodeError:
            error_body = response.text[:1000]
        return f"status={response.status_code}, body={error_body}"

    def _build_prompt(self, query: PriceRecommendationQuery) -> str:
        recent_prices = [asdict(price) for price in query.recent_prices[:20]]
        return (
            "You estimate a fair secondhand marketplace listing price in KRW.\n"
            "Use title, description, category, images if provided, and recent comparable prices if provided.\n"
            "Return a realistic range for a seller listing price, not the original retail price.\n"
            "If comparable prices are provided, prioritize their median and distribution over general knowledge.\n"
            "All prices must be integers in Korean won and must satisfy: "
            "suggestedPriceMin <= suggestedPrice <= suggestedPriceMax.\n"
            "Never return negative prices. Return only JSON with this shape: "
            '{"suggestedPriceMin": number, "suggestedPrice": number, '
            '"suggestedPriceMax": number, "confidence": number, "reason": string, '
            '"factors": [string]}.\n'
            f"Title: {query.title or ''}\n"
            f"Description: {query.description or ''}\n"
            f"Category ID: {query.category_id or ''}\n"
            f"Category name: {query.category_name or ''}\n"
            f"Sale type: {query.sale_type or ''}\n"
            f"Recent prices: {json.dumps(recent_prices, ensure_ascii=False)}"
        )

    async def _build_image_parts(self, image_urls: tuple[str, ...]) -> list[dict]:
        urls = image_urls[:3]
        if not urls:
            return []

        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            follow_redirects=True,
        ) as client:
            return await asyncio.gather(
                *(self._download_image_part(client, image_url) for image_url in urls)
            )

    async def _download_image_part(self, client: httpx.AsyncClient, image_url: str) -> dict:
        response = await client.get(image_url)
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

    def _parse_response(self, payload: dict) -> PriceRecommendationResult:
        text = self._extract_text(payload)
        try:
            result = json.loads(text)
        except JSONDecodeError as exception:
            raise ValueError("Gemini did not return valid JSON") from exception

        suggested_price_min = self._normalize_price(result["suggestedPriceMin"])
        suggested_price = self._normalize_price(result["suggestedPrice"])
        suggested_price_max = self._normalize_price(result["suggestedPriceMax"])
        if not suggested_price_min <= suggested_price <= suggested_price_max:
            raise ValueError("Gemini returned an invalid price range")

        return PriceRecommendationResult(
            suggested_price_min=suggested_price_min,
            suggested_price=suggested_price,
            suggested_price_max=suggested_price_max,
            confidence=self._normalize_confidence(result.get("confidence", 0)),
            reason=str(result.get("reason", ""))[:500],
            factors=tuple(str(factor)[:80] for factor in result.get("factors", [])[:6]),
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

    def _normalize_price(self, value: object) -> int:
        price = int(float(value))
        if price < 0:
            raise ValueError("price cannot be negative")
        return price

    def _normalize_confidence(self, value: object) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.0
        return min(max(confidence, 0.0), 1.0)


class FallbackPriceRecommender:
    def __init__(
        self,
        primary: PriceRecommender,
        fallback: PriceRecommender,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    def recommend_price(
        self,
        query: PriceRecommendationQuery,
    ) -> PriceRecommendationResult:
        try:
            return self._primary.recommend_price(query)
        except Exception as exception:
            logger.warning("Primary price recommendation failed: %s", exception)
            return self._fallback.recommend_price(query)
