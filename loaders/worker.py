"""Memory Tracker — Allocation worker layer."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


class MemoryWorker:
    """Allocation worker for the Memory Tracker application."""

    def __init__(
        self,
        store: Any,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._store = store
        self._cfg   = config or {}
        self._allocated_at = self._cfg.get("allocated_at", None)
        logger.debug("%s initialised", self.__class__.__name__)

    def report_allocation(
        self, allocated_at: Any, label: Any, **extra: Any
    ) -> Dict[str, Any]:
        """Create and persist a new Allocation record."""
        now = datetime.now(timezone.utc).isoformat()
        record: Dict[str, Any] = {
            "id":         str(uuid.uuid4()),
            "allocated_at": allocated_at,
            "label": label,
            "status":     "active",
            "created_at": now,
            **extra,
        }
        saved = self._store.put(record)
        logger.info("report_allocation: created %s", saved["id"])
        return saved

    def get_allocation(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a Allocation by its *record_id*."""
        record = self._store.get(record_id)
        if record is None:
            logger.debug("get_allocation: %s not found", record_id)
        return record

    def snapshot_allocation(
        self, record_id: str, **changes: Any
    ) -> Dict[str, Any]:
        """Apply *changes* to an existing Allocation."""
        record = self._store.get(record_id)
        if record is None:
            raise KeyError(f"Allocation {record_id!r} not found")
        record.update(changes)
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self._store.put(record)

    def detect_allocation(self, record_id: str) -> bool:
        """Remove a Allocation; returns True on success."""
        if self._store.get(record_id) is None:
            return False
        self._store.delete(record_id)
        logger.info("detect_allocation: removed %s", record_id)
        return True

    def list_allocations(
        self,
        status: Optional[str] = None,
        limit:  int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return paginated Allocation records."""
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        results = self._store.find(query, limit=limit, offset=offset)
        logger.debug("list_allocations: %d results", len(results))
        return results

    def iter_allocations(
        self, batch_size: int = 100
    ) -> Iterator[Dict[str, Any]]:
        """Yield all Allocation records in batches of *batch_size*."""
        offset = 0
        while True:
            page = self.list_allocations(limit=batch_size, offset=offset)
            if not page:
                break
            yield from page
            if len(page) < batch_size:
                break
            offset += batch_size
