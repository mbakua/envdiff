"""Masking utilities for sensitive environment variable values."""

import re
from typing import FrozenSet

from envdiff.differ import DiffResult

# Default patterns that indicate a value should be masked
_SENSITIVE_PATTERNS: tuple[str, ...] = (
    r".*secret.*",
    r".*password.*",
    r".*passwd.*",
    r".*token.*",
    r".*api[_-]?key.*",
    r".*private[_-]?key.*",
    r".*auth.*",
    r".*credential.*",
)

MASK = "***"


def _is_sensitive(key: str, patterns: tuple[str, ...] = _SENSITIVE_PATTERNS) -> bool:
    """Return True if the key matches any sensitive pattern (case-insensitive)."""
    lower = key.lower()
    return any(re.fullmatch(p, lower) for p in patterns)


def mask_value(key: str, value: str | None, patterns: tuple[str, ...] = _SENSITIVE_PATTERNS) -> str | None:
    """Return MASK if the key is sensitive, otherwise return value unchanged."""
    if value is None:
        return None
    return MASK if _is_sensitive(key, patterns) else value


def mask_diff(
    diff: DiffResult,
    patterns: tuple[str, ...] = _SENSITIVE_PATTERNS,
    extra_keys: FrozenSet[str] = frozenset(),
) -> DiffResult:
    """Return a new DiffResult with sensitive values replaced by MASK."""

    def should_mask(key: str) -> bool:
        return _is_sensitive(key, patterns) or key in extra_keys

    masked_left = {
        k: (MASK if should_mask(k) else v)
        for k, v in diff.only_in_left.items()
    }
    masked_right = {
        k: (MASK if should_mask(k) else v)
        for k, v in diff.only_in_right.items()
    }
    masked_mismatches = {
        k: (
            MASK if should_mask(k) else lv,
            MASK if should_mask(k) else rv,
        )
        for k, (lv, rv) in diff.value_mismatches.items()
    }

    return DiffResult(
        only_in_left=masked_left,
        only_in_right=masked_right,
        value_mismatches=masked_mismatches,
        matching_keys=diff.matching_keys,
    )
