"""抖音 JSON 抓取层：借真实浏览器的签名能力拿 aweme/detail。

设计约束与取舍
--------------
1. playwright 的 sync API **对象是线程绑定的**，不能跨线程共享 Browser。
   所以这里用一个专用 daemon 线程独占浏览器，其他线程通过队列投递任务，
   用 Future 取结果。这样既能复用浏览器（省掉每次 3~5 秒冷启动），
   又不会踩线程亲和性的坑。

2. 浏览器**懒启动**：第一次真正要解析抖音时才拉起 Chrome。
   服务启动、解析 B 站等场景完全不受影响。

3. 不下载 Chromium。优先复用系统已装的 Chrome（channel="chrome"），
   依次降级 msedge / chromium / playwright 自带浏览器。

4. 使用的 context 不注入任何用户数据：独立临时 profile、无 cookie、
   无 localStorage、无扩展。cookie 全部由抖音自己匿名种下
   （UIFID / x-web-secsdk-uid / ttwid）。
"""

from __future__ import annotations

import logging
import queue
import re
import threading
from typing import Any, Callable

logger = logging.getLogger("govid.douyin.browser")

DETAIL_PATH_RE = re.compile(r"/aweme/v1/web/aweme/detail/")

DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)

_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--disable-background-timer-throttling",
    "--mute-audio",
]

# 按优先级尝试；空 dict 表示用 playwright 自带的 Chromium 构建
_LAUNCH_ATTEMPTS: tuple[dict[str, Any], ...] = (
    {"channel": "chrome"},
    {"channel": "msedge"},
    {"channel": "chromium"},
    {},
)


class DouyinBrowserError(RuntimeError):
    """浏览器不可用或抓取失败。"""


# ---------------------------------------------------------------- worker

_jobs: "queue.Queue[tuple[Callable[[Any], Any], Any] | None]" = queue.Queue()
_worker_lock = threading.Lock()
_worker_started = False


def _new_context(playwright):
    """按优先级挑一个可用的浏览器，返回 BrowserContext。"""
    errors: list[str] = []
    for attempt in _LAUNCH_ATTEMPTS:
        label = attempt.get("channel") or "bundled-chromium"
        try:
            browser = playwright.chromium.launch(
                headless=True, args=_LAUNCH_ARGS, **attempt
            )
        except Exception as exc:  # noqa: BLE001 - 逐个降级
            errors.append(f"{label}: {type(exc).__name__}: {exc}")
            continue
        context = browser.new_context(
            user_agent=DEFAULT_UA,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
        )
        context.set_default_timeout(30_000)
        logger.info("抖音浏览器就绪（%s）", label)
        return browser, context
    raise DouyinBrowserError(
        "没有可用的浏览器内核。装一个 Google Chrome，或执行 "
        "`playwright install chromium`。尝试记录： " + " | ".join(errors)
    )


def _worker_loop() -> None:
    playwright = None
    browser = None
    context = None

    while True:
        item = _jobs.get()
        if item is None:
            break
        fn, future = item
        try:
            if playwright is None:
                try:
                    from playwright.sync_api import sync_playwright
                except ImportError as exc:
                    raise DouyinBrowserError(
                        "抖音解析需要 playwright 组件，请执行 "
                        "`pip install playwright` 后重启服务"
                    ) from exc

                playwright = sync_playwright().start()

            # 浏览器崩溃 / 被回收时重建
            if context is None or browser is None or not browser.is_connected():
                if browser is not None:
                    try:
                        browser.close()
                    except Exception:  # noqa: BLE001
                        pass
                browser, context = _new_context(playwright)

            future.set_result(fn(context))
        except Exception as exc:  # noqa: BLE001 - 单次失败不能拖垮 worker
            # 出错后丢弃浏览器，下次重建，避免带着坏状态继续用
            context = None
            if browser is not None:
                try:
                    browser.close()
                except Exception:  # noqa: BLE001
                    pass
                browser = None
            future.set_exception(exc)

    try:
        if browser is not None:
            browser.close()
        if playwright is not None:
            playwright.stop()
    except Exception:  # noqa: BLE001
        pass


def _ensure_worker() -> None:
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        threading.Thread(
            target=_worker_loop, name="govid-douyin-browser", daemon=True
        ).start()
        _worker_started = True


def _submit(fn: Callable[[Any], Any], timeout: float) -> Any:
    from concurrent.futures import Future

    _ensure_worker()
    future: Future = Future()
    _jobs.put((fn, future))
    try:
        return future.result(timeout=timeout)
    except TimeoutError as exc:  # noqa: UP041 - Future 抛的是 TimeoutError
        raise DouyinBrowserError("抖音页面加载超时，请稍后重试") from exc


# ---------------------------------------------------------------- 抓取


def warmup() -> None:
    """预热：提前把浏览器拉起来。失败静默，不影响主流程。"""
    try:
        _submit(lambda ctx: ctx.new_page().close(), timeout=90)
        logger.info("抖音浏览器预热完成")
    except Exception as exc:  # noqa: BLE001
        logger.info("抖音浏览器预热未完成：%s", exc)


def _grab(context, aweme_id: str, timeout_ms: int) -> dict[str, Any]:
    from playwright.sync_api import TimeoutError as PWTimeout

    page = context.new_page()
    try:
        page.set_default_timeout(timeout_ms)
        # 一律走 /video/{id}：
        # 实测 /note/{id}（图集页）**不会**发出 aweme/detail 请求，
        # 只有 /video/{id} 才会。而 /video/{id} 对图集作品同样返回完整数据
        # （含 images 字段），所以不需要按类型分路径。
        target = f"https://www.douyin.com/video/{aweme_id}"
        captured: dict[str, Any] = {}

        def _predicate(response) -> bool:
            # 注意：Python 版 playwright 里 response.url 是属性，不是方法
            url = response.url
            if not DETAIL_PATH_RE.search(url):
                return False
            return f"aweme_id={aweme_id}" in url

        with page.expect_response(_predicate, timeout=timeout_ms) as info:
            try:
                page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            except PWTimeout:
                # 抖音首屏资源多，domcontentloaded 也可能超时；
                # 只要 detail 请求已经发出，后面的 expect_response 仍能拿到。
                logger.debug("页面导航超时，继续等待 detail 响应")

        response = info.value
        if response.status != 200:
            raise DouyinBrowserError(f"抖音接口返回 {response.status}，请稍后重试")

        payload = response.json()
        if not isinstance(payload, dict):
            raise DouyinBrowserError("抖音返回了非预期的数据格式")

        detail = payload.get("aweme_detail")
        if not isinstance(detail, dict):
            status = payload.get("status_code")
            if status not in (0, None):
                raise DouyinBrowserError(f"抖音拒绝了这个视频（status_code={status}）")
            raise DouyinBrowserError(
                "没取到视频信息。链接可能已删除、被设为私密，或需要登录才能查看"
            )
        return detail
    except PWTimeout as exc:
        raise DouyinBrowserError("等待抖音接口响应超时，请稍后重试") from exc
    finally:
        try:
            page.close()
        except Exception:  # noqa: BLE001
            pass


def fetch_aweme(aweme_id: str, *, timeout: float = 60.0) -> dict[str, Any]:
    """抓取单个作品的完整 JSON（aweme_detail）。线程安全。"""
    if not aweme_id.isdigit():
        raise DouyinBrowserError(f"作品 ID 不合法：{aweme_id}")

    timeout_ms = int(max(15.0, timeout - 10.0) * 1000)
    return _submit(lambda ctx: _grab(ctx, aweme_id, timeout_ms), timeout=timeout)
