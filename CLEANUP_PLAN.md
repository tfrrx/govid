# 清理计划

## 要删除的文件/文件夹（不可行的方案）

### 1. Vercel 相关（不支持 yt-dlp + ffmpeg）
- `vercel-proxy/` - 只是 CORS 代理，不解析视频
- `vercel.json` - Vercel 配置，用不上
- `docs/部署计划-Vercel直连方案.md` - 理论方案，实际不可行

### 2. Cloudflare Workers 相关（只支持 JS，不支持 Python）
- `workers/` - 只是 CORS 代理，不解析视频
- `frontend-lite/workers/` - 废弃的尝试

### 3. 杂乱的测试文件
- `test_cors_proxy.py`
- `test_download_methods.py`
- `test_frontend_cors_proxy.md`

### 4. 旧的部署脚本（会被新的替代）
- `deploy.sh`
- `deploy_backend.sh`
- `deploy_frontend.sh`

## 要保留的
- `backend/` - 完整后端，支持所有平台
- `frontend/` - 前端界面
- `frontend-lite/` - 纯前端版（只支持抖音，可选）
- `.env.example`
- `requirements.txt`

## 新增的
- `render.yaml` - Render 部署配置
- `Dockerfile` - Docker 容器配置
- `DEPLOYMENT.md` - 部署文档
