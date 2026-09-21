"""yt-dlp 薄封装（不改 yt-dlp 仓库任何一行代码）。

对外只暴露两个函数：
- parse_video(url)  → 视频元信息 + 整理好的清晰度列表
- run_download(...) → 阻塞式下载，通过回调汇报进度

清晰度整理策略（比计划书原文略进一步，原因写在下面）：
计划书原文写「过滤无音频纯视频流」，但 YouTube / B 站高码率档位
（1080P 及以上）绝大多数只有 video-only 流，音频是独立轨。
若真把它们过滤掉，验收标准里的「1080P / 720P / 480P 正确展示」根本达不到。
所以这里按「分辨率」归组，每个分辨率给一个可直接选择的 yt-dlp selector：
  - 该分辨率存在音视频合体流 → 直接用它的 format_id
  - 只存在纯视频流         → 用 bestvideo[height<=H]+bestaudio/best 让 yt-dlp 自动合并
前端只需要把 id 原样回传，后端不做二次解释。
"""

from __future__ import annotations

import logging
import re
import threading
from pathlib import Path
from typing import Any, Callable, Iterable

import yt_dlp

from config import settings
from core.errors import (
    GoVidError,
    InvalidURLError,
    translate_error,
)
from core.ffmpeg import ffmpeg_location
from extractors import douyin as douyin_extractor

logger = logging.getLogger("govid.media")

# ---------------------------------------------------------------- 常量

BEST_SELECTOR = "bestvideo+bestaudio/best"
BEST_LABEL = "最佳画质"
AUDIO_SELECTOR = "bestaudio/best"

_EXT_PRIORITY = ("mp4", "webm", "mkv", "mov", "flv", "3gp")
_SKIP_PROTOCOLS = ("mhtml",)

_PLATFORM_NAMES = {
    "youtube": "YouTube",
    "bilibili": "哔哩哔哩",
    "vimeo": "Vimeo",
    "twitter": "X（Twitter）",
    "tiktok": "TikTok",
    "douyin": "抖音",
    "instagram": "Instagram",
    "facebook": "Facebook",
    "twitch": "Twitch",
    "reddit": "Reddit",
    "dailymotion": "Dailymotion",
    "soundcloud": "SoundCloud",
    "youku": "优酷",
    "qqmusic": "QQ 音乐",
    "tencent": "腾讯视频",
    "iqiyi": "爱奇艺",
    "weibo": "微博",
    "xiaohongshu": "小红书",
    "ted": "TED",
    "nicovideo": "niconico",
    "sohu": "搜狐视频",
    "acfun": "AcFun",
    "kuaishou": "快手",
    "pinterest": "Pinterest",
    "linkedin": "LinkedIn",
    "archiveorg": "Internet Archive",
}


# ---------------------------------------------------------------- 工具


def _human_size(num: int | float | None) -> str | None:
    if not num or num <= 0:
        return None
    step = 1024.0
    value = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < step:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= step
    return f"{value:.1f} PB"


def _filesize(fmt: dict) -> int | None:
    size = fmt.get("filesize") or fmt.get("filesize_approx")
    return int(size) if size else None


def _ext_rank(ext: str | None) -> int:
    try:
        return _EXT_PRIORITY.index((ext or "").lower())
    except ValueError:
        return len(_EXT_PRIORITY)


def _quality_score(fmt: dict) -> tuple:
    """同一分辨率下挑「最好那一档」的排序键：体积大 > 码率高 > mp4 优先。"""
    return (
        _filesize(fmt) or 0,
        fmt.get("tbr") or fmt.get("vbr") or 0,
        -_ext_rank(fmt.get("ext")),
        fmt.get("fps") or 0,
    )


def _looks_like_url(value: str) -> bool:
    return bool(re.match(r"^https?://[^\s]+$", value.strip(), re.IGNORECASE))


def platform_name(info: dict) -> str:
    raw = (info.get("extractor_key") or info.get("extractor") or "").strip()
    key = raw.lower().replace(" ", "").replace("_", "")
    for token, name in _PLATFORM_NAMES.items():
        if token in key:
            return name
    return raw or "未知平台"


# ---------------------------------------------------------------- 解析


def _base_opts() -> dict[str, Any]:
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "ignoreerrors": False,
        "socket_timeout": settings.socket_timeout,
        "retries": 3,
        "extractor_retries": 2,
        "no_color": True,
    }
    proxy = (settings.proxy or "").strip()
    if proxy:
        opts["proxy"] = proxy
    cookies = (settings.cookies_file or "").strip()
    if cookies and Path(cookies).expanduser().exists():
        opts["cookiefile"] = str(Path(cookies).expanduser())
    return opts


def build_formats(info: dict[str, Any], *, max_formats: int | None = None) -> list[dict[str, Any]]:
    """把 yt-dlp 的 formats 压成前端可读的清晰度列表。"""
    limit = max_formats or settings.max_formats
    raw: Iterable[dict] = info.get("formats") or []

    progressive: dict[int, dict] = {}
    video_only: dict[int, dict] = {}
    best_audio: dict | None = None

    for fmt in raw:
        if not isinstance(fmt, dict):
            continue
        if (fmt.get("protocol") or "") in _SKIP_PROTOCOLS:
            continue
        note = str(fmt.get("format_note") or "").lower()
        if "storyboard" in note or "images" in note:
            continue

        vcodec = fmt.get("vcodec") or "none"
        acodec = fmt.get("acodec") or "none"
        if vcodec == "none" and acodec == "none":
            continue

        if vcodec == "none":
            if best_audio is None or (fmt.get("abr") or 0) > (best_audio.get("abr") or 0):
                best_audio = fmt
            continue

        height = int(fmt.get("height") or 0)
        if height <= 0:
            continue

        bucket = progressive if acodec != "none" else video_only
        current = bucket.get(height)
        if current is None or _quality_score(fmt) > _quality_score(current):
            bucket[height] = fmt

    # 完全没有独立音轨时，纯视频流不能被合并 → 退化为直接下载（无声）
    mergeable = best_audio is not None
    heights = sorted(set(progressive) | (set(video_only) if mergeable else set()), reverse=True)

    audio_size = _filesize(best_audio) if best_audio else 0
    formats: list[dict[str, Any]] = []

    # 1) 最佳画质（自动合并）
    best_video = None
    for height, fmt in sorted(video_only.items(), reverse=True):
        if best_video is None or _quality_score(fmt) > _quality_score(best_video):
            best_video = fmt
    if not best_video:
        for height, fmt in sorted(progressive.items(), reverse=True):
            if best_video is None or height > int(best_video.get("height") or 0):
                best_video = fmt

    if best_video or mergeable or heights:
        top_tier = max((_tier(f) for f in list(progressive.values()) + list(video_only.values())), default=0)
        size = None
        if best_video:
            size = (_filesize(best_video) or 0) + audio_size or None
        formats.append(
            {
                "id": BEST_SELECTOR,
                "kind": "video",
                "label": BEST_LABEL,
                "resolution": f"{top_tier}P 封顶" if top_tier else "原始画质",
                "height": top_tier or None,
                "ext": "mp4",
                "fps": best_video.get("fps") if best_video else None,
                "size": size,
                "size_text": _human_size(size),
                "has_audio": True,
                "needs_merge": True,
                "recommended": True,
                "note": "自动挑选最高画质并合并音轨",
            }
        )

    # 2) 逐档分辨率
    for height in heights[:limit]:
        if height in progressive:
            fmt = progressive[height]
            selector = str(fmt.get("format_id"))
            size = _filesize(fmt)
            needs_merge = False
            note = "音视频已合体，单文件直下"
        else:
            fmt = video_only[height]
            selector = f"bestvideo[height<={height}]+bestaudio/best"
            video_size = _filesize(fmt) or 0
            size = (video_size + audio_size) or None
            needs_merge = True
            note = "需合并音轨（自动完成）"

        if fmt.get("filesize") is None and fmt.get("filesize_approx") is None:
            note = f"{note} · 体积按码率估算"

        formats.append(
            {
                "id": selector,
                "kind": "video",
                "label": f"{_tier(fmt)}P",
                "resolution": _resolution_text(fmt),
                "height": height,
                "ext": (fmt.get("ext") or "mp4") if not needs_merge else "mp4",
                "fps": fmt.get("fps"),
                "size": size,
                "size_text": _human_size(size),
                "has_audio": True,
                "needs_merge": needs_merge,
                "recommended": False,
                "note": note,
            }
        )

    # 3) 仅音频（顺手的能力，前端放在末位，不抢主线）
    if best_audio is not None:
        size = _filesize(best_audio)
        formats.append(
            {
                "id": AUDIO_SELECTOR,
                "kind": "audio",
                "label": "仅音频",
                "resolution": "MP3 320kbps",
                "height": None,
                "ext": "mp3",
                "fps": None,
                "size": size,
                "size_text": _human_size(size),
                "has_audio": True,
                "needs_merge": False,
                "recommended": False,
                "note": "只要声音，转码为 MP3",
            }
        )

    # 极端兜底：解析不出任何档位（部分站点不给 formats 明细）
    if len(formats) <= (1 if best_audio is not None else 0):
        formats.insert(
            0,
            {
                "id": "best",
                "kind": "video",
                "label": "默认画质",
                "resolution": "由平台决定",
                "height": None,
                "ext": "mp4",
                "fps": None,
                "size": None,
                "size_text": None,
                "has_audio": True,
                "needs_merge": False,
                "recommended": True,
                "note": "平台未提供清晰度明细",
            },
        )

    return formats


def _resolution_text(fmt: dict) -> str:
    width, height = fmt.get("width"), fmt.get("height")
    if width and height:
        return f"{width}×{height}"
    if height:
        return f"{height}P"
    return "未知分辨率"


def _tier(fmt: dict) -> int:
    """标准画质档位。

    竖屏视频（如 1080×1920 的短视频）如果直接拿 height 当档位会标成 1920P，
    与用户认知里的「1080P」不一致。所以取宽高中较小的一边作为档位，
    横屏 1920×1080 与竖屏 1080×1920 都会归到 1080P。
    """
    width, height = fmt.get("width"), fmt.get("height")
    if width and height:
        return int(min(width, height))
    return int(height or 0)


def parse_video(url: str) -> dict[str, Any]:
    """解析视频元信息。同步阻塞，调用方负责丢进线程池。"""
    url = (url or "").strip()
    if not url:
        raise InvalidURLError("请输入视频链接")

    # 抖音走独立通道：aweme/detail 已被 x-secsdk-web-signature 门禁挡死，
    # yt-dlp 的 douyin 提取器永远拿不到数据（给了 cookie 也一样）。
    # 路由必须在 URL 格式校验之前，因为抖音分享过来的是整段文案。
    if douyin_extractor.is_douyin(url):
        return douyin_extractor.parse(url)

    if not _looks_like_url(url):
        raise InvalidURLError("链接格式不对，请粘贴以 http:// 或 https:// 开头的完整地址")

    opts = _base_opts()
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            info = ydl.sanitize_info(info)
    except Exception as exc:  # noqa: BLE001 - 统一翻译成人话
        logger.info("解析失败 %s：%s", url, exc)
        raise translate_error(exc, fallback="解析失败") from exc

    if not isinstance(info, dict):
        raise GoVidError("解析结果异常，请换个链接重试")

    # 传进来的是合集 / 播放列表时，取第一条
    if info.get("_type") == "playlist":
        entries = [e for e in (info.get("entries") or []) if isinstance(e, dict)]
        if not entries:
            raise GoVidError("该链接下没有可下载的视频")
        first = entries[0]
        if first.get("_type") == "url":
            # extract_flat 残留：再单独解析一次真实条目
            return parse_video(first.get("url") or url)
        info = first

    if info.get("is_live"):
        raise GoVidError("暂不支持直播流")

    formats = build_formats(info)
    if not formats:
        raise GoVidError("没解析出可用的清晰度")

    duration = info.get("duration")
    return {
        "title": info.get("title") or "未命名视频",
        "thumbnail": info.get("thumbnail"),
        "duration": int(duration) if duration else None,
        "author": info.get("uploader") or info.get("channel") or info.get("creator") or "未知作者",
        "platform": platform_name(info),
        "webpage_url": info.get("webpage_url") or url,
        "video_id": info.get("id"),
        "extractor": info.get("extractor_key") or info.get("extractor"),
        "view_count": info.get("view_count"),
        "formats": formats,
    }


# ---------------------------------------------------------------- 下载

ProgressCallback = Callable[[dict[str, Any]], None]
PhaseCallback = Callable[[str], None]


def run_download(
    url: str,
    format_id: str,
    out_dir: Path,
    *,
    on_progress: ProgressCallback | None = None,
    on_phase: PhaseCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> Path:
    """阻塞式下载。返回最终落地的文件路径。"""
    out_dir.mkdir(parents=True, exist_ok=True)

    # 抖音：直链由解析阶段缓存，这里纯 HTTP 流式下载，不碰 yt-dlp
    if douyin_extractor.is_douyin(url):
        return douyin_extractor.download(
            url,
            format_id,
            out_dir,
            on_progress=on_progress,
            on_phase=on_phase,
            cancel_event=cancel_event,
        )

    selector = (format_id or BEST_SELECTOR).strip() or BEST_SELECTOR
    is_audio = selector == AUDIO_SELECTOR or selector.startswith("bestaudio")
    wants_merge = "+" in selector

    def _hook(payload: dict[str, Any]) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise yt_dlp.utils.DownloadCancelled("用户取消下载")
        if on_progress is not None:
            on_progress(payload)

    def _pp_hook(payload: dict[str, Any]) -> None:
        if on_phase is None:
            return
        if payload.get("status") == "started":
            on_phase("merging")

    opts: dict[str, Any] = _base_opts()
    opts.update(
        {
            "format": selector,
            "outtmpl": str(out_dir / "%(title).150B.%(ext)s"),
            "paths": {"home": str(out_dir), "temp": str(out_dir)},
            "progress_hooks": [_hook],
            "postprocessor_hooks": [_pp_hook],
            "noprogress": True,
            "windowsfilenames": False,
            "overwrites": True,
            "concurrent_fragment_downloads": 4,
        }
    )

    location = ffmpeg_location()
    if location:
        opts["ffmpeg_location"] = location
    elif wants_merge or is_audio:
        # 没有 ffmpeg 时，把多流选择器降级成单文件，至少能下到东西
        opts["format"] = "best"
        wants_merge = False

    if is_audio and location:
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadCancelled as exc:
        raise translate_error(exc, fallback="下载已取消") from exc
    except Exception as exc:  # noqa: BLE001
        logger.info("下载失败 %s：%s", url, exc)
        raise translate_error(exc, fallback="下载失败，请重试") from exc

    final = _resolve_output_file(out_dir)
    if final is None:
        raise GoVidError("下载完成但没找到文件，请重试")
    return final


_JUNK_SUFFIXES = (".part", ".ytdl", ".tmp", ".temp", ".webm.part")


def _resolve_output_file(out_dir: Path) -> Path | None:
    """下载结束后从任务目录里找最终文件。

    合并场景会有 .f137.mp4 / .f140.m4a 之类的中间产物，
    优先取「非临时后缀 + 体积最大」的那个，再用 mtime 兜底。
    """
    candidates: list[Path] = []
    for path in out_dir.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        if name.startswith("."):
            continue
        if any(name.endswith(suffix) for suffix in _JUNK_SUFFIXES):
            continue
        candidates.append(path)

    if not candidates:
        return None

    def _key(p: Path) -> tuple[int, float]:
        try:
            stat = p.stat()
        except OSError:
            return (0, 0.0)
        return (stat.st_size, stat.st_mtime)

    return max(candidates, key=_key)
