---
name: wecom-163mail-sync
description: 163邮件同步到飞书多维表格技能（泵行业专业版）。自动从163邮箱同步外贸客户邮件，智能识别泵类型（50+种）、国家（50+）、质检等级（A/B/C），并实时翻译为中文。适用于外贸客户邮件管理、询盘跟踪、售后质量分析等场景。当用户需要"同步邮件"、"查看客户邮件"、"管理外贸邮件"、"163邮箱同步"、"分析泵类询盘"时激活此技能。
---

# 163邮件同步到飞书多维表格 - 泵行业专业版

## 快速开始

```bash
# 手动触发同步
cd ./scripts
python3 sync_to_feishu.py
```

## 核心功能

### 1. 智能邮件同步

- 使用`openclaw的cron tool`每10分钟自动从163邮箱同步新邮件（只读模式）
- 自动识别**泵类型**（50+种）：稳压泵、增压泵、离心泵、液压手动泵等
- 自动识别**国家**（50+个）：菲律宾、伊拉克、印尼、阿联酋等
- 自动判断**质检等级**（A/B/C）：严重问题、一般问题、轻微问题
- 自动提取**客户姓名**、**备注信息**、**附件信息**
- 自动**翻译英文邮件为中文**

### 2. 多维表格字段

**字段（16个）**：
| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| 时间 | 时间 | 邮件发送时间 | 2026-03-22 00:00:00 |
| 邮件标题 | 文本 | 邮件标题 | 关于泵的询价 |
| 国家 | 单选 | 客户所在国家 | 菲律宾、伊拉克、印尼 |
| 发件人 | 文本 | 客户联系人姓名 | UNIQUA CHARMAINE |
| 产品项目 | 单选 | 泵类型识别 | 稳压泵、液压手动泵 |
| 质检等级 | 单选 | 问题严重程度 | A（严重）、B（一般）、C（轻微） |
| 来源 | 单选 | 邮件来源渠道 | 163邮箱、企业邮箱 |
| 第几次返修 | 数字 | 客户返修/跟踪次数 | 1、2、3... |
| 备注 | 文本 | 关键需求摘要 | FOR QUOTE |
| 中文内容 | 文本 | 邮件内容翻译成中文的版本 | 中文内容 |
| 邮件ID | 文本 | 邮件唯一标识 | 1234567890 |
| 发件人邮箱 | 文本 | 发件人邮箱地址 | example@163.com |
| 主题 | 文本 | 邮件主题 | 关于泵的询价 |
| 邮件正文 | 文本 | 邮件正文 | 中文内容 |
| 附件 | 文本 | 邮件附件信息 | 中文内容 |
| 是否已读 | 文本 | 邮件是否已读 | 中文内容 |

表格链接：{config.feishu_table_url}

## 前置条件检查

⚠️ **必须配置的常量**：

### config.json配置

```json
{
  "email": "", // ⚠️ 需要配置：163邮箱地址
  "imap_password": "", // ⚠️ 需要配置：IMAP授权码
  "imap_server": "imap.163.com", // 固定值
  "imap_port": 993, // 固定值
  "feishu_table_token": "", // ⚠️ 需要配置：飞书表格token
  "feishu_table_id": "", // ⚠️ 需要配置：飞书表格ID 如果没有配置 则创建一个 但是需要让用户可以修改的表格
  "feishu_folder_token": "", // 可选：飞书文件夹token
  "feishu_table_url": "" // ⚠️ 需要配置：飞书表格URL
}
```

### 获取IMAP授权码步骤

1. 登录163邮箱网页版
2. 设置 → POP3/SMTP/IMAP
3. 开启IMAP服务
4. 生成授权码（不是邮箱密码）

### 获取飞书表格token步骤

1. 打开飞书多维表格
2. 从URL中提取token：`https://x92l0onftm.feishu.cn/base/{token}`
3. 使用`feishu_bitable_list_fields`获取table_id
4. 注意：如果没有的话 自动创建一个表格 但是需要让用户可以进行增删改查的表格

## 工作流程

### 自动同步流程

1. **连接163邮箱**（IMAP协议）
2. **获取新邮件**（基于UID比对）
3. **智能识别**（泵类型、国家、质检等级）
4. **翻译为中文**（实时翻译）
5. **写入飞书表格**（批量创建记录）
6. **发送通知**（飞书个人消息）
7. **定时执行**（每10分钟）

### 手动操作

**同步邮件**：

```bash
cd ./scripts
python3 sync_to_feishu.py
```

**测试识别功能**：

```bash
cd ./scripts
python3 test_pump_intelligence.py
```

**测试IMAP连接**：

```bash
cd ./scripts

python3 diagnose_imap.py
```

## 脚本资源

### 核心脚本

**scripts/sync_to_feishu.py** - 主同步脚本

- 连接163邮箱
- 调用fetch_emails获取邮件
- 调用translate_email翻译
- 写入飞书表格

**scripts/fetch_emails.py** - 邮件获取和智能识别

- IMAP连接和邮件获取
- 泵类型识别（50+种）
- 国家识别（50+个）
- 质检等级判断（A/B/C）
- 客户姓名提取
- 备注信息提取
- 附件信息提取

**scripts/translate_email.py** - AI翻译模块

- 英文邮件实时翻译为中文
- 泵类型专业翻译
- 技术参数翻译
- 商业术语翻译

### 辅助脚本

**scripts/test_pump_intelligence.py** - 智能识别测试

- 测试泵类型识别
- 测试国家识别
- 测试质检等级判断

**scripts/diagnose_imap.py** - IMAP连接诊断

- 测试IMAP连接
- 测试邮箱登录
- 显示邮箱统计信息

**scripts/create_feishu_fields.sh** - 字段创建脚本

- 批量创建飞书表格字段
- 支持自定义字段配置

## 智能识别规则

### 泵类型识别（50+种）

**识别优先级**：

1. 匹配英文泵类型（更具体的优先）
   - `JOCKEY PUMP` → 稳压泵
   - `Hydraulic Hand Pump` → 液压手动泵
2. 匹配中文泵类型
   - `离心泵` → 离心泵
3. 无法识别 → 标记为"未识别"

**支持的泵类型**（部分）：

- 稳压泵(Jockey Pump)、增压泵(Booster Pump)、离心泵(Centrifugal Pump)
- 液压手动泵(Hydraulic Hand Pump)、手动泵(Hand Pump)
- 潜水泵(Submersible Pump)、化工泵(Chemical Pump)
- 齿轮泵(Gear Pump)、螺杆泵(Screw Pump)
- ...等50+种

完整列表见：`scripts/fetch_emails.py`中的`PUMP_TYPES`字典

### 国家识别（50+国家）

**识别规则**：

1. 从邮件主题和正文匹配国家关键词
2. 从发件人邮箱域名推断
3. 无法识别 → 标记为"未识别"

**重点市场**：

- 东南亚：印尼、菲律宾、越南、泰国、马来西亚、新加坡
- 中东：伊拉克、伊朗、沙特、阿联酋、阿曼、科威特
- 南亚：印度、巴基斯坦、孟加拉国

完整列表见：`scripts/fetch_emails.py`中的`COUNTRY_KEYWORDS`字典

### 质检等级判断

**判断逻辑**：

1. 检查严重问题关键词 → **A级**（严重）
   - not work, broken, damage, failure, crack, leak
   - 不工作、损坏、破裂、泄露、噪音、振动

2. 检查维修关键词 → **B级**（一般）
   - repair, replace, fix, worn-out
   - 维修、更换、修理、磨损

3. 检查询价关键词 → **C级**（轻微）
   - inquiry, catalog, quote, price
   - 询价、目录、报价、价格

### 客户姓名提取

**提取规则**：

1. 优先使用发件人显示名称
2. 其次从邮箱前缀提取并格式化
   - `john.smith@company.com` → John Smith
   - `alan.khalil@iraq.com` → Alan Khalil

### 备注信息提取

**提取规则**：

- 从邮件正文前20行提取包含关键词的句子
- 关键词：need, require, request, please, suggest
- 最多提取3条，用 `|` 分隔

## 翻译功能

### 翻译范围

**泵类型翻译**：

- Jockey Pump → 稳压泵
- Hydraulic Hand Pump → 液压手动泵
- Booster Pump → 增压泵

**技术参数翻译**：

- 2HP → 2马力
- 130 PSI → 130磅/平方英寸
- 220V → 220伏
- 20gpm → 20加仑/分钟

**商业术语翻译**：

- Inquiry → 询价
- Quote → 报价
- Best Price → 最优价格
- Packing List → 装箱单

**礼貌用语翻译**：

- Dear Sir → 尊敬的先生
- Good day → 您好
- Thanks & Best Regards → 感谢并致以最诚挚的问候

## 定时任务

### OpenClaw Cron配置

使用OpenClaw的Cron功能设置定时任务（**推荐**）：

```bash
# 查看cron任务
openclaw cron list

# 查看任务运行历史
openclaw cron runs --id b962bb65-2104-4625-b4df-2c62be907e31

# 手动触发任务
openclaw cron run b962bb65-2104-4625-b4df-2c62be907e31 --force
```

### Cron任务信息

- **任务ID**: b962bb65-2104-4625-b4df-2c62be907e31
- **任务名称**: 163邮件同步
- **执行频率**: 每10分钟
- **状态**: 已启用 ✅

## 使用场景

### 场景1：筛选高价值客户

在飞书表格中筛选：

- **质检等级 = A** → 优先处理严重问题
- **第几次返修 > 1** → 老客户需要特别关注
- **国家 = 重点市场** → 中东、东南亚客户

### 场景2：按产品类型分析

- 按"产品项目"分组
- 查看各类泵的询盘分布
- 识别热门产品类型

### 场景3：售后质量跟踪

- 筛选 A/B 级问题
- 查看备注中的具体问题
- 按国家分析质量问题分布

## 参考资源

### 字段配置文档

- **FEISHU_FIELDS_PUMP.md** - 泵行业字段配置指南（详细字段说明和创建命令）

### 技术文档

- **scripts/fetch_emails.py** - 智能识别实现代码
- **scripts/translate_email.py** - 翻译功能实现代码

### 测试脚本

- **test_pump_intelligence.py** - 智能识别功能测试
- **diagnose_imap.py** - IMAP连接诊断

## 注意事项

1. **只读模式**：技能严格只读，不会回复或删除任何邮件
2. **隐私保护**：邮件内容仅在本地处理和飞书存储
3. **同步频率**：默认10分钟，避免频繁请求被163限制
4. **翻译准确度**：基于规则匹配，可能需要手动修正专业术语
5. **识别准确度**：基于关键词匹配，准确率取决于邮件内容质量

## 故障排查

### IMAP连接失败

- 检查授权码是否正确（⚠️ 不是邮箱密码）
- 确认163邮箱已开启IMAP服务
- 检查网络连接
- 运行`python3 diagnose_imap.py`诊断

### 飞书写入失败

- 检查飞书API权限
- 确认多维表格token和table_id是否正确
- 查看字段是否已创建

### 识别不准确

- 检查邮件内容是否包含关键词
- 查看`scripts/fetch_emails.py`中的词典
- 可以添加新的关键词到词典中

### 翻译不准确

- 检查`scripts/translate_email.py`中的词典
- 可以添加新的翻译条目
- 专业术语可能需要手动修正
