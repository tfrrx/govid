# GoVid - 全网视频秒速下载

> 基于 yt-dlp 的 Python 全栈视频下载工具

## 特性

- 🌐 **跨平台支持**：底层 yt-dlp 覆盖 1201 个站点（含 1752 个提取器条目），实测可用情况见 [`docs/03-平台支持矩阵.md`](docs/03-平台支持矩阵.md)
- ⚡️ **极速解析**：实时获取视频信息和多种清晰度
- 📊 **进度可视化**：分段式进度展示（解析 → 下载 → 合并）
- 🎨 **专业体验**：绿色主题、桌面优先响应式设计
- 🎬 **无水印原画**：直取平台源文件，不加水印、不二次转码（抖音支持无水印原图与原视频）
- 💰 **当前版本完全免费**：不限次数、不加水印、不需要注册账号

## 快速开始

### 前置要求

- macOS / Linux
- Node.js ≥ 18
- Python ≥ 3.10（conda 可选，没有就用项目内 `.venv`）
- Google Chrome（仅抖音解析需要；没有则执行 `playwright install chromium` 替代）

### 一键启动

```bash
cd govid
chmod +x run.sh
./run.sh
```

首次运行会安装依赖、构建前端、并自动获取 ffmpeg 静态二进制（约 80MB）。

启动成功后访问：

- 本机：http://localhost:8000
- 手机：http://<本机IP>:8000（同一 Wi-Fi）
- 健康检查：http://localhost:8000/api/health

### 常用参数

```bash
./run.sh --dev          # 后端热重载 + Vite 开发服务器（前端改代码即时生效）
./run.sh --skip-build   # 跳过前端构建，只启服务
./run.sh --rebuild      # 强制重新构建前端
```

### 分享给亲友试用（免备案）

服务跑在本机，想在公网临时分享给别人试，用 Cloudflare 快速隧道即可 —— 不需要买服务器、不需要域名、不涉及备案：

```bash
./run.sh      # 终端 1：跑服务
./share.sh    # 终端 2：起隧道，打印一个 https://xxxx.trycloudflare.com 地址
```

把打印出来的 https 地址发给亲友，手机直接点开就能用。代价是本机要保持开机，且地址每次重启都会变（要固定地址得有自有域名 + 命名隧道）。详见 [`docs/02-技术架构文档.md`](docs/02-技术架构文档.md) §7.6。

## 实现状态

阶段 1（核心下载）与阶段 2（完整落地页）已完成并在真实浏览器中端到端验收通过，
截图存放在 `docs/screenshots/`。阶段 3（AI 增值）及之后尚未开始。

已验收：B 站解析 / 清晰度列表 / 实时进度 / 分段进度 / 文件下载 / 中文文件名 / 错误提示 / 桌面与移动端布局。

## 技术栈

- 后端：FastAPI + yt-dlp + Python 3.13
- 前端：Vue 3 + Vite + Tailwind CSS v4
- 环境：conda（可选）/ 项目内 venv
- 任务队列：进程内字典 + 线程（阶段 1-2 够用）

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查（ffmpeg 状态、队列深度、文件保留时长） |
| POST | `/api/parse` | 解析视频，返回元信息 + 清晰度列表 |
| POST | `/api/tasks` | 创建下载任务 |
| GET | `/api/tasks/{id}` | 查询进度（建议 1 秒轮询一次） |
| POST | `/api/tasks/{id}/cancel` | 取消下载 |
| GET | `/api/tasks/{id}/file` | 下载文件（UTF-8 文件名） |
| GET | `/api/proxy/thumbnail?url=` | 缩略图代理（绕过防盗链） |

## 目录结构

```
govid/
├── run.sh                 一键启动
├── share.sh               临时公网分享（Cloudflare 隧道）
├── backend/
│   ├── main.py            FastAPI 入口 + 前端静态托管 + SPA 兜底
│   ├── config.py          环境变量
│   ├── core/
│   │   ├── ffmpeg.py      ffmpeg 自动检测 / 自动获取
│   │   ├── media.py       平台路由 + yt-dlp 封装：解析 + 下载
│   │   ├── tasks.py       内存任务队列 + 进度聚合 + 过期回收
│   │   └── errors.py      统一错误类型与中文翻译
│   ├── extractors/
│   │   └── douyin/        抖音独立通道（不走 yt-dlp，不碰用户 cookie）
│   │                      browser.py 借签名 / parser.py 结构转换 / downloader.py 直链下载
│   ├── api/               health / video 路由
│   └── models/            pydantic 请求响应模型
└── frontend/
    └── src/
        ├── components/    输入、结果、进度、Toast + 落地页各区块
        ├── composables/   useDownloader 状态机
        ├── api/           后端接口封装
        └── style.css      设计 Token（Tailwind v4 @theme）
```

## 配置

复制 `.env.example` 为 `.env` 后按需修改，常用项：

| 变量 | 默认 | 说明 |
|------|------|------|
| `GOVID_PORT` | `8000` | 服务端口 |
| `GOVID_MAX_CONCURRENT_DOWNLOADS` | `2` | 并发下载数 |
| `GOVID_MAX_FORMATS` | `15` | 返回的清晰度档位上限 |
| `GOVID_TASK_TTL_HOURS` | `2` | 任务与临时文件保留时长；超时自动删除，前端会提示用户 |
| `GOVID_MAX_TMP_GB` | `20` | `tmp/` 占用上限，超出按最旧回收；`0` 关闭 |
| `GOVID_PROXY` | 空 | 网络代理，如 `http://127.0.0.1:7890`。**下 YouTube / X / Instagram 等国际站必须配** |

## 平台支持

底层是 yt-dlp，具备 1752 个提取器（1201 个顶级站点）；**抖音单独走一条自研通道**（`extractors/douyin`），不经过 yt-dlp。**实测可用情况**：

| 状态 | 平台 |
|------|------|
| ✅ 端到端验证通过 | 哔哩哔哩、**抖音（视频 + 图集，无需任何 cookie）** |
| ✅ 解析通过 | 网易云音乐、微博（`video.weibo.com` 格式）、腾讯视频（非 VIP）、YouTube（需配代理） |
| ⚠️ 需 cookies | 西瓜视频、Vimeo |
| ❌ 不支持 | 快手、乐视、PPTV、土豆、凤凰网、咪咕、1905、Netflix、Spotify 等 |

### 关于抖音

抖音自 2026-09-14 起给 `aweme/detail` 接口加上 `x-secsdk-web-signature` 门禁，该签名**只能由抖音网页内的 SDK 生成**，纯 HTTP 客户端（含 yt-dlp、含自己手算 `a_bogus`）一律收到：

```
403 Blocked by ArgusSecurityPlugin Uifid Not Found
```

**这个 403 与 cookie 无关** —— 带不带都一样。本项目因此另建通道：用一个**全新的、不含任何用户数据的**浏览器上下文打开抖音页面，让抖音自己的 JS 去生成签名，我们只读取页面自身发出的响应；真正的下载走纯 HTTP 直链。

- 不读取、不导入、不注入你浏览器里的任何 cookie 或登录态
- 支持视频（多档清晰度、无水印）与**图集**（原图打包 zip）
- 短链 `v.douyin.com/xxx`、网页链接、整段分享文案都能直接粘贴
- 只需机器上装了 Google Chrome（没有则可 `playwright install chromium`）

原理与踩坑详见 [`docs/02-技术架构文档.md`](docs/02-技术架构文档.md) §4.4，平台矩阵见 [`docs/03-平台支持矩阵.md`](docs/03-平台支持矩阵.md) §3.3。

## 项目文档

| 文档 | 内容 |
|------|------|
| [`docs/01-需求分析文档.md`](docs/01-需求分析文档.md) | 需求清单、验收标准、决策记录、变更记录 |
| [`docs/02-技术架构文档.md`](docs/02-技术架构文档.md) | 架构、模块职责、API 契约、关键踩坑、扩展指引 |
| [`docs/03-平台支持矩阵.md`](docs/03-平台支持矩阵.md) | 平台实测结果与自测方法 |
| [`GoVid开发计划书.md`](GoVid开发计划书.md) | 原始规划与实施记录 |

## 许可证

仅供学习和个人使用。使用本工具下载的内容请遵守相关平台的服务条款和版权法律。
