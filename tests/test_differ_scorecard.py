"""Tests for envdiff.differ_scorecard."""

import pytest

from envdiff.differ import DiffResult
from envdiff.differ_scorecard import (
    DiffScorecard,
    ScorecardEntry,
    build_scorecard,
)
from envdiff.scorer import score_diff


@pytest.fixture()
def clean_diff() -> DiffResult:
    return DiffResult(
        only_in_left={},
        only_in_right={},
        value_mismatches={},
        matching_keys={"DB_HOST": "localhost", "PORT": "5432"},
    )


@pytest.fixture()
def bad_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"SECRET": "abc", "TOKEN": "xyz"},
        only_in_right={"NEW_KEY": "val"},
        value_mismatches={"DB_HOST": ("localhost", "prod-db")},
        matching_keys={},
    )


@pytest.fixture()
def labeled(clean_diff, bad_diff) -> dict:
    return {"dev": clean_diff, "prod": bad_diff}


def test_build_scorecard_returns_diff_scorecard_type(labeled):
    result = build_scorecard(labeled)
    assert isinstance(result, DiffScorecard)


def test_entries_count_matches_input(labeled):
    result = build_scorecard(labeled)
    assert len(result.entries) == 2


def test_entries_are_scorecard_entry_instances(labeled):
    result = build_scorecard(labeled)
    for entry in result.entries:
        assert isinstance(entry, ScorecardEntry)


def test_best_returns_highest_scoring_entry(labeled):
    result = build_scorecard(labeled)
    assert result.best().label == "dev"


def test_worst_returns_lowest_scoring_entry(labeled):
    result = build_scorecard(labeled)
    assert result.worst().label == "prod"


def test_ranked_order_descending(labeled):
    result = build_scorecard(labeled)
    scores = [e.score.score for e in result.ranked()]
    assert scores == sorted(scores, reverse=True)


def test_average_score_is_between_0_and_100(labeled):
    result = build_scorecard(labeled)
    assert 0.0 <= result.average_score() <= 100.0


def test_average_score_empty_scorecard():
    card = DiffScorecard(entries=[])
    assert card.average_score() == 0.0


def test_best_returns_none_for_empty_scorecard():
    card = DiffScorecard(entries=[])
    assert card.best() is None


def test_worst_returns_none_for_empty_scorecard():
    card = DiffScorecard(entries=[])
    assert card.worst() is None


def test_to_dict_has_required_keys(labeled):
    result = build_scorecard(labeled)
    d = result.to_dict()
    assert "entries" in d
    assert "average_score" in d
    assert "best" in d
    assert "worst" in d


def test_to_dict_entries_have_label_score_grade(labeled):
    result = build_scorecard(labeled)
    for item in result.to_dict()["entries"]:
        assert "label" in item
        assert "score" in item
        assert "grade" in item


def test_scorecard_entry_str(clean_diff):
    entry = ScorecardEntry(label="dev", score=score_diff(clean_diff))
    s = str(entry)
    assert "dev" in s
    assert "/100" in s
