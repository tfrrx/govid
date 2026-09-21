"""抖音作品 JSON → GoVid 统一视频结构。

统一结构（与 yt-dlp 通道保持一致，前端无需区分来源）：
    {
      "title", "thumbnail", "duration", "author", "platform",
      "webpage_url", "video_id", "extractor", "view_count", "formats": [...]
    }

每个 format：
    {
      "id", "kind", "label", "resolution", "height", "ext", "fps",
      "size", "size_text", "has_audio", "needs_merge", "recommended", "note"
    }

`id` 形如 `douyin:<gear_name>`，前端原样回传，下载时用它反查直链。
"""

from __future__ import annotations

import logging
import re
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("govid.douyin.parser")

# ---------------------------------------------------------------- URL 识别

_HOST_RE = re.compile(r"(^|\.)(douyin\.com|iesdouyin\.com|amemv\.com|douyinpic\.com)$", re.I)

_ID_PATTERNS = (
    re.compile(r"/video/(\d{8,})"),
    re.compile(r"/note/(\d{8,})"),
    re.compile(r"/share/video/(\d{8,})"),
    re.compile(r"/share/note/(\d{8,})"),
    re.compile(r"/aweme/detail/(\d{8,})"),
    re.compile(r"[?&]aweme_id=(\d{8,})"),
    re.compile(r"[?&]modal_id=(\d{8,})"),
    re.compile(r"[?&]item_ids?=(\d{8,})"),
)

_URL_IN_TEXT_RE = re.compile(r"https?://[^\s，。、）)】\"']+")
_SHORT_HOST_RE = re.compile(r"^v\.douyin\.com$", re.I)

# 「最佳画质」总档：按码率挑真正最清楚的那条，与 yt-dlp 通道的同名档语义一致
BEST_SELECTOR = "douyin:best"
BEST_LABEL = "最佳画质"
IMAGES_SELECTOR = "douyin:images"

# ---------------------------------------------------------------- 缓存

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_LOCK = threading.RLock()
_CACHE_MAX = 48
_CACHE_MIN_TTL = 60.0
_CACHE_MAX_TTL = 3 * 3600.0


def cache_put(aweme_id: str, aweme: dict[str, Any]) -> None:
    ttl = _cache_ttl(aweme)
    with _CACHE_LOCK:
        if len(_CACHE) >= _CACHE_MAX:
            oldest = min(_CACHE.items(), key=lambda kv: kv[1][0])[0]
            _CACHE.pop(oldest, None)
        _CACHE[aweme_id] = (time.time() + ttl, aweme)


def cache_get(aweme_id: str) -> dict[str, Any] | None:
    with _CACHE_LOCK:
        entry = _CACHE.get(aweme_id)
        if entry is None:
            return None
        expire_at, aweme = entry
        if time.time() >= expire_at:
            _CACHE.pop(aweme_id, None)
            return None
        return aweme


def cache_clear() -> int:
    with _CACHE_LOCK:
        count = len(_CACHE)
        _CACHE.clear()
    return count


def _cache_ttl(aweme: dict[str, Any]) -> float:
    """直链有时效，缓存不能比直链活得久。"""
    video = aweme.get("video") or {}
    expired = video.get("cdn_url_expired")
    if isinstance(expired, (int, float)) and expired > 0:
        remaining = float(expired) - time.time() - 60.0
        return max(_CACHE_MIN_TTL, min(_CACHE_MAX_TTL, remaining))
    return 20 * 60.0


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


def _first_url(container: Any) -> str | None:
    if not isinstance(container, dict):
        return None
    urls = container.get("url_list") or []
    for url in urls:
        if isinstance(url, str) and url.startswith("http"):
            return url
    return None


def _pick_cover(video: dict[str, Any]) -> str | None:
    for key in ("cover", "origin_cover", "cover_original_scale", "dynamic_cover"):
        url = _first_url(video.get(key))
        if url:
            return url
    return None


_TIER_STOPS = (144, 240, 360, 480, 540, 720, 1080, 1440, 2160)


def _nearest_tier(value: int) -> int:
    if value <= 0:
        return 0
    return min(_TIER_STOPS, key=lambda stop: abs(stop - value))


def _gear_tier(gear: str, width: int | None, height: int | None) -> int:
    """抖音 gear_name 形如 normal_720_0 / adapt_lowest_720_1，中间那截就是档位。

    拿不到就退回真实分辨率（取短边，竖屏 720×1280 也归到 720P）。
    """
    match = re.search(r"_(\d{3,4})_", gear or "")
    if match:
        return _nearest_tier(int(match.group(1)))
    if width and height:
        return _nearest_tier(min(int(width), int(height)))
    if height:
        return _nearest_tier(int(height))
    return 0


def _clean_filename(name: str, *, limit: int = 100) -> str:
    text = re.sub(r"[\\/:*?\"<>|\r\n\t]+", " ", name or "")
    text = re.sub(r"\s+", " ", text).strip(" .")
    if not text:
        text = "douyin_video"
    return text[:limit].strip() or "douyin_video"


def output_filename(title: str, ext: str = "mp4") -> str:
    return f"{_clean_filename(title)}.{ext}"


# ---------------------------------------------------------------- 统一结构


def build_info(aweme: dict[str, Any], source_url: str) -> dict[str, Any]:
    video = aweme.get("video") or {}
    author = aweme.get("author") or {}
    statistics = aweme.get("statistics") or {}

    duration_ms = video.get("duration")
    duration = int(duration_ms / 1000) if isinstance(duration_ms, (int, float)) and duration_ms else None

    title = (aweme.get("desc") or "").strip() or f"抖音作品 {aweme.get('aweme_id')}"

    formats = build_formats(aweme)
    if not formats:
        raise ValueError("这条作品没有可下载的视频流")

    return {
        "title": title,
        "thumbnail": _pick_cover(video),
        "duration": duration,
        "author": author.get("nickname") or "未知作者",
        "platform": "抖音",
        "webpage_url": source_url,
        "video_id": str(aweme.get("aweme_id") or ""),
        "extractor": "DouyinDirect",
        "view_count": statistics.get("play_count") or None,
        "formats": formats,
    }


def build_formats(aweme: dict[str, Any]) -> list[dict[str, Any]]:
    """从 bit_rate 生成清晰度列表；bit_rate 缺失时退回 play_addr。

    图文作品（aweme_type 68 / images 非空）走单独分支：返回一个「图集」档，
    下载时打包成 zip —— 用户拿到的是原图集合，不是抖音自动生成的那条幻灯视频。
    """
    images = aweme.get("images") or []
    if images or int(aweme.get("aweme_type") or 0) in (2, 68):
        return _image_formats(images)

    video = aweme.get("video") or {}
    tiers: dict[int, dict[str, Any]] = {}

    for entry in video.get("bit_rate") or []:
        if not isinstance(entry, dict):
            continue
        play = entry.get("play_addr") or {}
        if not _first_url(play):
            continue
        gear = str(entry.get("gear_name") or "")
        width = play.get("width") or video.get("width")
        height = play.get("height") or video.get("height")
        tier = _gear_tier(gear, width, height)
        if tier <= 0:
            continue

        bitrate = int(entry.get("bit_rate") or 0)
        size = play.get("data_size")
        candidate = {
            "id": f"douyin:{gear or tier}",
            "gear": gear,
            "kind": "video",
            "label": f"{tier}P",
            "resolution": f"{width}×{height}" if width and height else "未知分辨率",
            "height": tier,
            "ext": (entry.get("format") or "mp4").lower(),
            "fps": None,
            "size": int(size) if isinstance(size, (int, float)) and size else None,
            "has_audio": True,
            "needs_merge": False,   # 抖音各档都是音视频合体单文件
            "recommended": False,
            "bitrate": bitrate,
            "source": "bit_rate",
        }
        current = tiers.get(tier)
        # 同档位取码率更高（体积更大）的那条
        if current is None or (bitrate, candidate["size"] or 0) > (
            current["bitrate"],
            current["size"] or 0,
        ):
            tiers[tier] = candidate

    # 兜底：没有任何 bit_rate 明细时，用主 play_addr 出一档
    if not tiers:
        play = video.get("play_addr") or {}
        url = _first_url(play)
        if url:
            width, height = play.get("width"), play.get("height")
            tier = _gear_tier("", width, height) or 0
            size = play.get("data_size")
            tiers[tier] = {
                "id": "douyin:play_addr",
                "gear": "play_addr",
                "kind": "video",
                "label": f"{tier}P" if tier else "默认画质",
                "resolution": f"{width}×{height}" if width and height else "未知分辨率",
                "height": tier or None,
                "ext": "mp4",
                "fps": None,
                "size": int(size) if isinstance(size, (int, float)) and size else None,
                "has_audio": True,
                "needs_merge": False,
                "recommended": True,
                "bitrate": 0,
                "source": "play_addr",
            }

    ordered = [tiers[tier] for tier in sorted(tiers, reverse=True)]
    if not ordered:
        return []

    # 抖音的档位不能只看分辨率：540P 档的码率常常比 720P 还高
    # （同一视频 540P 4.0MB / 720P 3.4MB 是常态），所以给一个「最佳画质」
    # 总档，按码率挑真正最清楚的那条，用户点第一个就行。
    best = max(ordered, key=lambda item: (item.get("bitrate") or 0, item.get("size") or 0))

    formats: list[dict[str, Any]] = [
        {
            "id": BEST_SELECTOR,
            "kind": "video",
            "label": BEST_LABEL,
            "resolution": f"{best['label']} 原件",
            "height": best.get("height"),
            "ext": best.get("ext") or "mp4",
            "fps": None,
            "size": best.get("size"),
            "size_text": _human_size(best.get("size")),
            "has_audio": True,
            "needs_merge": False,
            "recommended": True,
            "note": _bitrate_note(best.get("bitrate")) + " · 推荐",
        }
    ]

    for item in ordered:
        size = item.pop("size", None)
        bitrate = int(item.pop("bitrate", 0) or 0)
        item.pop("source", None)
        item.pop("gear", None)
        item["size"] = size
        item["size_text"] = _human_size(size)
        item["note"] = _bitrate_note(bitrate)
        item["recommended"] = False
        formats.append(item)

    return formats


def _bitrate_note(bitrate: Any) -> str:
    value = int(bitrate or 0)
    return f"码率 {value / 1000:.0f} kbps · 无水印" if value else "无水印"


def _image_formats(images: list[Any]) -> list[dict[str, Any]]:
    """图文作品只给一个档：图集（打包 zip）。"""
    usable = [
        img
        for img in images
        if isinstance(img, dict) and _first_url({"url_list": img.get("url_list")})
    ]
    if not usable:
        raise ValueError("这条图文作品没有可下载的图片")

    live_count = sum(1 for img in usable if img.get("video"))
    note = "无水印原图，打包为 zip 下载"
    if live_count:
        note += f"（含 {live_count} 张实况图）"

    return [
        {
            "id": IMAGES_SELECTOR,
            "kind": "video",
            "label": "图集",
            "resolution": f"{len(usable)} 张图片",
            "height": None,
            "ext": "zip",
            "fps": None,
            "size": None,
            "size_text": None,
            "has_audio": False,
            "needs_merge": False,
            "recommended": True,
            "note": note,
        }
    ]


def resolve_images(aweme: dict[str, Any]) -> list[list[str]]:
    """返回每张图的 CDN 候选列表（外层按图片顺序，内层是可替换线路）。"""
    result: list[list[str]] = []
    for img in aweme.get("images") or []:
        if not isinstance(img, dict):
            continue
        urls = [
            url
            for url in (img.get("url_list") or [])
            if isinstance(url, str) and url.startswith("http")
        ]
        if urls:
            result.append(urls)

    if not result:
        raise ValueError("这条图文作品没有可下载的图片")
    return result


def resolve_stream(aweme: dict[str, Any], format_id: str) -> tuple[list[str], str, int | None]:
    """按 format_id 找回直链候选列表。

    返回 (url_list, ext, size)。下载层按顺序尝试，前一个 CDN 失败就换下一个。
    """
    selector = (format_id or "").strip()
    if selector.startswith("douyin:"):
        selector = selector[len("douyin:"):]
    if not selector:
        selector = "play_addr"

    video = aweme.get("video") or {}

    if selector == "best":
        entries = [
            entry
            for entry in (video.get("bit_rate") or [])
            if isinstance(entry, dict) and _first_url(entry.get("play_addr") or {})
        ]
        if entries:
            top = max(entries, key=lambda entry: int(entry.get("bit_rate") or 0))
            play = top.get("play_addr") or {}
            urls = [u for u in (play.get("url_list") or []) if isinstance(u, str)]
            if urls:
                size = play.get("data_size")
                ext = (top.get("format") or "mp4").lower()
                return (
                    urls,
                    ext,
                    int(size) if isinstance(size, (int, float)) and size else None,
                )

    if selector == "play_addr":
        play = video.get("play_addr") or {}
        urls = [u for u in (play.get("url_list") or []) if isinstance(u, str)]
        if urls:
            size = play.get("data_size")
            return urls, "mp4", int(size) if isinstance(size, (int, float)) and size else None

    for entry in video.get("bit_rate") or []:
        if not isinstance(entry, dict):
            continue
        gear = str(entry.get("gear_name") or "")
        tier = _gear_tier(gear, (entry.get("play_addr") or {}).get("width"), (entry.get("play_addr") or {}).get("height"))
        if gear != selector and str(tier) != selector:
            continue
        play = entry.get("play_addr") or {}
        urls = [u for u in (play.get("url_list") or []) if isinstance(u, str)]
        if urls:
            size = play.get("data_size")
            ext = (entry.get("format") or "mp4").lower()
            return urls, ext, int(size) if isinstance(size, (int, float)) and size else None

    # 指定的档位没了（可能已被平台下架），退回主播放地址
    play = video.get("play_addr") or {}
    urls = [u for u in (play.get("url_list") or []) if isinstance(u, str)]
    if urls:
        size = play.get("data_size")
        return urls, "mp4", int(size) if isinstance(size, (int, float)) and size else None

    raise ValueError("这个清晰度已经不可用了，请重新解析后再试")


def is_image_post(aweme: dict[str, Any]) -> bool:
    if aweme.get("images"):
        return True
    return int(aweme.get("aweme_type") or 0) in (2, 68)


# ---------------------------------------------------------------- URL → ID


def is_douyin(url: str) -> bool:
    """判断是否归抖音通道。

    不能只 parse hostname —— 用户从 App 复制过来的是整段分享文案
    （「7.43 复制打开抖音… https://v.douyin.com/xxxx/」），
    这种情况 urlparse 拿不到 host，所以直接在原文里找域名。
    """
    text = (url or "").strip()
    if not text:
        return False
    if re.search(r"douyin\.com|iesdouyin\.com|amemv\.com", text, re.I):
        return True
    host = (urlparse(text).hostname or "").lower()
    return bool(host and _HOST_RE.search(host))


def _candidate_urls(raw: str) -> list[str]:
    text = (raw or "").strip()
    found = _URL_IN_TEXT_RE.findall(text)
    if found:
        return found
    return [text] if text else []


def _id_from_text(text: str) -> tuple[str, str] | None:
    for pattern in _ID_PATTERNS:
        match = pattern.search(text)
        if match:
            kind = "note" if "note" in pattern.pattern else "video"
            return match.group(1), kind
    return None


def extract_aweme_id(raw: str, *, timeout: float = 20.0) -> tuple[str, str]:
    """从链接或整段分享文案里取出 (aweme_id, kind)。

    支持短链 v.douyin.com —— 需要发一次 HTTP 拿重定向落点。
    """
    import httpx

    for candidate in _candidate_urls(raw):
        if not candidate.startswith("http"):
            candidate = "https://" + candidate.lstrip("/")
        parsed = urlparse(candidate)
        host = (parsed.hostname or "").lower()

        direct = _id_from_text(candidate)
        if direct:
            return direct

        if not _SHORT_HOST_RE.match(host) and not host.endswith("douyin.com"):
            continue

        # 短链或用户页：跟随重定向找落点
        try:
            with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                        "Mobile/15E148 Safari/604.1"
                    ),
                    "Referer": "https://www.douyin.com/",
                },
            ) as client:
                response = client.get(candidate)
                landed = str(response.url)
                found = _id_from_text(landed)
                if found:
                    return found
                # 分享页 HTML 里内嵌的 itemId 也能用
                body = response.text[:400000]
                for pattern in (
                    re.compile(r'"itemId"\s*:\s*"(\d{8,})"'),
                    re.compile(r'"aweme_id"\s*:\s*"(\d{8,})"'),
                    re.compile(r'\\"itemId\\"\s*:\s*\\"(\d{8,})\\"'),
                ):
                    match = pattern.search(body)
                    if match:
                        return match.group(1), "video"
        except Exception as exc:  # noqa: BLE001 - 换下一个候选
            logger.debug("短链解析失败 %s：%s", candidate, exc)
            continue

    raise ValueError(
        "没认出这是哪条抖音作品。请复制抖音 App 里的分享链接（v.douyin.com 短链），"
        "或网页版视频地址（douyin.com/video/...）"
    )


def source_path_hint(raw: str) -> str:
    return Path(urlparse((raw or "").split("?")[0]).path or "").name
