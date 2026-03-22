#!/usr/bin/env python3
"""
163邮件同步主脚本
获取邮件 -> 写入飞书多维表格 -> 发送通知
"""

import json
import sys
import os
from datetime import datetime

# 导入邮件获取模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from fetch_emails import fetch_emails, format_email_for_feishu, load_config, clean_email

def create_feishu_record(app_token, table_id, email_data):
    """
    创建飞书多维表格记录
    注意：这个函数需要通过OpenClaw的feishu_bitable_create_record调用
    """
    # 这里返回格式化的数据，由OpenClaw调用feishu_bitable_create_record
    return email_data

def sync_emails_to_feishu():
    """主同步流程"""
    print("==========================================")
    print("163邮件同步开始")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==========================================")

    # 1. 加载配置
    config = load_config()

    # 2. 检查飞书表格配置
    if not config.get('feishu_table_token') or not config.get('feishu_table_id'):
        print("⚠️  飞书多维表格未配置")
        print("请先创建飞书多维表格并更新config.json:")
        print("  feishu_table_token: <表格token>")
        print("  feishu_table_id: <子表ID>")
        return []

    # 3. 获取新邮件
    emails = fetch_emails(config, limit=20)

    if not emails:
        print("没有新邮件需要同步")
        return []

    # 4. 格式化邮件数据并更新跟踪计数
    formatted_emails = []
    for email_info in emails:
        formatted = format_email_for_feishu(email_info)
        formatted_emails.append(formatted)

        # 更新跟踪计数
        from_email = clean_email(email_info['from'])
        from fetch_emails import update_repair_count
        new_count = update_repair_count(from_email)
        print(f"更新跟踪计数: {from_email} -> 第 {new_count} 次")

    # 5. 写入飞书多维表格
    # 注意：这里需要通过OpenClaw调用feishu_bitable_create_record
    print(f"\n准备写入 {len(formatted_emails)} 封邮件到飞书多维表格")

    # 保存到JSON文件供OpenClaw读取
    sync_file = os.path.join(os.path.dirname(__file__), '..', 'sync_queue.json')
    sync_data = {
        'app_token': config['feishu_table_token'],
        'table_id': config['feishu_table_id'],
        'records': formatted_emails,
        'sync_time': datetime.now().isoformat()
    }

    with open(sync_file, 'w', encoding='utf-8') as f:
        json.dump(sync_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 同步数据已保存: {sync_file}")
    print("\n请通过OpenClaw助手执行:")
    print("1. 读取 sync_queue.json")
    print("2. 批量调用 feishu_bitable_create_record 写入记录")
    print("3. 发送飞书个人通知")

    # 6. 生成通知摘要
    summary = []
    for email_info in emails:
        summary.append({
            'subject': email_info['subject'],
            'from': email_info['from'],
            'date': email_info['date']
        })

    return summary

if __name__ == "__main__":
    summary = sync_emails_to_feishu()

    if summary:
        print(f"\n==========================================")
        print(f"同步完成！共处理 {len(summary)} 封新邮件")
        print("==========================================")
        for i, item in enumerate(summary, 1):
            print(f"\n{i}. {item['subject']}")
            print(f"   发件人: {item['from']}")
    else:
        print("\n同步完成，无需处理新邮件")
