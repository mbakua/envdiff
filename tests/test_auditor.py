"""Tests for envdiff.auditor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.auditor import AuditEntry, load_audit_log, record_diff
from envdiff.differ import DiffResult


@pytest.fixture()
def tmp_log(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


@pytest.fixture()
def simple_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"OLD_KEY": "1"},
        only_in_right={"NEW_KEY": "2"},
        value_mismatches={"DB_HOST": ("localhost", "prod.db")},
        matching_keys={"APP": "myapp"},
    )


class TestRecordDiff:
    def test_creates_log_file(self, simple_diff, tmp_log):
        record_diff(simple_diff, log_path=tmp_log)
        assert tmp_log.exists()

    def test_appends_valid_json_line(self, simple_diff, tmp_log):
        record_diff(simple_diff, log_path=tmp_log)
        lines = tmp_log.read_text().strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["operation"] == "diff"

    def test_multiple_calls_append(self, simple_diff, tmp_log):
        record_diff(simple_diff, log_path=tmp_log)
        record_diff(simple_diff, log_path=tmp_log)
        lines = tmp_log.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_keys_only_left_recorded(self, simple_diff, tmp_log):
        entry = record_diff(simple_diff, log_path=tmp_log)
        assert "OLD_KEY" in entry.keys_only_left

    def test_keys_only_right_recorded(self, simple_diff, tmp_log):
        entry = record_diff(simple_diff, log_path=tmp_log)
        assert "NEW_KEY" in entry.keys_only_right

    def test_mismatched_keys_recorded(self, simple_diff, tmp_log):
        entry = record_diff(simple_diff, log_path=tmp_log)
        assert "DB_HOST" in entry.keys_mismatched

    def test_sources_stored(self, simple_diff, tmp_log):
        entry = record_diff(simple_diff, "staging.env", "prod.env", log_path=tmp_log)
        assert entry.left_source == "staging.env"
        assert entry.right_source == "prod.env"

    def test_returns_audit_entry(self, simple_diff, tmp_log):
        result = record_diff(simple_diff, log_path=tmp_log)
        assert isinstance(result, AuditEntry)

    def test_creates_parent_dirs(self, simple_diff, tmp_path):
        nested = tmp_path / "deep" / "nested" / "audit.jsonl"
        record_diff(simple_diff, log_path=nested)
        assert nested.exists()


class TestLoadAuditLog:
    def test_empty_when_no_file(self, tmp_log):
        entries = load_audit_log(tmp_log)
        assert entries == []

    def test_returns_list_of_entries(self, simple_diff, tmp_log):
        record_diff(simple_diff, log_path=tmp_log)
        entries = load_audit_log(tmp_log)
        assert len(entries) == 1
        assert isinstance(entries[0], AuditEntry)

    def test_round_trip_preserves_operation(self, simple_diff, tmp_log):
        record_diff(simple_diff, log_path=tmp_log)
        entries = load_audit_log(tmp_log)
        assert entries[0].operation == "diff"

    def test_round_trip_preserves_sources(self, simple_diff, tmp_log):
        record_diff(simple_diff, "a.env", "b.env", log_path=tmp_log)
        entries = load_audit_log(tmp_log)
        assert entries[0].left_source == "a.env"
        assert entries[0].right_source == "b.env"
