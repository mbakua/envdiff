"""Tests for envdiff.snapshot_delta_cmd."""
from __future__ import annotations

import json
import pathlib

import pytest

from envdiff.snapshot_delta_cmd import build_snapshot_delta_parser, run_snapshot_delta


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


def _write_snapshot(path: pathlib.Path, env: dict) -> None:
    snap = {
        "timestamp": "2024-01-01T00:00:00",
        "user": "tester",
        "env": env,
    }
    path.write_text(json.dumps(snap))


@pytest.fixture
def before_file(tmp_dir):
    p = tmp_dir / "before.json"
    _write_snapshot(p, {"DB_HOST": "localhost", "LOG_LEVEL": "debug", "API_KEY": "abc"})
    return str(p)


@pytest.fixture
def after_file(tmp_dir):
    p = tmp_dir / "after.json"
    _write_snapshot(p, {"DB_HOST": "prod.db", "API_KEY": "abc", "NEW_KEY": "val"})
    return str(p)


class TestBuildSnapshotDeltaParser:
    def test_returns_parser(self):
        p = build_snapshot_delta_parser()
        assert p is not None

    def test_default_format_is_text(self):
        p = build_snapshot_delta_parser()
        args = p.parse_args(["a.json", "b.json"])
        assert args.format == "text"

    def test_json_format_flag(self):
        p = build_snapshot_delta_parser()
        args = p.parse_args(["a.json", "b.json", "--format", "json"])
        assert args.format == "json"

    def test_no_color_flag(self):
        p = build_snapshot_delta_parser()
        args = p.parse_args(["a.json", "b.json", "--no-color"])
        assert args.no_color is True


class TestRunSnapshotDelta:
    def test_returns_nonzero_when_changes(self, before_file, after_file):
        parser = build_snapshot_delta_parser()
        args = parser.parse_args([before_file, after_file])
        rc = run_snapshot_delta(args)
        assert rc == 1

    def test_returns_zero_when_no_changes(self, before_file):
        parser = build_snapshot_delta_parser()
        args = parser.parse_args([before_file, before_file])
        rc = run_snapshot_delta(args)
        assert rc == 0

    def test_json_output_is_valid(self, before_file, after_file, capsys):
        parser = build_snapshot_delta_parser()
        args = parser.parse_args([before_file, after_file, "--format", "json"])
        run_snapshot_delta(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "added" in data and "removed" in data and "changed" in data

    def test_json_added_key_present(self, before_file, after_file, capsys):
        parser = build_snapshot_delta_parser()
        args = parser.parse_args([before_file, after_file, "--format", "json"])
        run_snapshot_delta(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        added_keys = [e["key"] for e in data["added"]]
        assert "NEW_KEY" in added_keys

    def test_missing_file_returns_error(self, tmp_path, capsys):
        parser = build_snapshot_delta_parser()
        args = parser.parse_args(["nonexistent_a.json", "nonexistent_b.json"])
        rc = run_snapshot_delta(args)
        assert rc == 1
