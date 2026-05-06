"""Tests for envdiff.merger."""

import pytest

from envdiff.merger import (
    MergeConflictError,
    MergeStrategy,
    conflicts,
    merge_envs,
)


@pytest.fixture
def left():
    return {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}


@pytest.fixture
def right():
    return {"PORT": "9999", "LOG_LEVEL": "info"}


class TestMergeEnvs:
    def test_right_strategy_overrides_conflict(self, left, right):
        result = merge_envs(left, right, strategy=MergeStrategy.RIGHT)
        assert result["PORT"] == "9999"

    def test_left_strategy_keeps_base_on_conflict(self, left, right):
        result = merge_envs(left, right, strategy=MergeStrategy.LEFT)
        assert result["PORT"] == "5432"

    def test_new_keys_from_right_always_added(self, left, right):
        result = merge_envs(left, right, strategy=MergeStrategy.LEFT)
        assert result["LOG_LEVEL"] == "info"

    def test_non_conflicting_left_keys_preserved(self, left, right):
        result = merge_envs(left, right)
        assert result["HOST"] == "localhost"
        assert result["DEBUG"] == "true"

    def test_strict_strategy_raises_on_conflict(self, left, right):
        with pytest.raises(MergeConflictError) as exc_info:
            merge_envs(left, right, strategy=MergeStrategy.STRICT)
        assert exc_info.value.key == "PORT"
        assert exc_info.value.left_val == "5432"
        assert exc_info.value.right_val == "9999"

    def test_strict_strategy_no_error_when_no_conflict(self, left):
        right_no_conflict = {"NEW_KEY": "value"}
        result = merge_envs(left, right_no_conflict, strategy=MergeStrategy.STRICT)
        assert result["NEW_KEY"] == "value"

    def test_prefix_filter_limits_right_keys(self, left):
        right_mixed = {"APP_PORT": "8080", "PORT": "9999", "APP_DEBUG": "false"}
        result = merge_envs(left, right_mixed, prefix="APP_")
        assert result["PORT"] == "5432"  # not overridden — no APP_ prefix
        assert result["APP_PORT"] == "8080"
        assert result["APP_DEBUG"] == "false"

    def test_identical_values_do_not_conflict(self):
        env = {"KEY": "same"}
        result = merge_envs(env, {"KEY": "same"}, strategy=MergeStrategy.STRICT)
        assert result["KEY"] == "same"

    def test_empty_left_returns_right(self, right):
        result = merge_envs({}, right)
        assert result == right

    def test_empty_right_returns_left(self, left):
        result = merge_envs(left, {})
        assert result == left

    def test_returns_new_dict_does_not_mutate_left(self, left, right):
        original_port = left["PORT"]
        merge_envs(left, right, strategy=MergeStrategy.RIGHT)
        assert left["PORT"] == original_port


class TestConflicts:
    def test_detects_conflicting_keys(self, left, right):
        result = conflicts(left, right)
        assert "PORT" in result
        assert result["PORT"] == ("5432", "9999")

    def test_no_conflicts_returns_empty(self):
        assert conflicts({"A": "1"}, {"B": "2"}) == {}

    def test_identical_values_not_flagged(self):
        assert conflicts({"A": "same"}, {"A": "same"}) == {}

    def test_multiple_conflicts_all_reported(self):
        l = {"X": "1", "Y": "2"}
        r = {"X": "9", "Y": "8"}
        result = conflicts(l, r)
        assert len(result) == 2
