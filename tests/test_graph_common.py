from __future__ import annotations

import unittest

from knowledge.graph.common import result_to_rows


class PositionalResult:
    def get_column_names(self) -> list[str]:
        return ["name", "count"]

    def get_all(self) -> list[list[object]]:
        return [["Entity", 23], ["SourceChunk", 231]]


class IteratorResult:
    def __init__(self) -> None:
        self._rows = [["DISEASE_HAS_SYMPTOM", 4]]

    def get_column_names(self) -> list[str]:
        return ["relation", "count"]

    def has_next(self) -> bool:
        return bool(self._rows)

    def get_next(self) -> list[object]:
        return self._rows.pop(0)


class TestGraphCommon(unittest.TestCase):
    def test_result_to_rows_maps_positional_kuzu_rows(self) -> None:
        self.assertEqual(
            result_to_rows(PositionalResult()),
            [{"name": "Entity", "count": 23}, {"name": "SourceChunk", "count": 231}],
        )

    def test_result_to_rows_maps_iterator_rows_with_columns(self) -> None:
        self.assertEqual(
            result_to_rows(IteratorResult()),
            [{"relation": "DISEASE_HAS_SYMPTOM", "count": 4}],
        )


if __name__ == "__main__":
    unittest.main()
