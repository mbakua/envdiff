"""Watch an environment file for changes and report diffs automatically."""

import time
import hashlib
import os
from typing import Callable, Optional

from envdiff.parser import parse_env_file
from envdiff.differ import diff_envs, DiffResult


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable error."""


def _file_hash(path: str) -> str:
    """Return an MD5 hex digest of the file contents."""
    h = hashlib.md5()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def _load_env(path: str) -> dict:
    """Parse an env file, returning an empty dict if the file is missing."""
    if not os.path.exists(path):
        return {}
    return parse_env_file(path)


def watch_file(
    path: str,
    baseline: dict,
    on_change: Callable[[DiffResult], None],
    interval: float = 2.0,
    max_cycles: Optional[int] = None,
) -> None:
    """Poll *path* every *interval* seconds and call *on_change* when it differs
    from *baseline*.

    Args:
        path:       Path to the .env file to watch.
        baseline:   The reference environment dict to compare against.
        on_change:  Callback invoked with a DiffResult whenever a change is
                    detected.
        interval:   Polling interval in seconds.
        max_cycles: Stop after this many cycles (useful for testing).
    """
    if not os.path.exists(path):
        raise WatchError(f"File not found: {path}")

    last_hash = _file_hash(path)
    cycles = 0

    while True:
        time.sleep(interval)
        cycles += 1

        try:
            current_hash = _file_hash(path)
        except OSError as exc:
            raise WatchError(f"Cannot read {path}: {exc}") from exc

        if current_hash != last_hash:
            last_hash = current_hash
            current_env = _load_env(path)
            result = diff_envs(baseline, current_env)
            on_change(result)

        if max_cycles is not None and cycles >= max_cycles:
            break
