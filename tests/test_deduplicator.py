"""Tests for envdiff.deduplicator."""

from __future__ import annotations

import pytest

from envdiff.deduplicator import (
    DeduplicationReport,
    _find_duplicates,
    deduplicate_diff,
)
from envdiff.differ import DiffResult


@pytest.fixture()
def matching_diff() -> DiffResult:
    return DiffResult(
        only_in_left=[],
        only_in_right=[],
        value_mismatches={},
        matching_keys=["HOST", "PORT", "DEBUG"],
    )


@pytest.fixture()
def mixed_diff() -> DiffResult:
    return DiffResult(
        only_in_left=["EXTRA"],
        only_in_right=["NEW_KEY"],
        value_mismatches={"LOG_LEVEL": ("info", "debug")},
        matching_keys=["HOST", "PORT"],
    )


class TestFindDuplicates:
    def test_no_duplicates_returns_empty(self):
        assert _find_duplicates({"A": "1", "B": "2"}) == []

    def test_case_collision_detected(self):
        dupes = _find_duplicates({"host": "a", "HOST": "b"})
        assert "HOST" in dupes

    def test_unique_keys_all_different_case_no_collision(self):
        # Same casing — no collision
        assert _find_duplicates({"HOST": "a", "PORT": "b"}) == []


class TestDeduplicationReport:
    def test_is_clean_when_empty(self):
        report = DeduplicationReport()
        assert report.is_clean is True

    def test_is_not_clean_with_left_duplicates(self):
        report = DeduplicationReport(duplicates_left=["HOST"])
        assert report.is_clean is False

    def test_is_not_clean_with_redundant_matches(self):
        report = DeduplicationReport(redundant_matches=["PORT"])
        assert report.is_clean is False

    def test_summary_clean(self):
        report = DeduplicationReport()
        assert "No duplicates" in report.summary()

    def test_summary_includes_left_duplicates(self):
        report = DeduplicationReport(duplicates_left=["HOST"])
        assert "Left duplicates" in report.summary()
        assert "HOST" in report.summary()

    def test_summary_includes_redundant(self):
        report = DeduplicationReport(redundant_matches=["PORT", "HOST"])
        assert "Redundant" in report.summary()


class TestDeduplicateDiff:
    def test_returns_deduplication_report_type(self, matching_diff):
        left = {"HOST": "a", "PORT": "80", "DEBUG": "true"}
        right = {"HOST": "a", "PORT": "80", "DEBUG": "true"}
        result = deduplicate_diff(left, right, matching_diff)
        assert isinstance(result, DeduplicationReport)

    def test_identical_matching_keys_are_redundant(self, matching_diff):
        left = {"HOST": "a", "PORT": "80", "DEBUG": "true"}
        right = {"HOST": "a", "PORT": "80", "DEBUG": "true"}
        result = deduplicate_diff(left, right, matching_diff)
        assert set(result.redundant_matches) == {"HOST", "PORT", "DEBUG"}

    def test_differing_matching_key_not_redundant(self, mixed_diff):
        left = {"HOST": "a", "PORT": "80", "LOG_LEVEL": "info", "EXTRA": "x"}
        right = {"HOST": "a", "PORT": "80", "LOG_LEVEL": "debug", "NEW_KEY": "y"}
        result = deduplicate_diff(left, right, mixed_diff)
        assert "LOG_LEVEL" not in result.redundant_matches

    def test_no_case_collision_gives_empty_left_dupes(self, matching_diff):
        left = {"HOST": "a", "PORT": "80", "DEBUG": "true"}
        right = {"HOST": "a", "PORT": "80", "DEBUG": "true"}
        result = deduplicate_diff(left, right, matching_diff)
        assert result.duplicates_left == []

    def test_is_clean_when_no_issues(self, mixed_diff):
        left = {"HOST": "a", "PORT": "80", "LOG_LEVEL": "info", "EXTRA": "x"}
        right = {"HOST": "b", "PORT": "80", "LOG_LEVEL": "debug", "NEW_KEY": "y"}
        result = deduplicate_diff(left, right, mixed_diff)
        assert result.is_clean is True
