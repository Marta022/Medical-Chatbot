from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from qdrant_client.http.exceptions import ResponseHandlingException

import importlib
from models import MedicalItem
from models.contracts import PdfStructuredChunk


class TestQdrantIngest(unittest.TestCase):
    def test_ingest_filters_low_information_pdf_chunks_with_list_exception(self) -> None:
        ingest_module = importlib.import_module("knowledge.qdrant.ingest")
        low_fragment = PdfStructuredChunk(
            source_file="doc.pdf",
            page=315,
            chapter="CAPITOLUL 9",
            section="GPLM",
            chunk_id="frag-low",
            text="de colesterol,",
            is_list=False,
        )
        short_list_chunk = PdfStructuredChunk(
            source_file="doc.pdf",
            page=315,
            chapter="CAPITOLUL 9",
            section="GPLM",
            chunk_id="frag-list",
            text="1. Durere toracica",
            is_list=True,
        )

        with patch("knowledge.qdrant.ingest.load_medical_items", return_value=[]):
            with patch(
                "knowledge.qdrant.ingest.load_pdf_chunks",
                return_value=[low_fragment, short_list_chunk],
            ):
                with patch("knowledge.qdrant.ingest.load_disease_terms", return_value=set()):
                    with patch("knowledge.qdrant.ingest.embed_texts", return_value=[[0.3, 0.4]]):
                        with patch("knowledge.qdrant.ingest.vector_size", return_value=2):
                            with patch("knowledge.qdrant.ingest.ensure_collection"):
                                with patch(
                                    "knowledge.qdrant.ingest.client", MagicMock()
                                ) as client_mock:
                                    count = ingest_module.ingest(
                                        "a.json",
                                        "b.csv",
                                        pdf_paths=["doc.pdf"],
                                        include_structured_sources=False,
                                        chunk_min_chars=40,
                                        chunk_min_words=5,
                                        list_chunk_min_words=2,
                                    )

        self.assertEqual(count, 1)
        inserted = client_mock.upsert.call_args.kwargs["points"]
        self.assertEqual(len(inserted), 1)
        self.assertEqual(inserted[0].payload["chunk_id"], "frag-list")

    def test_ingest_builds_points(self) -> None:
        ingest_module = importlib.import_module("knowledge.qdrant.ingest")
        item = MedicalItem(title="A", description="B", source="json", category="C")
        pdf_chunk = PdfStructuredChunk(
            source_file="doc.pdf",
            page=1,
            chapter="CAPITOLUL 1",
            section="1.1 Sectiune",
            chunk_id="chunk-001",
            text="Text PDF",
            is_list=False,
        )

        with patch(
            "knowledge.qdrant.ingest.load_medical_items",
            return_value=[item],
        ):
            with patch(
                "knowledge.qdrant.ingest.chunk_text",
                return_value=["chunk1"],
            ):
                with patch(
                    "knowledge.qdrant.ingest.embed_texts",
                    side_effect=[[[0.1, 0.2]], [[0.3, 0.4]]],
                ):
                    with patch(
                        "knowledge.qdrant.ingest.load_pdf_chunks",
                        return_value=[pdf_chunk],
                    ):
                        with patch(
                            "knowledge.qdrant.ingest.vector_size",
                            return_value=2,
                        ):
                            with patch("knowledge.qdrant.ingest.ensure_collection") as ensure_mock:
                                with patch(
                                    "knowledge.qdrant.ingest.client", MagicMock()
                                ) as client_mock:
                                    count = ingest_module.ingest(
                                        "a.json",
                                        "b.csv",
                                        chunking_strategy="semantic",
                                        pdf_paths=["doc.pdf"],
                                    )

        ensure_mock.assert_called_once_with(2)
        client_mock.upsert.assert_called()
        points = client_mock.upsert.call_args_list[0].kwargs["points"]
        self.assertEqual(len(points), 2)
        self.assertEqual(points[1].payload["source"], "pdf")
        self.assertEqual(points[1].payload["source_file"], "doc.pdf")
        self.assertEqual(points[1].payload["chunk_id"], "chunk-001")
        self.assertEqual(count, 2)

    def test_ingest_handles_empty_pdf_chunks(self) -> None:
        ingest_module = importlib.import_module("knowledge.qdrant.ingest")
        item = MedicalItem(title="A", description="B", source="json", category="C")

        with patch("knowledge.qdrant.ingest.load_medical_items", return_value=[item]):
            with patch("knowledge.qdrant.ingest.chunk_text", return_value=["chunk1"]):
                with patch("knowledge.qdrant.ingest.embed_texts", return_value=[[0.1, 0.2]]):
                    with patch(
                        "knowledge.qdrant.ingest.load_pdf_chunks",
                        return_value=[],
                    ):
                        with patch("knowledge.qdrant.ingest.vector_size", return_value=2):
                            with patch("knowledge.qdrant.ingest.ensure_collection"):
                                with patch(
                                    "knowledge.qdrant.ingest.client", MagicMock()
                                ) as client_mock:
                                    count = ingest_module.ingest(
                                        "a.json",
                                        "b.csv",
                                        pdf_paths=["doc.pdf"],
                                    )

        client_mock.upsert.assert_called_once()
        self.assertEqual(count, 1)

    def test_ingest_pdf_only_skips_tabular_sources(self) -> None:
        ingest_module = importlib.import_module("knowledge.qdrant.ingest")
        pdf_chunk = PdfStructuredChunk(
            source_file="doc.pdf",
            page=3,
            chapter="CAPITOLUL 2",
            section="2.1",
            chunk_id="chunk-100",
            text="Informatii clinice",
            is_list=True,
        )

        with patch("knowledge.qdrant.ingest.load_medical_items") as load_tabular:
            with patch("knowledge.qdrant.ingest.load_pdf_chunks", return_value=[pdf_chunk]):
                with patch("knowledge.qdrant.ingest.embed_texts", return_value=[[0.4, 0.5]]):
                    with patch("knowledge.qdrant.ingest.vector_size", return_value=2):
                        with patch("knowledge.qdrant.ingest.ensure_collection"):
                            with patch(
                                "knowledge.qdrant.ingest.client", MagicMock()
                            ) as client_mock:
                                count = ingest_module.ingest(
                                    "a.json",
                                    "b.csv",
                                    pdf_paths=["doc.pdf"],
                                    include_structured_sources=False,
                                )

        load_tabular.assert_not_called()
        client_mock.upsert.assert_called_once()
        points = client_mock.upsert.call_args_list[0].kwargs["points"]
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0].payload["source"], "pdf")
        self.assertEqual(count, 1)

    def test_ingest_point_ids_are_stable_across_repeated_runs(self) -> None:
        ingest_module = importlib.import_module("knowledge.qdrant.ingest")
        item = MedicalItem(title="A", description="B", source="json", category="C")
        pdf_chunk = PdfStructuredChunk(
            source_file="doc.pdf",
            page=1,
            chapter="CAPITOLUL 1",
            section="1.1",
            chunk_id="chunk-001",
            text="Text PDF",
            is_list=False,
        )

        with patch("knowledge.qdrant.ingest.load_medical_items", return_value=[item]):
            with patch("knowledge.qdrant.ingest.chunk_text", return_value=["chunk1"]):
                with patch("knowledge.qdrant.ingest.load_pdf_chunks", return_value=[pdf_chunk]):
                    with patch(
                        "knowledge.qdrant.ingest.embed_texts",
                        side_effect=[[[0.1, 0.2]], [[0.3, 0.4]], [[0.1, 0.2]], [[0.3, 0.4]]],
                    ):
                        with patch("knowledge.qdrant.ingest.vector_size", return_value=2):
                            with patch("knowledge.qdrant.ingest.ensure_collection"):
                                with patch(
                                    "knowledge.qdrant.ingest.client", MagicMock()
                                ) as client_mock:
                                    ingest_module.ingest("a.json", "b.csv", pdf_paths=["doc.pdf"])
                                    ingest_module.ingest("a.json", "b.csv", pdf_paths=["doc.pdf"])

        first_points = client_mock.upsert.call_args_list[0].kwargs["points"]
        second_points = client_mock.upsert.call_args_list[1].kwargs["points"]
        first_ids = [point.id for point in first_points]
        second_ids = [point.id for point in second_points]
        self.assertEqual(first_ids, second_ids)

    def test_ingest_pdf_payload_contains_entity_annotations(self) -> None:
        ingest_module = importlib.import_module("knowledge.qdrant.ingest")
        pdf_chunk = PdfStructuredChunk(
            source_file="doc.pdf",
            page=12,
            chapter="CAPITOLUL 4",
            section="4.1",
            chunk_id="chunk-ner",
            text="Pacient cu MI si durere toracica.",
            is_list=False,
        )

        with patch("knowledge.qdrant.ingest.load_medical_items", return_value=[]):
            with patch("knowledge.qdrant.ingest.load_pdf_chunks", return_value=[pdf_chunk]):
                with patch(
                    "knowledge.qdrant.ingest.load_disease_terms", return_value={"infarct miocardic"}
                ):
                    with patch("knowledge.qdrant.ingest.embed_texts", return_value=[[0.3, 0.4]]):
                        with patch("knowledge.qdrant.ingest.vector_size", return_value=2):
                            with patch("knowledge.qdrant.ingest.ensure_collection"):
                                with patch(
                                    "knowledge.qdrant.ingest.client", MagicMock()
                                ) as client_mock:
                                    count = ingest_module.ingest(
                                        "a.json",
                                        "b.csv",
                                        pdf_paths=["doc.pdf"],
                                        include_structured_sources=False,
                                    )

        self.assertEqual(count, 1)
        point = client_mock.upsert.call_args.kwargs["points"][0]
        self.assertEqual(point.payload["chunk_id"], "chunk-ner")
        self.assertNotIn("page", point.payload)
        self.assertEqual(point.payload["source_file"], "doc.pdf")
        self.assertTrue(point.payload["entities"])
        self.assertTrue(
            any(
                ent["canonical_form"] == "myocardial infarction"
                for ent in point.payload["entities"]
            )
        )

    def test_ingest_upserts_in_batches_when_configured(self) -> None:
        ingest_module = importlib.import_module("knowledge.qdrant.ingest")
        items = [
            MedicalItem(title=f"A{i}", description="B", source="json", category="C")
            for i in range(3)
        ]

        with patch("knowledge.qdrant.ingest.load_medical_items", return_value=items):
            with patch("knowledge.qdrant.ingest.chunk_text", return_value=["chunk1"]):
                with patch("knowledge.qdrant.ingest.embed_texts", return_value=[[0.1, 0.2]] * 3):
                    with patch("knowledge.qdrant.ingest.load_pdf_chunks", return_value=[]):
                        with patch("knowledge.qdrant.ingest.vector_size", return_value=2):
                            with patch("knowledge.qdrant.ingest.ensure_collection"):
                                with patch(
                                    "knowledge.qdrant.ingest.client", MagicMock()
                                ) as client_mock:
                                    count = ingest_module.ingest(
                                        "a.json",
                                        "b.csv",
                                        qdrant_upsert_batch_size=2,
                                    )

        self.assertEqual(count, 3)
        self.assertEqual(client_mock.upsert.call_count, 2)
        first_batch = client_mock.upsert.call_args_list[0].kwargs["points"]
        second_batch = client_mock.upsert.call_args_list[1].kwargs["points"]
        self.assertEqual(len(first_batch), 2)
        self.assertEqual(len(second_batch), 1)

    def test_ingest_retries_transient_qdrant_failure(self) -> None:
        ingest_module = importlib.import_module("knowledge.qdrant.ingest")
        item = MedicalItem(title="A", description="B", source="json", category="C")
        transient_error = ResponseHandlingException(Exception("[WinError 10053] transient"))

        with patch("knowledge.qdrant.ingest.load_medical_items", return_value=[item]):
            with patch("knowledge.qdrant.ingest.chunk_text", return_value=["chunk1"]):
                with patch("knowledge.qdrant.ingest.embed_texts", return_value=[[0.1, 0.2]]):
                    with patch("knowledge.qdrant.ingest.load_pdf_chunks", return_value=[]):
                        with patch("knowledge.qdrant.ingest.vector_size", return_value=2):
                            with patch("knowledge.qdrant.ingest.ensure_collection"):
                                with patch("knowledge.qdrant.ingest.time.sleep") as sleep_mock:
                                    with patch(
                                        "knowledge.qdrant.ingest.client", MagicMock()
                                    ) as client_mock:
                                        client_mock.upsert.side_effect = [transient_error, None]
                                        count = ingest_module.ingest(
                                            "a.json",
                                            "b.csv",
                                            qdrant_upsert_batch_size=8,
                                            qdrant_upsert_max_retries=2,
                                            qdrant_upsert_retry_delay_seconds=0.01,
                                        )

        self.assertEqual(count, 1)
        self.assertEqual(client_mock.upsert.call_count, 2)
        sleep_mock.assert_called_once_with(0.01)


if __name__ == "__main__":
    unittest.main()
