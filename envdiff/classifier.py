"""Classify diff entries by category: infrastructure, application, security, etc."""

from dataclasses import dataclass, field
from typing import Dict, List
from envdiff.differ import DiffResult

_CATEGORY_PATTERNS: Dict[str, List[str]] = {
    "security": ["secret", "password", "passwd", "token", "key", "auth", "cert", "private"],
    "database": ["db", "database", "mongo", "postgres", "mysql", "redis", "dsn", "jdbc"],
    "network": ["host", "port", "url", "uri", "endpoint", "proxy", "dns", "ip", "addr"],
    "logging": ["log", "logger", "loglevel", "log_level", "debug", "verbose"],
    "infrastructure": ["aws", "gcp", "azure", "region", "bucket", "cluster", "node", "pod"],
    "application": [],  # fallback
}


@dataclass
class ClassifiedDiff:
    categories: Dict[str, List[str]] = field(default_factory=dict)
    key_to_category: Dict[str, str] = field(default_factory=dict)

    def keys_in(self, category: str) -> List[str]:
        return self.categories.get(category, [])

    def all_categories(self) -> List[str]:
        return [c for c, keys in self.categories.items() if keys]


def _categorize_key(key: str) -> str:
    lower = key.lower()
    for category, patterns in _CATEGORY_PATTERNS.items():
        if category == "application":
            continue
        for pattern in patterns:
            if pattern in lower:
                return category
    return "application"


def classify_diff(diff: DiffResult) -> ClassifiedDiff:
    """Assign each key in the diff to a named category."""
    all_keys: List[str] = (
        list(diff.only_in_left.keys())
        + list(diff.only_in_right.keys())
        + list(diff.mismatches.keys())
        + list(diff.matching.keys())
    )

    categories: Dict[str, List[str]] = {c: [] for c in _CATEGORY_PATTERNS}
    key_to_category: Dict[str, str] = {}

    for key in all_keys:
        cat = _categorize_key(key)
        categories[cat].append(key)
        key_to_category[key] = cat

    return ClassifiedDiff(categories=categories, key_to_category=key_to_category)
