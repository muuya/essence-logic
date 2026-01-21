"""
AI 服务客户端
支持 DeepSeek 直接调用和 AI Builders API
"""

import os
import requests
import httpx
import asyncio
from typing import Optional, Dict, List, Iterator, AsyncIterator, Any
import json

# 尝试加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 如果没有安装 python-dotenv，跳过


class AIBuildersClient:
    """AI Builders API 客户端"""
    
    def __init__(self, token: str, base_url: str = "https://space.ai-builders.com/backend"):
        """
        初始化客户端
        
        Args:
            token: Bearer token 用于认证
            base_url: API 基础 URL
        """
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.client_type = "AI Builders API"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(
        self,
        model: str = "deepseek",
        messages: List[Dict[str, str]] = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Any:
        """
        创建聊天完成请求（同步版本）
        
        Args:
            model: 模型名称，支持 deepseek, supermind-agent-v1, gemini-2.5-pro 等
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            stream: 是否使用流式响应
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
            
        Returns:
            如果 stream=False，返回完整的响应字典
            如果 stream=True，返回一个生成器，每次 yield 一个 chunk
        """
        if messages is None:
            messages = []
        
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        if stream:
            # 流式请求
            payload["stream"] = True
            return self._stream_chat_completion(url, payload)
        else:
            # 非流式请求
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
    
    def async_chat_completion(
        self,
        model: str = "deepseek",
        messages: List[Dict[str, str]] = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Any:
        """
        异步创建聊天完成请求
        
        Args:
            model: 模型名称，支持 deepseek, supermind-agent-v1, gemini-2.5-pro 等
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            stream: 是否使用流式响应
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
            
        Returns:
            如果 stream=False，返回一个协程，await 后得到完整的响应字典
            如果 stream=True，返回一个异步生成器，每次 yield 一个 chunk
        """
        if messages is None:
            messages = []
        
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        if stream:
            # 流式请求：直接返回异步生成器
            payload["stream"] = True
            return self._async_stream_chat_completion(url, payload)
        else:
            # 非流式请求：返回协程
            async def _non_stream():
                async with httpx.AsyncClient(timeout=60.0) as http_client:
                    try:
                        response = await http_client.post(
                            url,
                            headers=self.headers,
                            json=payload
                        )
                        response.raise_for_status()
                        return response.json()
                    except httpx.HTTPStatusError as e:
                        # 尝试读取错误响应
                        try:
                            error_detail = e.response.json()
                            raise Exception(f"API 请求失败 ({e.response.status_code}): {error_detail}")
                        except:
                            raise Exception(f"API 请求失败 ({e.response.status_code}): {e.response.text}")
            return _non_stream()
    
    def _stream_chat_completion(self, url: str, payload: Dict) -> Iterator[Dict]:
        """
        处理流式聊天完成请求（同步版本）
        
        Args:
            url: API URL
            payload: 请求负载
            
        Yields:
            每个 chunk 的字典
        """
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            stream=True,
            timeout=60
        )
        response.raise_for_status()
        
        # 解析 Server-Sent Events (SSE) 格式
        # SSE 格式: "data: {...}\n\n"
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            
            if line.startswith("data: "):
                data_str = line[6:]  # 移除 "data: " 前缀
                
                # 检查是否是结束标记
                if data_str.strip() == "[DONE]":
                    break
                
                try:
                    chunk = json.loads(data_str)
                    yield chunk
                except json.JSONDecodeError:
                    # 如果解析失败，跳过这个 chunk
                    continue
    
    async def _async_stream_chat_completion(self, url: str, payload: Dict) -> AsyncIterator[Dict]:
        """
        异步处理流式聊天完成请求
        
        Args:
            url: API URL
            payload: 请求负载
            
        Yields:
            每个 chunk 的字典
            
        Raises:
            httpx.HTTPStatusError: 如果 HTTP 请求失败
        """
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            try:
                async with http_client.stream(
                    "POST",
                    url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        lines = buffer.split('\n')
                        buffer = lines.pop() if lines else ""
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            if line.startswith("data: "):
                                data_str = line[6:]  # 移除 "data: " 前缀
                                
                                # 检查是否是结束标记
                                if data_str.strip() == "[DONE]":
                                    return
                                
                                try:
                                    chunk_data = json.loads(data_str)
                                    yield chunk_data
                                except json.JSONDecodeError:
                                    # 如果解析失败，跳过这个 chunk
                                    continue
            except httpx.HTTPStatusError as e:
                # 尝试读取错误响应
                try:
                    error_detail = e.response.json()
                    raise Exception(f"API 请求失败 ({e.response.status_code}): {error_detail}")
                except:
                    raise Exception(f"API 请求失败 ({e.response.status_code}): {e.response.text}")
    
    def list_models(self) -> Dict:
        """
        列出可用的模型
        
        Returns:
            模型列表响应
        """
        url = f"{self.base_url}/v1/models"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict:
        """
        健康检查
        
        Returns:
            健康状态响应
        """
        url = f"{self.base_url}/health"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def deploy(
        self,
        repo_url: str,
        service_name: str,
        branch: str = "main",
        port: int = 8000,
        env_vars: Optional[Dict[str, str]] = None,
        streaming_log_timeout_seconds: int = 60,
        **kwargs
    ) -> Dict:
        """
        部署项目到 AI Builders Space
        
        Args:
            repo_url: Git仓库URL（必须是公开的）
            service_name: 服务名称（3-32个字符，小写字母、数字、连字符）
            branch: Git分支（默认: main）
            port: 容器端口（默认: 8000）
            env_vars: 环境变量字典（可选，最多20个）
            streaming_log_timeout_seconds: 流式日志超时时间（默认: 60秒）
            **kwargs: 其他部署参数
            
        Returns:
            部署响应，包含部署状态和URL
        """
        url = f"{self.base_url}/v1/deployments"
        
        payload = {
            "repo_url": repo_url,
            "service_name": service_name,
            "branch": branch,
            "port": port,
            "streaming_log_timeout_seconds": streaming_log_timeout_seconds,
            **kwargs
        }
        
        if env_vars:
            payload["env_vars"] = env_vars
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = f"{error_msg}: {error_detail}"
                except:
                    error_msg = f"{error_msg}: {e.response.text}"
            raise Exception(f"部署失败: {error_msg}")
    
    def get_deployment_status(self, service_name: str) -> Dict:
        """
        获取部署状态
        
        Args:
            service_name: 服务名称（不是部署ID）
            
        Returns:
            部署状态信息
        """
        url = f"{self.base_url}/v1/deployments/{service_name}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = f"{error_msg}: {error_detail}"
                except:
                    error_msg = f"{error_msg}: {e.response.text}"
            raise Exception(f"获取部署状态失败: {error_msg}")
    
    def list_deployments(self) -> Dict:
        """
        列出所有部署
        
        Returns:
            部署列表
        """
        url = f"{self.base_url}/v1/deployments"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = f"{error_msg}: {error_detail}"
                except:
                    error_msg = f"{error_msg}: {e.response.text}"
            raise Exception(f"列出部署失败: {error_msg}")
    
    def get_deployment_logs(self, service_name: str) -> str:
        """
        获取部署日志
        
        Args:
            service_name: 服务名称
            
        Returns:
            日志内容
        """
        url = f"{self.base_url}/v1/deployments/{service_name}/logs"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = f"{error_msg}: {error_detail}"
                except:
                    error_msg = f"{error_msg}: {e.response.text}"
            raise Exception(f"获取部署日志失败: {error_msg}")


class DeepSeekClient:
    """DeepSeek API 客户端（OpenAI 兼容）"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化 DeepSeek 客户端
        
        Args:
            api_key: DeepSeek API Key
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.client_type = "DeepSeek API"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(
        self,
        model: str = "deepseek-chat",
        messages: List[Dict[str, str]] = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Any:
        """
        创建聊天完成请求（同步版本）
        
        Args:
            model: 模型名称，支持 deepseek-chat, deepseek-reasoner 等
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            stream: 是否使用流式响应
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
            
        Returns:
            如果 stream=False，返回完整的响应字典
            如果 stream=True，返回一个生成器，每次 yield 一个 chunk
        """
        if messages is None:
            messages = []
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        if stream:
            payload["stream"] = True
            return self._stream_chat_completion(url, payload)
        else:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
    
    def async_chat_completion(
        self,
        model: str = "deepseek-chat",
        messages: List[Dict[str, str]] = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Any:
        """
        异步创建聊天完成请求
        
        Args:
            model: 模型名称，支持 deepseek-chat, deepseek-reasoner 等
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            stream: 是否使用流式响应
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
            
        Returns:
            如果 stream=False，返回一个协程，await 后得到完整的响应字典
            如果 stream=True，返回一个异步生成器，每次 yield 一个 chunk
        """
        if messages is None:
            messages = []
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        if stream:
            payload["stream"] = True
            return self._async_stream_chat_completion(url, payload)
        else:
            async def _non_stream():
                async with httpx.AsyncClient(timeout=60.0) as http_client:
                    try:
                        response = await http_client.post(
                            url,
                            headers=self.headers,
                            json=payload
                        )
                        response.raise_for_status()
                        return response.json()
                    except httpx.HTTPStatusError as e:
                        try:
                            error_detail = e.response.json()
                            raise Exception(f"API 请求失败 ({e.response.status_code}): {error_detail}")
                        except:
                            raise Exception(f"API 请求失败 ({e.response.status_code}): {e.response.text}")
            return _non_stream()
    
    def _stream_chat_completion(self, url: str, payload: Dict) -> Iterator[Dict]:
        """处理流式聊天完成请求（同步版本）"""
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            stream=True,
            timeout=60
        )
        response.raise_for_status()
        
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                
                try:
                    chunk = json.loads(data_str)
                    yield chunk
                except json.JSONDecodeError:
                    continue
    
    async def _async_stream_chat_completion(self, url: str, payload: Dict) -> AsyncIterator[Dict]:
        """异步处理流式聊天完成请求"""
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            try:
                async with http_client.stream(
                    "POST",
                    url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        lines = buffer.split('\n')
                        buffer = lines.pop() if lines else ""
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str.strip() == "[DONE]":
                                    return
                                
                                try:
                                    chunk_data = json.loads(data_str)
                                    yield chunk_data
                                except json.JSONDecodeError:
                                    continue
            except httpx.HTTPStatusError as e:
                try:
                    error_detail = e.response.json()
                    raise Exception(f"API 请求失败 ({e.response.status_code}): {error_detail}")
                except:
                    raise Exception(f"API 请求失败 ({e.response.status_code}): {e.response.text}")


def get_client():
    """
    根据环境变量配置创建 AI 客户端实例
    
    环境变量:
        AI_SERVICE: 服务类型，可选值:
            - "deepseek": 直接调用 DeepSeek API
            - "test": 通过 AI Builders API 调用（默认）
        DEEPSEEK_API_KEY: DeepSeek API Key（当 AI_SERVICE=deepseek 时必需）
        AI_BUILDER_TOKEN: AI Builders Token（当 AI_SERVICE=test 时必需）
    
    Returns:
        DeepSeekClient 或 AIBuildersClient 实例
        
    Raises:
        ValueError: 如果必需的环境变量未设置
    """
    # 开发环境：重新加载环境变量
    is_dev = os.getenv("ENVIRONMENT", "development").lower() == "development"
    if is_dev:
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
        except ImportError:
            pass
    
    ai_service = os.getenv("AI_SERVICE", "test").lower()
    
    if ai_service == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY 环境变量未设置。"
                "请设置环境变量: export DEEPSEEK_API_KEY='your_api_key_here'"
            )
        
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        client = DeepSeekClient(api_key=api_key, base_url=base_url)
        # 记录客户端创建信息
        try:
            from .logger_config import get_logger
        except ImportError:
            from logger_config import get_logger
        logger = get_logger("aibuilders_client")
        logger.info(f"已创建 DeepSeek 客户端 | API URL: {base_url}")
        return client
    
    elif ai_service == "test":
        token = os.getenv("AI_BUILDER_TOKEN")
        if not token:
            raise ValueError(
                "AI_BUILDER_TOKEN 环境变量未设置。"
                "请设置环境变量: export AI_BUILDER_TOKEN='your_token_here'"
            )
        
        base_url = os.getenv("AI_BUILDER_BASE_URL", "https://space.ai-builders.com/backend")
        client = AIBuildersClient(token=token, base_url=base_url)
        # 记录客户端创建信息
        try:
            from .logger_config import get_logger
        except ImportError:
            from logger_config import get_logger
        logger = get_logger("aibuilders_client")
        logger.info(f"已创建 AI Builders 客户端 | API URL: {base_url}")
        return client
    
    else:
        raise ValueError(
            f"无效的 AI_SERVICE 值: {ai_service}。"
            "有效值: 'deepseek' 或 'test'"
        )
