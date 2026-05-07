"""Generate environment variable templates from diff results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult
from envdiff.masker import should_mask


@dataclass
class TemplateEntry:
    key: str
    placeholder: str
    required: bool
    comment: Optional[str] = None

    def render(self) -> str:
        lines: List[str] = []
        if self.comment:
            lines.append(f"# {self.comment}")
        req_marker = "(required)" if self.required else "(optional)"
        lines.append(f"# {req_marker}")
        lines.append(f"{self.key}={self.placeholder}")
        return "\n".join(lines)


@dataclass
class EnvTemplate:
    entries: List[TemplateEntry] = field(default_factory=list)

    def render(self) -> str:
        """Render the full template as a .env-style string."""
        if not self.entries:
            return "# No template entries generated\n"
        sections = [e.render() for e in self.entries]
        return "\n\n".join(sections) + "\n"

    def keys(self) -> List[str]:
        return [e.key for e in self.entries]


def _placeholder_for(key: str) -> str:
    """Return a descriptive placeholder value for a key."""
    if should_mask(key):
        return "<SECRET>"
    lower = key.lower()
    if "url" in lower or "uri" in lower:
        return "<URL>"
    if "host" in lower:
        return "<HOSTNAME>"
    if "port" in lower:
        return "<PORT>"
    if "path" in lower or "dir" in lower:
        return "<PATH>"
    return "<VALUE>"


def generate_template(
    diff: DiffResult,
    include_right_only: bool = False,
    comment_mismatches: bool = True,
) -> EnvTemplate:
    """Build a template from a DiffResult.

    By default the template contains keys missing from the right env
    (only_in_left) plus mismatch keys, flagged as required.  Keys that
    only exist on the right can optionally be included as optional entries.
    """
    entries: List[TemplateEntry] = []

    for key in sorted(diff.only_in_left):
        entries.append(
            TemplateEntry(
                key=key,
                placeholder=_placeholder_for(key),
                required=True,
                comment=f"Missing from target env (left value: {diff.left.get(key, '')})",
            )
        )

    for key in sorted(diff.mismatches):
        comment = f"Value mismatch detected" if comment_mismatches else None
        entries.append(
            TemplateEntry(
                key=key,
                placeholder=_placeholder_for(key),
                required=True,
                comment=comment,
            )
        )

    if include_right_only:
        for key in sorted(diff.only_in_right):
            entries.append(
                TemplateEntry(
                    key=key,
                    placeholder=_placeholder_for(key),
                    required=False,
                    comment="Only present in target env",
                )
            )

    return EnvTemplate(entries=entries)
