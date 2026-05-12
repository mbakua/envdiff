"""Tests for envdiff.heatmap_cmd."""

from __future__ import annotations

import json
import pytest

from envdiff.heatmap_cmd import build_heatmap_parser, run_heatmap


@pytest.fixture
def env_file(tmp_path):
    def _write(name: str, content: str):
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


@pytest.fixture
def left_file(env_file):
    return env_file("left.env", "DB_HOST=localhost\nAPI_KEY=secret\nLOG_LEVEL=info\n")


@pytest.fixture
def right_file(env_file):
    return env_file("right.env", "DB_HOST=prod.db\nAPI_KEY=secret\nLOG_LEVEL=info\n")


@pytest.fixture
def right_file2(env_file):
    return env_file("right2.env", "DB_HOST=staging.db\nAPI_KEY=other\nLOG_LEVEL=info\n")


def test_returns_parser():
    p = build_heatmap_parser()
    assert p is not None


def test_default_top_is_10():
    p = build_heatmap_parser()
    args = p.parse_args(["a.env", "b.env"])
    assert args.top == 10


def test_json_flag_defaults_false():
    p = build_heatmap_parser()
    args = p.parse_args(["a.env", "b.env"])
    assert args.as_json is False


def test_run_heatmap_plain_output(left_file, right_file, capsys):
    p = build_heatmap_parser()
    args = p.parse_args([left_file, right_file])
    run_heatmap(args)
    out = capsys.readouterr().out
    assert "DB_HOST" in out


def test_run_heatmap_json_output(left_file, right_file, capsys):
    p = build_heatmap_parser()
    args = p.parse_args(["--json", left_file, right_file])
    run_heatmap(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data
    assert data["total_diffs"] == 1


def test_run_heatmap_two_pairs(left_file, right_file, right_file2, capsys):
    p = build_heatmap_parser()
    args = p.parse_args(["--json", left_file, right_file, left_file, right_file2])
    run_heatmap(args)
    data = json.loads(capsys.readouterr().out)
    assert data["total_diffs"] == 2
    db_entry = next(e for e in data["entries"] if e["key"] == "DB_HOST")
    assert db_entry["diff_count"] == 2


def test_odd_number_of_files_exits(left_file, right_file):
    p = build_heatmap_parser()
    args = p.parse_args([left_file, right_file, left_file])
    with pytest.raises(SystemExit):
        run_heatmap(args)
