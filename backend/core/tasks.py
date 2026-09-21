"""内存任务管理（阶段 1-2 不上数据库，够用且零依赖）。

设计要点：
- 全局 dict + RLock，后台线程跑下载，前端每秒 GET 一次进度
- 信号量控制并发，超出并发数的任务排队为 pending，不会把机器打满
- 多流（video+audio）合并下载时按流聚合进度，避免进度条来回横跳
- 启动清空 tmp/，运行中定期回收过期任务与文件
"""

from __future__ import annotations

import logging
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from config import settings
from core import media
from core.errors import GoVidError, TaskNotFoundError, translate_error

logger = logging.getLogger("govid.tasks")

STATUS_PENDING = "pending"
STATUS_DOWNLOADING = "downloading"
STATUS_MERGING = "merging"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

TERMINAL_STATUSES = {STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED}

_tasks: dict[str, dict[str, Any]] = {}
_lock = threading.RLock()
_semaphore: threading.BoundedSemaphore | None = None
_semaphore_lock = threading.Lock()
_reaper_started = False


# ---------------------------------------------------------------- 内部工具


def _get_semaphore() -> threading.BoundedSemaphore:
    global _semaphore
    with _semaphore_lock:
        if _semaphore is None:
            _semaphore = threading.BoundedSemaphore(max(1, settings.max_concurrent_downloads))
        return _semaphore


def _human_size(num: int | float | None) -> str | None:
    return media._human_size(num)


def _human_speed(bps: float | None) -> str | None:
    if not bps or bps <= 0:
        return None
    return f"{_human_size(bps)}/s"


def _human_eta(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    seconds = int(max(0, seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _percent_fallback(payload: dict[str, Any], downloaded: int) -> float:
    """总大小未知时（HLS 直播切片 / 分片流），退回 yt-dlp 自己的百分比。"""
    raw = payload.get("_percent")
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(payload.get("_percent_str") or "").strip().rstrip("%")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _task_dir(task_id: str) -> Path:
    return Path(settings.download_dir) / task_id


def _touch(task: dict[str, Any]) -> None:
    task["updated_at"] = time.time()


def public_view(task: dict[str, Any]) -> dict[str, Any]:
    """剥掉内部字段后的对外视图。"""
    keys = (
        "task_id", "url", "format_id", "status", "progress",
        "downloaded_bytes", "total_bytes", "downloaded_text", "total_text",
        "speed", "speed_bps", "eta", "eta_seconds", "error", "error_code",
        "file_name", "file_size", "file_size_text", "title", "thumbnail",
        "quality_label", "created_at", "updated_at",
        "has_file",
    )
    return {key: task.get(key) for key in keys}


# ---------------------------------------------------------------- 生命周期


def purge_download_dir() -> None:
    """启动时清空 tmp/，避免上次异常退出留下的半成品占磁盘。"""
    root = Path(settings.download_dir)
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
        return
    for child in root.iterdir():
        try:
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("清理 %s 失败：%s", child, exc)


def reset_tasks() -> None:
    with _lock:
        _tasks.clear()


def cleanup_expired() -> int:
    """回收过期任务：删任务记录 + 删文件。"""
    ttl = max(1, settings.task_ttl_hours) * 3600
    now = time.time()
    expired: list[str] = []

    with _lock:
        for task_id, task in list(_tasks.items()):
            if task.get("status") not in TERMINAL_STATUSES:
                continue
            if now - task.get("updated_at", now) > ttl:
                expired.append(task_id)

        for task_id in expired:
            task = _tasks.pop(task_id, None)
            if task and task.get("file_path"):
                try:
                    Path(task["file_path"]).unlink(missing_ok=True)
                except OSError:
                    pass

    for task_id in expired:
        shutil.rmtree(_task_dir(task_id), ignore_errors=True)

    if expired:
        logger.info("回收过期任务 %d 个", len(expired))
    return len(expired)


def enforce_disk_quota() -> int:
    """tmp 占用超过上限时，按最旧优先回收，避免磁盘被堆满。

    与 TTL 回收互补：TTL 管「单个任务别留太久」，配额管「总量别失控」。
    正在下载的任务目录必须跳过，否则会把别人下到一半的文件删掉。
    """
    limit = int(settings.max_tmp_gb * 1024 ** 3)
    if limit <= 0:
        return 0

    root = Path(settings.download_dir)
    if not root.exists():
        return 0

    with _lock:
        protected = {
            task_id
            for task_id, task in _tasks.items()
            if task.get("status") not in TERMINAL_STATUSES
        }

    items: list[tuple[float, Path, int]] = []
    total = 0
    for child in root.iterdir():
        try:
            if child.is_dir():
                size = sum(f.stat().st_size for f in child.rglob("*") if f.is_file())
            else:
                size = child.stat().st_size
            mtime = child.stat().st_mtime
        except OSError:
            continue
        items.append((mtime, child, size))
        total += size

    if total <= limit:
        return 0

    target = int(limit * 0.8)  # 一次降到 80%，避免每轮都触发
    removed = 0
    for _, path, size in sorted(items):
        if total <= target:
            break
        if path.name in protected:
            continue
        try:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
        except OSError:
            continue
        total -= size
        removed += 1
        with _lock:
            _tasks.pop(path.name, None)

    if removed:
        logger.warning(
            "tmp 超过 %.2f GB 上限，按最旧回收了 %d 项", settings.max_tmp_gb, removed
        )
    return removed


def start_reaper() -> None:
    """后台清理线程（daemon，随进程退出）。"""
    global _reaper_started
    with _lock:
        if _reaper_started:
            return
        _reaper_started = True

    def _loop() -> None:
        while True:
            time.sleep(300)
            try:
                cleanup_expired()
                enforce_disk_quota()
            except Exception as exc:  # noqa: BLE001 - 清理线程不能死
                logger.warning("清理任务时出错：%s", exc)

    threading.Thread(target=_loop, name="govid-reaper", daemon=True).start()


# ---------------------------------------------------------------- 创建 / 查询


def create_task(
    url: str,
    format_id: str,
    *,
    title: str | None = None,
    thumbnail: str | None = None,
    quality_label: str | None = None,
) -> dict[str, Any]:
    task_id = uuid.uuid4().hex[:16]
    now = time.time()
    task: dict[str, Any] = {
        "task_id": task_id,
        "url": url,
        "format_id": format_id,
        "status": STATUS_PENDING,
        "progress": 0.0,
        "downloaded_bytes": 0,
        "total_bytes": None,
        "downloaded_text": None,
        "total_text": None,
        "speed": None,
        "speed_bps": None,
        "eta": None,
        "eta_seconds": None,
        "error": None,
        "error_code": None,
        "file_path": None,
        "file_name": None,
        "file_size": None,
        "file_size_text": None,
        "title": title,
        "thumbnail": thumbnail,
        "quality_label": quality_label,
        "created_at": now,
        "updated_at": now,
        "cancel_requested": False,
        "cancel_event": threading.Event(),
        "_streams": {},
    }

    with _lock:
        _tasks[task_id] = task

    threading.Thread(
        target=_run_task,
        args=(task_id,),
        name=f"govid-dl-{task_id}",
        daemon=True,
    ).start()

    return public_view(task)


def get_task(task_id: str) -> dict[str, Any]:
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError()
        return public_view(task)


def get_task_raw(task_id: str) -> dict[str, Any]:
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError()
        return task


def cancel_task(task_id: str) -> dict[str, Any]:
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError()
        if task["status"] in TERMINAL_STATUSES:
            return public_view(task)
        task["cancel_requested"] = True
        task["cancel_event"].set()
        task["status"] = STATUS_CANCELLED
        task["error"] = "已取消下载"
        task["error_code"] = "cancelled"
        _touch(task)
        return public_view(task)


# ---------------------------------------------------------------- 下载执行


def _run_task(task_id: str) -> None:
    task = _tasks.get(task_id)
    if task is None:
        return

    semaphore = _get_semaphore()
    with semaphore:
        # 排队期间被取消
        if task.get("cancel_event") and task["cancel_event"].is_set():
            return
        try:
            _do_download(task)
        except GoVidError as exc:
            _fail(task, exc.message, exc.code)
        except Exception as exc:  # noqa: BLE001 - 后台线程必须兜住所有异常
            logger.exception("任务 %s 未捕获异常", task_id)
            _fail(task, translate_error(exc, fallback="下载失败").message, "error")


def _do_download(task: dict[str, Any]) -> None:
    task_id = task["task_id"]
    out_dir = _task_dir(task_id)
    last_write = 0.0

    with _lock:
        task["status"] = STATUS_DOWNLOADING
        task["progress"] = 0.0
        _touch(task)

    selecting = task["format_id"] or ""
    multi_stream = "+" in selecting

    def on_progress(payload: dict[str, Any]) -> None:
        nonlocal last_write
        now = time.time()
        # 限流：最多 4 次/秒写状态，避免锁竞争
        if now - last_write < 0.25 and payload.get("status") == "downloading":
            return
        last_write = now

        status = payload.get("status")
        info = payload.get("info_dict") or {}
        stream_key = str(info.get("format_id") or payload.get("filename") or "stream")

        with _lock:
            if task["status"] == STATUS_CANCELLED:
                return

            if status == "downloading":
                streams = task["_streams"]
                downloaded = int(payload.get("downloaded_bytes") or 0)
                total = payload.get("total_bytes") or payload.get("total_bytes_estimate")
                streams[stream_key] = {
                    "downloaded": downloaded,
                    "total": int(total) if total else None,
                }

                sum_downloaded = sum(s["downloaded"] for s in streams.values())
                totals = [s["total"] for s in streams.values()]
                if multi_stream and any(t is None for t in totals):
                    sum_total = None
                else:
                    sum_total = sum(t for t in totals if t) or None

                if sum_total:
                    percent = min(99.0, sum_downloaded / sum_total * 100)
                    task["total_bytes"] = sum_total
                else:
                    percent = min(99.0, _percent_fallback(payload, sum_downloaded))
                    task["total_bytes"] = None

                speed = payload.get("speed")
                if speed:
                    task["speed_bps"] = float(speed)
                    task["speed"] = _human_speed(float(speed))
                    if sum_total and sum_total > sum_downloaded:
                        task["eta_seconds"] = int((sum_total - sum_downloaded) / float(speed))
                        task["eta"] = _human_eta(task["eta_seconds"])

                if task["status"] != STATUS_MERGING:
                    task["status"] = STATUS_DOWNLOADING
                task["progress"] = round(percent, 1)
                task["downloaded_bytes"] = sum_downloaded
                task["downloaded_text"] = _human_size(sum_downloaded)
                task["total_text"] = _human_size(sum_total)
                _touch(task)

            elif status == "finished":
                # 多流选择器下载完最后一流后必然要合并；单文件流直接进收尾
                if multi_stream:
                    task["status"] = STATUS_MERGING
                    task["speed"] = None
                    task["eta"] = None
                task["progress"] = max(task["progress"], 99.0)
                _touch(task)

            elif status == "error":
                task["status"] = STATUS_FAILED

    def on_phase(phase: str) -> None:
        with _lock:
            if task["status"] == STATUS_CANCELLED:
                return
            if phase == "merging":
                task["status"] = STATUS_MERGING
                task["progress"] = max(task["progress"], 99.0)
                task["speed"] = None
                task["eta"] = None
                _touch(task)

    final_path = media.run_download(
        task["url"],
        task["format_id"],
        out_dir,
        on_progress=on_progress,
        on_phase=on_phase,
        cancel_event=task["cancel_event"],
    )

    with _lock:
        if task["status"] == STATUS_CANCELLED:
            return
        size = final_path.stat().st_size if final_path.exists() else None
        task["status"] = STATUS_COMPLETED
        task["progress"] = 100.0
        task["speed"] = None
        task["eta"] = None
        task["eta_seconds"] = None
        task["file_path"] = str(final_path)
        task["file_name"] = final_path.name
        task["file_size"] = size
        task["file_size_text"] = _human_size(size)
        task["total_bytes"] = size
        task["total_text"] = _human_size(size)
        task["downloaded_bytes"] = size or task["downloaded_bytes"]
        task["downloaded_text"] = _human_size(size)
        task["has_file"] = True
        task["_streams"] = {}
        _touch(task)


def _fail(task: dict[str, Any], message: str, code: str) -> None:
    with _lock:
        if task["status"] == STATUS_CANCELLED:
            return
        task["status"] = STATUS_FAILED
        task["error"] = message
        task["error_code"] = code
        task["speed"] = None
        task["eta"] = None
        _touch(task)
    logger.info("任务 %s 失败：%s", task["task_id"], message)
