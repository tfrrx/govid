#!/bin/bash
# 一键部署脚本（自动检测并推荐最佳方案）

set -e

echo "🚀 GoVid 部署向导"
echo ""

# 检测是否有 Vercel 账号
if command -v vercel &> /dev/null; then
    echo "✅ 检测到 Vercel CLI"
    HAS_VERCEL=true
else
    echo "⚠️  未检测到 Vercel CLI（可选）"
    HAS_VERCEL=false
fi

# 检测是否有 Railway 账号
if command -v railway &> /dev/null; then
    echo "✅ 检测到 Railway CLI"
    HAS_RAILWAY=true
else
    echo "⚠️  未检测到 Railway CLI（可选）"
    HAS_RAILWAY=false
fi

echo ""
echo "请选择部署模式："
echo "1) Lite 模式（免费 Serverless，只支持抖音/快手）"
echo "2) Full 模式（需要服务器，支持所有平台）"
read -p "输入数字选择 [1]: " MODE
MODE=${MODE:-1}

if [ "$MODE" -eq 1 ]; then
    echo ""
    echo "📦 构建 Lite 版前端..."
    cd frontend
    npm install
    npm run build -- --mode production.lite
    cd ..

    if [ "$HAS_VERCEL" = true ]; then
        echo ""
        echo "🚀 部署到 Vercel..."
        vercel --prod
    else
        echo ""
        echo "✅ 构建完成！前端产物在 frontend/dist"
        echo ""
        echo "请手动部署到以下任意平台："
        echo "  - Vercel: https://vercel.com"
        echo "  - Netlify: https://netlify.com"
        echo "  - Cloudflare Pages: https://pages.cloudflare.com"
    fi
else
    echo ""
    echo "请选择部署目标："
    echo "1) Railway（免费 $5/月额度）"
    echo "2) Docker Compose（需要自备服务器）"
    read -p "输入数字选择 [1]: " TARGET
    TARGET=${TARGET:-1}

    if [ "$TARGET" -eq 1 ]; then
        if [ "$HAS_RAILWAY" = true ]; then
            echo ""
            echo "🚀 部署到 Railway..."
            railway up
        else
            echo ""
            echo "⚠️  请先安装 Railway CLI:"
            echo "  npm i -g @railway/cli"
            echo "  railway login"
        fi
    else
        echo ""
        echo "📦 构建 Docker 镜像..."
        docker-compose build
        echo ""
        echo "🚀 启动服务..."
        docker-compose up -d
        echo ""
        echo "✅ 部署完成！服务运行在 http://localhost:8000"
    fi
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "📚 详细文档请查看: DEPLOY.md"
