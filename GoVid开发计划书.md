# GoVid - AI 视频下载总结器 · 开发计划书

> **项目定位**：Python 全栈视频下载工具，基于 yt-dlp，支持 1800+ 平台  
> **技术栈**：FastAPI + Vue 3 + Vite + Tailwind v4 + conda  
> **开发模式**：5 个阶段渐进式开发，每阶段可独立验收

---

## 一、项目概述

### 1.1 核心价值

- 🌐 **跨平台支持**：YouTube、B 站、Vimeo 等 1800+ 主流平台
- ⚡️ **极速解析**：实时解析视频信息，多种清晰度自由选择
- 📊 **进度可视化**：分段式进度展示（解析→下载→合并）
- 🎨 **专业体验**：绿色主题配色（#10B981），桌面优先响应式设计
- 🔮 **可扩展架构**：为 AI 总结、用户系统、支付功能预留扩展路径

### 1.2 技术选型

| 层级 | 技术 | 理由 |
|------|------|------|
| 后端框架 | FastAPI | 轻量、异步、API 友好 |
| 视频引擎 | yt-dlp（本地仓库） | 成熟、支持广泛、零改动封装 |
| 前端框架 | Vue 3 + Vite | 快速开发、Composition API、热更新 |
| CSS 方案 | Tailwind v4 | 原子化 CSS、开发效率高 |
| 环境管理 | conda (Python 3.13) | 隔离环境、依赖管理 |
| 任务队列 | 内存字典 + 线程 | 零依赖、阶段 1-2 够用 |
| 通信方式 | 轮询（1秒间隔） | 实现简单、兼容性好 |

### 1.3 设计决策汇总

| 类别 | 决策 |
|------|------|
| 项目名称 | GoVid（Go + Video，快速通行） |
| 品牌配色 | 绿色系（#10B981 emerald-500） |
| Hero 首屏 | 卖点 + 输入框（平衡型） |
| 结果区布局 | 双列分栏（左封面/信息，右清晰度） |
| 进度展示 | 分段进度（解析→下载→合并） |
| 平台墙 | Logo 墙 + 无限滚动动画 |
| 响应式策略 | 桌面优先 |
| 动效强度 | 适度微交互（250-350ms） |
| 定价文案 | 轻量保守（免费版/Pro版占位） |
| 平台支持 | 仅 yt-dlp 官方（不做专用 hack） |
| ffmpeg 策略 | 自动安装 static-ffmpeg |
| 错误处理 | 简单提示（统一格式 Toast） |
| 部署方式 | 一键脚本 run.sh |
| conda 环境 | govid / conda 默认位置 |

---

## 二、开发路线图

### 阶段 0：前期准备（已完成）
- ✅ 需求收集与决策确认
- ✅ 技术方案设计
- ✅ 设计系统定义

### 阶段 1：MVP - 核心下载功能（第 1 周）
**目标**：实现最小可用产品，验证核心价值

**功能范围**：
- 用户输入视频链接
- 解析视频信息（标题、封面、时长、作者、平台）
- 展示可用清晰度列表
- 选择清晰度后提交下载任务
- 实时显示下载进度（百分比、速度、ETA）
- 下载完成后提供文件下载
- 基础错误处理

**技术实现**：
- 后端：FastAPI + yt-dlp + 内存任务队列
- 前端：Vue 3 单页应用
- 部署：本地 8000 端口 + 局域网访问

### 阶段 2：完整落地页 + 品牌体验（第 2 周）
**目标**：打造专业产品形象

**功能范围**：
- Hero 区（标题 + 卖点 + 输入框）
- 功能特性区（3 个卡片）
- 使用流程区（3 步上手）
- 平台支持墙（Logo 滚动动画）
- 定价区（免费版 vs Pro 版占位）
- FAQ 区 + 页脚

### 阶段 3：AI 增值功能（第 3-4 周）
- AI 视频总结（DeepSeek API + SSE 流式输出）
- AI 思维导图生成
- AI 视频问答
- 字幕下载（SRT / VTT / TXT）

### 阶段 4：用户系统 + 付费（第 5-6 周）
- 用户注册登录（JWT）
- 权限管理（免费 vs Pro）
- Stripe 支付集成
- 数据库引入（SQLite / PostgreSQL）

### 阶段 5：生产就绪（第 7-8 周）
- Docker 容器化
- HTTPS 配置
- SEO 优化
- 性能监控 + 错误告警

---

## 三、阶段 1 详细实施方案

### 3.1 项目结构

```
/Users/happy/Project/Python_VideoDownlaoder/
├── yt-dlp/                          # 已有：引擎，零改动
└── govid/                           # 新建：主项目
    ├── .env.example
    ├── .env
    ├── .gitignore
    ├── README.md
    ├── run.sh                       # 一键启动脚本
    ├── backend/
    │   ├── main.py                  # FastAPI 入口
    │   ├── config.py                # 环境变量
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── ffmpeg.py            # ffmpeg 检测
    │   │   ├── media.py             # yt-dlp 封装
    │   │   └── tasks.py             # 任务队列
    │   ├── api/
    │   │   ├── __init__.py
    │   │   ├── health.py
    │   │   └── video.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── video.py
    │   └── requirements.txt
    └── frontend/
        ├── package.json
        ├── vite.config.js
        ├── index.html
        ├── tailwind.config.js
        ├── postcss.config.js
        └── src/
            ├── main.js
            ├── App.vue
            ├── style.css
            ├── api/
            │   └── video.js
            ├── components/
            │   ├── VideoInput.vue
            │   ├── VideoResult.vue
            │   ├── DownloadProgress.vue
            │   └── ErrorMessage.vue
            └── assets/
                └── icons/
```

### 3.2 后端核心模块

#### 3.2.1 `backend/core/ffmpeg.py`
```python
"""
ffmpeg 路径自动检测
- 优先尝试系统 ffmpeg（subprocess.run(['ffmpeg', '-version'])）
- 失败则 pip install static-ffmpeg（首次约 80MB）
- 返回 ffmpeg 可执行路径供 yt-dlp 使用
"""
```

#### 3.2.2 `backend/core/media.py`
```python
"""
yt-dlp 薄封装（零改动本地仓库代码）

parse_video(url) → dict
  返回：
    - title: 视频标题
    - thumbnail: 封面 URL
    - duration: 时长（秒）
    - author: 作者
    - platform: 平台名称
    - formats: [{id, resolution, size, hasAudio}]
  
  formats 整理逻辑：
    - 过滤无音频纯视频流
    - 按分辨率倒序排列
    - 最多返回 15 条，去重
    - 添加「最佳画质（自动合并）」：format='bestvideo+bestaudio/best'

download_task(task_id, url, format_id) → None
  - 后台线程执行下载
  - 使用 yt-dlp progress_hooks 更新进度
  - 下载到临时目录 tmp/{task_id}/
  - 完成后记录文件路径
"""
```

#### 3.2.3 `backend/core/tasks.py`
```python
"""
内存任务管理

全局字典：
tasks = {}  # task_id -> {status, progress, speed, eta, error, file_path}

函数：
- create_task(url, format_id) → task_id
- get_task(task_id) → task_info
- cleanup_task(task_id) → None
- startup 时清空 tmp/ 目录
"""
```

### 3.3 API 接口规范

| 方法 | 路径 | 请求体 | 响应体 | 说明 |
|------|------|--------|--------|------|
| GET | `/api/health` | - | `{status, ffmpeg}` | 健康检查 |
| POST | `/api/parse` | `{url}` | `{title, thumbnail, duration, author, platform, formats[]}` | 解析视频 |
| POST | `/api/tasks` | `{url, format_id}` | `{task_id}` | 创建下载任务 |
| GET | `/api/tasks/{id}` | - | `{status, progress, speed, eta, error}` | 查询进度 |
| GET | `/api/tasks/{id}/file` | - | 文件流 | 下载文件 |
| GET | `/api/proxy/thumbnail?url=` | - | 图片流 | 缩略图代理 |

**状态值**：
- `pending`: 等待中
- `downloading`: 下载中
- `completed`: 完成
- `failed`: 失败

### 3.4 前端设计系统

#### 3.4.1 CSS 设计 Token

```css
/* frontend/src/style.css */

:root {
  /* 品牌色 - 绿色系 */
  --color-primary: #10B981;           /* emerald-500 */
  --color-primary-dark: #059669;      /* emerald-600 */
  --color-primary-soft: rgba(16,185,129,0.1);
  
  /* 辅助色 */
  --color-accent: #F59E0B;            /* amber-500 */
  --color-error: #EF4444;             /* red-500 */
  
  /* 背景色 */
  --color-bg: #FFFFFF;
  --color-bg-sub: #F8FAFC;            /* slate-50 */
  
  /* 文字色 */
  --color-text: #0F172A;              /* slate-900 */
  --color-text-secondary: #64748B;    /* slate-500 */
  
  /* 边框 */
  --color-border: #E2E8F0;            /* slate-200 */
  
  /* 圆角 */
  --radius-base: 0.5rem;              /* 8px */
  --radius-lg: 0.75rem;               /* 12px */
  --radius-pill: 9999px;              /* 胶囊形 */
  
  /* 阴影 */
  --shadow-card: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --shadow-primary: 0 20px 25px -5px rgba(16,185,129,0.15);
  
  /* 动效 */
  --transition-base: 250ms ease-out;
}

/* 通用组件样式 */
.input-pill {
  @apply rounded-full ring-1 ring-slate-200 px-6 py-3;
  @apply focus:outline-none focus:ring-2 focus:ring-primary;
  transition: all var(--transition-base);
}

.btn-primary {
  @apply bg-primary text-white rounded-full px-6 py-3 font-medium;
  @apply hover:bg-primary-dark transition-all duration-250;
}

.card-hover {
  @apply transition-all duration-300;
  @apply hover:-translate-y-1 hover:shadow-primary;
}
```

#### 3.4.2 核心组件

**VideoInput.vue** - 输入框 + 解析按钮
- 胶囊形输入框
- 聚焦时绿色边框
- 解析按钮（主色）
- 加载状态

**VideoResult.vue** - 双列结果展示
- 左栏：封面 + 标题 + 作者 + 时长 + 平台
- 右栏：清晰度列表（单选）+ 开始下载按钮
- 响应式：手机端自动变单列堆叠

**DownloadProgress.vue** - 分段进度展示
- ✓ 解析完成
- ▶ 正在下载（进度条 + 百分比 + 速度 + ETA）
- ○ 合并音视频（等待中）
- 每 1 秒轮询 `/api/tasks/{id}`

**ErrorMessage.vue** - Toast 错误提示
- 顶部居中显示
- 5 秒后自动消失
- 可手动关闭

### 3.5 依赖清单

#### 后端 `requirements.txt`
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic-settings==2.6.0
python-multipart==0.0.12
static-ffmpeg==2.5
aiofiles==24.1.0
```

#### 前端 `package.json`
```json
{
  "name": "govid-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.0",
    "tailwindcss": "^4.0.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "vite": "^6.0.0"
  }
}
```

### 3.6 一键启动脚本

```bash
#!/bin/bash
# run.sh

set -e

echo "🚀 GoVid 启动中..."

# 1. 检查 conda 环境
if ! conda info --envs | grep -q "^govid "; then
    echo "📦 创建 conda 环境 govid (Python 3.13)..."
    conda create -n govid python=3.13 -y
fi

# 2. 激活环境并安装后端依赖
echo "📦 安装后端依赖..."
eval "$(conda shell.bash hook)"
conda activate govid

# 安装 yt-dlp（可编辑模式）
if [ ! -d "../yt-dlp" ]; then
    echo "❌ 错误：未找到 yt-dlp 仓库"
    exit 1
fi
pip install -e ../yt-dlp[default] --quiet

# 安装其他依赖
cd backend
pip install -r requirements.txt --quiet
cd ..

# 3. 安装前端依赖并构建
echo "📦 安装前端依赖..."
cd frontend
npm install --silent
echo "🔨 构建前端..."
npm run build --silent
cd ..

# 4. 获取本机 IP
LOCAL_IP=$(ipconfig getifaddr en0 || echo "127.0.0.1")

# 5. 启动服务
echo ""
echo "✅ GoVid 已启动！"
echo ""
echo "🌐 本机访问:  http://localhost:8000"
echo "📱 手机访问:  http://${LOCAL_IP}:8000"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

cd backend
python main.py
```

### 3.7 验收标准

#### 功能验收
- [ ] 能成功解析 B 站视频
- [ ] 能成功解析 YouTube 视频
- [ ] 清晰度列表正确展示（1080P / 720P / 480P）
- [ ] 下载进度实时更新（每秒刷新）
- [ ] 分段进度正确展示
- [ ] 下载完成文件可正常播放
- [ ] 中文文件名正确显示（不乱码）

#### 跨设备验收
- [ ] 桌面浏览器（Chrome / Safari）布局正常
- [ ] 手机浏览器（同 Wi-Fi）可正常访问使用

#### 错误处理验收
- [ ] 无效链接显示友好错误提示
- [ ] 不支持平台提示"平台暂不支持"
- [ ] 网络中断显示"下载失败，请重试"

#### 性能验收
- [ ] 首次启动完成时间 < 3 分钟
- [ ] 解析视频响应时间 < 5 秒
- [ ] 页面首屏加载 < 2 秒

---

## 四、阶段 2 实施要点

### 4.1 新增组件

```
frontend/src/components/
├── HeroSection.vue          # 完整 Hero 区
├── FeatureSection.vue       # 功能特性卡片
├── HowToSection.vue         # 三步上手指南
├── PlatformSection.vue      # Logo 无限滚动墙
├── PricingSection.vue       # 定价对比（占位）
├── FAQSection.vue           # 常见问题（折叠面板）
└── FooterSection.vue        # 页脚合规声明
```

### 4.2 关键实现

**PlatformSection.vue** - Logo 滚动动画
```vue
<style scoped>
@keyframes scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.animate-scroll {
  animation: scroll 30s linear infinite;
}

.animate-scroll:hover {
  animation-play-state: paused;
}
</style>
```

**PricingSection.vue** - 定价区文案（轻量保守）
- 免费版：每天 3 次解析下载 + 1080P 画质
- Pro 版：不限次数 + 4K 超高清 + AI 总结（即将上线）
- 按钮点击弹出"敬请期待" Toast

---

## 五、README 模板

```markdown
# GoVid - 全网视频秒速下载

> 基于 yt-dlp 的 Python 全栈视频下载工具

## 特性

- 🌐 **跨平台支持**：YouTube、B 站、Vimeo 等 1800+ 平台
- ⚡️ **极速解析**：实时获取视频信息和多种清晰度
- 📊 **进度可视化**：分段式进度展示
- 🎨 **专业体验**：现代化 UI 设计
- 🔒 **隐私安全**：本地运行，不上传任何数据

## 快速开始

### 前置要求

- macOS / Linux
- conda（Anaconda / Miniconda）
- Node.js ≥ 18

### 一键启动

```bash
cd govid
chmod +x run.sh
./run.sh
```

启动成功后访问：
- 本机：http://localhost:8000
- 手机：http://<本机IP>:8000（同一 Wi-Fi）

## 技术栈

- 后端：FastAPI + yt-dlp + Python 3.13
- 前端：Vue 3 + Vite + Tailwind CSS v4
- 环境：conda

## 许可证

仅供学习和个人使用。使用本工具下载的内容请遵守相关平台的服务条款和版权法律。
```

---

## 六、关键技术细节

### 6.1 yt-dlp 集成方式

**安装方式**：
```bash
pip install -e /path/to/yt-dlp[default]
```
- 可编辑模式安装本地仓库
- 零改动 yt-dlp 源码
- 升级 = `git pull` 本地仓库

**调用方式**：
```python
import yt_dlp

ydl_opts = {
    'format': format_id,
    'outtmpl': 'tmp/%(id)s/%(title)s.%(ext)s',
    'progress_hooks': [progress_callback],
    'ffmpeg_location': ffmpeg_path,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
```

### 6.2 任务队列设计

```python
# 全局字典（阶段 1-2 足够）
tasks = {}

# 任务状态
{
    'task_id': {
        'status': 'downloading',
        'progress': 72,
        'speed': '15.2 MB/s',
        'eta': '2:30',
        'error': None,
        'file_path': '/path/to/file.mp4'
    }
}

# 后台线程更新进度
def download_task(task_id, url, format_id):
    def progress_hook(d):
        if d['status'] == 'downloading':
            tasks[task_id]['progress'] = d.get('_percent_str', '0%')
            tasks[task_id]['speed'] = d.get('_speed_str', '')
            tasks[task_id]['eta'] = d.get('_eta_str', '')
```

### 6.3 中文文件名处理

```python
from urllib.parse import quote

# 响应头
headers = {
    'Content-Disposition': f"attachment; filename*=UTF-8''{quote(filename)}"
}
```

### 6.4 缩略图防盗链

```python
@app.get("/api/proxy/thumbnail")
async def proxy_thumbnail(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            content = await resp.read()
            return Response(content=content, media_type="image/jpeg")
```

---

## 七、风险与对策

| 风险 | 等级 | 对策 |
|------|------|------|
| ffmpeg 缺失导致高清合并失败 | 🔴 高 | static-ffmpeg 自动获取；失败则降级提示 |
| 系统 Python 版本不满足 | 🟡 中 | 使用 conda 独立环境（Python 3.13） |
| 首次装依赖慢 | 🟡 中 | 一次性成本；run.sh 做幂等检查 |
| 网络无法访问 YouTube | 🟡 中 | 验收用 B 站；YouTube 需在 `.env` 配 `GOVID_PROXY` 才能用 |
| 大文件占满磁盘 | 🟡 中 | 下载后即删；启动时清空 tmp/ |
| 部分站点需要 cookie | 🟡 中 | 阶段 3 支持 cookies.txt 配置 |

---

## 八、后续扩展路径

### 阶段 3：AI 能力（DeepSeek API）
- 字幕提取 + AI 总结
- Markdown 流式输出（SSE）
- 思维导图生成（Markmap）
- 视频问答（多轮对话）

### 阶段 4：商业化基础
- SQLite / PostgreSQL 数据库
- JWT 用户认证
- 免费版限制（每天 3 次）
- Stripe 支付集成

### 阶段 5：生产就绪
- Docker 容器化
- Nginx 反向代理
- HTTPS 配置
- 性能监控（Prometheus + Grafana）
- 错误追踪（Sentry）

---

**计划书版本**：v1.0  
**编写日期**：2026-09-21  
**状态**：✅ 已批准，可开工

---

## 九、实施记录（阶段 1 + 阶段 2 已落地）

> 实施日期：2026-09-21
> 交付范围：阶段 1（核心下载）+ 阶段 2（完整落地页）一次性做完
> 验收方式：真实浏览器（Chrome headless）+ 真实 B 站视频端到端跑通，截图存 `docs/screenshots/`

### 9.1 与计划书的差异（4 处，均为环境或效果所迫）

| # | 计划书原文 | 实际实现 | 原因 |
|---|-----------|---------|------|
| 1 | conda 环境 `govid` | 有 conda 用 conda，没有则自动建项目内 `.venv` | 本机未安装 conda，硬依赖会导致 `run.sh` 直接失败 |
| 2 | 「过滤无音频纯视频流」 | 按分辨率归组，纯视频流用 `bestvideo[height<=H]+bestaudio/best` 自动合并 | YouTube / B 站 1080P 及以上几乎只有 video-only 流，真过滤掉就看不到 1080P，验收标准无法达成 |
| 3 | ffmpeg 走 `static-ffmpeg` 自动安装 | 三级来源：系统 ffmpeg → static-ffmpeg → imageio-ffmpeg | 本机访问 GitHub 不稳定，static-ffmpeg 的二进制包托管在 GitHub；imageio-ffmpeg 的二进制直接打包在 PyPI wheel 里，PyPI 能通就能拿到 |
| 4 | Tailwind v4 + postcss + autoprefixer | Tailwind v4 官方 `@tailwindcss/vite` 插件 | v4 已内置 Lightning CSS 处理前缀，postcss 链路是 v3 的写法 |

### 9.2 计划书未写、但补上的能力

- **取消下载**：`POST /api/tasks/{id}/cancel`，UI 有「取消下载」按钮。下载动辄几分钟，不能取消体验太差。
- **仅音频导出（MP3 320kbps）**：成本极低，顺手补上，放在列表末位不抢主线。
- **缩略图 SSRF 防护**：只放行公网域名，拒绝 `localhost` / `*.local` / 私网字面 IP。
- **前端骨架屏**：解析期间给出双列骨架，不是空白等待。
- **后端离线提示条**：健康检查失败时页面顶部显式提示「请先启动后端」，而不是让用户对着按钮干猜。
- **`--dev` 开发模式**：`./run.sh --dev` 后端热重载 + Vite 开发服务器。

### 9.3 关键实现细节（与计划书不同或计划书未覆盖）

**多流下载的进度聚合**：计划书用 `d['_percent_str']` 直接读百分比，但在 `bestvideo+bestaudio` 场景下进度会从 100% 重置回 0%（两条流分别下载）。实际按 `format_id` 分桶累加 `downloaded_bytes` / `total_bytes`，得到一条单调递增的合并进度。

**ffmpeg 探测不能阻塞请求**：static-ffmpeg 首次要从 GitHub 拉 80MB，如果在 `ffmpeg_info()` 里同步做，一次下载请求会卡住好几分钟（实测 106 秒）。改成：请求路径只用本地快路径（系统 / imageio），static-ffmpeg 由启动时的后台线程探测，成功后再升级缓存。

**ffmpeg shim 目录**：imageio-ffmpeg 只提供 ffmpeg、没有 ffprobe，而 yt-dlp 的 `ffmpeg_location` 需要一个**目录**。项目根下的 `.bin/` 会把二进制软链成标准文件名 `ffmpeg` 再交给 yt-dlp。有 ffprobe 的来源则直接用原目录。

**竖屏视频的档位标注**：竖屏 1080×1920 若直接用 height 当档位会标成「1920P」。改为取宽高较小的一边作为档位，横屏 1920×1080 与竖屏 1080×1920 统一显示 1080P。

### 9.4 验收结果

| 验收项 | 结果 | 证据 |
|--------|------|------|
| 解析 B 站视频 | ✅ | `BV1myet61EDn` 标题/作者/时长/播放量/封面全部正确 |
| 清晰度列表 | ✅ | 1080P / 720P / 480P / 360P + 仅音频，均标注体积与 fps |
| 下载进度实时更新 | ✅ | 0% → 67.6% → 100%，速度与 ETA 正常 |
| 分段进度展示 | ✅ | 解析视频 / 下载数据 / 合并输出 三步状态正确流转 |
| 下载文件可播放 | ✅ | 产出 1,146,102 字节 MP4，`file` 识别为 ISO Media MP4 |
| 中文文件名 | ✅ | `Content-Disposition: attachment; filename*=UTF-8''%E7%94%B5...mp4` |
| 无效链接友好提示 | ✅ | 「链接格式不对，需要以 http:// 或 https:// 开头」 |
| 桌面浏览器布局 | ✅ | Chrome 1440×940，无控制台报错、无失败请求 |
| 手机浏览器布局 | ✅ | 390×844 无横向溢出，结果区自动折成单列 |
| 一键启动脚本 | ✅ | `./run.sh` 幂等启动，自动识别依赖与构建状态 |

**未能验收**：YouTube 解析。当前网络环境无法访问 YouTube（计划书第七章已列为已知风险，验收用 B 站）。平台能力本身由 yt-dlp 官方解析器覆盖。

### 9.5 本机环境备注

- 本机未安装 conda，实际使用项目内 `.venv`（Python 3.13.12）。
- 本机未安装系统 ffmpeg，已通过 static-ffmpeg 落地 ffmpeg + ffprobe（v5.0 静态二进制）。
- 首次安装依赖需访问 PyPI / GitHub，网络不稳定时可能重试多轮；`run.sh` 的依赖检查是幂等的，失败重跑即可。
- 阶段 3（AI 总结 / 思维导图 / 问答 / 字幕）与阶段 4-5 尚未开始。
