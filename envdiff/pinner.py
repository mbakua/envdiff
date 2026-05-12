"""Pin environment variable values to a reference snapshot for drift detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult


@dataclass
class PinViolation:
    key: str
    pinned_value: str
    actual_value: Optional[str]
    reason: str

    def __str__(self) -> str:
        return f"[{self.key}] {self.reason} (pinned={self.pinned_value!r}, actual={self.actual_value!r})"


@dataclass
class PinReport:
    violations: List[PinViolation] = field(default_factory=list)
    checked: int = 0

    @property
    def is_clean(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.is_clean:
            return f"All {self.checked} pinned key(s) match expected values."
        lines = [f"{len(self.violations)} pin violation(s) out of {self.checked} checked:"]
        for v in self.violations:
            lines.append(f"  - {v}")
        return "\n".join(lines)


def pin_diff(
    diff: DiffResult,
    pins: Dict[str, str],
) -> PinReport:
    """Check that every key in *pins* has the expected value in the right-hand env.

    A violation is raised when:
    - the key is missing from the right env entirely, or
    - the value in the right env differs from the pinned value.

    Keys that exist only in the left env are also flagged as missing.
    """
    violations: List[PinViolation] = []

    right_values: Dict[str, str] = {}
    for key, (_, right_val) in diff.value_mismatches.items():
        right_values[key] = right_val
    for key in diff.only_in_right:
        right_values[key] = diff.only_in_right[key]
    # Keys that match are present in both with equal values; retrieve from matching
    for key, val in diff.matching_keys.items():
        right_values[key] = val

    for key, pinned_value in pins.items():
        if key in diff.only_in_left:
            violations.append(
                PinViolation(
                    key=key,
                    pinned_value=pinned_value,
                    actual_value=None,
                    reason="key missing from right env",
                )
            )
        elif key in diff.value_mismatches:
            _, actual = diff.value_mismatches[key]
            if actual != pinned_value:
                violations.append(
                    PinViolation(
                        key=key,
                        pinned_value=pinned_value,
                        actual_value=actual,
                        reason="value mismatch",
                    )
                )
        elif key in right_values:
            actual = right_values[key]
            if actual != pinned_value:
                violations.append(
                    PinViolation(
                        key=key,
                        pinned_value=pinned_value,
                        actual_value=actual,
                        reason="value mismatch",
                    )
                )
        else:
            violations.append(
                PinViolation(
                    key=key,
                    pinned_value=pinned_value,
                    actual_value=None,
                    reason="key not found in either env",
                )
            )

    return PinReport(violations=violations, checked=len(pins))
