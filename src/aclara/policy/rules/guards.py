"""Conservative deterministic conversation guards; never infer identity or demographics."""

from __future__ import annotations

import re
import unicodedata


def normalized(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c)
    )


def _one_typo(word: str, expected: str) -> bool:
    """One insertion, deletion or substitution, only on bounded staff nouns."""
    if word == expected:
        return True
    if abs(len(word) - len(expected)) > 1:
        return False
    if len(word) == len(expected):
        return sum(a != b for a, b in zip(word, expected, strict=True)) == 1
    shorter, longer = sorted((word, expected), key=len)
    return any(longer[:i] + longer[i + 1 :] == shorter for i in range(len(longer)))


def human_request(text: str) -> bool:
    """Positive request + nearby staff noun; bounded typo tolerance, no fuzzy prose."""
    staff = ("persona", "pessoa", "humano", "humana", "agente", "atendente", "alguien", "alguem")
    for clause in re.split(r"[.;!?\n]|\b(?:pero|mas|y|e)\b", normalized(text)):
        words = re.findall(r"[a-z]+", clause)
        for i, word in enumerate(words):
            if len(word) < 5 or not any(_one_typo(word, noun) for noun in staff):
                continue
            prefix = words[max(0, i - 10) : i]
            # Standalone short requests are accepted, never third-party mentions.
            if (not prefix or prefix in (["una"], ["un"], ["uma"], ["um"])) and (
                not words[i + 1 :] or words[i + 1 :] == ["por", "favor"]
            ):
                return True
            verbs = {
                "quiero",
                "kiero",
                "necesito",
                "hablar",
                "pasame",
                "derivame",
                "quero",
                "preciso",
                "falar",
                "fale",
                "transfira",
            }
            for j, token in enumerate(prefix):
                if token not in verbs:
                    continue
                # Negation may precede a request or its nested "hablar/falar".
                if any(w in {"no", "nao", "sin", "sem"} for w in prefix):
                    continue
                contact = {
                    "hablar",
                    "falar",
                    "con",
                    "com",
                    "un",
                    "una",
                    "um",
                    "uma",
                    "a",
                    "o",
                    "al",
                    "ao",
                    "para",
                    "pra",
                    "de",
                    "que",
                    "me",
                    "mi",
                    "eu",
                    "atienda",
                    "atenda",
                    "atencion",
                    "atendimento",
                    "ayuda",
                    "ajuda",
                    "ahora",
                    "agora",
                    "por",
                    "favor",
                    "necesito",
                    "preciso",
                }
                if i - (max(0, i - 10) + j) <= 8 and all(w in contact for w in prefix[j + 1 :]):
                    return True
    return False


def escalations(text: str) -> list[str]:
    value = normalized(text)
    reasons = []
    if re.search(
        r"\b(condusef|superintendencia financiera|bcra|procon|abogado|advogado|demanda|processo|regulador|regulator)\b",
        value,
    ):
        reasons.append("ESC-02")
    # Expressed distress, allowing intensifiers ("estoy muy angustiado"). Never
    # infers protected attributes; only the customer's own stated state counts.
    if re.search(
        r"\b(?:estoy|estou|me siento|me sinto|ando|to|tô)\s+(?:(?:muy|muito|super|bastante|tan|tao|re)\s+)?"
        r"(?:desesperad|angustiad|agobiad|abrumad|sobrepasad|vulnerable|vulneravel|apavorad|aterrad)"
        r"|\bno puedo (?:mas|con esto|con todo esto)\b|\bnao (?:aguento mais|consigo lidar|dou conta)\b"
        r"|\bno tengo para comer\b|\bnao tenho dinheiro para comer\b"
        r"|\bme estan amenazando\b|\bestao me ameacando\b",
        value,
    ):
        reasons.append("ESC-03")
    if human_request(text):
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
