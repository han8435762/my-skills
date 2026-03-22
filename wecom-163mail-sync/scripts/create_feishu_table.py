#!/usr/bin/env python3
"""
创建飞书多维表格用于存储163邮件
"""

import json
import sys
import os

# 添加OpenClaw路径以便导入
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace'))

def create_feishu_bitable():
    """
    通过OpenClaw的feishu_bitable_create_app创建多维表格
    这个脚本会被OpenClaw调用，通过subprocess执行
    """
    print("开始创建飞书多维表格...")

    # 表格配置
    table_name = "163邮件同步表"
    fields = [
        {
            "field_name": "邮件ID",
            "field_type": 1,  # Text
            "property": {
                "default": ""
            }
        },
        {
            "field_name": "发件人",
            "field_type": 1,  # Text
            "property": {
                "default": ""
            }
        },
        {
            "field_name": "发件人邮箱",
            "field_type": 1,  # Text
            "property": {
                "default": ""
            }
        },
        {
            "field_name": "收件人",
            "field_type": 1,  # Text
            "property": {
                "default": ""
            }
        },
        {
            "field_name": "主题",
            "field_type": 1,  # Text
            "property": {
                "default": ""
            }
        },
        {
            "field_name": "发送时间",
            "field_type": 5,  # DateTime
            "property": {
                "format": "yyyy-MM-dd HH:mm",
                "default": "0"
            }
        },
        {
            "field_name": "邮件正文",
            "field_type": 1,  # Text
            "property": {
                "default": ""
            }
        },
        {
            "field_name": "同步时间",
            "field_type": 5,  # DateTime
            "property": {
                "format": "yyyy-MM-dd HH:mm",
                "default": "0"
            }
        },
        {
            "field_name": "是否已读",
            "field_type": 7,  # Checkbox
            "property": {
                "default": False
            }
        },
        {
            "field_name": "邮件标签",
            "field_type": 4,  # MultiSelect
            "property": {
                "options": [
                    {"name": "客户"},
                    {"name": "询盘"},
                    {"name": "订单"},
                    {"name": "其他"}
                ]
            }
        }
    ]

    # 输出配置供OpenClaw使用
    config = {
        "table_name": table_name,
        "fields": fields
    }

    # 保存到文件供后续使用
    config_file = os.path.join(os.path.dirname(__file__), '..', 'feishu_table_config.json')
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"✅ 表格配置已生成: {config_file}")
    print("\n请通过OpenClaw助手执行以下步骤:")
    print("1. 使用 feishu_bitable_create_app 创建多维表格")
    print("2. 使用 feishu_bitable_create_field 创建字段")
    print("3. 将app_token和table_id保存到config.json")

    return config

if __name__ == "__main__":
    create_feishu_bitable()
