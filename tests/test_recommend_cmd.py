"""Tests for envdiff.recommend_cmd."""

import pytest
from unittest.mock import patch

from envdiff.recommend_cmd import build_recommend_parser, run_recommend


@pytest.fixture
def env_file(tmp_path):
    return tmp_path


def _write(path, content):
    path.write_text(content)
    return str(path)


@pytest.fixture
def left_file(env_file):
    return _write(env_file / "left.env", "DB_PASSWORD=secret\nLOG_LEVEL=debug\n")


@pytest.fixture
def right_file(env_file):
    return _write(env_file / "right.env", "LOG_LEVEL=info\nNEW_KEY=value\n")


class TestBuildRecommendParser:
    def test_returns_parser(self):
        p = build_recommend_parser()
        assert p is not None

    def test_has_left_and_right(self):
        p = build_recommend_parser()
        args = p.parse_args(["a.env", "b.env"])
        assert args.left == "a.env"
        assert args.right == "b.env"

    def test_no_color_default_false(self):
        p = build_recommend_parser()
        args = p.parse_args(["a.env", "b.env"])
        assert args.no_color is False

    def test_severity_default_none(self):
        p = build_recommend_parser()
        args = p.parse_args(["a.env", "b.env"])
        assert args.severity is None

    def test_fail_on_error_default_false(self):
        p = build_recommend_parser()
        args = p.parse_args(["a.env", "b.env"])
        assert args.fail_on_error is False

    def test_severity_accepts_error(self):
        p = build_recommend_parser()
        args = p.parse_args(["a.env", "b.env", "--severity", "error"])
        assert args.severity == "error"


class TestRunRecommend:
    def test_returns_zero_on_clean(self, env_file):
        f = _write(env_file / "same.env", "KEY=value\n")
        p = build_recommend_parser()
        args = p.parse_args([f, f])
        assert run_recommend(args) == 0

    def test_returns_zero_without_fail_on_error(self, left_file, right_file):
        p = build_recommend_parser()
        args = p.parse_args([left_file, right_file])
        assert run_recommend(args) == 0

    def test_returns_one_with_fail_on_error_and_errors(self, left_file, right_file):
        p = build_recommend_parser()
        args = p.parse_args([left_file, right_file, "--fail-on-error"])
        assert run_recommend(args) == 1

    def test_no_color_flag_accepted(self, left_file, right_file):
        p = build_recommend_parser()
        args = p.parse_args([left_file, right_file, "--no-color"])
        result = run_recommend(args)
        assert result in (0, 1)

    def test_severity_filter_applied(self, left_file, right_file, capsys):
        p = build_recommend_parser()
        args = p.parse_args([left_file, right_file, "--severity", "info"])
        run_recommend(args)
        captured = capsys.readouterr()
        # info-level items should not contain ERROR prefix
        assert "[ERROR]" not in captured.out
