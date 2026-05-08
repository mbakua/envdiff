"""Tests for envdiff.tracker."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffResult
from envdiff.tracker import KeyHistory, TrackingReport, track_diffs


@pytest.fixture()
def diff_a() -> DiffResult:
    return DiffResult(
        only_in_left=["REMOVED"],
        only_in_right=["ADDED"],
        value_mismatches={"HOST": ("old", "new")},
        matching_keys=["PORT"],
    )


@pytest.fixture()
def diff_b() -> DiffResult:
    return DiffResult(
        only_in_left=[],
        only_in_right=[],
        value_mismatches={},
        matching_keys=["HOST", "PORT"],
    )


class TestTrackDiffs:
    def test_returns_tracking_report_type(self, diff_a):
        result = track_diffs([("stage-a", diff_a)])
        assert isinstance(result, TrackingReport)

    def test_all_keys_recorded(self, diff_a):
        result = track_diffs([("stage-a", diff_a)])
        assert "REMOVED" in result.entries
        assert "ADDED" in result.entries
        assert "HOST" in result.entries
        assert "PORT" in result.entries

    def test_left_only_status(self, diff_a):
        result = track_diffs([("stage-a", diff_a)])
        assert result.entries["REMOVED"].statuses == ["left_only"]

    def test_right_only_status(self, diff_a):
        result = track_diffs([("stage-a", diff_a)])
        assert result.entries["ADDED"].statuses == ["right_only"]

    def test_mismatch_status(self, diff_a):
        result = track_diffs([("stage-a", diff_a)])
        assert result.entries["HOST"].statuses == ["mismatch"]

    def test_match_status(self, diff_a):
        result = track_diffs([("stage-a", diff_a)])
        assert result.entries["PORT"].statuses == ["match"]

    def test_multiple_diffs_accumulate(self, diff_a, diff_b):
        result = track_diffs([("a", diff_a), ("b", diff_b)])
        assert len(result.entries["HOST"].statuses) == 2
        assert result.entries["HOST"].statuses == ["mismatch", "match"]

    def test_empty_input_returns_empty_report(self):
        result = track_diffs([])
        assert result.entries == {}


class TestKeyHistory:
    def test_change_count_counts_non_matches(self):
        h = KeyHistory(key="X", statuses=["match", "mismatch", "left_only"])
        assert h.change_count == 2

    def test_is_stable_when_all_match(self):
        h = KeyHistory(key="X", statuses=["match", "match"])
        assert h.is_stable is True

    def test_is_not_stable_when_any_mismatch(self):
        h = KeyHistory(key="X", statuses=["match", "mismatch"])
        assert h.is_stable is False


class TestTrackingReport:
    def test_unstable_keys(self, diff_a):
        result = track_diffs([("a", diff_a)])
        assert "PORT" not in result.unstable_keys
        assert "HOST" in result.unstable_keys

    def test_stable_keys(self, diff_a):
        result = track_diffs([("a", diff_a)])
        assert "PORT" in result.stable_keys

    def test_summary_string(self, diff_a):
        result = track_diffs([("a", diff_a)])
        s = result.summary()
        assert "Tracked" in s
        assert "stable" in s
        assert "unstable" in s
