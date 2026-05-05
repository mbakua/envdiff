"""Tests for envdiff.sorter."""

import pytest

from envdiff.differ import DiffResult
from envdiff.sorter import SortKey, sort_diff


@pytest.fixture()
def mixed_diff() -> DiffResult:
    return DiffResult(
        {
            "ZEBRA": {"left": "z", "right": "z"},
            "ALPHA": {"left": "a", "right": "b"},
            "MIDDLE": {"left": None, "right": "present"},
            "BETA": {"left": "only", "right": None},
        }
    )


class TestSortByName:
    def test_ascending(self, mixed_diff):
        result = sort_diff(mixed_diff, by=SortKey.NAME)
        keys = list(result.keys())
        assert keys == sorted(keys, key=str.lower)

    def test_descending(self, mixed_diff):
        result = sort_diff(mixed_diff, by=SortKey.NAME, reverse=True)
        keys = list(result.keys())
        assert keys == sorted(keys, key=str.lower, reverse=True)

    def test_returns_diff_result_type(self, mixed_diff):
        result = sort_diff(mixed_diff, by=SortKey.NAME)
        assert isinstance(result, DiffResult)


class TestSortByStatus:
    def test_only_in_left_before_match(self, mixed_diff):
        result = sort_diff(mixed_diff, by=SortKey.STATUS)
        keys = list(result.keys())
        assert keys.index("BETA") < keys.index("ZEBRA")

    def test_only_in_right_before_mismatch(self, mixed_diff):
        result = sort_diff(mixed_diff, by=SortKey.STATUS)
        keys = list(result.keys())
        assert keys.index("MIDDLE") < keys.index("ALPHA")

    def test_mismatch_before_match(self, mixed_diff):
        result = sort_diff(mixed_diff, by=SortKey.STATUS)
        keys = list(result.keys())
        assert keys.index("ALPHA") < keys.index("ZEBRA")


class TestSortByLeftRight:
    def test_sort_by_left_value(self):
        diff = DiffResult(
            {
                "Z_VAR": {"left": "zebra", "right": "x"},
                "A_VAR": {"left": "apple", "right": "x"},
                "M_VAR": {"left": None, "right": "x"},
            }
        )
        result = sort_diff(diff, by=SortKey.LEFT)
        keys = list(result.keys())
        # None sorts as empty string -> first
        assert keys[0] == "M_VAR"
        assert keys[1] == "A_VAR"
        assert keys[2] == "Z_VAR"

    def test_sort_by_right_value(self):
        diff = DiffResult(
            {
                "Z_VAR": {"left": "x", "right": "zebra"},
                "A_VAR": {"left": "x", "right": "apple"},
            }
        )
        result = sort_diff(diff, by=SortKey.RIGHT)
        keys = list(result.keys())
        assert keys == ["A_VAR", "Z_VAR"]


class TestEdgeCases:
    def test_empty_diff(self):
        result = sort_diff(DiffResult({}))
        assert result == {}

    def test_single_entry(self):
        diff = DiffResult({"ONLY": {"left": "v", "right": "v"}})
        result = sort_diff(diff, by=SortKey.STATUS)
        assert list(result.keys()) == ["ONLY"]

    def test_original_not_mutated(self, mixed_diff):
        original_keys = list(mixed_diff.keys())
        sort_diff(mixed_diff, by=SortKey.NAME)
        assert list(mixed_diff.keys()) == original_keys
