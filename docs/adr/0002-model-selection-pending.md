# ADR-0002: Provider adapter and deferred model selection

Date: 2026-09-26. Status: proposed.

## Context

The brief's initial Claude-first model choice was superseded by the AI-lane handoff: compare lower-cost models first and reserve Claude for final testing. A single OpenRouter key should cover round 1, with direct Gemini, DeepSeek, xAI, Qwen, and Anthropic paths optional.

## Options

Use one provider SDK only; use OpenRouter for every model; or use a small provider-neutral boundary with OpenAI-compatible, Gemini, Anthropic, mock, and recorded adapters.

## Decision

Use the provider-neutral boundary, Pydantic validation after every response, one retry, metadata-only call records, dated prices, and a fail-closed real-call/budget gate. Keep `nlu` and `phrase` routes on mock until a measured same-case comparison is reviewed. Prefer OpenRouter endpoints that deny collection and require zero data retention for candidate tests.

## Consequences and revisit

Provider-specific JSON behavior and privacy routing may reduce availability. A model is chosen only after the dev table reports accuracy, slot F1, JSON validity, ES/PT quality, latency, and cost, and its data terms are accepted. Revisit the adapter if an endpoint cannot meet the privacy and schema controls.
