# GoVid 后端 - Render 免费层优化版
FROM python:3.12-slim

# 设置环境变量，减少内存使用
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（分步安装，减少内存峰值）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装 Chromium（抖音需要，但可选）
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY backend/requirements.txt .

# 分批安装 Python 依赖，避免内存溢出
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic-settings python-multipart
RUN pip install --no-cache-dir aiofiles httpx
RUN pip install --no-cache-dir yt-dlp[default]
RUN pip install --no-cache-dir playwright

# 安装 Playwright 浏览器依赖（只装必需的）
RUN playwright install-deps chromium

# 复制后端代码
COPY backend/ .

# 创建下载目录
RUN mkdir -p /tmp/downloads

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health')"

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
