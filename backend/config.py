"""环境配置（支持双模式）。"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings

# 项目根目录（backend/ 的父目录）
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ---------------------------------------------------------------- 运行模式

    # "full" = 完整版（支持流式代理 + 本地下载）
    # "lite" = 纯 CDN 版（只解析直链，不下载）
    mode: str = os.getenv("GOVID_MODE", "full")

    # ---------------------------------------------------------------- 基础配置

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # ---------------------------------------------------------------- 下载配置（仅 full 模式）

    download_dir: str = "/tmp/govid"
    max_concurrent_downloads: int = 4
    task_ttl_hours: int = 2
    max_tmp_gb: float = 10.0

    # ---------------------------------------------------------------- 网络配置

    proxy: str | None = None
    cookies_file: str | None = None
    socket_timeout: int = 30
    thumbnail_timeout: int = 10
    thumbnail_max_bytes: int = 5 * 1024 * 1024

    # ---------------------------------------------------------------- 前端

    frontend_dist: str = str(Path(__file__).parent.parent / "frontend" / "dist")

    # ---------------------------------------------------------------- 平台配置

    max_formats: int = 8

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
