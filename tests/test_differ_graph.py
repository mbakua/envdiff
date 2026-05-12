"""Tests for envdiff.differ_graph."""
from __future__ import annotations

import pytest

from envdiff.differ import DiffResult
from envdiff.differ_graph import (
    DiffGraph,
    GraphEdge,
    GraphNode,
    build_graph,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def three_diffs():
    """Three pairwise diffs: dev<->staging, dev<->prod, staging<->prod."""
    dev_staging = DiffResult(
        only_in_left={"DEBUG": "true"},
        only_in_right={},
        value_mismatches={"DB_HOST": ("dev-db", "staging-db")},
        matching_keys={"APP_NAME": "envdiff"},
    )
    dev_prod = DiffResult(
        only_in_left={"DEBUG": "true"},
        only_in_right={},
        value_mismatches={
            "DB_HOST": ("dev-db", "prod-db"),
            "LOG_LEVEL": ("DEBUG", "ERROR"),
        },
        matching_keys={"APP_NAME": "envdiff"},
    )
    staging_prod = DiffResult(
        only_in_left={},
        only_in_right={},
        value_mismatches={"DB_HOST": ("staging-db", "prod-db")},
        matching_keys={"APP_NAME": "envdiff"},
    )
    return {
        ("dev", "staging"): dev_staging,
        ("dev", "prod"): dev_prod,
        ("staging", "prod"): staging_prod,
    }


# ---------------------------------------------------------------------------
# build_graph return type
# ---------------------------------------------------------------------------

def test_returns_diff_graph_type(three_diffs):
    result = build_graph(three_diffs)
    assert isinstance(result, DiffGraph)


def test_nodes_populated(three_diffs):
    graph = build_graph(three_diffs)
    assert set(graph.nodes.keys()) == {"dev", "staging", "prod"}


def test_node_is_graph_node_instance(three_diffs):
    graph = build_graph(three_diffs)
    for node in graph.nodes.values():
        assert isinstance(node, GraphNode)


def test_edge_count_matches_pairs(three_diffs):
    graph = build_graph(three_diffs)
    assert len(graph.edges) == 3


def test_edges_are_graph_edge_instances(three_diffs):
    graph = build_graph(three_diffs)
    for edge in graph.edges:
        assert isinstance(edge, GraphEdge)


def test_dev_node_has_correct_issue_keys(three_diffs):
    graph = build_graph(three_diffs)
    # dev appears in two diffs; union of issue keys expected
    dev_node = graph.nodes["dev"]
    assert "DEBUG" in dev_node.issue_keys
    assert "DB_HOST" in dev_node.issue_keys
    assert "LOG_LEVEL" in dev_node.issue_keys


def test_staging_prod_edge_has_one_mismatch(three_diffs):
    graph = build_graph(three_diffs)
    sp_edge = next(
        e for e in graph.edges if {e.source, e.target} == {"staging", "prod"}
    )
    assert sp_edge.mismatch_count == 1


def test_most_divergent_ordering(three_diffs):
    graph = build_graph(three_diffs)
    ranked = graph.most_divergent()
    # dev<->prod has 3 mismatches, should be first
    assert ranked[0][2] >= ranked[-1][2]
    top_pair = {ranked[0][0], ranked[0][1]}
    assert top_pair == {"dev", "prod"}


def test_neighbors_returns_connected_labels(three_diffs):
    graph = build_graph(three_diffs)
    neighbors = graph.neighbors("dev")
    assert set(neighbors) == {"staging", "prod"}


def test_empty_graph_has_no_nodes_or_edges():
    graph = build_graph({})
    assert graph.nodes == {}
    assert graph.edges == []


def test_identical_envs_edge_has_no_differences():
    identical = DiffResult(
        only_in_left={},
        only_in_right={},
        value_mismatches={},
        matching_keys={"KEY": "val"},
    )
    graph = build_graph({("a", "b"): identical})
    assert not graph.edges[0].has_differences
