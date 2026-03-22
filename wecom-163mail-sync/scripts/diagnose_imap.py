#!/usr/bin/env python3
"""
163邮箱IMAP连接诊断工具
"""

import imaplib
import sys

def diagnose_imap():
    """诊断IMAP连接问题"""

    email = "gonggaotong2024@163.com"
    password = "XGnS37mV5Gpt2Jv6"
    server = "imap.163.com"
    port = 993

    print("=" * 50)
    print("163邮箱IMAP连接诊断")
    print("=" * 50)
    print(f"邮箱: {email}")
    print(f"服务器: {server}:{port}")
    print()

    # 测试1: 连接服务器
    print("测试1: 连接到IMAP服务器...")
    try:
        imap = imaplib.IMAP4_SSL(server, port)
        print("✅ 连接成功")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

    # 测试2: 登录
    print("\n测试2: 登录...")
    try:
        typ, data = imap.login(email, password)
        if typ == 'OK':
            print(f"✅ 登录成功: {data[0].decode()}")
        else:
            print(f"❌ 登录失败: {data}")
            return False
    except imaplib.IMAP4.error as e:
        print(f"❌ 登录失败: {e}")
        print()
        print("可能的原因:")
        print("1. IMAP服务未开启")
        print("2. 授权码不正确")
        print("3. 需要在163邮箱设置中开启\"第三方客户端授权\"")
        print()
        print("解决方法:")
        print("1. 登录163邮箱网页版")
        print("2. 进入 设置 -> POP3/SMTP/IMAP")
        print("3. 开启IMAP服务")
        print("4. 生成IMAP授权码（不是登录密码！）")
        return False

    # 测试3: 选择收件箱
    print("\n测试3: 选择收件箱...")
    try:
        typ, data = imap.select('INBOX')
        if typ == 'OK':
            print(f"✅ 选择收件箱成功: {data[0].decode()} 封邮件")
        else:
            print(f"⚠️  选择收件箱警告: {data}")
    except imaplib.IMAP4.error as e:
        print(f"❌ 选择收件箱失败: {e}")
        if "Unsafe Login" in str(e):
            print()
            print("⚠️  检测到 'Unsafe Login' 错误")
            print()
            print("这个错误通常意味着:")
            print("1. 163邮箱的安全策略阻止了第三方客户端")
            print("2. 需要在邮箱设置中授权此客户端")
            print()
            print("解决方法:")
            print("1. 登录163邮箱网页版")
            print("2. 查找是否有\"授权管理\"或\"客户端授权\"设置")
            print("3. 允许此应用访问")
            print("4. 或者使用\"应用密码\"功能")
        return False

    # 测试4: 搜索邮件
    print("\n测试4: 搜索邮件...")
    try:
        typ, data = imap.search(None, 'ALL')
        if typ == 'OK':
            email_count = len(data[0].split())
            print(f"✅ 搜索成功，共 {email_count} 封邮件")
        else:
            print(f"❌ 搜索失败: {data}")
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False

    # 关闭连接
    imap.close()
    imap.logout()

    print()
    print("=" * 50)
    print("✅ 所有测试通过！IMAP连接正常")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = diagnose_imap()
    sys.exit(0 if success else 1)
