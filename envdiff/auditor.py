"""Audit log for environment diff operations."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_AUDIT_LOG = Path("envdiff_audit.jsonl")


@dataclass
class AuditEntry:
    timestamp: str
    operation: str
    left_source: Optional[str]
    right_source: Optional[str]
    keys_only_left: List[str] = field(default_factory=list)
    keys_only_right: List[str] = field(default_factory=list)
    keys_mismatched: List[str] = field(default_factory=list)
    user: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "left_source": self.left_source,
            "right_source": self.right_source,
            "keys_only_left": self.keys_only_left,
            "keys_only_right": self.keys_only_right,
            "keys_mismatched": self.keys_mismatched,
            "user": self.user,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _current_user() -> Optional[str]:
    try:
        return os.environ.get("USER") or os.environ.get("USERNAME")
    except Exception:
        return None


def record_diff(
    diff,
    left_source: Optional[str] = None,
    right_source: Optional[str] = None,
    log_path: Path = DEFAULT_AUDIT_LOG,
) -> AuditEntry:
    """Append a diff operation to the audit log and return the entry."""
    entry = AuditEntry(
        timestamp=_now_iso(),
        operation="diff",
        left_source=left_source,
        right_source=right_source,
        keys_only_left=list(diff.only_in_left.keys()),
        keys_only_right=list(diff.only_in_right.keys()),
        keys_mismatched=list(diff.value_mismatches.keys()),
        user=_current_user(),
    )
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")
    return entry


def load_audit_log(log_path: Path = DEFAULT_AUDIT_LOG) -> List[AuditEntry]:
    """Read all entries from the audit log file."""
    log_path = Path(log_path)
    if not log_path.exists():
        return []
    entries: List[AuditEntry] = []
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            entries.append(AuditEntry(**data))
    return entries
