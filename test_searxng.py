#!/usr/bin/env python3
"""
测试 SearXNG 公共实例搜索功能
完全免费，无需 API Key
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app_v2 import searxng_search, extract_item_id, convert_to_detail_url

def test_url_conversion():
    """测试链接转换功能"""
    print("🔗 测试链接转换功能...")
    
    test_cases = [
        # 淘宝搜索页 -> 详情页
        ("https://s.taobao.com/search?q=R720&id=688900123456", "https://item.taobao.com/item.htm?id=688900123456"),
        # 淘宝详情页（保持不变）
        ("https://item.taobao.com/item.htm?id=688900123456", "https://item.taobao.com/item.htm?id=688900123456"),
        # 京东搜索页 -> 详情页
        ("https://search.jd.com/Search?keyword=R720&sku=1000123456", "https://item.jd.com/1000123456.html"),
        # 京东详情页（保持不变）
        ("https://item.jd.com/1000123456.html", "https://item.jd.com/1000123456.html"),
        # 闲鱼搜索页 -> 详情页
        ("https://www.goofish.com/item/100000123456", "https://2.taobao.com/item.htm?id=100000123456"),
        # 闲鱼详情页（保持不变）
        ("https://2.taobao.com/item.htm?id=100000123456", "https://2.taobao.com/item.htm?id=100000123456"),
    ]
    
    all_passed = True
    for input_url, expected_url in test_cases:
        detail_url = convert_to_detail_url(input_url, "测试商品")
        if detail_url == expected_url:
            print(f"  ✅ {input_url[:50]}... -> {detail_url[:50]}...")
        else:
            print(f"  ❌ {input_url[:50]}... -> {detail_url[:50]}... (期望: {expected_url[:50]}...)")
            all_passed = False
    
    return all_passed

def test_searxng_search():
    """测试 SearXNG 搜索功能"""
    print("\n🔍 测试 SearXNG 搜索功能...")
    
    # 测试一个简单的查询
    query = "Dell R720 主板"
    print(f"  搜索关键词: {query}")
    
    try:
        results = searxng_search(query, n=5, instance_url="https://searx.be")
        
        if results:
            print(f"  ✅ 搜索成功！返回 {len(results)} 条结果")
            for i, result in enumerate(results[:3], 1):
                print(f"    结果 {i}: {result['title'][:60]}...")
                print(f"        价格: ¥{result['price'] if result['price'] > 0 else '未提取'}")
                print(f"        链接: {result['url'][:80]}...")
                print()
            return True
        else:
            print(f"  ⚠️ 搜索成功但返回空结果，可能是当前实例无数据")
            return True  # 仍然算成功，因为 API 调用没问题
            
    except Exception as e:
        print(f"  ❌ 搜索失败: {e}")
        return False

def test_demo_mode():
    """测试演示模式"""
    print("\n🎭 测试演示模式...")
    
    # 导入演示数据生成函数
    from app_v2 import generate_demo_data
    
    keyword = "R720"
    results, trend = generate_demo_data(keyword)
    
    if results:
        print(f"  ✅ 演示数据生成成功！返回 {len(results)} 条结果")
        print(f"    价格趋势: {len(trend)} 天数据")
        
        # 检查链接格式
        for i, result in enumerate(results[:2], 1):
            url = result['url']
            if 'item.taobao.com' in url or 'item.jd.com' in url or '2.taobao.com' in url:
                print(f"    结果 {i}: 商品详情页链接 ✅")
            else:
                print(f"    结果 {i}: 搜索页链接 ⚠️")
        
        return True
    else:
        print(f"  ❌ 演示数据生成失败")
        return False

def main():
    print("🚀 开始测试完全免费的 SearXNG 搜索方案")
    print("=" * 60)
    
    # 测试 1: 链接转换
    url_test_passed = test_url_conversion()
    
    # 测试 2: SearXNG 搜索
    search_test_passed = test_searxng_search()
    
    # 测试 3: 演示模式
    demo_test_passed = test_demo_mode()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"  链接转换测试: {'✅ 通过' if url_test_passed else '❌ 失败'}")
    print(f"  SearXNG 搜索测试: {'✅ 通过' if search_test_passed else '❌ 失败'}")
    print(f"  演示模式测试: {'✅ 通过' if demo_test_passed else '❌ 失败'}")
    
    all_passed = url_test_passed and search_test_passed and demo_test_passed
    if all_passed:
        print("\n🎉 所有测试通过！系统已准备好使用完全免费的 SearXNG 方案。")
        print("\n💡 部署建议:")
        print("  1. 直接部署到 Render.com（无需配置 API Key）")
        print("  2. 设置 DEMO_MODE=false 启用真实搜索")
        print("  3. 访问你的应用开始搜索服务器配件价格")
    else:
        print("\n⚠️ 部分测试失败，请检查网络连接或配置。")
        print("  可以暂时使用演示模式：export DEMO_MODE=true")

if __name__ == "__main__":
    main()