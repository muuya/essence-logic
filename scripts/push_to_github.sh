#!/bin/bash
# 推送到 GitHub 的脚本
# 使用方法: ./push_to_github.sh YOUR_USERNAME

if [ -z "$1" ]; then
    echo "使用方法: ./push_to_github.sh YOUR_GITHUB_USERNAME"
    echo "例如: ./push_to_github.sh steven"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="essence-logic"

echo "=========================================="
echo "准备推送到 GitHub"
echo "=========================================="
echo ""
echo "GitHub 用户名: $GITHUB_USERNAME"
echo "仓库名称: $REPO_NAME"
echo ""
echo "请确保你已经在 GitHub 上创建了公开仓库:"
echo "  https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
read -p "按 Enter 继续，或 Ctrl+C 取消..."

# 添加远程仓库
echo ""
echo "添加远程仓库..."
git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git 2>/dev/null || \
    git remote set-url origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git

# 推送代码
echo "推送到 GitHub..."
git push -u origin main

echo ""
echo "=========================================="
echo "✅ 推送完成！"
echo "=========================================="
echo ""
echo "仓库地址: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "现在可以使用以下命令部署："
echo "  python scripts/deploy.py --repo-url https://github.com/$GITHUB_USERNAME/$REPO_NAME --service-name essence-logic --branch main"
echo ""
