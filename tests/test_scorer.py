"""Tests for envdiff.scorer."""

import pytest

from envdiff.differ import DiffResult
from envdiff.scorer import ScoreResult, _grade, score_diff


@pytest.fixture()
def perfect_diff():
    return DiffResult(
        only_in_left=[],
        only_in_right=[],
        value_mismatches={},
        matching_keys=["A", "B"],
    )


@pytest.fixture()
def bad_diff():
    return DiffResult(
        only_in_left=["MISSING_KEY"],
        only_in_right=["EXTRA_KEY"],
        value_mismatches={"DB_HOST": ("prod-db", "staging-db")},
        matching_keys=["PORT"],
    )


class TestGrade:
    def test_a_grade(self):
        assert _grade(95) == "A"

    def test_b_grade(self):
        assert _grade(80) == "B"

    def test_c_grade(self):
        assert _grade(65) == "C"

    def test_d_grade(self):
        assert _grade(50) == "D"

    def test_f_grade(self):
        assert _grade(30) == "F"

    def test_boundary_90_is_a(self):
        assert _grade(90) == "A"


class TestScoreDiff:
    def test_returns_score_result_type(self, perfect_diff):
        result = score_diff(perfect_diff)
        assert isinstance(result, ScoreResult)

    def test_perfect_diff_scores_100(self, perfect_diff):
        result = score_diff(perfect_diff)
        assert result.score == 100

    def test_perfect_diff_grade_is_a(self, perfect_diff):
        result = score_diff(perfect_diff)
        assert result.grade == "A"

    def test_perfect_diff_no_issues(self, perfect_diff):
        result = score_diff(perfect_diff)
        assert result.issue_count == 0

    def test_bad_diff_score_below_100(self, bad_diff):
        result = score_diff(bad_diff)
        assert result.score < 100

    def test_bad_diff_issue_count(self, bad_diff):
        # 1 missing + 1 extra + 1 mismatch
        result = score_diff(bad_diff)
        assert result.issue_count == 3

    def test_score_never_negative(self):
        huge_diff = DiffResult(
            only_in_left=[f"K{i}" for i in range(50)],
            only_in_right=[],
            value_mismatches={},
            matching_keys=[],
        )
        result = score_diff(huge_diff)
        assert result.score >= 0

    def test_custom_weights_applied(self, bad_diff):
        default_result = score_diff(bad_diff)
        heavy_result = score_diff(bad_diff, weights={"missing": 10, "extra": 10, "mismatch": 10})
        assert heavy_result.score < default_result.score

    def test_total_keys_counts_all_categories(self, bad_diff):
        result = score_diff(bad_diff)
        # missing(1) + extra(1) + mismatch(1) + matching(1) = 4
        assert result.total_keys == 4

    def test_details_keys_present(self, bad_diff):
        result = score_diff(bad_diff)
        for key in ("missing_keys", "extra_keys", "mismatched_keys", "matching_keys"):
            assert key in result.details

    def test_str_representation(self, perfect_diff):
        result = score_diff(perfect_diff)
        text = str(result)
        assert "100" in text
        assert "A" in text
