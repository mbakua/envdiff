"""Pivot a diff result into a key-centric view showing presence/value per environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult


@dataclass
class PivotRow:
    """A single key's status across two environments."""

    key: str
    left_value: Optional[str]
    right_value: Optional[str]
    status: str  # 'left_only' | 'right_only' | 'mismatch' | 'match'

    def __str__(self) -> str:
        lv = self.left_value if self.left_value is not None else "<absent>"
        rv = self.right_value if self.right_value is not None else "<absent>"
        return f"{self.key}: [{self.status}] left={lv!r} right={rv!r}"


@dataclass
class PivotTable:
    """Key-centric view of a DiffResult."""

    left_label: str
    right_label: str
    rows: List[PivotRow] = field(default_factory=list)

    def for_key(self, key: str) -> Optional[PivotRow]:
        """Return the PivotRow for *key*, or None if not present."""
        for row in self.rows:
            if row.key == key:
                return row
        return None

    def by_status(self, status: str) -> List[PivotRow]:
        """Return all rows whose status matches *status*."""
        return [r for r in self.rows if r.status == status]

    def to_dict(self) -> Dict:
        return {
            "left_label": self.left_label,
            "right_label": self.right_label,
            "rows": [
                {
                    "key": r.key,
                    "left_value": r.left_value,
                    "right_value": r.right_value,
                    "status": r.status,
                }
                for r in self.rows
            ],
        }


def pivot_diff(
    diff: DiffResult,
    left_label: str = "left",
    right_label: str = "right",
) -> PivotTable:
    """Convert a DiffResult into a PivotTable."""
    rows: List[PivotRow] = []

    for key in sorted(diff.only_in_left):
        rows.append(PivotRow(key=key, left_value=diff.only_in_left[key],
                             right_value=None, status="left_only"))

    for key in sorted(diff.only_in_right):
        rows.append(PivotRow(key=key, left_value=None,
                             right_value=diff.only_in_right[key], status="right_only"))

    for key in sorted(diff.value_mismatches):
        lv, rv = diff.value_mismatches[key]
        rows.append(PivotRow(key=key, left_value=lv, right_value=rv, status="mismatch"))

    for key in sorted(diff.matching_keys):
        val = diff.matching_keys[key]
        rows.append(PivotRow(key=key, left_value=val, right_value=val, status="match"))

    rows.sort(key=lambda r: r.key)
    return PivotTable(left_label=left_label, right_label=right_label, rows=rows)
