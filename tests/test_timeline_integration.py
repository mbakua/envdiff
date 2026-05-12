"""Integration tests: build_timeline -> TimelineReport -> assertions."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envdiff.parser import parse_env_file
from envdiff.differ_timeline import build_timeline


@pytest.fixture()
def snapshot_files(tmp_path):
    files = [
        ("v1.env", "DB_HOST=db1\nDB_PASS=secret1\nAPP_ENV=dev\n"),
        ("v2.env", "DB_HOST=db2\nDB_PASS=secret1\nAPP_ENV=staging\n"),
        ("v3.env", "DB_HOST=db2\nDB_PASS=secret2\nAPP_ENV=prod\n"),
    ]
    paths = []
    for name, content in files:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        paths.append(str(p))
    return paths


class TestTimelineIntegration:
    def test_three_snapshot_report_has_correct_key_count(self, snapshot_files):
        snaps = [parse_env_file(f) for f in snapshot_files]
        report = build_timeline(snaps, ["v1", "v2", "v3"])
        assert len(report.timelines) == 3

    def test_db_host_changes_at_v2(self, snapshot_files):
        snaps = [parse_env_file(f) for f in snapshot_files]
        report = build_timeline(snaps, ["v1", "v2", "v3"])
        changes = report.timelines["DB_HOST"].change_points()
        assert changes == ["v2"]

    def test_db_pass_changes_at_v3(self, snapshot_files):
        snaps = [parse_env_file(f) for f in snapshot_files]
        report = build_timeline(snaps, ["v1", "v2", "v3"])
        changes = report.timelines["DB_PASS"].change_points()
        assert changes == ["v3"]

    def test_stable_count_in_to_dict(self, snapshot_files):
        snaps = [parse_env_file(f) for f in snapshot_files]
        report = build_timeline(snaps, ["v1", "v2", "v3"])
        d = report.to_dict()
        # All three keys change at some point, so stable_count should be 0
        assert d["stable_count"] == 0
        assert d["unstable_count"] == 3

    def test_absent_key_shows_none(self, tmp_path):
        p1 = tmp_path / "a.env"
        p2 = tmp_path / "b.env"
        p1.write_text("FOO=bar\nONLY_A=yes\n")
        p2.write_text("FOO=baz\n")
        snaps = [parse_env_file(str(p1)), parse_env_file(str(p2))]
        report = build_timeline(snaps, ["a", "b"])
        only_a_entry_b = report.timelines["ONLY_A"].entries[1]
        assert only_a_entry_b.value is None
