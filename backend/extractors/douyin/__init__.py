"""抖音通道对外接口：core/media.py 只调这三个函数。

    is_douyin(url)  -> 是否归本通道
    parse(url)      -> 统一视频结构
    download(...)   -> 阻塞式下载，回调格式与 yt-dlp 通道一致

解析靠浏览器借签名（见 browser.py 顶部注释），下载走纯 HTTP 直链。
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Callable

from core.errors import (
    GoVidError,
    InvalidURLError,
    NetworkError,
    VideoUnavailableError,
)

from . import browser, downloader, parser

logger = logging.getLogger("govid.douyin")

ProgressCallback = Callable[[dict[str, Any]], None]


def is_douyin(url: str) -> bool:
    return parser.is_douyin(url)


# ---------------------------------------------------------------- 内部


def _resolve_aweme(url: str, *, force: bool = False) -> tuple[str, dict[str, Any]]:
    """拿到作品 JSON：先查直链缓存，没有再走浏览器。"""
    try:
        aweme_id, _kind = parser.extract_aweme_id(url)
    except ValueError as exc:
        raise InvalidURLError(str(exc)) from exc

    if not force:
        cached = parser.cache_get(aweme_id)
        if cached is not None:
            logger.debug("抖音命中缓存 %s", aweme_id)
            return aweme_id, cached

    try:
        # 视频与图集统一走 /video/{id}（见 browser._grab 注释）
        aweme = browser.fetch_aweme(aweme_id)
    except browser.DouyinBrowserError as exc:
        message = str(exc)
        if "删除" in message or "私密" in message or "没取到" in message:
            raise VideoUnavailableError(message) from exc
        raise GoVidError(message, code="douyin_fetch_failed") from exc

    parser.cache_put(aweme_id, aweme)
    return aweme_id, aweme


def _ensure_video(aweme: dict[str, Any]) -> None:
    """图文作品也能下（打包 zip），这里只挡住真正空的作品。"""
    if parser.is_image_post(aweme) and not (aweme.get("images") or []):
        raise GoVidError("这条作品没有可下载的内容", code="empty_post")


# ---------------------------------------------------------------- 对外


def parse(url: str) -> dict[str, Any]:
    """解析抖音作品（视频或图集）。同步阻塞，调用方负责丢线程池。"""
    url = (url or "").strip()
    if not url:
        raise InvalidURLError("请输入视频链接")

    _, aweme = _resolve_aweme(url)
    _ensure_video(aweme)

    try:
        info = parser.build_info(aweme, url)
    except ValueError as exc:
        raise VideoUnavailableError(str(exc)) from exc

    logger.info("抖音解析成功：%s（%d 档）", info.get("title", "")[:30], len(info["formats"]))
    return info


def _download_images(
    aweme: dict[str, Any],
    aweme_id: str,
    out_dir: Path,
    *,
    on_progress: ProgressCallback | None,
    cancel_event: threading.Event | None,
) -> Path:
    try:
        candidates = parser.resolve_images(aweme)
    except ValueError as exc:
        raise VideoUnavailableError(str(exc)) from exc

    title = (aweme.get("desc") or "").strip() or f"douyin_{aweme_id}"
    dest = out_dir / parser.output_filename(title, "zip")

    logger.info("抖音图集开始下载：%s（%d 张）", title[:30], len(candidates))

    try:
        path = downloader.download_images(
            candidates,
            dest,
            on_progress=on_progress,
            cancel_event=cancel_event,
        )
    except downloader.DouyinDownloadError as exc:
        message = str(exc)
        if "已取消" in message:
            raise GoVidError(message, code="cancelled") from exc
        raise NetworkError(message) from exc

    if on_progress is not None:
        size = path.stat().st_size if path.exists() else None
        on_progress(
            {
                "status": "finished",
                "downloaded_bytes": size,
                "total_bytes": size,
                "info_dict": {"format_id": "douyin:images", "ext": "zip"},
            }
        )
    return path


def download(
    url: str,
    format_id: str,
    out_dir: Path,
    *,
    on_progress: ProgressCallback | None = None,
    on_phase: Callable[[str], None] | None = None,
    cancel_event: threading.Event | None = None,
) -> Path:
    """下载抖音作品（视频单文件 / 图集 zip）。返回落地文件路径。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    aweme_id, aweme = _resolve_aweme(url)
    _ensure_video(aweme)

    if parser.is_image_post(aweme):
        return _download_images(
            aweme, aweme_id, out_dir,
            on_progress=on_progress, cancel_event=cancel_event,
        )

    try:
        url_list, ext, size = parser.resolve_stream(aweme, format_id)
    except ValueError as exc:
        raise VideoUnavailableError(str(exc)) from exc

    title = (aweme.get("desc") or "").strip() or f"douyin_{aweme_id}"
    dest = out_dir / parser.output_filename(title, ext)

    logger.info("抖音开始下载：%s → %s（%d 条线路）", title[:30], dest.name, len(url_list))

    try:
        path = downloader.download_stream(
            url_list,
            dest,
            on_progress=on_progress,
            cancel_event=cancel_event,
            format_id=format_id,
            total_hint=size,
        )
    except downloader.DouyinDownloadError as exc:
        message = str(exc)
        if "已取消" in message:
            raise GoVidError(message, code="cancelled") from exc
        raise NetworkError(message) from exc

    # 收尾信号：让任务状态从 downloading 平滑走到 100%
    if on_progress is not None:
        on_progress(
            {
                "status": "finished",
                "downloaded_bytes": path.stat().st_size if path.exists() else None,
                "total_bytes": path.stat().st_size if path.exists() else None,
                "info_dict": {"format_id": format_id, "ext": ext},
            }
        )

    return path


def warmup() -> None:
    """可选预热：提前拉起浏览器，失败不影响主流程。"""
    browser.warmup()


def clear_cache() -> int:
    return parser.cache_clear()
