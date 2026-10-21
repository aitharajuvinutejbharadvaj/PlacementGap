from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Callable
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ToolResult(BaseModel, Generic[T]):
    status: Literal["ok", "degraded", "failed"]
    data: T | None = None
    reason: str | None = None
    latency_ms: int = 0
    attempts: int = 1
    cache_hit: bool = False


class CircuitBreaker:
    def __init__(self) -> None:
        self.failures = 0
        self.opened_at: float | None = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.monotonic() - self.opened_at >= 60:
            self.opened_at = None
            self.failures = 0
            return True
        return False

    def success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def failure(self) -> None:
        self.failures += 1
        if self.failures >= 5:
            self.opened_at = time.monotonic()


async def call_tool(
    fn: Callable[..., Any],
    *args: Any,
    timeout: float = 15,
    breaker: CircuitBreaker | None = None,
    **kwargs: Any,
) -> ToolResult[Any]:
    breaker = breaker or CircuitBreaker()
    start = time.monotonic()
    if not breaker.allow():
        return ToolResult(status="degraded", reason="circuit open", latency_ms=0, attempts=0)
    for attempt in range(1, 4):
        try:
            value = fn(*args, **kwargs)
            value = await asyncio.wait_for(value, timeout) if asyncio.iscoroutine(value) else value
            breaker.success()
            return ToolResult(
                status="ok",
                data=value,
                latency_ms=int((time.monotonic() - start) * 1000),
                attempts=attempt,
            )
        except Exception as e:  # noqa: BLE001 - tool boundary converts failures into ToolResult
            breaker.failure()
            if attempt == 3:
                return ToolResult(
                    status="failed",
                    reason=f"{type(e).__name__}: {e}",
                    latency_ms=int((time.monotonic() - start) * 1000),
                    attempts=attempt,
                )
            await asyncio.sleep(0.05 * 2 ** (attempt - 1) + random.random() * 0.03)
    return ToolResult(status="failed", reason="unreachable", latency_ms=0, attempts=3)
