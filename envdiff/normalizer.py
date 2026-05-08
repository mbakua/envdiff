"""Normalize environment variable dicts before comparison."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class NormalizeOptions:
    strip_whitespace: bool = True
    lowercase_keys: bool = False
    uppercase_keys: bool = False
    remove_empty: bool = False
    default_value: Optional[str] = None


def _normalize_key(key: str, opts: NormalizeOptions) -> str:
    if opts.strip_whitespace:
        key = key.strip()
    if opts.lowercase_keys:
        return key.lower()
    if opts.uppercase_keys:
        return key.upper()
    return key


def _normalize_value(value: str, opts: NormalizeOptions) -> str:
    if opts.strip_whitespace:
        value = value.strip()
    return value


def normalize_env(
    env: Dict[str, str],
    opts: Optional[NormalizeOptions] = None,
) -> Dict[str, str]:
    """Return a normalized copy of *env* according to *opts*."""
    if opts is None:
        opts = NormalizeOptions()

    result: Dict[str, str] = {}
    for raw_key, raw_value in env.items():
        key = _normalize_key(raw_key, opts)
        value = _normalize_value(raw_value, opts)

        if opts.remove_empty and value == "":
            continue

        result[key] = value

    if opts.default_value is not None:
        # Fill missing keys that ended up empty with the default
        result = {
            k: (v if v != "" else opts.default_value)
            for k, v in result.items()
        }

    return result


def normalize_pair(
    left: Dict[str, str],
    right: Dict[str, str],
    opts: Optional[NormalizeOptions] = None,
) -> tuple[Dict[str, str], Dict[str, str]]:
    """Normalize both sides of a comparison consistently."""
    return normalize_env(left, opts), normalize_env(right, opts)
