"""Tests for envdiff.patcher."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffResult
from envdiff.patcher import PatchResult, PatchStrategy, patch_env


@pytest.fixture()
def base_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"NEW_KEY": "new_val"},
        only_in_right={"OLD_KEY": "old_val"},
        mismatches={"SHARED": ("left_val", "right_val")},
        matching={"SAME": "same_val"},
    )


@pytest.fixture()
def target() -> dict:
    return {
        "SHARED": "right_val",
        "OLD_KEY": "old_val",
        "SAME": "same_val",
    }


class TestPatchResult:
    def test_change_count_sums_all_lists(self):
        pr = PatchResult(
            patched={},
            added=["A"],
            overwritten=["B", "C"],
            removed=["D"],
        )
        assert pr.change_count == 4

    def test_summary_no_changes(self):
        pr = PatchResult(patched={})
        assert pr.summary() == "no changes applied"

    def test_summary_with_changes(self):
        pr = PatchResult(patched={}, added=["A"], overwritten=["B"])
        assert "1 added" in pr.summary()
        assert "1 overwritten" in pr.summary()


class TestPatchEnvAddMissing:
    def test_returns_patch_result(self, target, base_diff):
        result = patch_env(target, base_diff)
        assert isinstance(result, PatchResult)

    def test_adds_only_in_left(self, target, base_diff):
        result = patch_env(target, base_diff)
        assert "NEW_KEY" in result.patched
        assert result.patched["NEW_KEY"] == "new_val"

    def test_does_not_overwrite_mismatch_by_default(self, target, base_diff):
        result = patch_env(target, base_diff)
        assert result.patched["SHARED"] == "right_val"
        assert result.overwritten == []

    def test_does_not_remove_right_only_by_default(self, target, base_diff):
        result = patch_env(target, base_diff)
        assert "OLD_KEY" in result.patched
        assert result.removed == []

    def test_added_list_populated(self, target, base_diff):
        result = patch_env(target, base_diff)
        assert "NEW_KEY" in result.added


class TestPatchEnvOverwrite:
    def test_overwrites_mismatch_values(self, target, base_diff):
        result = patch_env(target, base_diff, strategy=PatchStrategy.OVERWRITE)
        assert result.patched["SHARED"] == "left_val"
        assert "SHARED" in result.overwritten

    def test_does_not_remove_right_only(self, target, base_diff):
        result = patch_env(target, base_diff, strategy=PatchStrategy.OVERWRITE)
        assert "OLD_KEY" in result.patched


class TestPatchEnvFull:
    def test_removes_right_only_keys(self, target, base_diff):
        result = patch_env(target, base_diff, strategy=PatchStrategy.FULL)
        assert "OLD_KEY" not in result.patched
        assert "OLD_KEY" in result.removed

    def test_adds_and_overwrites_and_removes(self, target, base_diff):
        result = patch_env(target, base_diff, strategy=PatchStrategy.FULL)
        assert "NEW_KEY" in result.patched
        assert result.patched["SHARED"] == "left_val"
        assert "OLD_KEY" not in result.patched


class TestPatchEnvExclude:
    def test_excluded_key_not_added(self, target, base_diff):
        result = patch_env(target, base_diff, exclude=["NEW_KEY"])
        assert "NEW_KEY" not in result.patched
        assert "NEW_KEY" not in result.added

    def test_excluded_key_not_removed(self, target, base_diff):
        result = patch_env(
            target, base_diff, strategy=PatchStrategy.FULL, exclude=["OLD_KEY"]
        )
        assert "OLD_KEY" in result.patched
        assert "OLD_KEY" not in result.removed
