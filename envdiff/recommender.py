"""Recommender: suggest fixes for diff issues based on heuristics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.differ import DiffResult


@dataclass
class Recommendation:
    key: str
    issue: str
    suggestion: str
    severity: str  # "error", "warning", "info"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.suggestion}"


@dataclass
class RecommendationReport:
    recommendations: List[Recommendation] = field(default_factory=list)

    @property
    def errors(self) -> List[Recommendation]:
        return [r for r in self.recommendations if r.severity == "error"]

    @property
    def warnings(self) -> List[Recommendation]:
        return [r for r in self.recommendations if r.severity == "warning"]

    @property
    def infos(self) -> List[Recommendation]:
        return [r for r in self.recommendations if r.severity == "info"]

    def summary(self) -> str:
        e, w, i = len(self.errors), len(self.warnings), len(self.infos)
        return f"{e} error(s), {w} warning(s), {i} info(s)"


_SENSITIVE_SUBSTRINGS = ("password", "secret", "token", "key", "api", "auth")


def _looks_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(s in lower for s in _SENSITIVE_SUBSTRINGS)


def recommend(diff: DiffResult) -> RecommendationReport:
    """Analyse a DiffResult and produce actionable recommendations."""
    recs: List[Recommendation] = []

    for key in diff.only_in_left:
        severity = "error" if _looks_sensitive(key) else "warning"
        recs.append(Recommendation(
            key=key,
            issue="missing in right environment",
            suggestion=f"Add {key!r} to the right environment.",
            severity=severity,
        ))

    for key in diff.only_in_right:
        severity = "error" if _looks_sensitive(key) else "warning"
        recs.append(Recommendation(
            key=key,
            issue="missing in left environment",
            suggestion=f"Add {key!r} to the left environment.",
            severity=severity,
        ))

    for key, (lv, rv) in diff.value_mismatches.items():
        if _looks_sensitive(key):
            recs.append(Recommendation(
                key=key,
                issue="sensitive value mismatch",
                suggestion=f"Review and reconcile {key!r} — values differ and key appears sensitive.",
                severity="error",
            ))
        elif lv == "" or rv == "":
            recs.append(Recommendation(
                key=key,
                issue="one side has empty value",
                suggestion=f"{key!r} is empty on one side; ensure this is intentional.",
                severity="warning",
            ))
        else:
            recs.append(Recommendation(
                key=key,
                issue="value mismatch",
                suggestion=f"Align {key!r} across environments.",
                severity="info",
            ))

    return RecommendationReport(recommendations=recs)
