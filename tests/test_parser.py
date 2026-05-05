"""Tests for envdiff.parser module."""

import os
import textwrap
from pathlib import Path

import pytest

from envdiff.parser import parse_current_env, parse_env_file


@pytest.fixture()
def tmp_env_file(tmp_path: Path):
    """Factory fixture that writes content to a temp .env file and returns its path."""

    def _write(content: str) -> str:
        env_file = tmp_path / ".env"
        env_file.write_text(textwrap.dedent(content), encoding="utf-8")
        return str(env_file)

    return _write


class TestParseEnvFile:
    def test_basic_key_value(self, tmp_env_file):
        path = tmp_env_file("APP_ENV=production\nDEBUG=false\n")
        result = parse_env_file(path)
        assert result == {"APP_ENV": "production", "DEBUG": "false"}

    def test_quoted_values(self, tmp_env_file):
        path = tmp_env_file('DB_URL="postgres://localhost/mydb"\nSECRET=\'mysecret\'\n')
        result = parse_env_file(path)
        assert result["DB_URL"] == "postgres://localhost/mydb"
        assert result["SECRET"] == "mysecret"

    def test_skips_blank_lines_and_comments(self, tmp_env_file):
        path = tmp_env_file(
            """
            # This is a comment
            APP_NAME=envdiff

            # Another comment
            VERSION=1.0
            """
        )
        result = parse_env_file(path)
        assert result == {"APP_NAME": "envdiff", "VERSION": "1.0"}

    def test_inline_comment_stripped(self, tmp_env_file):
        path = tmp_env_file("PORT=8080 # default port\n")
        result = parse_env_file(path)
        assert result["PORT"] == "8080"

    def test_empty_value(self, tmp_env_file):
        path = tmp_env_file("EMPTY_VAR=\n")
        result = parse_env_file(path)
        assert result["EMPTY_VAR"] == ""

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError, match="not found"):
            parse_env_file("/nonexistent/path/.env")

    def test_invalid_line_raises(self, tmp_env_file):
        path = tmp_env_file("INVALID_LINE_NO_EQUALS\n")
        with pytest.raises(ValueError, match="Invalid syntax"):
            parse_env_file(path)

    def test_empty_key_raises(self, tmp_env_file):
        path = tmp_env_file("=value\n")
        with pytest.raises(ValueError, match="Empty key"):
            parse_env_file(path)


class TestParseCurrentEnv:
    def test_returns_dict(self):
        result = parse_current_env()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_prefix_filter(self, monkeypatch):
        monkeypatch.setenv("MYAPP_HOST", "localhost")
        monkeypatch.setenv("MYAPP_PORT", "9000")
        monkeypatch.setenv("OTHER_VAR", "ignored")
        result = parse_current_env(prefix="MYAPP_")
        assert "MYAPP_HOST" in result
        assert "MYAPP_PORT" in result
        assert "OTHER_VAR" not in result

    def test_no_prefix_includes_all(self, monkeypatch):
        monkeypatch.setenv("UNIQUE_TEST_VAR_XYZ", "present")
        result = parse_current_env()
        assert "UNIQUE_TEST_VAR_XYZ" in result
