"""Tests for the envdiff CLI entry point."""

import os
import textwrap

import pytest

from envdiff.cli import build_parser, main


@pytest.fixture()
def env_file(tmp_path):
    """Return a helper that writes a .env file and returns its path."""

    def _write(content: str) -> str:
        p = tmp_path / "test.env"
        p.write_text(textwrap.dedent(content))
        return str(p)

    return _write


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

class TestBuildParser:
    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["a.env", "b.env"])
        assert args.left == "a.env"
        assert args.right == "b.env"
        assert args.no_color is False
        assert args.only_mismatches is False
        assert args.exit_code is False

    def test_flags(self):
        parser = build_parser()
        args = parser.parse_args(["a.env", "b.env", "--no-color", "--only-mismatches", "--exit-code"])
        assert args.no_color is True
        assert args.only_mismatches is True
        assert args.exit_code is True


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

class TestMain:
    def test_no_differences_exit_zero(self, env_file):
        path = env_file("FOO=bar\nBAZ=qux\n")
        assert main([path, path]) == 0

    def test_differences_exit_zero_without_flag(self, env_file):
        left = env_file("FOO=bar\n")
        right = env_file("FOO=different\n")
        assert main([left, right]) == 0

    def test_differences_exit_one_with_flag(self, env_file):
        left = env_file("FOO=bar\n")
        right = env_file("FOO=different\n")
        assert main([left, right, "--exit-code"]) == 1

    def test_missing_file_exits_two(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["nonexistent.env", "nonexistent2.env"])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "file not found" in captured.err

    def test_no_color_flag_produces_output(self, env_file, capsys):
        left = env_file("FOO=bar\n")
        right = env_file("FOO=baz\n")
        main([left, right, "--no-color"])
        captured = capsys.readouterr()
        assert "FOO" in captured.out

    def test_dash_reads_current_env(self, env_file, monkeypatch):
        monkeypatch.setenv("_ENVDIFF_TEST_VAR", "hello")
        path = env_file("_ENVDIFF_TEST_VAR=hello\n")
        # Both sides should match, so exit code flag returns 0.
        assert main(["-", path, "--exit-code"]) == 0

    def test_only_mismatches_flag(self, env_file, capsys):
        content = "FOO=bar\nBAZ=qux\n"
        path = env_file(content)
        main([path, path, "--only-mismatches", "--no-color"])
        captured = capsys.readouterr()
        # Matching keys should not appear when --only-mismatches is set.
        assert "FOO" not in captured.out
        assert "BAZ" not in captured.out
