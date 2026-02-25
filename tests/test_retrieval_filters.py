from __future__ import annotations

import unittest

from rag.retrieval.retriever import _build_filter


class TestRetrievalFilters(unittest.TestCase):
    def test_build_filter_none(self) -> None:
        self.assertIsNone(_build_filter(None))
        self.assertIsNone(_build_filter({}))

    def test_build_filter_with_fields(self) -> None:
        payload_filter = _build_filter({"source": "json", "category": "infectious"})
        self.assertIsNotNone(payload_filter)
        self.assertEqual(len(payload_filter.must), 2)


if __name__ == "__main__":
    unittest.main()
