# GoVid 直连架构部署计划

## 🎯 目标

实现用户关机后仍可使用的零服务器流量架构：
- 抖音：浏览器直连 CDN（已实现）
- B 站 / YouTube：通过 Vercel Edge Function 代理（解决 CORS 和 Referer 限制）
- 其他平台：保留传统下载方式（占比 <10%）

## 📊 当前状态

✅ **已完成**
- Vercel 账号登录成功（`tftrxhan-3090`）
- CORS 代理代码已创建（`vercel-proxy/api/cors-proxy.js`）
- Cloudflare Worker 已部署（作为备用方案）

⏳ **待完成**
1. 部署 Vercel Edge Function
2. 测试代理功能
3. 更新后端配置
4. 前端适配新的下载方式
5. 验证完整流程

## 🚀 部署步骤（详细版）

### 第 1 步：部署到 Vercel

#### 1.1 运行部署命令

```bash
cd /Users/happy/Project/Python_VideoDownlaoder/govid/vercel-proxy
vercel --prod
```

#### 1.2 部署过程中的问题

第一次部署会问几个问题：

**Q: Set up and deploy "vercel-proxy"?**  
→ **回答：Y**

**Q: Which scope do you want to deploy to?**  
→ **选择：tftrxhan-3090**（你的账号）

**Q: Link to existing project?**  
→ **回答：N**（这是新项目）

**Q: What's your project's name?**  
→ **回答：govid-cors-proxy**（或直接回车用默认名）

**Q: In which directory is your code located?**  
→ **回答：./**（当前目录）

#### 1.3 部署完成

会看到类似输出：

```
✅ Production: https://govid-cors-proxy-xxx.vercel.app [复制此 URL]
```

**重要：记下这个 URL！** 后续配置需要用到。

---

### 第 2 步：测试 Vercel 代理

#### 2.1 健康检查

```bash
curl https://你的部署地址.vercel.app/api/cors-proxy
```

预期返回：

```json
{
  "name": "GoVid CORS Proxy (Vercel)",
  "status": "online",
  "usage": "Add ?url=YOUR_VIDEO_URL",
  "example": "..."
}
```

#### 2.2 测试 B 站视频代理

```bash
# 用一个真实的 B 站视频链接测试（需要先通过 yt-dlp 获取真实 CDN 链接）
curl -I "https://你的部署地址.vercel.app/api/cors-proxy?url=https://upos-sz-xxx.bilivideo.com/xxx.m4s"
```

预期：返回 200 或 206 状态码，且包含 `Access-Control-Allow-Origin: *` 响应头。

---

### 第 3 步：更新后端配置

#### 3.1 修改 `backend/config.py`

在 `Settings` 类中添加 CORS 代理 URL 配置：

```python
class Settings(BaseSettings):
    # ... 其他配置 ...
    
    # CORS 代理（用于前端直连需要特殊 Headers 的平台）
    cors_proxy_url: str = os.getenv(
        "GOVID_CORS_PROXY_URL",
        "https://你的部署地址.vercel.app/api/cors-proxy"
    )
```

#### 3.2 修改 `backend/core/media.py`

找到 `resolve_cors_proxy_link` 函数中的 Worker URL（约第 464 行和 485 行），替换：

```python
# 原来
worker_base = "https://govid-cors-proxy.tftrxhan.workers.dev"

# 改成
from backend.config import settings
worker_base = settings.cors_proxy_url
```

或者直接全局替换：

```bash
cd /Users/happy/Project/Python_VideoDownlaoder/govid/backend
grep -r "govid-cors-proxy.tftrxhan.workers.dev" . | cut -d: -f1 | uniq
# 然后手动编辑这些文件，替换成你的 Vercel URL
```

#### 3.3 修改 `backend/api/video.py`

如果 `api_cors_proxy` 接口中也硬编码了 Worker URL，同样替换。

---

### 第 4 步：前端适配

#### 4.1 检查前端 API 调用

检查 `frontend/src/api/video.js` 中是否有硬编码的 Worker URL。

#### 4.2 更新下载逻辑

确保前端调用 `/api/cors-proxy` 接口获取代理链接，而不是直接请求 Worker。

---

### 第 5 步：完整流程验证

#### 5.1 启动后端

```bash
cd /Users/happy/Project/Python_VideoDownlaoder/govid/backend
uvicorn main:app --reload
```

#### 5.2 启动前端

```bash
cd /Users/happy/Project/Python_VideoDownlaoder/govid/frontend
npm run dev
```

#### 5.3 测试完整流程

1. **测试抖音直连**
   - 输入抖音视频链接
   - 点击解析
   - 点击"直连下载"
   - 验证：浏览器直接从抖音 CDN 下载，不经过 govid 服务器

2. **测试 B 站 CORS 代理**
   - 输入 B 站视频链接
   - 点击解析
   - 点击"CORS 代理下载"（如果有此按钮）
   - 验证：浏览器通过 Vercel 代理下载，govid 服务器只返回代理链接

3. **测试其他平台**
   - 输入 YouTube / 小红书 / 微博链接
   - 验证现有下载方式仍然正常工作

---

## 📝 配置文件清单

需要修改的文件：

1. ✅ `vercel-proxy/api/cors-proxy.js` — 已创建
2. ✅ `vercel-proxy/vercel.json` — 已创建
3. ⏳ `backend/config.py` — 需添加 `cors_proxy_url` 配置
4. ⏳ `backend/core/media.py` — 替换 Worker URL（2 处）
5. ⏳ `backend/api/video.py` — 检查并替换（如果有）
6. ⏳ `frontend/src/api/video.js` — 检查前端配置

---

## 🔧 环境变量配置（可选）

如果你想通过环境变量配置 CORS 代理 URL：

```bash
# .env 文件
GOVID_CORS_PROXY_URL=https://你的部署地址.vercel.app/api/cors-proxy
```

---

## 🐛 故障排查

### 问题 1：部署失败 "Invalid vercel.json"

**原因**：配置文件格式错误。

**解决**：检查 `vercel.json` 是否为标准 JSON 格式：

```json
{
  "version": 2,
  "name": "govid-cors-proxy"
}
```

### 问题 2：代理返回 502 错误

**原因**：Edge Function 代码有错误。

**解决**：
1. 访问 Vercel Dashboard 查看日志
2. 或运行 `vercel logs` 查看实时日志

### 问题 3：CORS 错误仍然存在

**原因**：响应头未正确设置。

**解决**：确认 Edge Function 返回的响应包含：

```javascript
'Access-Control-Allow-Origin': '*'
'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS'
'Access-Control-Expose-Headers': '*'
```

### 问题 4：B 站视频无法播放

**原因**：缺少 Referer 请求头。

**解决**：检查代理代码中是否正确设置了：

```javascript
if (target.hostname.includes('bilibili')) {
  headers.set('Referer', 'https://www.bilibili.com/')
}
```

---

## 📈 预期效果

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| **服务器下载流量** | 100% | ~10%（只有 Twitter 等少数平台） |
| **服务器上传流量** | 100% | 0%（用户直连 CDN） |
| **磁盘占用** | 视频文件落盘 | 0（无需存储） |
| **并发能力** | 受服务器带宽限制 | 无限（CDN + Vercel 自动扩容） |
| **关机后可用性** | ❌ | ✅（Vercel 永久在线） |
| **成本** | 随用户量线性增长 | 固定（Vercel 免费额度足够） |

---

## ✅ 验收标准

部署成功后，必须满足：

1. ✅ Vercel 代理健康检查返回 `"status": "online"`
2. ✅ 抖音视频可直连下载（浏览器 Network 面板显示请求直接到抖音 CDN）
3. ✅ B 站视频通过 Vercel 代理下载（请求到 `your-deployment.vercel.app`）
4. ✅ 关闭本地服务器后，已生成的下载链接仍然有效
5. ✅ 浏览器控制台无 CORS 错误

---

## 🎉 下一步优化（可选）

完成基础部署后，可以考虑：

1. **绑定自定义域名**  
   比如 `cors.govid.app`，提升品牌形象。

2. **添加速率限制**  
   防止代理被滥用。

3. **添加日志监控**  
   追踪代理使用情况。

4. **支持更多平台**  
   扩展 YouTube / 小红书 / 微博的直连能力。

5. **前端优化**  
   添加"推荐下载方式"提示，引导用户使用直连。

---

## 📞 支持

如果部署过程中遇到问题：

1. 查看 Vercel Dashboard 日志
2. 运行 `vercel logs` 查看实时日志
3. 检查浏览器控制台的网络请求

---

**创建时间**：2026-10-29  
**最后更新**：2026-10-29  
**状态**：待部署
