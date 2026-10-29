# 🚀 GoVid 快速部署指南

> 支持 B站、抖音、小红书、微博、YouTube 等 20+ 平台，完全免费部署！

## 📋 目录

1. [快速开始](#快速开始)（5 分钟）
2. [详细步骤](#详细步骤)
3. [故障排查](#故障排查)
4. [成本说明](#成本说明)

---

## 快速开始

### 第 1 步：部署后端

1. 注册 [Render](https://render.com/)（用 GitHub 登录，免费）
2. 点击 **New +** → **Blueprint**
3. 连接这个 GitHub 仓库
4. 点击 **Apply**
5. 等待 5 分钟，完成！

你会得到一个后端 URL：
```
https://govid-backend-xxxx.onrender.com
```

### 第 2 步：部署前端

```bash
cd frontend
npm install
npm run build

# 部署到 Cloudflare Pages（最快）
npm install -g wrangler
wrangler login
wrangler pages deploy dist --project-name=govid
```

或者部署到 Vercel（也很快）：

```bash
npm install -g vercel
vercel --prod
```

### 第 3 步：连接前后端

```bash
# 在 frontend 目录下
cp .env.production.example .env.production

# 编辑 .env.production，填入你的后端 URL
# VITE_API_BASE_URL=https://govid-backend-xxxx.onrender.com
```

重新构建并部署前端：

```bash
npm run build
wrangler pages deploy dist
```

### 第 4 步：测试

打开浏览器访问你的前端 URL，试试这些链接：

- **B 站**: `https://www.bilibili.com/video/BV1xx411c7mD`
- **抖音**: `https://v.douyin.com/iRNBho6G/`
- **小红书**: `https://www.xiaohongshu.com/explore/xxx`
- **微博**: `https://weibo.com/tv/show/xxx`

全都能解析！🎉

---

## 详细步骤

见 [QUICKSTART.md](QUICKSTART.md)

---

## 故障排查

### 后端构建失败

见 [RENDER_NOTES.md](RENDER_NOTES.md)

### 前端无法访问后端

检查：
1. 后端是否部署成功
2. `.env.production` 中的 URL 是否正确
3. 后端环境变量 `GOVID_CORS_ORIGINS` 是否设置为 `*`

---

## 成本说明

| 项目 | 平台 | 费用 |
|------|------|------|
| 后端 | Render Free | $0/月 |
| 前端 | Cloudflare Pages | $0/月 |
| 监控 | Uptime Robot | $0/月 |
| **总计** | | **$0/月** |

完全免费！🎉

---

## 进阶配置

### 防止后端休眠

使用 [Uptime Robot](https://uptimerobot.com/)（免费）每 5 分钟 ping 一次后端。

### 绑定自定义域名

- **Cloudflare Pages**: 在 Dashboard 添加 Custom Domain
- **Render**: 在 Settings 添加 Custom Domain

---

## 技术栈

- **后端**: FastAPI + yt-dlp + ffmpeg
- **前端**: Vue 3 + Vite
- **部署**: Render (后端) + Cloudflare Pages (前端)

---

## 支持的平台

✅ B 站 • 抖音 • 快手 • 小红书 • 微博  
✅ YouTube • TikTok • Instagram • Twitter  
✅ 20+ 其他平台

完整列表见：https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

---

## 许可证

MIT License

---

**部署遇到问题？** 提交 [GitHub Issue](https://github.com/tfrrx/govid/issues)

**想贡献代码？** 欢迎 [Pull Request](https://github.com/tfrrx/govid/pulls)
