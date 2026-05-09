"""Matrix comparison: diff multiple env sets against each other."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from envdiff.differ import DiffResult, diff_envs


@dataclass
class MatrixCell:
    left_label: str
    right_label: str
    result: DiffResult

    @property
    def has_differences(self) -> bool:
        return bool(
            self.result.only_in_left
            or self.result.only_in_right
            or self.result.value_mismatches
        )

    @property
    def issue_count(self) -> int:
        return (
            len(self.result.only_in_left)
            + len(self.result.only_in_right)
            + len(self.result.value_mismatches)
        )


@dataclass
class DiffMatrix:
    labels: List[str]
    cells: List[MatrixCell] = field(default_factory=list)

    def get(self, left: str, right: str) -> MatrixCell | None:
        for cell in self.cells:
            if cell.left_label == left and cell.right_label == right:
                return cell
        return None

    def pairs_with_differences(self) -> List[MatrixCell]:
        return [c for c in self.cells if c.has_differences]

    def summary(self) -> Dict[str, int]:
        return {
            f"{c.left_label}:{c.right_label}": c.issue_count
            for c in self.cells
        }


def build_matrix(
    envs: Dict[str, Dict[str, str]],
    pairs: List[Tuple[str, str]] | None = None,
) -> DiffMatrix:
    """Compare all label pairs (or explicit pairs) and return a DiffMatrix."""
    labels = list(envs.keys())
    if pairs is None:
        pairs = [
            (labels[i], labels[j])
            for i in range(len(labels))
            for j in range(i + 1, len(labels))
        ]
    cells: List[MatrixCell] = []
    for left_label, right_label in pairs:
        result = diff_envs(envs[left_label], envs[right_label])
        cells.append(MatrixCell(left_label, right_label, result))
    return DiffMatrix(labels=labels, cells=cells)
