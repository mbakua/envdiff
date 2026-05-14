"""Compute a delta (change summary) between two snapshots of DiffResults."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult


@dataclass
class DeltaEntry:
    key: str
    before: Optional[str]  # None means key was absent
    after: Optional[str]   # None means key was removed

    @property
    def status(self) -> str:
        if self.before is None:
            return "added"
        if self.after is None:
            return "removed"
        return "changed"

    def __str__(self) -> str:
        return f"{self.key}: {self.before!r} -> {self.after!r} ({self.status})"


@dataclass
class SnapshotDelta:
    added: List[DeltaEntry] = field(default_factory=list)
    removed: List[DeltaEntry] = field(default_factory=list)
    changed: List[DeltaEntry] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)

    def summary(self) -> str:
        if self.is_empty:
            return "No changes between snapshots."
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        return ", ".join(parts)

    def to_dict(self) -> Dict:
        return {
            "added": [{"key": e.key, "after": e.after} for e in self.added],
            "removed": [{"key": e.key, "before": e.before} for e in self.removed],
            "changed": [{"key": e.key, "before": e.before, "after": e.after} for e in self.changed],
        }


def _left_values(diff: DiffResult) -> Dict[str, Optional[str]]:
    """Flatten a DiffResult into {key: left_value_or_None}."""
    result: Dict[str, Optional[str]] = {}
    for k in diff.only_in_left:
        result[k] = diff.left.get(k)
    for k in diff.only_in_right:
        result[k] = None
    for k, (lv, _rv) in diff.value_mismatches.items():
        result[k] = lv
    for k in diff.matching_keys:
        result[k] = diff.left.get(k)
    return result


def compute_snapshot_delta(before: DiffResult, after: DiffResult) -> SnapshotDelta:
    """Return a SnapshotDelta describing how the left-side env changed."""
    before_vals = _left_values(before)
    after_vals = _left_values(after)

    all_keys = set(before_vals) | set(after_vals)
    delta = SnapshotDelta()

    for key in sorted(all_keys):
        bv = before_vals.get(key)
        av = after_vals.get(key)
        if key not in before_vals:
            delta.added.append(DeltaEntry(key=key, before=None, after=av))
        elif key not in after_vals:
            delta.removed.append(DeltaEntry(key=key, before=bv, after=None))
        elif bv != av:
            delta.changed.append(DeltaEntry(key=key, before=bv, after=av))

    return delta
