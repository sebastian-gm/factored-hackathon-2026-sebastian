"""Code-owned questions for the single unresolved normalized NLU slot."""

from typing import Literal


def clarification_question(
    slot: Literal["currency", "amount", "date", "language"], language: str
) -> str:
    es, pt = {
        "amount": ("¿Cuál es el monto del cargo?", "Qual é o valor da cobrança?"),
        "currency": ("¿En qué moneda está el cargo?", "Em qual moeda está a cobrança?"),
        "date": ("¿En qué fecha aparece el cargo?", "Em que data aparece a cobrança?"),
        "language": (
            "Puedo atenderte en español o portugués. / Posso atender em espanhol ou português.",
            "Puedo atenderte en español o portugués. / Posso atender em espanhol ou português.",
        ),
    }[slot]
    return pt if language == "pt" else es
