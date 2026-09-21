#!/usr/bin/env bash
#
# GoVid 临时公网分享 —— 让亲友直接在手机上试用，不用买服务器、不用备案
#
# 原理：用 Cloudflare 的「快速隧道」把本机 8000 端口映射到一个 https 公网地址。
#   - 快速隧道不需要 Cloudflare 账号、不需要域名、不需要公网 IP；
#   - 备案只针对**中国大陆境内**的服务器，这里流量落在中国香港/境外的 Cloudflare
#     边缘节点，再回源到你自己电脑，不涉及备案；
#   - 亲友打开 https 地址即可使用，无需安装任何东西。
#
# 用法：
#   ./share.sh                 # 默认转发本机 8000
#   ./share.sh --port 9000     # 指定端口
#
# 注意：
#   - 地址每次重启都会变（形如 https://xxx-yyy-zzz.trycloudflare.com）
#   - 你的电脑要保持开机，并且服务（./run.sh）与这个隧道都别关
#   - 结束后 Ctrl+C 即可，隧道随之中断

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="${ROOT_DIR}/.bin/cloudflared"
PORT=8000

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="${2:-8000}"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "未知参数：$1（用 --help 看用法）" >&2; exit 1 ;;
  esac
done

green() { printf '\033[1;32m%s\033[0m\n' "$1"; }
warn()  { printf '\033[1;33m%s\033[0m\n' "$1"; }
fail()  { printf '\033[1;31m%s\033[0m\n' "$1" >&2; exit 1; }

# ---------------------------------------------------------------- 1. cloudflared

if [[ ! -x "${BIN}" ]]; then
  warn "未找到 cloudflared，正在下载（约 19MB，一次性）…"
  mkdir -p "${ROOT_DIR}/.bin"
  ARCH="$(uname -m)"
  case "${ARCH}" in
    arm64)  PKG="cloudflared-darwin-arm64.tgz" ;;
    x86_64) PKG="cloudflared-darwin-amd64.tgz" ;;
    *)      fail "不支持的架构：${ARCH}" ;;
  esac
  curl -fL --progress-bar -o "${ROOT_DIR}/.bin/${PKG}" \
    "https://github.com/cloudflare/cloudflared/releases/latest/download/${PKG}" \
    || fail "下载 cloudflared 失败，请检查网络后重试"
  tar -xzf "${ROOT_DIR}/.bin/${PKG}" -C "${ROOT_DIR}/.bin/"
  rm -f "${ROOT_DIR}/.bin/${PKG}"
  chmod +x "${BIN}"
  green "cloudflared 就绪"
fi

# ---------------------------------------------------------------- 2. 本地服务

if ! curl -s -m 5 --noproxy '*' -o /dev/null "http://127.0.0.1:${PORT}/api/health"; then
  fail "本机 ${PORT} 端口没有服务在跑。先在另一个终端执行 ./run.sh，再回来跑这个脚本。"
fi
green "本地服务在跑（127.0.0.1:${PORT}），开始建立隧道…"

# ---------------------------------------------------------------- 3. 起隧道

echo
echo "---------------------------------------------------------------"
echo " 隧道建立后会打印一个 https://xxxx.trycloudflare.com 地址，"
echo " 把它发给亲友，手机点开就能用。按 Ctrl+C 结束分享。"
echo "---------------------------------------------------------------"
echo

"${BIN}" tunnel --url "http://127.0.0.1:${PORT}" --no-autoupdate 2>&1 | while IFS= read -r line; do
  echo "$line"
  case "$line" in
    *trycloudflare.com*)
      url="$(printf '%s' "$line" | grep -oE 'https://[a-z0-9][a-z0-9-]*\.trycloudflare\.com' || true)"
      if [[ -n "${url}" ]]; then
        printf '\n\033[1;32m>>> 分享这个地址给亲友： %s\033[0m\n' "${url}"
        printf '\033[1;33m    提醒：对方若在微信 / QQ 里点开，需要点右上角「⋯」→「在浏览器打开」，\033[0m\n'
        printf '\033[1;33m    否则内置浏览器存不了文件（这是微信的限制，不是服务的问题）。\033[0m\n\n'
      fi
      ;;
  esac
done
