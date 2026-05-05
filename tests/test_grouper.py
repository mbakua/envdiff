"""Tests for envdiff.grouper."""

import pytest

from envdiff.differ import DiffResult
from envdiff.grouper import GroupedDiff, group_diff


@pytest.fixture()
def full_diff() -> DiffResult:
    return DiffResult(
        {
            "ONLY_L": {"left": "val", "right": None},
            "ONLY_R": {"left": None, "right": "val"},
            "MISMATCH": {"left": "old", "right": "new"},
            "MATCH": {"left": "same", "right": "same"},
        }
    )


class TestGroupDiff:
    def test_returns_grouped_diff_type(self, full_diff):
        result = group_diff(full_diff)
        assert isinstance(result, GroupedDiff)

    def test_only_in_left_populated(self, full_diff):
        result = group_diff(full_diff)
        assert "ONLY_L" in result.only_in_left
        assert len(result.only_in_left) == 1

    def test_only_in_right_populated(self, full_diff):
        result = group_diff(full_diff)
        assert "ONLY_R" in result.only_in_right
        assert len(result.only_in_right) == 1

    def test_mismatches_populated(self, full_diff):
        result = group_diff(full_diff)
        assert "MISMATCH" in result.mismatches
        assert len(result.mismatches) == 1

    def test_matches_populated(self, full_diff):
        result = group_diff(full_diff)
        assert "MATCH" in result.matches
        assert len(result.matches) == 1

    def test_total_equals_input_size(self, full_diff):
        result = group_diff(full_diff)
        assert result.total() == len(full_diff)

    def test_empty_diff_produces_empty_groups(self):
        result = group_diff(DiffResult({}))
        assert result.total() == 0

    def test_all_matches(self):
        diff = DiffResult(
            {
                "A": {"left": "x", "right": "x"},
                "B": {"left": "y", "right": "y"},
            }
        )
        result = group_diff(diff)
        assert len(result.matches) == 2
        assert len(result.mismatches) == 0
        assert len(result.only_in_left) == 0
        assert len(result.only_in_right) == 0

    def test_all_mismatches(self):
        diff = DiffResult({"X": {"left": "a", "right": "b"}})
        result = group_diff(diff)
        assert len(result.mismatches) == 1
        assert len(result.matches) == 0


class TestNonEmptyGroups:
    def test_yields_only_populated_groups(self, full_diff):
        result = group_diff(full_diff)
        labels = [label for label, _ in result.non_empty_groups()]
        assert set(labels) == {"only_in_left", "only_in_right", "mismatches", "matches"}

    def test_empty_groups_excluded(self):
        diff = DiffResult({"K": {"left": "v", "right": "v"}})
        result = group_diff(diff)
        labels = [label for label, _ in result.non_empty_groups()]
        assert labels == ["matches"]

    def test_yields_diff_result_values(self, full_diff):
        result = group_diff(full_diff)
        for _, group in result.non_empty_groups():
            assert isinstance(group, DiffResult)
