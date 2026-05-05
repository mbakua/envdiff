"""Sorting and ordering utilities for DiffResult entries."""

from enum import Enum
from typing import Callable

from envdiff.differ import DiffResult


class SortKey(str, Enum):
    NAME = "name"
    STATUS = "status"
    LEFT = "left"
    RIGHT = "right"


_STATUS_ORDER = {
    "only_in_left": 0,
    "only_in_right": 1,
    "mismatch": 2,
    "match": 3,
}


def _key_by_name(item: tuple) -> str:
    return item[0].lower()


def _key_by_status(item: tuple) -> tuple:
    key, entry = item
    status = _resolve_status(entry)
    return (_STATUS_ORDER.get(status, 99), key.lower())


def _key_by_left(item: tuple) -> tuple:
    _, entry = item
    val = entry.get("left") or ""
    return (val.lower(), item[0].lower())


def _key_by_right(item: tuple) -> tuple:
    _, entry = item
    val = entry.get("right") or ""
    return (val.lower(), item[0].lower())


def _resolve_status(entry: dict) -> str:
    if entry.get("left") is None:
        return "only_in_right"
    if entry.get("right") is None:
        return "only_in_left"
    if entry["left"] != entry["right"]:
        return "mismatch"
    return "match"


_KEY_FUNCS: dict[SortKey, Callable] = {
    SortKey.NAME: _key_by_name,
    SortKey.STATUS: _key_by_status,
    SortKey.LEFT: _key_by_left,
    SortKey.RIGHT: _key_by_right,
}


def sort_diff(
    diff: DiffResult,
    by: SortKey = SortKey.NAME,
    reverse: bool = False,
) -> DiffResult:
    """Return a new DiffResult with entries sorted by the given key."""
    key_func = _KEY_FUNCS[by]
    sorted_items = sorted(diff.items(), key=key_func, reverse=reverse)
    return DiffResult(sorted_items)
