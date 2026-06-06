from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from agent.benchmarking.benchmark import run_evaluation_smoke
from agent.orchestrator.orchestrator import Orchestrator
from config.settings import SETTINGS
from knowledge.qdrant.ingest import ingest
from models import OrchestratorResponse, QueryRequest
from models.serde import serialize_to_json_compatible
from storage import InteractionStore


class InteractionStoreProtocol(Protocol):
    def save_interaction(
        self,
        *,
        request: QueryRequest,
        response: OrchestratorResponse,
        endpoint: str,
        session_id: str | None = None,
    ) -> str: ...


@dataclass(frozen=True)
class ApiDependencies:
    orchestrator_factory: Callable[[], Orchestrator]
    ingest: Callable[[str, str, str], int]
    run_eval: Callable[[], Any]
    to_json_compatible: Callable[[Any], Any]
    interaction_store: InteractionStoreProtocol | None = None


def default_dependencies() -> ApiDependencies:
    interaction_store = (
        InteractionStore(SETTINGS.interaction_db_path) if SETTINGS.interaction_db_enabled else None
    )
    return ApiDependencies(
        orchestrator_factory=Orchestrator,
        ingest=ingest,
        run_eval=run_evaluation_smoke,
        to_json_compatible=serialize_to_json_compatible,
        interaction_store=interaction_store,
    )
