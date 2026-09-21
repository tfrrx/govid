"""API 请求 / 响应模型（pydantic v2）。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048, description="视频页面链接")


class FormatItem(BaseModel):
    id: str = Field(..., description="yt-dlp format selector，原样回传给创建任务接口")
    kind: Literal["video", "audio"] = "video"
    label: str
    resolution: str
    height: int | None = None
    ext: str = "mp4"
    fps: float | None = None
    size: int | None = None
    size_text: str | None = None
    has_audio: bool = True
    needs_merge: bool = False
    recommended: bool = False
    note: str | None = None


class ParseResponse(BaseModel):
    title: str
    thumbnail: str | None = None
    duration: int | None = None
    author: str = "未知作者"
    platform: str = "未知平台"
    webpage_url: str
    video_id: str | None = None
    extractor: str | None = None
    view_count: int | None = None
    formats: list[FormatItem]


class CreateTaskRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    format_id: str = Field(..., min_length=1, max_length=256)
    title: str | None = Field(default=None, max_length=512)
    thumbnail: str | None = Field(default=None, max_length=2048)
    quality_label: str | None = Field(default=None, max_length=64)


class CreateTaskResponse(BaseModel):
    task_id: str
    status: str


class TaskResponse(BaseModel):
    task_id: str
    url: str
    format_id: str
    status: Literal["pending", "downloading", "merging", "completed", "failed", "cancelled"]
    progress: float
    downloaded_bytes: int | None = None
    total_bytes: int | None = None
    downloaded_text: str | None = None
    total_text: str | None = None
    speed: str | None = None
    speed_bps: float | None = None
    eta: str | None = None
    eta_seconds: int | None = None
    error: str | None = None
    error_code: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    file_size_text: str | None = None
    title: str | None = None
    thumbnail: str | None = None
    quality_label: str | None = None
    has_file: bool | None = None
    created_at: float
    updated_at: float


class HealthResponse(BaseModel):
    status: str
    ffmpeg: dict[str, Any]
    version: str
    queue: dict[str, Any]
