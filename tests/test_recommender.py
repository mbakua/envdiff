"""Tests for envdiff.recommender."""

import pytest

from envdiff.differ import DiffResult
from envdiff.recommender import recommend, Recommendation, RecommendationReport


@pytest.fixture
def clean_diff():
    return DiffResult(
        only_in_left={},
        only_in_right={},
        value_mismatches={},
        matching_keys={"HOST": "localhost"},
    )


@pytest.fixture
def mixed_diff():
    return DiffResult(
        only_in_left={"DB_PASSWORD": "secret"},
        only_in_right={"NEW_KEY": "value"},
        value_mismatches={
            "API_TOKEN": ("abc", "xyz"),
            "LOG_LEVEL": ("debug", "info"),
            "EMPTY_VAR": ("set", ""),
        },
        matching_keys={"HOST": "localhost"},
    )


class TestRecommend:
    def test_returns_recommendation_report(self, clean_diff):
        result = recommend(clean_diff)
        assert isinstance(result, RecommendationReport)

    def test_no_issues_gives_empty_report(self, clean_diff):
        result = recommend(clean_diff)
        assert result.recommendations == []

    def test_only_in_left_sensitive_is_error(self, mixed_diff):
        result = recommend(mixed_diff)
        rec = next(r for r in result.recommendations if r.key == "DB_PASSWORD")
        assert rec.severity == "error"

    def test_only_in_right_non_sensitive_is_warning(self, mixed_diff):
        result = recommend(mixed_diff)
        rec = next(r for r in result.recommendations if r.key == "NEW_KEY")
        assert rec.severity == "warning"

    def test_sensitive_mismatch_is_error(self, mixed_diff):
        result = recommend(mixed_diff)
        rec = next(r for r in result.recommendations if r.key == "API_TOKEN")
        assert rec.severity == "error"

    def test_non_sensitive_mismatch_is_info(self, mixed_diff):
        result = recommend(mixed_diff)
        rec = next(r for r in result.recommendations if r.key == "LOG_LEVEL")
        assert rec.severity == "info"

    def test_empty_value_mismatch_is_warning(self, mixed_diff):
        result = recommend(mixed_diff)
        rec = next(r for r in result.recommendations if r.key == "EMPTY_VAR")
        assert rec.severity == "warning"

    def test_suggestion_mentions_key(self, mixed_diff):
        result = recommend(mixed_diff)
        for rec in result.recommendations:
            assert rec.key in rec.suggestion

    def test_summary_counts(self, mixed_diff):
        result = recommend(mixed_diff)
        summary = result.summary()
        assert "error" in summary
        assert "warning" in summary

    def test_errors_property_filters(self, mixed_diff):
        result = recommend(mixed_diff)
        assert all(r.severity == "error" for r in result.errors)

    def test_warnings_property_filters(self, mixed_diff):
        result = recommend(mixed_diff)
        assert all(r.severity == "warning" for r in result.warnings)

    def test_infos_property_filters(self, mixed_diff):
        result = recommend(mixed_diff)
        assert all(r.severity == "info" for r in result.infos)

    def test_str_representation(self, mixed_diff):
        result = recommend(mixed_diff)
        for rec in result.recommendations:
            s = str(rec)
            assert rec.severity.upper() in s
            assert rec.key in s
