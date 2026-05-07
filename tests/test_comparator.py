"""Tests for envdiff.comparator."""

import pytest

from envdiff.differ import DiffResult
from envdiff.comparator import ComparisonResult, compare_diffs, _issue_keys


@pytest.fixture
def clean_diff() -> DiffResult:
    return DiffResult(
        only_in_left={},
        only_in_right={},
        value_mismatches={},
        matching_keys={"KEY": "val"},
    )


@pytest.fixture
def dirty_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"REMOVED": "x"},
        only_in_right={"ADDED": "y"},
        value_mismatches={"CHANGED": ("old", "new")},
        matching_keys={},
    )


class TestIssueKeys:
    def test_empty_diff_has_no_issue_keys(self, clean_diff):
        assert _issue_keys(clean_diff) == set()

    def test_collects_all_problem_keys(self, dirty_diff):
        keys = _issue_keys(dirty_diff)
        assert keys == {"REMOVED", "ADDED", "CHANGED"}

    def test_only_left_keys_included(self):
        diff = DiffResult(only_in_left={"A": "1"}, only_in_right={},
                          value_mismatches={}, matching_keys={})
        assert "A" in _issue_keys(diff)


class TestCompareDiffs:
    def test_returns_comparison_result_type(self, clean_diff):
        result = compare_diffs(clean_diff, clean_diff)
        assert isinstance(result, ComparisonResult)

    def test_no_changes_between_identical_clean_diffs(self, clean_diff):
        result = compare_diffs(clean_diff, clean_diff)
        assert result.resolved == []
        assert result.introduced == []
        assert result.unchanged_issues == []

    def test_resolved_keys_detected(self, dirty_diff, clean_diff):
        result = compare_diffs(dirty_diff, clean_diff)
        assert "REMOVED" in result.resolved
        assert "ADDED" in result.resolved
        assert "CHANGED" in result.resolved

    def test_introduced_keys_detected(self, clean_diff, dirty_diff):
        result = compare_diffs(clean_diff, dirty_diff)
        assert "REMOVED" in result.introduced
        assert "ADDED" in result.introduced

    def test_unchanged_issues_detected(self, dirty_diff):
        result = compare_diffs(dirty_diff, dirty_diff)
        assert set(result.unchanged_issues) == {"REMOVED", "ADDED", "CHANGED"}
        assert result.introduced == []
        assert result.resolved == []

    def test_is_improved_true_when_resolved_no_new(self, dirty_diff, clean_diff):
        result = compare_diffs(dirty_diff, clean_diff)
        assert result.is_improved is True

    def test_is_improved_false_when_new_issues(self, clean_diff, dirty_diff):
        result = compare_diffs(clean_diff, dirty_diff)
        assert result.is_improved is False

    def test_has_regressions_true_when_introduced(self, clean_diff, dirty_diff):
        result = compare_diffs(clean_diff, dirty_diff)
        assert result.has_regressions is True

    def test_has_regressions_false_when_clean(self, dirty_diff, clean_diff):
        result = compare_diffs(dirty_diff, clean_diff)
        assert result.has_regressions is False

    def test_summary_no_changes(self, clean_diff):
        result = compare_diffs(clean_diff, clean_diff)
        assert result.summary() == "no changes"

    def test_summary_contains_resolved_count(self, dirty_diff, clean_diff):
        result = compare_diffs(dirty_diff, clean_diff)
        assert "3 resolved" in result.summary()

    def test_results_are_sorted(self, dirty_diff):
        extra = DiffResult(
            only_in_left={"ZEBRA": "z"},
            only_in_right={},
            value_mismatches={},
            matching_keys={},
        )
        result = compare_diffs(dirty_diff, extra)
        assert result.introduced == sorted(result.introduced)
