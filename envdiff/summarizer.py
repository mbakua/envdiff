"""Summarizer: produce a human-readable summary report from a DiffResult."""

from dataclasses import dataclass, field
from typing import List

from envdiff.differ import DiffResult
from envdiff.masker import mask_diff


@dataclass
class SummaryReport:
    total_keys: int
    matching: int
    only_in_left: int
    only_in_right: int
    mismatches: int
    lines: List[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return (self.only_in_left + self.only_in_right + self.mismatches) > 0

    def __str__(self) -> str:
        return "\n".join(self.lines)


def _section(title: str, items: dict, label_left: str, label_right: str) -> List[str]:
    if not items:
        return []
    lines = [f"  [{title}]"]
    for key, (lv, rv) in items.items():
        left_part = f"{label_left}={lv!r}" if lv is not None else ""
        right_part = f"{label_right}={rv!r}" if rv is not None else ""
        parts = ", ".join(p for p in (left_part, right_part) if p)
        lines.append(f"    {key}: {parts}")
    return lines


def summarize_diff(
    diff: DiffResult,
    label_left: str = "left",
    label_right: str = "right",
    mask_secrets: bool = True,
) -> SummaryReport:
    """Build a SummaryReport from a DiffResult."""
    if mask_secrets:
        diff = mask_diff(diff)

    total = (
        len(diff.matching)
        + len(diff.only_in_left)
        + len(diff.only_in_right)
        + len(diff.value_mismatches)
    )

    report = SummaryReport(
        total_keys=total,
        matching=len(diff.matching),
        only_in_left=len(diff.only_in_left),
        only_in_right=len(diff.only_in_right),
        mismatches=len(diff.value_mismatches),
    )

    lines: List[str] = []
    lines.append("=== envdiff Summary ===")
    lines.append(f"  Total keys : {total}")
    lines.append(f"  Matching   : {report.matching}")
    lines.append(f"  Only left  : {report.only_in_left}")
    lines.append(f"  Only right : {report.only_in_right}")
    lines.append(f"  Mismatches : {report.mismatches}")

    mismatch_pairs = {k: (lv, rv) for k, (lv, rv) in diff.value_mismatches.items()}
    left_only_pairs = {k: (v, None) for k, v in diff.only_in_left.items()}
    right_only_pairs = {k: (None, v) for k, v in diff.only_in_right.items()}

    lines += _section("MISMATCHES", mismatch_pairs, label_left, label_right)
    lines += _section("ONLY IN LEFT", left_only_pairs, label_left, label_right)
    lines += _section("ONLY IN RIGHT", right_only_pairs, label_left, label_right)

    if not report.has_issues:
        lines.append("  All keys match. No issues found.")

    report.lines = lines
    return report
