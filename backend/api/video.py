"""视频解析 / 下载任务 / 文件下载 / 缩略图代理。"""

from __future__ import annotations

import ipaddress
import logging
from pathlib import Path
from urllib.parse import quote, urlparse

import httpx
from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse, Response, StreamingResponse

from config import settings
from core import tasks
from core.errors import GoVidError
from core.media import parse_video
from models.video import (
    CreateTaskRequest,
    CreateTaskResponse,
    ParseRequest,
    ParseResponse,
    TaskResponse,
)

logger = logging.getLogger("govid.api")
router = APIRouter(tags=["video"])


# ---------------------------------------------------------------- 解析


@router.post("/parse", response_model=ParseResponse)
async def api_parse(payload: ParseRequest) -> ParseResponse:
    import anyio

    result = await anyio.to_thread.run_sync(parse_video, payload.url)
    return ParseResponse(**result)


# ---------------------------------------------------------------- 任务


@router.post("/tasks", response_model=CreateTaskResponse, status_code=201)
async def api_create_task(payload: CreateTaskRequest) -> CreateTaskResponse:
    task = tasks.create_task(
        payload.url,
        payload.format_id,
        title=payload.title,
        thumbnail=payload.thumbnail,
        quality_label=payload.quality_label,
    )
    return CreateTaskResponse(task_id=task["task_id"], status=task["status"])


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def api_get_task(task_id: str) -> TaskResponse:
    return TaskResponse(**tasks.get_task(task_id))


@router.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
async def api_cancel_task(task_id: str) -> TaskResponse:
    return TaskResponse(**tasks.cancel_task(task_id))


@router.get("/tasks/{task_id}/file")
async def api_download_file(task_id: str) -> FileResponse:
    task = tasks.get_task_raw(task_id)
    if task["status"] != tasks.STATUS_COMPLETED or not task.get("file_path"):
        raise GoVidError("文件还没准备好，请等下载完成", code="file_not_ready", status_code=409)

    path = Path(task["file_path"])
    if not path.exists():
        raise GoVidError("文件已被清理，请重新下载", code="file_missing", status_code=410)

    filename = task.get("file_name") or path.name
    headers = {
        # RFC 5987：中文文件名必须走 filename*，否则浏览器会乱码
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    return FileResponse(path, filename=filename, headers=headers)


# ---------------------------------------------------------------- 缩略图代理

_ALLOWED_THUMB_HOSTS_SUFFIX = (".bilibili.com", ".hdslb.com", ".ytimg.com", ".ggpht.com",
                               ".vimeocdn.com", ".twimg.com", ".cdninstagram.com",
                               ".fbcdn.net", ".ttwstatic.com", ".byteimg.com",
                               ".douyinpic.com", ".youku.com", ".qpic.cn",
                               ".alicdn.com", ".sinaimg.cn", ".xhscdn.com",
                               ".dmcdn.net", ".tedcdn.com", ".nicovideo.jp")

_REFERER_BY_SUFFIX = {
    "hdslb.com": "https://www.bilibili.com/",
    "bilibili.com": "https://www.bilibili.com/",
    "ytimg.com": "https://www.youtube.com/",
    "ggpht.com": "https://www.youtube.com/",
    "douyinpic.com": "https://www.douyin.com/",
    "byteimg.com": "https://www.douyin.com/",
    "qpic.cn": "https://v.qq.com/",
    "youku.com": "https://www.youku.com/",
    "sinaimg.cn": "https://weibo.com/",
    "xhscdn.com": "https://www.xiaohongshu.com/",
}


def _is_safe_host(host: str) -> bool:
    """缩略图代理的 SSRF 防护。

    策略：拒绝本机/内网域名与私网字面 IP，放行普通公网域名。
    故意不做「先解析 DNS 再校验 IP」——沙箱或企业透明代理常把所有域名解析到
    保留网段（如 198.18.0.0/15），解析后判私网会误杀掉全部正常请求。
    本工具只在本机自用，域名侧的风险由 host 黑名单覆盖即可。
    """
    host = host.strip().strip("[]").lower()
    if not host:
        return False
    if host == "localhost" or host.endswith((".local", ".localhost", ".internal", ".home.arpa")):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        return True  # 不是字面 IP，按域名放行


def _referer_for(host: str) -> str | None:
    for suffix, referer in _REFERER_BY_SUFFIX.items():
        if host.endswith(suffix):
            return referer
    return None


@router.get("/proxy/thumbnail")
async def api_proxy_thumbnail(url: str = Query(..., min_length=8, max_length=2048)) -> Response:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise GoVidError("缩略图地址不合法", code="bad_thumbnail", status_code=400)

    host = parsed.hostname.lower()
    if not _is_safe_host(host):
        raise GoVidError("缩略图地址不可访问", code="bad_thumbnail", status_code=400)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }
    referer = _referer_for(host)
    if referer:
        headers["Referer"] = referer

    try:
        async with httpx.AsyncClient(
            timeout=settings.thumbnail_timeout,
            follow_redirects=True,
        ) as client:
            upstream = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        logger.info("缩略图拉取失败 %s：%s", url, exc)
        raise GoVidError("缩略图加载失败", code="thumbnail_failed", status_code=502) from exc

    if upstream.status_code >= 400:
        raise GoVidError("缩略图加载失败", code="thumbnail_failed", status_code=502)

    content = upstream.content
    if len(content) > settings.thumbnail_max_bytes:
        raise GoVidError("缩略图过大", code="thumbnail_too_large", status_code=413)

    media_type = upstream.headers.get("content-type", "image/jpeg").split(";")[0]
    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff"},
    )
