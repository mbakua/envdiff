"""Tests for envdiff.normalizer."""

from __future__ import annotations

import pytest

from envdiff.normalizer import NormalizeOptions, normalize_env, normalize_pair


@pytest.fixture()
def raw_env() -> dict:
    return {
        "  KEY_A  ": "  value1  ",
        "KEY_B": "",
        "Key_C": "hello",
    }


class TestNormalizeEnv:
    def test_strips_whitespace_by_default(self, raw_env):
        result = normalize_env(raw_env)
        assert result["KEY_A"] == "value1"

    def test_strips_key_whitespace(self, raw_env):
        result = normalize_env(raw_env)
        assert "KEY_A" in result
        assert "  KEY_A  " not in result

    def test_lowercase_keys(self, raw_env):
        opts = NormalizeOptions(lowercase_keys=True)
        result = normalize_env(raw_env, opts)
        assert "key_a" in result
        assert "key_b" in result
        assert "key_c" in result

    def test_uppercase_keys(self):
        env = {"db_host": "localhost", "db_port": "5432"}
        opts = NormalizeOptions(uppercase_keys=True)
        result = normalize_env(env, opts)
        assert "DB_HOST" in result
        assert "DB_PORT" in result

    def test_remove_empty_drops_blank_values(self, raw_env):
        opts = NormalizeOptions(remove_empty=True)
        result = normalize_env(raw_env, opts)
        assert "KEY_B" not in result

    def test_remove_empty_keeps_non_blank(self, raw_env):
        opts = NormalizeOptions(remove_empty=True)
        result = normalize_env(raw_env, opts)
        assert "Key_C" in result

    def test_default_value_fills_empty(self, raw_env):
        opts = NormalizeOptions(default_value="UNSET")
        result = normalize_env(raw_env, opts)
        assert result["KEY_B"] == "UNSET"

    def test_default_value_does_not_overwrite_non_empty(self, raw_env):
        opts = NormalizeOptions(default_value="UNSET")
        result = normalize_env(raw_env, opts)
        assert result["Key_C"] == "hello"

    def test_no_opts_returns_copy(self):
        env = {"A": "1", "B": "2"}
        result = normalize_env(env)
        assert result == {"A": "1", "B": "2"}
        assert result is not env

    def test_empty_env_returns_empty(self):
        assert normalize_env({}) == {}


class TestNormalizePair:
    def test_returns_two_dicts(self):
        left = {"A": " x "}
        right = {"B": " y "}
        l, r = normalize_pair(left, right)
        assert isinstance(l, dict)
        assert isinstance(r, dict)

    def test_both_sides_stripped(self):
        left = {"K": "  val  "}
        right = {"K": "  other  "}
        l, r = normalize_pair(left, right)
        assert l["K"] == "val"
        assert r["K"] == "other"

    def test_opts_applied_to_both_sides(self):
        left = {"db_host": "localhost"}
        right = {"db_port": "5432"}
        opts = NormalizeOptions(uppercase_keys=True)
        l, r = normalize_pair(left, right, opts)
        assert "DB_HOST" in l
        assert "DB_PORT" in r
