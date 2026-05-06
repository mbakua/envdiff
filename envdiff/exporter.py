"""Export diff results to various file formats on disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from envdiff.differ import DiffResult
from envdiff.formatter import format_json, format_dotenv, format_markdown

_FORMAT_MAP: dict[str, tuple[str, Callable[[DiffResult], str]]] = {
    "json": (".json", format_json),
    "dotenv": (".env", format_dotenv),
    "markdown": (".md", format_markdown),
}


class ExportError(Exception):
    """Raised when an export operation fails."""


def supported_formats() -> list[str]:
    """Return the list of supported export format names."""
    return list(_FORMAT_MAP.keys())


def export_diff(
    diff: DiffResult,
    dest: str | Path,
    fmt: str,
    *,
    overwrite: bool = False,
) -> Path:
    """Serialise *diff* in *fmt* and write it to *dest*.

    Parameters
    ----------
    diff:
        The diff result to export.
    dest:
        Destination file path.  If *dest* is a directory the file is placed
        inside it with an auto-generated name.
    fmt:
        One of the keys returned by :func:`supported_formats`.
    overwrite:
        When ``False`` (default) raise :class:`ExportError` if *dest* already
        exists.

    Returns
    -------
    Path
        The resolved path of the written file.
    """
    fmt = fmt.lower()
    if fmt not in _FORMAT_MAP:
        raise ExportError(
            f"Unsupported format {fmt!r}. Choose from: {supported_formats()}"
        )

    extension, formatter = _FORMAT_MAP[fmt]
    dest = Path(dest)

    if dest.is_dir():
        dest = dest / f"envdiff_output{extension}"

    if dest.exists() and not overwrite:
        raise ExportError(
            f"Destination {dest} already exists. Pass overwrite=True to replace it."
        )

    content = formatter(diff)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest.resolve()
