---
name: build-guardrail-agent
description: Design, extend, and harden a medical chatbot guardrail agent using deterministic rules, LLM fallback, and structured safety policies
argument-hint: <folder-path>
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Build Guardrail Agent

Systematically design, refactor, and harden the medical guardrail agent inside `$ARGUMENTS`
so it becomes safer, more modular, easier to maintain, and easier to evaluate.

The goal is to produce a **deterministic-first, LLM-assisted guardrail layer** that can:
- detect emergencies,
- detect unsafe / self-harm / violence / drug-related prompts at two severity levels,
- distinguish informational questions from personal medical situations,
- return structured, explainable, and observable outcomes,
- remain robust even when the LLM is unavailable.

---

## Scope Rules

- **Only** modify files inside `$ARGUMENTS`. Never touch files outside that path.
- Any shared logic extracted during refactoring must remain **inside the target folder**.
- Keep imports from outside the folder unchanged unless strictly necessary.
- Do not redesign the entire app architecture outside guardrail scope.
- Prefer incremental, testable improvements over speculative rewrites.

---

## Objectives

The resulting guardrail agent must follow these principles:

1. **Deterministic first** — keyword/rule-based checks run before any LLM call; high-risk patterns are blocked without depending on the LLM.
2. **Structured outcomes** — every decision produces a structured result with validity, category, reason code, confidence, matched keywords, `used_llm` flag, and an optional user-facing message.
3. **Conservative medical safety** — emergencies are escalated immediately; unsafe requests never receive procedural assistance; ambiguous personal requests are treated more carefully than generic educational ones.
4. **Explainability** — each block/allow decision is traceable through reason codes, matched keywords, and logs.
5. **Graceful degradation** — if the LLM classifier fails, the system remains safe and operational, with a distinct `LLM_UNAVAILABLE` reason code.

---

## Procedure

### 1. Scan

Use Glob `$ARGUMENTS/**/*.py` to identify all Python files related to guardrails.

Read each relevant file and note:
- rule engine entrypoints,
- LLM classifier usage,
- keyword lists,
- normalization helpers,
- result schemas,
- reason codes,
- logging patterns,
- current error handling,
- how user-facing messages are constructed.

Also identify whether the current implementation mixes policy logic, text normalization, pattern matching, LLM invocation, response/message generation, and logging. If these concerns are mixed, plan to separate them.

---

### 2. Design the Guardrail Structure

Refactor the guardrail logic into clear responsibilities.

Preferred module split inside the target folder:

- `rules_engine.py` — public entrypoint `apply_guardrails(query: str) -> GuardrailResult`
- `llm_classifier.py` — LLM fallback classifier only
- `policies.py` — risk categories, reason codes, severity constants, public message templates
- `patterns.py` — emergency keywords, unsafe keywords grouped by severity, informational patterns, first-person symptom markers
- `normalization.py` — text normalization utilities
- `utils.py` — shared helpers for pattern matching, label parsing, confidence helpers

Do not force this split if the folder is very small, but separate concerns whenever it improves readability and testability.

---

### 3. Safety Classification Model

Implement or refactor the guardrail logic around these explicit categories:

- `SAFE`
- `INFO_ONLY`
- `PERSONAL_MEDICAL`
- `EMERGENCY`
- `UNSAFE`
- `AMBIGUOUS`

Use these reason codes for machine-readable traceability:

- `EMPTY_QUERY`
- `KEYWORD_EMERGENCY`
- `KEYWORD_UNSAFE_CRITICAL`
- `KEYWORD_UNSAFE_SOFT`
- `KEYWORD_PERSONAL_MEDICAL`
- `KEYWORD_INFO_ONLY`
- `LLM_EMERGENCY`
- `LLM_UNSAFE`
- `LLM_AMBIGUOUS`
- `LLM_UNAVAILABLE`
- `SAFE`

Keep reason codes stable and descriptive. Do not break existing call sites unless required — if backward compatibility matters, preserve old fields and add new ones.

The `GuardrailResult` schema must include at minimum:

```python
@dataclass
class GuardrailResult:
    is_valid: bool
    is_emergency: bool = False
    is_unsafe: bool = False
    category: str = "SAFE"
    reason_code: str = "SAFE"
    confidence: float = 1.0
    message: Optional[str] = None
    matched_keywords: list[str] = field(default_factory=list)
    used_llm: bool = False
```

`matched_keywords` is mandatory — it is the primary explainability signal for audits and academic evaluation. `used_llm` is required to measure how often LLM classification is invoked versus deterministic rules.

---

### 4. Deterministic Rules First

Before calling the LLM, run deterministic passes in this order:

#### Pass 1 — Empty / malformed input
- Reject empty or whitespace-only queries.
- Return a user-friendly prompt to enter a question.
- Confidence: 1.0.

#### Pass 2 — Emergency detection
- Match acute medical emergency phrases.
- Prioritize symptoms and crisis signals over generic wording.
- Emergency detection is the highest priority pass.
- Return all matched keywords in `matched_keywords`.
- Confidence: 0.95.

#### Pass 3 — Unsafe detection (two severity tiers)

Split unsafe keywords into two groups with separate reason codes:

**Critical unsafe** (`KEYWORD_UNSAFE_CRITICAL`) — block immediately, high confidence:
- self-harm and suicide intent,
- violence toward others,
- illicit drug synthesis.

**Soft unsafe** (`KEYWORD_UNSAFE_SOFT`) — block but log separately, slightly lower confidence:
- exact dosage / prescription seeking,
- requests for diagnosis certainty,
- requests for personalized treatment schemas.

This split prevents false positives on legitimate medical queries that mention dosage or treatment in an educational framing.

#### Pass 4 — Informational vs personal intent

Distinguish educational queries from personal symptom reports using **symptom ownership markers** — not generic first-person words.

```python
# Too broad — causes false positives on "am citit ca" or "am intrebat despre"
FIRST_PERSON_MARKERS = ["am ", "imi ", "ma ", "eu "]

# Correct — targets actual symptom ownership
FIRST_PERSON_SYMPTOM_MARKERS = [
    "am durere", "am febra", "am tuse", "am ameteli",
    "ma doare", "simt ca", "ma simt", "imi este rau",
    "am observat ca", "sufar de", "am simptome",
]
```

- If query matches symptom ownership markers → `PERSONAL_MEDICAL`, route to LLM or handle conservatively.
- If query matches `SAFE_INFO_PATTERNS` with no personal markers → `INFO_ONLY`, allow directly.

#### Pass 5 — Ambiguity routing

If a query is not clearly safe informational content and not blocked by rules, route it to the LLM classifier if enabled.

Keep deterministic checks fast, explainable, and side-effect free.

---

### 5. Improve Keyword and Pattern Handling

Refactor raw flat keyword lists into grouped structures by semantic intent.

Emergency pattern groups:
- cardiovascular emergency
- breathing emergency
- neurological emergency
- overdose / poisoning
- severe bleeding / trauma

Unsafe pattern groups:
- self-harm / suicide (critical)
- violence toward others (critical)
- illicit drug preparation (critical)
- exact dosage / prescription seeking (soft)
- unsafe medical certainty requests (soft)

Rules:
- normalize once before matching,
- return all matched phrases for observability,
- deduplicate repeated phrases across groups,
- avoid one giant flat list — use category-grouped dicts or named lists.

You may introduce normalized substring matching, token-aware matching, or regex for high-value patterns. Avoid overengineering.

---

### 6. LLM Fallback Policy

Refactor the LLM fallback into a strict classifier, not a free-form assistant.

Requirements:
- classifier output must be restricted to an allowed label set: `EMERGENCY`, `UNSAFE`, `SAFE`, optionally `AMBIGUOUS`,
- invalid or verbose outputs must be sanitized — strip, uppercase, substring-match,
- if the LLM returns empty or `None`, **raise an exception** — do not silently return `SAFE`,
- the `rules_engine` catches the exception and returns `LLM_UNAVAILABLE` with `is_valid=True, confidence=0.6`,
- temperature must be 0 for determinism,
- log when the LLM is used and what label it returned.

```python
def classify_guardrail_with_llm(query: str) -> str:
    response = llm_classify(...)

    if not response:
        raise ValueError("LLM classifier returned empty response")

    label = response.strip().upper()
    if label in VALID_LABELS:
        logger.info("guardrail_llm_classified", extra={"label": label})
        return label

    for candidate in (LABEL_EMERGENCY, LABEL_UNSAFE, LABEL_AMBIGUOUS):
        if candidate in label:
            logger.warning("guardrail_llm_fuzzy_match", extra={"raw": label, "resolved": candidate})
            return candidate

    logger.warning("guardrail_llm_unknown_label", extra={"raw": label})
    return LABEL_SAFE
```

The classifier prompt must explicitly instruct the model:
- output one label only,
- do not explain,
- prefer `EMERGENCY` when immediate risk is plausible,
- prefer `UNSAFE` for harmful or prohibited intent,
- use `SAFE` only for benign educational content.

---

### 7. User-Facing Response Policy

Standardize public messages. Extract all message text into constants in `policies.py` — never hardcode inline.

Messages must be: short, calm, factual, non-judgmental, actionable.

Maintain separate messages for:
- **emergency** — direct to emergency services (112) and nearest emergency department,
- **unsafe / critical** — refuse and encourage immediate real-world support,
- **unsafe / soft** — refuse and recommend consultation with a licensed clinician,
- **empty query** — prompt to enter a question,
- **ambiguous** — recommend consulting a clinician, do not provide medical advice.

---

### 8. Logging and Observability

Add consistent structured logging. Log at minimum:
- final category and reason code,
- whether deterministic rules or LLM decided the result (`used_llm`),
- matched keywords where applicable,
- exception details when the LLM classifier fails.

Log levels:
- `logger.info` for safe and blocked-by-rules results,
- `logger.warning` for emergencies, unsafe detections, and LLM fallback fuzzy matches,
- `logger.exception` for LLM failures.

Do not log raw sensitive user text unless the project explicitly permits it. Prefer summary metadata. Avoid silent failures, bare `except:` clauses, and inconsistent event names.

---

### 9. Confidence Policy

Use confidence values consistently and document their meaning:

| Situation | Confidence |
|---|---|
| Deterministic emergency or unsafe match | 0.95 |
| LLM-based decision | 0.80 |
| LLM unavailable, safe pass-through | 0.60 |
| Empty query | 1.00 |
| General safe (no LLM) | 0.90 |

Document the meaning of these values in docstrings. Do not assign arbitrary numbers.

---

### 10. False Positive and False Negative Reduction

Guard against common classification mistakes:

**False positives to prevent:**
- educational queries blocked because they mention dangerous terms (e.g., `"ce inseamna infarct"` must not trigger emergency),
- queries containing `"am "` or `"ma "` flagged as personal medical when they are not symptom reports,
- `"reteta"` alone triggering an unsafe block in an educational framing.

**False negatives to prevent:**
- exact dosage / exact treatment requests slipping through as safe,
- self-harm intent expressed indirectly.

Use contextual heuristics:
- first-person **symptom ownership** markers (not generic first-person),
- urgency markers,
- educational framing words: `"ce este"`, `"definitie"`, `"cauze"`, `"ce inseamna"`,
- imperative harmful phrasing: `"cum sa fac"`, `"cum prepar"`, `"cum pot obtine"`.

Document trade-offs in comments where non-obvious.

---

### 11. PEP 8, Typing, and Clean Code

Apply these standards to all touched files:
- type hints on all functions and methods,
- descriptive constant names, no magic strings,
- small, single-purpose functions,
- concise docstrings on all public functions and modules,
- no dead code or unused imports,
- no bare `except:` — use `except Exception as exc:` and log appropriately,
- normalize once — avoid repeated normalization calls.

---

### 12. Add or Improve Tests

If a test folder exists inside scope, extend it. If not, create lightweight tests inside `$ARGUMENTS` only if they fit naturally.

#### Emergency
- acute chest pain
- severe breathing difficulty
- stroke-like symptoms
- major bleeding
- overdose / poisoning

#### Unsafe — critical
- self-harm intent
- suicide method seeking
- violence toward others
- drug synthesis

#### Unsafe — soft
- exact prescription/dose request
- personalized treatment schema request
- `"antibiotic fara reteta"` (specific, not just `"reteta"`)

#### Safe informational (must NOT be blocked)
- `"ce este diabetul"`
- `"care sunt simptomele gripei"`
- `"ce inseamna hipertensiune"`
- `"ce inseamna infarct"` ← must not trigger emergency

#### Ambiguous / personal
- `"am febra si tusesc"`
- `"ma doare capul de 3 zile"`
- `"ce antibiotic sa iau exact"`
- `"am citit despre diabet"` ← must NOT be flagged as personal medical

#### LLM failure
- simulate classifier exception
- verify graceful fallback to `LLM_UNAVAILABLE` with `is_valid=True`

Each test must assert: `category`, `is_valid`, `is_emergency`, `is_unsafe`, `reason_code`, `matched_keywords` (empty or non-empty), and correct block/allow behavior.

---

### 13. Verify

After all edits, run syntax validation on every modified file:

```bash
python -c "import ast; ast.parse(open('<file>', encoding='utf-8').read())"
```
