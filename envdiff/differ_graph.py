"""Build a dependency/relationship graph from multiple environment diffs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from envdiff.differ import DiffResult


@dataclass
class GraphNode:
    """Represents a single environment label in the graph."""

    label: str
    issue_keys: Set[str] = field(default_factory=set)

    @property
    def issue_count(self) -> int:
        return len(self.issue_keys)


@dataclass
class GraphEdge:
    """Represents a diff relationship between two environments."""

    source: str
    target: str
    diff: DiffResult

    @property
    def has_differences(self) -> bool:
        return bool(
            self.diff.only_in_left
            or self.diff.only_in_right
            or self.diff.value_mismatches
        )

    @property
    def mismatch_count(self) -> int:
        return (
            len(self.diff.only_in_left)
            + len(self.diff.only_in_right)
            + len(self.diff.value_mismatches)
        )


@dataclass
class DiffGraph:
    """Graph of environments connected by their diffs."""

    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)

    def neighbors(self, label: str) -> List[str]:
        """Return labels of all environments directly connected to *label*."""
        result: List[str] = []
        for edge in self.edges:
            if edge.source == label:
                result.append(edge.target)
            elif edge.target == label:
                result.append(edge.source)
        return result

    def most_divergent(self) -> List[Tuple[str, str, int]]:
        """Return edges sorted by mismatch count descending."""
        ranked = [
            (e.source, e.target, e.mismatch_count)
            for e in self.edges
            if e.has_differences
        ]
        return sorted(ranked, key=lambda t: t[2], reverse=True)


def build_graph(
    labeled_diffs: Dict[Tuple[str, str], DiffResult],
) -> DiffGraph:
    """Build a *DiffGraph* from a mapping of (source, target) -> DiffResult."""
    graph = DiffGraph()
    for (src, tgt), diff in labeled_diffs.items():
        for label in (src, tgt):
            if label not in graph.nodes:
                graph.nodes[label] = GraphNode(label=label)
        issue_keys: Set[str] = (
            set(diff.only_in_left)
            | set(diff.only_in_right)
            | set(diff.value_mismatches)
        )
        graph.nodes[src].issue_keys |= issue_keys
        graph.nodes[tgt].issue_keys |= issue_keys
        graph.edges.append(GraphEdge(source=src, target=tgt, diff=diff))
    return graph
