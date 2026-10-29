"""CORS 代理 API - 让前端能直连需要特殊 Headers 的平台"""

from urllib.parse import unquote

import httpx
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

router = APIRouter(tags=["proxy"])


@router.get("/cors-proxy")
@router.head("/cors-proxy")
async def cors_proxy(
    request: Request,
    url: str = Query(..., description="目标视频 URL"),
    referer: str = Query(None, description="Referer Header"),
    user_agent: str = Query(None, description="User-Agent Header"),
):
    """
    CORS 代理：转发视频请求并添加必要的 Headers

    用于前端直连 B 站、YouTube 等需要特定 Headers 的平台
    """
    # 解码 URL
    target_url = unquote(url)

    # 构建请求头
    headers = {}
    if referer:
        headers["Referer"] = unquote(referer)
    if user_agent:
        headers["User-Agent"] = unquote(user_agent)
    else:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # 根据目标平台自动添加 Referer
    if not referer:
        if "bilibili" in target_url or "bilivideo" in target_url:
            headers["Referer"] = "https://www.bilibili.com/"
        elif "youtube" in target_url or "googlevideo" in target_url:
            headers["Referer"] = "https://www.youtube.com/"

    # HEAD 请求：只返回响应头
    if request.method == "HEAD":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(target_url, headers=headers, follow_redirects=True)

            # 返回响应头
            return JSONResponse(
                status_code=response.status_code,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                    "Access-Control-Expose-Headers": "*",
                    "Content-Type": response.headers.get("Content-Type", ""),
                    "Content-Length": response.headers.get("Content-Length", "0"),
                }
            )
        except Exception as e:
            return JSONResponse(
                {"error": str(e)},
                status_code=500,
                headers={"Access-Control-Allow-Origin": "*"}
            )

    # GET 请求：流式转发
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", target_url, headers=headers, follow_redirects=True) as response:
                # 构建响应头
                response_headers = {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                    "Access-Control-Expose-Headers": "*",
                }

                # 转发原始响应头
                for key in ["Content-Type", "Content-Length", "Content-Range", "Accept-Ranges"]:
                    if key in response.headers:
                        response_headers[key] = response.headers[key]

                # 流式返回
                async def stream_content():
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        yield chunk

                return StreamingResponse(
                    stream_content(),
                    status_code=response.status_code,
                    headers=response_headers,
                )
    except Exception as e:
        return JSONResponse(
            {"error": f"代理请求失败: {str(e)}"},
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )


@router.options("/cors-proxy")
async def cors_proxy_options():
    """OPTIONS 请求：CORS 预检"""
    return JSONResponse(
        {},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )
