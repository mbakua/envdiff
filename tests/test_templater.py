"""Tests for envdiff.templater."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffResult
from envdiff.templater import (
    EnvTemplate,
    TemplateEntry,
    _placeholder_for,
    generate_template,
)


@pytest.fixture()
def base_diff() -> DiffResult:
    return DiffResult(
        left={"DB_HOST": "localhost", "API_TOKEN": "abc123", "APP_URL": "http://a"},
        right={"DB_HOST": "prod-host", "EXTRA_KEY": "only-right"},
        only_in_left={"API_TOKEN", "APP_URL"},
        only_in_right={"EXTRA_KEY"},
        mismatches={"DB_HOST"},
        matches=set(),
    )


class TestPlaceholderFor:
    def test_secret_key_returns_secret(self):
        assert _placeholder_for("API_TOKEN") == "<SECRET>"

    def test_password_key_returns_secret(self):
        assert _placeholder_for("DB_PASSWORD") == "<SECRET>"

    def test_url_key_returns_url(self):
        assert _placeholder_for("APP_URL") == "<URL>"

    def test_host_key_returns_hostname(self):
        assert _placeholder_for("DB_HOST") == "<HOSTNAME>"

    def test_port_key_returns_port(self):
        assert _placeholder_for("SERVER_PORT") == "<PORT>"

    def test_path_key_returns_path(self):
        assert _placeholder_for("LOG_PATH") == "<PATH>"

    def test_generic_key_returns_value(self):
        assert _placeholder_for("APP_NAME") == "<VALUE>"


class TestGenerateTemplate:
    def test_returns_env_template_type(self, base_diff):
        result = generate_template(base_diff)
        assert isinstance(result, EnvTemplate)

    def test_only_in_left_included_as_required(self, base_diff):
        result = generate_template(base_diff)
        keys = result.keys()
        assert "API_TOKEN" in keys
        assert "APP_URL" in keys

    def test_mismatch_keys_included_as_required(self, base_diff):
        result = generate_template(base_diff)
        assert "DB_HOST" in result.keys()

    def test_right_only_excluded_by_default(self, base_diff):
        result = generate_template(base_diff)
        assert "EXTRA_KEY" not in result.keys()

    def test_right_only_included_when_flag_set(self, base_diff):
        result = generate_template(base_diff, include_right_only=True)
        assert "EXTRA_KEY" in result.keys()

    def test_right_only_entry_is_not_required(self, base_diff):
        result = generate_template(base_diff, include_right_only=True)
        entry = next(e for e in result.entries if e.key == "EXTRA_KEY")
        assert entry.required is False

    def test_mismatch_entry_is_required(self, base_diff):
        result = generate_template(base_diff)
        entry = next(e for e in result.entries if e.key == "DB_HOST")
        assert entry.required is True

    def test_mismatch_comment_present_by_default(self, base_diff):
        result = generate_template(base_diff)
        entry = next(e for e in result.entries if e.key == "DB_HOST")
        assert entry.comment is not None

    def test_mismatch_comment_suppressed(self, base_diff):
        result = generate_template(base_diff, comment_mismatches=False)
        entry = next(e for e in result.entries if e.key == "DB_HOST")
        assert entry.comment is None

    def test_empty_diff_produces_empty_template(self):
        empty = DiffResult(
            left={}, right={},
            only_in_left=set(), only_in_right=set(),
            mismatches=set(), matches=set(),
        )
        result = generate_template(empty)
        assert result.keys() == []


class TestEnvTemplateRender:
    def test_render_contains_key(self, base_diff):
        template = generate_template(base_diff)
        rendered = template.render()
        assert "API_TOKEN" in rendered

    def test_render_contains_placeholder(self, base_diff):
        template = generate_template(base_diff)
        rendered = template.render()
        assert "<SECRET>" in rendered

    def test_empty_template_render_is_comment(self):
        template = EnvTemplate(entries=[])
        rendered = template.render()
        assert rendered.startswith("#")

    def test_entry_render_includes_required_marker(self):
        entry = TemplateEntry(key="FOO", placeholder="<VALUE>", required=True)
        rendered = entry.render()
        assert "(required)" in rendered

    def test_entry_render_includes_optional_marker(self):
        entry = TemplateEntry(key="BAR", placeholder="<VALUE>", required=False)
        rendered = entry.render()
        assert "(optional)" in rendered
