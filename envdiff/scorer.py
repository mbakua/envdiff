"""Score the health of an environment diff on a 0-100 scale."""

from dataclasses import dataclass
from typing import Optional

from envdiff.differ import DiffResult


@dataclass
class ScoreResult:
    """Holds the numeric score and a short grade label."""

    score: int  # 0-100
    grade: str  # A, B, C, D, F
    total_keys: int
    issue_count: int
    details: dict

    def __str__(self) -> str:
        return f"Score: {self.score}/100 ({self.grade}) — {self.issue_count} issue(s) across {self.total_keys} key(s)"


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def score_diff(diff: DiffResult, weights: Optional[dict] = None) -> ScoreResult:
    """Compute a health score for *diff*.

    Parameters
    ----------
    diff:
        The diff to score.
    weights:
        Optional mapping with keys ``missing``, ``extra``, ``mismatch``
        controlling how many points each issue type costs.  Defaults to
        ``{missing: 3, extra: 1, mismatch: 2}``.
    """
    if weights is None:
        weights = {"missing": 3, "extra": 1, "mismatch": 2}

    missing_penalty = len(diff.only_in_left) * weights.get("missing", 3)
    extra_penalty = len(diff.only_in_right) * weights.get("extra", 1)
    mismatch_penalty = len(diff.value_mismatches) * weights.get("mismatch", 2)

    total_penalty = missing_penalty + extra_penalty + mismatch_penalty

    all_keys = (
        set(diff.only_in_left)
        | set(diff.only_in_right)
        | set(diff.value_mismatches)
        | set(diff.matching_keys)
    )
    total_keys = len(all_keys)

    raw_score = max(0, 100 - total_penalty)
    score = min(100, raw_score)

    issue_count = len(diff.only_in_left) + len(diff.only_in_right) + len(diff.value_mismatches)

    details = {
        "missing_keys": len(diff.only_in_left),
        "extra_keys": len(diff.only_in_right),
        "mismatched_keys": len(diff.value_mismatches),
        "matching_keys": len(diff.matching_keys),
        "missing_penalty": missing_penalty,
        "extra_penalty": extra_penalty,
        "mismatch_penalty": mismatch_penalty,
    }

    return ScoreResult(
        score=score,
        grade=_grade(score),
        total_keys=total_keys,
        issue_count=issue_count,
        details=details,
    )
