"""Tests for envdiff.validator."""

from __future__ import annotations

import os
import textwrap

import pytest

from envdiff.validator import (
    ValidationResult,
    load_schema,
    validate_required,
)


@pytest.fixture()
def schema() -> frozenset:
    return frozenset({"DATABASE_URL", "SECRET_KEY", "DEBUG"})


@pytest.fixture()
def complete_env() -> dict:
    return {"DATABASE_URL": "postgres://", "SECRET_KEY": "abc", "DEBUG": "1"}


class TestValidateRequired:
    def test_valid_env_returns_is_valid_true(self, complete_env, schema):
        result = validate_required(complete_env, schema)
        assert result.is_valid is True

    def test_missing_keys_detected(self, schema):
        env = {"DATABASE_URL": "postgres://"}
        result = validate_required(env, schema)
        assert "SECRET_KEY" in result.missing_keys
        assert "DEBUG" in result.missing_keys
        assert result.is_valid is False

    def test_extra_keys_ignored_by_default(self, complete_env, schema):
        env = {**complete_env, "EXTRA_VAR": "x"}
        result = validate_required(env, schema)
        assert result.is_valid is True
        assert result.extra_keys == frozenset()

    def test_strict_mode_flags_extra_keys(self, complete_env, schema):
        env = {**complete_env, "EXTRA_VAR": "x"}
        result = validate_required(env, schema, strict=True)
        assert "EXTRA_VAR" in result.extra_keys
        assert result.is_valid is False

    def test_empty_env_all_required_missing(self, schema):
        result = validate_required({}, schema)
        assert result.missing_keys == schema

    def test_empty_required_always_valid(self, complete_env):
        result = validate_required(complete_env, frozenset())
        assert result.is_valid is True


class TestValidationResultSummary:
    def test_ok_when_valid(self, complete_env, schema):
        result = validate_required(complete_env, schema)
        assert result.summary == "OK"

    def test_summary_shows_missing_count(self, schema):
        result = validate_required({}, schema)
        assert "missing=3" in result.summary

    def test_summary_shows_extra_count(self, complete_env, schema):
        env = {**complete_env, "A": "1", "B": "2"}
        result = validate_required(env, schema, strict=True)
        assert "extra=2" in result.summary


class TestLoadSchema:
    def test_loads_keys_from_file(self, tmp_path):
        schema_file = tmp_path / "schema.txt"
        schema_file.write_text("DATABASE_URL\nSECRET_KEY\nDEBUG\n")
        result = load_schema(str(schema_file))
        assert result == frozenset({"DATABASE_URL", "SECRET_KEY", "DEBUG"})

    def test_skips_comments_and_blank_lines(self, tmp_path):
        schema_file = tmp_path / "schema.txt"
        schema_file.write_text(
            textwrap.dedent("""\
            # required keys
            DATABASE_URL

            SECRET_KEY
            """)
        )
        result = load_schema(str(schema_file))
        assert result == frozenset({"DATABASE_URL", "SECRET_KEY"})

    def test_returns_frozenset(self, tmp_path):
        schema_file = tmp_path / "schema.txt"
        schema_file.write_text("KEY_A\n")
        assert isinstance(load_schema(str(schema_file)), frozenset)
