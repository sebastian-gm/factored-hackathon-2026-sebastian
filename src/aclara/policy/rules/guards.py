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
        r"\b(condusef|superintendencia financiera|bcra|procon|abogado|advogado|regulador|regulator)\b"
        r"|\b(?:demanda|processo)\s+judicial\b|\bjudicial\s+(?:demanda|processo)\b"
        r"|\bentrar com (?:um |o )?processo\b",
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
    """Require a request for someone else's records, never a family/ID mention."""
    # Identifier dots are formatting, not clause boundaries. Normalize only the
    # bounded CPF/DNI/cédula/RUT span; keep actual sentence punctuation intact.
    value = re.sub(
        r"\b(?:cpf|dni|cedula|rut|documento)\s*(?:numero\s*)?[:#]?\s*"
        r"\d[\d. -]*[\dk]\b",
        lambda match: match.group(0).replace(".", ""),
        normalized(text),
    )
    access = re.compile(
        r"\b(?:ver|mostrar|mostre|mostra|muestrame|muestre|muestra|consultar|consulta|"
        r"consulte|abrir|abre|abra|acceder|accede|acessar|acessa|acesse|revisar|revisa|"
        r"revise|busca|buscar|exibir|exiba|movimientos|saldo|extrato|datos|dados)\b"
    )
    person = (
        r"(?:(?:otro|otra|outro|outra)\s+(?:cliente|persona|pessoa)|"
        r"(?:(?:mi|mis|minha|meu|minhas|meus)\s+)?"
        r"(?:espos[oa]|marido|madre|padre|mae|pai|herman[oa]|irma[oa])|el titular|o titular)"
    )
    records = (
        r"(?:cuenta|conta|cargos?|cobros?|cobrancas?|movimientos|saldo|extrato|datos|dados|"
        r"tarjeta|cartao|cpf|dni|cedula|rut|documento)"
    )
    target = re.compile(
        rf"\b{records}\s+(?:de|del|do|da|dessa|daquela|desse|daquele)\s+{person}\b|"
        r"\b(?:otra cuenta|conta alheia|cuenta ajena|other account)\b|"
        # Using a supplied identifier to look up a different account is access;
        # merely asking which document to bring is not.
        r"\b(?:cpf|dni|cedula|rut|documento)\s*(?:numero\s*)?[:#]?\s*\d[\d. -]{4,}k?\b|"
        rf"\b(?:cuenta|conta)\b.{{0,30}}\b(?:con|com|pelo|por)\b.{{0,12}}"
        r"\b(?:cpf|dni|cedula|rut|documento)\b"
    )
    return any(
        access.search(clause)
        and target.search(
            # An explicitly self-owned record is not a third-party target.
            re.sub(
                r"\b(?:mi|mis|minha|meu|minhas|meus)\s+"
                r"(?:cpf|dni|cedula|rut|documento)\s*(?:numero\s*)?[:#]?\s*\d[\d. -]*k?",
                "",
                clause,
            )
        )
        for clause in re.split(r"[.!?;\n]", value)
    )


def injection(text: str) -> bool:
    value = normalized(text)
    return bool(
        re.search(
            r"(ignora|ignore|ignorar|olvida|forget|desconsider[ae]).{0,50}(instru|regla|regra|rule|policy|politica|sistema)|system\s*prompt|prompt\s*(del|do|de)\s*sistema|instrucciones internas|instrucoes internas|developer message|system:|<\|.*?\|>|revela.{0,30}(prompt|secreto)|reveal.{0,30}(prompt|secret)|actua como administrador|aja como administrador",
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
