"""Generate a human-readable changelog from a sequence of DiffResults."""

from dataclasses import dataclass, field
from typing import List, Optional

from envdiff.differ import DiffResult


@dataclass
class ChangelogEntry:
    label: str
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def __str__(self) -> str:
        lines = [f"[{self.label}]"]
        for k in sorted(self.added):
            lines.append(f"  + {k}")
        for k in sorted(self.removed):
            lines.append(f"  - {k}")
        for k in sorted(self.changed):
            lines.append(f"  ~ {k}")
        if self.is_empty():
            lines.append("  (no changes)")
        return "\n".join(lines)


@dataclass
class DiffChangelog:
    entries: List[ChangelogEntry] = field(default_factory=list)

    def total_changes(self) -> int:
        return sum(
            len(e.added) + len(e.removed) + len(e.changed)
            for e in self.entries
        )

    def non_empty_entries(self) -> List[ChangelogEntry]:
        return [e for e in self.entries if not e.is_empty()]

    def __str__(self) -> str:
        if not self.entries:
            return "(empty changelog)"
        return "\n\n".join(str(e) for e in self.entries)


def build_changelog(
    diffs: List[DiffResult],
    labels: Optional[List[str]] = None,
) -> DiffChangelog:
    """Build a DiffChangelog from an ordered list of DiffResult snapshots.

    Each consecutive pair of diffs is compared to produce a ChangelogEntry
    describing what keys were added, removed, or changed between them.

    Args:
        diffs: Ordered list of DiffResult objects (oldest first).
        labels: Optional labels for each transition. Length must be
                len(diffs) - 1 when provided.

    Returns:
        A DiffChangelog instance.
    """
    if len(diffs) < 2:
        return DiffChangelog()

    if labels is not None and len(labels) != len(diffs) - 1:
        raise ValueError(
            f"Expected {len(diffs) - 1} labels for {len(diffs)} diffs, "
            f"got {len(labels)}."
        )

    entries: List[ChangelogEntry] = []

    for i in range(len(diffs) - 1):
        prev = diffs[i]
        curr = diffs[i + 1]
        label = labels[i] if labels else f"step-{i + 1}"

        prev_all = dict(
            **{k: v for k, v in prev.value_mismatches.items()},
            **{k: prev.left.get(k, "") for k in prev.only_in_left},
            **{k: prev.right.get(k, "") for k in prev.only_in_right},
        )
        curr_all = dict(
            **{k: v for k, v in curr.value_mismatches.items()},
            **{k: curr.left.get(k, "") for k in curr.only_in_left},
            **{k: curr.right.get(k, "") for k in curr.only_in_right},
        )

        prev_keys = (
            set(prev.only_in_left)
            | set(prev.only_in_right)
            | set(prev.value_mismatches)
        )
        curr_keys = (
            set(curr.only_in_left)
            | set(curr.only_in_right)
            | set(curr.value_mismatches)
        )

        added = sorted(curr_keys - prev_keys)
        removed = sorted(prev_keys - curr_keys)
        changed = sorted(
            k for k in curr_keys & prev_keys if curr_all.get(k) != prev_all.get(k)
        )

        entries.append(ChangelogEntry(label=label, added=added, removed=removed, changed=changed))

    return DiffChangelog(entries=entries)
