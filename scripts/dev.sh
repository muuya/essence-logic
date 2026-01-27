#!/bin/bash
# 开发模式启动脚本
# 使用 uvicorn --reload 自动重载代码变化
# 环境变量变化可通过 /api/reload-config 端点重新加载，无需重启

cd "$(dirname "$0")/.."

echo "=========================================="
echo "启动开发服务器（自动重载模式）"
echo "=========================================="
echo ""
echo "特性："
echo "  - 代码修改自动重载（无需手动重启）"
echo "  - 环境变量修改后调用 POST /api/reload-config 即可生效"
echo "  - 监听地址: http://0.0.0.0:8000"
echo ""
echo "提示："
echo "  - 修改 .env 文件后，调用: curl -X POST http://localhost:8000/api/reload-config"
echo "  - 或访问: http://localhost:8000/docs 使用 Swagger UI"
echo ""

# 设置开发环境标识
export ENVIRONMENT=development

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "警告: 未找到虚拟环境，使用系统 Python"
fi

# 使用 uvicorn 启动（--reload 启用自动重载）
uvicorn src.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info
