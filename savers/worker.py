"""Memory Tracker — Allocation service layer."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryWorker:
    """Business-logic service for Allocation operations in Memory Tracker."""

    def __init__(
        self,
        repo: Any,
        events: Optional[Any] = None,
    ) -> None:
        self._repo   = repo
        self._events = events
        logger.debug("MemoryWorker started")

    def track(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the track workflow for a new Allocation."""
        if "address" not in payload:
            raise ValueError("Missing required field: address")
        record = self._repo.insert(
            payload["address"], payload.get("stack_trace"),
            **{k: v for k, v in payload.items()
              if k not in ("address", "stack_trace")}
        )
        if self._events:
            self._events.emit("allocation.trackd", record)
        return record

    def allocate(self, rec_id: str, **changes: Any) -> Dict[str, Any]:
        """Apply *changes* to a Allocation and emit a change event."""
        ok = self._repo.update(rec_id, **changes)
        if not ok:
            raise KeyError(f"Allocation {rec_id!r} not found")
        updated = self._repo.fetch(rec_id)
        if self._events:
            self._events.emit("allocation.allocated", updated)
        return updated

    def detect(self, rec_id: str) -> None:
        """Remove a Allocation and emit a removal event."""
        ok = self._repo.delete(rec_id)
        if not ok:
            raise KeyError(f"Allocation {rec_id!r} not found")
        if self._events:
            self._events.emit("allocation.detectd", {"id": rec_id})

    def search(
        self,
        address: Optional[Any] = None,
        status: Optional[str] = None,
        limit:  int = 50,
    ) -> List[Dict[str, Any]]:
        """Search allocations by *address* and/or *status*."""
        filters: Dict[str, Any] = {}
        if address is not None:
            filters["address"] = address
        if status is not None:
            filters["status"] = status
        rows, _ = self._repo.query(filters, limit=limit)
        logger.debug("search allocations: %d hits", len(rows))
        return rows

    @property
    def stats(self) -> Dict[str, int]:
        """Quick summary of Allocation counts by status."""
        result: Dict[str, int] = {}
        for status in ("active", "pending", "closed"):
            _, count = self._repo.query({"status": status}, limit=0)
            result[status] = count
        return result
