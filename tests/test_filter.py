"""Tests for envdiff.filter module."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffResult
from envdiff.filter import exclude_keys, filter_by_pattern, filter_by_prefix


@pytest.fixture()
def sample_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"AWS_KEY": "abc", "DB_HOST": "localhost"},
        only_in_right={"AWS_SECRET": "xyz", "APP_PORT": "8080"},
        value_mismatches={"AWS_REGION": ("us-east-1", "eu-west-1"), "LOG_LEVEL": ("DEBUG", "INFO")},
        matching_keys={"APP_NAME", "DB_PORT"},
    )


class TestFilterByPrefix:
    def test_matching_prefix_filters_correctly(self, sample_diff: DiffResult) -> None:
        result = filter_by_prefix(sample_diff, "AWS")
        assert set(result.only_in_left.keys()) == {"AWS_KEY"}
        assert set(result.only_in_right.keys()) == {"AWS_SECRET"}
        assert set(result.value_mismatches.keys()) == {"AWS_REGION"}
        assert result.matching_keys == set()

    def test_prefix_case_insensitive(self, sample_diff: DiffResult) -> None:
        result = filter_by_prefix(sample_diff, "aws")
        assert "AWS_KEY" in result.only_in_left
        assert "AWS_SECRET" in result.only_in_right

    def test_no_match_returns_empty(self, sample_diff: DiffResult) -> None:
        result = filter_by_prefix(sample_diff, "NONEXISTENT")
        assert not result.only_in_left
        assert not result.only_in_right
        assert not result.value_mismatches
        assert not result.matching_keys

    def test_db_prefix(self, sample_diff: DiffResult) -> None:
        result = filter_by_prefix(sample_diff, "DB")
        assert "DB_HOST" in result.only_in_left
        assert "DB_PORT" in result.matching_keys


class TestFilterByPattern:
    def test_regex_pattern_matches(self, sample_diff: DiffResult) -> None:
        result = filter_by_pattern(sample_diff, r"^AWS_")
        assert "AWS_KEY" in result.only_in_left
        assert "AWS_SECRET" in result.only_in_right
        assert "AWS_REGION" in result.value_mismatches

    def test_partial_pattern(self, sample_diff: DiffResult) -> None:
        result = filter_by_pattern(sample_diff, r"PORT")
        assert "APP_PORT" in result.only_in_right
        assert "DB_PORT" in result.matching_keys

    def test_invalid_keys_excluded(self, sample_diff: DiffResult) -> None:
        result = filter_by_pattern(sample_diff, r"^LOG")
        assert set(result.value_mismatches.keys()) == {"LOG_LEVEL"}
        assert not result.only_in_left
        assert not result.only_in_right


class TestExcludeKeys:
    def test_excludes_specified_keys(self, sample_diff: DiffResult) -> None:
        result = exclude_keys(sample_diff, ["AWS_KEY", "LOG_LEVEL", "APP_NAME"])
        assert "AWS_KEY" not in result.only_in_left
        assert "LOG_LEVEL" not in result.value_mismatches
        assert "APP_NAME" not in result.matching_keys

    def test_exclusion_case_insensitive(self, sample_diff: DiffResult) -> None:
        result = exclude_keys(sample_diff, ["aws_key"])
        assert "AWS_KEY" not in result.only_in_left

    def test_non_existent_key_no_error(self, sample_diff: DiffResult) -> None:
        result = exclude_keys(sample_diff, ["DOES_NOT_EXIST"])
        assert result.only_in_left == sample_diff.only_in_left

    def test_empty_exclusion_list(self, sample_diff: DiffResult) -> None:
        result = exclude_keys(sample_diff, [])
        assert result.only_in_left == sample_diff.only_in_left
        assert result.matching_keys == sample_diff.matching_keys
