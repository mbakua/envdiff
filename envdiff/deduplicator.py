"""Detect and report duplicate or redundant keys across env sets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.differ import DiffResult


@dataclass
class DeduplicationReport:
    """Result of a deduplication scan over a pair of env dicts."""

    duplicates_left: List[str] = field(default_factory=list)
    duplicates_right: List[str] = field(default_factory=list)
    redundant_matches: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """True when no duplicates or redundant entries were found."""
        return (
            not self.duplicates_left
            and not self.duplicates_right
            and not self.redundant_matches
        )

    def summary(self) -> str:
        parts: List[str] = []
        if self.duplicates_left:
            parts.append(
                f"Left duplicates: {', '.join(sorted(self.duplicates_left))}"
            )
        if self.duplicates_right:
            parts.append(
                f"Right duplicates: {', '.join(sorted(self.duplicates_right))}"
            )
        if self.redundant_matches:
            parts.append(
                f"Redundant (identical in both): {', '.join(sorted(self.redundant_matches))}"
            )
        return "; ".join(parts) if parts else "No duplicates or redundant keys found."


def _find_duplicates(env: Dict[str, str]) -> List[str]:
    """Return keys that appear more than once (case-insensitive collision)."""
    seen: Dict[str, str] = {}
    dupes: List[str] = []
    for key in env:
        lower = key.lower()
        if lower in seen and seen[lower] != key:
            dupes.append(key)
        else:
            seen[lower] = key
    return dupes


def deduplicate_diff(
    left: Dict[str, str],
    right: Dict[str, str],
    diff: DiffResult,
) -> DeduplicationReport:
    """Analyse *left* and *right* envs for duplicate / redundant keys.

    A key is *redundant* when it appears in ``diff.matching_keys`` with
    identical values — it contributes no signal to the diff.
    """
    dupes_left = _find_duplicates(left)
    dupes_right = _find_duplicates(right)

    redundant = [
        k
        for k in diff.matching_keys
        if left.get(k) == right.get(k)
    ]

    return DeduplicationReport(
        duplicates_left=dupes_left,
        duplicates_right=dupes_right,
        redundant_matches=redundant,
    )
