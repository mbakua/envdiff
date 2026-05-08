"""Redactor: replace sensitive env values with configurable placeholders."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Optional

from envdiff.differ import DiffResult

_SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api[_\-]?key", re.IGNORECASE),
    re.compile(r"private[_\-]?key", re.IGNORECASE),
    re.compile(r"auth", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
]

DEFAULT_PLACEHOLDER = "[REDACTED]"


@dataclass
class RedactedDiff:
    only_in_left: Dict[str, str] = field(default_factory=dict)
    only_in_right: Dict[str, str] = field(default_factory=dict)
    mismatches: Dict[str, tuple[str, str]] = field(default_factory=dict)
    matching: Dict[str, str] = field(default_factory=dict)
    redacted_keys: list[str] = field(default_factory=list)


def is_sensitive(key: str) -> bool:
    """Return True if *key* matches any known sensitive pattern."""
    return any(p.search(key) for p in _SENSITIVE_PATTERNS)


def _redact(value: str, placeholder: str) -> str:
    return placeholder


def redact_diff(
    diff: DiffResult,
    placeholder: str = DEFAULT_PLACEHOLDER,
    extra_keys: Optional[list[str]] = None,
) -> RedactedDiff:
    """Return a copy of *diff* with sensitive values replaced by *placeholder*.

    Parameters
    ----------
    diff:        Source DiffResult to redact.
    placeholder: String used in place of sensitive values.
    extra_keys:  Additional key names (case-insensitive) to treat as sensitive.
    """
    extra_patterns: list[re.Pattern[str]] = []
    for k in (extra_keys or []):
        extra_patterns.append(re.compile(re.escape(k), re.IGNORECASE))

    def _sensitive(key: str) -> bool:
        return is_sensitive(key) or any(p.search(key) for p in extra_patterns)

    redacted_keys: list[str] = []

    def _maybe(key: str, value: str) -> str:
        if _sensitive(key):
            if key not in redacted_keys:
                redacted_keys.append(key)
            return _redact(value, placeholder)
        return value

    only_in_left = {k: _maybe(k, v) for k, v in diff.only_in_left.items()}
    only_in_right = {k: _maybe(k, v) for k, v in diff.only_in_right.items()}
    matching = {k: _maybe(k, v) for k, v in diff.matching.items()}
    mismatches: Dict[str, tuple[str, str]] = {}
    for k, (lv, rv) in diff.mismatches.items():
        mismatches[k] = (_maybe(k, lv), _maybe(k, rv))

    return RedactedDiff(
        only_in_left=only_in_left,
        only_in_right=only_in_right,
        mismatches=mismatches,
        matching=matching,
        redacted_keys=sorted(set(redacted_keys)),
    )
