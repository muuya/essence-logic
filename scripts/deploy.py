#!/usr/bin/env python3
"""
部署脚本 - 将项目部署到 AI Builders Space
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Dict

# 添加 src 目录到路径（脚本在 scripts/ 目录，需要回到项目根目录）
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 切换到项目根目录（确保相对路径正确）
os.chdir(project_root)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from aibuilders_client import AIBuildersClient, get_client


def load_project_config(config_path: Optional[str] = None) -> Dict:
    """
    加载项目配置
    
    Args:
        config_path: 配置文件路径（可选）
        
    Returns:
        项目配置字典
    """
    if config_path:
        # 如果是相对路径，尝试多个位置
        if not os.path.isabs(config_path):
            # 1. 当前目录
            if os.path.exists(config_path):
                pass
            # 2. config/ 目录
            elif os.path.exists(f"config/{config_path}"):
                config_path = f"config/{config_path}"
            # 3. 项目根目录
            elif os.path.exists(f"../{config_path}"):
                config_path = f"../{config_path}"
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    # 默认配置
    return {
        "name": "essence-logic",
        "display_name": "本质看板",
        "description": "基于段永平'本分'与'平常心'哲学的本质看板系统",
        "version": "4.0.0",
        "environment": "production"
    }


def get_project_info() -> Dict:
    """
    从项目文件获取项目信息
    
    Returns:
        项目信息字典
    """
    project_info = {
        "name": "essence-logic",
        "display_name": "本质看板",
        "description": "基于段永平'本分'与'平常心'哲学的本质看板系统",
        "version": "4.0.0"
    }
    
    # 尝试从 main.py 读取版本信息
    main_py = Path(__file__).parent / "src" / "main.py"
    if main_py.exists():
        content = main_py.read_text(encoding='utf-8')
        if 'version="' in content:
            import re
            match = re.search(r'version="([^"]+)"', content)
            if match:
                project_info["version"] = match.group(1)
    
    return project_info


def deploy_project(
    client: AIBuildersClient,
    repo_url: str,
    service_name: str,
    branch: str = "main",
    port: int = 8000,
    env_vars: Optional[Dict[str, str]] = None,
    wait: bool = True,
    timeout: int = 600
) -> Dict:
    """
    部署项目
    
    Args:
        client: AIBuildersClient 实例
        repo_url: Git 仓库 URL（必须是公开的）
        service_name: 服务名称（3-32个字符，小写字母、数字、连字符）
        branch: Git 分支（默认: main）
        port: 容器端口（默认: 8000）
        env_vars: 环境变量字典（可选）
        wait: 是否等待部署完成
        timeout: 超时时间（秒，默认600秒=10分钟）
        
    Returns:
        部署结果
    """
    print(f"🚀 开始部署项目")
    print(f"   仓库: {repo_url}")
    print(f"   服务名: {service_name}")
    print(f"   分支: {branch}")
    print(f"   端口: {port}")
    if env_vars:
        print(f"   环境变量: {len(env_vars)} 个")
    print()
    
    try:
        # 执行部署
        print("📦 正在提交部署请求...")
        deploy_response = client.deploy(
            repo_url=repo_url,
            service_name=service_name,
            branch=branch,
            port=port,
            env_vars=env_vars,
            streaming_log_timeout_seconds=60
        )
        
        print(f"✅ 部署请求已提交 (202 Accepted)")
        print(f"   服务名: {deploy_response.get('service_name', service_name)}")
        print(f"   状态: {deploy_response.get('status', 'unknown')}")
        
        if deploy_response.get('streaming_logs'):
            print(f"\n📋 初始构建日志:")
            print("-" * 60)
            print(deploy_response['streaming_logs'])
            print("-" * 60)
        
        if deploy_response.get('public_url'):
            print(f"\n🌐 访问地址: {deploy_response['public_url']}")
        
        if deploy_response.get('message'):
            print(f"\n💡 {deploy_response['message']}")
        
        print()
        
        service_name = deploy_response.get("service_name", service_name)
        
        if wait:
            print(f"⏳ 等待部署完成 (超时: {timeout}秒)...")
            print(f"   提示: 部署通常需要 5-10 分钟")
            print()
            
            start_time = time.time()
            last_status = None
            while time.time() - start_time < timeout:
                try:
                    status = client.get_deployment_status(service_name)
                    status_str = status.get("status", "unknown")
                    
                    # 只在状态变化时打印
                    if status_str != last_status:
                        print(f"   状态: {status_str}")
                        last_status = status_str
                    
                    # Koyeb 状态表示部署完成
                    if status_str in ["HEALTHY", "UNHEALTHY", "DEGRADED", "SLEEPING", "ERROR"]:
                        print()
                        if status_str == "HEALTHY":
                            print(f"✅ 部署成功!")
                            if status.get('public_url'):
                                print(f"   🌐 访问地址: {status['public_url']}")
                            if status.get('git_commit_id'):
                                print(f"   📝 Git Commit: {status['git_commit_id'][:8]}")
                        else:
                            print(f"⚠️  部署状态: {status_str}")
                            if status.get('message'):
                                print(f"   信息: {status['message']}")
                        return status
                    
                    # 如果还在工作流状态，继续等待
                    if status_str in ["queued", "deploying"]:
                        time.sleep(10)  # 每10秒检查一次
                    else:
                        time.sleep(5)
                        
                except Exception as e:
                    print(f"\n⚠️  查询状态时出错: {e}")
                    time.sleep(5)
            
            print()
            print(f"⏱️  超时: 部署未在 {timeout} 秒内完成")
            print(f"   服务名: {service_name}")
            print(f"   请稍后使用以下命令查询状态:")
            print(f"   python scripts/deploy.py --status {service_name}")
            return {"service_name": service_name, "status": "timeout"}
        else:
            return deploy_response
            
    except Exception as e:
        print(f"❌ 部署失败: {e}")
        raise


def list_deployments(client: AIBuildersClient):
    """列出所有部署"""
    print("📋 获取部署列表...")
    try:
        deployments = client.list_deployments()
        print(json.dumps(deployments, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 获取部署列表失败: {e}")
        raise


def get_status(client: AIBuildersClient, service_name: str):
    """获取部署状态"""
    print(f"📊 查询部署状态: {service_name}")
    try:
        status = client.get_deployment_status(service_name)
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        if status.get('public_url'):
            print(f"\n🌐 访问地址: {status['public_url']}")
        if status.get('status'):
            print(f"   状态: {status['status']}")
    except Exception as e:
        print(f"❌ 查询状态失败: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="部署本质看板项目到 AI Builders Space"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径（JSON格式）"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="不等待部署完成"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="等待超时时间（秒，默认300）"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有部署"
    )
    parser.add_argument(
        "--status",
        type=str,
        help="查询指定部署ID的状态"
    )
    parser.add_argument(
        "--repo-url",
        type=str,
        help="Git 仓库 URL（必需，必须是公开的）"
    )
    parser.add_argument(
        "--service-name",
        type=str,
        help="服务名称（3-32个字符，小写字母、数字、连字符）"
    )
    parser.add_argument(
        "--branch",
        type=str,
        default="main",
        help="Git 分支（默认: main）"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="容器端口（默认: 8000）"
    )
    
    args = parser.parse_args()
    
    # 检查环境变量
    token = os.getenv("AI_BUILDER_TOKEN")
    if not token:
        print("❌ 错误: 未设置 AI_BUILDER_TOKEN 环境变量")
        print("   请设置: export AI_BUILDER_TOKEN='your_token_here'")
        sys.exit(1)
    
    base_url = os.getenv("AI_BUILDER_BASE_URL", "https://space.ai-builders.com/backend")
    
    # 创建客户端
    try:
        client = AIBuildersClient(token=token, base_url=base_url)
    except Exception as e:
        print(f"❌ 创建客户端失败: {e}")
        sys.exit(1)
    
    # 列出部署
    if args.list:
        list_deployments(client)
        return
    
    # 查询状态
    if args.status:
        get_status(client, args.status)
        return
    
    # 执行部署
    try:
        # 检查必需参数
        repo_url = args.repo_url
        service_name = args.service_name
        
        # 处理配置文件路径
        config_path = args.config
        if config_path:
            # 如果没有指定路径，尝试默认位置
            if not os.path.exists(config_path):
                # 尝试 config/ 目录
                alt_path = project_root / "config" / os.path.basename(config_path)
                if alt_path.exists():
                    config_path = str(alt_path)
                # 尝试项目根目录
                elif (project_root / os.path.basename(config_path)).exists():
                    config_path = str(project_root / os.path.basename(config_path))
        
        if not repo_url:
            # 尝试从配置文件读取
            project_config = load_project_config(config_path)
            repo_url = project_config.get("repo_url")
        
        if not repo_url:
            print("❌ 错误: 需要提供 Git 仓库 URL")
            print("   使用方法:")
            print("   python scripts/deploy.py --repo-url https://github.com/user/repo --service-name my-app")
            print("   或在配置文件中设置 repo_url")
            sys.exit(1)
        
        if not service_name:
            # 尝试从配置文件或项目名生成
            project_config = load_project_config(config_path)
            service_name = project_config.get("service_name") or project_config.get("name", "essence-logic")
            # 确保服务名符合要求（小写、数字、连字符，3-32字符）
            import re
            service_name = re.sub(r'[^a-z0-9-]', '-', service_name.lower())
            service_name = service_name[:32]
            if len(service_name) < 3:
                service_name = "essence-logic"
        
        # 加载环境变量（如果有配置文件）
        env_vars = None
        if config_path:
            project_config = load_project_config(config_path)
            if project_config.get("env_vars"):
                env_vars = project_config["env_vars"]
        
        # 执行部署
        result = deploy_project(
            client=client,
            repo_url=repo_url,
            service_name=service_name,
            branch=args.branch,
            port=args.port,
            env_vars=env_vars,
            wait=not args.no_wait,
            timeout=args.timeout
        )
        
        print()
        print("=" * 60)
        print("部署完成!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  部署已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 部署失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
