# 🚀 Render 部署修复指南

## 问题修复清单

### ✅ 已修复的问题

1. **CORS 代理失效** - 后端现在有自己的 `/api/cors-proxy` 接口
2. **抖音解析失败** - Dockerfile 现在会安装 Chromium 浏览器
3. **B 站解析成功但下载失败** - 配置已更新为使用后端自己的代理

## 🔧 部署步骤

### 1. 提交代码到 GitHub

```bash
git add .
git commit -m "fix: 修复 Render 部署的 CORS 代理和浏览器配置"
git push origin main
```

### 2. 在 Render 控制台更新环境变量

访问：https://dashboard.render.com/web/你的服务ID/env

添加/修改环境变量：

```
GOVID_CORS_PROXY_URL=https://govid-hqln.onrender.com/api/cors-proxy
```

**注意**：把 `govid-hqln` 改成你的实际服务名！

### 3. 手动触发重新部署

- 方式 A：在 Render 控制台点击 "Manual Deploy" → "Deploy latest commit"
- 方式 B：推送新的 commit 自动触发

### 4. 等待部署完成（约 5-10 分钟）

部署过程中会：
- 安装 Chromium 浏览器（抖音需要）
- 安装 ffmpeg（视频合并）
- 启动新的后端服务

### 5. 测试功能

访问：https://你的后端地址.onrender.com

测试各平台：
- ✅ **抖音**：需要浏览器，现在会用系统 Chromium
- ✅ **B 站**：使用后端 CORS 代理
- ✅ **YouTube**：使用 yt-dlp
- ✅ **小红书、快手**：使用 yt-dlp

## 🐛 如果还是不行

### 抖音仍然报错 "没有浏览器"

**原因**：Render 免费层内存只有 512MB，Chromium 可能启动失败

**解决方案 A**：检查后端日志，看是否有内存不足错误

```bash
# 在 Render 控制台查看 Logs
```

**解决方案 B**：禁用抖音的浏览器模式

修改 `backend/extractors/douyin/browser.py:95`，让它直接抛出异常跳过浏览器：

```python
def get_browser_page():
    raise RuntimeError("Render 免费层内存不足，无法运行浏览器")
```

### B 站直连下载仍然失败

检查 CORS 代理是否生效：

```bash
curl https://你的后端.onrender.com/api/cors-proxy?url=https://www.bilibili.com/
```

应该返回 B 站首页 HTML，而不是 CORS 错误。

### 服务器下载报 "内部错误"

查看后端日志，找到具体错误信息：

```bash
# Render 控制台 → Logs → 搜索 "ERROR"
```

可能原因：
- `/tmp/downloads` 目录权限问题
- yt-dlp 下载超时（Render 免费层带宽有限）
- 某个平台需要 cookies（需要手动配置 `GOVID_COOKIES_FILE`）

## 📊 预期效果

修复后：

| 平台 | 解析方式 | 下载方式 | 状态 |
|------|----------|----------|------|
| 抖音 | Chromium | CORS 代理 | ⚠️ 内存受限 |
| 快手 | yt-dlp | 服务器流 | ✅ |
| B 站 | yt-dlp | CORS 代理 | ✅ |
| YouTube | yt-dlp | 服务器流 | ✅ |
| 小红书 | yt-dlp | 服务器流 | ✅ |
| 微博 | yt-dlp | 服务器流 | ✅ |

## 💡 长期建议

如果抖音在 Render 上始终不稳定，有两个选择：

1. **只在前端支持抖音**：用你的 `frontend-lite` 纯前端方案
2. **升级到 Railway**：有更多内存，Chromium 能稳定运行

---

## 🎯 下一步

部署成功后，更新前端的 API 地址：

```bash
# 在 frontend/.env.production 中
VITE_API_BASE_URL=https://你的后端.onrender.com/api
```

然后重新部署前端到 Vercel。
