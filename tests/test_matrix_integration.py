"""Integration tests: build_matrix + matrix_cmd together."""
import json
import pytest
from envdiff.differ_matrix import build_matrix
from envdiff.matrix_cmd import build_matrix_parser, run_matrix


@pytest.fixture
def env_files(tmp_path):
    files = {
        "dev": tmp_path / "dev.env",
        "staging": tmp_path / "staging.env",
        "prod": tmp_path / "prod.env",
    }
    files["dev"].write_text("DB_HOST=localhost\nSECRET_KEY=abc\nDEBUG=true\n")
    files["staging"].write_text("DB_HOST=staging.db\nSECRET_KEY=abc\nDEBUG=false\n")
    files["prod"].write_text("DB_HOST=prod.db\nSECRET_KEY=xyz\n")
    return {k: str(v) for k, v in files.items()}


class TestMatrixIntegration:
    def test_three_way_matrix_has_three_cells(self):
        envs = {
            "a": {"X": "1"},
            "b": {"X": "2"},
            "c": {"X": "1"},
        }
        matrix = build_matrix(envs)
        assert len(matrix.cells) == 3

    def test_prod_missing_debug_shows_in_matrix(self):
        envs = {
            "dev": {"DEBUG": "true", "HOST": "localhost"},
            "prod": {"HOST": "prod.example.com"},
        }
        matrix = build_matrix(envs)
        cell = matrix.get("dev", "prod")
        assert "DEBUG" in cell.result.only_in_left

    def test_cmd_json_contains_issue_count(self, env_files, capsys):
        p = build_matrix_parser()
        args = p.parse_args([
            f"dev={env_files['dev']}",
            f"prod={env_files['prod']}",
            "--format", "json",
        ])
        run_matrix(args)
        data = json.loads(capsys.readouterr().out)
        key = "dev:prod"
        assert key in data
        assert data[key]["issue_count"] > 0

    def test_identical_pair_zero_issues(self):
        envs = {
            "a": {"K": "v", "M": "n"},
            "b": {"K": "v", "M": "n"},
        }
        matrix = build_matrix(envs)
        assert matrix.cells[0].issue_count == 0

    def test_summary_reflects_all_pairs(self):
        envs = {"x": {"A": "1"}, "y": {"A": "2"}, "z": {"A": "1"}}
        matrix = build_matrix(envs)
        summary = matrix.summary()
        assert len(summary) == 3
