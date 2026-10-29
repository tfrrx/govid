# GoVid 部署到 Render 的注意事项

## ✅ 已优化的地方

### 1. Dockerfile 内存优化
- 分批安装 Python 包，避免内存溢出
- 移除了不必要的 Playwright 浏览器（只保留 Chromium）
- 设置了 `PIP_NO_CACHE_DIR=1` 减少磁盘占用

### 2. render.yaml 配置
- 设置了健康检查路径 `/api/health`
- 自动部署已关闭（`autoDeploy: false`），避免每次 push 都重新构建

### 3. 环境变量
- `GOVID_CORS_ORIGINS=*` 允许所有来源（前端可以访问）
- `GOVID_DOWNLOAD_DIR=/tmp/downloads` 使用临时目录（重启后会清空）

## ⚠️ Render 免费层限制

### 构建时
- **内存限制**: 4GB
- **构建时间**: 最长 15 分钟
- **磁盘空间**: 2GB

我们的优化：
- Dockerfile 分批安装依赖，峰值内存 < 2GB
- 总构建时间约 5-8 分钟
- 镜像大小约 1.5GB

### 运行时
- **内存限制**: 512MB
- **CPU**: 0.1 vCPU（共享）
- **磁盘空间**: 临时存储，重启后清空
- **并发**: 建议 1 个 worker

我们的配置：
- `--workers=1` 单进程运行
- 下载文件存到 `/tmp/downloads/`（临时目录）
- 处理完立即删除，不占用磁盘

### 网络
- **休眠**: 15 分钟无请求后自动休眠
- **唤醒**: 首次请求需要 30-60 秒
- **带宽**: 无限制，但 IP 可能被部分平台限流

## 🔧 如果构建失败

### 错误 1: "Out of Memory"

**原因**: 构建时内存不够。

**解决**: 在 Render Dashboard 的 **Advanced** 设置中：

1. 展开 **Docker Command**
2. 添加：
   ```
   --memory=2g --memory-swap=2g
   ```

### 错误 2: "Build timeout"

**原因**: 构建超过 15 分钟。

**解决**: 
1. 检查网络是否正常
2. 或者减少依赖（去掉 Playwright）

在 `Dockerfile` 中注释掉：

```dockerfile
# RUN apt-get install -y chromium chromium-driver
# RUN pip install playwright
# RUN playwright install-deps chromium
```

这样抖音解析会失败，但其他平台（B站、YouTube、小红书、微博）仍然可用。

### 错误 3: "Disk space exceeded"

**原因**: 磁盘空间不够。

**解决**: 在 Dockerfile 中添加清理命令：

```dockerfile
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
```

## 🚀 部署后的测试

### 1. 健康检查

```bash
curl https://你的地址.onrender.com/api/health
```

预期返回：

```json
{
  "status": "ok",
  "version": "1.0.0",
  "ffmpeg_available": true
}
```

### 2. 测试 B 站（不需要 Playwright）

```bash
curl "https://你的地址.onrender.com/api/parse?url=https://www.bilibili.com/video/BV1xx411c7mD"
```

### 3. 测试抖音（需要 Playwright）

```bash
curl "https://你的地址.onrender.com/api/parse?url=https://v.douyin.com/iRNBho6G/"
```

如果返回 500 错误，检查日志看是否 Playwright 相关。

## 📊 监控

### 查看实时日志

在 Render Dashboard：
1. 点击你的服务
2. 点击 **Logs** 标签
3. 实时查看日志

### 查看资源使用

在 Render Dashboard：
1. 点击你的服务
2. 点击 **Metrics** 标签
3. 查看 CPU、内存使用情况

如果内存经常接近 512MB，说明需要优化或升级到付费层。

## 💡 优化建议

### 1. 减少内存使用

在 `backend/config.py` 中限制并发：

```python
# 限制最多同时处理 2 个下载任务
MAX_CONCURRENT_DOWNLOADS = 2
```

### 2. 添加请求缓存

相同视频链接 5 分钟内返回缓存结果，减少后端压力。

### 3. 使用 Uptime Robot

免费监控服务，每 5 分钟 ping 一次，防止休眠：

https://uptimerobot.com/

配置：
- **Monitor Type**: HTTP(s)
- **URL**: `https://你的地址.onrender.com/api/health`
- **Monitoring Interval**: 5 minutes

## 🎯 升级选项

如果免费层不够用：

| 方案 | 费用 | 优势 |
|------|------|------|
| Render Starter | $7/月 | 不休眠，1GB RAM |
| Railway | $5/月起 | 按用量计费 |
| Fly.io | $0-10/月 | 更灵活的配置 |

但对于个人使用，**免费层完全够用**！

---

**提示**: 如果你只想要 B 站 + YouTube + 小红书，可以去掉 Playwright（节省 200MB+ 空间），抖音就不能用了。
