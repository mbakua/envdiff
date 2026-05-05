"""Tests for envdiff.formatter."""

import json

import pytest

from envdiff.differ import DiffResult
from envdiff.formatter import format_dotenv, format_json, format_markdown


@pytest.fixture()
def sample_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"ALPHA": "1", "BETA": "2"},
        only_in_right={"GAMMA": "3"},
        value_mismatches={"DELTA": ("old", "new")},
        matching_keys={"COMMON"},
    )


class TestFormatJson:
    def test_returns_valid_json(self, sample_diff: DiffResult) -> None:
        result = format_json(sample_diff)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_only_in_left_present(self, sample_diff: DiffResult) -> None:
        parsed = json.loads(format_json(sample_diff))
        assert parsed["only_in_left"] == {"ALPHA": "1", "BETA": "2"}

    def test_only_in_right_present(self, sample_diff: DiffResult) -> None:
        parsed = json.loads(format_json(sample_diff))
        assert parsed["only_in_right"] == {"GAMMA": "3"}

    def test_value_mismatches_structure(self, sample_diff: DiffResult) -> None:
        parsed = json.loads(format_json(sample_diff))
        assert parsed["value_mismatches"]["DELTA"] == {"left": "old", "right": "new"}

    def test_matching_keys_sorted(self, sample_diff: DiffResult) -> None:
        parsed = json.loads(format_json(sample_diff))
        assert parsed["matching_keys"] == ["COMMON"]

    def test_empty_diff_produces_empty_sections(self) -> None:
        empty = DiffResult(
            only_in_left={},
            only_in_right={},
            value_mismatches={},
            matching_keys=set(),
        )
        parsed = json.loads(format_json(empty))
        assert parsed["only_in_left"] == {}
        assert parsed["only_in_right"] == {}


class TestFormatDotenv:
    def test_left_side_output(self, sample_diff: DiffResult) -> None:
        result = format_dotenv(sample_diff, side="left")
        assert "ALPHA=1" in result
        assert "BETA=2" in result

    def test_right_side_output(self, sample_diff: DiffResult) -> None:
        result = format_dotenv(sample_diff, side="right")
        assert "GAMMA=3" in result

    def test_invalid_side_raises(self, sample_diff: DiffResult) -> None:
        with pytest.raises(ValueError, match="side must be"):
            format_dotenv(sample_diff, side="both")

    def test_empty_side_returns_empty_string(self) -> None:
        diff = DiffResult(
            only_in_left={},
            only_in_right={},
            value_mismatches={},
            matching_keys=set(),
        )
        assert format_dotenv(diff, side="left") == ""


class TestFormatMarkdown:
    def test_contains_header(self, sample_diff: DiffResult) -> None:
        result = format_markdown(sample_diff)
        assert "# Environment Diff Report" in result

    def test_only_in_left_section(self, sample_diff: DiffResult) -> None:
        result = format_markdown(sample_diff)
        assert "## Only in left" in result
        assert "`ALPHA`" in result

    def test_value_mismatches_section(self, sample_diff: DiffResult) -> None:
        result = format_markdown(sample_diff)
        assert "## Value mismatches" in result
        assert "`DELTA`" in result
        assert "`old`" in result
        assert "`new`" in result

    def test_matching_keys_section(self, sample_diff: DiffResult) -> None:
        result = format_markdown(sample_diff)
        assert "## Matching keys" in result
        assert "`COMMON`" in result
