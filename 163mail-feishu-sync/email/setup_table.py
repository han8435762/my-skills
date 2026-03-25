#!/usr/bin/env python3
"""
setup_table.py - 一次性脚本：创建飞书多维表格及所有字段，并将 app_token/table_id 写回 config.json
运行方式：python setup_table.py
"""

from config import load_config, save_config
import feishu_client as fc


FIELDS = [
    # (field_name, type_id)
    ("邮件ID", 1),
    ("发送时间", 5),
    ("邮件标题", 1),
    ("发件人", 1),
    ("发件人邮箱", 1),
    ("邮件正文", 1),
    ("附件", 1),
    ("是否已读", 7),
    ("交流次数", 2),
    ("标题含泵类型", 1),
    ("客户所在国家", 1),
    ("联系人姓名", 1),
    ("产品项目", 1),
    ("质检等级", 1),
    ("第几次返修", 2),
    ("备注", 1),
    ("中文内容", 1),
]


def main():
    config = load_config()

    app_token = config["feishu"].get("app_token", "").strip()
    table_id = config["feishu"].get("table_id", "").strip()

    if app_token and table_id:
        print(f"已存在配置: app_token={app_token}, table_id={table_id}")
        print("如需重新创建，请清空 config.json 中的 app_token 和 table_id")
        return

    print("正在创建多维表格 App...")
    app_token = fc.create_bitable_app(config, name="163邮件同步")
    print(f"创建成功，app_token: {app_token}")

    print("正在创建表...")
    table_id = fc.create_table(config, app_token, table_name="邮件")
    print(f"创建成功，table_id: {table_id}")

    print("正在删除默认空表...")
    for t in fc.list_tables(config, app_token):
        if t["table_id"] != table_id:
            fc.delete_table(config, app_token, t["table_id"])
            print(f"  已删除: {t['name']}")

    print("正在重命名主字段...")
    fc.rename_primary_field(config, app_token, table_id, "邮件ID")
    print("  主字段已重命名为: 邮件ID")

    print("正在创建字段...")
    for field_name, field_type in FIELDS:
        if field_name == "邮件ID":
            continue  # 主字段已重命名，跳过
        fc.create_field(config, app_token, table_id, field_name, field_type)
        print(f"  创建字段: {field_name} (type={field_type})")

    config["feishu"]["app_token"] = app_token
    config["feishu"]["table_id"] = table_id
    save_config(config)

    print("正在授予管理权限...")
    fc.grant_full_access(config, app_token)
    print("权限授予成功")
    print(f"\n配置已写入 config.json")
    print(f"app_token: {app_token}")
    print(f"table_id:  {table_id}")
    print("\n请在飞书多维表格中确认表格已创建，并开放应用权限。")


if __name__ == "__main__":
    main()
