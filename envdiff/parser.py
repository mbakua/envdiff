"""Parser module for loading environment variable sets from various sources."""

import os
from pathlib import Path
from typing import Dict, Optional


def parse_env_file(filepath: str) -> Dict[str, str]:
    """Parse a .env file and return a dictionary of key-value pairs.

    Supports:
    - KEY=VALUE
    - KEY="VALUE" or KEY='VALUE'
    - Inline comments (# ...)
    - Blank lines and full-line comments are skipped

    Args:
        filepath: Path to the .env file.

    Returns:
        Dictionary of environment variable names to their string values.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a line cannot be parsed.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Environment file not found: {filepath}")

    env_vars: Dict[str, str] = {}

    with path.open("r", encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.strip()

            # Skip blank lines and comments
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                raise ValueError(
                    f"Invalid syntax at line {lineno} in '{filepath}': {raw_line.rstrip()!r}"
                )

            key, _, value = line.partition("=")
            key = key.strip()

            # Strip inline comments from unquoted values
            if value and value[0] not in ("'", '"'):
                value = value.split(" #")[0].strip()
            else:
                # Strip surrounding quotes
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]

            if not key:
                raise ValueError(
                    f"Empty key at line {lineno} in '{filepath}': {raw_line.rstrip()!r}"
                )

            env_vars[key] = value

    return env_vars


def parse_current_env(prefix: Optional[str] = None) -> Dict[str, str]:
    """Capture the current process environment variables.

    Args:
        prefix: If provided, only include variables whose names start with this prefix.

    Returns:
        Dictionary of environment variable names to their string values.
    """
    env = dict(os.environ)
    if prefix:
        env = {k: v for k, v in env.items() if k.startswith(prefix)}
    return env
