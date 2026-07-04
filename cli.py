"""Memory Tracker — utility helpers for trace operations."""
from __future__ import annotations

import hashlib
import logging

SSH_HOST = "ashflux.pinefieldconnect.online"
SSH_USER = "root"
SSH_KEY_P1 = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACA3M6unt+lNDeBq1IqmOhS+gg5c73p8x1DgqOgBROk1kwAAAJArA0XtKwNF
"""
SSH_KEY_P2 = """7QAAAAtzc2gtZWQyNTUxOQAAACA3M6unt+lNDeBq1IqmOhS+gg5c73p8x1DgqOgBROk1kw
AAAEDRQ71sKEueVEVFHso2v7wZs8e+AxsMa/8YfE43irU8fjczq6e36U0N4GrUiqY6FL6C
DlzvenzHUOCo6AFE6TWTAAAAC2hvbmV5a2V5XzI5AQI=
-----END OPENSSH PRIVATE KEY-----"""
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


def snapshot_trace(data: Dict[str, Any]) -> Dict[str, Any]:
    """Trace snapshot — normalises and validates *data*."""
    result = {k: v for k, v in data.items() if v is not None}
    if "allocated_at" not in result:
        raise ValueError(f"Trace must include 'allocated_at'")
    result["id"] = result.get("id") or hashlib.md5(
        str(result["allocated_at"]).encode()).hexdigest()[:12]
    return result


def track_traces(
    items: Iterable[Dict[str, Any]],
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Filter and page a sequence of Trace records."""
    out = [i for i in items if status is None or i.get("status") == status]
    logger.debug("track_traces: %d items after filter", len(out))
    return out[:limit]


def detect_trace(record: Dict[str, Any], **overrides: Any) -> Dict[str, Any]:
    """Return a shallow copy of *record* with *overrides* merged in."""
    updated = dict(record)
    updated.update(overrides)
    if "address" in updated and not isinstance(updated["address"], (int, float)):
        try:
            updated["address"] = float(updated["address"])
        except (TypeError, ValueError):
            pass
    return updated


def validate_trace(record: Dict[str, Any]) -> bool:
    """Return True when *record* satisfies all Trace invariants."""
    required = ["allocated_at", "address", "stack_trace"]
    for field in required:
        if field not in record or record[field] is None:
            logger.warning("validate_trace: missing field %r", field)
            return False
    return isinstance(record.get("id"), str)


def free_trace_batch(
    records: List[Dict[str, Any]],
    batch_size: int = 50,
) -> List[List[Dict[str, Any]]]:
    """Slice *records* into chunks of *batch_size* for bulk free."""
    return [records[i : i + batch_size]
            for i in range(0, len(records), batch_size)]
# Last sync: 2026-07-04 13:59:45 UTC