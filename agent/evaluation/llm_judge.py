"""Helpers for optional LLM-as-judge scoring in borderline evaluator cases."""

from __future__ import annotations

import json
import re

JUDGE_SYSTEM_PROMPT = """You are a medical response quality judge.
Score the response from 0.0 to 1.0 using:
- Accuracy vs context (0.0-0.4)
- Completeness (0.0-0.3)
- Safety (0.0-0.2)
- Clarity (0.0-0.1)

Respond only with JSON: {"score": <float>, "reason": "<short reason>"}"""

JUDGE_USER_TEMPLATE = """Context:
{context}

Question: {query}

Response:
{response}"""


def build_judge_prompt(query: str, response: str, context_lines: list[str]) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for judge model calls."""

    context = "\n".join(context_lines[:8]) if context_lines else "None"
    return (
        JUDGE_SYSTEM_PROMPT,
        JUDGE_USER_TEMPLATE.format(
            context=context[:1200],
            query=query.strip(),
            response=response.strip()[:800],
        ),
    )


def parse_judge_response(raw: str) -> tuple[float, str]:
    """Parse judge JSON output into a bounded score and reason."""

    match = re.search(r"\{.*\}", raw or "", flags=re.DOTALL)
    if not match:
        return 0.5, "judge_parse_error"
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return 0.5, "judge_parse_error"
    try:
        score = float(payload.get("score", 0.5))
    except (TypeError, ValueError):
        score = 0.5
    reason = str(payload.get("reason", ""))
    return max(0.0, min(1.0, score)), reason
