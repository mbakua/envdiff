"""Tests for envdiff.normalize_cmd."""

from __future__ import annotations

import json
import os
import pytest

from envdiff.normalize_cmd import build_normalize_parser, run_normalize


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PASS=  secret  \nEMPTY=\n")
    return str(p)


class TestBuildNormalizeParser:
    def test_returns_parser(self):
        p = build_normalize_parser()
        assert p is not None

    def test_default_format_is_dotenv(self):
        p = build_normalize_parser()
        args = p.parse_args(["some.env"])
        assert args.format == "dotenv"

    def test_json_format_flag(self):
        p = build_normalize_parser()
        args = p.parse_args(["some.env", "--format", "json"])
        assert args.format == "json"

    def test_lowercase_keys_flag(self):
        p = build_normalize_parser()
        args = p.parse_args(["some.env", "--lowercase-keys"])
        assert args.lowercase_keys is True

    def test_uppercase_keys_flag(self):
        p = build_normalize_parser()
        args = p.parse_args(["some.env", "--uppercase-keys"])
        assert args.uppercase_keys is True

    def test_remove_empty_flag(self):
        p = build_normalize_parser()
        args = p.parse_args(["some.env", "--remove-empty"])
        assert args.remove_empty is True

    def test_default_value_flag(self):
        p = build_normalize_parser()
        args = p.parse_args(["some.env", "--default-value", "UNSET"])
        assert args.default_value == "UNSET"


class TestRunNormalize:
    def test_missing_file_returns_1(self, tmp_path):
        p = build_normalize_parser()
        args = p.parse_args([str(tmp_path / "missing.env")])
        assert run_normalize(args) == 1

    def test_valid_file_returns_0(self, env_file):
        p = build_normalize_parser()
        args = p.parse_args([env_file])
        assert run_normalize(args) == 0

    def test_dotenv_output(self, env_file, capsys):
        p = build_normalize_parser()
        args = p.parse_args([env_file])
        run_normalize(args)
        out = capsys.readouterr().out
        assert "DB_HOST=localhost" in out

    def test_strips_value_whitespace(self, env_file, capsys):
        p = build_normalize_parser()
        args = p.parse_args([env_file])
        run_normalize(args)
        out = capsys.readouterr().out
        assert "DB_PASS=secret" in out

    def test_json_output_is_valid(self, env_file, capsys):
        p = build_normalize_parser()
        args = p.parse_args([env_file, "--format", "json"])
        run_normalize(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "DB_HOST" in data

    def test_remove_empty_excludes_blank_key(self, env_file, capsys):
        p = build_normalize_parser()
        args = p.parse_args([env_file, "--remove-empty"])
        run_normalize(args)
        out = capsys.readouterr().out
        assert "EMPTY" not in out

    def test_uppercase_keys_in_output(self, tmp_path, capsys):
        f = tmp_path / ".env"
        f.write_text("db_host=localhost\n")
        p = build_normalize_parser()
        args = p.parse_args([str(f), "--uppercase-keys"])
        run_normalize(args)
        out = capsys.readouterr().out
        assert "DB_HOST=localhost" in out
