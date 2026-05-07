"""Tests for envdiff.tagger."""

import pytest
from envdiff.differ import DiffResult
from envdiff.tagger import tag_diff, TaggedDiff, _tags_for_key


@pytest.fixture
def mixed_diff():
    return DiffResult(
        only_in_left=["DB_PASSWORD", "AWS_SECRET_ACCESS_KEY"],
        only_in_right=["REDIS_HOST", "FEATURE_FLAG_DARK_MODE"],
        value_mismatches={"LOG_LEVEL": ("INFO", "DEBUG"), "DB_HOST": ("localhost", "prod-db")},
        matching_keys=["APP_NAME"],
    )


class TestTagsForKey:
    def test_password_gets_secret_tag(self):
        assert "secret" in _tags_for_key("DB_PASSWORD")

    def test_token_gets_secret_tag(self):
        assert "secret" in _tags_for_key("AUTH_TOKEN")

    def test_host_gets_network_tag(self):
        assert "network" in _tags_for_key("REDIS_HOST")

    def test_log_level_gets_logging_tag(self):
        assert "logging" in _tags_for_key("LOG_LEVEL")

    def test_feature_flag_gets_feature_tag(self):
        assert "feature" in _tags_for_key("FEATURE_FLAG_DARK_MODE")

    def test_aws_key_gets_aws_tag(self):
        assert "aws" in _tags_for_key("AWS_SECRET_ACCESS_KEY")

    def test_unrecognized_key_returns_empty(self):
        assert _tags_for_key("APP_NAME") == []

    def test_extra_tags_applied(self):
        tags = _tags_for_key("PAYMENT_GATEWAY", extra_tags={"billing": ["payment"]})
        assert "billing" in tags

    def test_extra_tags_case_insensitive(self):
        tags = _tags_for_key("PAYMENT_GATEWAY", extra_tags={"billing": ["PAYMENT"]})
        assert "billing" in tags


class TestTagDiff:
    def test_returns_tagged_diff_type(self, mixed_diff):
        result = tag_diff(mixed_diff)
        assert isinstance(result, TaggedDiff)

    def test_secret_tag_contains_password_key(self, mixed_diff):
        result = tag_diff(mixed_diff)
        assert "DB_PASSWORD" in result.keys_for_tag("secret")

    def test_aws_tag_contains_aws_key(self, mixed_diff):
        result = tag_diff(mixed_diff)
        assert "AWS_SECRET_ACCESS_KEY" in result.keys_for_tag("aws")

    def test_network_tag_contains_host_keys(self, mixed_diff):
        result = tag_diff(mixed_diff)
        assert "REDIS_HOST" in result.keys_for_tag("network")
        assert "DB_HOST" in result.keys_for_tag("network")

    def test_logging_tag_contains_log_level(self, mixed_diff):
        result = tag_diff(mixed_diff)
        assert "LOG_LEVEL" in result.keys_for_tag("logging")

    def test_feature_tag_contains_feature_flag(self, mixed_diff):
        result = tag_diff(mixed_diff)
        assert "FEATURE_FLAG_DARK_MODE" in result.keys_for_tag("feature")

    def test_untagged_key_has_empty_tags(self, mixed_diff):
        result = tag_diff(mixed_diff)
        assert result.tags_for_key("APP_NAME") == []

    def test_all_tags_returns_sorted_list(self, mixed_diff):
        result = tag_diff(mixed_diff)
        tags = result.all_tags()
        assert tags == sorted(tags)

    def test_unknown_tag_returns_empty_set(self, mixed_diff):
        result = tag_diff(mixed_diff)
        assert result.keys_for_tag("nonexistent") == set()

    def test_extra_tags_integrated(self, mixed_diff):
        result = tag_diff(mixed_diff, extra_tags={"app": ["APP_"]})
        assert "APP_NAME" in result.keys_for_tag("app")

    def test_key_can_have_multiple_tags(self, mixed_diff):
        # AWS_SECRET_ACCESS_KEY matches both 'aws' and 'secret'
        result = tag_diff(mixed_diff)
        key_tags = result.tags_for_key("AWS_SECRET_ACCESS_KEY")
        assert "aws" in key_tags
        assert "secret" in key_tags
