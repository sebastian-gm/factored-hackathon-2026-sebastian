"""Conservative deterministic conversation guards; never infer identity or demographics."""

from __future__ import annotations

import re
import unicodedata


def normalized(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c)
    )


def escalation(text: str) -> str | None:
    value = normalized(text)
    if re.search(
        r"\b(condusef|superintendencia financiera|bcra|procon|abogado|advogado|demanda|processo|regulador|regulator)\b",
        value,
    ):
        return "ESC-02"
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
        return "ESC-03"
    return None


def cross_customer(text: str) -> bool:
    value = normalized(text)
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
