"""Annotate diff entries with human-readable notes and context hints."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult


@dataclass
class Annotation:
    key: str
    note: str
    severity: str = "info"  # info | warning | error

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.note}"


@dataclass
class AnnotatedDiff:
    diff: DiffResult
    annotations: List[Annotation] = field(default_factory=list)

    def for_key(self, key: str) -> List[Annotation]:
        return [a for a in self.annotations if a.key == key]

    def by_severity(self, severity: str) -> List[Annotation]:
        return [a for a in self.annotations if a.severity == severity]

    def has_errors(self) -> bool:
        return any(a.severity == "error" for a in self.annotations)


_SENSITIVE_HINTS = ("secret", "password", "token", "key", "auth", "credential")
_NETWORK_HINTS = ("host", "url", "port", "endpoint", "addr")


def _infer_note(key: str, context: str) -> Optional[str]:
    lower = key.lower()
    if context == "missing_right":
        if any(h in lower for h in _SENSITIVE_HINTS):
            return "Sensitive key absent in target environment — possible security gap"
        if any(h in lower for h in _NETWORK_HINTS):
            return "Network config key missing in target — connectivity may break"
        return "Key present in source but not in target"
    if context == "missing_left":
        return "Key exists only in target — may be an undocumented addition"
    if context == "mismatch":
        if any(h in lower for h in _SENSITIVE_HINTS):
            return "Secret value differs between environments"
        return "Value mismatch between environments"
    return None


def _severity_for(key: str, context: str) -> str:
    lower = key.lower()
    if context == "missing_right" and any(h in lower for h in _SENSITIVE_HINTS):
        return "error"
    if context == "mismatch" and any(h in lower for h in _SENSITIVE_HINTS):
        return "error"
    if context in ("missing_right", "mismatch"):
        return "warning"
    return "info"


def annotate_diff(
    diff: DiffResult,
    extra: Optional[Dict[str, str]] = None,
) -> AnnotatedDiff:
    """Produce an AnnotatedDiff from a DiffResult with auto-generated notes."""
    annotations: List[Annotation] = []

    for key in diff.only_in_left:
        note = _infer_note(key, "missing_right")
        if note:
            annotations.append(Annotation(key, note, _severity_for(key, "missing_right")))

    for key in diff.only_in_right:
        note = _infer_note(key, "missing_left")
        if note:
            annotations.append(Annotation(key, note, _severity_for(key, "missing_left")))

    for key in diff.value_mismatches:
        note = _infer_note(key, "mismatch")
        if note:
            annotations.append(Annotation(key, note, _severity_for(key, "mismatch")))

    if extra:
        for key, custom_note in extra.items():
            annotations.append(Annotation(key, custom_note, "info"))

    return AnnotatedDiff(diff=diff, annotations=annotations)
