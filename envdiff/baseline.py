"""Baseline comparison: compare current env against a saved snapshot baseline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult, diff_envs
from envdiff.snapshotter import load_snapshot


@dataclass
class BaselineReport:
    snapshot_path: str
    snapshot_label: Optional[str]
    diff: DiffResult
    regressions: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """True when there are no differences from the baseline."""
        return not (
            self.diff.only_in_left
            or self.diff.only_in_right
            or self.diff.value_mismatches
        )

    def summary(self) -> str:
        lines = [f"Baseline: {self.snapshot_path}"]
        if self.snapshot_label:
            lines.append(f"Label   : {self.snapshot_label}")
        if self.is_clean:
            lines.append("Status  : CLEAN — no drift from baseline")
        else:
            lines.append("Status  : DRIFT DETECTED")
            if self.diff.only_in_left:
                lines.append(f"  Removed keys  : {', '.join(sorted(self.diff.only_in_left))}")
            if self.diff.only_in_right:
                lines.append(f"  Added keys    : {', '.join(sorted(self.diff.only_in_right))}")
            if self.diff.value_mismatches:
                lines.append(f"  Changed values: {', '.join(sorted(self.diff.value_mismatches))}")
        return "\n".join(lines)


def compare_to_baseline(
    current_env: Dict[str, str],
    snapshot_path: str,
) -> BaselineReport:
    """Diff *current_env* against the env stored in *snapshot_path*.

    The snapshot is treated as the **left** side (baseline) and the
    current environment as the **right** side so that:
    - ``only_in_left``  → keys removed since the snapshot was taken
    - ``only_in_right`` → keys added since the snapshot was taken
    - ``value_mismatches`` → keys whose values changed
    """
    snapshot = load_snapshot(snapshot_path)
    baseline_env: Dict[str, str] = snapshot.get("env", {})
    label: Optional[str] = snapshot.get("label")

    result = diff_envs(baseline_env, current_env)

    regressions = list(result.only_in_left) + list(result.value_mismatches)
    improvements = list(result.only_in_right)

    return BaselineReport(
        snapshot_path=snapshot_path,
        snapshot_label=label,
        diff=result,
        regressions=sorted(regressions),
        improvements=sorted(improvements),
    )
