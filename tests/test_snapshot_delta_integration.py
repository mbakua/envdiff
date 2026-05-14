"""Integration tests: snapshotter -> differ -> compute_snapshot_delta pipeline."""
from __future__ import annotations

import pathlib
import pytest

from envdiff.snapshotter import save_snapshot, load_snapshot
from envdiff.differ import diff_envs
from envdiff.differ_snapshot_delta import compute_snapshot_delta


@pytest.fixture
def v1_snap(tmp_path) -> pathlib.Path:
    env = {"DB_HOST": "localhost", "DB_PASS": "secret", "LOG_LEVEL": "debug"}
    p = tmp_path / "v1.json"
    save_snapshot(env, str(p))
    return p


@pytest.fixture
def v2_snap(tmp_path) -> pathlib.Path:
    env = {"DB_HOST": "prod.db", "DB_PASS": "secret", "NEW_FEATURE": "on"}
    p = tmp_path / "v2.json"
    save_snapshot(env, str(p))
    return p


class TestSnapshotDeltaIntegration:
    def test_pipeline_produces_delta(self, v1_snap, v2_snap):
        s1 = load_snapshot(str(v1_snap))
        s2 = load_snapshot(str(v2_snap))
        d1 = diff_envs(s1["env"], {})
        d2 = diff_envs(s2["env"], {})
        delta = compute_snapshot_delta(d1, d2)
        assert not delta.is_empty

    def test_log_level_removed_in_v2(self, v1_snap, v2_snap):
        s1 = load_snapshot(str(v1_snap))
        s2 = load_snapshot(str(v2_snap))
        d1 = diff_envs(s1["env"], {})
        d2 = diff_envs(s2["env"], {})
        delta = compute_snapshot_delta(d1, d2)
        removed_keys = [e.key for e in delta.removed]
        assert "LOG_LEVEL" in removed_keys

    def test_new_feature_added_in_v2(self, v1_snap, v2_snap):
        s1 = load_snapshot(str(v1_snap))
        s2 = load_snapshot(str(v2_snap))
        d1 = diff_envs(s1["env"], {})
        d2 = diff_envs(s2["env"], {})
        delta = compute_snapshot_delta(d1, d2)
        added_keys = [e.key for e in delta.added]
        assert "NEW_FEATURE" in added_keys

    def test_db_host_changed(self, v1_snap, v2_snap):
        s1 = load_snapshot(str(v1_snap))
        s2 = load_snapshot(str(v2_snap))
        d1 = diff_envs(s1["env"], {})
        d2 = diff_envs(s2["env"], {})
        delta = compute_snapshot_delta(d1, d2)
        changed_keys = [e.key for e in delta.changed]
        assert "DB_HOST" in changed_keys

    def test_db_pass_unchanged(self, v1_snap, v2_snap):
        s1 = load_snapshot(str(v1_snap))
        s2 = load_snapshot(str(v2_snap))
        d1 = diff_envs(s1["env"], {})
        d2 = diff_envs(s2["env"], {})
        delta = compute_snapshot_delta(d1, d2)
        all_changed = (
            [e.key for e in delta.added]
            + [e.key for e in delta.removed]
            + [e.key for e in delta.changed]
        )
        assert "DB_PASS" not in all_changed

    def test_total_changes_is_three(self, v1_snap, v2_snap):
        s1 = load_snapshot(str(v1_snap))
        s2 = load_snapshot(str(v2_snap))
        d1 = diff_envs(s1["env"], {})
        d2 = diff_envs(s2["env"], {})
        delta = compute_snapshot_delta(d1, d2)
        assert delta.total_changes == 3
