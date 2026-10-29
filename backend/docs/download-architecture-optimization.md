# 下载架构优化方案

## 问题

原架构：**所有视频先下载到服务器 → 再推送给用户**

后果：
- 服务器流量 = 2 × 视频大小（下行+上行）
- 磁盘 I/O 成倍增加
- 用户量增长 → 服务器带宽线性扩容
- 成本不可持续

## 解决方案：混合下载架构

根据平台特性智能选择三种下载方式：

| 方式 | 适用场景 | 服务器流量 | 磁盘 I/O | 延迟 |
|------|---------|----------|---------|------|
| **直连下载** | 抖音（CDN 无 Referer 限制） | 0 | 0 | 最低 |
| **流式代理** | B 站/YouTube（需特定 Headers） | 1× | 0 | 低 |
| **传统下载** | Twitter 等（IP 绑定） | 2× | 2× | 高 |

### 核心改进

1. **抖音直连**（占流量 60%+）
   - 服务器只返回 302 跳转
   - 字节流在用户浏览器 ↔ CDN 之间传输
   - **服务器流量降为 0**

2. **流式代理**（占流量 30%）
   - 服务器边拉边推，不落盘
   - 峰值内存 < 1MB/请求
   - **磁盘 I/O 降为 0**

3. **传统下载**（占流量 10%）
   - 仅用于必须的场景（Twitter IP 绑定）
   - 保留原有逻辑

## 实现细节

### 后端改动

#### 1. 平台能力矩阵 ([backend/core/media.py:446](backend/core/media.py:446))

```python
def resolve_download_method(url: str, format_id: str) -> dict:
    """智能决策下载方式"""
    CAPABILITIES = {
        "bilibili": "stream",
        "youtube": "stream",
        "twitter": "download",
        "xiaohongshu": "stream",
        "weibo": "stream",
    }
    # 抖音 → direct
    # 其他 → 查表或默认 download
```

#### 2. 流式代理 API ([backend/api/video.py:320](backend/api/video.py:320))

```python
@router.get("/tasks/{task_id}/stream")
async def api_stream_video(task_id: str):
    """边拉边推，零落盘"""
    async def stream_generator():
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", video_url, headers=...) as response:
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    yield chunk
    return StreamingResponse(stream_generator(), ...)
```

#### 3. 格式字段扩展 ([backend/models/video.py](backend/models/video.py))

每个 `FormatItem` 新增：
```python
download_method: Literal["direct", "stream", "download"] = "download"
```

抖音格式自动标记 `download_method: "direct"`。

### 前端改动

前端已有的「直连下载」按钮（[frontend/src/components/DownloadProgress.vue:252](frontend/src/components/DownloadProgress.vue:252)）可直接复用。

对于 `download_method: "stream"` 的格式，前端可以：
- 用传统「下载文件」按钮调 `/tasks/{id}/file`
- 或新增「流式下载」按钮调 `/tasks/{id}/stream`

现阶段**无需前端改动**，后端智能路由即可。

## 效果预测

假设用户构成：
- 抖音 60%
- B 站/YouTube 30%
- 其他 10%

### 优化前
- 服务器总流量：200%（下行 + 上行各 100%）
- 磁盘 I/O：200%（写入 + 读出各 100%）

### 优化后
- **服务器总流量**：60% × 0% + 30% × 100% + 10% × 200% = **50%** ↓ 75%
- **磁盘 I/O**：60% × 0% + 30% × 0% + 10% × 200% = **20%** ↓ 90%
- **成本增长**：从线性变为亚线性

## 部署计划

### 第 1 阶段：基础设施（本次完成）
- ✅ 添加 `resolve_download_method` 函数
- ✅ 添加 `/tasks/{id}/stream` 接口
- ✅ 格式字段添加 `download_method`
- ✅ 抖音格式自动标记 `direct`

### 第 2 阶段：平台测试（下一步）
1. 测试 B 站直链稳定性（是否需要定期刷新 Cookie）
2. 测试 YouTube 直链时效（是否需要缓存 + 定时刷新）
3. 补充小红书 / 微博的 Headers 规则
4. 记录每个平台的下载成功率

### 第 3 阶段：监控与兜底（持续优化）
- 加埋点：记录 `direct`/`stream`/`download` 各自的成功率
- 直链失效时自动降级到流式代理
- 流式代理失败时自动降级到传统下载
- 定期清理 `/tmp`（现在只有 10% 流量落盘）

## 回滚方案

如果流式代理出现问题，只需：
1. 修改 `CAPABILITIES` 表，把对应平台改回 `"download"`
2. 重启后端（零停机，nginx 有缓冲）
3. 前端无需改动

## 参考资料

- [httpx 流式响应文档](https://www.python-httpx.org/advanced/#streaming-responses)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- B 站 Referer 检测规则（内部测试记录）

---

**作者**：GoVid 优化小组  
**日期**：2024-10-29  
**状态**：✅ 第 1 阶段已完成
