#!/bin/bash
# 生产模式启动脚本
# 使用 uvicorn 启动，不支持自动重载

cd "$(dirname "$0")/.."

echo "=========================================="
echo "启动生产服务器"
echo "=========================================="
echo ""

# 设置生产环境标识
export ENVIRONMENT=production

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "警告: 未找到虚拟环境，使用系统 Python"
fi

# 使用 uvicorn 启动（生产模式，无自动重载）
uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info
