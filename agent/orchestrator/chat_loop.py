"""Interactive CLI chat runtime.

Flow per user message:
1) Read query from terminal.
2) Build `QueryRequest` with policy controls (`top_k`, optional filters).
3) Delegate to `Orchestrator` (guardrail, retrieval, response generation, evaluation).
4) Print guardrail feedback, retrieval evidence, and final assistant response.

This module is intentionally minimal and presentation-focused; business logic lives
in orchestrator/retrieval/evaluation components.
"""

from __future__ import annotations

import logging

from agent.orchestrator.orchestrator import Orchestrator
from config.logging_config import new_correlation_id
from config.settings import SETTINGS
from models import OrchestratorResponse, QueryRequest

logger = logging.getLogger(__name__)
EXIT_COMMANDS = {"exit", "quit", ":q"}
RETRIEVED_CHUNKS_LABEL = "Chunk-uri similare gasite:"
ROMANIAN_CONTEXT_LABEL = "Context folosit (in romana):"
RESPONSE_SEPARATOR = "=" * 80


def run_chat_loop(
    top_k: int | None = None,
    filters: dict[str, str] | None = None,
) -> None:
    """Run the interactive chat loop using the orchestrator pipeline."""

    query_top_k = top_k if top_k is not None else SETTINGS.default_top_k
    orchestrator = Orchestrator()
    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() in EXIT_COMMANDS:
            logger.info("Bye.")
            break

        new_correlation_id()
        request = QueryRequest(query=query, top_k=query_top_k, filters=filters)
        result: OrchestratorResponse = orchestrator.run(request)

        if not result.guardrail.is_valid:
            logger.info(result.guardrail.message)
            continue

        if result.retrieval and result.retrieval.hits:
            logger.info(RETRIEVED_CHUNKS_LABEL)
            for index, hit in enumerate(result.retrieval.hits, start=1):
                source_parts: list[str] = [f"source={hit.source}"]
                if hit.source_file:
                    source_parts.append(f"file={hit.source_file}")
                if hit.page is not None:
                    source_parts.append(f"page={hit.page}")
                if hit.chunk_id:
                    source_parts.append(f"chunk={hit.chunk_id}")
                source_meta = ", ".join(source_parts)
                logger.info(
                    "%s) score=%.4f | %s | %s",
                    index,
                    hit.score,
                    source_meta,
                    hit.text,
                )

        logger.info(ROMANIAN_CONTEXT_LABEL)
        for index, item in enumerate(result.context_lines, start=1):
            logger.info("%s. %s", index, item)
        logger.info(RESPONSE_SEPARATOR)
        logger.info("Assistant: %s", result.response)
