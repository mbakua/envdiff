"""Tests for envdiff.timeline_cmd."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

import pytest

from envdiff.timeline_cmd import build_timeline_parser, run_timeline


@pytest.fixture()
def env_file(tmp_path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        return str(p)
    return _write


@pytest.fixture()
def dev_file(env_file):
    return env_file("dev.env", "HOST=localhost\nPORT=5432\nDEBUG=true\n")


@pytest.fixture()
def prod_file(env_file):
    return env_file("prod.env", "HOST=prod.example.com\nPORT=5432\nDEBUG=false\n")


class TestBuildTimelineParser:
    def test_returns_parser(self):
        p = build_timeline_parser()
        assert p is not None

    def test_parses_files(self, dev_file, prod_file):
        p = build_timeline_parser()
        args = p.parse_args([dev_file, prod_file])
        assert len(args.files) == 2

    def test_default_format_is_text(self, dev_file, prod_file):
        p = build_timeline_parser()
        args = p.parse_args([dev_file, prod_file])
        assert args.format == "text"

    def test_json_format_flag(self, dev_file, prod_file):
        p = build_timeline_parser()
        args = p.parse_args([dev_file, prod_file, "--format", "json"])
        assert args.format == "json"

    def test_unstable_only_flag(self, dev_file, prod_file):
        p = build_timeline_parser()
        args = p.parse_args([dev_file, prod_file, "--unstable-only"])
        assert args.unstable_only is True

    def test_key_filter_flag(self, dev_file, prod_file):
        p = build_timeline_parser()
        args = p.parse_args([dev_file, prod_file, "--key", "HOST"])
        assert args.key == "HOST"


class TestRunTimeline:
    def test_returns_zero_on_success(self, dev_file, prod_file):
        p = build_timeline_parser()
        args = p.parse_args([dev_file, prod_file])
        assert run_timeline(args) == 0

    def test_json_output_is_valid(self, dev_file, prod_file, capsys):
        p = build_timeline_parser()
        args = p.parse_args([dev_file, prod_file, "--format", "json"])
        run_timeline(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "HOST" in data

    def test_key_filter_limits_output(self, dev_file, prod_file, capsys):
        p = build_timeline_parser()
        args = p.parse_args([dev_file, prod_file, "--key", "HOST", "--format", "json"])
        run_timeline(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert list(data.keys()) == ["HOST"]

    def test_unstable_only_excludes_stable(self, dev_file, prod_file, capsys):
        p = build_timeline_parser()
        args = p.parse_args([dev_file, prod_file, "--unstable-only", "--format", "json"])
        run_timeline(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "PORT" not in data

    def test_label_mismatch_returns_error(self, dev_file, prod_file):
        p = build_timeline_parser()
        args = p.parse_args([dev_file, prod_file, "--labels", "only-one"])
        assert run_timeline(args) == 2
