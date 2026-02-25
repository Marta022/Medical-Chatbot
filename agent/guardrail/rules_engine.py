from __future__ import annotations

import logging
import unicodedata

from agent.guardrail.llm_classifier import classify_guardrail_with_llm
from config.settings import GUARDRAIL_LLM_ENABLED
from models import GuardrailResult

logger = logging.getLogger(__name__)

EMERGENCY_KEYWORDS = [
    "durere in piept",
    "infarct",
    "atac cardiac",
    "presiune in piept",
    "nu pot respira",
    "dificultati de respiratie",
    "greu de respirat",
    "respiratie foarte grea",
    "pierdere de constiinta",
    "lesin",
    "am lesinat",
    "pierdut constiinta",
    "sangerare masiva",
    "sangerare severa",
    "hemoragie",
    "accident",
    "ranit grav",
    "trauma grava",
    "fractura deschisa",
    "otravire",
    "supradoza",
    "otravit",
    "am inghitit otrava",
    "am luat prea multe pastile",
    "reactie alergica severa",
    "anafilaxie",
    "soc anafilactic",
    "accident vascular",
    "apoplexie",
    "atac cerebral",
    "fata cazuta pe o parte",
    "arsuri grave",
    "arsuri majore",
    "durere abdominala severa",
    "dureri abdominale extreme",
    "nu pot sa respir",
    "respiratie grea",
    "respir greu",
    "sangerare care nu se opreste",
    "plaga adanca",
    "rana adanca",
    "durere puternica in piept",
    "pierdere brusca a vederii",
    "nu pot vorbi",
    "confuzie brusca",
    "convulsii",
]

UNSAFE_KEYWORDS = [
    "vreau sa ma sinucid",
    "ma sinucid",
    "nu mai vreau sa traiesc",
    "imi fac rau",
    "ma tai",
    "vreau sa omor",
    "cum omor pe cineva",
    "cum ranesc pe cineva",
    "cum fac droguri",
    "cum prepar droguri",
    "cum fac metamfetamina",
    "cum fac cocaina",
    "schema de tratament",
    "doza exacta",
    "prescrie-mi",
    "reteta",
    "antibiotic fara reteta",
    "medicamente fara reteta",
    "diagnostic sigur",
    "sinucidere",
    "suicid",
    "cum sa ma sinucid",
    "cum sa imi fac rau",
    "doza precisa",
    "doza exacta pentru",
    "tratament exact",
    "tratament personalizat",
    "schema exacta",
    "amestec droguri",
    "cum se face heroina",
    "cum se face metamfetamina",
]

SAFE_INFO_PATTERNS = [
    "ce simptome",
    "care sunt simptomele",
    "simptomele",
    "ce boala",
    "ce este",
    "ce inseamna",
    "definitie",
    "cauze",
    "factori de risc",
    "prevenire",
    "complicatii",
    "tratament",
]

FIRST_PERSON_MARKERS = [
    "am ",
    "imi ",
    "ma ",
    "m ",
    "eu ",
    "simt ",
    "ma simt",
]

EMERGENCY_MESSAGE = (
    "Simptomele descrise pot indica o urgenta medicala. "
    "Nu pot oferi sfaturi medicale in aceasta situatie. "
    "Suna acum la 112 sau 911 ori mergi de urgenta la cel mai apropiat spital."
)

UNSAFE_MESSAGE = (
    "Nu pot ajuta cu aceasta solicitare. "
    "Daca te simti in pericol sau ai ganduri de auto-vatamare, "
    "cauta ajutor imediat: suna la 112, sau mergi la camera de garda."
)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower().strip()


def check_emergency_keywords(query: str) -> bool:
    query_lower = normalize_text(query)
    return any(keyword in query_lower for keyword in EMERGENCY_KEYWORDS)


def check_unsafe_keywords(query: str) -> bool:
    query_lower = normalize_text(query)
    return any(keyword in query_lower for keyword in UNSAFE_KEYWORDS)


def is_general_info_query(query: str) -> bool:
    query_lower = normalize_text(query)
    if any(marker in query_lower for marker in FIRST_PERSON_MARKERS):
        return False
    return any(pattern in query_lower for pattern in SAFE_INFO_PATTERNS)


def apply_guardrails(query: str) -> GuardrailResult:
    if not query or not query.strip():
        result = GuardrailResult(
            is_valid=False,
            message="Te rog introdu o intrebare.",
            reason_code="EMPTY_QUERY",
            confidence=1.0,
        )
        logger.info("guardrail_blocked", extra={"reason_code": result.reason_code})
        return result

    if check_emergency_keywords(query):
        result = GuardrailResult(
            is_emergency=True,
            is_valid=False,
            message=EMERGENCY_MESSAGE,
            reason_code="KEYWORD_EMERGENCY",
            confidence=0.95,
        )
        logger.warning("guardrail_emergency", extra={"reason_code": result.reason_code})
        return result

    if check_unsafe_keywords(query):
        result = GuardrailResult(
            is_unsafe=True,
            is_valid=False,
            message=UNSAFE_MESSAGE,
            reason_code="KEYWORD_UNSAFE",
            confidence=0.95,
        )
        logger.warning("guardrail_unsafe", extra={"reason_code": result.reason_code})
        return result

    if GUARDRAIL_LLM_ENABLED and not is_general_info_query(query):
        try:
            label = classify_guardrail_with_llm(query)
        except Exception as exc:
            logger.exception("guardrail_llm_unavailable", extra={"error": str(exc)})
            return GuardrailResult(
                is_valid=True,
                reason_code="LLM_UNAVAILABLE",
                confidence=0.6,
            )
        if label == "EMERGENCY":
            result = GuardrailResult(
                is_emergency=True,
                is_valid=False,
                message=EMERGENCY_MESSAGE,
                reason_code="LLM_EMERGENCY",
                confidence=0.8,
            )
            logger.warning("guardrail_emergency", extra={"reason_code": result.reason_code})
            return result
        if label == "UNSAFE":
            result = GuardrailResult(
                is_unsafe=True,
                is_valid=False,
                message=UNSAFE_MESSAGE,
                reason_code="LLM_UNSAFE",
                confidence=0.8,
            )
            logger.warning("guardrail_unsafe", extra={"reason_code": result.reason_code})
            return result

    result = GuardrailResult(
        is_valid=True,
        reason_code="SAFE",
        confidence=0.9,
    )
    logger.info("guardrail_safe", extra={"reason_code": result.reason_code})
    return result
