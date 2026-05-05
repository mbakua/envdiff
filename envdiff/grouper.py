"""Group DiffResult entries by status category."""

from dataclasses import dataclass, field
from typing import Iterator

from envdiff.differ import DiffResult


@dataclass
class GroupedDiff:
    only_in_left: DiffResult = field(default_factory=DiffResult)
    only_in_right: DiffResult = field(default_factory=DiffResult)
    mismatches: DiffResult = field(default_factory=DiffResult)
    matches: DiffResult = field(default_factory=DiffResult)

    def non_empty_groups(self) -> Iterator[tuple[str, DiffResult]]:
        """Yield (label, DiffResult) pairs for groups that have entries."""
        pairs = [
            ("only_in_left", self.only_in_left),
            ("only_in_right", self.only_in_right),
            ("mismatches", self.mismatches),
            ("matches", self.matches),
        ]
        for label, group in pairs:
            if group:
                yield label, group

    def total(self) -> int:
        return (
            len(self.only_in_left)
            + len(self.only_in_right)
            + len(self.mismatches)
            + len(self.matches)
        )


def group_diff(diff: DiffResult) -> GroupedDiff:
    """Partition a DiffResult into four status-based groups."""
    only_left: dict = {}
    only_right: dict = {}
    mismatches: dict = {}
    matches: dict = {}

    for key, entry in diff.items():
        left = entry.get("left")
        right = entry.get("right")

        if left is None:
            only_right[key] = entry
        elif right is None:
            only_left[key] = entry
        elif left != right:
            mismatches[key] = entry
        else:
            matches[key] = entry

    return GroupedDiff(
        only_in_left=DiffResult(only_left),
        only_in_right=DiffResult(only_right),
        mismatches=DiffResult(mismatches),
        matches=DiffResult(matches),
    )
