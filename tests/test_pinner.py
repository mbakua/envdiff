"""Tests for envdiff.pinner."""

import pytest

from envdiff.differ import DiffResult
from envdiff.pinner import PinReport, PinViolation, pin_diff


@pytest.fixture()
def base_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"REMOVED_KEY": "old_val"},
        only_in_right={"NEW_KEY": "new_val"},
        value_mismatches={"DB_HOST": ("localhost", "prod-db.example.com")},
        matching_keys={"APP_ENV": "production", "LOG_LEVEL": "info"},
    )


class TestPinReport:
    def test_is_clean_when_no_violations(self):
        report = PinReport(violations=[], checked=3)
        assert report.is_clean is True

    def test_is_not_clean_when_violations_present(self):
        v = PinViolation(key="X", pinned_value="a", actual_value="b", reason="value mismatch")
        report = PinReport(violations=[v], checked=1)
        assert report.is_clean is False

    def test_summary_clean(self):
        report = PinReport(violations=[], checked=5)
        assert "5" in report.summary()
        assert "match" in report.summary()

    def test_summary_with_violations(self):
        v = PinViolation(key="DB_HOST", pinned_value="localhost", actual_value="remote", reason="value mismatch")
        report = PinReport(violations=[v], checked=2)
        summary = report.summary()
        assert "1" in summary
        assert "DB_HOST" in summary


class TestPinViolationStr:
    def test_str_contains_key(self):
        v = PinViolation(key="SECRET", pinned_value="abc", actual_value=None, reason="key missing from right env")
        assert "SECRET" in str(v)

    def test_str_contains_reason(self):
        v = PinViolation(key="X", pinned_value="1", actual_value="2", reason="value mismatch")
        assert "value mismatch" in str(v)


class TestPinDiff:
    def test_returns_pin_report_type(self, base_diff):
        result = pin_diff(base_diff, {})
        assert isinstance(result, PinReport)

    def test_empty_pins_is_clean(self, base_diff):
        result = pin_diff(base_diff, {})
        assert result.is_clean
        assert result.checked == 0

    def test_matching_key_correct_value_passes(self, base_diff):
        result = pin_diff(base_diff, {"APP_ENV": "production"})
        assert result.is_clean
        assert result.checked == 1

    def test_matching_key_wrong_value_fails(self, base_diff):
        result = pin_diff(base_diff, {"APP_ENV": "staging"})
        assert not result.is_clean
        assert result.violations[0].key == "APP_ENV"
        assert result.violations[0].reason == "value mismatch"

    def test_missing_from_right_flagged(self, base_diff):
        result = pin_diff(base_diff, {"REMOVED_KEY": "old_val"})
        assert not result.is_clean
        assert result.violations[0].key == "REMOVED_KEY"
        assert "missing" in result.violations[0].reason

    def test_mismatch_key_correct_pinned_right_value_passes(self, base_diff):
        # DB_HOST mismatch: left=localhost, right=prod-db.example.com
        result = pin_diff(base_diff, {"DB_HOST": "prod-db.example.com"})
        assert result.is_clean

    def test_mismatch_key_wrong_pin_fails(self, base_diff):
        result = pin_diff(base_diff, {"DB_HOST": "localhost"})
        assert not result.is_clean
        assert result.violations[0].key == "DB_HOST"

    def test_unknown_key_flagged(self, base_diff):
        result = pin_diff(base_diff, {"GHOST_KEY": "value"})
        assert not result.is_clean
        assert result.violations[0].key == "GHOST_KEY"
        assert "not found" in result.violations[0].reason

    def test_checked_count_matches_pins(self, base_diff):
        pins = {"APP_ENV": "production", "LOG_LEVEL": "info", "DB_HOST": "prod-db.example.com"}
        result = pin_diff(base_diff, pins)
        assert result.checked == 3

    def test_only_in_right_key_correct_value_passes(self, base_diff):
        result = pin_diff(base_diff, {"NEW_KEY": "new_val"})
        assert result.is_clean

    def test_only_in_right_key_wrong_value_fails(self, base_diff):
        result = pin_diff(base_diff, {"NEW_KEY": "wrong_val"})
        assert not result.is_clean
