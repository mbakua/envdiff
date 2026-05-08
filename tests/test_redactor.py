"""Tests for envdiff.redactor."""

import pytest

from envdiff.differ import DiffResult
from envdiff.redactor import (
    DEFAULT_PLACEHOLDER,
    RedactedDiff,
    is_sensitive,
    redact_diff,
)


@pytest.fixture()
def base_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"DB_PASSWORD": "s3cr3t", "HOST": "localhost"},
        only_in_right={"API_TOKEN": "tok-abc", "PORT": "5432"},
        mismatches={"SECRET_KEY": ("old", "new"), "LOG_LEVEL": ("debug", "info")},
        matching={"APP_NAME": "myapp", "AUTH_USER": "admin"},
    )


class TestIsSensitive:
    def test_password_key(self):
        assert is_sensitive("DB_PASSWORD") is True

    def test_secret_key(self):
        assert is_sensitive("SECRET_KEY") is True

    def test_token_key(self):
        assert is_sensitive("API_TOKEN") is True

    def test_auth_key(self):
        assert is_sensitive("AUTH_USER") is True

    def test_api_key_variant(self):
        assert is_sensitive("STRIPE_API_KEY") is True

    def test_plain_key_not_sensitive(self):
        assert is_sensitive("LOG_LEVEL") is False

    def test_host_not_sensitive(self):
        assert is_sensitive("HOST") is False


class TestRedactDiff:
    def test_returns_redacted_diff_type(self, base_diff):
        result = redact_diff(base_diff)
        assert isinstance(result, RedactedDiff)

    def test_sensitive_value_in_only_in_left_is_redacted(self, base_diff):
        result = redact_diff(base_diff)
        assert result.only_in_left["DB_PASSWORD"] == DEFAULT_PLACEHOLDER

    def test_non_sensitive_value_in_only_in_left_preserved(self, base_diff):
        result = redact_diff(base_diff)
        assert result.only_in_left["HOST"] == "localhost"

    def test_sensitive_value_in_only_in_right_is_redacted(self, base_diff):
        result = redact_diff(base_diff)
        assert result.only_in_right["API_TOKEN"] == DEFAULT_PLACEHOLDER

    def test_non_sensitive_value_in_only_in_right_preserved(self, base_diff):
        result = redact_diff(base_diff)
        assert result.only_in_right["PORT"] == "5432"

    def test_sensitive_mismatch_both_sides_redacted(self, base_diff):
        result = redact_diff(base_diff)
        lv, rv = result.mismatches["SECRET_KEY"]
        assert lv == DEFAULT_PLACEHOLDER
        assert rv == DEFAULT_PLACEHOLDER

    def test_non_sensitive_mismatch_preserved(self, base_diff):
        result = redact_diff(base_diff)
        assert result.mismatches["LOG_LEVEL"] == ("debug", "info")

    def test_sensitive_matching_key_is_redacted(self, base_diff):
        result = redact_diff(base_diff)
        assert result.matching["AUTH_USER"] == DEFAULT_PLACEHOLDER

    def test_non_sensitive_matching_key_preserved(self, base_diff):
        result = redact_diff(base_diff)
        assert result.matching["APP_NAME"] == "myapp"

    def test_redacted_keys_list_populated(self, base_diff):
        result = redact_diff(base_diff)
        assert "DB_PASSWORD" in result.redacted_keys
        assert "SECRET_KEY" in result.redacted_keys
        assert "API_TOKEN" in result.redacted_keys

    def test_non_sensitive_keys_not_in_redacted_list(self, base_diff):
        result = redact_diff(base_diff)
        assert "HOST" not in result.redacted_keys
        assert "LOG_LEVEL" not in result.redacted_keys

    def test_custom_placeholder(self, base_diff):
        result = redact_diff(base_diff, placeholder="***")
        assert result.only_in_left["DB_PASSWORD"] == "***"

    def test_extra_keys_treated_as_sensitive(self, base_diff):
        result = redact_diff(base_diff, extra_keys=["HOST"])
        assert result.only_in_left["HOST"] == DEFAULT_PLACEHOLDER
        assert "HOST" in result.redacted_keys

    def test_redacted_keys_sorted(self, base_diff):
        result = redact_diff(base_diff)
        assert result.redacted_keys == sorted(result.redacted_keys)
