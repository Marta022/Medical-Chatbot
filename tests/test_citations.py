from __future__ import annotations

import unittest

from agent.orchestrator.citations import (
    append_citation_block,
    append_retrieved_chunks_block,
    build_citation_rows,
)
from models import RetrievalHit, RetrievalResult


class TestCitations(unittest.TestCase):
    def test_build_citation_rows_includes_required_schema(self) -> None:
        retrieval = RetrievalResult(
            hits=[
                RetrievalHit(
                    title="A",
                    text="alpha",
                    score=0.9,
                    source="pdf",
                    source_file="doc.pdf",
                    page=12,
                    section="4.1",
                    chunk_id="chunk-12",
                )
            ]
        )
        rows = build_citation_rows(retrieval)
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0].keys()), {"source_file", "page", "section", "chunk_id"})

    def test_append_citation_block_formats_output(self) -> None:
        response = append_citation_block(
            "Raspuns clinic",
            [{"source_file": "doc.pdf", "page": 1, "section": "1.1", "chunk_id": "chunk-1"}],
        )
        self.assertIn("Citations:", response)
        self.assertIn("source_file=doc.pdf", response)
        self.assertIn("page=1", response)
        self.assertIn("section=1.1", response)
        self.assertIn("chunk_id=chunk-1", response)

    def test_append_retrieved_chunks_block_formats_output(self) -> None:
        retrieval = RetrievalResult(
            hits=[
                RetrievalHit(
                    title="A",
                    text="alpha beta gamma",
                    score=0.9,
                    source="pdf",
                    source_file="doc.pdf",
                    page=12,
                    section="4.1",
                    chunk_id="chunk-12",
                )
            ]
        )
        response = append_retrieved_chunks_block("Raspuns clinic", retrieval)
        self.assertIn("Most similar chunks:", response)
        self.assertIn("score=0.9000", response)
        self.assertIn("source_file=doc.pdf", response)
        self.assertIn("page=12", response)
        self.assertIn("section=4.1", response)
        self.assertIn("chunk_id=chunk-12", response)
        self.assertIn("text=alpha beta gamma", response)


if __name__ == "__main__":
    unittest.main()
