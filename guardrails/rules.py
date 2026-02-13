"""
Guardrail rules to detect emergency/unsafe queries and prevent RAG usage.
If emergency or unsafe intent is detected, bypass RAG and respond with safety guidance.
"""

import unicodedata

from config.settings import GUARDRAIL_LLM_ENABLED
from guardrails.llm_guardrail import classify_guardrail_with_llm

# Emergency keywords that trigger immediate medical referral (no RAG)
EMERGENCY_KEYWORDS = [
    # Chest/heart
    "durere in piept",
    "infarct",
    "atac cardiac",
    "presiune in piept",

    # Breathing
    "nu pot respira",
    "dificultati de respiratie",
    "greu de respirat",
    "respiratie foarte grea",

    # Loss of consciousness
    "pierdere de constiinta",
    "lesin",
    "am lesinat",
    "pierdut constiinta",

    # Severe bleeding
    "sangerare masiva",
    "sangerare severa",
    "hemoragie",

    # Accidents/trauma
    "accident",
    "ranit grav",
    "trauma grava",
    "fractura deschisa",

    # Poisoning/overdose
    "otravire",
    "supradoza",
    "otravit",
    "am inghitit otrava",
    "am luat prea multe pastile",

    # Severe allergic reaction
    "reactie alergica severa",
    "anafilaxie",
    "soc anafilactic",

    # Stroke
    "accident vascular",
    "apoplexie",
    "atac cerebral",
    "fata cazuta pe o parte",

    # Severe burns
    "arsuri grave",
    "arsuri majore",

    # Severe abdominal pain
    "durere abdominala severa",
    "dureri abdominale extreme",
]

UNSAFE_KEYWORDS = [
    # Self-harm / suicide
    "vreau sa ma sinucid",
    "ma sinucid",
    "nu mai vreau sa traiesc",
    "imi fac rau",
    "ma tai",

    # Harm to others / violence
    "vreau sa omor",
    "cum omor pe cineva",
    "cum ranesc pe cineva",

    # Illegal or dangerous drug use
    "cum fac droguri",
    "cum prepar droguri",
    "cum fac metamfetamina",
    "cum fac cocaina",

    # Unsafe medical requests
    "schema de tratament",
    "doza exacta",
    "prescrie-mi",
    "reteta",
    "antibiotic fara reteta",
    "medicamente fara reteta",
    "diagnostic sigur",
]

# General informational queries should go through RAG.
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

# First-person markers suggest personal medical context.
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


def normalize_text(text):
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower().strip()


def check_emergency_keywords(query):
    """
    Check if the query contains emergency keywords.

    Args:
        query: User input query

    Returns:
        True if emergency keywords detected, False otherwise
    """
    query_lower = normalize_text(query)

    for keyword in EMERGENCY_KEYWORDS:
        if keyword.lower() in query_lower:
            return True

    return False


def check_unsafe_keywords(query):
    """
    Check if the query contains unsafe intent keywords.

    Args:
        query: User input query

    Returns:
        True if unsafe intent detected, False otherwise
    """
    query_lower = normalize_text(query)

    for keyword in UNSAFE_KEYWORDS:
        if keyword.lower() in query_lower:
            return True

    return False


def is_general_info_query(query):
    query_lower = normalize_text(query)

    if any(marker in query_lower for marker in FIRST_PERSON_MARKERS):
        return False

    return any(pattern in query_lower for pattern in SAFE_INFO_PATTERNS)


def apply_guardrails(query):
    """
    Apply all guardrail rules to the query.

    Args:
        query: User input query

    Returns:
        dict with:
            - is_emergency: bool
            - is_unsafe: bool
            - is_valid: bool
            - message: str (guardrail message if applicable)
    """
    result = {
        "is_emergency": False,
        "is_unsafe": False,
        "is_valid": True,
        "message": None,
    }

    # Additional basic validations
    if not query or len(query.strip()) == 0:
        result["is_valid"] = False
        result["message"] = "Te rog introdu o intrebare."
        return result

    # Check for emergency keywords
    if check_emergency_keywords(query):
        result["is_emergency"] = True
        result["is_valid"] = False
        result["message"] = EMERGENCY_MESSAGE
        return result

    # Check for unsafe intent
    if check_unsafe_keywords(query):
        result["is_unsafe"] = True
        result["is_valid"] = False
        result["message"] = UNSAFE_MESSAGE
        return result

    # Optional LLM-based guardrail classification
    # Skip LLM guardrail for general informational queries so RAG can answer.
    if GUARDRAIL_LLM_ENABLED and not is_general_info_query(query):
        label = classify_guardrail_with_llm(query)
        if label == "EMERGENCY":
            result["is_emergency"] = True
            result["is_valid"] = False
            result["message"] = EMERGENCY_MESSAGE
            return result
        if label == "UNSAFE":
            result["is_unsafe"] = True
            result["is_valid"] = False
            result["message"] = UNSAFE_MESSAGE
            return result

    return result
