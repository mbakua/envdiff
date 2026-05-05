"""Filter utilities for environment variable diff results."""

from __future__ import annotations

import re
from typing import Iterable

from envdiff.differ import DiffResult


def filter_by_prefix(diff: DiffResult, prefix: str) -> DiffResult:
    """Return a new DiffResult containing only keys that start with *prefix*."""
    prefix_upper = prefix.upper()

    return DiffResult(
        only_in_left={
            k: v for k, v in diff.only_in_left.items()
            if k.upper().startswith(prefix_upper)
        },
        only_in_right={
            k: v for k, v in diff.only_in_right.items()
            if k.upper().startswith(prefix_upper)
        },
        value_mismatches={
            k: v for k, v in diff.value_mismatches.items()
            if k.upper().startswith(prefix_upper)
        },
        matching_keys={
            k for k in diff.matching_keys
            if k.upper().startswith(prefix_upper)
        },
    )


def filter_by_pattern(diff: DiffResult, pattern: str) -> DiffResult:
    """Return a new DiffResult containing only keys matching *pattern* (regex)."""
    compiled = re.compile(pattern, re.IGNORECASE)

    def _match(key: str) -> bool:
        return bool(compiled.search(key))

    return DiffResult(
        only_in_left={k: v for k, v in diff.only_in_left.items() if _match(k)},
        only_in_right={k: v for k, v in diff.only_in_right.items() if _match(k)},
        value_mismatches={k: v for k, v in diff.value_mismatches.items() if _match(k)},
        matching_keys={k for k in diff.matching_keys if _match(k)},
    )


def exclude_keys(diff: DiffResult, keys: Iterable[str]) -> DiffResult:
    """Return a new DiffResult with the specified *keys* removed entirely."""
    excluded = {k.upper() for k in keys}

    def _keep(key: str) -> bool:
        return key.upper() not in excluded

    return DiffResult(
        only_in_left={k: v for k, v in diff.only_in_left.items() if _keep(k)},
        only_in_right={k: v for k, v in diff.only_in_right.items() if _keep(k)},
        value_mismatches={k: v for k, v in diff.value_mismatches.items() if _keep(k)},
        matching_keys={k for k in diff.matching_keys if _keep(k)},
    )
