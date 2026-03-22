#!/usr/bin/env python3
"""
测试泵行业智能识别功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from fetch_emails import extract_country, extract_pump_type, extract_quality_grade, extract_recipient_name

def test_all_recognitions():
    """综合测试所有识别功能"""
    print("=" * 80)
    print("泵行业智能识别功能测试")
    print("=" * 80)

    test_cases = [
        {
            'name': '菲律宾询盘 - 稳压泵',
            'subject': '[Inquiry] JOCKEY PUMP 2HP, 130 PSI, 220V / 20gpm, 3ph',
            'body': '''Website:www.yangtzeriverpump.com
Company Name：O.M. Manufacturing Philippines, Inc.
Contact：UNIQUA CHARMAINE LIWANAG
E-mail：uniquacharmaineliwanag@gmail.com
Message： JOCKEY PUMP 2HP, 130 PSI, 220V / 20gpm, 3ph,2hp 230v 60hz195ft TDH with complete controls and accessories FOR QUOTE''',
            'from': 'uniquacharmaineliwanag@gmail.com',
            'from_str': 'UNIQUA CHARMAINE LIWANAG <uniquacharmaineliwanag@gmail.com>',
            'expected': {
                'country': '菲律宾',
                'pump_type': '稳压泵',
                'quality_grade': 'C',
                'recipient': 'UNIQUA CHARMAINE LIWANAG'
            }
        },
        {
            'name': '伊拉克询价 - 液压手动泵',
            'subject': 'AMS-26-0182',
            'body': '''Dear Sir,

Good day

We are requesting you to give your best price with the packing list. For the items in the attached files
Appreciate if you could take this on your urgent consideration to check

No | Description | Qty
1 | OMFB - Hydraulic Hand Pump Type: FULCRO - PMI 45-S/5+VS | 2

Thanks & Best Regards

Eng.Alan khalil.
Sales & Manager''',
            'from': 'alan.khalil@iraq-company.com',
            'from_str': 'Eng.Alan khalil <alan.khalil@iraq-company.com>',
            'expected': {
                'country': '伊拉克',
                'pump_type': '液压手动泵',
                'quality_grade': 'C',
                'recipient': 'Eng.Alan khalil'
            }
        },
        {
            'name': '印尼投诉 - 离心泵故障',
            'subject': 'URGENT: Centrifugal Pump Not Working',
            'body': '''Dear Support,

Our centrifugal pump is not working after 2 months of use.
The pump makes loud noise and vibration.
We need urgent repair or replacement.

This is a serious problem affecting our production.

Best regards,
LINZ QUA
Indonesia''',
            'from': 'linz.qua@indo-factory.com',
            'from_str': 'LINZ QUA <linz.qua@indo-factory.com>',
            'expected': {
                'country': '印尼',
                'pump_type': '离心泵',
                'quality_grade': 'A',
                'recipient': 'LINZ QUA'
            }
        },
        {
            'name': '美国咨询 - 增压泵备件',
            'subject': 'Inquiry for Booster Pump Spare Parts',
            'body': '''Hi,

We are looking for spare parts for our booster pump model BP-200.
Could you please send us the catalog and price list?

Thank you,
John Smith
USA''',
            'from': 'john.smith@us-corporation.com',
            'from_str': 'John Smith <john.smith@us-corporation.com>',
            'expected': {
                'country': '美国',
                'pump_type': '增压泵',
                'quality_grade': 'C',
                'recipient': 'John Smith'
            }
        },
        {
            'name': '泰国维修 - 手动泵更换部件',
            'subject': 'RE: Hand Pump Repair',
            'body': '''Dear Sir,

We need to replace the worn-out parts of our hand pump.
Please quote for the repair kit.

Best regards,
SomchaiWang
Bangkok, Thailand''',
            'from': 'somchai@thai-water.com',
            'from_str': 'Somchai Wang <somchai@thai-water.com>',
            'expected': {
                'country': '泰国',
                'pump_type': '手动泵',
                'quality_grade': 'B',
                'recipient': 'Somchai Wang'
            }
        },
        {
            'name': '阿联酋询价 - 化工泵',
            'subject': 'Chemical Pump Inquiry from Dubai',
            'body': '''We need a chemical pump for our new plant in Dubai.
Capacity: 100 m3/h
Head: 50m
Material: Stainless steel

Please provide quotation.

Best regards''',
            'from': 'info@dubai-chemical.ae',
            'from_str': 'Dubai Chemical <info@dubai-chemical.ae>',
            'expected': {
                'country': '阿联酋',
                'pump_type': '化工泵',
                'quality_grade': 'C',
                'recipient': 'Dubai Chemical'
            }
        }
    ]

    passed = 0
    failed = 0

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试用例 {i}: {case['name']}")
        print(f"{'='*80}")

        # 执行识别
        country = extract_country(case['subject'], case['body'], case['from'])
        pump_type = extract_pump_type(case['subject'], case['body'])
        quality_grade = extract_quality_grade(case['subject'], case['body'])
        recipient = extract_recipient_name(case['from_str'])

        # 验证结果
        results = {
            'country': (country, case['expected']['country']),
            'pump_type': (pump_type, case['expected']['pump_type']),
            'quality_grade': (quality_grade, case['expected']['quality_grade']),
            'recipient': (recipient, case['expected']['recipient'])
        }

        all_correct = True
        for field, (actual, expected) in results.items():
            status = "✅" if actual == expected else "❌"
            if actual != expected:
                all_correct = False
            print(f"{status} {field:15s}: {actual:30s} (期望: {expected})")

        if all_correct:
            passed += 1
            print(f"\n✅ 测试通过！")
        else:
            failed += 1
            print(f"\n❌ 测试失败！")

    print(f"\n{'='*80}")
    print(f"测试总结")
    print(f"{'='*80}")
    print(f"总计: {len(test_cases)} 个测试用例")
    print(f"通过: {passed} 个 ✅")
    print(f"失败: {failed} 个 ❌")
    print(f"通过率: {passed/len(test_cases)*100:.1f}%")
    print(f"{'='*80}")

    return failed == 0

if __name__ == "__main__":
    success = test_all_recognitions()
    sys.exit(0 if success else 1)
