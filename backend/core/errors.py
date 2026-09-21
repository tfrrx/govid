"""统一错误类型：后端抛友好中文，前端统一 Toast 展示。

设计原则：任何 yt-dlp 的原始英文报错都不允许直接冒到用户面前，
一律经 translate_error() 映射成人话。
"""

from __future__ import annotations


class GoVidError(Exception):
    """业务错误基类。code 供前端做分支，message 直接展示给用户。"""

    code = "error"
    status_code = 400

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class InvalidURLError(GoVidError):
    code = "invalid_url"

    def __init__(self, message: str = "请输入有效的视频链接"):
        super().__init__(message)


class PlatformNotSupportedError(GoVidError):
    code = "platform_not_supported"

    def __init__(self, message: str = "平台暂不支持，请换一个视频链接试试"):
        super().__init__(message)


class VideoUnavailableError(GoVidError):
    code = "video_unavailable"

    def __init__(self, message: str = "视频不可用，可能已被删除或设为私密"):
        super().__init__(message)


class LoginRequiredError(GoVidError):
    code = "login_required"

    def __init__(self, message: str = "该视频需要登录后才能访问"):
        super().__init__(message)


class NetworkError(GoVidError):
    code = "network_error"

    def __init__(self, message: str = "网络请求超时或中断，请稍后重试"):
        super().__init__(message)


class TaskNotFoundError(GoVidError):
    status_code = 404
    code = "task_not_found"

    def __init__(self, message: str = "任务不存在或已过期"):
        super().__init__(message)


class FFmpegMissingError(GoVidError):
    status_code = 503
    code = "ffmpeg_missing"

    def __init__(self, message: str = "未检测到 ffmpeg，高清音视频合并不可用，请运行 run.sh 自动安装"):
        super().__init__(message)


# yt-dlp 英文报错 → 用户能看懂的中文
_ERROR_RULES: tuple[tuple[tuple[str, ...], type[GoVidError], str], ...] = (
    (
        ("unsupported url", "no suitable extractor", "is not a valid url"),
        PlatformNotSupportedError,
        "平台暂不支持，请换一个视频链接试试",
    ),
    (
        ("private video", "video unavailable", "removed by the uploader", "has been deleted",
         "not available in your country", "this video is not available"),
        VideoUnavailableError,
        "视频不可用，可能已被删除、设为私密或限制地区",
    ),
    (
        ("sign in to confirm", "login required", "cookies", "age-restricted",
         "confirm you're not a bot", "confirm you’re not a bot", "account"),
        LoginRequiredError,
        "该视频需要登录后才能访问（B 站会员 / YouTube 年龄验证等）",
    ),
    (
        ("failed to resolve", "name or service not known", "nodename nor servname",
         "no address associated with hostname", "temporary failure in name resolution",
         "getaddrinfo failed", "name resolution"),
        InvalidURLError,
        "找不到该网站，请检查链接是否拼写正确",
    ),
    (
        ("timed out", "timeout", "connection", "temporary failure", "unable to download",
         "network", "ssl", "proxy", "getaddrinfo", "remote end closed"),
        NetworkError,
        "网络请求超时或中断，请检查网络后重试",
    ),
    (
        ("unsupported", "url"),
        PlatformNotSupportedError,
        "平台暂不支持，请换一个视频链接试试",
    ),
)


def translate_error(exc: BaseException, *, fallback: str = "操作失败，请稍后重试") -> GoVidError:
    """把任意异常翻译成 GoVidError。"""
    if isinstance(exc, GoVidError):
        return exc

    raw = str(exc).lower()
    for keywords, error_cls, message in _ERROR_RULES:
        if any(k in raw for k in keywords):
            return error_cls(message)

    return GoVidError(f"{fallback}（{type(exc).__name__}）")
