"""Compare two DiffResult snapshots to detect changes over time."""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from envdiff.differ import DiffResult


@dataclass
class ComparisonResult:
    """Result of comparing two DiffResult snapshots."""

    resolved: List[str] = field(default_factory=list)
    """Keys that had mismatches before but are now matching."""

    introduced: List[str] = field(default_factory=list)
    """Keys that are newly mismatched or missing."""

    unchanged_issues: List[str] = field(default_factory=list)
    """Keys that still have the same issue in both snapshots."""

    @property
    def is_improved(self) -> bool:
        """Return True if issues were resolved without new ones introduced."""
        return len(self.resolved) > 0 and len(self.introduced) == 0

    @property
    def has_regressions(self) -> bool:
        """Return True if new issues were introduced."""
        return len(self.introduced) > 0

    def summary(self) -> str:
        parts = []
        if self.resolved:
            parts.append(f"{len(self.resolved)} resolved")
        if self.introduced:
            parts.append(f"{len(self.introduced)} introduced")
        if self.unchanged_issues:
            parts.append(f"{len(self.unchanged_issues)} unchanged")
        return ", ".join(parts) if parts else "no changes"


def _issue_keys(diff: DiffResult) -> Set[str]:
    """Return all keys that have any kind of mismatch or absence."""
    keys: Set[str] = set()
    keys.update(diff.only_in_left.keys())
    keys.update(diff.only_in_right.keys())
    keys.update(diff.value_mismatches.keys())
    return keys


def compare_diffs(before: DiffResult, after: DiffResult) -> ComparisonResult:
    """Compare two DiffResult objects and classify changes.

    Args:
        before: The earlier diff (baseline).
        after: The more recent diff.

    Returns:
        A ComparisonResult describing what changed between the two diffs.
    """
    before_issues = _issue_keys(before)
    after_issues = _issue_keys(after)

    resolved = sorted(before_issues - after_issues)
    introduced = sorted(after_issues - before_issues)
    unchanged = sorted(before_issues & after_issues)

    return ComparisonResult(
        resolved=resolved,
        introduced=introduced,
        unchanged_issues=unchanged,
    )
