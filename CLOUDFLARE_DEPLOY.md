# GoVid Lite 部署到 Cloudflare Pages 完整教程

从零开始，手把手教你把 GoVid Lite 部署上线！

---

## 为什么选择 Cloudflare Pages？

- ✅ **完全免费** — 无限流量，无限请求
- ✅ **全球 CDN** — 自动分发到 275+ 个城市
- ✅ **自动构建** — 推送 GitHub 自动部署
- ✅ **自定义域名** — 支持绑定自己的域名
- ✅ **零配置 HTTPS** — 自动签发证书

---

## 第一步：注册账号（5 分钟）

### 1.1 注册 Cloudflare 账号

访问：https://dash.cloudflare.com/sign-up

- 输入邮箱（建议用 Gmail）
- 设置密码（至少 8 位）
- 点击 **Create Account**
- 去邮箱验证（点击邮件里的链接）

### 1.2 注册 GitHub 账号（如果已有就跳过）

访问：https://github.com/signup

- 输入邮箱、密码、用户名
- 验证邮箱
- 完成账号创建

---

## 第二步：上传代码到 GitHub（10 分钟）

### 2.1 在 GitHub 上创建仓库

1. 登录 GitHub 后，点击右上角 **+** → **New repository**
2. 填写信息：
   - **Repository name**: `govid-lite`（仓库名，随便起）
   - **Description**: `GoVid Lite 视频下载工具`（可选）
   - **Public** / **Private**：选 **Private**（私有，只有自己能看）
   - ❌ **不要勾选** "Add a README file"
3. 点击 **Create repository**

### 2.2 本地推送代码

**在你的项目目录（govid）里**，打开终端：

```bash
# 1. 检查 git 状态
git status

# 2. 添加远程仓库（把 YOUR_USERNAME 改成你的 GitHub 用户名）
git remote add github https://github.com/YOUR_USERNAME/govid-lite.git

# 3. 推送代码到 GitHub
git push -u github main
```

**如果提示输入用户名和密码**：
- 用户名：你的 GitHub 用户名
- 密码：需要用 **Personal Access Token**（不是账号密码！）

### 2.3 生成 GitHub Token（如果需要）

1. 访问：https://github.com/settings/tokens
2. 点击 **Generate new token** → **Generate new token (classic)**
3. 填写：
   - **Note**: `govid-lite-deploy`
   - **Expiration**: `No expiration`（永不过期）
   - **权限勾选**: `repo`（完整权限）
4. 点击 **Generate token**
5. **复制 Token**（只会显示一次，务必保存好！）
6. 回到终端，密码处粘贴这个 Token

---

## 第三步：连接 Cloudflare Pages（5 分钟）

### 3.1 进入 Cloudflare Pages 控制台

1. 登录 Cloudflare：https://dash.cloudflare.com
2. 左侧菜单点击 **Workers & Pages**
3. 点击 **Create application**
4. 选择 **Pages** 标签
5. 点击 **Connect to Git**

### 3.2 授权 GitHub

1. 点击 **Connect GitHub**
2. 会跳转到 GitHub 授权页面
3. 选择：
   - **Only select repositories** （只授权指定仓库）
   - 在下拉框选择 `govid-lite`
4. 点击 **Install & Authorize**

### 3.3 选择仓库

1. 回到 Cloudflare 页面，你会看到刚才授权的仓库
2. 点击 `govid-lite` 旁边的 **Begin setup**

---

## 第四步：配置构建设置（3 分钟）

### 4.1 填写项目设置

在 **Set up builds and deployments** 页面：

**Project name**:
```
govid-lite
```
（这个会是你的网址前缀，如 `govid-lite.pages.dev`）

**Production branch**:
```
main
```
（使用 main 分支作为生产环境）

### 4.2 构建配置

**Framework preset**:
```
None
```
（选择"None"，我们手动配置）

**Build command**:
```bash
cd frontend-lite && npm install && npm run build
```

**Build output directory**:
```
frontend-lite/dist
```

**Root directory (optional)**:
```
留空
```

### 4.3 环境变量（重要！）

点击 **Add environment variable**，添加：

| Variable name | Value |
|---------------|-------|
| `NODE_VERSION` | `18` |

> 这个环境变量告诉 Cloudflare 使用 Node.js 18 版本

### 4.4 开始部署

点击 **Save and Deploy** 按钮！

---

## 第五步：等待部署完成（5-10 分钟）

### 5.1 观察构建日志

部署开始后，你会看到实时日志：

```
17:52:12   Cloning repository...
17:52:15   Installing dependencies...
17:52:45   Building application...
17:53:20   Deploying to Cloudflare's global network...
17:53:25   Success! Deployed to https://govid-lite.pages.dev
```

### 5.2 部署成功的标志

看到绿色的 **✓ Success** 和网址链接，就说明部署成功了！

---

## 第六步：访问你的网站！🎉

### 6.1 获取网址

部署成功后，你会得到一个网址，格式是：

```
https://govid-lite.pages.dev
```

或者你自定义的项目名：

```
https://YOUR-PROJECT-NAME.pages.dev
```

### 6.2 测试功能

1. 打开网址
2. 粘贴一个抖音视频链接（例如：`https://v.douyin.com/xxx`）
3. 点击「解析视频」
4. 看到清晰度列表后，点击下载按钮
5. 视频开始下载 ✅

---

## 常见问题

### Q1: 构建失败，提示 `npm: command not found`

**原因**：没有设置 `NODE_VERSION` 环境变量。

**解决**：
1. 回到 Cloudflare Pages 项目设置
2. 点击 **Settings** → **Environment variables**
3. 添加 `NODE_VERSION = 18`
4. 点击 **Retry deployment**

### Q2: 构建失败，提示 `ENOENT: no such file or directory`

**原因**：Build command 路径错误。

**解决**：确认 Build command 是：
```bash
cd frontend-lite && npm install && npm run build
```

### Q3: 网站能打开，但解析失败，提示 404

**原因**：前端没有连接到后端 API。

**解决**：Lite 版本**只有前端**，需要单独部署后端到 Vercel：

```bash
# 1. 构建后端（在 govid 根目录）
cd backend

# 2. 部署到 Vercel
vercel --prod
# 会得到一个后端地址，如：https://govid-backend.vercel.app

# 3. 修改前端环境变量
cd ../frontend-lite
nano .env.production
```

修改为：
```
VITE_API_BASE_URL=https://govid-backend.vercel.app
```

```bash
# 4. 重新推送代码（触发 Cloudflare 自动部署）
git add .env.production
git commit -m "fix: 连接后端 API"
git push github main
```

### Q4: 想绑定自己的域名

**操作步骤**：
1. 在 Cloudflare Pages 项目页面，点击 **Custom domains**
2. 点击 **Set up a custom domain**
3. 输入你的域名（如 `download.example.com`）
4. 按照提示添加 DNS 记录（CNAME）
5. 等待 DNS 生效（5-30 分钟）
6. 自动签发 HTTPS 证书 ✅

---

## 后续更新

每次你在本地修改代码后：

```bash
git add .
git commit -m "feat: 你的更新说明"
git push github main
```

Cloudflare Pages 会**自动检测**并重新部署，无需手动操作！

---

## 成本

| 资源 | 额度 | 费用 |
|------|------|------|
| Cloudflare Pages | 无限流量 + 无限请求 | **完全免费** |
| 自定义域名 | 需要自行购买域名 | ¥10-60/年（可选） |
| Vercel 后端 | 100GB 流量/月 | **免费** |

**总结**：完全免费部署，零成本上线！

---

## 下一步

- [ ] 部署后端到 Vercel（参考 `DEPLOY.md`）
- [ ] 绑定自定义域名（可选）
- [ ] 配置 Cloudflare Analytics（免费流量统计）
- [ ] 添加自定义 favicon 和 meta 标签

**祝部署顺利！🚀**
