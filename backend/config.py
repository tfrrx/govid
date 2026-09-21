"""GoVid 环境变量与运行配置。

所有可调项都有安全默认值，本地直接 `python main.py` 即可跑通。
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="GOVID_",
    )

    # ---- 服务 ----
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # ---- 下载 ----
    download_dir: Path = PROJECT_ROOT / "tmp"
    max_concurrent_downloads: int = 2
    """同时在跑的真实下载数，超出部分排队（状态 pending）。"""

    socket_timeout: int = 30
    task_ttl_hours: int = 6
    """任务（含临时文件）保留时长，超时由后台清理线程回收。"""

    # ---- 解析 ----
    max_formats: int = 15
    """清晰度列表最多返回多少条。"""

    # ---- 静态资源 ----
    frontend_dist: Path = PROJECT_ROOT / "frontend" / "dist"

    # ---- 网络 ----
    proxy: str = ""
    """形如 http://127.0.0.1:7890，留空则直连。"""

    cookies_file: str = ""
    """Netscape 格式 cookies.txt 路径，阶段 3 会用到，现留占位。"""

    # ---- 缩略图代理 ----
    thumbnail_timeout: int = 15
    thumbnail_max_bytes: int = 12 * 1024 * 1024


settings = Settings()
