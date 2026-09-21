"""ffmpeg 自动检测与获取。

三级来源，按可靠性从高到低尝试：
1. 系统 PATH 上的 ffmpeg（用户已装则零成本）
2. static-ffmpeg 包（首次调用会从 GitHub 拉静态二进制，约 80MB）
3. imageio-ffmpeg 包（ffmpeg 二进制直接打包在 PyPI wheel 里，走 PyPI 网络）

第 3 级是为「GitHub 不可达」的网络环境准备的兜底：PyPI 能通就能拿到 ffmpeg。
它只提供 ffmpeg、不带 ffprobe，所以这里会额外建一个 shim 目录，
把二进制软链成 yt-dlp 期望的 `ffmpeg` 文件名，再把该目录作为 ffmpeg_location。
yt-dlp 拿不到 ffprobe 时只会关闭少量依赖探测的功能（如元数据探测），
合并音视频轨照常工作。

结果进程内缓存，避免每次请求都做 subprocess 探测。
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import threading
from pathlib import Path

from config import PROJECT_ROOT

logger = logging.getLogger("govid.ffmpeg")

SHIM_DIR = PROJECT_ROOT / ".bin"

_lock = threading.RLock()
_cached: dict | None = None

# static-ffmpeg 首次可能需要从 GitHub 拉 80MB 二进制，属于慢路径。
# 它只在启动时的后台线程里探测一次，请求路径永远不会因它阻塞。
_static_result: tuple[str, str | None] | None = None
_static_probed = False

_EMPTY: dict = {
    "available": False,
    "source": None,
    "ffmpeg": None,
    "ffprobe": None,
    "location": None,
    "error": None,
}


# ---------------------------------------------------------------- 基础探测


def _probe(executable: str) -> bool:
    """真的执行一次 -version，确认二进制可用（而不是只看文件名存在）。"""
    try:
        result = subprocess.run(
            [executable, "-version"],
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _sibling(executable: str, name: str) -> str | None:
    candidate = os.path.join(os.path.dirname(os.path.abspath(executable)), name)
    return candidate if os.path.exists(candidate) else None


# ---------------------------------------------------------------- 三级来源


def _from_system() -> tuple[str, str | None] | None:
    executable = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not executable or not _probe(executable):
        return None
    # static_ffmpeg 在 import 时会把自带目录塞进 PATH，这里跳过它，
    # 免得把它误标成「系统 ffmpeg」（能力等价，只是状态展示要跟来源一致）
    if f"{os.sep}static_ffmpeg{os.sep}" in os.path.abspath(executable):
        return None
    probe = shutil.which("ffprobe") or _sibling(executable, "ffprobe")
    if probe and not _probe(probe):
        probe = None
    return executable, probe


def _from_static_ffmpeg() -> tuple[str, str | None] | None:
    # 策略 A：static_ffmpeg.add_paths() —— 会把目录写进 PATH 并返回 (ffmpeg, ffprobe)
    try:
        from static_ffmpeg import add_paths  # type: ignore[attr-defined]

        paths = add_paths()
        if isinstance(paths, (list, tuple)) and paths:
            executable = str(paths[0])
            probe = str(paths[1]) if len(paths) > 1 else _sibling(executable, "ffprobe")
            if _probe(executable):
                return executable, (probe if probe and os.path.exists(probe) else None)
    except Exception as exc:  # noqa: BLE001 - 弱失败，继续下一策略
        logger.debug("static_ffmpeg.add_paths() 不可用：%s", exc)

    # 策略 B：直接从 run 子模块要可执行文件路径
    try:
        from static_ffmpeg import run as static_run

        get_exe = getattr(static_run, "get_or_fetch_platform_executables_else_raise", None)
        if callable(get_exe):
            executable, probe = get_exe()
            if _probe(str(executable)):
                probe = str(probe)
                return str(executable), (probe if os.path.exists(probe) else None)
    except Exception as exc:  # noqa: BLE001
        logger.info("static-ffmpeg 不可用（GitHub 拉取失败？）：%s", exc)

    return None


def _from_imageio() -> tuple[str, None] | None:
    try:
        import imageio_ffmpeg

        executable = imageio_ffmpeg.get_ffmpeg_exe()
        if executable and os.path.exists(executable) and _probe(executable):
            return str(executable), None
    except Exception as exc:  # noqa: BLE001
        logger.debug("imageio-ffmpeg 不可用：%s", exc)
    return None


# ---------------------------------------------------------------- shim


def _ensure_shim(ffmpeg: str, ffprobe: str | None) -> str | None:
    """建一个含 `ffmpeg`（和可选 `ffprobe`）文件名的目录，供 yt-dlp 定位。"""
    try:
        SHIM_DIR.mkdir(parents=True, exist_ok=True)

        def _link(name: str, target: str | None) -> None:
            link = SHIM_DIR / name
            if target is None:
                if link.is_symlink() or link.exists():
                    link.unlink(missing_ok=True)
                return
            if link.is_symlink() and os.path.realpath(link) == os.path.realpath(target):
                return
            if link.exists() or link.is_symlink():
                link.unlink(missing_ok=True)
            os.symlink(os.path.abspath(target), link)

        _link("ffmpeg", ffmpeg)
        _link("ffprobe", ffprobe)

        if not (SHIM_DIR / "ffmpeg").exists():
            return None
        return str(SHIM_DIR)
    except OSError as exc:
        logger.warning("创建 ffmpeg shim 目录失败：%s", exc)
        return None


def _needs_shim(ffmpeg: str, ffprobe: str | None) -> bool:
    """系统目录里已经有 ffmpeg / ffprobe 这两个标准文件名时，不需要 shim。"""
    if os.path.basename(ffmpeg) != "ffmpeg":
        return True
    if ffprobe is None:
        # 没有 ffprobe 也能直接用所在目录，但为了路径统一仍走 shim
        return True
    return not (
        os.path.basename(ffprobe) == "ffprobe"
        and os.path.dirname(os.path.abspath(ffprobe)) == os.path.dirname(os.path.abspath(ffmpeg))
    )


# ---------------------------------------------------------------- 对外接口


def ffmpeg_info() -> dict:
    """返回 ffmpeg 探测结果（带进程内缓存）。

    注意：这里只做本地快路径（系统 PATH / imageio 包内二进制 / 已完成的 static 探测），
    绝不做网络 I/O。static-ffmpeg 的 GitHub 拉取由 warmup() 的后台线程负责，
    否则一次请求会卡住好几分钟。
    """
    global _cached

    with _lock:
        if _cached is not None:
            return _cached

    info = dict(_EMPTY)
    errors: list[str] = []

    with _lock:
        static_candidate = _static_result if _static_probed else None

    for source, resolver in (
        ("system", _from_system),
        ("static-ffmpeg", lambda: static_candidate),
        ("imageio-ffmpeg", _from_imageio),
    ):
        try:
            found = resolver()
        except Exception as exc:  # noqa: BLE001 - 单级失败不影响其他级
            errors.append(f"{source}: {type(exc).__name__}: {exc}")
            continue

        if not found:
            continue

        executable, probe = found
        try:
            location = (
                _ensure_shim(executable, probe)
                if _needs_shim(executable, probe)
                else os.path.dirname(os.path.abspath(executable))
            )
        except OSError as exc:
            errors.append(f"{source}: shim 失败: {exc}")
            continue

        if location is None:
            continue

        info.update(
            {
                "available": True,
                "source": source,
                "ffmpeg": os.path.abspath(executable),
                "ffprobe": os.path.abspath(probe) if probe else None,
                "location": location,
                "error": None,
            }
        )
        logger.info("ffmpeg 就绪（来源 %s）：%s", source, executable)

        with _lock:
            _cached = info
            # 把含 ffmpeg 的目录挂进 PATH，yt-dlp 内部走裸命令时也能命中
            if location not in os.environ.get("PATH", "").split(os.pathsep):
                os.environ["PATH"] = os.pathsep.join([location, os.environ.get("PATH", "")])
            return _cached

    if errors:
        info["error"] = " | ".join(errors)

    logger.warning("未找到可用的 ffmpeg，高清合并与音频转码将被禁用")

    with _lock:
        _cached = info
    return _cached


def detect_ffmpeg(*, allow_static: bool = True) -> str | None:
    """返回 ffmpeg 可执行路径；找不到返回 None。"""
    return ffmpeg_info().get("ffmpeg")


def ffmpeg_location() -> str | None:
    """返回可直接传给 yt-dlp 的 ffmpeg_location。"""
    return ffmpeg_info().get("location")


def ffmpeg_status() -> dict:
    """给 /api/health 用的状态快照（不含绝对路径以外的内部字段）。"""
    info = ffmpeg_info()
    return {
        "available": info["available"],
        "source": info["source"],
        "path": info["ffmpeg"],
        "ffprobe": info["ffprobe"],
        "error": info["error"],
    }


def warmup() -> None:
    """启动预热。

    1) 立刻用本地快路径把 ffmpeg 定下来（系统 / imageio），请求不会被网络拖住；
    2) 同时在后台尝试 static-ffmpeg（可能要从 GitHub 拉 80MB），
       成功的话它带 ffprobe，能力更全，届时重建缓存切过去。
    """
    ffmpeg_info()

    def probe_static() -> None:
        global _static_result, _static_probed, _cached
        found = None
        try:
            found = _from_static_ffmpeg()
        except Exception as exc:  # noqa: BLE001
            logger.info("static-ffmpeg 探测失败：%s", exc)

        with _lock:
            _static_result = found
            _static_probed = True
            if found:
                # 丢掉旧缓存，让下一次调用重新解析并升级到 static-ffmpeg
                _cached = None

        if found:
            logger.info("static-ffmpeg 后台就绪，切换到更完整的 ffmpeg（含 ffprobe）")
            ffmpeg_info()

    threading.Thread(target=probe_static, name="govid-ffmpeg-static", daemon=True).start()
