#!/usr/bin/env python3
"""合并所有备份文件，去重后生成完整导出"""

import json
from pathlib import Path
from datetime import datetime
from collections import OrderedDict

def merge_all_backups():
    """合并所有备份文件"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    backup_dir = project_root / "backups"
    
    if not backup_dir.exists():
        print("❌ backups 目录不存在")
        return
    
    # 获取所有备份文件
    backup_files = sorted(backup_dir.glob("chat_history_export_*.json"), reverse=True)
    
    if not backup_files:
        print("⚠️  没有找到备份文件")
        return
    
    print(f"📁 找到 {len(backup_files)} 个备份文件")
    print()
    
    # 使用 OrderedDict 去重（按 timestamp + user_message 作为唯一键）
    all_records = OrderedDict()
    
    for backup_file in backup_files:
        print(f"📄 读取: {backup_file.name}")
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
                if not isinstance(records, list):
                    records = [records]
                
                for record in records:
                    # 使用 timestamp + user_message 作为唯一键
                    key = f"{record.get('timestamp', '')}_{record.get('user_message', '')}"
                    if key not in all_records:
                        all_records[key] = record
                    else:
                        # 如果已存在，保留时间戳更早的（更完整的记录）
                        existing = all_records[key]
                        if record.get('timestamp', '') < existing.get('timestamp', ''):
                            all_records[key] = record
                
                print(f"   ✅ 读取 {len(records)} 条记录")
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
    
    if not all_records:
        print("\n⚠️  没有找到任何记录")
        return
    
    # 转换为列表并按时间戳排序（最新的在前）
    merged_records = list(all_records.values())
    merged_records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    print()
    print(f"📊 合并结果:")
    print(f"   去重后记录数: {len(merged_records)}")
    
    # 保存合并后的文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = backup_dir / f"chat_history_merged_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_records, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 60)
    print(f"✅ 合并完成！")
    print(f"   文件: {output_file}")
    print(f"   记录数: {len(merged_records)}")
    print(f"   文件大小: {output_file.stat().st_size / 1024:.2f} KB")
    print("=" * 60)
    
    # 显示统计信息
    print("\n📊 统计信息:")
    print(f"   总记录数: {len(merged_records)}")
    if merged_records:
        avg_user_len = sum(r.get('user_message_length', 0) for r in merged_records) / len(merged_records)
        avg_assistant_len = sum(r.get('assistant_message_length', 0) for r in merged_records) / len(merged_records)
        print(f"   平均用户消息长度: {avg_user_len:.1f} 字符")
        print(f"   平均AI回复长度: {avg_assistant_len:.1f} 字符")
        
        timestamps = [r.get('timestamp', '') for r in merged_records if r.get('timestamp')]
        if timestamps:
            print(f"   最早记录: {min(timestamps)}")
            print(f"   最新记录: {max(timestamps)}")
    
    # 显示所有记录列表
    print("\n📝 所有记录列表:")
    for i, record in enumerate(merged_records, 1):
        timestamp = record.get('timestamp', 'N/A')
        user_msg = record.get('user_message', '')[:50]
        print(f"   [{i}] {timestamp} | {user_msg}...")
    
    return output_file

if __name__ == "__main__":
    try:
        merge_all_backups()
    except Exception as e:
        print(f"❌ 合并失败: {e}")
        import traceback
        traceback.print_exc()
