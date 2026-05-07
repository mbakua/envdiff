"""Tests for envdiff.summarizer."""

import pytest

from envdiff.differ import DiffResult
from envdiff.summarizer import SummaryReport, summarize_diff


@pytest.fixture()
def clean_diff() -> DiffResult:
    return DiffResult(
        only_in_left={},
        only_in_right={},
        value_mismatches={},
        matching={"APP_ENV": "production", "PORT": "8080"},
    )


@pytest.fixture()
def mixed_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"LEGACY_FLAG": "1"},
        only_in_right={"NEW_FEATURE": "enabled"},
        value_mismatches={"DB_HOST": ("localhost", "db.prod.internal")},
        matching={"APP_ENV": "production"},
    )


@pytest.fixture()
def secret_diff() -> DiffResult:
    return DiffResult(
        only_in_left={},
        only_in_right={},
        value_mismatches={"API_SECRET": ("hunter2", "s3cr3t")},
        matching={},
    )


class TestSummarizeReturnType:
    def test_returns_summary_report(self, clean_diff):
        result = summarize_diff(clean_diff)
        assert isinstance(result, SummaryReport)

    def test_total_keys_correct(self, mixed_diff):
        report = summarize_diff(mixed_diff, mask_secrets=False)
        assert report.total_keys == 4

    def test_matching_count(self, mixed_diff):
        report = summarize_diff(mixed_diff, mask_secrets=False)
        assert report.matching == 1

    def test_only_in_left_count(self, mixed_diff):
        report = summarize_diff(mixed_diff, mask_secrets=False)
        assert report.only_in_left == 1

    def test_only_in_right_count(self, mixed_diff):
        report = summarize_diff(mixed_diff, mask_secrets=False)
        assert report.only_in_right == 1

    def test_mismatches_count(self, mixed_diff):
        report = summarize_diff(mixed_diff, mask_secrets=False)
        assert report.mismatches == 1


class TestHasIssues:
    def test_clean_diff_has_no_issues(self, clean_diff):
        report = summarize_diff(clean_diff)
        assert report.has_issues is False

    def test_mixed_diff_has_issues(self, mixed_diff):
        report = summarize_diff(mixed_diff, mask_secrets=False)
        assert report.has_issues is True


class TestStringOutput:
    def test_str_contains_header(self, clean_diff):
        report = summarize_diff(clean_diff)
        assert "envdiff Summary" in str(report)

    def test_str_contains_totals(self, mixed_diff):
        text = str(summarize_diff(mixed_diff, mask_secrets=False))
        assert "Total keys" in text
        assert "Mismatches" in text

    def test_mismatch_key_in_output(self, mixed_diff):
        text = str(summarize_diff(mixed_diff, mask_secrets=False))
        assert "DB_HOST" in text

    def test_only_left_key_in_output(self, mixed_diff):
        text = str(summarize_diff(mixed_diff, mask_secrets=False))
        assert "LEGACY_FLAG" in text

    def test_clean_diff_shows_no_issues_message(self, clean_diff):
        text = str(summarize_diff(clean_diff))
        assert "No issues" in text


class TestMasking:
    def test_secret_value_masked_by_default(self, secret_diff):
        text = str(summarize_diff(secret_diff))
        assert "hunter2" not in text
        assert "s3cr3t" not in text

    def test_no_mask_shows_values(self, secret_diff):
        text = str(summarize_diff(secret_diff, mask_secrets=False))
        assert "hunter2" in text
