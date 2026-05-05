"""Tests for envdiff.differ module."""

import pytest
from envdiff.differ import diff_envs, DiffResult


STAGING = {
    "APP_NAME": "myapp",
    "DB_HOST": "staging-db.internal",
    "DB_PORT": "5432",
    "SECRET_KEY": "staging-secret",
    "DEBUG": "true",
}

PRODUCTION = {
    "APP_NAME": "myapp",
    "DB_HOST": "prod-db.internal",
    "DB_PORT": "5432",
    "SECRET_KEY": "prod-secret",
    "LOG_LEVEL": "info",
}


class TestDiffEnvs:
    def test_only_in_left(self):
        result = diff_envs(STAGING, PRODUCTION)
        assert "DEBUG" in result.only_in_left
        assert result.only_in_left["DEBUG"] == "true"

    def test_only_in_right(self):
        result = diff_envs(STAGING, PRODUCTION)
        assert "LOG_LEVEL" in result.only_in_right
        assert result.only_in_right["LOG_LEVEL"] == "info"

    def test_value_mismatches(self):
        result = diff_envs(STAGING, PRODUCTION)
        assert "DB_HOST" in result.value_mismatches
        assert result.value_mismatches["DB_HOST"] == ("staging-db.internal", "prod-db.internal")
        assert "SECRET_KEY" in result.value_mismatches

    def test_matching_keys(self):
        result = diff_envs(STAGING, PRODUCTION)
        assert "APP_NAME" in result.matching
        assert "DB_PORT" in result.matching

    def test_has_differences_true(self):
        result = diff_envs(STAGING, PRODUCTION)
        assert result.has_differences is True

    def test_has_differences_false(self):
        env = {"KEY": "value"}
        result = diff_envs(env, env.copy())
        assert result.has_differences is False

    def test_ignore_keys(self):
        result = diff_envs(STAGING, PRODUCTION, ignore_keys=["SECRET_KEY", "DEBUG", "LOG_LEVEL"])
        assert "SECRET_KEY" not in result.value_mismatches
        assert "DEBUG" not in result.only_in_left
        assert "LOG_LEVEL" not in result.only_in_right

    def test_empty_envs(self):
        result = diff_envs({}, {})
        assert not result.has_differences

    def test_identical_envs(self):
        result = diff_envs(STAGING, STAGING.copy())
        assert not result.has_differences
        assert len(result.matching) == len(STAGING)

    def test_summary_no_differences(self):
        result = diff_envs({"K": "v"}, {"K": "v"})
        assert result.summary == "No differences found."

    def test_summary_with_differences(self):
        result = diff_envs(STAGING, PRODUCTION)
        summary = result.summary
        assert "Differences detected" in summary
        assert "Value mismatch" in summary

    def test_ignore_keys_empty_list(self):
        result_no_ignore = diff_envs(STAGING, PRODUCTION)
        result_empty_ignore = diff_envs(STAGING, PRODUCTION, ignore_keys=[])
        assert result_no_ignore.value_mismatches == result_empty_ignore.value_mismatches
