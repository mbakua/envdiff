"""Tests for envdiff.baseline and envdiff.baseline_cmd."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from envdiff.baseline import BaselineReport, compare_to_baseline
from envdiff.differ import DiffResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_snapshot(path: Path, env: dict, label: str | None = None) -> None:
    data = {"env": env}
    if label:
        data["label"] = label
    path.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# compare_to_baseline
# ---------------------------------------------------------------------------

class TestCompareToBaseline:
    def test_returns_baseline_report_type(self, tmp_path):
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, {"KEY": "val"})
        report = compare_to_baseline({"KEY": "val"}, str(snap))
        assert isinstance(report, BaselineReport)

    def test_clean_when_envs_match(self, tmp_path):
        snap = tmp_path / "snap.json"
        env = {"A": "1", "B": "2"}
        _write_snapshot(snap, env)
        report = compare_to_baseline(env.copy(), str(snap))
        assert report.is_clean

    def test_detects_removed_key(self, tmp_path):
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, {"A": "1", "B": "2"})
        report = compare_to_baseline({"A": "1"}, str(snap))
        assert not report.is_clean
        assert "B" in report.diff.only_in_left

    def test_detects_added_key(self, tmp_path):
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, {"A": "1"})
        report = compare_to_baseline({"A": "1", "NEW": "x"}, str(snap))
        assert not report.is_clean
        assert "NEW" in report.diff.only_in_right
        assert "NEW" in report.improvements

    def test_detects_value_mismatch(self, tmp_path):
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, {"A": "old"})
        report = compare_to_baseline({"A": "new"}, str(snap))
        assert not report.is_clean
        assert "A" in report.diff.value_mismatches
        assert "A" in report.regressions

    def test_snapshot_label_captured(self, tmp_path):
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, {"A": "1"}, label="production-2024")
        report = compare_to_baseline({"A": "1"}, str(snap))
        assert report.snapshot_label == "production-2024"

    def test_snapshot_path_stored(self, tmp_path):
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, {})
        report = compare_to_baseline({}, str(snap))
        assert report.snapshot_path == str(snap)


# ---------------------------------------------------------------------------
# BaselineReport.summary
# ---------------------------------------------------------------------------

class TestBaselineReportSummary:
    def test_clean_summary_contains_clean(self, tmp_path):
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, {"X": "1"})
        report = compare_to_baseline({"X": "1"}, str(snap))
        assert "CLEAN" in report.summary()

    def test_drift_summary_mentions_drift(self, tmp_path):
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, {"X": "1"})
        report = compare_to_baseline({"X": "2"}, str(snap))
        assert "DRIFT" in report.summary()

    def test_summary_includes_label(self, tmp_path):
        snap = tmp_path / "snap.json"
        _write_snapshot(snap, {}, label="staging")
        report = compare_to_baseline({}, str(snap))
        assert "staging" in report.summary()
