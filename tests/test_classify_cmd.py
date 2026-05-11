"""Tests for envdiff.classify_cmd."""

import json
import pytest
from unittest.mock import patch
from envdiff.classify_cmd import build_classify_parser, run_classify


@pytest.fixture
def env_file(tmp_path):
    def _write(name, content):
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


@pytest.fixture
def left_file(env_file):
    return env_file("left.env", "DB_HOST=localhost\nSECRET_KEY=abc\nAPP_NAME=myapp\n")


@pytest.fixture
def right_file(env_file):
    return env_file("right.env", "DB_HOST=prod-db\nLOG_LEVEL=debug\nAPP_NAME=myapp\n")


class TestBuildClassifyParser:
    def test_returns_parser(self):
        p = build_classify_parser()
        assert p is not None

    def test_default_format_is_text(self, left_file, right_file):
        p = build_classify_parser()
        args = p.parse_args([left_file, right_file])
        assert args.format == "text"

    def test_json_format_flag(self, left_file, right_file):
        p = build_classify_parser()
        args = p.parse_args([left_file, right_file, "--format", "json"])
        assert args.format == "json"

    def test_category_filter_flag(self, left_file, right_file):
        p = build_classify_parser()
        args = p.parse_args([left_file, right_file, "--category", "security"])
        assert args.category == "security"


class TestRunClassify:
    def test_text_output_contains_category_header(self, left_file, right_file, capsys):
        p = build_classify_parser()
        args = p.parse_args([left_file, right_file])
        run_classify(args)
        out = capsys.readouterr().out
        assert "[" in out

    def test_json_output_is_valid(self, left_file, right_file, capsys):
        p = build_classify_parser()
        args = p.parse_args([left_file, right_file, "--format", "json"])
        run_classify(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_json_output_contains_network(self, left_file, right_file, capsys):
        p = build_classify_parser()
        args = p.parse_args([left_file, right_file, "--format", "json"])
        run_classify(args)
        data = json.loads(capsys.readouterr().out)
        assert "network" in data

    def test_category_filter_text(self, left_file, right_file, capsys):
        p = build_classify_parser()
        args = p.parse_args([left_file, right_file, "--category", "security"])
        run_classify(args)
        out = capsys.readouterr().out
        assert "security" in out

    def test_category_filter_json(self, left_file, right_file, capsys):
        p = build_classify_parser()
        args = p.parse_args([left_file, right_file, "--category", "network", "--format", "json"])
        run_classify(args)
        data = json.loads(capsys.readouterr().out)
        assert "network" in data
        assert "DB_HOST" in data["network"]

    def test_returns_zero(self, left_file, right_file):
        p = build_classify_parser()
        args = p.parse_args([left_file, right_file])
        assert run_classify(args) == 0

    def test_unknown_category_prints_no_keys(self, left_file, right_file, capsys):
        p = build_classify_parser()
        args = p.parse_args([left_file, right_file, "--category", "nonexistent"])
        run_classify(args)
        out = capsys.readouterr().out
        assert "No keys found" in out
