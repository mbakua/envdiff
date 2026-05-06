"""Snapshot current or file-based env state to disk for later comparison."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

SNAPSHOT_VERSION = 1


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_snapshot(
    env: Dict[str, str],
    path: str | Path,
    label: Optional[str] = None,
) -> Path:
    """Persist *env* as a JSON snapshot file at *path*.

    Returns the resolved Path that was written.
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "version": SNAPSHOT_VERSION,
        "label": label or "",
        "created_at": _timestamp(),
        "env": env,
    }

    try:
        dest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    except OSError as exc:
        raise SnapshotError(f"Cannot write snapshot to {dest}: {exc}") from exc

    return dest


def load_snapshot(path: str | Path) -> Dict[str, str]:
    """Load a previously saved snapshot and return the env mapping.

    Raises SnapshotError on missing file, bad JSON, or version mismatch.
    """
    src = Path(path)
    if not src.exists():
        raise SnapshotError(f"Snapshot file not found: {src}")

    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"Invalid JSON in snapshot {src}: {exc}") from exc

    if data.get("version") != SNAPSHOT_VERSION:
        raise SnapshotError(
            f"Unsupported snapshot version {data.get('version')} in {src}"
        )

    env = data.get("env")
    if not isinstance(env, dict):
        raise SnapshotError(f"Snapshot {src} is missing 'env' mapping")

    return {str(k): str(v) for k, v in env.items()}


def snapshot_metadata(path: str | Path) -> Dict[str, str]:
    """Return metadata (label, created_at, version) without the full env."""
    src = Path(path)
    if not src.exists():
        raise SnapshotError(f"Snapshot file not found: {src}")

    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"Invalid JSON in snapshot {src}: {exc}") from exc

    return {
        "version": str(data.get("version", "")),
        "label": str(data.get("label", "")),
        "created_at": str(data.get("created_at", "")),
    }
