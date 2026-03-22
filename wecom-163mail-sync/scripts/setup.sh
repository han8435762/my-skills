#!/bin/bash
# 163邮件同步技能 - 首次设置脚本

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SKILL_DIR/config.json"

echo "=========================================="
echo "163邮件同步技能 - 首次设置"
echo "=========================================="
echo ""

# 检查配置文件是否存在
if [ -f "$CONFIG_FILE" ]; then
    echo "配置文件已存在: $CONFIG_FILE"
    read -p "是否重新配置？(y/n): " redo
    if [ "$redo" != "y" ]; then
        echo "保持现有配置"
        exit 0
    fi
fi

# 输入163邮箱地址
echo ""
echo "请输入你的163邮箱地址:"
read -p "邮箱: " email_addr

if [ -z "$email_addr" ]; then
    echo "邮箱地址不能为空"
    exit 1
fi

# 验证是否为163邮箱
if [[ ! $email_addr =~ @163\.com$ ]]; then
    echo "警告: 这不是163邮箱地址，可能无法使用163的IMAP服务"
    read -p "继续吗？(y/n): " cont
    if [ "$cont" != "y" ]; then
        exit 1
    fi
fi

# 复制模板并配置
cp "$SKILL_DIR/config.json.template" "$CONFIG_FILE"

# 使用sed替换邮箱地址（需要处理macOS和Linux的sed差异）
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/your_email@163.com/$email_addr/" "$CONFIG_FILE"
else
    # Linux
    sed -i "s/your_email@163.com/$email_addr/" "$CONFIG_FILE"
fi

echo ""
echo "✅ 配置文件已创建: $CONFIG_FILE"
echo ""
echo "配置信息:"
echo "  邮箱: $email_addr"
echo "  IMAP服务器: imap.163.com:993"
echo "  授权码: XGnS37mV5Gpt2Jv6"
echo ""
echo "下一步:"
echo "1. 测试邮件连接: cd $SKILL_DIR/scripts && python3 fetch_emails.py"
echo "2. 创建飞书多维表格（通过OpenClaw助手）"
echo "3. 设置定期同步（cron或heartbeat）"
echo ""
