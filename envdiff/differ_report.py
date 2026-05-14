"""Consolidated diff report combining stats, score, and recommendations."""

from dataclasses import dataclass, field
from typing import Optional

from envdiff.differ import DiffResult
from envdiff.differ_stats import DiffStats, compute_stats
from envdiff.scorer import ScoreResult, score_diff
from envdiff.recommender import RecommendationReport, recommend


@dataclass
class ConsolidatedReport:
    diff: DiffResult
    stats: DiffStats
    score: ScoreResult
    recommendations: RecommendationReport
    label_left: str = "left"
    label_right: str = "right"

    @property
    def has_issues(self) -> bool:
        return self.stats.total_issues > 0

    @property
    def is_healthy(self) -> bool:
        return self.score.grade in ("A", "B") and not self.recommendations.errors

    def summary(self) -> str:
        lines = [
            f"Diff Report: {self.label_left!r} vs {self.label_right!r}",
            f"  Grade   : {self.score.grade} ({self.score.score:.1f}/100)",
            f"  Total   : {self.stats.total_keys} keys",
            f"  Issues  : {self.stats.total_issues}",
            f"  Match % : {self.stats.match_rate:.1f}%",
        ]
        if self.recommendations.errors:
            lines.append(f"  Errors  : {len(self.recommendations.errors)}")
        if self.recommendations.warnings:
            lines.append(f"  Warnings: {len(self.recommendations.warnings)}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "labels": {"left": self.label_left, "right": self.label_right},
            "stats": self.stats.to_dict(),
            "score": {
                "score": self.score.score,
                "grade": self.score.grade,
            },
            "recommendations": {
                "errors": [str(r) for r in self.recommendations.errors],
                "warnings": [str(r) for r in self.recommendations.warnings],
            },
            "healthy": self.is_healthy,
        }


def build_report(
    diff: DiffResult,
    label_left: str = "left",
    label_right: str = "right",
) -> ConsolidatedReport:
    """Build a consolidated report from a DiffResult."""
    return ConsolidatedReport(
        diff=diff,
        stats=compute_stats(diff),
        score=score_diff(diff),
        recommendations=recommend(diff),
        label_left=label_left,
        label_right=label_right,
    )
