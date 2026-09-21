#!/usr/bin/env bash
#
# GoVid 一键启动脚本
#
#   ./run.sh              # 装依赖 + 构建前端 + 启动服务（默认，幂等）
#   ./run.sh --skip-build # 跳过前端构建，只启服务
#   ./run.sh --rebuild    # 强制重新构建前端
#   ./run.sh --dev        # 后端热重载 + Vite 开发服务器（前端改代码即时生效）
#
# 环境策略：有 conda 就用名为 govid 的 conda 环境；没有 conda 就退回到
# 项目内的 .venv（Python 3.13）。两条路都留，换机器不用改脚本。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
YTDLP_DIR="${ROOT_DIR}/../yt-dlp"
VENV_DIR="${ROOT_DIR}/.venv"

MODE="default"
for arg in "$@"; do
  case "$arg" in
    --skip-build) MODE="skip-build" ;;
    --rebuild)    MODE="rebuild" ;;
    --dev)        MODE="dev" ;;
    -h|--help)    sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "未知参数：$arg（用 --help 看用法）" >&2; exit 1 ;;
  esac
done

step() { printf '\n\033[1;32m▸ %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$1"; }
fail() { printf '\033[1;31m✗ %s\033[0m\n' "$1" >&2; exit 1; }

# ---------------------------------------------------------------- 1. yt-dlp

[ -d "${YTDLP_DIR}" ] || fail "未找到 yt-dlp 仓库：${YTDLP_DIR}"

# ---------------------------------------------------------------- 2. Python 环境

PYTHON_BIN=""
PIP_BIN=""
USE_CONDA=0

if command -v conda >/dev/null 2>&1; then
  USE_CONDA=1
elif [ -x "${VENV_DIR}/bin/python" ]; then
  PYTHON_BIN="${VENV_DIR}/bin/python"
  PIP_BIN="${VENV_DIR}/bin/pip"
else
  # 优先用 WorkBuddy 受管 Python 3.13，其次系统 python3
  CANDIDATE_PY=""
  for candidate in \
    "${HOME}/.workbuddy/binaries/python/versions/3.13.12/bin/python3" \
    "$(command -v python3.13 || true)" \
    "$(command -v python3 || true)"
  do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      CANDIDATE_PY="$candidate"
      break
    fi
  done
  [ -n "${CANDIDATE_PY}" ] || fail "找不到 Python 3.10+，请先安装 Python 或 conda"

  step "创建虚拟环境 .venv（${CANDIDATE_PY}）"
  "${CANDIDATE_PY}" -m venv "${VENV_DIR}"
  PYTHON_BIN="${VENV_DIR}/bin/python"
  PIP_BIN="${VENV_DIR}/bin/pip"
fi

if [ "${USE_CONDA}" -eq 1 ]; then
  step "使用 conda 环境 govid"
  # shellcheck disable=SC1091
  eval "$(conda shell.bash hook)"
  if ! conda env list | awk '{print $1}' | grep -qx "govid"; then
    conda create -y -n govid python=3.13
  fi
  conda activate govid
  PYTHON_BIN="$(command -v python)"
  PIP_BIN="$(command -v pip)"
  PY_VER="$(python -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  case "${PY_VER}" in
    3.9|3.8|3.7) fail "Python ${PY_VER} 太旧，yt-dlp 需要 3.10+" ;;
  esac
else
  PY_VER="$("${PYTHON_BIN}" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  case "${PY_VER}" in
    3.9|3.8|3.7) fail "Python ${PY_VER} 太旧，yt-dlp 需要 3.10+" ;;
  esac
fi

step "Python ${PY_VER} 就绪"

# ---------------------------------------------------------------- 3. 后端依赖

needs_backend_install=0
"${PYTHON_BIN}" -c "import yt_dlp, fastapi, uvicorn, static_ffmpeg, imageio_ffmpeg, httpx" >/dev/null 2>&1 || needs_backend_install=1

if [ "${needs_backend_install}" -eq 1 ]; then
  step "安装后端依赖（首次较慢，最长几分钟）"
  "${PIP_BIN}" install --quiet --upgrade pip || warn "pip 升级失败，继续"
  "${PIP_BIN}" install --timeout 120 --retries 8 -e "${YTDLP_DIR}[default]"
  "${PIP_BIN}" install --timeout 120 --retries 8 -r "${BACKEND_DIR}/requirements.txt"
else
  step "后端依赖已就绪，跳过"
fi

# playwright 单独检查：只有抖音通道需要它，缺了不该拖累其他平台。
# 它不需要 `playwright install`，直接复用系统已装的 Google Chrome。
if ! "${PYTHON_BIN}" -c "import playwright" >/dev/null 2>&1; then
  step "安装抖音解析所需的 playwright（约 43MB）"
  "${PIP_BIN}" install --timeout 120 --retries 8 "playwright>=1.48" \
    || warn "playwright 安装失败：抖音链接将无法解析，其他平台不受影响"
fi

if [ "$(uname)" = "Darwin" ] && [ ! -d "/Applications/Google Chrome.app" ]; then
  warn "未检测到 Google Chrome：抖音解析需要它，或执行 \`playwright install chromium\` 作为替代"
fi

# ---------------------------------------------------------------- 4. ffmpeg

step "检查 ffmpeg（首次会自动下载静态二进制，约 80MB）"
if ! "${PYTHON_BIN}" -c "
import sys, shutil
sys.path.insert(0, '${BACKEND_DIR}')
from core.ffmpeg import detect_ffmpeg
sys.exit(0 if detect_ffmpeg() else 1)
" ; then
  warn "ffmpeg 不可用：高清音视频合并与音频转码会被禁用，其余功能正常"
fi

# ---------------------------------------------------------------- 5. 前端

[ -f "${FRONTEND_DIR}/package.json" ] || fail "未找到 ${FRONTEND_DIR}/package.json"

if [ "${MODE}" != "skip-build" ]; then
  if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
    step "安装前端依赖"
    (cd "${FRONTEND_DIR}" && npm install --no-audit --no-fund)
  fi

  if [ "${MODE}" = "rebuild" ] || [ ! -f "${FRONTEND_DIR}/dist/index.html" ]; then
    step "构建前端"
    (cd "${FRONTEND_DIR}" && npm run build)
  else
    step "前端已构建，跳过（要强制重建用 ./run.sh --rebuild）"
  fi
fi

# ---------------------------------------------------------------- 6. 启动

LOCAL_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo '127.0.0.1')"
PORT="$("${PYTHON_BIN}" -c "
import sys
sys.path.insert(0, '${BACKEND_DIR}')
from config import settings
print(settings.port)
")"

if [ "${MODE}" = "dev" ]; then
  step "开发模式：后端热重载 + Vite 开发服务器"
  (
    cd "${BACKEND_DIR}"
    GOVID_RELOAD=true "${PYTHON_BIN}" main.py
  ) &
  BACKEND_PID=$!
  trap 'kill ${BACKEND_PID} 2>/dev/null || true' EXIT INT TERM
  sleep 2
  echo ""
  echo "  API   http://localhost:${PORT}/api/health"
  echo "  页面  http://localhost:5173"
  echo ""
  cd "${FRONTEND_DIR}" && npm run dev
  exit 0
fi

echo ""
printf '\033[1;32m✅ GoVid 已就绪\033[0m\n'
echo ""
echo "  🌐 本机访问   http://localhost:${PORT}"
echo "  📱 局域网访问 http://${LOCAL_IP}:${PORT}"
echo "  🩺 健康检查   http://localhost:${PORT}/api/health"
echo ""
echo "  按 Ctrl+C 停止服务"
echo ""

cd "${BACKEND_DIR}"
exec "${PYTHON_BIN}" main.py
