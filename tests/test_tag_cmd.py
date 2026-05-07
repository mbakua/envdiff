"""Tests for envdiff.tag_cmd."""

import json
import pytest
from unittest.mock import patch, MagicMock
from envdiff.tag_cmd import build_tag_parser, run_tag, _parse_extra_tags


@pytest.fixture
def env_file(tmp_path):
    def _write(name, content):
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


@pytest.fixture
def left_file(env_file):
    return env_file("left.env", "DB_PASSWORD=secret\nLOG_LEVEL=INFO\nAPP_NAME=myapp\n")


@pytest.fixture
def right_file(env_file):
    return env_file("right.env", "DB_PASSWORD=secret\nLOG_LEVEL=DEBUG\nREDIS_HOST=cache\n")


class TestBuildTagParser:
    def test_returns_parser(self):
        parser = build_tag_parser()
        assert parser is not None

    def test_requires_left_and_right(self):
        parser = build_tag_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_left_right(self, left_file, right_file):
        parser = build_tag_parser()
        args = parser.parse_args([left_file, right_file])
        assert args.left == left_file
        assert args.right == right_file

    def test_json_flag_default_false(self, left_file, right_file):
        parser = build_tag_parser()
        args = parser.parse_args([left_file, right_file])
        assert args.as_json is False

    def test_filter_tag_default_none(self, left_file, right_file):
        parser = build_tag_parser()
        args = parser.parse_args([left_file, right_file])
        assert args.filter_tag is None


class TestParseExtraTags:
    def test_valid_entry_parsed(self):
        result = _parse_extra_tags(["billing=PAYMENT"])
        assert result == {"billing": ["PAYMENT"]}

    def test_multiple_patterns_same_tag(self):
        result = _parse_extra_tags(["billing=PAYMENT", "billing=INVOICE"])
        assert set(result["billing"]) == {"PAYMENT", "INVOICE"}

    def test_malformed_entry_skipped(self, capsys):
        result = _parse_extra_tags(["badvalue"])
        assert result == {}
        captured = capsys.readouterr()
        assert "Warning" in captured.err


class TestRunTag:
    def test_plain_output(self, left_file, right_file, capsys):
        parser = build_tag_parser()
        args = parser.parse_args([left_file, right_file])
        code = run_tag(args)
        assert code == 0
        out = capsys.readouterr().out
        assert "[" in out  # at least one tag block printed

    def test_json_output_is_valid(self, left_file, right_file, capsys):
        parser = build_tag_parser()
        args = parser.parse_args([left_file, right_file, "--json"])
        run_tag(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_filter_tag_shows_only_matching(self, left_file, right_file, capsys):
        parser = build_tag_parser()
        args = parser.parse_args([left_file, right_file, "--filter-tag", "logging"])
        run_tag(args)
        out = capsys.readouterr().out
        assert "LOG_LEVEL" in out
        assert "DB_PASSWORD" not in out

    def test_filter_tag_json(self, left_file, right_file, capsys):
        parser = build_tag_parser()
        args = parser.parse_args([left_file, right_file, "--filter-tag", "secret", "--json"])
        run_tag(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "secret" in data
        assert "DB_PASSWORD" in data["secret"]

    def test_filter_tag_no_match_prints_message(self, left_file, right_file, capsys):
        parser = build_tag_parser()
        args = parser.parse_args([left_file, right_file, "--filter-tag", "nonexistent"])
        code = run_tag(args)
        assert code == 0
        out = capsys.readouterr().out
        assert "No keys matched" in out
