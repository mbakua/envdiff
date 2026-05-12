"""Tests for envdiff.aliaser and envdiff.alias_cmd."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envdiff.aliaser import AliasMap, apply_aliases, load_alias_map
from envdiff.differ import DiffResult, diff_envs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def base_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"DB_PASSWORD": "secret"},
        only_in_right={"API_TOKEN": "tok123"},
        value_mismatches={"LOG_LEVEL": ("debug", "info")},
        matching_keys=["APP_NAME"],
    )


@pytest.fixture()
def alias_map() -> AliasMap:
    return load_alias_map(
        {
            "DB_PASSWORD": "database-password",
            "API_TOKEN": "api-token",
            "LOG_LEVEL": "log-level",
            "APP_NAME": "app-name",
        }
    )


# ---------------------------------------------------------------------------
# AliasMap unit tests
# ---------------------------------------------------------------------------

class TestAliasMap:
    def test_alias_for_known_key(self, alias_map):
        assert alias_map.alias_for("DB_PASSWORD") == "database-password"

    def test_alias_for_unknown_key_returns_none(self, alias_map):
        assert alias_map.alias_for("UNKNOWN_KEY") is None

    def test_key_for_known_alias(self, alias_map):
        assert alias_map.key_for("api-token") == "API_TOKEN"

    def test_key_for_unknown_alias_returns_none(self, alias_map):
        assert alias_map.key_for("nope") is None

    def test_all_keys_returns_registered_keys(self, alias_map):
        assert "DB_PASSWORD" in alias_map.all_keys()

    def test_all_aliases_returns_registered_aliases(self, alias_map):
        assert "log-level" in alias_map.all_aliases()


# ---------------------------------------------------------------------------
# apply_aliases tests
# ---------------------------------------------------------------------------

class TestApplyAliases:
    def test_only_in_left_key_renamed(self, base_diff, alias_map):
        result = apply_aliases(base_diff, alias_map)
        assert "database-password" in result.only_in_left
        assert "DB_PASSWORD" not in result.only_in_left

    def test_only_in_right_key_renamed(self, base_diff, alias_map):
        result = apply_aliases(base_diff, alias_map)
        assert "api-token" in result.only_in_right

    def test_value_mismatch_key_renamed(self, base_diff, alias_map):
        result = apply_aliases(base_diff, alias_map)
        assert "log-level" in result.value_mismatches
        assert "LOG_LEVEL" not in result.value_mismatches

    def test_matching_keys_renamed(self, base_diff, alias_map):
        result = apply_aliases(base_diff, alias_map)
        assert "app-name" in result.matching_keys

    def test_unmapped_key_preserved(self, alias_map):
        diff = DiffResult(
            only_in_left={"UNMAPPED_KEY": "val"},
            only_in_right={},
            value_mismatches={},
            matching_keys=[],
        )
        result = apply_aliases(diff, alias_map)
        assert "UNMAPPED_KEY" in result.only_in_left

    def test_returns_diff_result_type(self, base_diff, alias_map):
        result = apply_aliases(base_diff, alias_map)
        assert isinstance(result, DiffResult)


# ---------------------------------------------------------------------------
# alias_cmd integration test
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        return p
    return _write


def test_alias_cmd_runs_without_alias_file(env_file, capsys):
    from envdiff.alias_cmd import build_alias_parser, run_alias

    left = env_file("left.env", "APP=hello\n")
    right = env_file("right.env", "APP=world\n")
    parser = build_alias_parser()
    args = parser.parse_args([str(left), str(right), "--no-color"])
    rc = run_alias(args)
    assert rc == 0


def test_alias_cmd_applies_alias_file(env_file, tmp_path, capsys):
    from envdiff.alias_cmd import build_alias_parser, run_alias

    left = env_file("left.env", "DB_PASSWORD=secret\n")
    right = env_file("right.env", "DB_PASSWORD=other\n")
    alias_file = tmp_path / "aliases.json"
    alias_file.write_text(json.dumps({"DB_PASSWORD": "database-password"}))

    parser = build_alias_parser()
    args = parser.parse_args([str(left), str(right), "--alias-file", str(alias_file), "--no-color"])
    rc = run_alias(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "database-password" in out


def test_alias_cmd_bad_alias_file_returns_exit_2(env_file, tmp_path):
    from envdiff.alias_cmd import build_alias_parser, run_alias

    left = env_file("left.env", "A=1\n")
    right = env_file("right.env", "A=2\n")
    bad = tmp_path / "bad.json"
    bad.write_text("[1,2,3]")

    parser = build_alias_parser()
    args = parser.parse_args([str(left), str(right), "--alias-file", str(bad)])
    rc = run_alias(args)
    assert rc == 2
