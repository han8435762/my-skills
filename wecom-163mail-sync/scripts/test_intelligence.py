#!/usr/bin/env python3
"""
测试智能字段识别功能
"""

import sys
import os

# 添加脚本路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from fetch_emails import extract_country_from_email, extract_product_category, extract_relevance

def test_country_extraction():
    """测试国家识别"""
    print("=" * 60)
    print("测试国家识别功能")
    print("=" * 60)

    test_cases = [
        {
            'subject': 'Inquiry from USA customer',
            'body': 'We are interested in your products',
            'from_email': 'customer@example.com',
            'expected': '美国'
        },
        {
            'subject': '询问产品价格',
            'body': '来自日本的客户询价',
            'from_email': 'customer@jp.co.jp',
            'expected': '日本'
        },
        {
            'subject': 'Product inquiry',
            'body': 'We are from Germany',
            'from_email': 'customer@de-company.de',
            'expected': '德国'
        },
        {
            'subject': 'Hello',
            'body': 'Just a general inquiry',
            'from_email': 'customer@unknown.xyz',
            'expected': '未识别'
        }
    ]

    for i, case in enumerate(test_cases, 1):
        result = extract_country_from_email(case['subject'], case['body'], case['from_email'])
        status = "✅" if result == case['expected'] else "❌"
        print(f"\n{i}. {status}")
        print(f"   主题: {case['subject']}")
        print(f"   邮箱: {case['from_email']}")
        print(f"   识别结果: {result}")
        print(f"   期望结果: {case['expected']}")

def test_product_category_extraction():
    """测试产品类目识别"""
    print("\n" + "=" * 60)
    print("测试产品类目识别功能")
    print("=" * 60)

    test_cases = [
        {
            'subject': 'Inquiry about mobile phones',
            'body': 'We are looking for smartphone suppliers',
            'expected': '电子产品'
        },
        {
            'subject': 'Dress and shirt inquiry',
            'body': 'Fashion clothing items needed',
            'expected': '服装服饰'
        },
        {
            'subject': 'Home furniture',
            'body': 'Looking for sofa and table',
            'expected': '家居用品'
        },
        {
            'subject': 'General inquiry',
            'body': 'Just asking for information',
            'expected': '其他'
        }
    ]

    for i, case in enumerate(test_cases, 1):
        result = extract_product_category(case['subject'], case['body'])
        status = "✅" if result == case['expected'] else "❌"
        print(f"\n{i}. {status}")
        print(f"   主题: {case['subject']}")
        print(f"   识别结果: {result}")
        print(f"   期望结果: {case['expected']}")

def test_relevance_extraction():
    """测试相关度评估"""
    print("\n" + "=" * 60)
    print("测试相关度评估功能")
    print("=" * 60)

    test_cases = [
        {
            'subject': 'Price inquiry for bulk order',
            'body': 'We want to purchase 1000 units, please quote',
            'expected': '高'
        },
        {
            'subject': 'Product catalog request',
            'body': 'Can you send me your product list?',
            'expected': '中'
        },
        {
            'subject': 'Hello',
            'body': 'Just saying hi',
            'expected': '低'
        }
    ]

    for i, case in enumerate(test_cases, 1):
        result = extract_relevance(case['subject'], case['body'])
        status = "✅" if result == case['expected'] else "❌"
        print(f"\n{i}. {status}")
        print(f"   主题: {case['subject']}")
        print(f"   评估结果: {result}")
        print(f"   期望结果: {case['expected']}")

if __name__ == "__main__":
    print("\n🧪 智能字段识别功能测试\n")

    test_country_extraction()
    test_product_category_extraction()
    test_relevance_extraction()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
