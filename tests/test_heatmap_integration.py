"""Integration tests: build_heatmap working with real diff_envs output."""

from __future__ import annotations

import pytest

from envdiff.differ import diff_envs
from envdiff.differ_heatmap import build_heatmap


ENV_BASE = {"DB_HOST": "localhost", "DB_PASS": "secret", "LOG_LEVEL": "info"}
ENV_PROD = {"DB_HOST": "prod.db", "DB_PASS": "s3cr3t", "LOG_LEVEL": "info"}
ENV_STAGING = {"DB_HOST": "staging.db", "DB_PASS": "secret", "LOG_LEVEL": "debug"}
ENV_DEV = {"DB_HOST": "localhost", "DB_PASS": "secret", "LOG_LEVEL": "info"}


@pytest.fixture
def multi_diffs():
    return [
        diff_envs(ENV_BASE, ENV_PROD),
        diff_envs(ENV_BASE, ENV_STAGING),
        diff_envs(ENV_BASE, ENV_DEV),
    ]


def test_db_host_hottest_key(multi_diffs):
    heatmap = build_heatmap(multi_diffs)
    hottest = heatmap.hottest(1)
    assert hottest[0].key == "DB_HOST"


def test_dev_match_reduces_frequency(multi_diffs):
    heatmap = build_heatmap(multi_diffs)
    db_host = next(e for e in heatmap.entries if e.key == "DB_HOST")
    # base vs dev is identical, so only 2 out of 3 diffs
    assert db_host.diff_count == 2
    assert db_host.frequency == pytest.approx(2 / 3)


def test_log_level_only_in_one_diff(multi_diffs):
    heatmap = build_heatmap(multi_diffs)
    log = next((e for e in heatmap.entries if e.key == "LOG_LEVEL"), None)
    assert log is not None
    assert log.diff_count == 1


def test_stable_key_not_in_heatmap():
    d1 = diff_envs({"STABLE": "same", "X": "1"}, {"STABLE": "same", "X": "2"})
    d2 = diff_envs({"STABLE": "same", "X": "1"}, {"STABLE": "same", "X": "3"})
    heatmap = build_heatmap([d1, d2])
    keys = {e.key for e in heatmap.entries}
    assert "STABLE" not in keys
    assert "X" in keys
