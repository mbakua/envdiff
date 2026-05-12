"""Map environment variable keys to human-readable aliases and resolve them back."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult


@dataclass
class AliasMap:
    """Bidirectional mapping between raw env keys and their aliases."""

    _forward: Dict[str, str] = field(default_factory=dict)  # key -> alias
    _reverse: Dict[str, str] = field(default_factory=dict)  # alias -> key

    def add(self, key: str, alias: str) -> None:
        """Register a key/alias pair."""
        self._forward[key] = alias
        self._reverse[alias] = key

    def alias_for(self, key: str) -> Optional[str]:
        """Return the alias for *key*, or None if unmapped."""
        return self._forward.get(key)

    def key_for(self, alias: str) -> Optional[str]:
        """Return the raw key for *alias*, or None if unmapped."""
        return self._reverse.get(alias)

    def all_keys(self) -> List[str]:
        return list(self._forward.keys())

    def all_aliases(self) -> List[str]:
        return list(self._reverse.keys())


def load_alias_map(mapping: Dict[str, str]) -> AliasMap:
    """Build an :class:`AliasMap` from a plain *key -> alias* dict."""
    am = AliasMap()
    for key, alias in mapping.items():
        am.add(key, alias)
    return am


def apply_aliases(diff: DiffResult, alias_map: AliasMap) -> DiffResult:
    """Return a new :class:`DiffResult` with keys replaced by their aliases.

    Keys that have no alias entry are left unchanged.
    """

    def _rename(d: Dict[str, str]) -> Dict[str, str]:
        return {alias_map.alias_for(k) or k: v for k, v in d.items()}

    def _rename_keys(keys: List[str]) -> List[str]:
        return [alias_map.alias_for(k) or k for k in keys]

    return DiffResult(
        only_in_left=_rename(diff.only_in_left),
        only_in_right=_rename(diff.only_in_right),
        value_mismatches={
            alias_map.alias_for(k) or k: v for k, v in diff.value_mismatches.items()
        },
        matching_keys=_rename_keys(diff.matching_keys),
    )
