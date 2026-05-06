"""Tests for envdiff.exporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.differ import DiffResult
from envdiff.exporter import (
    ExportError,
    export_diff,
    supported_formats,
)


@pytest.fixture()
def simple_diff() -> DiffResult:
    return DiffResult(
        only_in_left={"ONLY_LEFT": "val1"},
        only_in_right={"ONLY_RIGHT": "val2"},
        value_mismatches={"SHARED": ("old", "new")},
        matching_keys={"SAME": "same"},
    )


class TestSupportedFormats:
    def test_returns_list(self):
        assert isinstance(supported_formats(), list)

    def test_contains_json(self):
        assert "json" in supported_formats()

    def test_contains_dotenv(self):
        assert "dotenv" in supported_formats()

    def test_contains_markdown(self):
        assert "markdown" in supported_formats()


class TestExportDiff:
    def test_json_creates_file(self, tmp_path, simple_diff):
        out = export_diff(simple_diff, tmp_path / "out.json", "json")
        assert out.exists()

    def test_json_content_is_valid(self, tmp_path, simple_diff):
        out = export_diff(simple_diff, tmp_path / "out.json", "json")
        data = json.loads(out.read_text())
        assert "only_in_left" in data

    def test_dotenv_creates_file(self, tmp_path, simple_diff):
        out = export_diff(simple_diff, tmp_path / "out.env", "dotenv")
        assert out.exists()

    def test_markdown_creates_file(self, tmp_path, simple_diff):
        out = export_diff(simple_diff, tmp_path / "out.md", "markdown")
        assert out.exists()

    def test_dest_is_directory_uses_default_name(self, tmp_path, simple_diff):
        out = export_diff(simple_diff, tmp_path, "json")
        assert out.name == "envdiff_output.json"

    def test_overwrite_false_raises_on_existing_file(self, tmp_path, simple_diff):
        dest = tmp_path / "out.json"
        dest.write_text("existing")
        with pytest.raises(ExportError, match="already exists"):
            export_diff(simple_diff, dest, "json", overwrite=False)

    def test_overwrite_true_replaces_file(self, tmp_path, simple_diff):
        dest = tmp_path / "out.json"
        dest.write_text("existing")
        out = export_diff(simple_diff, dest, "json", overwrite=True)
        assert json.loads(out.read_text())  # valid JSON written

    def test_unsupported_format_raises(self, tmp_path, simple_diff):
        with pytest.raises(ExportError, match="Unsupported format"):
            export_diff(simple_diff, tmp_path / "out.xyz", "xml")

    def test_returns_resolved_path(self, tmp_path, simple_diff):
        out = export_diff(simple_diff, tmp_path / "out.md", "markdown")
        assert out.is_absolute()

    def test_creates_missing_parent_dirs(self, tmp_path, simple_diff):
        dest = tmp_path / "nested" / "deep" / "out.json"
        out = export_diff(simple_diff, dest, "json")
        assert out.exists()
