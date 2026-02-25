from __future__ import annotations

from agent.evaluation.evaluator import evaluate_response
from models import EvaluatorResult


def run_evaluation_smoke() -> EvaluatorResult:
    return evaluate_response(
        query="Care sunt simptomele gripei?",
        response="Gripa include febra, frisoane, tuse si dureri musculare.",
        context_lines=["Simptome frecvente: febra, tuse, dureri musculare."],
    )
