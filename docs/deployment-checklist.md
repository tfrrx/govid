# 部署检查清单

## ✅ 代码改动完成

### 后端核心
- ✅ `backend/models/video.py`：`FormatItem` 添加 `download_method` 字段
- ✅ `backend/core/media.py`：
  - `resolve_download_method()` 函数（平台能力矩阵）
  - `build_formats()` 添加 `download_method` 字段
- ✅ `backend/api/video.py`：
  - 导入 `Path` 和 `resolve_download_method`
  - 新增 `/tasks/{task_id}/stream` 接口

### 抖音提取器
- ✅ `backend/extractors/douyin/__init__.py`：抖音格式标记 `download_method: "direct"`
- ✅ `backend/extractors/douyin/parser.py`：抖音图集格式标记 `download_method: "direct"`

### 前端
- ✅ 无需改动（现有「直连下载」按钮可复用）

## 📋 部署前测试

### 1. 启动后端
```bash
cd backend
uvicorn main:app --reload
```

### 2. 测试抖音直连
```bash
curl -X POST "http://localhost:8000/api/parse" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://v.douyin.com/iRNBho6V/"}'

# 检查返回的 formats 中是否有 download_method: "direct"
```

### 3. 测试流式代理接口
```bash
# 先创建任务
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bilibili.com/video/BV1xx411c7mD",
    "format_id": "best"
  }'

# 等任务完成后，测试流式下载
curl "http://localhost:8000/api/tasks/{task_id}/stream" \
  --output test_stream.mp4

# 检查文件是否完整
ffmpeg -i test_stream.mp4 2>&1 | grep "Duration"
```

### 4. 测试平台能力矩阵
```bash
python test_download_methods.py
```

## 🚀 上线步骤

### 1. 备份现有代码
```bash
git checkout -b backup-before-stream-proxy
git add -A
git commit -m "备份：流式代理改造前"
```

### 2. 部署新代码
```bash
git checkout main
git pull
# ... 部署流程 ...
```

### 3. 监控指标
部署后观察 7 天：
- [ ] 抖音下载成功率（应保持 > 95%）
- [ ] B 站流式代理成功率（目标 > 90%）
- [ ] 服务器磁盘 I/O（预期降低 90%）
- [ ] 服务器带宽（预期降低 75%）
- [ ] `/tmp` 目录占用（预期降低 90%）

### 4. 回滚准备
如果出现问题：
```bash
# 方案 A：快速关闭流式代理
# 编辑 backend/core/media.py:487
CAPABILITIES = {
    "bilibili": "download",  # 改回 download
    "youtube": "download",
    # ...
}

# 方案 B：完全回滚
git checkout backup-before-stream-proxy
```

## 📊 预期效果

| 指标 | 优化前 | 优化后 | 提升 |
|-----|-------|-------|-----|
| 服务器总流量 | 200% | 50% | ↓ 75% |
| 磁盘 I/O | 200% | 20% | ↓ 90% |
| 抖音下载延迟 | 中 | 最低 | ↑ 显著 |
| B 站下载延迟 | 高 | 低 | ↑ 显著 |

## 🔧 后续优化

### 短期（1-2 周）
- [ ] 添加下载方式埋点统计
- [ ] 测试 YouTube 直链稳定性
- [ ] 补充小红书 / 微博 Headers 规则

### 中期（1 个月）
- [ ] 实现直链失效自动降级
- [ ] 添加流式代理失败重试逻辑
- [ ] 优化 `/tmp` 清理策略

### 长期（持续）
- [ ] 考虑引入 CDN（抖音直连已经是 CDN）
- [ ] 考虑对象存储（七牛云 / 阿里云 OSS）
- [ ] 考虑边缘计算（Cloudflare Workers）

---

**部署负责人签字**：__________  
**日期**：__________  
**备注**：__________
