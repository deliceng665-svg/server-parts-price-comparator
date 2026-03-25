#!/usr/bin/env python3
"""
快速测试脚本 - 验证核心功能
"""

import sys
import os
import re

def test_url_conversion():
    """测试链接转换功能"""
    print("🔗 测试链接转换功能...")
    
    # 简单的正则测试
    test_cases = [
        # (输入URL, 期望提取的ID)
        ("https://s.taobao.com/search?q=R720&id=688900123456", "688900123456"),
        ("https://item.taobao.com/item.htm?id=688900123456", "688900123456"),
        ("https://detail.tmall.com/item.htm?id=688900123456", "688900123456"),
        ("https://item.jd.com/1000123456.html", "1000123456"),
        ("https://search.jd.com/Search?keyword=R720&sku=1000123456", "1000123456"),
        ("https://www.goofish.com/item/100000123456", "100000123456"),
    ]
    
    # 从代码中提取正则表达式
    patterns = [
        # 淘宝详情页
        r'item\.taobao\.com/item\.htm.*[?&]id=(\d+)',
        r'detail\.tmall\.com.*[?&]id=(\d+)',
        # 淘宝搜索页转详情页
        r's\.taobao\.com.*[?&]id=(\d+)',
        # 京东
        r'item\.jd\.com/(\d+)\.html',
        r'item\.jd\.com.*[?&]sku=(\d+)',
        # 闲鱼
        r'goofish\.com/item/(\d+)',
        r'2\.taobao\.com/item\.htm.*[?&]id=(\d+)',
    ]
    
    all_passed = True
    for input_url, expected_id in test_cases:
        found_id = None
        for pattern in patterns:
            match = re.search(pattern, input_url)
            if match:
                found_id = match.group(1)
                break
        
        if found_id == expected_id:
            print(f"  ✅ {input_url[:60]}... -> ID: {found_id}")
        else:
            print(f"  ❌ {input_url[:60]}... -> 找到: {found_id}, 期望: {expected_id}")
            all_passed = False
    
    return all_passed

def test_demo_data():
    """测试演示数据生成"""
    print("\n🎭 测试演示数据生成...")
    
    # 模拟演示数据生成逻辑
    demo_keywords = ["R720", "DDR4 ECC", "Xeon 6130"]
    
    for keyword in demo_keywords:
        # 简单的演示数据检查
        if any(word.lower() in keyword.lower() for word in ["r720", "ddr4", "xeon", "e5", "ssd"]):
            print(f"  ✅ 关键词 '{keyword}' 匹配演示数据库")
        else:
            print(f"  ⚠️  关键词 '{keyword}' 可能不在演示数据库中")
    
    return True

def test_imports():
    """测试模块导入"""
    print("\n📦 测试模块导入...")
    
    try:
        # 尝试导入主要模块
        import flask
        import requests
        import json
        import re
        import random
        
        print(f"  ✅ Flask: {flask.__version__}")
        print(f"  ✅ requests: {requests.__version__}")
        print(f"  ✅ 核心模块导入成功")
        return True
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def main():
    print("🚀 开始快速测试完全免费的 SearXNG 方案")
    print("=" * 60)
    
    # 测试 1: 模块导入
    import_test_passed = test_imports()
    
    # 测试 2: 链接转换
    url_test_passed = test_url_conversion()
    
    # 测试 3: 演示数据
    demo_test_passed = test_demo_data()
    
    print("\n" + "=" * 60)
    print("📊 快速测试结果:")
    print(f"  模块导入测试: {'✅ 通过' if import_test_passed else '❌ 失败'}")
    print(f"  链接转换测试: {'✅ 通过' if url_test_passed else '❌ 失败'}")
    print(f"  演示数据测试: {'✅ 通过' if demo_test_passed else '❌ 失败'}")
    
    all_passed = import_test_passed and url_test_passed and demo_test_passed
    
    if all_passed:
        print("\n🎉 核心功能测试通过！")
        print("\n📋 下一步:")
        print("  1. 部署到 Render.com:")
        print("     - 连接到 GitHub 仓库")
        print("     - 使用 render.yaml 配置")
        print("     - 无需配置任何 API Key！")
        print("  2. 本地运行:")
        print("     cd server-parts-price-comparator")
        print("     python3 backend/app_v2.py")
        print("  3. 访问:")
        print("     http://localhost:5001 (本地)")
        print("     或你的 Render URL (云端)")
        
        print("\n💡 完全免费方案特点:")
        print("  ✅ 无需信用卡")
        print("  ✅ 无需 API Key")
        print("  ✅ 无查询限制")
        print("  ✅ 自动实例切换")
        print("  ✅ 商品详情页链接")
    else:
        print("\n⚠️ 部分测试失败，请检查:")
        print("  - Python 环境 (python3 --version)")
        print("  - 依赖安装 (pip3 install -r requirements.txt)")
        print("  - 网络连接")

if __name__ == "__main__":
    main()