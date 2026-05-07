"""Profile environment variable sets to produce summary statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.differ import DiffResult


@dataclass
class EnvProfile:
    """Statistical profile of an environment variable set."""

    total_keys: int = 0
    only_in_left: int = 0
    only_in_right: int = 0
    matching: int = 0
    mismatched: int = 0
    sensitive_keys: List[str] = field(default_factory=list)
    longest_key: str = ""
    longest_value_key: str = ""

    @property
    def coverage(self) -> float:
        """Fraction of keys present in both sides (0.0 – 1.0)."""
        if self.total_keys == 0:
            return 0.0
        return round((self.matching + self.mismatched) / self.total_keys, 4)

    def to_dict(self) -> Dict:
        return {
            "total_keys": self.total_keys,
            "only_in_left": self.only_in_left,
            "only_in_right": self.only_in_right,
            "matching": self.matching,
            "mismatched": self.mismatched,
            "coverage": self.coverage,
            "sensitive_keys": self.sensitive_keys,
            "longest_key": self.longest_key,
            "longest_value_key": self.longest_value_key,
        }


_SENSITIVE_HINTS = ("password", "secret", "token", "key", "auth", "credential")


def _is_sensitive(name: str) -> bool:
    lower = name.lower()
    return any(hint in lower for hint in _SENSITIVE_HINTS)


def profile_diff(diff: DiffResult) -> EnvProfile:
    """Derive an EnvProfile from a DiffResult."""
    all_keys = (
        set(diff.only_in_left)
        | set(diff.only_in_right)
        | set(diff.matching)
        | set(diff.mismatched)
    )

    sensitive = [k for k in all_keys if _is_sensitive(k)]

    longest_key = max(all_keys, key=len) if all_keys else ""

    # Determine which side has the longer value for mismatched keys
    longest_value_key = ""
    max_val_len = -1
    for k, (lv, rv) in diff.mismatched.items():
        for v in (lv, rv):
            if v and len(v) > max_val_len:
                max_val_len = len(v)
                longest_value_key = k
    for k, v in {**diff.only_in_left, **diff.only_in_right}.items():
        if v and len(v) > max_val_len:
            max_val_len = len(v)
            longest_value_key = k

    return EnvProfile(
        total_keys=len(all_keys),
        only_in_left=len(diff.only_in_left),
        only_in_right=len(diff.only_in_right),
        matching=len(diff.matching),
        mismatched=len(diff.mismatched),
        sensitive_keys=sorted(sensitive),
        longest_key=longest_key,
        longest_value_key=longest_value_key,
    )
