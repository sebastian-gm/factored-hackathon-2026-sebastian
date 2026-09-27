"""Conservative deterministic conversation guards; never infer identity or demographics."""

from __future__ import annotations

import re
import unicodedata


def normalized(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c)
    )


def escalations(text: str) -> list[str]:
    value = normalized(text)
    reasons = []
    if re.search(
        r"\b(condusef|superintendencia financiera|bcra|procon|abogado|advogado|demanda|processo|regulador|regulator)\b",
        value,
    ):
        reasons.append("ESC-02")
    if any(
        t in value
        for t in (
            "estoy desesperad",
            "estou desesperad",
            "no puedo mas",
            "nao aguento mais",
            "no tengo para comer",
            "nao tenho dinheiro para comer",
            "estoy angustiad",
            "estou angustiad",
            "me siento vulnerable",
            "estou vulneravel",
            "me estan amenazando",
            "estao me ameacando",
        )
    ):
        reasons.append("ESC-03")
    if re.search(r"\b(persona|pessoa|humano|agente|atendente|falar com alguem)\b", value):
        reasons.append("ESC-01")
    return reasons


def escalation(text: str) -> str | None:
    return next((reason for reason in escalations(text) if reason != "ESC-01"), None)


def cross_customer(text: str) -> bool:
    value = normalized(text)
    # Describing an unknown purchase's actor is not a request for their records.
    value = re.sub(
        r"\b(?:lo hizo|la hizo|fue|foi|quem fez foi) (?:otra persona|outra pessoa)\b", "", value
    )
    return bool(
        re.search(
            r"\b(otro cliente|otra persona|outro cliente|outra pessoa|other customer|other account|soy el esposo|soy la esposa|minha esposa|meu marido|cuenta de mi|conta de|minha mae|mi esposa|mi esposo|documento|cedula|cpf|dni)\b",
            value,
        )
    )


def injection(text: str) -> bool:
    value = normalized(text)
    return bool(
        re.search(
            r"(ignora|ignore|ignorar|olvida|forget|desconsidera).{0,50}(instru|regla|rule|policy|sistema)|system\s*prompt|prompt\s*(del|do|de)\s*sistema|instrucciones internas|instrucoes internas|developer message|system:|<\|.*?\|>|revela.{0,30}(prompt|secreto)|reveal.{0,30}(prompt|secret)|actua como administrador|aja como administrador",
            value,
        )
    )


def unsupported_language(text: str) -> bool:
    value = normalized(text)
    return bool(
        re.search(
            r"\b(i need|i want|please|bonjour|je veux|ich |hello|my card|my account|do not recognize)\b",
            value,
        )
    )
