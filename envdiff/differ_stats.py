"""Statistics and metrics derived from a DiffResult."""
from dataclasses import dataclass
from typing import Dict
from envdiff.differ import DiffResult


@dataclass
class DiffStats:
    total_keys: int
    only_in_left: int
    only_in_right: int
    mismatches: int
    matching: int

    @property
    def change_rate(self) -> float:
        """Fraction of keys that differ in any way (0.0 – 1.0)."""
        if self.total_keys == 0:
            return 0.0
        changed = self.only_in_left + self.only_in_right + self.mismatches
        return round(changed / self.total_keys, 4)

    @property
    def match_rate(self) -> float:
        """Fraction of keys that are identical in both sides."""
        return round(1.0 - self.change_rate, 4)

    def to_dict(self) -> Dict:
        return {
            "total_keys": self.total_keys,
            "only_in_left": self.only_in_left,
            "only_in_right": self.only_in_right,
            "mismatches": self.mismatches,
            "matching": self.matching,
            "change_rate": self.change_rate,
            "match_rate": self.match_rate,
        }

    def __str__(self) -> str:
        return (
            f"Total keys : {self.total_keys}\n"
            f"Only left  : {self.only_in_left}\n"
            f"Only right : {self.only_in_right}\n"
            f"Mismatches : {self.mismatches}\n"
            f"Matching   : {self.matching}\n"
            f"Change rate: {self.change_rate:.1%}\n"
            f"Match rate : {self.match_rate:.1%}"
        )


def compute_stats(diff: DiffResult) -> DiffStats:
    """Compute statistics from a DiffResult."""
    only_left = len(diff.only_in_left)
    only_right = len(diff.only_in_right)
    mismatches = len(diff.value_mismatches)
    matching = len(diff.matching_keys)
    total = only_left + only_right + mismatches + matching
    return DiffStats(
        total_keys=total,
        only_in_left=only_left,
        only_in_right=only_right,
        mismatches=mismatches,
        matching=matching,
    )
