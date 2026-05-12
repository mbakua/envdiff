"""Timeline diff: track how a single key's value evolves across ordered snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TimelineEntry:
    label: str
    value: Optional[str]  # None means the key was absent

    def __str__(self) -> str:
        val = self.value if self.value is not None else "<absent>"
        return f"{self.label}: {val}"


@dataclass
class KeyTimeline:
    key: str
    entries: List[TimelineEntry] = field(default_factory=list)

    def change_points(self) -> List[str]:
        """Return labels where the value changed from the previous snapshot."""
        changes: List[str] = []
        for i in range(1, len(self.entries)):
            if self.entries[i].value != self.entries[i - 1].value:
                changes.append(self.entries[i].label)
        return changes

    def is_stable(self) -> bool:
        return len(self.change_points()) == 0

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "stable": self.is_stable(),
            "change_points": self.change_points(),
            "entries": [{"label": e.label, "value": e.value} for e in self.entries],
        }


@dataclass
class TimelineReport:
    timelines: Dict[str, KeyTimeline] = field(default_factory=dict)

    def unstable_keys(self) -> List[str]:
        return [k for k, t in self.timelines.items() if not t.is_stable()]

    def stable_keys(self) -> List[str]:
        return [k for k, t in self.timelines.items() if t.is_stable()]

    def to_dict(self) -> dict:
        return {
            "total_keys": len(self.timelines),
            "unstable_count": len(self.unstable_keys()),
            "stable_count": len(self.stable_keys()),
            "timelines": {k: t.to_dict() for k, t in self.timelines.items()},
        }


def build_timeline(snapshots: List[Dict[str, Optional[str]]], labels: List[str]) -> TimelineReport:
    """Build a timeline report from an ordered list of env dicts and their labels."""
    if len(snapshots) != len(labels):
        raise ValueError("snapshots and labels must have the same length")

    all_keys: set = set()
    for snap in snapshots:
        all_keys.update(snap.keys())

    report = TimelineReport()
    for key in sorted(all_keys):
        entries = [
            TimelineEntry(label=label, value=snap.get(key))
            for snap, label in zip(snapshots, labels)
        ]
        report.timelines[key] = KeyTimeline(key=key, entries=entries)

    return report
