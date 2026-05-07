"""Integration tests: recommender + differ working together."""

import pytest

from envdiff.differ import diff_envs
from envdiff.recommender import recommend


class TestRecommenderIntegration:
    def test_full_match_yields_no_recommendations(self):
        env = {"HOST": "localhost", "PORT": "5432"}
        diff = diff_envs(env, env)
        report = recommend(diff)
        assert report.recommendations == []

    def test_missing_secret_in_right_is_error(self):
        left = {"DB_SECRET": "abc123", "HOST": "localhost"}
        right = {"HOST": "localhost"}
        diff = diff_envs(left, right)
        report = recommend(diff)
        keys = [r.key for r in report.errors]
        assert "DB_SECRET" in keys

    def test_missing_plain_key_in_right_is_warning(self):
        left = {"LOG_LEVEL": "debug", "HOST": "localhost"}
        right = {"HOST": "localhost"}
        diff = diff_envs(left, right)
        report = recommend(diff)
        keys = [r.key for r in report.warnings]
        assert "LOG_LEVEL" in keys

    def test_value_mismatch_on_token_is_error(self):
        left = {"API_TOKEN": "old", "HOST": "h"}
        right = {"API_TOKEN": "new", "HOST": "h"}
        diff = diff_envs(left, right)
        report = recommend(diff)
        errors = [r.key for r in report.errors]
        assert "API_TOKEN" in errors

    def test_all_severities_present_in_mixed_env(self):
        left = {"API_TOKEN": "t1", "LOG_LEVEL": "debug", "EXTRA": "val"}
        right = {"API_TOKEN": "t2", "LOG_LEVEL": "info"}
        diff = diff_envs(left, right)
        report = recommend(diff)
        severities = {r.severity for r in report.recommendations}
        assert "error" in severities
        assert "info" in severities

    def test_report_summary_is_string(self):
        left = {"SECRET_KEY": "a"}
        right = {"SECRET_KEY": "b"}
        diff = diff_envs(left, right)
        report = recommend(diff)
        assert isinstance(report.summary(), str)
