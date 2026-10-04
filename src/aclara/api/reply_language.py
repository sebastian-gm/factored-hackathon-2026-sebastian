"""Conversation language and verified receipt text, without model calls."""

from __future__ import annotations

import re
from typing import Any

from aclara.agent.contracts import ResponsePlan
from aclara.agent.nlg.builder import render_template
from aclara.agent.nlg.grounding import scan_dlp
from aclara.agent.nlu.rules import detect_language_evidence, normalize_text


def conversation_language(message: str, current: str, merchants: tuple[str, ...]) -> str:
    text = normalize_text(message)
    for merchant in merchants:
        if merchant.strip():
            text = text.replace(normalize_text(merchant), " ")
    requested = re.search(
        r"\b(?:responder|responda|responde|respondas|habla|hablar|fale|falar)\b"
        r"[^.!?]{0,40}\b(?:en|em)\s+(espanol|castellano|portugues)\b",
        text,
    )
    if requested:
        return "pt" if requested.group(1) == "portugues" else "es"
    evidence = detect_language_evidence(message, ignored_terms=merchants)
    return current if evidence == "uncertain" else evidence


def receipt_reply(response: dict[str, Any], language: str) -> str:
    """Re-render only text after the caller verifies the stored receipt facts."""
    plan = ResponsePlan.model_validate(response)
    if plan.case and not re.fullmatch(r"DSP-[A-Za-z0-9-]{1,32}", plan.case.case_id):
        raise ValueError("Invalid verified case reference")
    if plan.response_type == "report_status":
        if plan.case is None or plan.verified is not True:
            raise ValueError("Cannot render an unverified status receipt")
        text = (
            f"O caso {plan.case.case_id} tem status {plan.case.status}."
            if language == "pt"
            else f"El caso {plan.case.case_id} tiene estado {plan.case.status}."
        )
    else:
        text = render_template(plan, language=language)
    checked = text.replace(plan.case.case_id, "[VERIFIED_CASE]") if plan.case else text
    if scan_dlp(checked):
        raise ValueError("Receipt template contains sensitive content")
    return text
