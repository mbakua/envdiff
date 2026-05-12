"""Heatmap: rank keys by how frequently they differ across multiple diff results."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict

from envdiff.differ import DiffResult


@dataclass
class HeatmapEntry:
    key: str
    diff_count: int
    total: int

    @property
    def frequency(self) -> float:
        """Fraction of diffs in which this key appeared as a mismatch."""
        if self.total == 0:
            return 0.0
        return self.diff_count / self.total

    def __str__(self) -> str:
        return f"{self.key}: {self.diff_count}/{self.total} ({self.frequency:.0%})"


@dataclass
class DiffHeatmap:
    entries: List[HeatmapEntry] = field(default_factory=list)
    total_diffs: int = 0

    def hottest(self, n: int = 5) -> List[HeatmapEntry]:
        """Return the top-n most frequently differing keys."""
        return sorted(self.entries, key=lambda e: e.frequency, reverse=True)[:n]

    def to_dict(self) -> Dict:
        return {
            "total_diffs": self.total_diffs,
            "entries": [
                {"key": e.key, "diff_count": e.diff_count, "frequency": round(e.frequency, 4)}
                for e in self.entries
            ],
        }


def build_heatmap(diffs: List[DiffResult]) -> DiffHeatmap:
    """Aggregate multiple DiffResult objects into a frequency heatmap."""
    total = len(diffs)
    counter: Counter = Counter()

    for dr in diffs:
        problem_keys = (
            set(dr.only_in_left)
            | set(dr.only_in_right)
            | set(dr.value_mismatches)
        )
        for key in problem_keys:
            counter[key] += 1

    entries = [
        HeatmapEntry(key=key, diff_count=count, total=total)
        for key, count in counter.most_common()
    ]
    return DiffHeatmap(entries=entries, total_diffs=total)
