"""Apply a diff result as a patch to produce a merged env dict."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envdiff.differ import DiffResult


class PatchStrategy(str, Enum):
    """How to resolve each category of diff entry when patching."""

    ADD_MISSING = "add_missing"       # add keys only_in_left into target
    OVERWRITE = "overwrite"           # also overwrite mismatched values
    FULL = "full"                     # add missing + overwrite + remove extras


@dataclass
class PatchResult:
    """Outcome of applying a patch."""

    patched: Dict[str, str]
    added: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

    @property
    def change_count(self) -> int:
        return len(self.added) + len(self.overwritten) + len(self.removed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.overwritten:
            parts.append(f"{len(self.overwritten)} overwritten")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if not parts:
            return "no changes applied"
        return ", ".join(parts)


def patch_env(
    target: Dict[str, str],
    diff: DiffResult,
    strategy: PatchStrategy = PatchStrategy.ADD_MISSING,
    exclude: Optional[List[str]] = None,
) -> PatchResult:
    """Return a new env dict with *diff* applied to *target*.

    The diff is treated as "left is authoritative": keys only in left are
    candidates for addition, mismatches use the left value, and keys only in
    right are candidates for removal (FULL strategy only).
    """
    exclude_set = set(exclude or [])
    patched = dict(target)
    added: List[str] = []
    overwritten: List[str] = []
    removed: List[str] = []

    # Add keys that exist in left but not in target
    for key, value in diff.only_in_left.items():
        if key in exclude_set:
            continue
        patched[key] = value
        added.append(key)

    # Handle mismatched values (left value wins)
    if strategy in (PatchStrategy.OVERWRITE, PatchStrategy.FULL):
        for key, (left_val, _right_val) in diff.mismatches.items():
            if key in exclude_set:
                continue
            patched[key] = left_val
            overwritten.append(key)

    # Remove keys that are only in right (i.e. not in left)
    if strategy == PatchStrategy.FULL:
        for key in list(diff.only_in_right.keys()):
            if key in exclude_set:
                continue
            patched.pop(key, None)
            removed.append(key)

    return PatchResult(
        patched=patched,
        added=added,
        overwritten=overwritten,
        removed=removed,
    )
