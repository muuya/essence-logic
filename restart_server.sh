#!/bin/bash
# 重启服务器脚本
# 注意：开发环境建议使用 dev.sh，修改环境变量后调用 /api/reload-config 即可

cd "$(dirname "$0")"

echo "正在停止旧服务器进程..."
# 查找并停止运行中的服务器进程
pkill -f "python.*src/main.py" || pkill -f "uvicorn.*main:app" || echo "未找到运行中的服务器"

# 等待进程完全停止
sleep 2

echo "正在启动新服务器..."
echo ""
echo "提示："
echo "  - 开发环境建议使用: ./dev.sh (支持代码自动重载)"
echo "  - 修改环境变量后，开发环境可调用: curl -X POST http://localhost:8000/api/reload-config"
echo ""

# 激活虚拟环境并启动服务器
if [ -d ".venv" ]; then
    source .venv/bin/activate
    # 默认使用开发模式
    export ENVIRONMENT=development
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &
else
    # 如果没有虚拟环境，直接使用系统 Python
    export ENVIRONMENT=development
    python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &
fi

echo "服务器已启动，PID: $!"
echo "查看日志: tail -f logs/app.log"
