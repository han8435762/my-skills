#!/usr/bin/env python3
"""
邮件翻译模块 - 将英文邮件翻译成中文
"""

import re
import json
import os

def translate_email_to_chinese(subject, body):
    """
    将邮件内容翻译成中文
    使用规则匹配 + 智能识别的方式
    """
    # 如果已经是中文，直接返回
    if is_chinese_content(subject + " " + body):
        return f"{subject}\n\n{body}"

    # 翻译主题
    translated_subject = translate_subject(subject)

    # 翻译正文
    translated_body = translate_body(body)

    return f"{translated_subject}\n\n{translated_body}"

def is_chinese_content(text):
    """检查内容是否主要是中文"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', text))
    if total_chars == 0:
        return False
    return chinese_chars / total_chars > 0.3

def translate_subject(subject):
    """翻译邮件主题"""
    if not subject:
        return ""

    # 泵类型词典
    pump_terms = {
        'Jockey Pump': '稳压泵',
        'Booster Pump': '增压泵',
        'Centrifugal Pump': '离心泵',
        'Hand Pump': '手动泵',
        'Hydraulic Hand Pump': '液压手动泵',
        'Submersible Pump': '潜水泵',
        'Sewage Pump': '污水泵',
        'Chemical Pump': '化工泵',
        'Water Pump': '清水泵',
        'Fire Pump': '消防泵',
        'Gear Pump': '齿轮泵',
        'Screw Pump': '螺杆泵',
        'Diaphragm Pump': '隔膜泵',
        'Piston Pump': '活塞泵',
        'Plunger Pump': '柱塞泵',
        'Vacuum Pump': '真空泵',
        'Metering Pump': '计量泵',
        'Dosing Pump': '加药泵',
        'Magnetic Drive Pump': '磁力泵',
        'Self Priming Pump': '自吸泵',
        'Multi-stage Pump': '多级泵',
        'Single Stage Pump': '单级泵',
        'Vertical Pump': '立式泵',
        'Horizontal Pump': '卧式泵',
        'End Suction Pump': '端吸泵',
        'Inline Pump': '管道泵',
        'Axial Flow Pump': '轴流泵',
        'Mixed Flow Pump': '混流泵',
        'Lobe Pump': '转子泵',
        'Vane Pump': '叶片泵',
        'Peristaltic Pump': '蠕动泵',
        'Slurry Pump': '渣浆泵',
        'Mud Pump': '泥浆泵',
        'Dewatering Pump': '降水泵',
        'Irrigation Pump': '灌溉泵',
        'Drainage Pump': '排水泵',
        'Circulation Pump': '循环泵',
        'HVAC Pump': '暖通泵',
        'Oil Pump': '油泵',
        'Fuel Pump': '燃油泵',
        'High Pressure Pump': '高压泵',
        'Solar Pump': '太阳能泵',
        'Marine Pump': '船用泵',
        'Mining Pump': '矿用泵',
        'Cryogenic Pump': '低温泵',
        'Bitumen Pump': '沥青泵',
        'Hot Oil Pump': '导热油泵',
        'Foot Pump': '脚踏泵',
        'Garden Pump': '园林泵',
        'Well Pump': '井泵',
        'Jet Pump': '喷射泵',
        'Hydraulic Pump': '液压泵',
    }

    # 常用词汇
    common_terms = {
        'Inquiry': '询价',
        'Quote': '报价',
        'Quotation': '报价',
        'Request': '请求',
        'Order': '订单',
        'Urgent': '紧急',
        'Best Price': '最优价格',
        'Price List': '价格表',
        'Packing List': '装箱单',
        'Catalog': '目录',
        'Specification': '规格',
        'Capacity': '容量',
        'Flow Rate': '流量',
        'Head': '扬程',
        'Pressure': '压力',
        'Power': '功率',
        'Voltage': '电压',
        'RPM': '转速',
        'HP': '马力',
        'PSI': '磅/平方英寸',
        'GPM': '加仑/分钟',
        'Phase': '相',
        'Hz': '赫兹',
        'TDH': '总扬程',
        'Accessory': '配件',
        'Spare Parts': '备件',
        'Replacement': '更换',
        'Repair': '维修',
        'Maintenance': '维护',
        'Installation': '安装',
        'Warranty': '质保',
        'Delivery': '交付',
        'Shipment': '装运',
        'Stock': '库存',
        'Available': '可提供',
        'Manufacturer': '制造商',
        'Supplier': '供应商',
        'Company': '公司',
        'Corporation': '公司',
        'Inc': '公司',
        'Ltd': '有限公司',
        'Co.': '公司',
        'Email': '邮箱',
        'Tel': '电话',
        'Mobile': '手机',
        'Website': '网站',
        'Product Link': '产品链接',
        'IP': 'IP地址',
        'Contact': '联系人',
        'Message': '信息',
        'Thank': '感谢',
        'Regards': '致意',
        'Dear': '亲爱的',
        'Sir': '先生',
        'Madam': '女士',
        'Good day': '您好',
        'Please': '请',
        'Appreciate': '感谢',
        'Consideration': '考虑',
        'Check': '检查',
        'Items': '项目',
        'Attached': '附件',
        'Files': '文件',
        'No.': '编号',
        'Description': '描述',
        'Qty': '数量',
        'Type': '类型',
        'Sales': '销售',
        'Manager': '经理',
        'Engineer': '工程师',
        'Eng.': '工程师',
        'Mr.': '先生',
        'Mrs.': '女士',
        'Ms.': '女士',
    }

    # 单位翻译
    units = {
        '2HP': '2马力',
        '3HP': '3马力',
        '5HP': '5马力',
        '10HP': '10马力',
        '130 PSI': '130磅/平方英寸',
        '220V': '220伏',
        '20gpm': '20加仑/分钟',
        '3ph': '3相',
        '60hz': '60赫兹',
        '230v': '230伏',
        '195ft': '195英尺',
    }

    # 合并所有词典
    all_terms = {}
    all_terms.update(pump_terms)
    all_terms.update(common_terms)
    all_terms.update(units)

    # 按长度降序排序（优先匹配长的词组）
    sorted_terms = sorted(all_terms.items(), key=lambda x: -len(x[0]))

    translated = subject
    for en, cn in sorted_terms:
        # 不区分大小写替换
        pattern = re.compile(re.escape(en), re.IGNORECASE)
        translated = pattern.sub(cn, translated)

    # 清理多余空格
    translated = re.sub(r'\s+', ' ', translated).strip()

    return translated

def translate_body(body):
    """翻译邮件正文"""
    if not body:
        return ""

    # 分行翻译
    lines = body.split('\n')
    translated_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            translated_lines.append('')
            continue

        # 跳过纯分隔符行
        if re.match(r'^[\s\-_|=]+$', line):
            translated_lines.append(line)
            continue

        # 翻译这一行
        translated_line = translate_line(line)
        translated_lines.append(translated_line)

    return '\n'.join(translated_lines)

def translate_line(line):
    """翻译单行文本"""
    # 技术参数词典
    technical_terms = {
        # 泵类型
        'Jockey Pump': '稳压泵',
        'Booster Pump': '增压泵',
        'Hydraulic Hand Pump': '液压手动泵',
        'Hand Pump': '手动泵',
        'Centrifugal Pump': '离心泵',

        # 常用词汇
        'Website': '网站',
        'Product Link': '产品链接',
        'Company Name': '公司名称',
        'Contact': '联系人',
        'E-mail': '邮箱',
        'Telephone': '电话',
        'Mobile': '手机',
        'Message': '信息',
        'FOR QUOTE': '请求报价',
        'We are requesting you to give your best price': '请求您提供最优价格',
        'with the packing list': '及装箱单',
        'For the items in the attached files': '关于附件中的产品',
        'Appreciate if you could take this on your urgent consideration to check': '感谢您紧急考虑并检查',
        'Good day': '您好',
        'Dear Sir': '尊敬的先生',
        'Thanks & Best Regards': '感谢并致以最诚挚的问候',
        'Sales & Manager': '销售经理',
        'OMFB': 'OMFB',
        'Type': '类型',
        'No.': '编号',
        'Description': '描述',
        'Qty': '数量',
        'capacity': '容量',
        'flow rate': '流量',
        'head': '扬程',
        'pressure': '压力',
        'power': '功率',
        'voltage': '电压',
        'complete controls': '完整控制',
        'accessories': '配件',
    }

    # 单位翻译
    units = {
        '2HP': '2马力',
        '2HP,': '2马力，',
        '2HP ': '2马力 ',
        '130 PSI': '130 PSI（磅/平方英寸）',
        '220V': '220V（伏）',
        '220V /': '220V / ',
        '20gpm': '20 GPM（加仑/分钟）',
        '3ph': '3相',
        '3ph,': '3相，',
        '2hp': '2马力',
        '230v': '230V',
        '60hz': '60Hz',
        '195ft': '195英尺',
        'TDH': '总扬程',
    }

    # 合并词典
    all_terms = {}
    all_terms.update(technical_terms)
    all_terms.update(units)

    # 按长度降序排序
    sorted_terms = sorted(all_terms.items(), key=lambda x: -len(x[0]))

    translated = line
    for en, cn in sorted_terms:
        pattern = re.compile(re.escape(en), re.IGNORECASE)
        translated = pattern.sub(cn, translated)

    return translated

if __name__ == "__main__":
    # 测试翻译
    subject = "[Inquiry] JOCKEY PUMP 2HP, 130 PSI, 220V / 20gpm, 3ph"
    body = """Website:www.yangtzeriverpump.com
Company Name：O.M. Manufacturing Philippines, Inc.
Contact：UNIQUA CHARMAINE LIWANAG
E-mail：uniquacharmaineliwanag@gmail.com
Message： JOCKEY PUMP 2HP, 130 PSI, 220V / 20gpm, 3ph,2hp 230v 60hz195ft TDH with complete controls and accessories FOR QUOTE"""

    result = translate_email_to_chinese(subject, body)
    print("翻译结果：")
    print(result)
