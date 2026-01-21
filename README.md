# 本质看板 (The Essence Logic) 4.0

一个引导式观察工具，通过"如实观照"帮助用户看清什么是"对的事情"，并停止那些"错的事情"。基于段永平"本分"与"平常心"哲学。

🌐 **在线访问：** [https://essence-logic.ai-builders.space/](https://essence-logic.ai-builders.space/)  
📚 **API 文档：** [https://essence-logic.ai-builders.space/docs](https://essence-logic.ai-builders.space/docs)  
📦 **GitHub 仓库：** [https://github.com/muuya/essence-logic](https://github.com/muuya/essence-logic)

## 产品理念

在日常生活中，我们在面对决策、挫折或诱惑时，往往被**贪婪、恐惧、虚荣或短视**所蒙蔽。这些噪音掩盖了事情的本质，让我们偏离了"本分"，失去了"平常心"。

**核心价值：** 现有的 AI 助手大多在教人"如何多快好省地做事情"，却很少有人帮助我们思考"这件事该不该做"以及"它的本质是什么"。

## 核心功能

通过**"如实观照"**的逻辑，引导用户完成以下四步：

1. **安顿与映射（Mirroring）：** 准确说出用户当下的情绪和处境，允许情绪存在，不做道德评判。
2. **回归常识（Tracing）：** 引导用户剥离"运气、面子、短期暴利"，寻找本质。
3. **共识门槛（Consensus Gate）：** 在给建议前，必须先确认核心问题。
4. **微小实践（Action）：** 确认共识后，仅提供"把事情做对"的微小起始点。

## 技术架构

- **后端框架：** FastAPI
- **AI 服务：** AI Builders API
- **设计原则：** 极简、快速、直击本质

## 环境设置

本项目使用 [uv](https://github.com/astral-sh/uv) 管理 Python 虚拟环境和依赖。

### 安装 uv

```bash
# macOS (使用 Homebrew)
brew install uv

# 或使用官方安装脚本
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 设置虚拟环境

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv sync
```

### 配置环境变量

项目支持两种 AI 服务模式，通过 `AI_SERVICE` 环境变量配置：

**1. DeepSeek 直接调用模式（AI_SERVICE=deepseek）**

```bash
AI_SERVICE=deepseek
DEEPSEEK_API_KEY=sk-aa2772f56bf64e309bd3fd1885a03948
```

**2. AI Builders API 模式（AI_SERVICE=test，默认）**

```bash
AI_SERVICE=test
AI_BUILDER_TOKEN=your_token_here
```

**推荐方法：使用 .env 文件**

编辑项目根目录下的 `.env` 文件，根据你的需求配置：
```bash
# 选择服务类型
AI_SERVICE=deepseek  # 或 test

# DeepSeek 配置（当 AI_SERVICE=deepseek 时）
DEEPSEEK_API_KEY=sk-aa2772f56bf64e309bd3fd1885a03948

# AI Builders 配置（当 AI_SERVICE=test 时）
AI_BUILDER_TOKEN=your_token_here
```

**或者使用环境变量：**
```bash
export AI_SERVICE="deepseek"
export DEEPSEEK_API_KEY="sk-aa2772f56bf64e309bd3fd1885a03948"
```

**注意**: API Key 和 Token 不要提交到 Git，`.env` 文件已在 `.gitignore` 中。

## 运行应用

### 开发模式（推荐）

开发模式支持代码自动重载，修改环境变量后无需重启服务器：

```bash
# 使用开发脚本启动（推荐）
./dev.sh

# 或手动启动
source .venv/bin/activate
export ENVIRONMENT=development
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**开发模式特性：**
- ✅ 代码修改自动重载（无需手动重启）
- ✅ 环境变量修改后调用 `POST /api/reload-config` 即可生效，无需重启
- ✅ 自动检测 `.env` 文件变化

**修改环境变量后的操作：**

1. 修改 `.env` 文件
2. 调用重载接口：
   ```bash
   curl -X POST http://localhost:8000/api/reload-config
   ```
3. 或访问 Swagger UI：http://localhost:8000/docs，找到 `/api/reload-config` 端点并执行

### 生产模式

```bash
# 使用生产脚本启动
./start.sh

# 或手动启动
source .venv/bin/activate
export ENVIRONMENT=production
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 访问 API

- API 文档：http://localhost:8000/docs
- OpenAPI Schema：http://localhost:8000/openapi.json
- 主页：http://localhost:8000/
- 健康检查：http://localhost:8000/health
- 配置重载（仅开发环境）：http://localhost:8000/api/reload-config

## 🌐 在线访问

项目已成功部署到 AI Builders Space，可以直接访问：

- **主页：** https://essence-logic.ai-builders.space/
- **API 文档：** https://essence-logic.ai-builders.space/docs
- **健康检查：** https://essence-logic.ai-builders.space/health

## 部署到 AI Builders Space

项目已集成 AI Builders API 部署功能，可以一键部署到生产环境。

### 前置要求

1. **设置 AI Builders Token**
   ```bash
   export AI_BUILDER_TOKEN='your_token_here'
   ```
   或在 `.env` 文件中配置：
   ```bash
   AI_BUILDER_TOKEN=your_token_here
   ```

2. **确保项目可正常运行**
   ```bash
   ./dev.sh  # 测试本地运行
   ```

### 快速部署

**基本部署（使用默认配置）：**
```bash
python deploy.py
```

**使用自定义配置：**
```bash
# 1. 复制配置示例
cp deploy.config.example.json deploy.config.json

# 2. 编辑配置文件（可选）
# 修改 deploy.config.json

# 3. 使用配置文件部署
python deploy.py --config deploy.config.json
```

**指定项目名称：**
```bash
python deploy.py --project-name my-essence-logic
```

### 部署选项

- `--config <path>`: 指定配置文件路径
- `--no-wait`: 不等待部署完成（立即返回）
- `--timeout <seconds>`: 设置等待超时时间（默认300秒）
- `--list`: 列出所有部署
- `--status <deployment_id>`: 查询指定部署的状态
- `--project-name <name>`: 指定项目名称

### 部署管理

**列出所有部署：**
```bash
python deploy.py --list
```

**查询部署状态：**
```bash
python deploy.py --status <deployment_id>
```

### 部署状态

当前部署状态：✅ **HEALTHY**  
部署地址：https://essence-logic.ai-builders.space/  
GitHub 仓库：https://github.com/muuya/essence-logic

### 详细文档

更多部署信息请参考：[部署指南](./部署指南.md)

## API 使用

### 聊天接口

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "我想投资某个项目，但不确定是否该做"}
    ],
    "model": "deepseek"
  }'
```

### Python 示例

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "messages": [
            {"role": "user", "content": "我想投资某个项目，但不确定是否该做"}
        ],
        "model": "deepseek"
    }
)

print(response.json()["message"]["content"])
```

## 项目结构

```
guide/
├── .venv/                  # 虚拟环境（由 uv 创建）
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── main.py            # FastAPI 应用主文件
│   ├── aibuilders_client.py  # AI Builders API 客户端（包含部署功能）
│   ├── system_prompt.py   # 系统提示词
│   └── logger_config.py   # 日志配置
├── static/                 # 静态文件目录
│   └── index.html         # 前端页面
├── logs/                   # 日志目录
├── dev.sh                  # 开发模式启动脚本（推荐）
├── start.sh                # 生产模式启动脚本
├── restart_server.sh        # 重启服务器脚本
├── deploy.py               # 部署脚本（AI Builders Space）
├── deploy.config.example.json  # 部署配置示例
├── 部署指南.md             # 部署文档
├── 产品定义简报.md         # 产品定义文档
├── requirements.txt        # Python 依赖列表
├── pyproject.toml         # 项目配置（uv 推荐）
└── README.md              # 本文件
```

## 系统提示词

系统提示词定义了 Chatbot 的行为准则，基于段永平"本分"与"平常心"哲学。详细内容请查看 `src/system_prompt.py` 和 `产品定义简报.md`。

## 开发工作流

### 环境变量管理最佳实践

**问题：** 修改 `.env` 文件后需要重启服务器才能生效，很不方便。

**解决方案：**

1. **开发环境使用 `dev.sh` 启动**
   ```bash
   ./dev.sh
   ```

2. **修改 `.env` 文件后，调用重载接口**
   ```bash
   curl -X POST http://localhost:8000/api/reload-config
   ```
   或者访问 http://localhost:8000/docs 使用 Swagger UI 调用

3. **代码修改会自动重载**（uvicorn --reload）

**工作原理：**
- 开发环境（`ENVIRONMENT=development`）每次请求都会重新加载 `.env` 文件
- 生产环境（`ENVIRONMENT=production`）只在启动时加载一次，性能更好
- `/api/reload-config` 端点可以手动触发配置重载（仅开发环境）

### 基本开发流程

1. **激活虚拟环境**
   ```bash
   source .venv/bin/activate
   ```

2. **运行应用**
   ```bash
   uvicorn src.main:app --reload
   ```

3. **测试 API**
   访问 http://localhost:8000/docs 使用交互式 API 文档

## 产品目标

**目标一：实现"直击本质"的对话深度**
- AI 必须在 3 轮对话内识别出用户陈述中的"非本分"动机
- 输出结果中，关于"不该做什么"的权重必须大于"该做什么"

**目标二：确保"平常心"的思维训练**
- 用户在对话结束后的焦虑感自测评分平均下降 30%
- 所有的分析必须基于"常识"和"逻辑"，严禁使用成功学、鸡汤或未经证实的预测

**目标三：极简的用户体验**
- 响应速度极快，且没有任何多余的 UI 装饰，体现"本分"的产品观

## 项目链接

- 🌐 **在线访问：** [https://essence-logic.ai-builders.space/](https://essence-logic.ai-builders.space/)
- 📚 **API 文档：** [https://essence-logic.ai-builders.space/docs](https://essence-logic.ai-builders.space/docs)
- 📦 **GitHub 仓库：** [https://github.com/muuya/essence-logic](https://github.com/muuya/essence-logic)
- 📋 **部署指南：** [部署指南](./部署指南.md)
- 📄 **产品定义：** [产品定义简报](./产品定义简报.md)

## 参考资源

- [uv 文档](https://github.com/astral-sh/uv)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [AI Builders API 文档](https://space.ai-builders.com/backend/openapi.json)
- [产品定义简报](./产品定义简报.md)
