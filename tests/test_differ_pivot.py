"""Tests for envdiff.differ_pivot."""

import pytest

from envdiff.differ import DiffResult
from envdiff.differ_pivot import PivotRow, PivotTable, pivot_diff


@pytest.fixture()
def full_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"LEFT_ONLY": "lo_val"},
        only_in_right={"RIGHT_ONLY": "ro_val"},
        value_mismatches={"MISMATCH_KEY": ("old", "new")},
        matching_keys={"SHARED": "same"},
    )


@pytest.fixture()
def table(full_diff: DiffResult) -> PivotTable:
    return pivot_diff(full_diff, left_label="dev", right_label="prod")


class TestPivotDiff:
    def test_returns_pivot_table_type(self, table: PivotTable) -> None:
        assert isinstance(table, PivotTable)

    def test_labels_stored(self, table: PivotTable) -> None:
        assert table.left_label == "dev"
        assert table.right_label == "prod"

    def test_row_count_matches_total_keys(self, table: PivotTable) -> None:
        assert len(table.rows) == 4

    def test_all_rows_are_pivot_row(self, table: PivotTable) -> None:
        assert all(isinstance(r, PivotRow) for r in table.rows)

    def test_rows_sorted_by_key(self, table: PivotTable) -> None:
        keys = [r.key for r in table.rows]
        assert keys == sorted(keys)

    def test_left_only_status(self, table: PivotTable) -> None:
        row = table.for_key("LEFT_ONLY")
        assert row is not None
        assert row.status == "left_only"
        assert row.left_value == "lo_val"
        assert row.right_value is None

    def test_right_only_status(self, table: PivotTable) -> None:
        row = table.for_key("RIGHT_ONLY")
        assert row is not None
        assert row.status == "right_only"
        assert row.right_value == "ro_val"
        assert row.left_value is None

    def test_mismatch_status(self, table: PivotTable) -> None:
        row = table.for_key("MISMATCH_KEY")
        assert row is not None
        assert row.status == "mismatch"
        assert row.left_value == "old"
        assert row.right_value == "new"

    def test_match_status(self, table: PivotTable) -> None:
        row = table.for_key("SHARED")
        assert row is not None
        assert row.status == "match"
        assert row.left_value == row.right_value == "same"


class TestPivotTableHelpers:
    def test_for_key_returns_none_for_unknown(self, table: PivotTable) -> None:
        assert table.for_key("NONEXISTENT") is None

    def test_by_status_left_only(self, table: PivotTable) -> None:
        rows = table.by_status("left_only")
        assert len(rows) == 1
        assert rows[0].key == "LEFT_ONLY"

    def test_by_status_match(self, table: PivotTable) -> None:
        rows = table.by_status("match")
        assert len(rows) == 1
        assert rows[0].key == "SHARED"

    def test_by_status_unknown_returns_empty(self, table: PivotTable) -> None:
        assert table.by_status("ghost") == []

    def test_to_dict_structure(self, table: PivotTable) -> None:
        d = table.to_dict()
        assert d["left_label"] == "dev"
        assert d["right_label"] == "prod"
        assert len(d["rows"]) == 4
        assert all({"key", "left_value", "right_value", "status"} <= r.keys()
                   for r in d["rows"])


class TestPivotRowStr:
    def test_str_includes_key_and_status(self) -> None:
        row = PivotRow(key="FOO", left_value="a", right_value="b", status="mismatch")
        s = str(row)
        assert "FOO" in s
        assert "mismatch" in s

    def test_str_absent_when_none(self) -> None:
        row = PivotRow(key="BAR", left_value=None, right_value="x", status="right_only")
        assert "<absent>" in str(row)


def test_empty_diff_produces_empty_table() -> None:
    diff = DiffResult(only_in_left={}, only_in_right={},
                      value_mismatches={}, matching_keys={})
    table = pivot_diff(diff)
    assert table.rows == []
