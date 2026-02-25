from __future__ import annotations

import unittest

from knowledge.qdrant.ingest import build_point_id


class TestIngestHelpers(unittest.TestCase):
    def test_build_point_id_is_deterministic(self) -> None:
        first = build_point_id("json", "title", "cat", "chunk", 1)
        second = build_point_id("json", "title", "cat", "chunk", 1)
        self.assertEqual(first, second)

    def test_build_point_id_changes_with_chunk(self) -> None:
        first = build_point_id("json", "title", "cat", "chunk", 1)
        second = build_point_id("json", "title", "cat", "chunk2", 1)
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
