from __future__ import annotations

import logging

from agent.orchestrator.orchestrator import Orchestrator
from config.logging_config import new_correlation_id
from config.settings import SETTINGS
from models import OrchestratorResponse, QueryRequest

logger = logging.getLogger(__name__)


def run_chat_loop(top_k: int | None = None) -> None:
    query_top_k = top_k if top_k is not None else SETTINGS.default_top_k
    orchestrator = Orchestrator()
    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() in {"exit", "quit", ":q"}:
            logger.info("Bye.")
            break

        new_correlation_id()
        request = QueryRequest(query=query, top_k=query_top_k)
        result: OrchestratorResponse = orchestrator.run(request)

        if not result.guardrail.is_valid:
            logger.info(result.guardrail.message)
            continue

        logger.info("Context folosit (in romana):")
        for index, item in enumerate(result.context_lines, start=1):
            logger.info("%s. %s", index, item)
        logger.info("=" * 80)
        logger.info("Assistant: %s", result.response)
