# 163邮件同步技能 - 使用指南

## 快速开始

### 1. 首次配置

运行设置脚本并输入你的163邮箱地址：

```bash
cd /root/.openclaw/workspace/skills/wecom-163mail-sync/scripts
./setup.sh
```

### 2. 测试邮件连接

```bash
cd /root/.openclaw/workspace/skills/wecom-163mail-sync/scripts
python3 fetch_emails.py
```

如果看到邮件列表，说明连接成功！

### 3. 创建飞书多维表格

通过OpenClaw助手创建：

```
使用feishu_bitable_create_app创建一个名为"163邮件同步表"的多维表格
```

然后创建以下字段：
- 邮件ID (Text)
- 发件人 (Text)
- 发件人邮箱 (Text)
- 收件人 (Text)
- 主题 (Text)
- 发送时间 (DateTime)
- 邮件正文 (Text)
- 同步时间 (DateTime)
- 是否已读 (Checkbox)
- 邮件标签 (MultiSelect: 客户/询盘/订单/其他)

### 4. 更新配置文件

将创建的飞书多维表格信息更新到 `config.json`：

```json
{
  "email": "your_email@163.com",
  "imap_password": "XGnS37mV5Gpt2Jv6",
  "imap_server": "imap.163.com",
  "imap_port": 993,
  "last_sync_uid": "0",
  "feishu_table_token": "<你的表格token>",
  "feishu_table_id": "<子表ID>"
}
```

### 5. 执行同步

```bash
cd /root/.openclaw/workspace/skills/wecom-163mail-sync/scripts
python3 sync_to_feishu.py
```

### 6. 设置自动同步

在 `HEARTBEAT.md` 中添加：

```markdown
## 邮件同步

每10分钟检查一次163邮件并同步到飞书：
```bash
cd /root/.openclaw/workspace/skills/wecom-163mail-sync/scripts && python3 sync_to_feishu.py
```
```

## 工作原理

### IMAP连接（只读模式）

- 使用IMAP协议连接到 imap.163.com:993
- 使用授权码认证（不是登录密码）
- 只读取邮件，不回复、不删除、不修改

### 邮件获取流程

1. 读取上次同步的邮件UID（last_sync_uid）
2. 搜索收件箱中所有邮件
3. 筛选出UID大于last_sync_uid的新邮件
4. 解析邮件头和正文
5. 更新last_sync_uid

### 数据同步

1. 格式化邮件数据为飞书字段格式
2. 批量写入多维表格（通过feishu_bitable_create_record）
3. 发送新邮件通知到个人飞书

### 隐私和安全

- ✅ 只读模式，不修改原始邮件
- ✅ 授权码存储在本地配置文件
- ✅ 邮件内容仅同步到个人飞书多维表格
- ✅ 不上传到第三方服务器

## 故障排查

### IMAP连接失败

**错误**: "Authentication failed" 或 "IMAP login failed"

**解决方案**:
1. 确认163邮箱已开启IMAP服务（设置 -> POP3/SMTP/IMAP）
2. 确认使用的是IMAP授权码，不是登录密码
3. 检查授权码是否正确：XGnS37mV5Gpt2Jv6

### 邮件重复同步

**原因**: last_sync_uid未正确更新

**解决方案**:
1. 检查 `last_sync.txt` 文件是否存在
2. 手动删除 `last_sync.txt` 重新同步全部邮件
3. 或者手动设置last_sync_uid为最大邮件UID

### 飞书写入失败

**错误**: "feishu_bitable_create_record failed"

**解决方案**:
1. 检查飞书API权限（需要多维表格写入权限）
2. 确认app_token和table_id是否正确
3. 检查字段类型是否匹配

### 同步频率过高被限制

**症状**: IMAP连接变慢或失败

**解决方案**:
1. 降低同步频率（改为15-30分钟）
2. 每次同步限制邮件数量（limit=10）
3. 避免在短时间内多次手动同步

## 高级配置

### 自定义同步时间

修改 `fetch_emails.py` 中的 `limit` 参数：

```python
emails = fetch_emails(config, limit=50)  # 每次最多同步50封
```

### 自定义邮件标签

修改 `sync_to_feishu.py` 中的标签逻辑，根据邮件内容自动分类：

```python
if 'inquiry' in email_info['subject'].lower():
    email_data['邮件标签'] = ['询盘']
elif 'order' in email_info['subject'].lower():
    email_data['邮件标签'] = ['订单']
```

### 过滤特定邮件

修改 `fetch_emails.py` 中的搜索条件：

```python
# 只搜索未读邮件
status, messages = imap_server.search(None, 'UNSEEN')

# 只搜索特定发件人
status, messages = imap_server.search(None, 'FROM "customer@example.com"')
```

## 监控和日志

### 查看同步日志

```bash
tail -f /root/.openclaw/workspace/skills/wecom-163mail-sync/sync.log
```

### 查看最后同步时间

```bash
cat /root/.openclaw/workspace/skills/wecom-163mail-sync/last_sync.txt
```

### 查看同步队列

```bash
cat /root/.openclaw/workspace/skills/wecom-163mail-sync/sync_queue.json
```

## 最佳实践

1. **定期备份**: 定期导出飞书多维表格数据
2. **监控异常**: 设置飞书机器人报警，同步失败时通知
3. **清理旧邮件**: 多维表格过大时，归档旧数据
4. **权限管理**: 定期更新授权码，确保安全

## 外贸场景优化建议

1. **客户识别**: 根据发件人域名自动识别国家/地区
2. **询盘分类**: 自动标记产品类型和询价数量
3. **跟进提醒**: 标记重要客户，设置飞书待办提醒
4. **数据分析**: 定期统计邮件来源、回复率等指标
