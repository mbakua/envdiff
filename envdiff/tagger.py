"""Tag environment variable keys with semantic labels for categorization."""

from dataclasses import dataclass, field
from typing import Dict, List, Set
from envdiff.differ import DiffResult

# Built-in tag patterns: (tag_name, key_substrings)
_BUILTIN_TAGS: List[tuple] = [
    ("secret", ["secret", "password", "passwd", "token", "api_key", "apikey", "private_key"]),
    ("database", ["db_", "database", "postgres", "mysql", "mongo", "redis", "dsn"]),
    ("network", ["host", "port", "url", "endpoint", "addr", "address", "proxy"]),
    ("logging", ["log", "logger", "loglevel", "log_level", "debug", "verbose"]),
    ("feature", ["feature", "flag", "enable", "disable", "toggle"]),
    ("aws", ["aws_", "s3_", "ec2_", "iam_", "lambda_"]),
]


@dataclass
class TaggedDiff:
    tags: Dict[str, Set[str]] = field(default_factory=dict)  # tag -> set of keys
    key_tags: Dict[str, List[str]] = field(default_factory=dict)  # key -> list of tags

    def keys_for_tag(self, tag: str) -> Set[str]:
        return self.tags.get(tag, set())

    def tags_for_key(self, key: str) -> List[str]:
        return self.key_tags.get(key, [])

    def all_tags(self) -> List[str]:
        return sorted(self.tags.keys())


def _tags_for_key(key: str, extra_tags: Dict[str, List[str]] = None) -> List[str]:
    """Return all matching tags for a given key name."""
    lower = key.lower()
    matched: List[str] = []

    for tag, patterns in _BUILTIN_TAGS:
        if any(p in lower for p in patterns):
            matched.append(tag)

    if extra_tags:
        for tag, patterns in extra_tags.items():
            if any(p.lower() in lower for p in patterns):
                if tag not in matched:
                    matched.append(tag)

    return matched


def tag_diff(diff: DiffResult, extra_tags: Dict[str, List[str]] = None) -> TaggedDiff:
    """Assign semantic tags to all keys present in a DiffResult."""
    all_keys: Set[str] = (
        set(diff.only_in_left)
        | set(diff.only_in_right)
        | set(diff.value_mismatches)
        | set(diff.matching_keys)
    )

    tags: Dict[str, Set[str]] = {}
    key_tags: Dict[str, List[str]] = {}

    for key in sorted(all_keys):
        matched = _tags_for_key(key, extra_tags)
        key_tags[key] = matched
        for tag in matched:
            tags.setdefault(tag, set()).add(key)

    return TaggedDiff(tags=tags, key_tags=key_tags)
