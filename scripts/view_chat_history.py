#!/usr/bin/env python3
"""查看生产环境对话记录（格式化显示）"""

import requests
import json
import os
from pathlib import Path
from datetime import datetime

# 从环境变量或文件读取 ADMIN_TOKEN
def get_admin_token():
    """获取 ADMIN_TOKEN"""
    token = os.getenv("ADMIN_TOKEN")
    if token:
        return token
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    token_file = project_root / "ADMIN_TOKEN.txt"
    if token_file.exists():
        with open(token_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("ADMIN_TOKEN:"):
                    return line.split(":", 1)[1].strip()
    
    raise ValueError("未找到 ADMIN_TOKEN，请设置环境变量或确保 ADMIN_TOKEN.txt 文件存在")

ADMIN_TOKEN = get_admin_token()
API_URL = "https://essence-logic.ai-builders.space/api/chat/history"

def view_chat_history(limit=50, offset=0):
    """查看对话记录"""
    print("=" * 80)
    print("📋 生产环境对话记录")
    print("=" * 80)
    print(f"API: {API_URL}")
    print(f"限制: {limit} 条 | 偏移: {offset}")
    print()
    
    headers = {
        "X-Admin-Token": ADMIN_TOKEN
    }
    
    try:
        response = requests.get(
            API_URL,
            headers=headers,
            params={"limit": limit, "offset": offset},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        records = data.get("records", [])
        total = data.get("total", 0)
        
        if not records:
            print("⚠️  没有找到对话记录")
            return
        
        print(f"📊 共找到 {total} 条记录，显示 {len(records)} 条\n")
        
        for i, record in enumerate(records, 1):
            timestamp = record.get('timestamp', 'N/A')
            user_msg = record.get('user_message', '')
            assistant_msg = record.get('assistant_message', '')
            
            # 格式化时间
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = timestamp
            
            print("-" * 80)
            print(f"[{i}] {time_str}")
            print(f"   用户消息 ({record.get('user_message_length', 0)} 字符):")
            print(f"   {user_msg}")
            print()
            print(f"   AI 回复 ({record.get('assistant_message_length', 0)} 字符):")
            # 显示前 200 字符，如果更长则显示省略号
            if len(assistant_msg) > 200:
                print(f"   {assistant_msg[:200]}...")
            else:
                print(f"   {assistant_msg}")
            print()
        
        print("=" * 80)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   状态码: {e.response.status_code}")
            print(f"   响应: {e.response.text[:200]}")

if __name__ == "__main__":
    import sys
    
    limit = 50
    offset = 0
    
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    if len(sys.argv) > 2:
        offset = int(sys.argv[2])
    
    try:
        view_chat_history(limit=limit, offset=offset)
    except ValueError as e:
        print(f"❌ 错误: {e}")
    except Exception as e:
        print(f"❌ 查看失败: {e}")
        import traceback
        traceback.print_exc()
