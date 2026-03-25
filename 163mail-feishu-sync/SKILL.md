---
name: 163mail-feishu-sync
description: 163邮箱同步到飞书多维表格工具（泵行业外贸版）。通过IMAP协议读取163邮箱，使用MiniMax AI自动提取客户国家、联系人姓名、产品类型、质检等级、返修次数、中文翻译等关键字段，写入飞书多维表格并发送飞书通知。项目代码位于 ./email 目录。当用户说"同步邮件"、"163邮箱同步飞书"、"查看外贸邮件"、"运行邮件同步"、"初始化邮件表格"、"设置邮件定时同步"、"email同步"、"邮件同步到飞书"时，务必激活此技能。
---

# 163邮箱同步到飞书多维表格

项目代码在 `./email/` 目录，通过IMAP读取163邮箱邮件，用MiniMax AI提取关键字段，写入飞书多维表格，并发送飞书Bot通知。

## 快速上手

### 第一步：配置凭证

```bash
cd ./email
cp config.json.template config.json
# 编辑 config.json，填写以下内容：
```

`config.json` 配置项：

```json
{
  "imap": {
    "server": "imap.163.com",
    "port": 993,
    "email": "your@163.com",
    "password": "your_imap_auth_code"   // IMAP授权码，非登录密码
  },
  "feishu": {
    "app_id": "cli_xxx",                // 飞书自建应用 App ID
    "app_secret": "xxx",               // 飞书自建应用 App Secret
    "app_token": "",                   // 留空，运行 setup_table.py 自动写入
    "table_id": "",                    // 留空，运行 setup_table.py 自动写入
    "receiver_open_id": "ou_xxx"       // 接收通知的用户 open_id
  },
  "minimax": {
    "api_key": "your_minimax_api_key",
    "model": "abab6.5s-chat"
  }
}
```

### 第二步：创建飞书多维表格（只需一次）

```bash
cd ./email
python setup_table.py
```

这会自动创建飞书多维表格和所有字段，并将 `app_token`/`table_id` 写回 `config.json`。

### 第三步：初始同步（首次同步近10天邮件）

```bash
cd ./email
python main.py --init
```

### 第四步：增量同步（同步近6小时新邮件）

```bash
cd ./email
python main.py
```

### 配置定时任务（每10分钟自动同步）

```bash
crontab -e
```

添加（路径按实际调整）：

```
*/10 * * * * cd /path/to/email && python main.py >> logs/sync.log 2>&1
```

```bash
mkdir -p ./email/logs
```

## 项目文件说明

| 文件 | 作用 |
|------|------|
| `main.py` | 主入口，协调同步流程 |
| `config.py` | 读写 config.json |
| `imap_client.py` | IMAP连接、邮件解析 |
| `feishu_client.py` | 飞书API（多维表格读写、Bot通知） |
| `minimax_client.py` | MiniMax AI字段提取 |
| `sync_state.py` | 本地已同步记录（synced_ids.json），防重复 |
| `setup_table.py` | 一次性建表脚本 |

## 飞书多维表格字段

| 字段名 | 来源 |
|--------|------|
| 邮件ID | Message-ID，用于去重 |
| 发送时间 | 邮件时间戳 |
| 邮件标题 | Subject |
| 发件人 / 发件人邮箱 | From 字段 |
| 邮件正文 | 正文前2000字 |
| 附件 | 附件文件名（分号分隔） |
| 是否已读 | 默认 False |
| 交流次数 | 同一发件人历史记录数 |
| 标题含泵类型 | AI提取 |
| 客户所在国家 | AI提取 |
| 联系人姓名 | AI提取 |
| 产品项目 | AI提取 |
| 质检等级 | AI提取（A/B/C） |
| 第几次返修 | AI提取 |
| 备注 | AI提取：100字中文需求摘要 |
| 中文内容 | AI提取：完整中文翻译 |

## 前置条件

- **163邮箱IMAP授权码**：登录163邮箱 → 设置 → POP3/SMTP/IMAP → 开启IMAP → 生成授权码
- **飞书自建应用**：需开通"多维表格"和"发送消息"权限
- **飞书用户 open_id**：用于接收Bot通知
- **MiniMax API Key**：用于AI字段提取

## 去重机制

双重去重保障：
1. **本地状态**：`synced_ids.json` 记录已同步的 Message-ID
2. **飞书查询**：写入前查询飞书确认记录不存在

## 常见问题

**IMAP连接失败**：确认使用的是授权码而非登录密码，且163邮箱已开启IMAP服务。

**飞书写入失败**：检查飞书应用是否有多维表格权限，`app_token`/`table_id` 是否已填写（先运行 `setup_table.py`）。

**AI提取失败**：MiniMax API调用失败时，相关字段返回空值/默认值，不影响邮件写入。
