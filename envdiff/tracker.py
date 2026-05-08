"""Track which environment keys have changed between multiple diff snapshots over time."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult


@dataclass
class KeyHistory:
    key: str
    appearances: List[str] = field(default_factory=list)  # list of stage/label names
    statuses: List[str] = field(default_factory=list)     # 'left_only','right_only','mismatch','match'

    @property
    def change_count(self) -> int:
        return sum(1 for s in self.statuses if s != "match")

    @property
    def is_stable(self) -> bool:
        return self.change_count == 0


@dataclass
class TrackingReport:
    entries: Dict[str, KeyHistory] = field(default_factory=dict)

    @property
    def unstable_keys(self) -> List[str]:
        return [k for k, h in self.entries.items() if not h.is_stable]

    @property
    def stable_keys(self) -> List[str]:
        return [k for k, h in self.entries.items() if h.is_stable]

    def summary(self) -> str:
        total = len(self.entries)
        unstable = len(self.unstable_keys)
        stable = len(self.stable_keys)
        return f"Tracked {total} keys: {stable} stable, {unstable} unstable."


def track_diffs(labeled_diffs: List[tuple[str, DiffResult]]) -> TrackingReport:
    """Build a TrackingReport from a sequence of (label, DiffResult) pairs."""
    report = TrackingReport()

    for label, diff in labeled_diffs:
        for key in diff.only_in_left:
            _record(report, key, label, "left_only")
        for key in diff.only_in_right:
            _record(report, key, label, "right_only")
        for key in diff.value_mismatches:
            _record(report, key, label, "mismatch")
        for key in diff.matching_keys:
            _record(report, key, label, "match")

    return report


def _record(report: TrackingReport, key: str, label: str, status: str) -> None:
    if key not in report.entries:
        report.entries[key] = KeyHistory(key=key)
    report.entries[key].appearances.append(label)
    report.entries[key].statuses.append(status)
