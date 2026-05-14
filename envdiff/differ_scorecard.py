"""Scorecard: aggregate multiple DiffResult instances into a ranked report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult
from envdiff.scorer import ScoreResult, score_diff


@dataclass
class ScorecardEntry:
    label: str
    score: ScoreResult

    def __str__(self) -> str:
        return f"{self.label}: {self.score.grade} ({self.score.score}/100)"


@dataclass
class DiffScorecard:
    entries: List[ScorecardEntry] = field(default_factory=list)

    def best(self) -> Optional[ScorecardEntry]:
        if not self.entries:
            return None
        return max(self.entries, key=lambda e: e.score.score)

    def worst(self) -> Optional[ScorecardEntry]:
        if not self.entries:
            return None
        return min(self.entries, key=lambda e: e.score.score)

    def average_score(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.score.score for e in self.entries) / len(self.entries)

    def ranked(self) -> List[ScorecardEntry]:
        return sorted(self.entries, key=lambda e: e.score.score, reverse=True)

    def to_dict(self) -> Dict:
        return {
            "entries": [
                {"label": e.label, "score": e.score.score, "grade": e.score.grade}
                for e in self.ranked()
            ],
            "average_score": round(self.average_score(), 2),
            "best": self.best().label if self.best() else None,
            "worst": self.worst().label if self.worst() else None,
        }


def build_scorecard(
    labeled_diffs: Dict[str, DiffResult],
) -> DiffScorecard:
    """Build a scorecard from a mapping of label -> DiffResult."""
    entries = [
        ScorecardEntry(label=label, score=score_diff(diff))
        for label, diff in labeled_diffs.items()
    ]
    return DiffScorecard(entries=entries)
