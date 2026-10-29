# GoVid 部署指南 - Render 免费层

> 🎉 **完全免费，支持所有平台**（B站、抖音、小红书、微博、YouTube 等）

## 快速开始

### 1. 注册 Render 账号

访问：https://render.com/

- ✅ 无需信用卡
- ✅ 使用 GitHub 账号登录即可

### 2. 部署后端

#### 方法 A：一键部署（推荐）

1. Fork 这个仓库到你的 GitHub
2. 访问：https://dashboard.render.com/
3. 点击 **New +** → **Web Service**
4. 选择你 Fork 的仓库：`govid`
5. 配置：
   - **Name**: `govid-backend`（或任意名字）
   - **Runtime**: `Docker`
   - **Instance Type**: `Free`
6. 点击 **Create Web Service**

等待 3-5 分钟，Render 会自动：
- 拉取代码
- 构建 Docker 镜像
- 安装 ffmpeg + Python + yt-dlp
- 启动服务

部署完成后，你会得到一个 URL：
```
https://govid-backend-xxxx.onrender.com
```

#### 方法 B：使用 Blueprint（推荐）

1. 在 Render Dashboard 点击 **New +** → **Blueprint**
2. 连接你的 GitHub 仓库
3. Render 会自动读取 `render.yaml` 配置
4. 点击 **Apply**，完成！

### 3. 测试后端

打开浏览器访问：
```
https://你的部署地址.onrender.com/api/health
```

应该返回：
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### 4. 部署前端

#### 方法 A：Cloudflare Pages（推荐，快速）

```bash
cd frontend
npm install
npm run build

# 安装 Cloudflare CLI
npm install -g wrangler

# 登录
wrangler login

# 部署
wrangler pages deploy dist --project-name=govid
```

#### 方法 B：Vercel（也很快）

```bash
cd frontend
npm install

# 安装 Vercel CLI
npm install -g vercel

# 登录并部署
vercel --prod
```

#### 方法 C：Render 静态网站

1. Render Dashboard → **New +** → **Static Site**
2. 选择仓库
3. 配置：
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
4. 部署！

### 5. 连接前后端

编辑 `frontend/.env.production`：

```bash
VITE_API_BASE_URL=https://你的后端地址.onrender.com
```

重新构建并部署前端。

---

## 免费层限制

### Render 免费 Web Service

✅ **优点**：
- 每月 750 小时免费（够用）
- 支持 Docker（可以装 ffmpeg + yt-dlp）
- 支持所有平台
- 自动 HTTPS

⚠️ **注意**：
- 15 分钟无请求会休眠
- 首次唤醒需要 30-60 秒（用户需要等一下）
- 512MB RAM（够用）

### 如何避免休眠？

可以用 **Uptime Robot** 免费监控，每 5 分钟 ping 一次：

1. 注册：https://uptimerobot.com/
2. 添加监控：
   - **Monitor Type**: HTTP(s)
   - **URL**: `https://你的后端地址.onrender.com/api/health`
   - **Monitoring Interval**: 5 minutes
3. 保存，完成！

这样后端就不会休眠了。

---

## 测试所有平台

### 测试 B 站

```bash
curl "https://你的后端地址.onrender.com/api/parse?url=https://www.bilibili.com/video/BV1xx411c7mD"
```

### 测试抖音

```bash
curl "https://你的后端地址.onrender.com/api/parse?url=https://v.douyin.com/iRNBho6G/"
```

### 测试小红书

```bash
curl "https://你的后端地址.onrender.com/api/parse?url=https://www.xiaohongshu.com/explore/xxx"
```

### 测试微博

```bash
curl "https://你的后端地址.onrender.com/api/parse?url=https://weibo.com/tv/show/xxx"
```

所有平台都能解析！

---

## 故障排查

### 1. 部署失败："Out of Memory"

**原因**：构建时内存不够。

**解决**：在 `Dockerfile` 中优化：

```dockerfile
# 分阶段安装依赖
RUN pip install --no-cache-dir fastapi uvicorn
RUN pip install --no-cache-dir yt-dlp[default]
```

### 2. 抖音解析失败

**原因**：Playwright 浏览器未安装。

**解决**：确保 `Dockerfile` 中有：

```dockerfile
RUN playwright install chromium
RUN playwright install-deps
```

### 3. 首次访问很慢

**原因**：服务休眠了。

**解决**：使用 Uptime Robot 保持唤醒（见上文）。

### 4. ffmpeg 找不到

**原因**：未安装 ffmpeg。

**解决**：确保 `Dockerfile` 中有：

```dockerfile
RUN apt-get install -y ffmpeg
```

---

## 成本估算

| 服务 | 平台 | 月费用 |
|------|------|--------|
| 后端 API | Render Free | **$0** |
| 前端 | Cloudflare Pages | **$0** |
| 监控（防休眠） | Uptime Robot | **$0** |
| **总计** | | **$0** |

完全免费！🎉

---

## 限制与注意事项

### ⚠️ 不要滥用

- 免费层有 CPU 时间限制
- 不要用于商业用途
- 不要短时间内大量请求

### ⚠️ 数据不持久

- `/tmp/downloads/` 每次重启会清空
- 不要存储重要文件

### ⚠️ IP 限制

虽然 Render 的 IP 比 Cloudflare Workers 好，但仍可能被部分平台限流。

---

## 升级到付费层（可选）

如果免费层不够用，可以升级：

- **Render Starter**: $7/月，不会休眠
- **Railway**: $5/月免费额度
- **Fly.io**: 类似限制

但对于个人使用，免费层完全够用！

---

## 下一步

- [ ] 部署后端到 Render
- [ ] 部署前端到 Cloudflare Pages
- [ ] 设置 Uptime Robot 防止休眠
- [ ] 测试所有平台
- [ ] 分享给朋友！

---

**创建时间**：2026-10-29  
**作者**：Claude Opus 5.5
