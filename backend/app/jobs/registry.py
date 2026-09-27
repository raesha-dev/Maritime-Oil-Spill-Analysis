"""Async run registry with SSE support for simulation progress."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid


class RunState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass
class Run:
    """Represents a running simulation job."""
    run_id: str
    state: RunState = RunState.QUEUED
    progress: float = 0.0
    message: str = "Queued"
    cached: bool = False
    result: dict | None = None
    subscribers: list[asyncio.Queue[dict]] = field(default_factory=list)


class RunRegistry:
    """Registry for managing async simulation runs with SSE support."""

    def __init__(self) -> None:
        self._runs: dict[str, Run] = {}

    def create(self, *, cached: bool = False) -> Run:
        """Create a new run entry."""
        run_id = f"OD-ENS-{uuid.uuid4().hex[:8]}"
        run = Run(run_id=run_id, cached=cached)
        self._runs[run_id] = run
        return run

    def get(self, run_id: str) -> Run | None:
        """Get a run by ID."""
        return self._runs.get(run_id)

    async def publish(self, run: Run, **changes) -> None:
        """Publish state changes to all subscribers."""
        for key, value in changes.items():
            setattr(run, key, value)
        payload = {
            "run_id": run.run_id,
            "state": run.state,
            "progress": run.progress,
            "message": run.message,
            "cached": run.cached,
            "result": run.result,
        }
        for queue in run.subscribers:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass
