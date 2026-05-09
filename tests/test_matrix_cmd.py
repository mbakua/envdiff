"""Tests for envdiff.matrix_cmd."""
import json
import os
import pytest
from unittest.mock import patch
from envdiff.matrix_cmd import build_matrix_parser, run_matrix


@pytest.fixture
def env_file(tmp_path):
    def _write(name, content):
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


@pytest.fixture
def dev_file(env_file):
    return env_file("dev.env", "A=1\nB=2\nC=3\n")


@pytest.fixture
def prod_file(env_file):
    return env_file("prod.env", "A=1\nB=99\nD=4\n")


@pytest.fixture
def staging_file(env_file):
    return env_file("staging.env", "A=1\nB=2\nC=3\n")


class TestBuildMatrixParser:
    def test_returns_parser(self):
        p = build_matrix_parser()
        import argparse
        assert isinstance(p, argparse.ArgumentParser)

    def test_default_format_is_text(self, dev_file, prod_file):
        p = build_matrix_parser()
        args = p.parse_args([f"dev={dev_file}", f"prod={prod_file}"])
        assert args.format == "text"

    def test_json_format_flag(self, dev_file, prod_file):
        p = build_matrix_parser()
        args = p.parse_args([f"dev={dev_file}", f"prod={prod_file}", "--format", "json"])
        assert args.format == "json"

    def test_only_diff_flag(self, dev_file, prod_file):
        p = build_matrix_parser()
        args = p.parse_args([f"dev={dev_file}", f"prod={prod_file}", "--only-diff"])
        assert args.only_diff is True


class TestRunMatrix:
    def test_returns_zero_on_success(self, dev_file, prod_file, capsys):
        p = build_matrix_parser()
        args = p.parse_args([f"dev={dev_file}", f"prod={prod_file}"])
        code = run_matrix(args)
        assert code == 0

    def test_returns_one_when_too_few_envs(self, dev_file, capsys):
        p = build_matrix_parser()
        args = p.parse_args([f"dev={dev_file}"])
        code = run_matrix(args)
        assert code == 1

    def test_text_output_contains_labels(self, dev_file, prod_file, capsys):
        p = build_matrix_parser()
        args = p.parse_args([f"dev={dev_file}", f"prod={prod_file}"])
        run_matrix(args)
        out = capsys.readouterr().out
        assert "dev" in out
        assert "prod" in out

    def test_json_output_is_valid(self, dev_file, prod_file, capsys):
        p = build_matrix_parser()
        args = p.parse_args([f"dev={dev_file}", f"prod={prod_file}", "--format", "json"])
        run_matrix(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_only_diff_hides_clean_pairs(self, dev_file, staging_file, prod_file, capsys):
        p = build_matrix_parser()
        args = p.parse_args([
            f"dev={dev_file}", f"staging={staging_file}", f"prod={prod_file}",
            "--only-diff",
        ])
        run_matrix(args)
        out = capsys.readouterr().out
        # dev vs staging and dev vs prod are identical; staging vs prod also identical
        assert "OK" not in out
