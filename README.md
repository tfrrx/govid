# GoVid

全网视频下载工具，支持 1200+ 站点，多清晰度可选，原画质无水印输出。

## 功能特性

- **广泛支持** — 覆盖抖音、B 站、YouTube、快手、小红书等 1200+ 平台
- **多清晰度** — 自动解析所有可用画质，最高支持 4K
- **无水印直出** — 原画质输出，自动合并音视频
- **实时进度** — 下载进度可见，支持暂停与取消
- **隐私安全** — 不上传用户视频，临时文件自动清理

## 版本对比

### Full 版（完整版）

服务器下载后推送给用户，支持所有平台。

- ✅ 支持 1200+ 站点
- ✅ 无平台限制
- ⚠️ 需要服务器带宽

### Lite 版（轻量版）

浏览器直连 CDN 下载，零服务器流量。

- ✅ 零服务器流量
- ✅ 解析速度快
- ⚠️ 仅支持开放 CDN 平台（抖音、快手等）

## 技术栈

### 后端
- **Python 3.10+** — FastAPI + yt-dlp
- **FFmpeg** — 音视频合并（可选）

### 前端
- **Vue 3** — Composition API
- **Tailwind CSS** — 原子化样式
- **Vite** — 快速构建

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- FFmpeg（可选，用于高清合并）

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

服务运行在 `http://localhost:8000`

### 前端启动

**完整版：**

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`

**Lite 版：**

```bash
cd frontend-lite
npm install
npm run dev
```

访问 `http://localhost:5174`

## 部署

### Vercel（推荐）

**后端：**

```bash
cd backend
vercel --prod
```

**前端：**

```bash
cd frontend  # 或 frontend-lite
vercel --prod
```

### Docker

```bash
docker build -t govid .
docker run -p 8000:8000 govid
```

### 环境变量

后端 `.env` 配置：

```env
# Lite 模式（可选）
GOVID_MODE=lite

# 临时文件目录
GOVID_TMP_DIR=/tmp/govid

# 日志级别
LOG_LEVEL=INFO
```

前端 `.env` 配置：

```env
VITE_API_BASE_URL=https://your-api.vercel.app
```

## 项目结构

```
govid/
├── backend/              # 后端服务
│   ├── api/             # API 路由
│   ├── core/            # 核心逻辑
│   ├── extractors/      # 平台解析器
│   └── main.py          # 入口文件
├── frontend/            # 完整版前端
│   ├── src/
│   │   ├── components/  # Vue 组件
│   │   └── composables/ # 状态管理
│   └── package.json
├── frontend-lite/       # Lite 版前端
│   └── src/
└── README.md
```

## 开源协议

MIT License

---

**注意：** 本工具仅供学习交流，请遵守各平台服务条款，尊重版权。
