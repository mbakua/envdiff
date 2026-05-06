"""Tests for envdiff.linter."""

from __future__ import annotations

import pytest
from envdiff.linter import lint_env, LintIssue, LintResult


@pytest.fixture()
def clean_env():
    return {'DATABASE_URL': 'postgres://localhost/db', 'PORT': '5432'}


class TestLintResult:
    def test_is_clean_when_no_issues(self):
        result = LintResult()
        assert result.is_clean is True

    def test_is_not_clean_when_issues_present(self):
        result = LintResult(issues=[LintIssue('X', 'bad', 'error')])
        assert result.is_clean is False

    def test_errors_filters_correctly(self):
        result = LintResult(issues=[
            LintIssue('A', 'msg', 'error'),
            LintIssue('B', 'msg', 'warning'),
        ])
        assert len(result.errors) == 1
        assert result.errors[0].key == 'A'

    def test_warnings_filters_correctly(self):
        result = LintResult(issues=[
            LintIssue('A', 'msg', 'error'),
            LintIssue('B', 'msg', 'warning'),
        ])
        assert len(result.warnings) == 1
        assert result.warnings[0].key == 'B'

    def test_summary_clean(self):
        assert 'No lint' in LintResult().summary()

    def test_summary_with_issues(self):
        result = LintResult(issues=[
            LintIssue('A', 'x', 'error'),
            LintIssue('B', 'y', 'warning'),
        ])
        assert '1 error' in result.summary()
        assert '1 warning' in result.summary()


class TestLintEnv:
    def test_clean_env_returns_no_issues(self, clean_env):
        result = lint_env(clean_env)
        assert result.is_clean

    def test_lowercase_key_is_error(self):
        result = lint_env({'bad_key': 'value'})
        assert any(i.severity == 'error' for i in result.issues)

    def test_key_with_leading_digit_is_error(self):
        result = lint_env({'1INVALID': 'value'})
        errors = [i for i in result.issues if i.severity == 'error']
        assert len(errors) >= 1

    def test_empty_value_is_warning(self):
        result = lint_env({'MY_VAR': ''})
        warnings = [i for i in result.issues if i.severity == 'warning']
        assert any('empty' in w.message.lower() for w in warnings)

    def test_leading_whitespace_in_value_is_warning(self):
        result = lint_env({'MY_VAR': '  hello'})
        warnings = [i for i in result.issues if i.severity == 'warning']
        assert any('whitespace' in w.message.lower() for w in warnings)

    def test_trailing_whitespace_in_value_is_warning(self):
        result = lint_env({'MY_VAR': 'hello  '})
        warnings = [i for i in result.issues if i.severity == 'warning']
        assert any('whitespace' in w.message.lower() for w in warnings)

    def test_newline_in_value_is_warning(self):
        result = lint_env({'MY_VAR': 'line1\nline2'})
        warnings = [i for i in result.issues if i.severity == 'warning']
        assert any('newline' in w.message.lower() for w in warnings)

    def test_multiple_keys_accumulate_issues(self):
        env = {'bad': '', '1ALSO_BAD': 'fine'}
        result = lint_env(env)
        assert len(result.issues) >= 2

    def test_lint_issue_str_includes_severity_and_key(self):
        issue = LintIssue(key='FOO', message='some problem', severity='error')
        text = str(issue)
        assert 'ERROR' in text
        assert 'FOO' in text
