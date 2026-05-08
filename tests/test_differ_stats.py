"""Tests for envdiff.differ_stats and envdiff.stats_cmd."""
import io
import json
import os
import pytest

from envdiff.differ import DiffResult
from envdiff.differ_stats import DiffStats, compute_stats


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def full_diff():
    return DiffResult(
        only_in_left={"GONE": "old"},
        only_in_right={"NEW": "val"},
        value_mismatches={"HOST": ("a", "b"), "PORT": ("80", "443")},
        matching_keys={"DEBUG": "true", "APP": "envdiff"},
    )


@pytest.fixture
def empty_diff():
    return DiffResult(
        only_in_left={},
        only_in_right={},
        value_mismatches={},
        matching_keys={},
    )


# ---------------------------------------------------------------------------
# compute_stats
# ---------------------------------------------------------------------------

class TestComputeStats:
    def test_returns_diff_stats_type(self, full_diff):
        assert isinstance(compute_stats(full_diff), DiffStats)

    def test_total_keys(self, full_diff):
        stats = compute_stats(full_diff)
        assert stats.total_keys == 6  # 1+1+2+2

    def test_only_in_left(self, full_diff):
        assert compute_stats(full_diff).only_in_left == 1

    def test_only_in_right(self, full_diff):
        assert compute_stats(full_diff).only_in_right == 1

    def test_mismatches(self, full_diff):
        assert compute_stats(full_diff).mismatches == 2

    def test_matching(self, full_diff):
        assert compute_stats(full_diff).matching == 2

    def test_change_rate(self, full_diff):
        stats = compute_stats(full_diff)
        # changed = 1+1+2 = 4, total = 6
        assert stats.change_rate == round(4 / 6, 4)

    def test_match_rate_plus_change_rate_equals_one(self, full_diff):
        stats = compute_stats(full_diff)
        assert round(stats.match_rate + stats.change_rate, 4) == 1.0

    def test_empty_diff_zero_rates(self, empty_diff):
        stats = compute_stats(empty_diff)
        assert stats.change_rate == 0.0
        assert stats.match_rate == 0.0
        assert stats.total_keys == 0

    def test_to_dict_has_all_keys(self, full_diff):
        d = compute_stats(full_diff).to_dict()
        expected = {"total_keys", "only_in_left", "only_in_right",
                    "mismatches", "matching", "change_rate", "match_rate"}
        assert expected == set(d.keys())

    def test_str_contains_total(self, full_diff):
        assert "Total keys" in str(compute_stats(full_diff))


# ---------------------------------------------------------------------------
# stats_cmd
# ---------------------------------------------------------------------------

@pytest.fixture
def env_file(tmp_path):
    def _write(name, content):
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


class TestStatsCmd:
    def test_text_output(self, env_file):
        from envdiff.stats_cmd import build_stats_parser, run_stats
        left = env_file("left.env", "A=1\nB=2\n")
        right = env_file("right.env", "A=1\nC=3\n")
        args = build_stats_parser().parse_args([left, right])
        buf = io.StringIO()
        rc = run_stats(args, out=buf)
        assert rc == 0
        assert "Total keys" in buf.getvalue()

    def test_json_output_valid(self, env_file):
        from envdiff.stats_cmd import build_stats_parser, run_stats
        left = env_file("l.env", "X=1\n")
        right = env_file("r.env", "X=2\n")
        args = build_stats_parser().parse_args(["--format", "json", left, right])
        buf = io.StringIO()
        run_stats(args, out=buf)
        data = json.loads(buf.getvalue())
        assert "total_keys" in data
        assert data["mismatches"] == 1

    def test_build_stats_parser_returns_parser(self):
        from envdiff.stats_cmd import build_stats_parser
        import argparse
        assert isinstance(build_stats_parser(), argparse.ArgumentParser)
