"""Tests for envdiff.masker."""

import pytest

from envdiff.differ import DiffResult
from envdiff.masker import MASK, _is_sensitive, mask_diff, mask_value


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def base_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"DB_PASSWORD": "secret123", "APP_NAME": "myapp"},
        only_in_right={"API_KEY": "key-abc", "PORT": "8080"},
        value_mismatches={
            "AUTH_TOKEN": ("tok-old", "tok-new"),
            "LOG_LEVEL": ("DEBUG", "INFO"),
        },
        matching_keys=frozenset({"REGION"}),
    )


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

class TestIsSensitive:
    def test_password_key(self):
        assert _is_sensitive("DB_PASSWORD") is True

    def test_secret_key(self):
        assert _is_sensitive("APP_SECRET") is True

    def test_token_key(self):
        assert _is_sensitive("AUTH_TOKEN") is True

    def test_api_key(self):
        assert _is_sensitive("API_KEY") is True

    def test_non_sensitive_key(self):
        assert _is_sensitive("LOG_LEVEL") is False

    def test_case_insensitive(self):
        assert _is_sensitive("db_Password") is True


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

class TestMaskValue:
    def test_sensitive_value_is_masked(self):
        assert mask_value("DB_PASSWORD", "hunter2") == MASK

    def test_non_sensitive_value_unchanged(self):
        assert mask_value("APP_NAME", "myapp") == "myapp"

    def test_none_value_stays_none(self):
        assert mask_value("DB_PASSWORD", None) is None


# ---------------------------------------------------------------------------
# mask_diff
# ---------------------------------------------------------------------------

class TestMaskDiff:
    def test_returns_diff_result_type(self, base_diff):
        result = mask_diff(base_diff)
        assert isinstance(result, DiffResult)

    def test_sensitive_only_in_left_masked(self, base_diff):
        result = mask_diff(base_diff)
        assert result.only_in_left["DB_PASSWORD"] == MASK

    def test_non_sensitive_only_in_left_unchanged(self, base_diff):
        result = mask_diff(base_diff)
        assert result.only_in_left["APP_NAME"] == "myapp"

    def test_sensitive_only_in_right_masked(self, base_diff):
        result = mask_diff(base_diff)
        assert result.only_in_right["API_KEY"] == MASK

    def test_non_sensitive_only_in_right_unchanged(self, base_diff):
        result = mask_diff(base_diff)
        assert result.only_in_right["PORT"] == "8080"

    def test_sensitive_mismatch_both_sides_masked(self, base_diff):
        result = mask_diff(base_diff)
        lv, rv = result.value_mismatches["AUTH_TOKEN"]
        assert lv == MASK
        assert rv == MASK

    def test_non_sensitive_mismatch_unchanged(self, base_diff):
        result = mask_diff(base_diff)
        lv, rv = result.value_mismatches["LOG_LEVEL"]
        assert lv == "DEBUG"
        assert rv == "INFO"

    def test_matching_keys_preserved(self, base_diff):
        result = mask_diff(base_diff)
        assert result.matching_keys == base_diff.matching_keys

    def test_extra_keys_are_masked(self, base_diff):
        result = mask_diff(base_diff, extra_keys=frozenset({"APP_NAME"}))
        assert result.only_in_left["APP_NAME"] == MASK

    def test_original_diff_not_mutated(self, base_diff):
        mask_diff(base_diff)
        assert base_diff.only_in_left["DB_PASSWORD"] == "secret123"
