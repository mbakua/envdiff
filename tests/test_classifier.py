"""Tests for envdiff.classifier."""

import pytest
from envdiff.differ import DiffResult
from envdiff.classifier import classify_diff, ClassifiedDiff, _categorize_key


@pytest.fixture
def mixed_diff():
    return DiffResult(
        only_in_left={"DB_HOST": "localhost", "SECRET_KEY": "abc"},
        only_in_right={"LOG_LEVEL": "debug"},
        mismatches={"API_TOKEN": ("tok1", "tok2"), "AWS_REGION": ("us-east-1", "eu-west-1")},
        matching={"APP_NAME": "envdiff", "POSTGRES_DSN": "postgres://..."},
    )


class TestCategorizeKey:
    def test_password_is_security(self):
        assert _categorize_key("DB_PASSWORD") == "security"

    def test_token_is_security(self):
        assert _categorize_key("API_TOKEN") == "security"

    def test_host_is_network(self):
        assert _categorize_key("DB_HOST") == "network"

    def test_log_level_is_logging(self):
        assert _categorize_key("LOG_LEVEL") == "logging"

    def test_aws_is_infrastructure(self):
        assert _categorize_key("AWS_REGION") == "infrastructure"

    def test_dsn_is_database(self):
        assert _categorize_key("POSTGRES_DSN") == "database"

    def test_unknown_is_application(self):
        assert _categorize_key("APP_NAME") == "application"


class TestClassifyDiff:
    def test_returns_classified_diff_type(self, mixed_diff):
        result = classify_diff(mixed_diff)
        assert isinstance(result, ClassifiedDiff)

    def test_security_keys_present(self, mixed_diff):
        result = classify_diff(mixed_diff)
        assert "SECRET_KEY" in result.keys_in("security")
        assert "API_TOKEN" in result.keys_in("security")

    def test_logging_keys_present(self, mixed_diff):
        result = classify_diff(mixed_diff)
        assert "LOG_LEVEL" in result.keys_in("logging")

    def test_infrastructure_keys_present(self, mixed_diff):
        result = classify_diff(mixed_diff)
        assert "AWS_REGION" in result.keys_in("infrastructure")

    def test_database_keys_present(self, mixed_diff):
        result = classify_diff(mixed_diff)
        assert "POSTGRES_DSN" in result.keys_in("database")

    def test_application_fallback(self, mixed_diff):
        result = classify_diff(mixed_diff)
        assert "APP_NAME" in result.keys_in("application")

    def test_key_to_category_mapping(self, mixed_diff):
        result = classify_diff(mixed_diff)
        assert result.key_to_category["LOG_LEVEL"] == "logging"
        assert result.key_to_category["AWS_REGION"] == "infrastructure"

    def test_all_categories_excludes_empty(self, mixed_diff):
        result = classify_diff(mixed_diff)
        active = result.all_categories()
        for cat in active:
            assert len(result.keys_in(cat)) > 0

    def test_empty_diff_returns_empty_categories(self):
        diff = DiffResult({}, {}, {}, {})
        result = classify_diff(diff)
        assert result.all_categories() == []
