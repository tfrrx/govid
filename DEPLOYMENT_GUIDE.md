# GoVid 部署指南

> **更新日期**：2026-10-29  
> **适用版本**：Full Mode（完整版）  
> **目标用户**：需要完整功能（流式代理 + 本地下载）的用户

---

## 🎯 部署概览

GoVid 完整版由三部分组成：

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│                 │     │                  │     │                │
│  前端（Vercel） │────▶│ 后端（自己部署） │────▶│ CORS 代理      │
│  用户界面       │     │  解析 + 下载    │     │  (Vercel)      │
│                 │     │                  │     │                │
└─────────────────┘     └──────────────────┘     └────────────────┘
```

### 各部分职责

| 组件 | 职责 | 部署位置 | 成本 |
|------|------|---------|------|
| **前端** | 用户界面、视频信息展示 | Vercel | 免费 |
| **后端** | 视频解析、下载、流式代理 | 自己的服务器 | 服务器成本 |
| **CORS 代理** | 绕过浏览器跨域限制 | Vercel（已部署） | 免费 |

---

## 📋 部署前准备

### 1. 账号注册

- **GitHub**：https://github.com/signup
- **Vercel**：https://vercel.com/signup
- **服务器**：任选一个
  - 腾讯云轻量应用服务器：¥112/年（2核4G）
  - 阿里云ECS：按需选择
  - Vultr/DigitalOcean：$6/月起

### 2. 本地工具安装

**macOS**:
```bash
# 安装 Vercel CLI
npm install -g vercel

# 检查安装
vercel --version
```

**Windows**:
```bash
npm install -g vercel
```

### 3. 服务器准备

**推荐配置**：
- **操作系统**：Ubuntu 22.04 LTS
- **配置**：2核4G内存，50GB存储
- **带宽**：3Mbps 起（用户越多需要越大）

---

## 🚀 部署步骤

### 第一步：部署 CORS 代理（已完成）✅

CORS 代理已部署在：
```
https://govid-cors-proxy.vercel.app/api/cors-proxy
```

**无需操作**，直接使用即可。

---

### 第二步：部署后端到服务器

#### 2.1 登录服务器

```bash
ssh root@你的服务器IP
```

#### 2.2 安装系统依赖

```bash
# 更新系统
apt-get update && apt-get upgrade -y

# 安装 Python 和 ffmpeg
apt-get install -y python3 python3-pip python3-venv ffmpeg git
```

#### 2.3 克隆代码

```bash
# 进入部署目录
cd /opt

# 克隆仓库（替换成你的仓库地址）
git clone https://github.com/你的用户名/govid.git
cd govid
```

#### 2.4 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt
```

#### 2.5 配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
# 运行模式
GOVID_MODE=full

# 后端地址（0.0.0.0 监听所有网卡）
GOVID_HOST=0.0.0.0
GOVID_PORT=8000

# CORS 代理地址（已部署好的）
GOVID_CORS_PROXY_URL=https://govid-cors-proxy.vercel.app/api/cors-proxy

# 下载目录（可选）
# GOVID_DOWNLOAD_DIR=/opt/govid/downloads
EOF
```

#### 2.6 测试运行

```bash
# 测试启动
python3 backend/main.py
```

看到以下输出说明成功：
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**按 Ctrl+C 停止**，然后继续下一步。

#### 2.7 配置 systemd 服务（开机自启）

```bash
# 创建服务文件
cat > /etc/systemd/system/govid.service << 'EOF'
[Unit]
Description=GoVid Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/govid
Environment="PATH=/opt/govid/.venv/bin"
ExecStart=/opt/govid/.venv/bin/python3 backend/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重载 systemd
systemctl daemon-reload

# 启动服务
systemctl start govid

# 设置开机自启
systemctl enable govid

# 查看状态
systemctl status govid
```

看到 **Active: active (running)** 说明成功。

#### 2.8 配置防火墙

**腾讯云/阿里云控制台**：
1. 进入「安全组」或「防火墙」设置
2. 添加规则：
   - 协议：TCP
   - 端口：8000
   - 来源：0.0.0.0/0（允许所有）

**服务器本地防火墙**：
```bash
# Ubuntu UFW
ufw allow 8000/tcp
ufw reload
```

#### 2.9 验证后端

```bash
# 本地测试
curl http://你的服务器IP:8000/health
```

应该返回：
```json
{
  "status": "ok",
  "mode": "full",
  "uptime": "0h 0m 5s"
}
```

---

### 第三步：部署前端到 Vercel

#### 3.1 修改前端配置

**在你的本地电脑上**，编辑 `frontend/.env.production`：

```bash
cd /Users/happy/Project/Python_VideoDownlaoder/govid/frontend

# 修改 API 地址（改成你的服务器）
cat > .env.production << 'EOF'
# 后端 API 地址（改成你的服务器 IP）
VITE_API_BASE_URL=http://你的服务器IP:8000
EOF
```

#### 3.2 提交代码

```bash
# 添加更改
git add .env.production

# 提交
git commit -m "fix: 配置生产环境后端地址"

# 推送到 GitHub
git push origin main
```

#### 3.3 登录 Vercel

```bash
cd frontend
vercel login
```

浏览器会打开，授权后回到终端。

#### 3.4 部署到 Vercel

```bash
# 部署到生产环境
vercel --prod
```

**第一次部署会询问**：
```
? Set up and deploy "~/Project/Python_VideoDownlaoder/govid/frontend"? [Y/n] y
? Which scope do you want to deploy to? 选择你的账号
? Link to existing project? [y/N] n
? What's your project's name? govid-frontend
? In which directory is your code located? ./
? Want to override the settings? [y/N] n
```

稍等片刻，看到：
```
✅  Production: https://govid-frontend.vercel.app [deployed]
```

---

### 第四步：验证完整流程

#### 4.1 打开前端

访问：`https://govid-frontend.vercel.app`

#### 4.2 测试解析

1. 粘贴一个抖音视频链接：
   ```
   https://v.douyin.com/iksxDRNM/
   ```

2. 点击「解析视频」

3. 应该看到：
   - ✅ 视频标题、封面、时长
   - ✅ 清晰度列表
   - ✅ 可以点击下载

#### 4.3 测试下载

1. 选择一个清晰度
2. 点击「开始下载」
3. 看到进度条走动
4. 完成后点击「下载文件」

**如果全部成功，部署完成！🎉**

---

## 🔧 常见问题

### Q1: 前端提示「连接后端失败」

**症状**：打开网站后，顶部显示「请先启动后端」

**排查步骤**：

1. **检查后端是否在运行**：
   ```bash
   ssh root@你的服务器IP
   systemctl status govid
   ```
   
   如果显示 `Active: active (running)`，说明后端正常。

2. **检查防火墙**：
   ```bash
   # 测试端口是否开放
   curl http://你的服务器IP:8000/health
   ```
   
   如果超时，说明防火墙没开 8000 端口。

3. **检查前端配置**：
   ```bash
   # 查看 Vercel 环境变量
   cd frontend
   vercel env ls
   ```
   
   确认 `VITE_API_BASE_URL` 是否正确。

### Q2: 解析成功，但下载失败

**症状**：能看到视频信息，但点下载后卡住或报错

**排查步骤**：

1. **检查后端日志**：
   ```bash
   ssh root@你的服务器IP
   journalctl -u govid -f
   ```
   
   看最后几行是否有错误。

2. **检查磁盘空间**：
   ```bash
   df -h
   ```
   
   确保 `/opt/govid` 所在分区有足够空间。

3. **检查 ffmpeg**：
   ```bash
   ffmpeg -version
   ```
   
   如果提示 `command not found`，重新安装：
   ```bash
   apt-get install -y ffmpeg
   systemctl restart govid
   ```

### Q3: 抖音能解析，B站/YouTube 失败

**原因**：抖音是自研解析器，其他平台走 yt-dlp，可能需要更新。

**解决**：

```bash
ssh root@你的服务器IP
cd /opt/govid
source .venv/bin/activate
pip install --upgrade yt-dlp
systemctl restart govid
```

### Q4: 下载速度慢

**原因**：服务器带宽不足，或视频源站限速。

**优化方案**：

1. **升级服务器带宽**（最有效）
2. **对于抖音视频，使用直连模式**（见下一节）

---

## ⚡ 性能优化

### 1. 抖音直连模式（推荐）

抖音视频支持 **302 直连**，不走服务器中转，速度更快：

**后端配置**：无需修改，默认支持。

**前端使用**：
- 下载时会自动使用直连
- 文件不经过服务器，节省带宽

### 2. 调整并发数

```bash
# 编辑 .env
nano /opt/govid/.env
```

添加：
```
# 最大并发下载数（默认 3）
GOVID_MAX_CONCURRENT=5
```

重启服务：
```bash
systemctl restart govid
```

### 3. 清理临时文件

```bash
# 添加定时清理（每天凌晨 3 点）
crontab -e
```

添加一行：
```
0 3 * * * find /opt/govid/downloads -mtime +1 -delete
```

---

## 🔄 更新部署

### 更新后端

```bash
ssh root@你的服务器IP
cd /opt/govid
git pull
source .venv/bin/activate
pip install -r backend/requirements.txt
systemctl restart govid
```

### 更新前端

```bash
# 本地电脑
cd /Users/happy/Project/Python_VideoDownlaoder/govid/frontend
git pull
vercel --prod
```

---

## 📊 监控与日志

### 查看后端日志

```bash
# 实时日志
journalctl -u govid -f

# 最近 100 行
journalctl -u govid -n 100

# 今天的日志
journalctl -u govid --since today
```

### 查看资源使用

```bash
# CPU 和内存
htop

# 磁盘使用
df -h

# 网络流量（需要安装 vnstat）
apt-get install -y vnstat
vnstat
```

---

## 🛡️ 安全建议

### 1. 使用 HTTPS（推荐）

前端已在 Vercel 自动启用 HTTPS，但后端还是 HTTP。

**方案**：用 Nginx 反向代理 + Let's Encrypt 证书

```bash
# 安装 Nginx 和 Certbot
apt-get install -y nginx certbot python3-certbot-nginx

# 配置 Nginx
cat > /etc/nginx/sites-available/govid << 'EOF'
server {
    listen 80;
    server_name api.你的域名.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# 启用配置
ln -s /etc/nginx/sites-available/govid /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# 申请证书
certbot --nginx -d api.你的域名.com
```

然后把前端的 `VITE_API_BASE_URL` 改为 `https://api.你的域名.com`。

### 2. 限制访问来源

如果只想自己用，可以限制 IP：

```bash
# 编辑 Nginx 配置
nano /etc/nginx/sites-available/govid
```

添加：
```nginx
location / {
    allow 你的家庭IP;
    deny all;
    proxy_pass http://127.0.0.1:8000;
}
```

### 3. 定期备份

```bash
# 备份脚本
cat > /root/backup-govid.sh << 'EOF'
#!/bin/bash
tar -czf /root/govid-backup-$(date +%Y%m%d).tar.gz /opt/govid
find /root -name "govid-backup-*.tar.gz" -mtime +7 -delete
EOF

chmod +x /root/backup-govid.sh

# 每周日凌晨 2 点备份
crontab -e
# 添加：0 2 * * 0 /root/backup-govid.sh
```

---

## 💰 成本估算

| 项目 | 费用 | 说明 |
|------|------|------|
| 服务器 | ¥112-300/年 | 腾讯云轻量应用服务器 |
| 域名 | ¥10-60/年 | 可选，只想自己用可不买 |
| Vercel | 免费 | 100GB 流量/月 |
| CORS 代理 | 免费 | 已部署，无需付费 |

**总计**：¥112-360/年

---

## 🎓 下一步

- [ ] 绑定自定义域名（可选）
- [ ] 配置 HTTPS 证书
- [ ] 设置监控告警（可用 UptimeRobot 免费版）
- [ ] 邀请朋友一起用

**祝部署顺利！🚀**

如有问题，请查看项目文档或提 Issue。
