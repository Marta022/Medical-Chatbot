from __future__ import annotations

"""Guardrail categories, reason codes, confidence policy, and user-facing messages.

Confidence policy:
- 1.00: empty input rejection
- 0.95: deterministic high-risk matches (emergency + critical unsafe)
- 0.92: deterministic soft unsafe matches
- 0.80: LLM-based decisions
- 0.60: LLM unavailable fallback
- 0.90: deterministic safe/info outcomes
"""

CATEGORY_AMBIGUOUS = "AMBIGUOUS"
CATEGORY_EMERGENCY = "EMERGENCY"
CATEGORY_INFO_ONLY = "INFO_ONLY"
CATEGORY_PERSONAL_MEDICAL = "PERSONAL_MEDICAL"
CATEGORY_SAFE = "SAFE"
CATEGORY_UNSAFE = "UNSAFE"

REASON_EMPTY_QUERY = "EMPTY_QUERY"
REASON_KEYWORD_EMERGENCY = "KEYWORD_EMERGENCY"
REASON_KEYWORD_INFO_ONLY = "KEYWORD_INFO_ONLY"
REASON_KEYWORD_PERSONAL_MEDICAL = "KEYWORD_PERSONAL_MEDICAL"
REASON_KEYWORD_UNSAFE_CRITICAL = "KEYWORD_UNSAFE_CRITICAL"
REASON_KEYWORD_UNSAFE_SOFT = "KEYWORD_UNSAFE_SOFT"
REASON_LLM_AMBIGUOUS = "LLM_AMBIGUOUS"
REASON_LLM_EMERGENCY = "LLM_EMERGENCY"
REASON_LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
REASON_LLM_UNSAFE = "LLM_UNSAFE"
REASON_SAFE = "SAFE"

CONFIDENCE_EMPTY = 1.0
CONFIDENCE_KEYWORD_HIGH_RISK = 0.95
CONFIDENCE_KEYWORD_SOFT_UNSAFE = 0.92
CONFIDENCE_LLM = 0.8
CONFIDENCE_LLM_UNAVAILABLE = 0.6
CONFIDENCE_SAFE_DETERMINISTIC = 0.9

EMPTY_QUERY_MESSAGE = "Te rog introdu o intrebare."
EMERGENCY_MESSAGE = (
    "Simptomele descrise pot indica o urgenta medicala. "
    "Suna imediat la 112 sau mergi la cel mai apropiat serviciu de urgenta."
)
UNSAFE_CRITICAL_MESSAGE = (
    "Nu pot ajuta cu aceasta solicitare. "
    "Daca exista risc imediat pentru tine sau altcineva, suna la 112 acum."
)
UNSAFE_SOFT_MESSAGE = (
    "Nu pot oferi doze exacte, prescriptii sau scheme personalizate de tratament. "
    "Discuta cu un medic licentiat pentru recomandari sigure."
)
AMBIGUOUS_MESSAGE = (
    "Nu pot oferi recomandari medicale personalizate in aceasta situatie. "
    "Consulta un medic pentru evaluare directa."
)

LABEL_AMBIGUOUS = "AMBIGUOUS"
LABEL_EMERGENCY = "EMERGENCY"
LABEL_SAFE = "SAFE"
LABEL_UNSAFE = "UNSAFE"
VALID_LLM_LABELS = (LABEL_EMERGENCY, LABEL_UNSAFE, LABEL_SAFE, LABEL_AMBIGUOUS)
