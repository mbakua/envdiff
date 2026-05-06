"""Tests for envdiff.snapshotter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.snapshotter import (
    SnapshotError,
    load_snapshot,
    save_snapshot,
    snapshot_metadata,
)

SAMPLE_ENV = {"APP_ENV": "production", "DB_HOST": "db.example.com", "PORT": "5432"}


# ---------------------------------------------------------------------------
# save_snapshot
# ---------------------------------------------------------------------------


class TestSaveSnapshot:
    def test_creates_file(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        result = save_snapshot(SAMPLE_ENV, dest)
        assert result == dest
        assert dest.exists()

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        dest = tmp_path / "nested" / "deep" / "snap.json"
        save_snapshot(SAMPLE_ENV, dest)
        assert dest.exists()

    def test_file_is_valid_json(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        save_snapshot(SAMPLE_ENV, dest)
        data = json.loads(dest.read_text())
        assert isinstance(data, dict)

    def test_env_preserved(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        save_snapshot(SAMPLE_ENV, dest)
        data = json.loads(dest.read_text())
        assert data["env"] == SAMPLE_ENV

    def test_label_stored(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        save_snapshot(SAMPLE_ENV, dest, label="staging-2024")
        data = json.loads(dest.read_text())
        assert data["label"] == "staging-2024"

    def test_version_field_present(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        save_snapshot(SAMPLE_ENV, dest)
        data = json.loads(dest.read_text())
        assert "version" in data

    def test_created_at_field_present(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        save_snapshot(SAMPLE_ENV, dest)
        data = json.loads(dest.read_text())
        assert "created_at" in data and data["created_at"]


# ---------------------------------------------------------------------------
# load_snapshot
# ---------------------------------------------------------------------------


class TestLoadSnapshot:
    def test_roundtrip(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        save_snapshot(SAMPLE_ENV, dest)
        loaded = load_snapshot(dest)
        assert loaded == SAMPLE_ENV

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(SnapshotError, match="not found"):
            load_snapshot(tmp_path / "missing.json")

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        with pytest.raises(SnapshotError, match="Invalid JSON"):
            load_snapshot(bad)

    def test_wrong_version_raises(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        dest.write_text(
            json.dumps({"version": 99, "env": {}, "label": "", "created_at": ""}),
            encoding="utf-8",
        )
        with pytest.raises(SnapshotError, match="Unsupported snapshot version"):
            load_snapshot(dest)

    def test_missing_env_key_raises(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        dest.write_text(
            json.dumps({"version": 1, "label": "", "created_at": ""}),
            encoding="utf-8",
        )
        with pytest.raises(SnapshotError, match="missing 'env'"):
            load_snapshot(dest)


# ---------------------------------------------------------------------------
# snapshot_metadata
# ---------------------------------------------------------------------------


class TestSnapshotMetadata:
    def test_returns_label(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        save_snapshot(SAMPLE_ENV, dest, label="prod")
        meta = snapshot_metadata(dest)
        assert meta["label"] == "prod"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(SnapshotError, match="not found"):
            snapshot_metadata(tmp_path / "gone.json")

    def test_keys_present(self, tmp_path: Path) -> None:
        dest = tmp_path / "snap.json"
        save_snapshot(SAMPLE_ENV, dest)
        meta = snapshot_metadata(dest)
        assert {"version", "label", "created_at"} == set(meta.keys())
