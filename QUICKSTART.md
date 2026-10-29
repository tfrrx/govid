# GoVid 一键部署指南

## 🚀 5 分钟部署到 Render（完全免费）

### 步骤 1：准备代码

```bash
# 确保所有改动已提交
git add .
git commit -m "准备部署到 Render"
git push origin main
```

### 步骤 2：注册 Render

1. 访问：https://render.com/
2. 点击右上角 **Get Started**
3. 用 GitHub 账号登录（无需信用卡）

### 步骤 3：部署后端

#### 方法 A：使用 Blueprint（最简单，推荐）

1. 在 Render Dashboard 点击 **New +**
2. 选择 **Blueprint**
3. 连接你的 GitHub 仓库（`govid`）
4. Render 会自动检测到 `render.yaml`
5. 点击 **Apply**
6. 等待 3-5 分钟，完成！

#### 方法 B：手动创建 Web Service

1. 点击 **New +** → **Web Service**
2. 连接你的 GitHub 仓库
3. 配置：
   - **Name**: `govid-backend`
   - **Region**: 选离你最近的（Singapore 对国内用户最快）
   - **Branch**: `main`
   - **Runtime**: `Docker`
   - **Instance Type**: `Free`
4. 点击 **Create Web Service**

### 步骤 4：获取后端 URL

部署完成后，Render 会给你一个 URL，类似：

```
https://govid-backend-xxxx.onrender.com
```

复制这个 URL！

### 步骤 5：部署前端到 Cloudflare Pages

```bash
# 进入前端目录
cd frontend

# 创建生产环境配置
cp .env.production.example .env.production

# 编辑 .env.production，替换后端 URL
# VITE_API_BASE_URL=https://govid-backend-xxxx.onrender.com

# 安装依赖
npm install

# 构建
npm run build

# 安装 Wrangler CLI
npm install -g wrangler

# 登录 Cloudflare（会打开浏览器）
wrangler login

# 部署到 Cloudflare Pages
wrangler pages deploy dist --project-name=govid-frontend
```

部署完成后，你会得到前端 URL：

```
https://govid-frontend.pages.dev
```

### 步骤 6：测试

打开浏览器访问你的前端 URL，测试：

1. **抖音视频**：
   ```
   https://v.douyin.com/iRNBho6G/
   ```

2. **B 站视频**：
   ```
   https://www.bilibili.com/video/BV1xx411c7mD
   ```

3. **小红书笔记**：
   ```
   https://www.xiaohongshu.com/explore/xxx
   ```

所有平台都能解析！🎉

---

## 🔧 进阶配置

### 防止后端休眠（推荐）

Render 免费层会在 15 分钟无请求后休眠。使用 **Uptime Robot** 保持唤醒：

1. 注册：https://uptimerobot.com/（免费）
2. 添加监控：
   - **Monitor Type**: HTTP(s)
   - **URL**: `https://你的后端地址.onrender.com/api/health`
   - **Monitoring Interval**: 5 minutes
3. 保存，后端就不会休眠了！

### 绑定自定义域名（可选）

#### 前端（Cloudflare Pages）

1. 在 Cloudflare Pages Dashboard 点击你的项目
2. **Custom domains** → **Set up a custom domain**
3. 输入你的域名（例如 `govid.yourdomain.com`）
4. 按照提示添加 CNAME 记录

#### 后端（Render）

1. 在 Render Dashboard 点击你的服务
2. **Settings** → **Custom Domain**
3. 输入域名（例如 `api.yourdomain.com`）
4. 添加 CNAME 记录到：`govid-backend-xxxx.onrender.com`

### 查看日志

在 Render Dashboard：

1. 点击你的服务
2. 点击 **Logs** 标签
3. 实时查看运行日志

---

## 📊 成本估算

| 项目 | 平台 | 费用 |
|------|------|------|
| 后端 API | Render Free | **$0** |
| 前端 | Cloudflare Pages | **$0** |
| 防休眠监控 | Uptime Robot | **$0** |
| **总计** | | **$0/月** |

完全免费！🎉

---

## ⚠️ 限制说明

### Render 免费层

- ✅ 每月 750 小时运行时间
- ✅ 支持 Docker（可以装 ffmpeg + yt-dlp）
- ✅ 512MB RAM（够用）
- ⚠️ 15 分钟无请求会休眠
- ⚠️ 首次唤醒需要 30-60 秒

### 如何优化用户体验？

1. **防止休眠**：用 Uptime Robot 每 5 分钟 ping 一次
2. **加载提示**：前端显示"后端正在唤醒，请稍候..."
3. **缓存结果**：相同视频链接缓存解析结果

---

## 🐛 故障排查

### 1. 部署失败："Out of Memory"

**解决**：在 Render Dashboard 的 Build Command 中添加：

```bash
docker build --memory=1g -t govid .
```

### 2. 前端访问后端报 CORS 错误

**检查**：
1. 后端环境变量 `GOVID_CORS_ORIGINS` 是否设置为 `*`
2. 前端 `.env.production` 中的后端 URL 是否正确

**解决**：在 Render Dashboard → **Environment** 添加：

```
GOVID_CORS_ORIGINS=*
```

### 3. 抖音解析失败

**原因**：Playwright 浏览器未安装。

**检查日志**：在 Render Logs 中搜索 `playwright`

**解决**：确保 `Dockerfile` 中有：

```dockerfile
RUN playwright install-deps
```

### 4. ffmpeg 找不到

**检查**：访问 `https://你的后端地址.onrender.com/api/health`

应该返回：

```json
{
  "status": "ok",
  "version": "1.0.0",
  "ffmpeg_available": true
}
```

如果 `ffmpeg_available` 为 `false`，说明 ffmpeg 未安装。

---

## 🎯 下一步

- [ ] 部署后端到 Render
- [ ] 部署前端到 Cloudflare Pages
- [ ] 设置 Uptime Robot 防止休眠
- [ ] 测试所有平台（B站、抖音、小红书、微博）
- [ ] （可选）绑定自定义域名
- [ ] 分享给朋友使用！

---

## 📞 需要帮助？

- Render 文档：https://docs.render.com/
- Cloudflare Pages 文档：https://developers.cloudflare.com/pages/
- 项目问题：提交 GitHub Issue

---

**创建时间**：2026-10-29  
**作者**：Claude Opus 5.5

祝部署顺利！🚀
