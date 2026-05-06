"""Tests for envdiff.audit_cmd."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.audit_cmd import build_audit_parser, run_list, run_stats
from envdiff.auditor import record_diff
from envdiff.differ import DiffResult


@pytest.fixture()
def tmp_log(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


@pytest.fixture()
def populated_log(tmp_log: Path) -> Path:
    diff = DiffResult(
        only_in_left={"GONE": "x"},
        only_in_right={"NEW": "y"},
        value_mismatches={"HOST": ("a", "b")},
        matching_keys={},
    )
    record_diff(diff, "staging.env", "prod.env", log_path=tmp_log)
    record_diff(diff, "dev.env", "staging.env", log_path=tmp_log)
    return tmp_log


class TestBuildAuditParser:
    def test_returns_parser(self):
        p = build_audit_parser()
        assert p is not None

    def test_default_log_path(self):
        p = build_audit_parser()
        args = p.parse_args(["list"])
        assert "audit" in args.log or "envdiff" in args.log

    def test_custom_log_flag(self):
        p = build_audit_parser()
        args = p.parse_args(["--log", "/tmp/my.jsonl", "list"])
        assert args.log == "/tmp/my.jsonl"


class TestRunList:
    def test_empty_log_prints_message(self, tmp_log, capsys):
        import argparse
        args = argparse.Namespace(log=str(tmp_log))
        run_list(args)
        captured = capsys.readouterr()
        assert "No audit entries" in captured.out

    def test_lists_entries(self, populated_log, capsys):
        import argparse
        args = argparse.Namespace(log=str(populated_log))
        run_list(args)
        captured = capsys.readouterr()
        assert "staging.env" in captured.out

    def test_returns_zero(self, populated_log):
        import argparse
        args = argparse.Namespace(log=str(populated_log))
        assert run_list(args) == 0


class TestRunStats:
    def test_shows_totals(self, populated_log, capsys):
        import argparse
        args = argparse.Namespace(log=str(populated_log), user=None)
        run_stats(args)
        out = capsys.readouterr().out
        assert "Total operations" in out
        assert "2" in out

    def test_shows_mismatch_count(self, populated_log, capsys):
        import argparse
        args = argparse.Namespace(log=str(populated_log), user=None)
        run_stats(args)
        out = capsys.readouterr().out
        assert "Value mismatches" in out

    def test_empty_log_no_entries_message(self, tmp_log, capsys):
        import argparse
        args = argparse.Namespace(log=str(tmp_log), user=None)
        run_stats(args)
        out = capsys.readouterr().out
        assert "No matching" in out

    def test_returns_zero(self, populated_log):
        import argparse
        args = argparse.Namespace(log=str(populated_log), user=None)
        assert run_stats(args) == 0
