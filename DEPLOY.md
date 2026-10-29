# GoVid 双模式部署指南

## 模式选择

### Lite 模式（纯 CDN 版）
- ✅ **免费部署到 Vercel / Netlify**
- ✅ 只解析视频返回直链，不下载文件
- ⚠️ 只支持抖音、快手等开放 CDN 平台
- ❌ B 站 / YouTube / Twitter 暂不支持

### Full 模式（完整版）
- ✅ 支持所有平台（流式代理 + 本地下载）
- ⚠️ 需要服务器（推荐 Railway 免费版或轻量云服务器）
- ⚠️ 需要带宽和磁盘空间

---

## 部署方式 1：Lite 模式（免费 Serverless）

### Vercel 部署（推荐）

```bash
# 1. 安装 Vercel CLI
npm i -g vercel

# 2. 构建前端（Lite 版）
cd frontend
npm install
npm run build -- --mode production.lite

# 3. 部署到 Vercel
cd ..
vercel --prod
```

**环境变量配置**：
```bash
# Vercel 项目设置 → Environment Variables
GOVID_MODE=lite
PYTHONPATH=backend
```

**免费额度**：
- 100GB 流量/月
- 10 万次请求/月
- 对于纯解析场景，可服务 5000-10000 日活

### Netlify 部署（备选）

```bash
# 1. 构建前端
cd frontend && npm run build -- --mode production.lite

# 2. 创建 netlify.toml
cat > netlify.toml << 'EOF'
[build]
  command = "cd frontend && npm install && npm run build -- --mode production.lite"
  publish = "frontend/dist"

[functions]
  directory = "backend"

[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200
EOF

# 3. 部署
netlify deploy --prod
```

---

## 部署方式 2：Full 模式（服务器部署）

### Railway 免费版（推荐新手）

**Railway 免费额度**：
- $5 美金免费额度/月（约 500 小时运行时间）
- 500MB 内存 + 1GB 磁盘
- 适合日活 < 200 人

```bash
# 1. 安装 Railway CLI
npm i -g @railway/cli

# 2. 登录
railway login

# 3. 初始化项目
railway init

# 4. 部署
railway up
```

**环境变量**：
```bash
GOVID_MODE=full
DOWNLOAD_DIR=/tmp/govid
MAX_CONCURRENT_DOWNLOADS=2
TASK_TTL_HOURS=1
MAX_TMP_GB=0.8
```

### Docker Compose 部署（轻量服务器）

```yaml
# docker-compose.yml

version: '3.8'

services:
  govid:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOVID_MODE=full
      - DOWNLOAD_DIR=/tmp/govid
      - MAX_CONCURRENT_DOWNLOADS=4
      - TASK_TTL_HOURS=2
    volumes:
      - /tmp/govid:/tmp/govid
    restart: unless-stopped
```

```bash
# 部署
docker-compose up -d

# 配置 Nginx 反向代理
sudo apt install nginx
sudo nano /etc/nginx/sites-available/govid

# 配置内容见下方 nginx.conf
```

---

## 免费资源组合方案

### 方案 A：纯免费（适合验证 MVP）
- **前端 + API**：Vercel Lite 模式（免费）
- **支持平台**：抖音、快手
- **日活上限**：5000-10000 人
- **成本**：¥0/月

### 方案 B：Railway 托底（适合初创）
- **前端**：Vercel Lite 模式（免费）
- **后端**：Railway Full 模式（$5/月免费额度）
- **支持平台**：所有平台
- **日活上限**：200-500 人
- **成本**：¥0/月（免费额度内）

### 方案 C：学生优惠（适合长期运营）
- **服务器**：阿里云学生机（¥9/月，1C2G + 1Mbps）
- **CDN**：腾讯云学生 CDN（50GB/月免费）
- **支持平台**：所有平台
- **日活上限**：500-1000 人
- **成本**：¥9-19/月

---

## 前端构建命令

```json
// package.json
{
  "scripts": {
    "build": "vite build",
    "build:lite": "vite build --mode production.lite",
    "build:full": "vite build --mode production"
  }
}
```

---

## 切换模式

### 从 Lite 升级到 Full

```bash
# 1. 在 Vercel 项目设置中修改环境变量
GOVID_MODE=full

# 2. 重新部署（触发自动构建）
git commit -m "chore: 升级到 Full 模式"
git push origin main
```

### 同时运行两个版本

```bash
# Lite 版：部署到 govid-lite.vercel.app
vercel --prod --name govid-lite

# Full 版：部署到 Railway
railway up --name govid-full
```

---

## 成本估算

| 日活用户 | 推荐方案 | 月成本 |
|---------|---------|--------|
| < 500   | Vercel Lite | ¥0 |
| 500-1000 | Railway Full | ¥0-30 |
| 1000-5000 | 阿里云学生机 | ¥9-19 |
| 5000-10000 | 轻量服务器 | ¥150-300 |

## 监控与报警

```bash
# Vercel Analytics（免费）
# 自动统计：请求量、响应时间、错误率

# Railway Metrics（免费）
# 监控：CPU、内存、磁盘使用率

# 自定义报警（可选）
# 用 Sentry 监控错误（免费额度：5000 事件/月）
```
