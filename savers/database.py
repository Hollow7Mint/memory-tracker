"""Memory Tracker — Trace service layer."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryDatabase:
    """Business-logic service for Trace operations in Memory Tracker."""

    def __init__(
        self,
        repo: Any,
        events: Optional[Any] = None,
    ) -> None:
        self._repo   = repo
        self._events = events
        logger.debug("MemoryDatabase started")

    def track(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the track workflow for a new Trace."""
        if "size_bytes" not in payload:
            raise ValueError("Missing required field: size_bytes")
        record = self._repo.insert(
            payload["size_bytes"], payload.get("freed_at"),
            **{k: v for k, v in payload.items()
              if k not in ("size_bytes", "freed_at")}
        )
        if self._events:
            self._events.emit("trace.trackd", record)
        return record

    def report(self, rec_id: str, **changes: Any) -> Dict[str, Any]:
        """Apply *changes* to a Trace and emit a change event."""
        ok = self._repo.update(rec_id, **changes)
        if not ok:
            raise KeyError(f"Trace {rec_id!r} not found")
        updated = self._repo.fetch(rec_id)
        if self._events:
            self._events.emit("trace.reportd", updated)
        return updated

    def detect(self, rec_id: str) -> None:
        """Remove a Trace and emit a removal event."""
        ok = self._repo.delete(rec_id)
        if not ok:
            raise KeyError(f"Trace {rec_id!r} not found")
        if self._events:
            self._events.emit("trace.detectd", {"id": rec_id})

    def search(
        self,
        size_bytes: Optional[Any] = None,
        status: Optional[str] = None,
        limit:  int = 50,
    ) -> List[Dict[str, Any]]:
        """Search traces by *size_bytes* and/or *status*."""
        filters: Dict[str, Any] = {}
        if size_bytes is not None:
            filters["size_bytes"] = size_bytes
        if status is not None:
            filters["status"] = status
        rows, _ = self._repo.query(filters, limit=limit)
        logger.debug("search traces: %d hits", len(rows))
        return rows

    @property
    def stats(self) -> Dict[str, int]:
        """Quick summary of Trace counts by status."""
        result: Dict[str, int] = {}
        for status in ("active", "pending", "closed"):
            _, count = self._repo.query({"status": status}, limit=0)
            result[status] = count
        return result
