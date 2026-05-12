"""Tests for envdiff.differ_heatmap."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffResult
from envdiff.differ_heatmap import HeatmapEntry, DiffHeatmap, build_heatmap


@pytest.fixture
def three_diffs():
    d1 = DiffResult(
        only_in_left=["REMOVED"],
        only_in_right=[],
        value_mismatches={"DB_HOST": ("a", "b"), "API_KEY": ("x", "y")},
        matching_keys=["LOG_LEVEL"],
    )
    d2 = DiffResult(
        only_in_left=[],
        only_in_right=["NEW_KEY"],
        value_mismatches={"DB_HOST": ("a", "c")},
        matching_keys=["LOG_LEVEL", "API_KEY"],
    )
    d3 = DiffResult(
        only_in_left=[],
        only_in_right=[],
        value_mismatches={"DB_HOST": ("a", "d")},
        matching_keys=["LOG_LEVEL", "API_KEY", "REMOVED"],
    )
    return [d1, d2, d3]


def test_returns_diff_heatmap_type(three_diffs):
    result = build_heatmap(three_diffs)
    assert isinstance(result, DiffHeatmap)


def test_total_diffs_recorded(three_diffs):
    result = build_heatmap(three_diffs)
    assert result.total_diffs == 3


def test_db_host_appears_in_all_diffs(three_diffs):
    result = build_heatmap(three_diffs)
    entry = next(e for e in result.entries if e.key == "DB_HOST")
    assert entry.diff_count == 3


def test_api_key_appears_in_one_diff(three_diffs):
    result = build_heatmap(three_diffs)
    entry = next(e for e in result.entries if e.key == "API_KEY")
    assert entry.diff_count == 1


def test_frequency_is_fraction(three_diffs):
    result = build_heatmap(three_diffs)
    entry = next(e for e in result.entries if e.key == "DB_HOST")
    assert entry.frequency == pytest.approx(1.0)


def test_hottest_returns_sorted_descending(three_diffs):
    result = build_heatmap(three_diffs)
    top = result.hottest(10)
    freqs = [e.frequency for e in top]
    assert freqs == sorted(freqs, reverse=True)


def test_hottest_respects_n_limit(three_diffs):
    result = build_heatmap(three_diffs)
    assert len(result.hottest(2)) <= 2


def test_empty_diffs_list():
    result = build_heatmap([])
    assert result.total_diffs == 0
    assert result.entries == []


def test_to_dict_contains_expected_keys(three_diffs):
    result = build_heatmap(three_diffs)
    d = result.to_dict()
    assert "total_diffs" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_entry_str_format():
    entry = HeatmapEntry(key="DB_HOST", diff_count=3, total=3)
    s = str(entry)
    assert "DB_HOST" in s
    assert "3/3" in s
    assert "100%" in s


def test_matching_only_keys_not_counted(three_diffs):
    result = build_heatmap(three_diffs)
    keys = {e.key for e in result.entries}
    assert "LOG_LEVEL" not in keys
