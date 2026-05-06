"""Validate environment variable sets against required key schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional


@dataclass(frozen=True)
class ValidationResult:
    missing_keys: FrozenSet[str]
    extra_keys: FrozenSet[str]
    is_valid: bool

    @property
    def summary(self) -> str:
        parts: List[str] = []
        if self.missing_keys:
            parts.append(f"missing={len(self.missing_keys)}")
        if self.extra_keys:
            parts.append(f"extra={len(self.extra_keys)}")
        if not parts:
            return "OK"
        return ", ".join(parts)


def validate_required(
    env: Dict[str, str],
    required: FrozenSet[str],
    *,
    strict: bool = False,
) -> ValidationResult:
    """Check *env* against a set of *required* keys.

    Parameters
    ----------
    env:
        The environment mapping to validate.
    required:
        Keys that must be present in *env*.
    strict:
        When ``True``, keys in *env* that are not in *required* are
        reported as *extra_keys*.
    """
    present = frozenset(env.keys())
    missing = required - present
    extra = (present - required) if strict else frozenset()
    return ValidationResult(
        missing_keys=missing,
        extra_keys=extra,
        is_valid=(len(missing) == 0 and len(extra) == 0),
    )


def load_schema(path: str) -> FrozenSet[str]:
    """Load a newline-separated list of required key names from *path*.

    Lines starting with ``#`` and blank lines are ignored.
    """
    keys: List[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            keys.append(line)
    return frozenset(keys)
