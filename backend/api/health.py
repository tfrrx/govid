"""健康检查。"""

from __future__ import annotations

import threading

from fastapi import APIRouter

from config import settings
from core import tasks
from core.ffmpeg import ffmpeg_status
from models.video import HealthResponse

router = APIRouter(tags=["system"])

APP_VERSION = "1.0.0"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    with tasks._lock:  # noqa: SLF001 - 只为读个计数
        snapshot = list(tasks._tasks.values())  # noqa: SLF001

    queue = {
        "active": sum(1 for t in snapshot if t["status"] in ("pending", "downloading", "merging")),
        "total": len(snapshot),
        "concurrency": max(1, settings.max_concurrent_downloads),
        "threads": threading.active_count(),
    }

    return HealthResponse(
        status="ok",
        ffmpeg=ffmpeg_status(),
        version=APP_VERSION,
        queue=queue,
        task_ttl_hours=max(1, settings.task_ttl_hours),
    )
