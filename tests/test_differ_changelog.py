"""Tests for envdiff.differ_changelog."""

import pytest

from envdiff.differ import DiffResult
from envdiff.differ_changelog import (
    ChangelogEntry,
    DiffChangelog,
    build_changelog,
)


def _make_diff(
    only_left=None,
    only_right=None,
    mismatches=None,
    matching=None,
) -> DiffResult:
    return DiffResult(
        only_in_left=only_left or [],
        only_in_right=only_right or [],
        value_mismatches=mismatches or {},
        matching_keys=matching or [],
        left={k: "L" for k in (only_left or [])},
        right={k: "R" for k in (only_right or [])},
    )


@pytest.fixture
def snap_a():
    return _make_diff(only_left=["OLD_KEY"], mismatches={"DB_HOST": ("a", "b")})


@pytest.fixture
def snap_b():
    return _make_diff(only_right=["NEW_KEY"], mismatches={"DB_HOST": ("b", "c")})


@pytest.fixture
def snap_c():
    return _make_diff(matching=["DB_HOST"])


class TestChangelogEntry:
    def test_is_empty_when_no_changes(self):
        entry = ChangelogEntry(label="v1")
        assert entry.is_empty()

    def test_not_empty_when_added(self):
        entry = ChangelogEntry(label="v1", added=["FOO"])
        assert not entry.is_empty()

    def test_str_includes_label(self):
        entry = ChangelogEntry(label="v2", added=["X"])
        assert "[v2]" in str(entry)

    def test_str_marks_added_with_plus(self):
        entry = ChangelogEntry(label="v1", added=["NEW"])
        assert "+ NEW" in str(entry)

    def test_str_marks_removed_with_minus(self):
        entry = ChangelogEntry(label="v1", removed=["OLD"])
        assert "- OLD" in str(entry)

    def test_str_marks_changed_with_tilde(self):
        entry = ChangelogEntry(label="v1", changed=["MOD"])
        assert "~ MOD" in str(entry)

    def test_str_no_changes_shows_notice(self):
        entry = ChangelogEntry(label="v1")
        assert "(no changes)" in str(entry)


class TestBuildChangelog:
    def test_returns_diff_changelog_type(self, snap_a, snap_b):
        result = build_changelog([snap_a, snap_b])
        assert isinstance(result, DiffChangelog)

    def test_single_diff_returns_empty_changelog(self, snap_a):
        result = build_changelog([snap_a])
        assert result.entries == []

    def test_entry_count_equals_transitions(self, snap_a, snap_b, snap_c):
        result = build_changelog([snap_a, snap_b, snap_c])
        assert len(result.entries) == 2

    def test_custom_labels_applied(self, snap_a, snap_b):
        result = build_changelog([snap_a, snap_b], labels=["v1->v2"])
        assert result.entries[0].label == "v1->v2"

    def test_default_label_format(self, snap_a, snap_b):
        result = build_changelog([snap_a, snap_b])
        assert result.entries[0].label == "step-1"

    def test_wrong_label_count_raises(self, snap_a, snap_b):
        with pytest.raises(ValueError, match="Expected 1 labels"):
            build_changelog([snap_a, snap_b], labels=["a", "b"])

    def test_added_key_detected(self, snap_a, snap_b):
        result = build_changelog([snap_a, snap_b])
        assert "NEW_KEY" in result.entries[0].added

    def test_removed_key_detected(self, snap_a, snap_b):
        result = build_changelog([snap_a, snap_b])
        assert "OLD_KEY" in result.entries[0].removed

    def test_total_changes_sums_all_entries(self, snap_a, snap_b, snap_c):
        result = build_changelog([snap_a, snap_b, snap_c])
        assert result.total_changes() >= 0

    def test_non_empty_entries_excludes_empty(self, snap_a, snap_b, snap_c):
        result = build_changelog([snap_a, snap_b, snap_c])
        for e in result.non_empty_entries():
            assert not e.is_empty()

    def test_str_contains_all_labels(self, snap_a, snap_b, snap_c):
        result = build_changelog([snap_a, snap_b, snap_c], labels=["A->B", "B->C"])
        s = str(result)
        assert "A->B" in s
        assert "B->C" in s

    def test_empty_changelog_str(self):
        cl = DiffChangelog()
        assert "empty" in str(cl)
