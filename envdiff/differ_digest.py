"""Digest module: produce a compact fingerprint summary of a DiffResult."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import List

from envdiff.differ import DiffResult


@dataclass
class DiffDigest:
    """Compact fingerprint of a DiffResult."""

    fingerprint: str
    total_keys: int
    issue_keys: List[str] = field(default_factory=list)
    is_clean: bool = False

    def __str__(self) -> str:  # pragma: no cover
        status = "clean" if self.is_clean else "dirty"
        return (
            f"DiffDigest(fingerprint={self.fingerprint[:12]}…, "
            f"total={self.total_keys}, status={status})"
        )


def _collect_issue_keys(diff: DiffResult) -> List[str]:
    """Return sorted list of keys that appear in any problem category."""
    keys: set[str] = set()
    keys.update(diff.only_in_left)
    keys.update(diff.only_in_right)
    keys.update(diff.value_mismatches.keys())
    return sorted(keys)


def _fingerprint(diff: DiffResult) -> str:
    """Produce a stable SHA-256 hex fingerprint from the diff contents."""
    payload = {
        "only_in_left": sorted(diff.only_in_left),
        "only_in_right": sorted(diff.only_in_right),
        "value_mismatches": {
            k: list(v) for k, v in sorted(diff.value_mismatches.items())
        },
        "matching_keys": sorted(diff.matching_keys),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def digest_diff(diff: DiffResult) -> DiffDigest:
    """Compute a DiffDigest from a DiffResult."""
    issue_keys = _collect_issue_keys(diff)
    all_keys: set[str] = set()
    all_keys.update(diff.only_in_left)
    all_keys.update(diff.only_in_right)
    all_keys.update(diff.value_mismatches.keys())
    all_keys.update(diff.matching_keys)
    return DiffDigest(
        fingerprint=_fingerprint(diff),
        total_keys=len(all_keys),
        issue_keys=issue_keys,
        is_clean=len(issue_keys) == 0,
    )
