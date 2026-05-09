"""Tests for envdiff.differ_matrix."""
import pytest
from envdiff.differ_matrix import build_matrix, DiffMatrix, MatrixCell


@pytest.fixture
def three_envs():
    return {
        "dev": {"A": "1", "B": "2", "C": "3"},
        "staging": {"A": "1", "B": "99", "D": "4"},
        "prod": {"A": "1", "B": "2", "C": "3"},
    }


class TestBuildMatrix:
    def test_returns_diff_matrix_type(self, three_envs):
        result = build_matrix(three_envs)
        assert isinstance(result, DiffMatrix)

    def test_labels_recorded(self, three_envs):
        result = build_matrix(three_envs)
        assert set(result.labels) == {"dev", "staging", "prod"}

    def test_cell_count_for_three_envs(self, three_envs):
        result = build_matrix(three_envs)
        # C(3,2) = 3 pairs
        assert len(result.cells) == 3

    def test_cells_are_matrix_cell_type(self, three_envs):
        result = build_matrix(three_envs)
        for cell in result.cells:
            assert isinstance(cell, MatrixCell)

    def test_identical_envs_have_no_differences(self, three_envs):
        result = build_matrix(three_envs)
        cell = result.get("dev", "prod")
        assert cell is not None
        assert not cell.has_differences

    def test_differing_envs_detected(self, three_envs):
        result = build_matrix(three_envs)
        cell = result.get("dev", "staging")
        assert cell is not None
        assert cell.has_differences

    def test_issue_count_correct(self, three_envs):
        result = build_matrix(three_envs)
        cell = result.get("dev", "staging")
        # B mismatch, C only_in_left, D only_in_right => 3
        assert cell.issue_count == 3

    def test_get_returns_none_for_missing_pair(self, three_envs):
        result = build_matrix(three_envs)
        assert result.get("dev", "nonexistent") is None

    def test_pairs_with_differences_filters(self, three_envs):
        result = build_matrix(three_envs)
        diffs = result.pairs_with_differences()
        labels = [(c.left_label, c.right_label) for c in diffs]
        assert ("dev", "prod") not in labels

    def test_summary_keys_are_colon_separated(self, three_envs):
        result = build_matrix(three_envs)
        summary = result.summary()
        for key in summary:
            assert ":" in key

    def test_explicit_pairs(self, three_envs):
        result = build_matrix(three_envs, pairs=[("dev", "prod")])
        assert len(result.cells) == 1
        assert result.cells[0].left_label == "dev"
        assert result.cells[0].right_label == "prod"

    def test_two_identical_envs_clean(self):
        envs = {"a": {"X": "1"}, "b": {"X": "1"}}
        result = build_matrix(envs)
        assert len(result.pairs_with_differences()) == 0
