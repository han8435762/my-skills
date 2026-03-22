#!/usr/bin/env python3
"""
测试163邮件同步功能
"""

import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from fetch_emails import fetch_emails, format_email_for_feishu, load_config

def test_sync():
    """测试同步流程"""
    print("==========================================")
    print("测试163邮件同步")
    print("==========================================\n")

    # 1. 加载配置
    print("1. 加载配置...")
    config = load_config()

    if config['email'] == 'your_email@163.com':
        print("❌ 请先配置你的163邮箱地址")
        print("编辑 config.json，将 your_email@163.com 改为你的实际邮箱")
        return False

    print(f"✅ 邮箱: {config['email']}")
    print(f"✅ IMAP: {config['imap_server']}:{config['imap_port']}")
    print(f"✅ 飞书表格: {config['feishu_table_token']}")

    # 2. 测试IMAP连接
    print("\n2. 测试IMAP连接...")
    try:
        import imaplib
        imap_server = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
        imap_server.login(config['email'], config['imap_password'])
        imap_server.select('INBOX')
        imap_server.close()
        imap_server.logout()
        print("✅ IMAP连接成功！")
    except Exception as e:
        print(f"❌ IMAP连接失败: {e}")
        print("\n请检查:")
        print("1. 163邮箱是否开启IMAP服务")
        print("2. 授权码是否正确")
        return False

    # 3. 获取新邮件（测试模式，只获取5封）
    print("\n3. 获取新邮件（测试模式，最多5封）...")
    emails = fetch_emails(config, limit=5)

    if not emails:
        print("ℹ️  没有新邮件（或已全部同步）")
        return True

    print(f"✅ 获取到 {len(emails)} 封新邮件")

    # 4. 格式化邮件数据
    print("\n4. 格式化邮件数据...")
    formatted_emails = []
    for i, email_info in enumerate(emails, 1):
        formatted = format_email_for_feishu(email_info)
        formatted_emails.append(formatted)
        print(f"\n邮件 {i}:")
        print(f"  主题: {email_info['subject']}")
        print(f"  发件人: {email_info['from']}")
        print(f"  时间: {email_info['date']}")
        print(f"  正文长度: {len(email_info['body'])} 字符")

    # 5. 保存同步数据
    print("\n5. 保存同步数据...")
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
    print(f"   共 {len(formatted_emails)} 条记录待写入")

    # 6. 生成报告
    print("\n==========================================")
    print("测试完成！")
    print("==========================================")
    print("\n下一步:")
    print("1. 查看同步数据: cat sync_queue.json")
    print("2. 通过OpenClaw助手写入飞书多维表格")
    print("3. 设置定期自动同步（每10分钟）")
    print("\n提示: 首次同步建议手动测试，确认无误后再开启自动同步")

    return True

if __name__ == "__main__":
    success = test_sync()
    sys.exit(0 if success else 1)
