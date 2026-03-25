# 163邮箱同步到飞书多维表格

将网易163邮箱的邮件自动同步到飞书多维表格，支持 AI 字段提取（MiniMax）和飞书 Bot 私信通知。

## 前置准备

**依赖包**
```bash
pip install requests python-dateutil
```

**需要准备的凭证**
- 163邮箱 IMAP 授权码（非登录密码，在163邮箱设置 → POP3/SMTP/IMAP 中开启并获取）
- 飞书自建应用的 app_id 和 app_secret（需开通多维表格和消息相关权限）
- 飞书接收通知的用户 open_id
- MiniMax API Key

## 配置

复制配置模板并填写：

```bash
cp config.json.template config.json
```

编辑 `config.json`：

```json
{
  "imap": {
    "server": "imap.163.com",
    "port": 993,
    "email": "your@163.com",
    "password": "your_imap_auth_code"
  },
  "feishu": {
    "app_id": "cli_xxx",
    "app_secret": "xxx",
    "app_token": "",
    "table_id": "",
    "receiver_open_id": "ou_xxx"
  },
  "minimax": {
    "api_key": "your_minimax_api_key",
    "model": "abab6.5s-chat"
  }
}
```

> `app_token` 和 `table_id` 留空，运行 `setup_table.py` 后会自动写入。

## 运行步骤

### 第一步：创建多维表格

只需运行一次，自动创建表格和所有字段，并将 `app_token`/`table_id` 写回 `config.json`：

```bash
python setup_table.py
```

### 第二步：初始同步

同步最近 10 天的邮件：

```bash
python main.py --init
```

### 第三步：增量同步

同步最近 6 小时的邮件（用于日常定时任务）：

```bash
python main.py
```

### 配置定时任务（crontab）

每 10 分钟自动同步一次：

```bash
crontab -e
```

添加以下内容（路径按实际调整）：

```
*/10 * * * * cd /Users/hanyang/WORK/www/my-skills/email && python main.py >> logs/sync.log 2>&1
```

创建日志目录：

```bash
mkdir -p logs
```

## 表格字段说明

| 字段名 | 来源 |
|--------|------|
| 邮件ID | 邮件 Message-ID，用于去重 |
| 发送时间 | 邮件发送时间戳 |
| 邮件标题 | Subject |
| 发件人 / 发件人邮箱 | From 字段解析 |
| 邮件正文 | 正文前 2000 字 |
| 附件 | 附件文件名，分号分隔 |
| 是否已读 | 默认 False |
| 交流次数 | 同发件人邮箱的历史记录数 |
| 标题含泵类型 | AI 提取：标题中的泵类型文本 |
| 客户所在国家 | AI 提取 |
| 联系人姓名 | AI 提取 |
| 产品项目 | AI 提取 |
| 质检等级 | AI 提取：A / B / C |
| 第几次返修 | AI 提取 |
| 备注 | AI 提取：关键需求摘要 |
| 中文内容 | AI 提取：邮件中文翻译 |
