"""Tests for envdiff.differ_report."""

import pytest

from envdiff.differ import DiffResult
from envdiff.differ_report import ConsolidatedReport, build_report


@pytest.fixture
def clean_diff():
    return DiffResult(
        only_in_left={},
        only_in_right={},
        value_mismatches={},
        matching_keys={"APP_ENV": "production", "LOG_LEVEL": "info"},
    )


@pytest.fixture
def mixed_diff():
    return DiffResult(
        only_in_left={"OLD_KEY": "legacy"},
        only_in_right={"NEW_KEY": "fresh"},
        value_mismatches={"DB_PASSWORD": ("secret1", "secret2")},
        matching_keys={"APP_ENV": "production"},
    )


class TestBuildReport:
    def test_returns_consolidated_report_type(self, clean_diff):
        result = build_report(clean_diff)
        assert isinstance(result, ConsolidatedReport)

    def test_labels_default_to_left_right(self, clean_diff):
        result = build_report(clean_diff)
        assert result.label_left == "left"
        assert result.label_right == "right"

    def test_custom_labels_stored(self, clean_diff):
        result = build_report(clean_diff, label_left="dev", label_right="prod")
        assert result.label_left == "dev"
        assert result.label_right == "prod"

    def test_clean_diff_has_no_issues(self, clean_diff):
        result = build_report(clean_diff)
        assert not result.has_issues

    def test_mixed_diff_has_issues(self, mixed_diff):
        result = build_report(mixed_diff)
        assert result.has_issues

    def test_clean_diff_is_healthy(self, clean_diff):
        result = build_report(clean_diff)
        assert result.is_healthy

    def test_mixed_diff_is_not_healthy(self, mixed_diff):
        result = build_report(mixed_diff)
        assert not result.is_healthy


class TestConsolidatedReportSummary:
    def test_summary_contains_grade(self, clean_diff):
        report = build_report(clean_diff)
        assert "Grade" in report.summary()

    def test_summary_contains_labels(self, clean_diff):
        report = build_report(clean_diff, label_left="dev", label_right="prod")
        assert "dev" in report.summary()
        assert "prod" in report.summary()

    def test_summary_contains_match_rate(self, clean_diff):
        report = build_report(clean_diff)
        assert "Match" in report.summary()

    def test_summary_contains_total_keys(self, mixed_diff):
        report = build_report(mixed_diff)
        assert "Total" in report.summary()


class TestConsolidatedReportToDict:
    def test_to_dict_returns_dict(self, clean_diff):
        report = build_report(clean_diff)
        assert isinstance(report.to_dict(), dict)

    def test_to_dict_has_stats_key(self, clean_diff):
        d = build_report(clean_diff).to_dict()
        assert "stats" in d

    def test_to_dict_has_score_key(self, clean_diff):
        d = build_report(clean_diff).to_dict()
        assert "score" in d

    def test_to_dict_has_recommendations_key(self, mixed_diff):
        d = build_report(mixed_diff).to_dict()
        assert "recommendations" in d

    def test_to_dict_healthy_flag_true_for_clean(self, clean_diff):
        d = build_report(clean_diff).to_dict()
        assert d["healthy"] is True

    def test_to_dict_healthy_flag_false_for_mixed(self, mixed_diff):
        d = build_report(mixed_diff).to_dict()
        assert d["healthy"] is False

    def test_to_dict_labels_present(self, clean_diff):
        d = build_report(clean_diff, label_left="staging", label_right="prod").to_dict()
        assert d["labels"]["left"] == "staging"
        assert d["labels"]["right"] == "prod"
