#!/usr/bin/env python3
"""导出生产环境对话记录"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path

# 从环境变量或文件读取 ADMIN_TOKEN
def get_admin_token():
    """获取 ADMIN_TOKEN"""
    # 优先从环境变量读取
    token = os.getenv("ADMIN_TOKEN")
    if token:
        return token
    
    # 从文件读取（脚本在 scripts/ 目录，需要回到项目根目录）
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

def export_chat_history():
    """导出对话记录（使用 HTTP Header，推荐方式）"""
    print("🚀 开始导出生产环境对话记录...")
    print(f"   API: {API_URL}")
    print()
    
    all_records = []
    offset = 0
    limit = 100
    
    # 使用 HTTP Header 传递令牌（推荐）
    headers = {
        "X-Admin-Token": ADMIN_TOKEN
    }
    
    page = 1
    while True:
        print(f"📄 获取第 {page} 页（offset={offset}, limit={limit})...", end=" ")
        
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
            
            print(f"✅ 获取到 {len(records)} 条记录（总计: {total}）")
            
            if not records:
                break
            
            all_records.extend(records)
            
            if len(records) < limit:
                break
            
            offset += limit
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 错误: {e}")
            break
    
    if not all_records:
        print("\n⚠️  没有找到对话记录")
        return None
    
    # 创建备份目录（在项目根目录）
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    backup_dir = project_root / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    # 保存到文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = backup_dir / f"chat_history_export_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 60)
    print(f"✅ 导出完成！")
    print(f"   文件: {filename}")
    print(f"   记录数: {len(all_records)}")
    print(f"   文件大小: {filename.stat().st_size / 1024:.2f} KB")
    print("=" * 60)
    
    # 显示统计信息
    print("\n📊 统计信息:")
    print(f"   总记录数: {len(all_records)}")
    if all_records:
        avg_user_len = sum(r.get('user_message_length', 0) for r in all_records) / len(all_records)
        avg_assistant_len = sum(r.get('assistant_message_length', 0) for r in all_records) / len(all_records)
        print(f"   平均用户消息长度: {avg_user_len:.1f} 字符")
        print(f"   平均AI回复长度: {avg_assistant_len:.1f} 字符")
        
        # 时间范围
        timestamps = [r.get('timestamp', '') for r in all_records if r.get('timestamp')]
        if timestamps:
            print(f"   最早记录: {min(timestamps)}")
            print(f"   最新记录: {max(timestamps)}")
    
    # 显示最新几条记录预览
    print("\n📝 最新 3 条记录预览:")
    for i, record in enumerate(all_records[:3], 1):
        print(f"\n[{i}] {record.get('timestamp', 'N/A')}")
        print(f"   用户: {record.get('user_message', '')[:60]}...")
        print(f"   AI: {record.get('assistant_message', '')[:80]}...")
    
    return filename

if __name__ == "__main__":
    try:
        export_chat_history()
    except ValueError as e:
        print(f"❌ 错误: {e}")
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()
