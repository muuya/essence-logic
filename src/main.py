"""
本质看板 (The Essence Logic) 4.0 Chatbot API
基于段永平"本分"与"平常心"哲学，通过"如实观照"帮助用户看清什么是"对的事情"，并停止那些"错的事情"
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, validator
from typing import List, Optional
import os
import json
import time
from datetime import datetime
from pathlib import Path

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 如果没有安装 python-dotenv，跳过

try:
    from .aibuilders_client import get_client
    from .system_prompt import SYSTEM_PROMPT
    from .logger_config import get_logger
except ImportError:
    from aibuilders_client import get_client
    from system_prompt import SYSTEM_PROMPT
    from logger_config import get_logger

# 初始化 logger
logger = get_logger("main")

app = FastAPI(
    title="本质看板",
    description="基于段永平'本分'与'平常心'哲学的本质看板系统——一面清澈的镜子，帮助用户通过'如实观照'看清本质",
    version="4.0.0"
)

# 判断是否为开发环境
IS_DEV = os.getenv("ENVIRONMENT", "development").lower() == "development"

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有 HTTP 请求"""
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    # 记录请求（排除静态文件）
    if not request.url.path.startswith("/static"):
        logger.info(f"收到请求 | {request.method} {request.url.path} | IP: {client_ip}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 记录响应（排除静态文件和健康检查）
        if not request.url.path.startswith("/static") and request.url.path != "/health":
            logger.info(
                f"请求完成 | {request.method} {request.url.path} | "
                f"状态: {response.status_code} | 耗时: {process_time:.3f}s"
            )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"请求异常 | {request.method} {request.url.path} | "
            f"IP: {client_ip} | 耗时: {process_time:.3f}s | 错误: {str(e)}"
        )
        raise

# 挂载静态文件目录
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# AI 客户端缓存（支持懒加载和重新加载）
_client_cache = None
_client_error = None


def get_ai_client():
    """
    获取 AI 客户端（懒加载模式）
    在开发环境中，每次调用都会重新加载环境变量
    """
    global _client_cache, _client_error
    
    # 开发环境：每次重新加载环境变量
    if IS_DEV:
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)  # override=True 确保重新加载
        except ImportError:
            pass
    
    # 如果客户端已缓存且不是开发环境，直接返回
    if _client_cache is not None and not IS_DEV:
        return _client_cache
    
    # 重新创建客户端
    try:
        _client_cache = get_client()
        _client_error = None
        ai_service = os.getenv("AI_SERVICE", "test").lower()
        if _client_cache:
            client_type = getattr(_client_cache, 'client_type', 'Unknown')
            client_url = getattr(_client_cache, 'base_url', 'Unknown')
            if IS_DEV:
                logger.info(
                    f"AI 客户端已重新加载 | 服务类型: {ai_service} | "
                    f"客户端类型: {client_type} | API URL: {client_url}"
                )
        else:
            if IS_DEV:
                logger.info(f"AI 客户端已重新加载 | 服务类型: {ai_service}")
        return _client_cache
    except ValueError as e:
        _client_cache = None
        _client_error = str(e)
        logger.warning(f"AI 客户端未配置: {e}")
        return None


def reload_config():
    """重新加载配置（清除客户端缓存）"""
    global _client_cache, _client_error
    _client_cache = None
    _client_error = None
    return get_ai_client()


# 初始化 AI 客户端（启动时）
client = get_ai_client()
if client:
    ai_service = os.getenv("AI_SERVICE", "test").lower()
    client_type = getattr(client, 'client_type', 'Unknown')
    client_url = getattr(client, 'base_url', 'Unknown')
    logger.info(
        f"AI 客户端初始化成功 | 服务类型: {ai_service} | "
        f"客户端类型: {client_type} | API URL: {client_url}"
    )
else:
    logger.warning(f"AI 客户端未配置: {_client_error or '未知错误'}")


def normalize_model_name(model: str) -> str:
    """
    根据 AI 服务类型规范化模型名称
    
    Args:
        model: 原始模型名称
        
    Returns:
        规范化后的模型名称
    """
    # 开发环境：重新加载环境变量
    if IS_DEV:
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
        except ImportError:
            pass
    
    ai_service = os.getenv("AI_SERVICE", "test").lower()
    
    if ai_service == "deepseek":
        # DeepSeek API 使用 deepseek-chat 作为默认模型
        if model == "deepseek":
            return "deepseek-chat"
        return model
    else:
        # AI Builders API 使用 deepseek 作为模型名称
        if model == "deepseek-chat":
            return "deepseek"
        return model


# ==================== 数据模型 ====================

class ChatMessage(BaseModel):
    """单条消息"""
    role: str  # "user" 或 "assistant"
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[ChatMessage]
    model: str = "deepseek"  # 使用 deepseek 模型（OpenAI 兼容）
    stream: bool = True  # 是否使用流式响应（默认启用）


class ChatResponse(BaseModel):
    """聊天响应"""
    message: ChatMessage
    model: str


class FeedbackRequest(BaseModel):
    """反馈请求"""
    message_id: str
    feedback_type: str  # "mapping_accuracy" 或 "suggestion_usefulness"
    rating: int  # 1-5 评分
    comment: Optional[str] = None  # 可选评论
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        if v not in ['mapping_accuracy', 'suggestion_usefulness']:
            raise ValueError('feedback_type must be mapping_accuracy or suggestion_usefulness')
        return v
    
    @validator('rating')
    def validate_rating(cls, v):
        if not isinstance(v, int) or v < 1 or v > 5:
            raise ValueError('rating must be an integer between 1 and 5')
        return v


class ScenarioRequest(BaseModel):
    """使用场景请求"""
    scenario: str  # "decision_before" / "review_after" / "mood_fluctuation"
    user_question_type: Optional[str] = None  # 用户问题类型（可选）
    
    @validator('scenario')
    def validate_scenario(cls, v):
        valid_scenarios = ['decision_before', 'review_after', 'mood_fluctuation']
        if v not in valid_scenarios:
            raise ValueError(f'scenario must be one of {valid_scenarios}')
        return v


# ==================== API 端点 ====================

@app.get("/")
async def root():
    """根端点 - 返回前端页面"""
    static_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    current_client = get_ai_client()
    return {
        "name": "本质看板",
        "description": "基于段永平'本分'与'平常心'哲学的本质看板系统——一面清澈的镜子，帮助用户通过'如实观照'看清什么是'对的事情'，并停止那些'错的事情'",
        "version": "4.0.0",
        "status": "running" if current_client else "not_configured"
    }


@app.get("/health")
async def health():
    """健康检查"""
    # 开发环境：重新加载环境变量
    if IS_DEV:
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
        except ImportError:
            pass
    
    current_client = get_ai_client()
    ai_service = os.getenv("AI_SERVICE", "test").lower()
    return {
        "status": "healthy",
        "client_configured": current_client is not None,
        "ai_service": ai_service,
        "environment": "development" if IS_DEV else "production"
    }


@app.post("/api/reload-config")
async def reload_config_endpoint():
    """
    重新加载配置（仅开发环境）
    修改 .env 文件后调用此端点即可生效，无需重启服务器
    """
    if not IS_DEV:
        raise HTTPException(status_code=403, detail="此功能仅在开发环境中可用")
    
    try:
        new_client = reload_config()
        ai_service = os.getenv("AI_SERVICE", "test").lower()
        logger.info(f"配置已重新加载 | 服务类型: {ai_service}")
        return {
            "status": "success",
            "message": "配置已重新加载",
            "ai_service": ai_service,
            "client_configured": new_client is not None
        }
    except Exception as e:
        logger.error(f"重新加载配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新加载配置失败: {str(e)}")


@app.post("/api/chat")
async def chat(request: ChatRequest, http_request: Request):
    """
    本质看板对话接口（支持流式响应）
    
    接收用户消息，使用系统提示词引导用户通过"如实观照"完成：
    1. 安顿与映射（Mirroring）：准确说出用户当下的情绪和处境
    2. 回归常识（Tracing）：引导用户剥离"运气、面子、短期暴利"，寻找本质
    3. 共识门槛（Consensus Gate）：在给建议前，必须先确认核心问题
    4. 微小实践（Action）：确认共识后，仅提供"把事情做对"的微小起始点
    """
    start_time = time.time()
    client_ip = http_request.client.host if http_request.client else "unknown"
    
    # 使用懒加载获取客户端（开发环境会自动重新加载配置）
    current_client = get_ai_client()
    if not current_client:
        logger.error("AI 客户端未配置")
        ai_service = os.getenv("AI_SERVICE", "test").lower()
        if ai_service == "deepseek":
            detail = "AI 客户端未配置，请设置 DEEPSEEK_API_KEY 环境变量"
        else:
            detail = "AI 客户端未配置，请设置 AI_BUILDER_TOKEN 环境变量"
        raise HTTPException(status_code=503, detail=detail)
    
    # 获取当前 AI 服务类型
    ai_service = os.getenv("AI_SERVICE", "test").lower()
    
    # 检查是否请求流式响应（优先从查询参数，其次从请求体，默认启用流式）
    stream_param = http_request.query_params.get('stream', '').lower()
    if stream_param:
        # 查询参数优先
        stream = stream_param == 'true'
    else:
        # 使用请求体中的值（默认 True）
        stream = request.stream
    
    # 记录请求信息
    message_count = len(request.messages)
    # 获取最后一条用户消息的前100个字符作为摘要
    last_user_message = ""
    if request.messages:
        last_msg = request.messages[-1]
        if last_msg.role == "user":
            last_user_message = last_msg.content[:100] + ("..." if len(last_msg.content) > 100 else "")
    
    logger.info(
        f"收到聊天请求 | IP: {client_ip} | "
        f"消息数: {message_count} | 服务类型: {ai_service} | 模型: {request.model} | 流式: {stream}"
    )
    if last_user_message:
        logger.info(f"用户消息摘要 | {last_user_message}")
    
    try:
        # 构建消息列表，确保系统提示词在最前面
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # 添加用户历史消息
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 规范化模型名称
        normalized_model = normalize_model_name(request.model)
        if normalized_model != request.model:
            logger.debug(f"模型名称规范化 | {request.model} -> {normalized_model}")
        
        # 流式响应
        if stream:
            # 确保使用最新的客户端
            stream_client = get_ai_client()
            if not stream_client:
                raise ValueError("AI 客户端未配置")
            client_type = getattr(stream_client, 'client_type', 'Unknown')
            client_url = getattr(stream_client, 'base_url', 'Unknown')
            logger.info(
                f"开始流式响应 | IP: {client_ip} | "
                f"客户端类型: {client_type} | API URL: {client_url} | "
                f"服务类型: {ai_service} | 模型: {normalized_model}"
            )
            async def generate():
                chunk_count = 0
                total_content_length = 0
                full_response_content = ""  # 用于收集完整响应
                try:
                    stream_gen = stream_client.async_chat_completion(
                        model=normalized_model,
                        messages=messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=2000  # 增加最大 token 数，允许更长的回复
                    )
                    
                    async for chunk in stream_gen:
                        chunk_count += 1
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                total_content_length += len(content)
                                full_response_content += content  # 累积完整响应
                                # 立即发送每个内容块，确保实时传输
                                event_data = json.dumps({'content': content, 'done': False}, ensure_ascii=False)
                                yield f"data: {event_data}\n\n"
                        
                        # 检查是否完成
                        if chunk.get('choices') and len(chunk['choices']) > 0:
                            finish_reason = chunk['choices'][0].get('finish_reason')
                            if finish_reason:
                                break
                    
                    # 发送完成标记
                    yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
                    
                    # 记录成功完成
                    elapsed_time = time.time() - start_time
                    logger.info(
                        f"流式响应完成 | IP: {client_ip} | "
                        f"耗时: {elapsed_time:.2f}s | 块数: {chunk_count} | 总长度: {total_content_length}"
                    )
                    
                    # 保存对话记录
                    if total_content_length > 0 and full_response_content:
                        user_msg = last_user_message if last_user_message else (request.messages[-1].content if request.messages and request.messages[-1].role == "user" else "")
                        save_chat_history(
                            user_message=user_msg,
                            assistant_message=full_response_content,
                            client_ip=client_ip,
                            message_count=message_count
                        )
                except Exception as e:
                    import traceback
                    error_msg = str(e)
                    elapsed_time = time.time() - start_time
                    logger.error(
                        f"流式响应错误 | IP: {client_ip} | 耗时: {elapsed_time:.2f}s | 错误: {error_msg}"
                    )
                    logger.debug(traceback.format_exc())
                    error_data = json.dumps({'error': error_msg, 'done': True}, ensure_ascii=False)
                    yield f"data: {error_data}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache, no-transform",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
                    "Content-Encoding": "identity"  # 确保不压缩流式数据
                }
            )
        
        # 非流式响应（兼容旧版本）
        else:
            # 确保使用最新的客户端
            non_stream_client = get_ai_client()
            if not non_stream_client:
                raise ValueError("AI 客户端未配置")
            client_type = getattr(non_stream_client, 'client_type', 'Unknown')
            client_url = getattr(non_stream_client, 'base_url', 'Unknown')
            logger.info(
                f"开始非流式响应 | IP: {client_ip} | "
                f"客户端类型: {client_type} | API URL: {client_url} | "
                f"服务类型: {ai_service} | 模型: {normalized_model}"
            )
            response_coro = non_stream_client.async_chat_completion(
                model=normalized_model,
                messages=messages,
                stream=False,
                temperature=0.7,
                max_tokens=2000  # 增加最大 token 数，允许更长的回复
            )
            response = await response_coro
            
            assistant_message = response["choices"][0]["message"]["content"]
            response_length = len(assistant_message)
            elapsed_time = time.time() - start_time
            
            # 记录响应摘要（前100个字符）
            response_preview = assistant_message[:100] + ("..." if response_length > 100 else "")
            
            logger.info(
                f"非流式响应完成 | IP: {client_ip} | "
                f"响应长度: {response_length} | 耗时: {elapsed_time:.2f}s"
            )
            logger.debug(f"响应内容预览 | {response_preview}")
            
            # 保存对话记录
            save_chat_history(
                user_message=last_user_message if last_user_message else request.messages[-1].content if request.messages else "",
                assistant_message=assistant_message,
                client_ip=client_ip,
                message_count=message_count
            )
            
            return ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content=assistant_message
                ),
                model=response.get("model", request.model)
            )
    
    except HTTPException:
        # 重新抛出 HTTP 异常（不需要记录）
        raise
    except Exception as e:
        import traceback
        elapsed_time = time.time() - start_time
        error_msg = str(e)
        logger.error(
            f"聊天请求失败 | IP: {client_ip} | 耗时: {elapsed_time:.2f}s | 错误: {error_msg}"
        )
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"聊天请求失败: {error_msg}"
        )


# ==================== 反馈和场景收集 ====================

# 数据存储目录
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
FEEDBACK_FILE = DATA_DIR / "feedback.json"
SCENARIO_FILE = DATA_DIR / "scenarios.json"
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"


def load_json_file(file_path: Path, default: list = None):
    """加载JSON文件"""
    if default is None:
        default = []
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保返回的是列表
                if not isinstance(data, list):
                    logger.warning(f"文件 {file_path} 不是列表格式，返回默认值")
                    return default
                return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败 {file_path}: {e}")
            return default
        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {e}")
            return default
    return default


def save_json_file(file_path: Path, data: list):
    """保存JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存文件失败 {file_path}: {e}")
        return False


def save_chat_history(user_message: str, assistant_message: str, client_ip: str, message_count: int):
    """
    保存对话记录
    
    Args:
        user_message: 用户消息
        assistant_message: AI 回复
        client_ip: 客户端 IP
        message_count: 消息数量（对话轮数）
    """
    try:
        chat_history = load_json_file(CHAT_HISTORY_FILE, [])
        
        chat_record = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "assistant_message": assistant_message,
            "client_ip": client_ip,
            "message_count": message_count,
            "user_message_length": len(user_message),
            "assistant_message_length": len(assistant_message)
        }
        
        chat_history.append(chat_record)
        
        # 只保留最近 1000 条记录（避免文件过大）
        if len(chat_history) > 1000:
            chat_history = chat_history[-1000:]
        
        if save_json_file(CHAT_HISTORY_FILE, chat_history):
            logger.debug(f"对话记录已保存 | IP: {client_ip} | 消息数: {message_count}")
    except Exception as e:
        logger.error(f"保存对话记录失败: {e}")


@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest, http_request: Request):
    """
    提交用户反馈
    
    反馈类型：
    - mapping_accuracy: 映射准确性（AI是否准确识别了用户的情绪和处境）
    - suggestion_usefulness: 建议有用性（AI的建议是否有用）
    """
    client_ip = http_request.client.host if http_request.client else "unknown"
    
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "message_id": request.message_id,
        "feedback_type": request.feedback_type,
        "rating": request.rating,
        "comment": request.comment,
        "ip": client_ip
    }
    
    # 加载现有反馈
    feedbacks = load_json_file(FEEDBACK_FILE, [])
    feedbacks.append(feedback_data)
    
    # 保存反馈
    if save_json_file(FEEDBACK_FILE, feedbacks):
        logger.info(
            f"收到反馈 | IP: {client_ip} | "
            f"类型: {request.feedback_type} | 评分: {request.rating}"
        )
        return {
            "status": "success",
            "message": "反馈已提交，感谢您的反馈！"
        }
    else:
        raise HTTPException(status_code=500, detail="保存反馈失败")


@app.post("/api/scenario")
async def submit_scenario(request: ScenarioRequest, http_request: Request):
    """
    提交用户使用场景
    
    场景类型：
    - decision_before: 决策前夕
    - review_after: 事后复盘
    - mood_fluctuation: 心境波动
    """
    client_ip = http_request.client.host if http_request.client else "unknown"
    
    scenario_data = {
        "timestamp": datetime.now().isoformat(),
        "scenario": request.scenario,
        "user_question_type": request.user_question_type,
        "ip": client_ip
    }
    
    # 加载现有场景数据
    scenarios = load_json_file(SCENARIO_FILE, [])
    scenarios.append(scenario_data)
    
    # 保存场景数据
    if save_json_file(SCENARIO_FILE, scenarios):
        logger.info(
            f"收到场景数据 | IP: {client_ip} | "
            f"场景: {request.scenario}"
        )
        return {
            "status": "success",
            "message": "场景信息已记录"
        }
    else:
        raise HTTPException(status_code=500, detail="保存场景数据失败")


@app.get("/api/feedback/stats")
async def get_feedback_stats():
    """获取反馈统计信息（仅开发环境）"""
    if not IS_DEV:
        raise HTTPException(status_code=403, detail="此功能仅在开发环境中可用")
    
    feedbacks = load_json_file(FEEDBACK_FILE, [])
    scenarios = load_json_file(SCENARIO_FILE, [])
    
    # 确保feedbacks和scenarios是列表
    if not isinstance(feedbacks, list):
        feedbacks = []
    if not isinstance(scenarios, list):
        scenarios = []
    
    # 计算统计信息
    mapping_accuracy = [f for f in feedbacks if isinstance(f, dict) and f.get("feedback_type") == "mapping_accuracy"]
    suggestion_usefulness = [f for f in feedbacks if isinstance(f, dict) and f.get("feedback_type") == "suggestion_usefulness"]
    
    stats = {
        "total_feedbacks": len(feedbacks),
        "mapping_accuracy": {
            "count": len(mapping_accuracy),
            "average_rating": sum(f.get("rating", 0) for f in mapping_accuracy) / len(mapping_accuracy) if mapping_accuracy else 0
        },
        "suggestion_usefulness": {
            "count": len(suggestion_usefulness),
            "average_rating": sum(f.get("rating", 0) for f in suggestion_usefulness) / len(suggestion_usefulness) if suggestion_usefulness else 0
        },
        "scenarios": {
            "total": len(scenarios),
            "decision_before": len([s for s in scenarios if isinstance(s, dict) and s.get("scenario") == "decision_before"]),
            "review_after": len([s for s in scenarios if isinstance(s, dict) and s.get("scenario") == "review_after"]),
            "mood_fluctuation": len([s for s in scenarios if isinstance(s, dict) and s.get("scenario") == "mood_fluctuation"])
        }
    }
    
    return stats


@app.get("/api/chat/history")
async def get_chat_history(
    limit: int = 50, 
    offset: int = 0, 
    token: Optional[str] = None,
    request: Request = None
):
    """
    获取对话记录
    
    Args:
        limit: 返回记录数量（默认50，最大100）
        offset: 偏移量（默认0）
        token: 访问令牌（优先从查询参数，也可从 X-Admin-Token Header）
        request: FastAPI Request 对象（用于读取 Header）
    
    注意：
    - 开发环境：可以直接访问
    - 生产环境：需要提供正确的访问令牌（通过环境变量 ADMIN_TOKEN 设置）
    - 令牌可以通过查询参数或 HTTP Header (X-Admin-Token) 传递
    """
    # 生产环境需要验证 token
    if not IS_DEV:
        admin_token = os.getenv("ADMIN_TOKEN")
        if not admin_token:
            raise HTTPException(status_code=403, detail="生产环境需要设置 ADMIN_TOKEN 环境变量")
        
        # 优先从 Header 读取令牌（更安全），其次从查询参数
        provided_token = None
        if request:
            provided_token = request.headers.get("X-Admin-Token")
        if not provided_token:
            provided_token = token
        
        if not provided_token or provided_token != admin_token:
            raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    chat_history = load_json_file(CHAT_HISTORY_FILE, [])
    
    # 确保是列表
    if not isinstance(chat_history, list):
        chat_history = []
    
    # 限制最大返回数量
    limit = min(limit, 100)
    
    # 返回最新的记录（倒序）
    total = len(chat_history)
    start = max(0, total - offset - limit)
    end = total - offset
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "records": chat_history[start:end][::-1]  # 倒序，最新的在前
    }


if __name__ == "__main__":
    import uvicorn
    # 支持 PORT 环境变量（Koyeb 部署要求）
    port = int(os.getenv("PORT", 8000))
    logger.info("=" * 60)
    logger.info("启动 FastAPI 服务器")
    logger.info(f"监听地址: 0.0.0.0:{port}")
    logger.info(f"AI 服务类型: {os.getenv('AI_SERVICE', 'test')}")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port)