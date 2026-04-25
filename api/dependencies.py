from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agent.benchmarking.benchmark import run_evaluation_smoke
from agent.orchestrator.orchestrator import Orchestrator
from knowledge.qdrant.ingest import ingest
from models.serde import serialize_to_json_compatible


@dataclass(frozen=True)
class ApiDependencies:
    orchestrator_factory: Callable[[], Orchestrator]
    ingest: Callable[[str, str, str], int]
    run_eval: Callable[[], Any]
    to_json_compatible: Callable[[Any], Any]


def default_dependencies() -> ApiDependencies:
    return ApiDependencies(
        orchestrator_factory=Orchestrator,
        ingest=ingest,
        run_eval=run_evaluation_smoke,
        to_json_compatible=serialize_to_json_compatible,
    )
