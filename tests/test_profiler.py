"""Tests for envdiff.profiler."""

import pytest

from envdiff.differ import DiffResult
from envdiff.profiler import EnvProfile, profile_diff


@pytest.fixture()
def full_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"OLD_FLAG": "1"},
        only_in_right={"NEW_FEATURE": "enabled"},
        matching={"APP_NAME": "envdiff"},
        mismatched={
            "DB_PASSWORD": ("hunter2", "s3cr3t"),
            "LOG_LEVEL": ("DEBUG", "INFO"),
        },
    )


class TestProfileDiff:
    def test_returns_env_profile_type(self, full_diff):
        result = profile_diff(full_diff)
        assert isinstance(result, EnvProfile)

    def test_total_keys(self, full_diff):
        result = profile_diff(full_diff)
        # 1 left-only + 1 right-only + 1 matching + 2 mismatched
        assert result.total_keys == 5

    def test_only_in_left_count(self, full_diff):
        assert profile_diff(full_diff).only_in_left == 1

    def test_only_in_right_count(self, full_diff):
        assert profile_diff(full_diff).only_in_right == 1

    def test_matching_count(self, full_diff):
        assert profile_diff(full_diff).matching == 1

    def test_mismatched_count(self, full_diff):
        assert profile_diff(full_diff).mismatched == 2

    def test_sensitive_keys_detected(self, full_diff):
        result = profile_diff(full_diff)
        assert "DB_PASSWORD" in result.sensitive_keys

    def test_non_sensitive_keys_excluded(self, full_diff):
        result = profile_diff(full_diff)
        assert "LOG_LEVEL" not in result.sensitive_keys
        assert "APP_NAME" not in result.sensitive_keys

    def test_coverage_between_zero_and_one(self, full_diff):
        result = profile_diff(full_diff)
        assert 0.0 <= result.coverage <= 1.0

    def test_coverage_value(self, full_diff):
        # matching + mismatched = 3, total = 5 → 0.6
        assert profile_diff(full_diff).coverage == pytest.approx(0.6)

    def test_longest_key_populated(self, full_diff):
        result = profile_diff(full_diff)
        assert isinstance(result.longest_key, str)
        assert len(result.longest_key) > 0

    def test_longest_value_key_populated(self, full_diff):
        result = profile_diff(full_diff)
        assert isinstance(result.longest_value_key, str)

    def test_to_dict_contains_expected_keys(self, full_diff):
        d = profile_diff(full_diff).to_dict()
        for key in (
            "total_keys", "only_in_left", "only_in_right",
            "matching", "mismatched", "coverage",
            "sensitive_keys", "longest_key", "longest_value_key",
        ):
            assert key in d

    def test_empty_diff_returns_zero_totals(self):
        empty = DiffResult({}, {}, {}, {})
        result = profile_diff(empty)
        assert result.total_keys == 0
        assert result.coverage == 0.0
        assert result.sensitive_keys == []
        assert result.longest_key == ""
