"""Tests for envdiff.watcher and envdiff.watch_cmd."""

import os
import pytest

from envdiff.watcher import watch_file, WatchError, _file_hash, _load_env
from envdiff.differ import DiffResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


@pytest.fixture()
def baseline():
    return {"FOO": "bar", "BAZ": "qux"}


# ---------------------------------------------------------------------------
# _file_hash
# ---------------------------------------------------------------------------

class TestFileHash:
    def test_returns_string(self, env_file):
        assert isinstance(_file_hash(str(env_file)), str)

    def test_same_content_same_hash(self, env_file):
        h1 = _file_hash(str(env_file))
        h2 = _file_hash(str(env_file))
        assert h1 == h2

    def test_different_content_different_hash(self, env_file):
        h1 = _file_hash(str(env_file))
        env_file.write_text("FOO=changed\n")
        h2 = _file_hash(str(env_file))
        assert h1 != h2


# ---------------------------------------------------------------------------
# _load_env
# ---------------------------------------------------------------------------

class TestLoadEnv:
    def test_returns_dict_for_existing_file(self, env_file):
        result = _load_env(str(env_file))
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_returns_empty_dict_for_missing_file(self, tmp_path):
        result = _load_env(str(tmp_path / "missing.env"))
        assert result == {}


# ---------------------------------------------------------------------------
# watch_file
# ---------------------------------------------------------------------------

class TestWatchFile:
    def test_raises_watch_error_for_missing_file(self, tmp_path, baseline):
        missing = str(tmp_path / "ghost.env")
        with pytest.raises(WatchError, match="File not found"):
            watch_file(missing, baseline, on_change=lambda d: None, max_cycles=1)

    def test_on_change_called_when_file_modified(self, env_file, baseline, monkeypatch):
        """Simulate a file change between the first and second poll."""
        calls = []

        original_hash = _file_hash(str(env_file))
        hashes = iter([original_hash, "different_hash_value"])

        monkeypatch.setattr("envdiff.watcher._file_hash", lambda p: next(hashes))
        monkeypatch.setattr("envdiff.watcher._load_env", lambda p: {"FOO": "changed"})
        monkeypatch.setattr("envdiff.watcher.time.sleep", lambda s: None)

        watch_file(
            str(env_file),
            baseline,
            on_change=lambda d: calls.append(d),
            interval=0,
            max_cycles=2,
        )

        assert len(calls) == 1
        assert isinstance(calls[0], DiffResult)

    def test_on_change_not_called_when_file_unchanged(self, env_file, baseline, monkeypatch):
        calls = []
        monkeypatch.setattr("envdiff.watcher.time.sleep", lambda s: None)

        watch_file(
            str(env_file),
            baseline,
            on_change=lambda d: calls.append(d),
            interval=0,
            max_cycles=3,
        )

        assert calls == []
