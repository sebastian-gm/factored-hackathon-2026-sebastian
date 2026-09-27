"""Thin adapters; only normalized text and usage leave this module."""

from __future__ import annotations

import json
from collections.abc import Callable
from importlib import import_module
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel

from aclara.llm.types import ModelFailure, ModelSpec, ProviderResponse, TokenUsage


class Provider(Protocol):
    def complete(
        self, spec: ModelSpec, system: str, user: str, schema: type[BaseModel], key: str
    ) -> ProviderResponse: ...


def _provider_schema(value: Any) -> Any:
    """Use the common strict-schema subset; Pydantic enforces removed constraints locally."""
    if isinstance(value, list):
        return [_provider_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    unsupported = {
        "default",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "pattern",
        "examples",
    }
    cleaned = {key: _provider_schema(item) for key, item in value.items() if key not in unsupported}
    if cleaned.get("type") == "object" and "properties" in cleaned:
        cleaned["required"] = list(cleaned["properties"])
        cleaned["additionalProperties"] = False
    return cleaned


class OpenAICompat:
    def complete(
        self, spec: ModelSpec, system: str, user: str, schema: type[BaseModel], key: str
    ) -> ProviderResponse:
        if not spec.base_url or not spec.base_url.startswith("https://"):
            raise ModelFailure("OpenAI-compatible endpoint requires an HTTPS base URL")
        schema_json = _provider_schema(schema.model_json_schema())
        response_format: dict[str, Any]
        if spec.output_mode == "json_schema":
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "strict": True, "schema": schema_json},
            }
        else:
            response_format = {"type": "json_object"}
            system += "\nReturn one JSON object matching this schema: " + json.dumps(schema_json)
        payload: dict[str, Any] = {
            "model": spec.model_id,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": response_format,
            "max_tokens": 1024,
        }
        if spec.base_url.rstrip("/") == "https://openrouter.ai/api/v1":
            payload["provider"] = {"data_collection": "deny", "zdr": True}
            if spec.output_mode == "json_schema":
                payload["provider"]["require_parameters"] = True
            if spec.price_ceiling is not None:
                payload["provider"]["max_price"] = {
                    "prompt": spec.price_ceiling[0],
                    "completion": spec.price_ceiling[1],
                    "request": 0,
                }
        request = Request(  # noqa: S310 - HTTPS base URL is checked above
            f"{spec.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=spec.timeout_seconds) as response:  # noqa: S310 - HTTPS URL checked above
                data = json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            raise ModelFailure("OpenAI-compatible request failed") from exc
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage = data.get("usage") or {}
            prompt_details = usage.get("prompt_tokens_details") or {}
            usage_known = (
                all(
                    isinstance(usage.get(field), int)
                    and not isinstance(usage[field], bool)
                    and usage[field] >= 0
                    for field in ("prompt_tokens", "completion_tokens")
                )
                and usage["prompt_tokens"] > 0
            )
            return ProviderResponse(
                text=content if isinstance(content, str) else "",
                model_id=str(data.get("model") or spec.model_id),
                usage=TokenUsage(
                    input_tokens=int(usage.get("prompt_tokens") or 0),
                    output_tokens=int(usage.get("completion_tokens") or 0),
                    cache_read_tokens=int(prompt_details.get("cached_tokens") or 0),
                ),
                stop_reason=choice.get("finish_reason"),
                usage_known=usage_known,
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ModelFailure("Malformed provider response") from exc


class Gemini:
    def complete(
        self, spec: ModelSpec, system: str, user: str, schema: type[BaseModel], key: str
    ) -> ProviderResponse:
        try:
            genai = import_module("google.genai")
        except ImportError as exc:
            raise ModelFailure("Install the llm extra for Gemini") from exc
        client = genai.Client(api_key=key)
        config: dict[str, Any] = {
            "system_instruction": system,
            "response_mime_type": "application/json",
            "max_output_tokens": 1024,
        }
        if spec.output_mode == "json_schema":
            config["response_schema"] = schema
        else:
            config["system_instruction"] = (
                system
                + "\nReturn one JSON object matching this schema: "
                + json.dumps(_provider_schema(schema.model_json_schema()))
            )
        try:
            response = client.models.generate_content(
                model=spec.model_id, contents=user, config=config
            )
        except Exception as exc:
            raise ModelFailure("Gemini request failed") from exc
        usage = response.usage_metadata
        return ProviderResponse(
            text=response.text or "",
            model_id=response.model_version or spec.model_id,
            usage=TokenUsage(
                input_tokens=int(usage.prompt_token_count or 0) if usage else 0,
                output_tokens=int(usage.candidates_token_count or 0) if usage else 0,
                cache_read_tokens=int(usage.cached_content_token_count or 0) if usage else 0,
            ),
            stop_reason=str(response.candidates[0].finish_reason) if response.candidates else None,
        )


class Anthropic:
    def complete(
        self, spec: ModelSpec, system: str, user: str, schema: type[BaseModel], key: str
    ) -> ProviderResponse:
        try:
            anthropic = import_module("anthropic")
        except ImportError as exc:
            raise ModelFailure("Install the llm extra for Anthropic") from exc
        client = anthropic.Anthropic(api_key=key, timeout=20.0, max_retries=0)
        try:
            response = client.messages.parse(
                model=spec.model_id,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=schema,
            )
        except Exception as exc:
            raise ModelFailure("Anthropic request failed") from exc
        content = next((part.text for part in response.content if part.type == "text"), "")
        usage = response.usage
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
        return ProviderResponse(
            text=content,
            model_id=response.model,
            usage=TokenUsage(
                input_tokens=usage.input_tokens + cache_read + cache_write,
                output_tokens=usage.output_tokens,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
            ),
            stop_reason=response.stop_reason,
        )


class Mock:
    def __init__(self, response: Callable[[str, str, type[BaseModel]], str]):
        self.response = response

    def complete(
        self, spec: ModelSpec, system: str, user: str, schema: type[BaseModel], key: str
    ) -> ProviderResponse:
        return ProviderResponse(
            text=self.response(system, user, schema), model_id=spec.model_id, usage=TokenUsage()
        )


class Recorded:
    def __init__(self, cassettes: dict[str, str]):
        self.cassettes = cassettes

    def complete(
        self, spec: ModelSpec, system: str, user: str, schema: type[BaseModel], key: str
    ) -> ProviderResponse:
        # Caller supplies fixture-only keys. No raw prompts are stored here or in call records.
        if user not in self.cassettes:
            raise ModelFailure("No fixture cassette for this request")
        return ProviderResponse(self.cassettes[user], spec.model_id, TokenUsage())
