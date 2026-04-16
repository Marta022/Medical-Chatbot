from __future__ import annotations

"""LLM-backed fallback classification for guardrail decisioning."""

import logging

from config.prompts import GUARDRAIL_SYSTEM_PROMPT
from llm.llm_router import llm_classify

from agent.guardrail.policies import (
    LABEL_AMBIGUOUS,
    LABEL_EMERGENCY,
    LABEL_SAFE,
    LABEL_UNSAFE,
    VALID_LLM_LABELS,
)

logger = logging.getLogger(__name__)

GUARDRAIL_CLASSIFIER_SUFFIX = (
    " Returneaza exact o singura eticheta: EMERGENCY, UNSAFE, SAFE sau AMBIGUOUS. "
    "Nu explica raspunsul. Alege EMERGENCY daca exista risc imediat plauzibil. "
    "Alege UNSAFE pentru intentii daunatoare/interzise. "
    "Alege SAFE doar pentru continut informational benign."
)


def classify_guardrail_with_llm(query: str) -> str:
    """Classify a query into the constrained guardrail label set.

    Raises:
        ValueError: If the classifier output is empty.
    """

    response = llm_classify(
        messages=[
            {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
            {"role": "system", "content": GUARDRAIL_CLASSIFIER_SUFFIX},
            {"role": "user", "content": query},
        ],
        temperature=0,
    )

    if not response:
        raise ValueError("LLM classifier returned empty response")

    label = response.strip().upper()
    if label in VALID_LLM_LABELS:
        logger.info("guardrail_llm_classified", extra={"label": label})
        return label

    for candidate in (LABEL_EMERGENCY, LABEL_UNSAFE, LABEL_AMBIGUOUS):
        if candidate in label:
            logger.warning(
                "guardrail_llm_fuzzy_match",
                extra={"raw": label, "resolved": candidate},
            )
            return candidate

    logger.warning("guardrail_llm_unknown_label", extra={"raw": label})
    return LABEL_SAFE
