"""Tests for envdiff.differ_timeline."""

from __future__ import annotations

import pytest

from envdiff.differ_timeline import (
    TimelineEntry,
    KeyTimeline,
    TimelineReport,
    build_timeline,
)


@pytest.fixture()
def three_snaps():
    return [
        {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"},
        {"HOST": "staging.example.com", "PORT": "5432"},
        {"HOST": "prod.example.com", "PORT": "5432", "DEBUG": "false"},
    ]


@pytest.fixture()
def labels():
    return ["dev", "staging", "prod"]


class TestBuildTimeline:
    def test_returns_timeline_report_type(self, three_snaps, labels):
        result = build_timeline(three_snaps, labels)
        assert isinstance(result, TimelineReport)

    def test_all_keys_present(self, three_snaps, labels):
        result = build_timeline(three_snaps, labels)
        assert set(result.timelines.keys()) == {"HOST", "PORT", "DEBUG"}

    def test_absent_key_has_none_value(self, three_snaps, labels):
        result = build_timeline(three_snaps, labels)
        staging_debug = result.timelines["DEBUG"].entries[1]
        assert staging_debug.value is None

    def test_mismatched_lengths_raises(self, three_snaps):
        with pytest.raises(ValueError):
            build_timeline(three_snaps, ["only-one"])

    def test_stable_key_detected(self, three_snaps, labels):
        result = build_timeline(three_snaps, labels)
        assert result.timelines["PORT"].is_stable()

    def test_unstable_key_detected(self, three_snaps, labels):
        result = build_timeline(three_snaps, labels)
        assert not result.timelines["HOST"].is_stable()

    def test_stable_keys_list(self, three_snaps, labels):
        result = build_timeline(three_snaps, labels)
        assert "PORT" in result.stable_keys()

    def test_unstable_keys_list(self, three_snaps, labels):
        result = build_timeline(three_snaps, labels)
        assert "HOST" in result.unstable_keys()
        assert "DEBUG" in result.unstable_keys()


class TestKeyTimeline:
    def test_change_points_correct(self, three_snaps, labels):
        result = build_timeline(three_snaps, labels)
        host_changes = result.timelines["HOST"].change_points()
        assert host_changes == ["staging", "prod"]

    def test_no_change_points_for_stable(self, three_snaps, labels):
        result = build_timeline(three_snaps, labels)
        assert result.timelines["PORT"].change_points() == []

    def test_to_dict_contains_key(self, three_snaps, labels):
        result = build_timeline(three_snaps, labels)
        d = result.timelines["HOST"].to_dict()
        assert d["key"] == "HOST"
        assert "entries" in d
        assert "change_points" in d


class TestTimelineEntry:
    def test_str_with_value(self):
        e = TimelineEntry(label="dev", value="localhost")
        assert str(e) == "dev: localhost"

    def test_str_without_value(self):
        e = TimelineEntry(label="staging", value=None)
        assert str(e) == "staging: <absent>"


class TestTimelineReport:
    def test_to_dict_structure(self, three_snaps, labels):
        report = build_timeline(three_snaps, labels)
        d = report.to_dict()
        assert "total_keys" in d
        assert "unstable_count" in d
        assert "stable_count" in d
        assert d["total_keys"] == 3
