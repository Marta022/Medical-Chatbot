# Model Ownership and Usage Guidelines (T1.4.5)

Date: 2026-02-13  
Task ID: `T1.4.5`

## Purpose

Define how typed models are used and owned so new development does not regress to ad-hoc dictionary payloads.

## Model Ownership

Primary model definitions live in:
- `models/contracts.py`

Serialization helpers live in:
- `models/serde.py`

## Required Usage Rules

1. New orchestrator/guardrail/retrieval/evaluation code must accept/return typed models for core payloads.
2. Legacy dictionary payloads are only allowed inside compatibility shims.
3. Any new API payload object must be added as a model before endpoint logic is implemented.
4. Model validation must happen at module boundaries (CLI/API input, provider output mapping).

## Current Core Models

- `QueryRequest`
- `GuardrailResult`
- `RetrievalHit`
- `RetrievalResult`
- `LLMRequest`
- `LLMResponse`
- `EvaluatorResult`
- `MedicalItem`

## Serialization Strategy

- Use `to_dict` / `from_dict` methods on model classes where available.
- Use helpers from `models/serde.py` for JSON-compatible payload conversion and typed reconstruction.

## Change Process

When adding a field to an existing model:
1. Update the model class.
2. Update serialization helpers.
3. Update affected tests in `tests/test_models.py`.
4. Update this guideline if ownership/rules changed.

