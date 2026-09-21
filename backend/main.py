"""GoVid FastAPI 入口。

启动方式：
    cd backend && python main.py
或（仓库根）：
    ./run.sh
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 让 `python backend/main.py` 与 `cd backend && python main.py` 都能正确 import
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from api import health as health_api  # noqa: E402
from api import video as video_api  # noqa: E402
from config import settings  # noqa: E402
from core import tasks as task_core  # noqa: E402
from core.ffmpeg import warmup as ffmpeg_warmup  # noqa: E402
from core.errors import GoVidError  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("govid")

DIST_DIR = Path(settings.frontend_dist)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task_core.purge_download_dir()
    task_core.reset_tasks()
    task_core.start_reaper()

    import threading

    threading.Thread(target=ffmpeg_warmup, name="govid-ffmpeg-warmup", daemon=True).start()

    logger.info("GoVid 已启动 · 下载目录 %s", settings.download_dir)
    if not DIST_DIR.exists():
        logger.warning("未找到前端产物 %s，请先在 frontend/ 执行 npm run build", DIST_DIR)
    yield
    logger.info("GoVid 正在关闭")


app = FastAPI(
    title="GoVid API",
    description="基于 yt-dlp 的视频解析与下载服务",
    version=health_api.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # 本机 / 局域网自用服务，直接放开；对外部署时再收紧
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.exception_handler(GoVidError)
async def govid_error_handler(request: Request, exc: GoVidError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """把 pydantic 的英文校验信息换成人话，前端只认 detail/code 两个字段。"""
    fields = {str(err.get("loc", ["", ""])[-1]) for err in exc.errors()}
    if "url" in fields:
        message, code = "请输入视频链接", "invalid_url"
    elif "format_id" in fields:
        message, code = "请先选择清晰度", "invalid_format"
    else:
        message, code = "请求参数不完整", "invalid_request"
    return JSONResponse(status_code=422, content={"detail": message, "code": code})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("未处理异常 %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务内部错误，请稍后重试", "code": "internal_error"},
    )


app.include_router(health_api.router, prefix="/api")
app.include_router(video_api.router, prefix="/api")


# ---------------------------------------------------------------- 前端静态资源


if (DIST_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    """Vue SPA 兜底：静态文件命中就发文件，否则一律回 index.html。"""
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "接口不存在", "code": "not_found"})

    if not DIST_DIR.exists():
        return JSONResponse(
            status_code=503,
            content={
                "detail": "前端产物缺失，请在 frontend/ 目录执行 npm install && npm run build",
                "code": "frontend_missing",
            },
        )

    candidate = (DIST_DIR / full_path).resolve()
    try:
        candidate.relative_to(DIST_DIR.resolve())
    except ValueError:
        return JSONResponse(status_code=403, content={"detail": "非法路径", "code": "forbidden"})

    if full_path and candidate.is_file():
        return FileResponse(candidate)

    return FileResponse(DIST_DIR / "index.html", headers={"Cache-Control": "no-cache"})


def main() -> None:
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
