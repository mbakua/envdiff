"""Tests for envdiff.differ_snapshot_delta."""
from __future__ import annotations

import pytest

from envdiff.differ import DiffResult
from envdiff.differ_snapshot_delta import (
    DeltaEntry,
    SnapshotDelta,
    compute_snapshot_delta,
)


def _make_diff(
    left: dict,
    right: dict,
    only_left=(),
    only_right=(),
    mismatches=None,
    matching=(),
) -> DiffResult:
    mismatches = mismatches or {}
    return DiffResult(
        left=left,
        right=right,
        only_in_left=list(only_left),
        only_in_right=list(only_right),
        value_mismatches=mismatches,
        matching_keys=list(matching),
    )


@pytest.fixture
def before_diff():
    return _make_diff(
        left={"DB_HOST": "localhost", "API_KEY": "old", "LOG_LEVEL": "debug"},
        right={},
        only_left=["DB_HOST", "API_KEY", "LOG_LEVEL"],
    )


@pytest.fixture
def after_diff():
    return _make_diff(
        left={"DB_HOST": "prod.db", "API_KEY": "old", "NEW_KEY": "val"},
        right={},
        only_left=["DB_HOST", "API_KEY", "NEW_KEY"],
    )


class TestSnapshotDelta:
    def test_returns_snapshot_delta_type(self, before_diff, after_diff):
        delta = compute_snapshot_delta(before_diff, after_diff)
        assert isinstance(delta, SnapshotDelta)

    def test_detects_added_key(self, before_diff, after_diff):
        delta = compute_snapshot_delta(before_diff, after_diff)
        added_keys = [e.key for e in delta.added]
        assert "NEW_KEY" in added_keys

    def test_detects_removed_key(self, before_diff, after_diff):
        delta = compute_snapshot_delta(before_diff, after_diff)
        removed_keys = [e.key for e in delta.removed]
        assert "LOG_LEVEL" in removed_keys

    def test_detects_changed_value(self, before_diff, after_diff):
        delta = compute_snapshot_delta(before_diff, after_diff)
        changed_keys = [e.key for e in delta.changed]
        assert "DB_HOST" in changed_keys

    def test_unchanged_key_not_in_delta(self, before_diff, after_diff):
        delta = compute_snapshot_delta(before_diff, after_diff)
        all_keys = (
            [e.key for e in delta.added]
            + [e.key for e in delta.removed]
            + [e.key for e in delta.changed]
        )
        assert "API_KEY" not in all_keys

    def test_total_changes_correct(self, before_diff, after_diff):
        delta = compute_snapshot_delta(before_diff, after_diff)
        assert delta.total_changes == 3

    def test_is_empty_false_when_changes(self, before_diff, after_diff):
        delta = compute_snapshot_delta(before_diff, after_diff)
        assert not delta.is_empty

    def test_is_empty_true_for_identical(self, before_diff):
        delta = compute_snapshot_delta(before_diff, before_diff)
        assert delta.is_empty

    def test_summary_includes_counts(self, before_diff, after_diff):
        delta = compute_snapshot_delta(before_diff, after_diff)
        s = delta.summary()
        assert "+1" in s or "added" in s

    def test_to_dict_keys(self, before_diff, after_diff):
        delta = compute_snapshot_delta(before_diff, after_diff)
        d = delta.to_dict()
        assert set(d.keys()) == {"added", "removed", "changed"}


class TestDeltaEntry:
    def test_status_added(self):
        e = DeltaEntry(key="X", before=None, after="v")
        assert e.status == "added"

    def test_status_removed(self):
        e = DeltaEntry(key="X", before="v", after=None)
        assert e.status == "removed"

    def test_status_changed(self):
        e = DeltaEntry(key="X", before="a", after="b")
        assert e.status == "changed"

    def test_str_representation(self):
        e = DeltaEntry(key="K", before="old", after="new")
        assert "K" in str(e) and "old" in str(e) and "new" in str(e)
