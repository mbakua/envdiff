"""Tests for envdiff.scorecard_cmd."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from envdiff.scorecard_cmd import build_scorecard_parser, run_scorecard, main


@pytest.fixture()
def env_file(tmp_path: Path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


@pytest.fixture()
def left_file(env_file):
    return env_file("left.env", "DB_HOST=localhost\nPORT=5432\nSECRET=abc\n")


@pytest.fixture()
def right_file(env_file):
    return env_file("right.env", "DB_HOST=prod-db\nPORT=5432\n")


@pytest.fixture()
def base_args(left_file, right_file):
    return ["--pair", f"dev:{left_file}:{right_file}"]


def test_returns_parser():
    p = build_scorecard_parser()
    assert p is not None


def test_default_format_is_text():
    p = build_scorecard_parser()
    args = p.parse_args(["--pair", "x:a:b"])
    assert args.format == "text"


def test_json_format_flag():
    p = build_scorecard_parser()
    args = p.parse_args(["--pair", "x:a:b", "--format", "json"])
    assert args.format == "json"


def test_run_scorecard_text_output(capsys, base_args, left_file, right_file):
    p = build_scorecard_parser()
    args = p.parse_args(base_args)
    run_scorecard(args)
    out = capsys.readouterr().out
    assert "dev" in out
    assert "Grade" in out or "/100" in out or "Score" in out


def test_run_scorecard_json_output(capsys, base_args, left_file, right_file):
    p = build_scorecard_parser()
    args = p.parse_args(base_args + ["--format", "json"])
    run_scorecard(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data
    assert "average_score" in data


def test_multiple_pairs_json(capsys, env_file):
    l1 = env_file("l1.env", "A=1\nB=2\n")
    r1 = env_file("r1.env", "A=1\nB=2\n")
    l2 = env_file("l2.env", "X=old\n")
    r2 = env_file("r2.env", "X=new\n")
    p = build_scorecard_parser()
    args = p.parse_args([
        "--pair", f"clean:{l1}:{r1}",
        "--pair", f"dirty:{l2}:{r2}",
        "--format", "json",
    ])
    run_scorecard(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    labels = [e["label"] for e in data["entries"]]
    assert "clean" in labels
    assert "dirty" in labels


def test_invalid_pair_exits(tmp_path):
    import sys
    p = build_scorecard_parser()
    args = p.parse_args(["--pair", "bad-format"])
    with pytest.raises(SystemExit):
        run_scorecard(args)


def test_main_runs_without_error(capsys, base_args):
    main(base_args)
    out = capsys.readouterr().out
    assert len(out) > 0
