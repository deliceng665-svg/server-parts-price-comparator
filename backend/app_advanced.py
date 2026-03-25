"""
服务器配件价格对比查询工具 - 增强版后端
使用 Brave Search + agent-browser 进行深度搜索
"""

import json
import subprocess
import re
import time
import os
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, 
            static_folder=os.path.join(BASE_DIR, 'static'),
            template_folder=BASE_DIR)
CORS(app)

# 演示模式（默认开启）
DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'

# Brave Search 路径
BRAVE_SEARCH_BIN = os.path.join(os.path.dirname(__file__), '../../.workbuddy/skills/brave-search/search.js')


def run_brave_search(query, count=15):
    """使用 Brave Search 搜索"""
    skill_path = os.path.expanduser('~/.workbuddy/skills/brave-search/search.js')
    cmd = f'node {skill_path} "{query}" -n {count}'
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout
    except Exception as e:
        print(f"Brave Search 错误: {e}")
        return ""


def run_agent_command(command):
    """执行 agent-browser 命令"""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=60
    )
    return result.stdout, result.stderr


def parse_brave_results(output):
    """解析 Brave Search 结果"""
    results = []
    current_item = {}
    
    for line in output.split('\n'):
        line = line.strip()
        
        if line.startswith('--- Result'):
            if current_item:
                results.append(current_item)
            current_item = {}
        elif line.startswith('Title:'):
            current_item['title'] = line.replace('Title:', '').strip()
        elif line.startswith('Link:'):
            current_item['link'] = line.replace('Link:', '').strip()
        elif line.startswith('Snippet:'):
            current_item['snippet'] = line.replace('Snippet:', '').strip()
    
    if current_item:
        results.append(current_item)
    
    return results


def get_product_price_with_agent(url, platform):
    """使用 agent-browser 获取商品详情页的价格"""
    try:
        cmd = f'agent-browser --session price-check open "{url}" && agent-browser --session price-check wait --load networkidle && agent-browser --session price-check wait 2000'
        stdout, stderr = run_agent_command(cmd)
        
        # 提取价格
        js_code = '''
        (function() {
            // 尝试多种价格选择器
            const selectors = [
                '.price', '.Price', '.price-value', '.goods-price', '.product-price',
                '[class*="price"]', '#price', '.j_% price', '.salePrice', '.promoPrice',
                'strong.price', 'span[class*="price"]', 'div[class*="price"]'
            ];
            
            for (let sel of selectors) {
                const el = document.querySelector(sel);
                if (el) {
                    const text = el.textContent || el.innerText;
                    const match = text.match(/\\d+(?:,\\d{3})*(?:\\.\\d{2})?/);
                    if (match) return { price: match[0].replace(',', ''), selector: sel };
                }
            }
            
            // 备用：从页面文本中搜索价格
            const bodyText = document.body.innerText;
            const priceMatch = bodyText.match(/(?:¥|￥|价格|券后)[:\\s]*(\\d+(?:\\.\\d{1,2})?)/);
            if (priceMatch) return { price: priceMatch[1], selector: 'body-text' };
            
            return null;
        })()
        '''
        
        cmd = f'agent-browser --session price-check eval --stdin <<\'JSEOF\'\n{js_code}\nJSEOF'
        stdout, _ = run_agent_command(cmd)
        
        run_agent_command('agent-browser --session price-check close')
        
        try:
            data = json.loads(stdout)
            if data and data.get('price'):
                return int(float(data['price']))
        except:
            pass
        
        return None
    except Exception as e:
        print(f"获取价格失败: {e}")
        run_agent_command('agent-browser --session price-check close 2>/dev/null || true')
        return None


def extract_price_from_snippet(snippet, url):
    """从搜索摘要中提取价格"""
    # 尝试匹配各种价格格式
    patterns = [
        r'¥\s*(\d+(?:\.\d{1,2})?)',
        r'￥\s*(\d+(?:\.\d{1,2})?)',
        r'价格[：:]\s*(\d+(?:\.\d{1,2})?)',
        r'(\d+)元',
        r'券后\s*(\d+(?:\.\d{1,2})?)',
        r'(\d+(?:\.\d{1,2})?)\s*元',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, snippet)
        if match:
            return int(float(match.group(1)))
    
    return None


def determine_platform(url):
    """根据 URL 判断平台"""
    if 'taobao' in url or 'tmall' in url:
        return 'taobao'
    elif 'goofish' in url or 'xianyu' in url:
        return 'xianyu'
    elif 'jd.com' in url or '360buy' in url:
        return 'jd'
    elif '1688' in url:
        return '1688'
    elif 'pinpin' in url:
        return 'pinpin'
    return 'other'


def search_taobao_products(keyword):
    """搜索淘宝/天猫商品"""
    print(f"搜索淘宝: {keyword}")
    results = []
    
    # 使用 Brave Search 搜索
    query = f"{keyword} 淘宝 闲鱼价格 site:taobao.com OR site:tmall.com"
    output = run_brave_search(query, 15)
    brave_results = parse_brave_results(output)
    
    for item in brave_results[:10]:
        url = item.get('link', '')
        if not url or 'taobao' not in url and 'tmall' not in url:
            continue
        
        price = extract_price_from_snippet(item.get('snippet', ''), url)
        
        # 清理标题
        title = item.get('title', '').strip()
        title = re.sub(r'【.*?】', '', title).strip()
        title = re.sub(r'\[.*?\]', '', title).strip()
        
        if title and (price or url):
            results.append({
                'platform': 'taobao',
                'title': title[:100],
                'price': price,
                'url': url,
                'source': 'brave'
            })
    
    print(f"淘宝: 找到 {len(results)} 条")
    return results


def search_xianyu_products(keyword):
    """搜索闲鱼商品"""
    print(f"搜索闲鱼: {keyword}")
    results = []
    
    # 使用 Brave Search 搜索
    query = f"{keyword} 闲鱼 二手"
    output = run_brave_search(query, 15)
    brave_results = parse_brave_results(output)
    
    for item in brave_results[:10]:
        url = item.get('link', '')
        if not url:
            continue
        
        platform = determine_platform(url)
        if platform != 'xianyu':
            continue
        
        price = extract_price_from_snippet(item.get('snippet', ''), url)
        
        title = item.get('title', '').strip()
        
        if title:
            results.append({
                'platform': 'xianyu',
                'title': title[:100],
                'price': price,
                'url': url,
                'source': 'brave'
            })
    
    print(f"闲鱼: 找到 {len(results)} 条")
    return results


def search_jd_products(keyword):
    """搜索京东商品"""
    print(f"搜索京东: {keyword}")
    results = []
    
    # 使用 Brave Search 搜索
    query = f"{keyword} 京东自营 site:jd.com"
    output = run_brave_search(query, 15)
    brave_results = parse_brave_results(output)
    
    for item in brave_results[:10]:
        url = item.get('link', '')
        if not url or 'jd.com' not in url:
            continue
        
        price = extract_price_from_snippet(item.get('snippet', ''), url)
        
        title = item.get('title', '').strip()
        
        if title:
            results.append({
                'platform': 'jd',
                'title': title[:100],
                'price': price,
                'url': url,
                'source': 'brave'
            })
    
    print(f"京东: 找到 {len(results)} 条")
    return results


def generate_demo_data(keyword):
    """生成演示数据"""
    print(f"生成演示数据: {keyword}")
    
    demo_templates = [
        {
            'pattern': r'R720|Dell.*主板',
            'platform': 'taobao',
            'items': [
                {'title': 'Dell R720 服务器主板 全新拆机 0FW88J', 'price': 185, 'url': 'https://item.taobao.com/item.htm?id=6889123456'},
                {'title': 'Dell PowerEdge R720 主板 0FW88J 性能稳定', 'price': 320, 'url': 'https://item.taobao.com/item.htm?id=6889234567'},
                {'title': 'R720 服务器主板 含原装挡板 质保三个月', 'price': 420, 'url': 'https://item.taobao.com/item.htm?id=6889345678'},
                {'title': 'Dell R720 主板 高配版 支持双路CPU', 'price': 580, 'url': 'https://item.taobao.com/item.htm?id=6889456789'},
                {'title': 'R720 0FW88J 主板 二手9成新 测试正常', 'price': 380, 'url': 'https://item.taobao.com/item.htm?id=6889567890'},
            ]
        },
        {
            'pattern': r'R720|Dell.*主板',
            'platform': 'xianyu',
            'items': [
                {'title': 'Dell R720 主板 二手拆机 自用闲置出', 'price': 168, 'url': 'https://www.goofish.com/goods/1000123456'},
                {'title': 'R720 服务器主板 9成新 送导轨', 'price': 195, 'url': 'https://www.goofish.com/goods/1000234567'},
                {'title': 'Dell R720 主板 单卖 不含CPU', 'price': 175, 'url': 'https://www.goofish.com/goods/1000345678'},
                {'title': '服务器升级换代 R720主板便宜出', 'price': 158, 'url': 'https://www.goofish.com/goods/1000456789'},
            ]
        },
        {
            'pattern': r'R720|Dell.*主板',
            'platform': 'jd',
            'items': [
                {'title': 'Dell R720 服务器主板 官方正品', 'price': 680, 'url': 'https://item.jd.com/100012345678.html'},
                {'title': '戴尔 PowerEdge R720 主板 含一年质保', 'price': 720, 'url': 'https://item.jd.com/100023456789.html'},
                {'title': 'Dell 服务器配件 R720主板 全新', 'price': 650, 'url': 'https://item.jd.com/100034567890.html'},
            ]
        },
        {
            'pattern': r'Xeon|6130|E5.*26',
            'platform': 'taobao',
            'items': [
                {'title': 'Intel Xeon 6130 处理器 16核32线程', 'price': 890, 'url': 'https://item.taobao.com/item.htm?id=5889123456'},
                {'title': 'Xeon E5-2680 v4 14核28线程 服务器CPU', 'price': 650, 'url': 'https://item.taobao.com/item.htm?id=5889234567'},
                {'title': 'Intel Xeon Gold 6130 全新盒装三年质保', 'price': 1200, 'url': 'https://item.taobao.com/item.htm?id=5889345678'},
                {'title': 'Xeon E5-2678 v3 12核24线程 稳定版', 'price': 480, 'url': 'https://item.taobao.com/item.htm?id=5889456789'},
                {'title': 'Intel Xeon 6148 20核40线程 高端CPU', 'price': 1580, 'url': 'https://item.taobao.com/item.htm?id=5889567890'},
            ]
        },
        {
            'pattern': r'Xeon|6130|E5.*26',
            'platform': 'xianyu',
            'items': [
                {'title': 'Xeon 6130 二手CPU 便宜出了', 'price': 780, 'url': 'https://www.goofish.com/goods/2000123456'},
                {'title': 'E5-2680v4 14核 测试正常 自用升级出', 'price': 520, 'url': 'https://www.goofish.com/goods/2000234567'},
                {'title': 'Intel Xeon E5-2678 v3 两颗打包', 'price': 680, 'url': 'https://www.goofish.com/goods/2000345678'},
                {'title': '服务器淘汰 Xeon CPU 全部好价', 'price': 450, 'url': 'https://www.goofish.com/goods/2000456789'},
            ]
        },
        {
            'pattern': r'Xeon|6130|E5.*26',
            'platform': 'jd',
            'items': [
                {'title': 'Intel Xeon 6130 官方旗舰店', 'price': 1450, 'url': 'https://item.jd.com/2000123456.html'},
                {'title': 'Xeon E5-2680 v4 京东自营 正品保障', 'price': 880, 'url': 'https://item.jd.com/2000234567.html'},
                {'title': 'Intel Xeon Gold系列 6130 官方正品', 'price': 1350, 'url': 'https://item.jd.com/2000345678.html'},
            ]
        },
        {
            'pattern': r'DDR4|ECC|32GB|16GB.*内存',
            'platform': 'taobao',
            'items': [
                {'title': '32GB DDR4 ECC RDIMM 服务器内存 Samsung', 'price': 280, 'url': 'https://item.taobao.com/item.htm?id=3889123456'},
                {'title': 'Samsung 32G DDR4 ECC RDIMM 全新原装', 'price': 320, 'url': 'https://item.taobao.com/item.htm?id=3889234567'},
                {'title': '16GB DDR4 ECC 服务器内存 2133频率', 'price': 150, 'url': 'https://item.taobao.com/item.htm?id=3889345678'},
                {'title': 'Hynix 32GB DDR4 ECC 服务器专用内存', 'price': 295, 'url': 'https://item.taobao.com/item.htm?id=3889456789'},
                {'title': '4GB DDR4 ECC 低价出 服务器拆机', 'price': 68, 'url': 'https://item.taobao.com/item.htm?id=3889567890'},
            ]
        },
        {
            'pattern': r'DDR4|ECC|32GB|16GB.*内存',
            'platform': 'xianyu',
            'items': [
                {'title': '32GB DDR4 ECC 内存 自用闲置出', 'price': 245, 'url': 'https://www.goofish.com/goods/3000123456'},
                {'title': '服务器 DDR4 ECC 16G 两条打包出', 'price': 180, 'url': 'https://www.goofish.com/goods/3000234567'},
                {'title': 'Samsung 32G DDR4 ECC 99新', 'price': 265, 'url': 'https://www.goofish.com/goods/3000345678'},
                {'title': '服务器升级换下 8G DDR4 ECC 便宜出', 'price': 85, 'url': 'https://www.goofish.com/goods/3000456789'},
            ]
        },
        {
            'pattern': r'DDR4|ECC|32GB|16GB.*内存',
            'platform': 'jd',
            'items': [
                {'title': '32GB DDR4 ECC 服务器内存 京东自营', 'price': 450, 'url': 'https://item.jd.com/3000123456.html'},
                {'title': 'Samsung 16GB DDR4 ECC 正品保障', 'price': 260, 'url': 'https://item.jd.com/3000234567.html'},
                {'title': 'Kingston 32GB DDR4 ECC 服务器内存', 'price': 380, 'url': 'https://item.jd.com/3000345678.html'},
            ]
        },
    ]
    
    results = []
    
    # 匹配模板
    for template in demo_templates:
        if re.search(template['pattern'], keyword, re.IGNORECASE):
            for item in template['items']:
                item_copy = item.copy()
                # 添加价格波动 ±10%
                price_variation = random.uniform(-0.1, 0.1)
                item_copy['price'] = int(item_copy['price'] * (1 + price_variation))
                results.append(item_copy)
    
    # 如果没有匹配，生成通用数据
    if not results:
        platforms = [
            ('taobao', '淘宝', 'https://item.taobao.com/item.htm?id='),
            ('xianyu', '闲鱼', 'https://www.goofish.com/goods/'),
            ('jd', '京东', 'https://item.jd.com/')
        ]
        
        for platform_id, platform_name, base_url in platforms:
            for i in range(random.randint(4, 6)):
                base_price = random.randint(100, 2000)
                results.append({
                    'platform': platform_id,
                    'title': f'{keyword} {platform_name}商品 #{i+1}',
                    'price': base_price,
                    'url': f'{base_url}{random.randint(1000000000, 9999999999)}'
                })
    
    return results


def search_all_platforms(keyword):
    """搜索所有平台"""
    if DEMO_MODE:
        return generate_demo_data(keyword)
    
    all_results = []
    
    # 并发搜索三个平台
    import threading
    
    results_lock = threading.Lock()
    
    def search_platform(search_func):
        results = search_func(keyword)
        with results_lock:
            all_results.extend(results)
    
    threads = [
        threading.Thread(target=search_platform, args=(search_taobao_products,)),
        threading.Thread(target=search_platform, args=(search_xianyu_products,)),
        threading.Thread(target=search_platform, args=(search_jd_products,)),
    ]
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    return all_results


@app.route('/')
def index():
    """主页"""
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/api/search', methods=['POST'])
def search():
    """搜索接口"""
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'error': '请输入搜索关键词'}), 400
    
    print(f"\n{'='*50}")
    print(f"搜索请求: {keyword}")
    print(f"演示模式: {DEMO_MODE}")
    print(f"{'='*50}")
    
    results = search_all_platforms(keyword)
    
    # 过滤掉没有价格的结果
    results = [r for r in results if r.get('price')]
    
    print(f"搜索完成: {len(results)} 条结果")
    
    return jsonify({
        'keyword': keyword,
        'results': results,
        'count': len(results),
        'demo_mode': DEMO_MODE
    })


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'demo_mode': DEMO_MODE})


if __name__ == '__main__':
    print("="*60)
    print("服务器配件价格对比查询工具 - 增强版")
    print("="*60)
    print(f"演示模式: {'启用' if DEMO_MODE else '禁用'}")
    print("="*60)
    app.run(host='0.0.0.0', port=5001, debug=True)
