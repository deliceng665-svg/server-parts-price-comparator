#!/usr/bin/env python3
"""
测试 Google Custom Search API 功能
"""

import os
import sys
import json

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量（模拟 Render 环境）
os.environ['DEMO_MODE'] = 'false'

# 测试函数
def test_google_search():
    """测试 Google Custom Search API"""
    try:
        from backend.app_v2 import google_search, extract_item_id, convert_to_detail_url
        
        print("=" * 60)
        print("Google Custom Search API 功能测试")
        print("=" * 60)
        
        # 测试链接提取功能
        print("\n1. 测试商品ID提取功能：")
        
        test_urls = [
            "https://s.taobao.com/search?q=R720&id=123456789012",
            "https://item.taobao.com/item.htm?id=987654321098",
            "https://detail.tmall.com/item.htm?id=555555555555",
            "https://item.jd.com/123456.html",
            "https://goofish.com/item/888888888888",
        ]
        
        for url in test_urls:
            item_id = extract_item_id(url)
            detail_url = convert_to_detail_url(url)
            print(f"  {url[:50]}...")
            print(f"    商品ID: {item_id}")
            print(f"    详情页: {detail_url[:60]}...")
            print()
        
        # 测试 Google API 配置
        print("2. 测试 Google API 配置：")
        
        # 检查环境变量
        api_key = os.getenv('GOOGLE_API_KEY', '')
        cse_id = os.getenv('GOOGLE_CSE_ID', '')
        
        if api_key and cse_id:
            print(f"  ✅ API Key 已配置: {api_key[:10]}...")
            print(f"  ✅ CSE ID 已配置: {cse_id[:20]}...")
            
            # 测试搜索（如果有配置）
            print(f"  🔍 测试搜索 'R720'...")
            results = google_search("R720", 3)
            print(f"    返回 {len(results)} 条结果")
            
            if results:
                for i, item in enumerate(results[:2], 1):
                    print(f"    {i}. {item['title'][:50]}...")
                    print(f"       价格: {item.get('price', 'N/A')}")
                    print(f"       链接: {item['url'][:60]}...")
                    print(f"       平台: {item.get('platform', 'unknown')}")
        else:
            print("  ⚠️ 未配置 API Key 和 CSE ID")
            print("  ℹ️ 请按照 QUICK_SETUP_GOOGLE_API.md 配置")
            
            # 测试演示模式
            print(f"  🔍 测试演示模式...")
            from backend.app_v2 import generate_demo_data
            results, trend = generate_demo_data("R720")
            print(f"    演示数据: {len(results)} 条结果")
            
            if results:
                for i, item in enumerate(results[:2], 1):
                    print(f"    {i}. {item['title'][:50]}...")
                    print(f"       价格: {item.get('price', 'N/A')}")
                    print(f"       链接: {item['url'][:60]}...")
                    print(f"       平台: {item.get('platform', 'unknown')}")
        
        # 测试主搜索函数
        print("\n3. 测试主搜索函数：")
        from backend.app_v2 import search_keyword, DEMO_MODE
        
        if DEMO_MODE:
            print(f"  ℹ️ 当前为演示模式 (DEMO_MODE={DEMO_MODE})")
        else:
            print(f"  ℹ️ 当前为真实搜索模式 (DEMO_MODE={DEMO_MODE})")
        
        results, trend = search_keyword("R720")
        print(f"  搜索 'R720' 返回 {len(results)} 条结果")
        
        # 检查链接类型
        detail_count = sum(1 for r in results if 'item.taobao.com/item.htm' in r['url'] or 
                          'item.jd.com/' in r['url'] or 
                          '2.taobao.com/item.htm' in r['url'])
        search_count = sum(1 for r in results if 's.taobao.com/search' in r['url'] or 
                          'search.jd.com' in r['url'] or 
                          'goofish.com/search' in r['url'])
        
        print(f"  商品详情页链接: {detail_count} 条")
        print(f"  搜索页链接: {search_count} 条")
        
        if detail_count > 0:
            print("  ✅ 成功生成商品详情页链接！")
        else:
            print("  ⚠️ 未生成商品详情页链接，请检查配置")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_search()