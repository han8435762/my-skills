#!/usr/bin/env python3
"""
163邮件同步到飞书多维表格 - 泉行业专业版
智能识别泵类型、问题等级、产品项目等
"""

import imaplib
import email
from email.header import decode_header
import json
import os
import re
from datetime import datetime
import sys

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
LAST_SYNC_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "last_sync.txt")

# ==================== 泵行业专业知识库 ====================

# 泵类型大全（英文 -> 中文映射）
PUMP_TYPES = {
    # 基本原理分类
    'centrifugal pump': '离心泵',
    'axial flow pump': '轴流泵',
    'mixed flow pump': '混流泵',
    'gear pump': '齿轮泵',
    'screw pump': '螺杆泵',
    'lobe pump': '转子泵',
    'vane pump': '叶片泵',
    'piston pump': '活塞泵',
    'plunger pump': '柱塞泵',
    'diaphragm pump': '隔膜泵',
    'peristaltic pump': '蠕动泵',

    # 安装方式
    'submersible pump': '潜水泵',
    'vertical pump': '立式泵',
    'horizontal pump': '卧式泵',
    'inline pump': '管道泵',
    'end suction pump': '端吸泵',

    # 用途分类
    'water pump': '清水泵',
    'sewage pump': '污水泵',
    'drainage pump': '排水泵',
    'irrigation pump': '灌溉泵',
    'fire pump': '消防泵',
    'jockey pump': '稳压泵',
    'booster pump': '增压泵',
    'circulation pump': '循环泵',
    'hvac pump': '暖通泵',
    'chemical pump': '化工泵',
    'oil pump': '油泵',
    'fuel pump': '燃油泵',
    'slurry pump': '渣浆泵',
    'mud pump': '泥浆泵',
    'dewatering pump': '降水泵',

    # 级数分类
    'single stage pump': '单级泵',
    'multistage pump': '多级泵',

    # 自吸能力
    'self priming pump': '自吸泵',
    'non self priming pump': '非自吸泵',

    # 特殊类型
    'magnetic drive pump': '磁力泵',
    'cryogenic pump': '低温泵',
    'metering pump': '计量泵',
    'dosing pump': '加药泵',
    'vacuum pump': '真空泵',
    'high pressure pump': '高压泵',
    'solar pump': '太阳能泵',
    'marine pump': '船用泵',
    'mining pump': '矿用泵',
    'bitumen pump': '沥青泵',
    'hot oil pump': '导热油泵',

    # 手动/小型
    'hand pump': '手动泵',
    'foot pump': '脚踏泵',
    'garden pump': '园林泵',
    'well pump': '井泵',
    'jet pump': '喷射泵',
    'hydraulic pump': '液压泵',
    'hydraulic hand pump': '液压手动泵',
}

# 国家关键词映射（扩展版）
COUNTRY_KEYWORDS = {
    '印尼': ['indonesia', 'indonesian', 'jakarta', '印尼', '印度尼西亚'],
    '菲律宾': ['philippines', 'philippine', 'filipino', 'manila', '菲律宾'],
    '越南': ['vietnam', 'vietnamese', 'hanoi', 'ho chi minh', '越南'],
    '泰国': ['thailand', 'thai', 'bangkok', '泰国'],
    '马来西亚': ['malaysia', 'malaysian', 'kuala lumpur', '马来西亚'],
    '新加坡': ['singapore', '新加坡'],
    '印度': ['india', 'indian', 'new delhi', 'mumbai', '印度'],
    '巴基斯坦': ['pakistan', 'pakistani', 'karachi', '巴基斯坦'],
    '孟加拉国': ['bangladesh', 'dhaka', '孟加拉'],
    '缅甸': ['myanmar', 'burma', 'yangon', '缅甸'],
    '伊拉克': ['iraq', 'iraqi', 'baghdad', '伊拉克'],
    '伊朗': ['iran', 'iranian', 'tehran', '伊朗'],
    '沙特': ['saudi', 'saudi arabia', 'riyadh', '沙特', '沙特阿拉伯'],
    '阿联酋': ['uae', 'dubai', 'abu dhabi', '阿联酋', '迪拜', '阿布扎比'],
    '阿曼': ['oman', 'muscat', '阿曼'],
    '科威特': ['kuwait', '科威特'],
    '卡塔尔': ['qatar', 'doha', '卡塔尔'],
    '约旦': ['jordan', 'amman', '约旦'],
    '黎巴嫩': ['lebanon', 'beirut', '黎巴嫩'],
    '叙利亚': ['syria', 'syrian', 'damascus', '叙利亚'],
    '土耳其': ['turkey', 'turkish', 'istanbul', 'ankara', '土耳其'],
    '埃及': ['egypt', 'egyptian', 'cairo', '埃及'],
    '美国': ['usa', 'united states', 'america', 'american', '美国'],
    '加拿大': ['canada', 'canadian', '加拿大'],
    '墨西哥': ['mexico', 'mexican', '墨西哥'],
    '巴西': ['brazil', 'brazilian', '巴西'],
    '阿根廷': ['argentina', 'buenos aires', '阿根廷'],
    '智利': ['chile', 'santiago', '智利'],
    '秘鲁': ['peru', 'lima', '秘鲁'],
    '哥伦比亚': ['colombia', 'bogota', '哥伦比亚'],
    '英国': ['uk', 'united kingdom', 'britain', 'british', 'england', 'london', '英国'],
    '德国': ['germany', 'german', 'deutschland', 'berlin', '德国'],
    '法国': ['france', 'french', 'paris', '法国'],
    '意大利': ['italy', 'italian', 'rome', '意大利'],
    '西班牙': ['spain', 'spanish', 'madrid', '西班牙'],
    '荷兰': ['netherlands', 'holland', 'amsterdam', '荷兰'],
    '比利时': ['belgium', 'brussels', '比利时'],
    '瑞士': ['switzerland', 'swiss', 'zurich', '瑞士'],
    '奥地利': ['austria', 'vienna', '奥地利'],
    '波兰': ['poland', 'warsaw', '波兰'],
    '捷克': ['czech', 'prague', '捷克'],
    '俄罗斯': ['russia', 'russian', 'moscow', '俄罗斯'],
    '乌克兰': ['ukraine', 'kiev', '乌克兰'],
    '日本': ['japan', 'japanese', 'tokyo', 'osaka', '日本'],
    '韩国': ['korea', 'south korea', 'korean', 'seoul', '韩国'],
    '南非': ['south africa', 'pretoria', '南非'],
    '澳大利亚': ['australia', 'australian', 'sydney', '澳大利亚'],
    '新西兰': ['new zealand', 'wellington', '新西兰'],
    '尼日利亚': ['nigeria', 'lagos', '尼日利亚'],
    '肯尼亚': ['kenya', 'nairobi', '肯尼亚'],
}

# 质检等级关键词
QUALITY_GRADES = {
    'A': {
        'keywords': ['not work', 'broken', 'damage', 'fail', 'failure', 'crack', 'leak', 'noise', 'vibration',
                    '不工作', '损坏', '破裂', '泄露', '噪音', '振动', '无法使用', '不能工作',
                    'serious', 'severe', 'urgent', 'emergency', 'critical', '严重', '紧急', '关键'],
        'description': '严重问题（影响使用）'
    },
    'B': {
        'keywords': ['repair', 'replace', 'fix', 'issue', 'problem', 'defect', 'wear',
                    '维修', '更换', '修理', '问题', '缺陷', '磨损',
                    'performance', 'efficiency', 'pressure', 'flow', '性能', '效率', '压力', '流量'],
        'description': '一般问题（可维修）'
    },
    'C': {
        'keywords': ['check', 'inspect', 'advice', 'information', 'inquiry', 'question',
                    '检查', '查看', '咨询', '询问', '问题',
                    'spare', 'part', 'catalog', 'price', 'quote', '备件', '零件', '目录', '价格', '报价'],
        'description': '轻微问题（不影响使用）'
    }
}

# 来源类型
SOURCE_TYPES = {
    '163邮箱': ['163.com', '@163'],
    'Gmail': ['gmail.com', '@gmail'],
    'Yahoo': ['yahoo.com', '@yahoo'],
    'Outlook': ['outlook.com', 'hotmail.com', '@outlook', '@hotmail'],
    '企业邮箱': ['company', 'corporation', 'ltd', 'inc', 'co.', ' corp'],
}

# ==================== 工具函数 ====================

def load_config():
    """加载配置文件"""
    if not os.path.exists(CONFIG_FILE):
        print(f"配置文件不存在: {CONFIG_FILE}")
        sys.exit(1)

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_last_sync_uid():
    """获取最后同步的邮件UID"""
    if os.path.exists(LAST_SYNC_FILE):
        with open(LAST_SYNC_FILE, 'r') as f:
            return f.read().strip()
    return "0"

def save_last_sync_uid(uid):
    """保存最后同步的邮件UID"""
    with open(LAST_SYNC_FILE, 'w') as f:
        f.write(str(uid))

def decode_str(header_value):
    """解码邮件头字符串"""
    if not header_value:
        return ""

    decoded_list = decode_header(header_value)
    result = ""
    for content, encoding in decoded_list:
        if isinstance(content, bytes):
            if encoding:
                try:
                    result += content.decode(encoding)
                except:
                    result += content.decode('utf-8', errors='ignore')
            else:
                result += content.decode('utf-8', errors='ignore')
        else:
            result += str(content)
    return result

def clean_email(email_str):
    """清理邮箱地址，去除尖括号等"""
    if not email_str:
        return ""
    match = re.search(r'<(.+?)>', email_str)
    if match:
        return match.group(1)
    return email_str.strip()

def get_email_body(msg):
    """提取邮件正文"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body += payload.decode(charset, errors='ignore')
                except:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
        except:
            pass

    return body.strip()

def get_email_attachments(msg):
    """提取邮件附件信息"""
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    filename = decode_str(filename)
                    file_size = len(part.get_payload(decode=True)) if part.get_payload() else 0
                    attachments.append({
                        'filename': filename,
                        'size': file_size,
                        'content_type': part.get_content_type(),
                        'content_id': part.get('Content-ID', '').strip('<>')
                    })

    return attachments

# ==================== 智能识别函数 ====================

def extract_pump_type(subject, body):
    """提取泵类型"""
    content = (subject + " " + body).lower()

    # 按优先级匹配（更具体的优先）
    for en_name, cn_name in sorted(PUMP_TYPES.items(), key=lambda x: -len(x[0])):
        if en_name in content:
            return cn_name

    # 尝试中文匹配
    for en_name, cn_name in PUMP_TYPES.items():
        if cn_name in content:
            return cn_name

    return '未识别'

def extract_country(subject, body, from_email):
    """提取国家"""
    content = (subject + " " + body).lower()

    # 检查国家关键词
    for country, keywords in sorted(COUNTRY_KEYWORDS.items(), key=lambda x: -len(x[1])):
        for keyword in keywords:
            if keyword in content:
                return country

    # 检查邮箱后缀
    domain = from_email.split('@')[-1].lower()
    for country, keywords in COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.replace(' ', '') in domain:
                return country

    return '未识别'

def extract_quality_grade(subject, body):
    """提取质检等级"""
    content = (subject + " " + body).lower()

    # 先检查询价类（纯询价，排除维修场景）
    inquiry_keywords = ['inquiry', 'catalog', 'information', 'specification',
                       '询价', '目录', '资料', '规格']
    if any(keyword in content for keyword in inquiry_keywords):
        # 检查是否包含维修关键词
        if not any(kw in content for kw in ['repair', 'replace', 'fix', 'worn', 'broken', 'damage']):
            return 'C'

    # 检查A类（严重问题）
    severe_problem_keywords = ['not work', 'broken', 'fail', 'failure', 'crack', 'leak',
                              'serious', 'severe',
                              '不工作', '损坏', '破裂', '无法使用', '不能工作', '严重']
    for keyword in severe_problem_keywords:
        if keyword in content:
            return 'A'

    # 检查urgent（需要结合上下文）
    if 'urgent' in content or 'emergency' in content:
        # 检查是否是质量问题
        if any(kw in content for kw in ['not work', 'broken', 'damage', 'fail']):
            return 'A'
        # 否则只是urgent的询价
        return 'C'

    # 检查维修相关（B类）- 优先于quote判断
    repair_keywords = ['repair', 'replace', 'fix', 'worn-out', 'worn out',
                      '维修', '更换', '修理', '磨损']
    if any(keyword in content for keyword in repair_keywords):
        return 'B'

    # 检查quote相关
    if 'quote' in content or 'quotation' in content or 'price' in content:
        return 'C'

    # 检查一般问题关键词
    for keyword in QUALITY_GRADES['B']['keywords']:
        if keyword in content:
            return 'B'

    # 默认为 C（咨询类）
    return 'C'

def extract_source(from_email):
    """提取来源"""
    domain = from_email.split('@')[-1].lower()

    for source, keywords in SOURCE_TYPES.items():
        for keyword in keywords:
            if keyword in domain:
                return source

    return '其他'

def extract_repair_times(from_email):
    """获取返修次数（基于历史跟踪）"""
    tracking_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tracking_count.json')

    if os.path.exists(tracking_file):
        with open(tracking_file, 'r', encoding='utf-8') as f:
            tracking_data = json.load(f)
            return tracking_data.get(from_email, 1)

    return 1

def extract_recipient_name(from_str):
    """提取收件人姓名"""
    # 从发件人字符串中提取姓名
    from_str = from_str.strip()
    # 移除邮箱地址
    email_match = re.search(r'<(.+?)>', from_str)
    if email_match:
        name = from_str.replace(email_match.group(0), '').strip().strip('"')
    else:
        # 尝试从邮箱中提取
        email_part = from_str.split('@')[0]
        name = email_part.replace('.', ' ').replace('_', ' ').title()

    return name if name else '未知'

def extract_notes(subject, body):
    """提取备注信息"""
    # 从正文中提取关键信息
    lines = body.split('\n')
    notes = []

    # 关键词标记
    note_keywords = ['need', 'require', 'request', 'please', 'suggest',
                    '需要', '要求', '请', '建议', '备注']

    for line in lines[:20]:  # 只检查前20行
        line = line.strip()
        if any(keyword in line.lower() for keyword in note_keywords):
            # 截取关键句
            if len(line) > 10 and len(line) < 200:
                notes.append(line)

    return ' | '.join(notes[:3]) if notes else ''

def translate_to_chinese(subject, body):
    """AI翻译邮件内容为中文"""
    try:
        # 导入翻译模块
        import translate_email
        return translate_email.translate_email_to_chinese(subject, body)
    except Exception as e:
        # 如果翻译失败，返回原文
        print(f"翻译失败: {str(e)}")
        return f"{subject}\n\n{body[:500]}"

def update_repair_count(from_email):
    """更新返修计数"""
    tracking_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tracking_count.json')

    tracking_data = {}
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r', encoding='utf-8') as f:
            tracking_data = json.load(f)

    current_count = tracking_data.get(from_email, 0)
    tracking_data[from_email] = current_count + 1

    with open(tracking_file, 'w', encoding='utf-8') as f:
        json.dump(tracking_data, f, ensure_ascii=False, indent=2)

    return tracking_data[from_email]

# ==================== 邮件获取函数 ====================

def fetch_emails(config, limit=20):
    """从163邮箱获取新邮件"""
    try:
        imap_server = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
        imap_server.login(config['email'], config['imap_password'])

        imaplib.Commands['ID'] = ('AUTH',)
        client_id = ("name", "OpenClaw-163Mail-Sync", "version", "2.0", "vendor", "OpenClaw")
        imap_server._simple_command('ID', '("' + '" "'.join(client_id) + '")')

        status, msg = imap_server.select('INBOX')
        if status != 'OK':
            print(f"选择收件箱失败: {msg}")
            return []

        last_uid = get_last_sync_uid()
        print(f"上次同步UID: {last_uid}")

        status, messages = imap_server.search(None, 'ALL')
        if status != 'OK':
            print("搜索邮件失败")
            return []

        email_list = messages[0].split()
        print(f"邮箱中共有 {len(email_list)} 封邮件")

        new_emails = []
        last_uid_int = int(last_uid) if last_uid.isdigit() else 0

        for idx, email_id in enumerate(email_list):
            status, uid_data = imap_server.fetch(email_id, '(UID)')
            if status == 'OK':
                uid_match = re.search(r'UID (\d+)', uid_data[0].decode())
                if uid_match:
                    current_uid = int(uid_match.group(1))

                    if current_uid > last_uid_int:
                        status, msg_data = imap_server.fetch(email_id, '(RFC822)')
                        if status == 'OK':
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)

                            email_info = {
                                'uid': current_uid,
                                'from': decode_str(msg.get('From', '')),
                                'to': decode_str(msg.get('To', '')),
                                'subject': decode_str(msg.get('Subject', '')),
                                'date': msg.get('Date', ''),
                                'body': get_email_body(msg),
                                'attachments': get_email_attachments(msg)
                            }

                            new_emails.append(email_info)
                            print(f"获取新邮件: {email_info['subject'][:50]}...")

                            save_last_sync_uid(current_uid)

                            if len(new_emails) >= limit:
                                break

        imap_server.close()
        imap_server.logout()

        print(f"共获取 {len(new_emails)} 封新邮件")
        return new_emails

    except Exception as e:
        print(f"获取邮件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def format_email_for_feishu(email_info):
    """格式化邮件信息为飞书多维表格格式"""
    from_str = email_info['from']
    from_email = clean_email(from_str)

    # 解析日期
    date_str = email_info['date']
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        timestamp = int(dt.timestamp() * 1000)
        date_only = dt.strftime('%Y-%m-%d')
    except:
        timestamp = int(datetime.now().timestamp() * 1000)
        date_only = datetime.now().strftime('%Y-%m-%d')

    body_preview = email_info['body'][:500] if email_info['body'] else ""

    # 智能识别
    country = extract_country(email_info['subject'], email_info['body'], from_email)
    pump_type = extract_pump_type(email_info['subject'], email_info['body'])
    quality_grade = extract_quality_grade(email_info['subject'], email_info['body'])
    source = extract_source(from_email)
    repair_times = extract_repair_times(from_email)
    recipient_name = extract_recipient_name(from_str)
    notes = extract_notes(email_info['subject'], email_info['body'])

    # 格式化附件
    attachments_str = "; ".join([att['filename'] for att in email_info.get('attachments', [])])

    # AI翻译（占位）
    ai_chinese = translate_to_chinese(email_info['subject'], email_info['body'])

    return {
        '时间': date_only,
        '国家': country,
        '收件人': recipient_name,
        '产品项目': pump_type,
        '质检等级': quality_grade,
        '来源': source,
        '第几次返修': repair_times,
        '备注': notes,
        '邮件ID': str(email_info['uid']),
        '发件人邮箱': from_email,
        '主题': email_info['subject'],
        '发送时间': timestamp,
        '邮件正文': body_preview,
        '附件': attachments_str,
        'AI_中文': ai_chinese,
        '同步时间': int(datetime.now().timestamp() * 1000),
        '是否已读': False,
        '邮件标签': ['其他']
    }

if __name__ == "__main__":
    config = load_config()
    emails = fetch_emails(config, limit=20)

    if emails:
        print(f"\n成功获取 {len(emails)} 封新邮件")
        for i, email_info in enumerate(emails, 1):
            print(f"\n{i}. {email_info['subject']}")
            print(f"   发件人: {email_info['from']}")
            print(f"   时间: {email_info['date']}")
    else:
        print("没有新邮件")
