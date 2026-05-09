"""Tests for envdiff.trimmer."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffResult
from envdiff.trimmer import TrimResult, trim_by_prefix, trim_keys, trim_matching


@pytest.fixture()
def mixed_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"ONLY_LEFT": "a", "DEBUG": "true"},
        only_in_right={"ONLY_RIGHT": "b"},
        value_mismatches={"DB_HOST": ("localhost", "prod.db"), "API_KEY": ("x", "y")},
        matching_keys={"PORT": "8080", "APP_NAME": "envdiff"},
    )


# ---------------------------------------------------------------------------
# TrimResult
# ---------------------------------------------------------------------------

class TestTrimResult:
    def test_removal_count(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, ["PORT"])
        assert result.removal_count == 1

    def test_returns_trim_result_type(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, [])
        assert isinstance(result, TrimResult)

    def test_diff_is_diff_result_type(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, [])
        assert isinstance(result.diff, DiffResult)


# ---------------------------------------------------------------------------
# trim_keys
# ---------------------------------------------------------------------------

class TestTrimKeys:
    def test_removes_from_only_in_left(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, ["ONLY_LEFT"])
        assert "ONLY_LEFT" not in result.diff.only_in_left

    def test_removes_from_only_in_right(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, ["ONLY_RIGHT"])
        assert "ONLY_RIGHT" not in result.diff.only_in_right

    def test_removes_from_value_mismatches(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, ["DB_HOST"])
        assert "DB_HOST" not in result.diff.value_mismatches

    def test_removes_from_matching_keys(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, ["PORT"])
        assert "PORT" not in result.diff.matching_keys

    def test_unrelated_keys_preserved(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, ["PORT"])
        assert "APP_NAME" in result.diff.matching_keys

    def test_removed_keys_recorded(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, ["PORT", "DEBUG"])
        assert set(result.removed_keys) == {"PORT", "DEBUG"}

    def test_nonexistent_key_not_in_removed(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, ["NONEXISTENT"])
        assert "NONEXISTENT" not in result.removed_keys

    def test_empty_key_list_changes_nothing(self, mixed_diff: DiffResult) -> None:
        result = trim_keys(mixed_diff, [])
        assert result.removal_count == 0
        assert result.diff.only_in_left == mixed_diff.only_in_left

    def test_duplicate_keys_deduplicated_in_removed(self, mixed_diff: DiffResult) -> None:
        # PORT appears only in matching_keys; passing it twice should record once
        result = trim_keys(mixed_diff, ["PORT", "PORT"])
        assert result.removed_keys.count("PORT") == 1


# ---------------------------------------------------------------------------
# trim_matching
# ---------------------------------------------------------------------------

class TestTrimMatching:
    def test_matching_keys_empty_after_trim(self, mixed_diff: DiffResult) -> None:
        result = trim_matching(mixed_diff)
        assert result.diff.matching_keys == {}

    def test_other_sections_untouched(self, mixed_diff: DiffResult) -> None:
        result = trim_matching(mixed_diff)
        assert result.diff.only_in_left == mixed_diff.only_in_left
        assert result.diff.only_in_right == mixed_diff.only_in_right
        assert result.diff.value_mismatches == mixed_diff.value_mismatches

    def test_removed_keys_contains_matching(self, mixed_diff: DiffResult) -> None:
        result = trim_matching(mixed_diff)
        assert set(result.removed_keys) == {"PORT", "APP_NAME"}


# ---------------------------------------------------------------------------
# trim_by_prefix
# ---------------------------------------------------------------------------

class TestTrimByPrefix:
    def test_removes_keys_with_prefix(self, mixed_diff: DiffResult) -> None:
        result = trim_by_prefix(mixed_diff, "DB_")
        assert "DB_HOST" not in result.diff.value_mismatches

    def test_case_insensitive_prefix(self, mixed_diff: DiffResult) -> None:
        result = trim_by_prefix(mixed_diff, "db_")
        assert "DB_HOST" not in result.diff.value_mismatches

    def test_unrelated_keys_survive(self, mixed_diff: DiffResult) -> None:
        result = trim_by_prefix(mixed_diff, "DB_")
        assert "API_KEY" in result.diff.value_mismatches

    def test_removal_count_reflects_prefix_matches(self, mixed_diff: DiffResult) -> None:
        result = trim_by_prefix(mixed_diff, "only")
        # ONLY_LEFT and ONLY_RIGHT both start with "only" (case-insensitive)
        assert result.removal_count == 2
