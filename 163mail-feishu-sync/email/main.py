#!/usr/bin/env python3
"""
main.py - 主入口：同步163邮箱到飞书多维表格

用法:
  python main.py          # 增量同步（最近6小时）
  python main.py --init   # 初始同步（最近10天）
"""

import argparse
import sys

from config import load_config
import imap_client
import feishu_client as fc
import minimax_client as mm
import sync_state


def build_record_fields(email_info, ai_fields, exchange_count):
    """将邮件信息和AI字段组合成飞书记录字段"""
    body_preview = email_info["body"][:2000] if email_info["body"] else ""
    attachments_str = "; ".join(email_info["attachments"])

    fields = {
        "邮件ID": email_info["message_id"],
        "发送时间": email_info["timestamp_ms"],
        "邮件标题": email_info["subject"],
        "发件人": email_info["from_name"],
        "发件人邮箱": email_info["from_email"],
        "邮件正文": body_preview,
        "附件": attachments_str,
        "是否已读": False,
        "交流次数": exchange_count,
        "标题含泵类型": ai_fields["pump_type_in_subject"],
        "客户所在国家": ai_fields["country"],
        "联系人姓名": ai_fields["contact_name"],
        "产品项目": ai_fields["product_type"],
        "质检等级": ai_fields["quality_grade"],
        "第几次返修": ai_fields["repair_count"],
        "备注": ai_fields["notes"],
        "中文内容": ai_fields["chinese_content"],
    }
    return fields


def sync(config, init_mode=False):
    app_token = config["feishu"]["app_token"]
    table_id = config["feishu"]["table_id"]

    if not app_token or not table_id:
        print("错误：config.json 中 app_token 或 table_id 为空，请先运行 python setup_table.py")
        sys.exit(1)

    if init_mode:
        print("初始模式：获取最近10天邮件")
        emails = imap_client.fetch_emails(config, days=10)
    else:
        print("增量模式：获取最近6小时邮件")
        emails = imap_client.fetch_emails(config, hours=6)

    if not emails:
        print("没有找到邮件，退出")
        return

    new_count = 0
    for email_info in emails:
        message_id = email_info["message_id"]

        if not message_id:
            print(f"跳过无 Message-ID 的邮件: {email_info['subject'][:50]}")
            continue

        # 本地去重
        if sync_state.is_synced(message_id):
            print(f"已同步（本地），跳过: {email_info['subject'][:50]}")
            continue

        # 飞书表格去重（双重保险）
        if fc.record_exists_by_email_id(config, app_token, table_id, message_id):
            print(f"已同步（飞书），跳过: {email_info['subject'][:50]}")
            sync_state.mark_synced(message_id)
            continue

        print(f"处理邮件: {email_info['subject'][:60]}")

        # 计算交流次数
        exchange_count = fc.count_records_by_email(
            config, app_token, table_id, email_info["from_email"]
        )

        # AI 提取字段
        ai_fields = mm.extract_ai_fields(
            config,
            subject=email_info["subject"],
            from_name=email_info["from_name"],
            from_email=email_info["from_email"],
            body=email_info["body"],
        )

        # 组装记录字段
        fields = build_record_fields(email_info, ai_fields, exchange_count)

        # 写入飞书
        try:
            record_id = fc.create_record(config, app_token, table_id, fields)
            sync_state.mark_synced(message_id)
            new_count += 1
            print(f"  已写入记录: {record_id}")
        except Exception as e:
            print(f"  写入失败: {e}")

    print(f"\n同步完成，新增 {new_count} 封邮件")

    # 发飞书通知
    if new_count > 0:
        try:
            fc.send_notification(config, f"163邮箱同步完成：新增 {new_count} 封邮件，请查看飞书多维表格。")
            print("飞书通知已发送")
        except Exception as e:
            print(f"发送通知失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="163邮箱同步到飞书多维表格")
    parser.add_argument("--init", action="store_true", help="初始同步（最近10天）")
    args = parser.parse_args()

    config = load_config()
    sync(config, init_mode=args.init)


if __name__ == "__main__":
    main()
