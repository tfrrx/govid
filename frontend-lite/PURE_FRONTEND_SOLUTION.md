# GoVid Lite 纯前端方案 — 支持 B 站、YouTube 等更多平台

> 🎯 **目标**：让 Lite 版通过纯前端 + Cloudflare Workers，支持 B 站、YouTube 等需要 Headers 的平台

---

## 核心问题与解决方案

### 问题
- **抖音**：CDN 完全开放 ✅ **已支持**，浏览器直接下载
- **B 站 / YouTube**：需要特定 Referer / Cookie，浏览器 CORS 阻止
- **小红书 / 微博**：需要登录态 Cookie，CORS + 鉴权双重限制

### 三种可行方案

| 方案 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| **A. Cloudflare Workers CORS 代理** | 零服务器成本，每天 10 万次免费请求 | 需要部署 Worker | ✅ **最推荐** |
| **B. 浏览器扩展** | 绕过 CORS，支持所有平台 | 需要用户安装扩展 | 高级用户 |
| **C. 第三方 API** | 开箱即用 | 依赖第三方，可能收费或失效 | 快速验证 |

---

## 方案 A：Cloudflare Workers CORS 代理（推荐）

### 架构图

```
用户浏览器
    ↓ 1. 输入视频链接
GoVid Lite 前端（Cloudflare Pages）
    ↓ 2. 解析视频信息（调用你的后端 API）
    ← 3. 返回直链 + 需要的 Headers
用户浏览器
    ↓ 4. 请求 Cloudflare Worker（带上 Headers）
Cloudflare Worker（CORS 代理）
    ↓ 5. 转发到 B 站 / YouTube CDN（注入 Referer）
B 站 / YouTube CDN
    ← 6. 返回视频流
Cloudflare Worker
    ← 7. 添加 CORS 头，返回给浏览器
用户浏览器下载完成 ✅
```

### 为什么选 Cloudflare Workers？

1. **完全免费**：
   - 每天 10 万次请求免费
   - 无需信用卡即可使用
   - 全球 CDN 加速

2. **零服务器成本**：
   - 不占用你的服务器带宽
   - 不需要维护服务器
   - 自动扩容

3. **部署简单**：
   - 一个 JS 文件搞定
   - 5 分钟部署完成

---

## 实现步骤

### 第 1 步：创建 Cloudflare Worker（CORS 代理）

创建 `workers/cors-proxy.js`：

```javascript
// Cloudflare Worker - CORS 代理
// 支持 B 站、YouTube 等需要特定 Headers 的平台

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // 从 URL 参数获取目标视频链接
    const targetUrl = url.searchParams.get('url');
    if (!targetUrl) {
      return new Response('Missing url parameter', { status: 400 });
    }

    try {
      // 解析目标平台
      const target = new URL(targetUrl);
      const headers = new Headers();

      // 根据平台注入必需的 Headers
      if (target.hostname.includes('bilibili')) {
        headers.set('Referer', 'https://www.bilibili.com/');
        headers.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
      } else if (target.hostname.includes('youtube') || target.hostname.includes('googlevideo')) {
        headers.set('Referer', 'https://www.youtube.com/');
        headers.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
      }

      // 转发请求到目标 CDN
      const response = await fetch(targetUrl, {
        method: request.method,
        headers: headers,
      });

      // 复制响应并添加 CORS 头
      const newResponse = new Response(response.body, response);
      newResponse.headers.set('Access-Control-Allow-Origin', '*');
      newResponse.headers.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
      newResponse.headers.set('Access-Control-Allow-Headers', '*');

      return newResponse;

    } catch (error) {
      return new Response(`Proxy error: ${error.message}`, { 
        status: 500,
        headers: {
          'Access-Control-Allow-Origin': '*',
        }
      });
    }
  }
};
```

**部署命令**（在项目根目录）：

```bash
# 安装 Wrangler CLI
npm install -g wrangler

# 登录 Cloudflare
wrangler login

# 部署 Worker
wrangler deploy workers/cors-proxy.js --name govid-cors-proxy
```

部署后你会得到一个地址：`https://govid-cors-proxy.你的账号.workers.dev`

---

### 第 2 步：后端返回代理链接

修改 `backend/api/video.py`：

```python
@router.get("/parse")
async def api_parse_video(url: str) -> dict:
    """解析视频信息，返回代理链接"""
    
    # 解析视频
    video_info = parse_video(url)
    
    # 判断是否需要 CORS 代理
    extractor = video_info.get("extractor", "").lower()
    
    if extractor in ["bilibili", "youtube"]:
        # B 站 / YouTube 需要 CORS 代理
        proxy_base = "https://govid-cors-proxy.你的账号.workers.dev"
        
        for format_item in video_info.get("formats", []):
            original_url = format_item["url"]
            # 包装成代理链接
            format_item["url"] = f"{proxy_base}?url={urllib.parse.quote(original_url)}"
            format_item["requires_proxy"] = True
    
    return video_info
```

---

### 第 3 步：前端直接下载

`frontend-lite/src/api/video.js` **不需要改**，后端返回的 URL 已经是代理链接了。

用户点击下载按钮：
```javascript
// 后端返回的 URL 已经是代理链接
// https://govid-cors-proxy.xxx.workers.dev?url=https://xxx.bilivideo.com/xxx.m4s

window.location.href = proxyUrl;  // 浏览器直接下载 ✅
```

---

## 方案 B：浏览器扩展（备选）

如果你想做一个**浏览器扩展版本**，可以参考这些现成的实现：

### 推荐项目

1. **[Downr](https://github.com/downr/downr)** 
   - 支持 YouTube、Bilibili、抖音等 **30+ 平台**
   - 纯浏览器实现，无需服务器
   - 有 Chrome 扩展版本

2. **[madkarmaa/youtube-downloader](https://github.com/madkarmaa/youtube-downloader)**
   - Tampermonkey 油猴脚本
   - 支持 YouTube / YouTube Shorts / YouTube Music
   - 一键下载，支持音频提取

### 实现方式

创建 `chrome-extension/manifest.json`：

```json
{
  "manifest_version": 3,
  "name": "GoVid Lite Extension",
  "version": "1.0.0",
  "permissions": [
    "webRequest",
    "webRequestBlocking",
    "*://*.bilibili.com/*",
    "*://*.youtube.com/*"
  ],
  "background": {
    "service_worker": "background.js"
  }
}
```

`chrome-extension/background.js`：

```javascript
// 拦截请求，注入 Headers
chrome.webRequest.onBeforeSendHeaders.addListener(
  function(details) {
    const headers = details.requestHeaders;
    
    if (details.url.includes('bilivideo.com')) {
      headers.push({ name: 'Referer', value: 'https://www.bilibili.com/' });
    }
    
    return { requestHeaders: headers };
  },
  { urls: ["<all_urls>"] },
  ["blocking", "requestHeaders"]
);
```

**优势**：
- 支持所有平台（包括需要登录的）
- 无需 CORS 代理
- 用户隐私更好

**劣势**：
- 需要用户安装扩展（额外步骤）
- Chrome Web Store 审核较严格

---

## 方案 C：第三方 API（最快）

如果只是快速验证，可以用现成的第三方解析 API：

### 推荐服务

1. **[Cobalt API](https://cobalt.tools/)**
   - 开源免费
   - 支持 YouTube、Bilibili、抖音等
   - API: `https://api.cobalt.tools/api/json`

2. **你自己的后端 + yt-dlp**（已有）
   - 最稳定，完全可控
   - 但需要服务器流量

---

## 成本对比

| 方案 | 初始成本 | 月度成本 | 用户量 1000 | 用户量 10000 |
|------|----------|----------|-------------|--------------|
| **Cloudflare Workers** | 0 元 | 0 元 | 0 元（10万次/天） | 0 元 |
| **你的后端服务器** | 0 元 | 50 元 | 200 元 | 2000 元+ |
| **浏览器扩展** | 0 元 | 0 元 | 0 元 | 0 元 |
| **第三方 API** | 0 元 | 0-100 元 | 可能限流 | 可能收费 |

---

## 推荐实施路径

### 阶段 1：Cloudflare Workers 代理（本周）

1. ✅ 部署 Workers CORS 代理（5 分钟）
2. ✅ 后端返回代理链接（10 分钟）
3. ✅ 测试 B 站 / YouTube 下载

**预期效果**：
- Lite 版支持 B 站、YouTube
- 零额外服务器成本
- 用户体验与抖音一致（直接下载）

### 阶段 2：浏览器扩展（下个月）

1. 开发 Chrome Extension
2. 发布到 Chrome Web Store
3. 宣传「无需后端」的扩展版

**预期效果**：
- 支持所有平台（包括需要登录的）
- 完全零成本运行
- 吸引技术用户

---

## 参考资源

### 开源项目
- [Downr](https://github.com/downr/downr) - 支持 30+ 平台的纯前端下载器
- [stream-proxy-worker](https://github.com/Danushka-Madushan/stream-proxy-worker) - Cloudflare Workers 流式代理
- [u2worker](https://github.com/suconghou/u2worker) - YouTube 专用 Worker 代理

### 官方文档
- [Cloudflare Workers CORS Proxy](https://developers.cloudflare.com/workers/examples/cors-header-proxy/)
- [Building CORS Proxy Tutorial](https://rednafi.com/javascript/cors-proxy-with-cloudflare-workers/)

### 社区方案
- [YouTube Worker 下载 Gist](https://gist.github.com/hizkifw/ae229eb0c5ff809fc2a4a88735bfd604)
- [CORS Proxy with WebSocket](https://gist.github.com/mkornatz/d7daca0203260340ffff7e85399a48db)

---

## 总结

✅ **推荐方案 A**：Cloudflare Workers CORS 代理
- 零成本，无需维护服务器
- 5 分钟部署完成
- 支持 B 站、YouTube 等主流平台

🔧 **备选方案 B**：浏览器扩展
- 适合技术用户
- 支持所有平台
- 完全无后端

🚀 **快速验证**：第三方 API
- 最快上线
- 但依赖第三方稳定性

---

**想试试吗？我可以直接帮你：**
1. 写好 Cloudflare Worker 代码
2. 修改后端返回代理链接
3. 部署并测试 B 站 / YouTube 下载

你只需要一个 Cloudflare 账号（免费注册）！
