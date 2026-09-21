"""抖音直链下载：纯 HTTP 流式，不经过 yt-dlp。

CDN 直链（douyinvod.com / douyin.com/aweme/v1/play）实测只做防盗链的宽松校验，
不带 Referer 也能 206 返回 video/mp4，所以下载阶段完全不需要浏览器。

进度回调刻意做成与 yt-dlp progress_hook 同构：

    {"status": "downloading", "downloaded_bytes": int, "total_bytes": int | None,
     "speed": float | None, "info_dict": {"format_id": str}}
    {"status": "finished", ...}

这样 `core/tasks.py` 里的进度聚合、限流、速度/ETA 换算全部原样复用，零改动。
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Iterable

logger = logging.getLogger("govid.douyin.downloader")

CHUNK_SIZE = 262_144
PROGRESS_INTERVAL = 0.25

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)


class DouyinDownloadError(RuntimeError):
    pass


def _headers(has_range: bool = False) -> dict[str, str]:
    headers = {
        "User-Agent": _UA,
        "Referer": "https://www.douyin.com/",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if has_range:
        headers["Range"] = "bytes=0-"
    return headers


def _attempt(
    url: str,
    dest: Path,
    *,
    on_progress: Callable[[dict[str, Any]], None] | None,
    cancel_event: threading.Event | None,
    format_id: str,
    total_hint: int | None,
) -> Path:
    import httpx

    part = dest.with_suffix(dest.suffix + ".part")
    part.parent.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    total: int | None = None
    started = time.time()
    last_emit = 0.0
    window_bytes = 0
    window_start = started

    with httpx.Client(
        timeout=httpx.Timeout(connect=15.0, read=60.0, write=60.0, pool=15.0),
        follow_redirects=True,
        headers=_headers(),
    ) as client:
        with client.stream("GET", url) as response:
            if response.status_code >= 400:
                raise DouyinDownloadError(f"CDN 返回 {response.status_code}")

            length = response.headers.get("content-length")
            if length and length.isdigit():
                total = int(length)
            elif total_hint:
                total = total_hint

            with open(part, "wb") as handle:
                for chunk in response.iter_bytes(CHUNK_SIZE):
                    if cancel_event is not None and cancel_event.is_set():
                        raise DouyinDownloadError("已取消下载")
                    if not chunk:
                        continue
                    handle.write(chunk)
                    downloaded += len(chunk)
                    window_bytes += len(chunk)

                    now = time.time()
                    if on_progress is None or now - last_emit < PROGRESS_INTERVAL:
                        continue
                    last_emit = now

                    elapsed = max(1e-6, now - window_start)
                    speed = window_bytes / elapsed
                    window_bytes = 0
                    window_start = now

                    on_progress(
                        {
                            "status": "downloading",
                            "downloaded_bytes": downloaded,
                            "total_bytes": total,
                            "speed": speed,
                            "info_dict": {"format_id": format_id, "ext": "mp4"},
                        }
                    )

    if downloaded <= 0:
        part.unlink(missing_ok=True)
        raise DouyinDownloadError("没有下载到任何数据")

    if total and downloaded < total * 0.98:
        part.unlink(missing_ok=True)
        raise DouyinDownloadError(
            f"下载不完整（{downloaded}/{total} 字节），已丢弃"
        )

    part.replace(dest)
    logger.info("抖音文件落地 %s（%d 字节，耗时 %.1fs）", dest.name, downloaded, time.time() - started)
    return dest


def download_stream(
    url_list: Iterable[str],
    dest: Path,
    *,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
    cancel_event: threading.Event | None = None,
    format_id: str = "douyin",
    total_hint: int | None = None,
) -> Path:
    """按顺序尝试多个 CDN 地址，前一个失败就换下一个。"""
    urls = [u for u in url_list if isinstance(u, str) and u.startswith("http")]
    if not urls:
        raise DouyinDownloadError("没有可用的下载地址，请重新解析后再试")

    errors: list[str] = []
    for index, url in enumerate(urls, start=1):
        if cancel_event is not None and cancel_event.is_set():
            raise DouyinDownloadError("已取消下载")
        try:
            return _attempt(
                url,
                dest,
                on_progress=on_progress,
                cancel_event=cancel_event,
                format_id=format_id,
                total_hint=total_hint,
            )
        except DouyinDownloadError as exc:
            if "已取消下载" in str(exc):
                raise
            errors.append(f"线路{index}: {exc}")
            logger.info("抖音 CDN 线路 %d 失败：%s", index, exc)
        except Exception as exc:  # noqa: BLE001 - 换线路重试
            errors.append(f"线路{index}: {type(exc).__name__}: {exc}")
            logger.info("抖音 CDN 线路 %d 异常：%s", index, exc)

    raise DouyinDownloadError("所有下载线路都失败了。请重新解析获取新地址后重试。" + "；".join(errors[:2]))


# ---------------------------------------------------------------- 图集


_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".avif")


def _ext_from_url(url: str, default: str = ".jpg") -> str:
    from urllib.parse import urlparse

    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in _IMAGE_SUFFIXES else default


def download_images(
    candidates: list[list[str]],
    dest_zip: Path,
    *,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
    cancel_event: threading.Event | None = None,
    format_id: str = "douyin:images",
) -> Path:
    """把图集逐张下载后打包成 zip。

    抖音图集页面的 `url_list` 是无水印原图，`download_url_list` 带水印，
    这里只用前者。

    进度按「已完成张数 / 总张数」上报，并用 `_percent` 字段告诉上层百分比
    —— 因为多张图片的总字节数在下载完之前无法预知。
    """
    import shutil
    import zipfile

    dest_zip = Path(dest_zip)
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    scratch = dest_zip.parent / (dest_zip.stem + "_parts")
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, exist_ok=True)

    total = len(candidates)
    done_bytes = 0
    saved = 0
    failures: list[str] = []

    try:
        with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for index, urls in enumerate(candidates, start=1):
                if cancel_event is not None and cancel_event.is_set():
                    raise DouyinDownloadError("已取消下载")

                name = f"{index:03d}{_ext_from_url(urls[0])}"
                target = scratch / name
                stored = False

                for url in urls:
                    if cancel_event is not None and cancel_event.is_set():
                        raise DouyinDownloadError("已取消下载")
                    try:
                        _attempt(
                            url,
                            target,
                            on_progress=None,
                            cancel_event=cancel_event,
                            format_id=format_id,
                            total_hint=None,
                        )
                        stored = True
                        break
                    except Exception as exc:  # noqa: BLE001 - 换线路
                        failures.append(f"{index}: {type(exc).__name__}")

                if not stored:
                    logger.info("图集第 %d 张全部线路失败", index)
                    continue

                archive.write(target, name)
                saved += 1
                done_bytes += target.stat().st_size

                if on_progress is not None:
                    on_progress(
                        {
                            "status": "downloading",
                            "downloaded_bytes": done_bytes,
                            "total_bytes": None,
                            "_percent": index / total * 100,
                            "info_dict": {"format_id": format_id, "ext": "zip"},
                        }
                    )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    if saved == 0:
        dest_zip.unlink(missing_ok=True)
        raise DouyinDownloadError("一张图都没下下来，请重新解析后重试")

    if saved < total:
        logger.info("图集部分成功：%d/%d 张（%s）", saved, total, "；".join(failures[:3]))

    logger.info("图集打包完成 %s（%d 张，%d 字节）", dest_zip.name, saved, dest_zip.stat().st_size)
    return dest_zip
