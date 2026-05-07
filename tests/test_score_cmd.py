"""Tests for envdiff.score_cmd."""

import json
import os
import pytest

from envdiff.score_cmd import build_score_parser, run_score
import argparse


@pytest.fixture()
def env_file(tmp_path):
    def _write(name: str, content: str):
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


@pytest.fixture()
def base_args(env_file):
    left = env_file("left.env", "DB_HOST=prod\nPORT=5432\nSECRET=abc\n")
    right = env_file("right.env", "DB_HOST=staging\nPORT=5432\nEXTRA=yes\n")
    parser = argparse.ArgumentParser()
    build_score_parser(parser)
    return parser.parse_args([left, right])


class TestBuildScoreParser:
    def test_returns_parser(self):
        p = argparse.ArgumentParser()
        result = build_score_parser(p)
        assert result is p

    def test_default_format_is_text(self, base_args):
        assert base_args.format == "text"

    def test_default_fail_under_is_zero(self, base_args):
        assert base_args.fail_under == 0


class TestRunScore:
    def test_returns_zero_on_success(self, base_args, capsys):
        code = run_score(base_args)
        assert code == 0

    def test_text_output_contains_score(self, base_args, capsys):
        run_score(base_args)
        out = capsys.readouterr().out
        assert "Score:" in out

    def test_json_output_is_valid(self, env_file, capsys):
        left = env_file("l.env", "A=1\nB=2\n")
        right = env_file("r.env", "A=1\nB=2\n")
        parser = argparse.ArgumentParser()
        build_score_parser(parser)
        args = parser.parse_args([left, right, "--format", "json"])
        run_score(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "score" in data
        assert "grade" in data

    def test_fail_under_triggers_exit_code_1(self, env_file):
        left = env_file("fl.env", "A=1\nMISSING=x\n")
        right = env_file("fr.env", "A=1\n")
        parser = argparse.ArgumentParser()
        build_score_parser(parser)
        args = parser.parse_args([left, right, "--fail-under", "99"])
        code = run_score(args)
        assert code == 1

    def test_invalid_weights_json_returns_2(self, base_args, capsys):
        base_args.weights = "{not valid json"
        code = run_score(base_args)
        assert code == 2

    def test_custom_weights_accepted(self, base_args, capsys):
        base_args.weights = '{"missing": 1, "extra": 1, "mismatch": 1}'
        code = run_score(base_args)
        assert code == 0
