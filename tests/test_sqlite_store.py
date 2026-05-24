from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from models import (
    EvaluatorResult,
    GuardrailResult,
    OrchestratorResponse,
    QueryRequest,
    RetrievalHit,
    RetrievalResult,
)
from storage import InteractionStore


def _evaluated_response() -> OrchestratorResponse:
    return OrchestratorResponse(
        response="Raspuns final.",
        provider="openai",
        model="unit-model",
        retries=1,
        guardrail=GuardrailResult(is_valid=True, category="SAFE", reason_code="SAFE"),
        evaluator=EvaluatorResult(passed=True, score=0.92),
        retrieval=RetrievalResult(
            provenance="vector",
            hits=[
                RetrievalHit(
                    title="Doc 1",
                    text="Textul nu trebuie duplicat in SQLite.",
                    score=0.91,
                    source="markdown",
                    source_file="document.md",
                    section="Cardiologie",
                    chunk_id="chunk-a",
                ),
                RetrievalHit(
                    title="Doc 2",
                    text="Alt continut nereplicat.",
                    score=0.83,
                    source="dataset",
                    chunk_id=None,
                ),
            ],
        ),
        context_lines=[],
    )


class TestInteractionStore(unittest.TestCase):
    def test_save_interaction_creates_schema_and_persists_chunk_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "nested" / "interactions.db"
            store = InteractionStore(
                db_path,
                id_factory=lambda: "interaction-1",
                timestamp_factory=lambda: "2026-05-24T08:00:00+00:00",
            )

            interaction_id = store.save_interaction(
                request=QueryRequest(query="Care sunt simptomele?"),
                response=_evaluated_response(),
                endpoint="/chat",
                session_id="session-1",
            )

            self.assertEqual(interaction_id, "interaction-1")
            self.assertTrue(db_path.exists())
            with closing(sqlite3.connect(db_path)) as connection:
                interaction = connection.execute(
                    """
                    SELECT id, session_id, user_query, assistant_response, provider, model,
                           retries, guardrail_valid, evaluator_passed, evaluator_score,
                           retrieval_provenance, retrieval_hit_count
                    FROM interactions
                    """
                ).fetchone()
                chunk_rows = connection.execute(
                    """
                    SELECT rank, chunk_id, score, source, source_file, page, section
                    FROM retrieved_chunk_refs
                    ORDER BY rank
                    """
                ).fetchall()
                chunk_columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(retrieved_chunk_refs)")
                }

            self.assertEqual(
                interaction,
                (
                    "interaction-1",
                    "session-1",
                    "Care sunt simptomele?",
                    "Raspuns final.",
                    "openai",
                    "unit-model",
                    1,
                    1,
                    1,
                    0.92,
                    "vector",
                    2,
                ),
            )
            self.assertEqual(
                chunk_rows[0],
                (1, "chunk-a", 0.91, "markdown", "document.md", None, "Cardiologie"),
            )
            self.assertEqual(chunk_rows[1], (2, None, 0.83, "dataset", None, None, None))
            self.assertNotIn("text", chunk_columns)

    def test_save_guardrail_blocked_response_has_no_chunk_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "interactions.db"
            store = InteractionStore(db_path, id_factory=lambda: "blocked-1")
            response = OrchestratorResponse(
                response="Solicita asistenta de urgenta.",
                provider=None,
                model=None,
                retries=0,
                guardrail=GuardrailResult(
                    is_valid=False,
                    category="EMERGENCY",
                    reason_code="KEYWORD_EMERGENCY",
                ),
                evaluator=None,
                retrieval=None,
                context_lines=[],
            )

            store.save_interaction(
                request=QueryRequest(query="Am o urgenta"),
                response=response,
                endpoint="/chat",
            )

            with closing(sqlite3.connect(db_path)) as connection:
                interaction = connection.execute(
                    """
                    SELECT guardrail_valid, guardrail_category, evaluator_passed,
                           retrieval_hit_count
                    FROM interactions
                    """
                ).fetchone()
                child_count = connection.execute(
                    "SELECT COUNT(*) FROM retrieved_chunk_refs"
                ).fetchone()[0]

            self.assertEqual(interaction, (0, "EMERGENCY", None, 0))
            self.assertEqual(child_count, 0)

    def test_initialize_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "interactions.db"
            store = InteractionStore(db_path)

            store.initialize()
            store.initialize()

            with closing(sqlite3.connect(db_path)) as connection:
                table_names = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
            self.assertIn("interactions", table_names)
            self.assertIn("retrieved_chunk_refs", table_names)

    def test_chunk_insert_failure_rolls_back_interaction(self) -> None:
        class FailingInteractionStore(InteractionStore):
            @staticmethod
            def _insert_chunk_references(
                connection: sqlite3.Connection,
                *,
                interaction_id: str,
                response: OrchestratorResponse,
            ) -> None:
                raise RuntimeError("chunk insert failed")

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "interactions.db"
            store = FailingInteractionStore(db_path)
            store.initialize()

            with self.assertRaisesRegex(RuntimeError, "chunk insert failed"):
                store.save_interaction(
                    request=QueryRequest(query="Test"),
                    response=_evaluated_response(),
                    endpoint="/chat",
                )

            with closing(sqlite3.connect(db_path)) as connection:
                interaction_count = connection.execute(
                    "SELECT COUNT(*) FROM interactions"
                ).fetchone()[0]
                chunk_count = connection.execute(
                    "SELECT COUNT(*) FROM retrieved_chunk_refs"
                ).fetchone()[0]
            self.assertEqual(interaction_count, 0)
            self.assertEqual(chunk_count, 0)

    def test_empty_endpoint_is_rejected_before_creating_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "interactions.db"
            store = InteractionStore(db_path)

            with self.assertRaisesRegex(ValueError, "endpoint must be a non-empty string"):
                store.save_interaction(
                    request=QueryRequest(query="Test"),
                    response=_evaluated_response(),
                    endpoint=" ",
                )

            self.assertFalse(db_path.exists())


if __name__ == "__main__":
    unittest.main()
