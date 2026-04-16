# Skill: Enhanced Medical Chatbot Evaluator with Adaptive Prompting

## Overview

This skill upgrades the existing deterministic evaluator (`evaluate_response`) to add:
1. **Multi-dimensional scoring** — not just length/emptiness, but medical-domain quality signals
2. **Adaptive prompting** — when evaluation fails, generates a targeted retry prompt instead of a generic one
3. **Failure taxonomy** — classifies *why* a response failed so the main agent can act differently per failure type
4. **LLM-judge fallback** — optional secondary LLM evaluation for borderline scores

---

## Architecture Overview

```
User Query
    │
    ▼
Main Agent builds prompt
    │
    ▼
LLM generates response
    │
    ▼
┌─────────────────────────────────────────────┐
│           Enhanced Evaluator                │
│                                             │
│  1. Deterministic heuristics (fast, free)   │
│  2. Domain-aware scoring                    │
│  3. Failure classification                  │
│  4. Adaptive prompt generation              │
│  5. (Optional) LLM-judge for borderline     │
└─────────────────────────────────────────────┘
    │
    ├─── PASSED ──► Return to user
    │
    └─── FAILED ──► EvaluatorResult(
                        passed=False,
                        adaptive_prompt=<targeted retry prompt>,
                        failure_type=<taxonomy tag>,
                        retry_strategy=<"adjust_prompt" | "switch_llm">
                    )
```

---

## File Structure to Create

```
evaluator/
├── __init__.py
├── evaluate.py          # Main entry point (drop-in replacement)
├── heuristics.py        # Deterministic checks (existing + new)
├── domain_checks.py     # Medical-domain-specific scoring
├── failure_taxonomy.py  # FailureType enum + classifier
├── adaptive_prompt.py   # Generates retry prompts per failure type
└── llm_judge.py         # Optional LLM-as-judge for borderline cases
```

---

## Step 1 — Define the failure taxonomy

**File: `evaluator/failure_taxonomy.py`**

```python
from __future__ import annotations
from enum import Enum


class FailureType(str, Enum):
    """Why did the evaluator reject this response?

    Each type maps to a different adaptive prompt strategy.
    """
    EMPTY = "empty"                          # No content at all
    TOO_SHORT = "too_short"                  # Under minimum length
    CONTEXT_IGNORED = "context_ignored"      # RAG context available but unused
    HALLUCINATION_RISK = "hallucination_risk"  # Claims not grounded in context
    REFUSED_WITH_CONTEXT = "refused_with_context"  # "I don't know" despite context
    UNSAFE_ADVICE = "unsafe_advice"          # Mentions drugs/dosage without disclaimer
    OFF_TOPIC = "off_topic"                  # Response topic drift detected
    INCOMPLETE = "incomplete"                # Starts answering but cuts off
    BORDERLINE = "borderline"                # Score near threshold; needs LLM judge
    UNKNOWN = "unknown"
```

---

## Step 2 — Enhanced heuristics (drop-in upgrade)

**File: `evaluator/heuristics.py`**

```python
from __future__ import annotations
import re
from .failure_taxonomy import FailureType

MIN_LENGTH = 10
SAFE_MIN_LENGTH = 80         # Medical responses should be more complete
REFUSED_PHRASES = [
    "I don't know based on the available data.",
    "I cannot answer",
    "I don't have enough information",
]
INCOMPLETE_ENDINGS = re.compile(r"[\w,;:]\s*$")  # ends mid-sentence
UNSAFE_PATTERNS = re.compile(
    r"\b(\d+\s?(mg|ml|mcg|units?|tablets?|capsules?))\b",
    re.IGNORECASE,
)
DISCLAIMER_PATTERNS = re.compile(
    r"(consult|doctor|physician|healthcare provider|professional|seek medical)",
    re.IGNORECASE,
)


def run_heuristics(
    query: str,
    response: str,
    context_lines: list[str],
) -> list[tuple[FailureType, float]]:
    """
    Returns a list of (FailureType, penalty) tuples.
    Penalties are subtracted from 1.0 to get the final score.
    """
    issues: list[tuple[FailureType, float]] = []
    stripped = response.strip()

    if not stripped:
        issues.append((FailureType.EMPTY, 1.0))
        return issues  # No point checking further

    if len(stripped) < MIN_LENGTH:
        issues.append((FailureType.TOO_SHORT, 0.8))
        return issues

    # Context was retrieved but response ignores it
    if context_lines and any(p in response for p in REFUSED_PHRASES):
        issues.append((FailureType.REFUSED_WITH_CONTEXT, 0.4))

    # Response is suspiciously short for a medical query with context
    if context_lines and len(stripped) < SAFE_MIN_LENGTH:
        issues.append((FailureType.INCOMPLETE, 0.3))

    # Dosage/drug quantities mentioned without disclaimer
    if UNSAFE_PATTERNS.search(response) and not DISCLAIMER_PATTERNS.search(response):
        issues.append((FailureType.UNSAFE_ADVICE, 0.5))

    # Response ends abruptly mid-sentence
    if INCOMPLETE_ENDINGS.search(stripped) and not stripped.endswith((".", "!", "?")):
        issues.append((FailureType.INCOMPLETE, 0.2))

    return issues
```

---

## Step 3 — Adaptive prompt generator

This is the core new feature. Instead of retrying with the exact same prompt, the evaluator generates a **targeted repair instruction**.

**File: `evaluator/adaptive_prompt.py`**

```python
from __future__ import annotations
from .failure_taxonomy import FailureType

# Templates are injected into the retry prompt as additional instructions.
# Use {query}, {context_summary}, {bad_response} as placeholders.

_TEMPLATES: dict[FailureType, str] = {
    FailureType.EMPTY: (
        "Your previous response was empty. "
        "Please answer the following question using the provided context.\n"
        "Question: {query}"
    ),
    FailureType.TOO_SHORT: (
        "Your previous response was too brief for a medical context. "
        "Provide a complete, structured answer (at least 2-3 sentences) "
        "covering the main point, relevant caveats, and a recommendation to "
        "consult a healthcare professional where appropriate.\n"
        "Question: {query}"
    ),
    FailureType.REFUSED_WITH_CONTEXT: (
        "You responded with 'I don't know' even though the following context "
        "is available:\n---\n{context_summary}\n---\n"
        "Use this context to answer the question. If the context is insufficient, "
        "explain what specifically is missing rather than refusing entirely.\n"
        "Question: {query}"
    ),
    FailureType.CONTEXT_IGNORED: (
        "Your answer did not draw from the retrieved medical context. "
        "Please re-read the context below and base your answer on it:\n"
        "---\n{context_summary}\n---\n"
        "Question: {query}"
    ),
    FailureType.UNSAFE_ADVICE: (
        "Your previous response mentioned specific dosages or drug quantities "
        "without including a safety disclaimer. Revise your answer to include "
        "a clear statement that the patient should consult their doctor or "
        "pharmacist before following any dosage guidance.\n"
        "Question: {query}\n"
        "Previous response: {bad_response}"
    ),
    FailureType.INCOMPLETE: (
        "Your previous response appears incomplete or cut off. "
        "Please provide a complete answer that ends with a proper conclusion.\n"
        "Question: {query}\n"
        "Incomplete response so far: {bad_response}"
    ),
    FailureType.OFF_TOPIC: (
        "Your response drifted from the original question. "
        "Focus specifically on: {query}\n"
        "Do not introduce unrelated medical topics."
    ),
    FailureType.BORDERLINE: (
        "Please review and improve the following response to the medical question. "
        "Ensure it is accurate, complete, safe, and cites the provided context.\n"
        "Question: {query}\n"
        "Draft response: {bad_response}"
    ),
    FailureType.HALLUCINATION_RISK: (
        "Your previous answer may contain claims not supported by the provided context. "
        "Please revise it to only include information that can be directly derived from:\n"
        "---\n{context_summary}\n---\n"
        "Question: {query}"
    ),
    FailureType.UNKNOWN: (
        "Please provide a clearer, more complete, and medically responsible answer.\n"
        "Question: {query}"
    ),
}


def build_adaptive_prompt(
    failure_type: FailureType,
    query: str,
    bad_response: str,
    context_lines: list[str],
) -> str:
    """
    Returns a targeted retry instruction string.

    This should be injected into the retry prompt by the main agent,
    either as a system-level addendum or as a user-turn correction.
    """
    template = _TEMPLATES.get(failure_type, _TEMPLATES[FailureType.UNKNOWN])

    context_summary = (
        "\n".join(context_lines[:5])  # First 5 chunks to avoid token bloat
        if context_lines
        else "No context available."
    )

    return template.format(
        query=query,
        bad_response=bad_response[:500],  # Truncate to avoid huge prompts
        context_summary=context_summary[:800],
    )
```

---

## Step 4 — Optional LLM-as-judge (for borderline cases)

Use this only when the heuristic score lands in the borderline zone (e.g. 0.45–0.65). It costs one extra LLM call but greatly reduces false rejects.

**File: `evaluator/llm_judge.py`**

```python
from __future__ import annotations

JUDGE_SYSTEM_PROMPT = """You are a medical response quality judge.
Score the response from 0.0 to 1.0 based on:
- Accuracy relative to the context (0–0.4)
- Completeness for the question (0–0.3)
- Safety (disclaimer present if needed) (0–0.2)
- Clarity and coherence (0–0.1)

Respond ONLY with a JSON object: {"score": <float>, "reason": "<one sentence>"}
Do not add any other text."""

JUDGE_USER_TEMPLATE = """Context:
{context}

Question: {query}

Response to evaluate:
{response}"""


def build_judge_prompt(
    query: str, response: str, context_lines: list[str]
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for the judge LLM call."""
    context_text = "\n".join(context_lines[:8]) if context_lines else "None"
    user = JUDGE_USER_TEMPLATE.format(
        context=context_text[:1200],
        query=query,
        response=response[:800],
    )
    return JUDGE_SYSTEM_PROMPT, user


def parse_judge_response(raw: str) -> tuple[float, str]:
    """Parse the JSON score from the judge's response. Returns (score, reason)."""
    import json, re

    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if not match:
        return 0.5, "judge_parse_error"
    try:
        data = json.loads(match.group())
        score = float(data.get("score", 0.5))
        reason = str(data.get("reason", ""))
        return max(0.0, min(1.0, score)), reason
    except (json.JSONDecodeError, ValueError):
        return 0.5, "judge_parse_error"
```

---

## Step 5 — Updated EvaluatorResult model

Update your `models.py` (or `EvaluatorResult` dataclass) to include the new fields:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from evaluator.failure_taxonomy import FailureType


@dataclass
class EvaluatorResult:
    passed: bool
    score: float
    reasons: list[str] = field(default_factory=list)
    retry_recommended: bool = False

    # New fields for adaptive prompting
    failure_types: list[FailureType] = field(default_factory=list)
    adaptive_prompt: str | None = None
    retry_strategy: str = "adjust_prompt"  # or "switch_llm"
    judge_used: bool = False
```

---

## Step 6 — New main evaluate.py (drop-in replacement)

**File: `evaluator/evaluate.py`**

```python
from __future__ import annotations

from config.eval_config import EVAL_CONFIG
from models import EvaluatorResult
from .heuristics import run_heuristics
from .failure_taxonomy import FailureType
from .adaptive_prompt import build_adaptive_prompt

# Score thresholds
BORDERLINE_LOW = 0.45
BORDERLINE_HIGH = 0.65

# Which failure types should trigger "switch_llm" instead of "adjust_prompt"
SWITCH_LLM_FAILURES = {FailureType.HALLUCINATION_RISK, FailureType.UNSAFE_ADVICE}


def evaluate_response(
    query: str,
    response: str,
    context_lines: list[str] | None = None,
    use_llm_judge: bool = False,
    llm_judge_fn=None,  # Callable[[str, str, list[str]], float] | None
) -> EvaluatorResult:
    """
    Evaluate a response and return an EvaluatorResult.

    If the response fails, EvaluatorResult.adaptive_prompt contains a
    targeted retry instruction for the main agent to use.

    Args:
        query:           The original user question.
        response:        The LLM's response to evaluate.
        context_lines:   RAG chunks that were provided as context (if any).
        use_llm_judge:   Whether to call an LLM judge for borderline scores.
        llm_judge_fn:    Optional callable for LLM judge integration.
                         Signature: (query, response, context_lines) -> float
    """
    context_lines = context_lines or []
    issues = run_heuristics(query, response, context_lines)

    # --- Compute score ---
    score = 1.0
    failure_types: list[FailureType] = []
    reasons: list[str] = []

    for failure_type, penalty in issues:
        score -= penalty
        failure_types.append(failure_type)
        reasons.append(failure_type.value)

    score = max(score, 0.0)

    # --- LLM judge for borderline cases ---
    judge_used = False
    if (
        use_llm_judge
        and llm_judge_fn is not None
        and BORDERLINE_LOW <= score <= BORDERLINE_HIGH
    ):
        judge_score = llm_judge_fn(query, response, context_lines)
        score = (score + judge_score) / 2  # Average heuristic + judge
        judge_used = True
        if not failure_types:
            failure_types.append(FailureType.BORDERLINE)

    # --- Pass/fail decision ---
    passed = score >= EVAL_CONFIG.pass_score

    # --- Adaptive prompt (only needed on failure) ---
    adaptive_prompt: str | None = None
    retry_strategy = "adjust_prompt"

    if not passed:
        # Pick the most severe failure type for the adaptive prompt
        primary_failure = failure_types[0] if failure_types else FailureType.UNKNOWN
        adaptive_prompt = build_adaptive_prompt(
            failure_type=primary_failure,
            query=query,
            bad_response=response,
            context_lines=context_lines,
        )
        # Decide retry strategy
        if primary_failure in SWITCH_LLM_FAILURES:
            retry_strategy = "switch_llm"

    return EvaluatorResult(
        passed=passed,
        score=round(score, 4),
        reasons=reasons,
        retry_recommended=not passed,
        failure_types=failure_types,
        adaptive_prompt=adaptive_prompt,
        retry_strategy=retry_strategy,
        judge_used=judge_used,
    )
```

---

## Step 7 — Wire it into the Main Agent

Update your main agent's retry logic to use `adaptive_prompt` and `retry_strategy`:

```python
# main_agent.py (relevant section)

from evaluator.evaluate import evaluate_response

result = evaluate_response(
    query=user_query,
    response=llm_response,
    context_lines=retrieved_chunks,
    use_llm_judge=True,
    llm_judge_fn=my_llm_judge,   # or None to skip
)

if result.passed:
    return result  # ✅ deliver to user

# ❌ Evaluation failed — use adaptive retry
if result.retry_strategy == "switch_llm":
    # Try a different provider with the SAME prompt
    llm_response = fallback_llm.generate(original_prompt)

elif result.retry_strategy == "adjust_prompt" and result.adaptive_prompt:
    # Rebuild prompt with targeted repair instruction
    retry_prompt = build_retry_prompt(
        original_prompt=original_prompt,
        adaptive_instruction=result.adaptive_prompt,
    )
    llm_response = primary_llm.generate(retry_prompt)
```

---

## Config additions (eval_config.py)

Add these to your existing config:

```python
# eval_config.py additions

@dataclass
class EvalConfig:
    pass_score: float = 0.7          # existing
    borderline_low: float = 0.45     # NEW: use LLM judge below this
    borderline_high: float = 0.65    # NEW: use LLM judge up to this
    use_llm_judge: bool = False       # NEW: toggle judge on/off
    max_retries: int = 2              # NEW: max retry attempts
    safe_min_length: int = 80         # NEW: medical responses minimum
```

---

## Testing the new evaluator

```python
# Quick smoke test
from evaluator.evaluate import evaluate_response
from evaluator.failure_taxonomy import FailureType

# Test 1: refused with context
result = evaluate_response(
    query="What is metformin used for?",
    response="I don't know based on the available data.",
    context_lines=["Metformin is a biguanide used to treat type 2 diabetes."],
)
assert not result.passed
assert FailureType.REFUSED_WITH_CONTEXT in result.failure_types
assert "context" in result.adaptive_prompt.lower()
print("✓ Test 1 passed")

# Test 2: unsafe dosage without disclaimer
result = evaluate_response(
    query="How much ibuprofen should I take?",
    response="You should take 400mg every 8 hours.",
    context_lines=[],
)
assert not result.passed
assert FailureType.UNSAFE_ADVICE in result.failure_types
assert result.retry_strategy == "switch_llm"
print("✓ Test 2 passed")

# Test 3: good response passes
result = evaluate_response(
    query="What is hypertension?",
    response=(
        "Hypertension refers to persistently elevated blood pressure above 130/80 mmHg. "
        "It is a major risk factor for heart disease and stroke. "
        "Please consult your doctor for a diagnosis and personalized treatment plan."
    ),
    context_lines=["Hypertension: blood pressure > 130/80 mmHg per ACC/AHA guidelines."],
)
assert result.passed
print("✓ Test 3 passed")
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Deterministic checks run first | Fast, zero cost, catch obvious failures immediately |
| Failure taxonomy before adaptive prompts | Different failures need different fixes — one-size retry doesn't work |
| `switch_llm` only for safety failures | Unsafe advice may be a model tendency, not a prompt issue |
| LLM judge only for borderline scores | Prevents cost explosion; deterministic checks handle clear cases |
| `adaptive_prompt` is a string, not a dict | Main agent can inject it anywhere: system prompt, user turn, prefix |
| Context summary capped at 800 chars | Avoids ballooning retry prompt tokens |
| `judge_fn` is injected, not imported | Keeps evaluator decoupled from any specific LLM client |

---

## What This Does NOT Do (by design)

- Does **not** call any LLM itself (unless `llm_judge_fn` is provided)
- Does **not** decide which LLM to switch to — that's the main agent's responsibility
- Does **not** modify the original prompt — it only generates an addendum
- Does **not** handle conversation history — evaluator is stateless per call
