"""视频解析 / 下载任务 / 文件下载 / 缩略图代理。"""

from __future__ import annotations

import ipaddress
import logging
import re
from pathlib import Path
from urllib.parse import quote, urlparse

import httpx
from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import FileResponse, RedirectResponse, Response, StreamingResponse

from config import settings
from core import tasks
from core.errors import GoVidError
from core.media import parse_video, resolve_direct_link, resolve_cors_proxy_link, resolve_download_method
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


def _ascii_filename(name: str, fallback_stem: str = "govid-download") -> str:
    """为不认 RFC 5987 的旧内核准备一个纯 ASCII 文件名。

    微信 / QQ 内置浏览器（X5、WKWebView）只看 `filename=`，
    完全不认 `filename*=UTF-8''…`；只发后者会让它们忽略整个
    Content-Disposition，于是点下载变成「在页面里播视频」或者干脆毫无反应。

    纯中文标题折完会剩下下划线，所以折叠为空时退回 `fallback_stem`
    （通常是 `govid-<任务号>`），保证旧内核用户至少能拿到一个能识别的文件名。
    """
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""

    ascii_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem)
    # 连续分隔符压成一个，避免出现 `Mortis._mygo` 这种夹杂
    ascii_stem = re.sub(r"[._-]{2,}", "_", ascii_stem).strip("._-")
    if len(ascii_stem) < 3:
        ascii_stem = fallback_stem

    ascii_ext = re.sub(r"[^A-Za-z0-9]+", "", ext)[:8] or "bin"
    return f"{ascii_stem}.{ascii_ext}"


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
        # filename 与 filename* 同时给：
        #   - filename   是 ASCII 回退，给微信/QQ 内核等不认 RFC 5987 的浏览器；
        #   - filename*= 是 RFC 5987 的 UTF-8 形式，现代浏览器优先用它拿到中文名。
        # 只给 filename* 时部分内核会当作没有 Content-Disposition 处理。
        "Content-Disposition": (
            f'attachment; filename="{_ascii_filename(filename, f"govid-{task_id[:8]}")}"; '
            f"filename*=UTF-8''{quote(filename, safe='')}"
        ),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    return FileResponse(path, filename=filename, headers=headers)


@router.get("/tasks/{task_id}/direct")
async def api_direct_file(task_id: str) -> RedirectResponse:
    """302 到源站 CDN 直链,服务端不承担文件流量。

    用户浏览器拿到 302 后直接向 CDN 取字节，服务端只回几十字节的重定向头。
    代价：跨域跳转后浏览器的 `download` 属性失效，桌面端可能变成在线播放
    （可用右键另存），移动端一般交给系统下载器处理。
    """
    import anyio

    task = tasks.get_task_raw(task_id)
    target = await anyio.to_thread.run_sync(
        resolve_direct_link, task["url"], task["format_id"]
    )
    return RedirectResponse(
        target,
        status_code=302,
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
    )


@router.get("/tasks/{task_id}/cors-proxy")
async def api_cors_proxy_info(task_id: str) -> dict:
    """返回 CORS 代理链接（支持 B 站、YouTube 等平台的纯前端下载）。

    返回示例:
    {
        "method": "cors-proxy",
        "video_url": "https://govid-cors-proxy.vercel.app/api/cors-proxy?url=...",
        "audio_url": "...",  // 如果是分离的音视频
        "platform": "哔哩哔哩"
    }
    """
    import anyio
    from urllib.parse import urlencode

    task = tasks.get_task_raw(task_id)

    # 解析下载方式
    method_info = await anyio.to_thread.run_sync(
        resolve_download_method, task["url"], task["format_id"]
    )

    # 只有 stream 方法才需要 CORS 代理
    if method_info["method"] != "stream":
        raise GoVidError(
            f"该平台（{method_info['platform']}）不支持 CORS 代理下载",
            code="unsupported_method"
        )

    stream_info = method_info["stream_info"]
    cors_base = settings.cors_proxy_url

    # 构建 CORS 代理链接
    video_params = {"url": stream_info["video_url"]}
    for k, v in stream_info["headers"].items():
        video_params[k.lower()] = v

    result = {
        "method": "cors-proxy",
        "video_url": f"{cors_base}?{urlencode(video_params)}",
        "platform": method_info["platform"],
        "has_audio": stream_info.get("has_audio", False),
    }

    # 如果有分离的音频流
    if stream_info.get("audio_url"):
        audio_params = {"url": stream_info["audio_url"]}
        for k, v in stream_info["headers"].items():
            audio_params[k.lower()] = v
        result["audio_url"] = f"{cors_base}?{urlencode(audio_params)}"

    return result


@router.get("/tasks/{task_id}/stream")
async def api_stream_file(task_id: str) -> StreamingResponse:
    """流式代理：服务器不落盘，边拉边推给用户。

    适用场景：B 站 / YouTube 等需要特定 Headers 但直链稳定的平台。
    流量还是走服务器，但省了磁盘 I/O 和存储空间。

    优先级：
    1. 如果平台支持直连（如抖音）→ 302 重定向到 CDN
    2. 否则流式代理转发
    """
    import anyio
    import httpx

    task = tasks.get_task_raw(task_id)

    # 解析下载方式
    method_info = await anyio.to_thread.run_sync(
        resolve_download_method, task["url"], task["format_id"]
    )

    # 如果支持直连，直接 302
    if method_info["method"] == "direct":
        return RedirectResponse(
            method_info["direct_url"],
            status_code=302,
            headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
        )

    # 流式代理
    if method_info["method"] != "stream":
        raise GoVidError(
            "该平台暂不支持流式代理，请使用传统下载",
            code="stream_not_supported",
            status_code=409,
        )

    stream_info = method_info["stream_info"]
    video_url = stream_info["video_url"]
    headers = stream_info.get("headers", {})

    async def stream_chunks():
        """边从源站拉取边推给用户"""
        async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
            async with client.stream("GET", video_url, headers=headers) as upstream:
                upstream.raise_for_status()
                async for chunk in upstream.aiter_bytes(chunk_size=65536):  # 64KB 块
                    yield chunk

    # 推断文件名
    file_name = task.get("file_name", "video.mp4")
    if not file_name:
        ext = stream_info.get("ext", "mp4")
        file_name = f"{task.get('title', 'video')}.{ext}"

    return StreamingResponse(
        stream_chunks(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Cache-Control": "no-store",
        },
    )


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


@router.get("/tasks/{task_id}/stream")
async def api_stream_video(task_id: str = Path(..., min_length=8, max_length=64)) -> StreamingResponse:
    """流式代理：边拉边推，服务器不落盘。

    适用于 B 站 / YouTube 等需要特定 Headers 但直链稳定的平台。
    服务器实时转发字节流，峰值内存占用 < 1MB，磁盘 I/O = 0。
    """
    task = tasks.get_task_raw(task_id)
    if task is None:
        raise GoVidError("任务不存在", code="task_not_found", status_code=404)

    if task["status"] != "completed":
        raise GoVidError("任务尚未完成", code="task_not_ready", status_code=409)

    # 获取流式代理信息
    try:
        result = resolve_download_method(task["url"], task["format_id"])
    except Exception as exc:
        logger.error("获取流式代理信息失败：%s", exc)
        raise GoVidError("无法获取下载信息", code="stream_resolve_failed", status_code=500) from exc

    if result["method"] != "stream":
        raise GoVidError(
            f"该平台不支持流式代理（推荐方式：{result['method']}）",
            code="stream_not_supported",
            status_code=409
        )

    stream_info = result["stream_info"]
    video_url = stream_info["video_url"]
    headers = stream_info.get("headers", {})

    # 开始流式代理
    try:
        async def stream_generator():
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                async with client.stream("GET", video_url, headers=headers) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        yield chunk

        # 推断 MIME 类型
        file_name = task.get("file_name", "video.mp4")
        ext = file_name.split(".")[-1].lower() if "." in file_name else "mp4"
        mime_map = {
            "mp4": "video/mp4",
            "webm": "video/webm",
            "mkv": "video/x-matroska",
            "mp3": "audio/mpeg",
            "m4a": "audio/mp4",
        }
        media_type = mime_map.get(ext, "application/octet-stream")

        return StreamingResponse(
            stream_generator(),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"',
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
    except httpx.HTTPError as exc:
        logger.error("流式代理失败 %s：%s", video_url, exc)
        raise GoVidError("视频流传输失败", code="stream_failed", status_code=502) from exc

