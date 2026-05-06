"""Lint environment variable keys and values for common issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import re

_VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')
_WHITESPACE_RE = re.compile(r'\s')


@dataclass
class LintIssue:
    key: str
    message: str
    severity: str  # 'error' | 'warning'

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == 'error']

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == 'warning']

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean:
            return "No lint issues found."
        return (
            f"{len(self.errors)} error(s), {len(self.warnings)} warning(s) found."
        )


def lint_env(env: Dict[str, str]) -> LintResult:
    """Lint an environment variable mapping and return a LintResult."""
    result = LintResult()

    for key, value in env.items():
        # Key must match POSIX convention
        if not _VALID_KEY_RE.match(key):
            result.issues.append(LintIssue(
                key=key,
                message="Key does not match expected pattern [A-Z_][A-Z0-9_]*",
                severity='error',
            ))

        # Warn on empty values
        if value == '':
            result.issues.append(LintIssue(
                key=key,
                message="Value is empty",
                severity='warning',
            ))

        # Warn on leading/trailing whitespace in value
        if value != value.strip():
            result.issues.append(LintIssue(
                key=key,
                message="Value has leading or trailing whitespace",
                severity='warning',
            ))

        # Warn if value contains unquoted newline characters
        if '\n' in value or '\r' in value:
            result.issues.append(LintIssue(
                key=key,
                message="Value contains newline characters",
                severity='warning',
            ))

    return result
