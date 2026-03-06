from __future__ import annotations

import unittest
from unittest.mock import patch

from models import RetrievalHit, RetrievalResult
from models.contracts import PdfStructuredChunk
from rag.retrieval.quality_report import build_quality_report


class TestQualityReport(unittest.TestCase):
    def test_build_quality_report_collects_chunk_and_probe_metrics(self) -> None:
        chunks = [
            PdfStructuredChunk(
                source_file="doc.pdf",
                page=1,
                chapter="CAPITOLUL 1",
                section="1.1",
                chunk_id="c1",
                text="fragment extins pentru diagnostic retrieval",
                is_list=False,
            ),
            PdfStructuredChunk(
                source_file="doc.pdf",
                page=1,
                chapter="CAPITOLUL 1",
                section="1.2",
                chunk_id="c2",
                text="scurt",
                is_list=False,
            ),
        ]
        retrieval = RetrievalResult(
            hits=[
                RetrievalHit(
                    title="Doc",
                    text="context util",
                    score=0.81,
                    source="pdf",
                    source_file="doc.pdf",
                    page=1,
                    section="1.1",
                    chunk_id="c1",
                )
            ]
        )

        with patch("rag.retrieval.quality_report.load_pdf_chunks", return_value=chunks):
            with patch("rag.retrieval.quality_report.retrieve_top_similar", return_value=retrieval):
                report = build_quality_report(
                    pdf_paths=["doc.pdf"],
                    chunking_strategy="semantic",
                    semantic_chunk_max_chars=700,
                    semantic_use_llamaindex=False,
                    probe_queries=["query demo"],
                    keyword_queries=["diagnostic"],
                    keyword_limit=3,
                    top_k=2,
                )

        self.assertIn("doc.pdf", report["pdf_chunk_metrics"])
        self.assertEqual(report["pdf_chunk_metrics"]["doc.pdf"]["count"], 2)
        self.assertIn("avg_words", report["pdf_chunk_metrics"]["doc.pdf"])
        self.assertEqual(len(report["retrieval_probes"]), 1)
        self.assertEqual(report["retrieval_probes"][0]["query"], "query demo")
        self.assertEqual(report["retrieval_probes"][0]["hit_count"], 1)
        self.assertEqual(report["retrieval_probes"][0]["provenance"], "vector")
        self.assertIn("doc.pdf", report["chunk_keyword_probes"])
        self.assertIn("diagnostic", report["chunk_keyword_probes"]["doc.pdf"])
        self.assertEqual(len(report["chunk_keyword_probes"]["doc.pdf"]["diagnostic"]), 1)


if __name__ == "__main__":
    unittest.main()
