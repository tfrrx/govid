"""纯 CDN 版 API：只解析视频返回直链，不下载文件。

适合部署到 Vercel / Netlify / Cloudflare Pages 等 Serverless 平台。
"""

from __future__ import annotations

import logging
from typing import Any

import anyio
from fastapi import APIRouter, HTTPException, Query

from core.errors import GoVidError
from core.media import parse_video
from models.video import ParseRequest, ParseResponse

logger = logging.getLogger("govid.api.lite")
router = APIRouter(tags=["video-lite"])


# 支持直连的平台列表（CDN 完全开放，无需 Referer）
DIRECT_SUPPORT_PLATFORMS = {
    "douyin",       # 抖音
    "kuaishou",     # 快手
    "pipixia",      # 皮皮虾
    # 注意：B 站 / YouTube 需要 Service Worker 辅助，算半支持
}


@router.post("/parse", response_model=ParseResponse)
async def api_parse_lite(payload: ParseRequest) -> ParseResponse:
    """解析视频元信息，只返回直链。

    前端拿到 formats 列表后：
    - 如果 format.direct = true → 浏览器直接 window.location.href = format.url
    - 如果 format.direct = false → 提示「该平台暂不支持，请用完整版」
    """
    try:
        result = await anyio.to_thread.run_sync(parse_video, payload.url)

        # 标记每个清晰度是否支持直连
        extractor = (result.get("extractor") or "").lower()
        for fmt in result.get("formats", []):
            # 抖音等平台已经在 parser 里标记了 direct: true
            # 这里补充其他平台的判断
            if "direct" not in fmt:
                fmt["direct"] = _is_direct_supported(extractor, fmt)

        return ParseResponse(**result)

    except GoVidError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.exception("解析失败 %s", payload.url)
        raise HTTPException(status_code=500, detail="解析失败，请重试") from exc


def _is_direct_supported(extractor: str, fmt: dict[str, Any]) -> bool:
    """判断该平台 + 清晰度是否支持浏览器直连。

    保守策略：只有明确测试过的平台才标 true，避免用户点了没反应。
    """
    # 抖音等：解析时已标记 direct: true，这里直接沿用
    if fmt.get("direct") is True:
        return True

    # 其他平台暂不支持（需要 Service Worker 或服务器中转）
    return False


@router.get("/supported-platforms")
async def api_supported_platforms() -> dict[str, Any]:
    """返回纯 CDN 版支持的平台列表。

    前端可根据此接口提示用户：
    「当前为纯直连版，仅支持抖音、快手等平台，B 站等需要使用完整版」
    """
    return {
        "platforms": [
            {"id": "douyin", "name": "抖音", "support": "full"},
            {"id": "kuaishou", "name": "快手", "support": "full"},
            {"id": "bilibili", "name": "哔哩哔哩", "support": "experimental"},  # 需 SW
            {"id": "youtube", "name": "YouTube", "support": "experimental"},
            {"id": "twitter", "name": "Twitter", "support": "none"},
            {"id": "weibo", "name": "微博", "support": "none"},
        ],
        "notice": "experimental 平台需要浏览器支持 Service Worker，none 平台请使用完整版"
    }
