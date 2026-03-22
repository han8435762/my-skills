#!/bin/bash
# 飞书多维表格字段批量创建脚本
# 使用前请确保已设置 app_token 和 table_id

set -e

# 配置信息（从 config.json 读取）
CONFIG_FILE="$(dirname "$0")/../config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 读取配置（需要 jq 工具）
if command -v jq &> /dev/null; then
    APP_TOKEN=$(jq -r '.feishu_table_token' "$CONFIG_FILE")
    TABLE_ID=$(jq -r '.feishu_table_id' "$CONFIG_FILE")
else
    echo "⚠️  未安装 jq，请手动设置 APP_TOKEN 和 TABLE_ID"
    echo "或安装 jq: apt-get install jq"
    exit 1
fi

if [ -z "$APP_TOKEN" ] || [ "$APP_TOKEN" = "null" ]; then
    echo "❌ 未配置 feishu_table_token"
    exit 1
fi

if [ -z "$TABLE_ID" ] || [ "$TABLE_ID" = "null" ]; then
    echo "❌ 未配置 feishu_table_id"
    exit 1
fi

echo "=========================================="
echo "飞书多维表格字段批量创建"
echo "=========================================="
echo "App Token: $APP_TOKEN"
echo "Table ID: $TABLE_ID"
echo "=========================================="
echo ""

# 创建字段的函数
create_field() {
    local field_name=$1
    local field_type=$2
    local property=$3

    echo "创建字段: $field_name"

    # 这里需要通过 OpenClaw 调用 feishu_bitable_create_field
    # 由于这是 bash 脚本，我们需要生成 OpenClaw 命令
    echo "  命令: openclaw feishu bitable create-field --app-token $APP_TOKEN --table-id $TABLE_ID --field-name \"$field_name\" --field-type $field_type --property '$property'"
    echo ""
}

echo "⚠️  注意：此脚本会生成创建字段的命令"
echo "请复制下面的命令到 OpenClaw 中执行"
echo ""
echo "=========================================="
echo "字段创建命令"
echo "=========================================="
echo ""

# 1. 创建"国家"字段（单选）
create_field "国家" 3 '{"options":[{"name":"美国"},{"name":"英国"},{"name":"德国"},{"name":"法国"},{"name":"日本"},{"name":"韩国"},{"name":"印度"},{"name":"俄罗斯"},{"name":"巴西"},{"name":"加拿大"},{"name":"澳大利亚"},{"name":"意大利"},{"name":"西班牙"},{"name":"荷兰"},{"name":"墨西哥"},{"name":"印尼"},{"name":"泰国"},{"name":"越南"},{"name":"菲律宾"},{"name":"马来西亚"},{"name":"新加坡"},{"name":"阿联酋"},{"name":"未识别"}]}'

# 2. 创建"产品类目"字段（单选）
create_field "产品类目" 3 '{"options":[{"name":"电子产品"},{"name":"服装服饰"},{"name":"家居用品"},{"name":"美容护肤"},{"name":"健康医疗"},{"name":"汽车配件"},{"name":"体育用品"},{"name":"食品饮料"},{"name":"母婴用品"},{"name":"办公文具"},{"name":"其他"}]}'

# 3. 创建"相关度"字段（单选）
create_field "相关度" 3 '{"options":[{"name":"高"},{"name":"中"},{"name":"低"}]}'

# 4. 创建"来源"字段（单选）
create_field "来源" 3 '{"options":[{"name":"163邮箱"}]}'

# 5. 创建"第几次跟踪"字段（数字）
create_field "第几次跟踪" 2 '{}'

# 6. 创建"附件"字段（文本）
create_field "附件" 1 '{}'

echo "=========================================="
echo "字段类型说明"
echo "=========================================="
echo "1 = 文本"
echo "2 = 数字"
echo "3 = 单选"
echo "4 = 多选"
echo "5 = 日期时间"
echo "7 = 复选框"
echo ""

echo "⚠️  重要提示："
echo "1. 请确保飞书表格中已有基础字段（邮件ID、发件人、主题等）"
echo "2. 如果字段已存在，命令会报错，可以忽略"
echo "3. 字段名称必须完全匹配，包括中文标点"
echo ""
