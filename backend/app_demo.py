"""
服务器配件价格对比查询工具 - 后端服务器（带演示模式）
使用 agent-browser 进行多平台数据采集
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

# 配置文件
SESSION_NAME = "server-parts-search"

# 演示模式 - 生成模拟数据（默认开启）
DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'


def run_agent_command(command):
    """执行 agent-browser 命令"""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    return result.stdout, result.stderr


def search_taobao(keyword):
    """搜索淘宝"""
    print(f"正在搜索淘宝: {keyword}")
    results = []

    try:
        # 打开淘宝搜索页面
        search_url = f"https://s.taobao.com/search?q={keyword.replace(' ', '+')}"
        cmd = f'agent-browser --session {SESSION_NAME} open "{search_url}" && agent-browser --session {SESSION_NAME} wait --load networkidle && agent-browser --session {SESSION_NAME} wait 3000'

        stdout, stderr = run_agent_command(cmd)
        print(f"淘宝页面加载完成")

        # 使用 JavaScript 提取商品数据
        js_code = '''
        (function() {
            const items = [];
            const elements = document.querySelectorAll('.item, .item-sku, .product-item');

            elements.slice(0, 10).forEach(item => {
                const titleElem = item.querySelector('.title, .productTitle, .itemTitle, .goods-title, a[title]');
                const priceElem = item.querySelector('.price, .productPrice, .itemPrice, .goods-price, strong');
                const linkElem = item.querySelector('a[href*="item"]');

                const title = titleElem?.textContent?.trim() || titleElem?.getAttribute('title') || '';
                const priceText = priceElem?.textContent || '';
                const link = linkElem?.href || '';

                if (title) {
                    const price = priceText.match(/\\d+(?:\\.\\d+)?/)?.[0];
                    if (price) {
                        items.push({ title, price: parseFloat(price), link });
                    }
                }
            });

            return JSON.stringify(items);
        })()
        '''

        cmd = f'agent-browser --session {SESSION_NAME} eval --stdin <<\'JSEOF\'\n{js_code}\nJSEOF'

        stdout, stderr = run_agent_command(cmd)

        # 解析结果
        try:
            items = json.loads(stdout)
            for item in items:
                link = item.get('link', '')
                if link and not link.startswith('http'):
                    link = 'https:' + link if link.startswith('//') else 'https://' + link

                results.append({
                    'platform': 'taobao',
                    'title': item['title'][:100],
                    'price': int(float(item['price'])),
                    'url': link
                })
        except (json.JSONDecodeError, ValueError) as e:
            print(f"淘宝解析失败: {e}")
            # 尝试备用方法
            results = extract_fallback_data(stdout, 'taobao')

    except Exception as e:
        print(f"淘宝搜索错误: {e}")

    return results


def search_xianyu(keyword):
    """搜索闲鱼"""
    print(f"正在搜索闲鱼: {keyword}")
    results = []

    try:
        # 打开闲鱼搜索页面
        search_url = f"https://www.goofish.com/search?q={keyword.replace(' ', '+')}&type=product"
        cmd = f'agent-browser --session {SESSION_NAME} open "{search_url}" && agent-browser --session {SESSION_NAME} wait --load networkidle && agent-browser --session {SESSION_NAME} wait 3000'

        stdout, stderr = run_agent_command(cmd)
        print(f"闲鱼页面加载完成")

        # 使用 JavaScript 提取商品数据
        js_code = '''
        (function() {
            const items = [];
            const elements = document.querySelectorAll('.feed-card, .product-item, .goods-item, .xianyu-item');

            elements.slice(0, 10).forEach(item => {
                const titleElem = item.querySelector('.title, .item-title, .goods-title, .product-title, a');
                const priceElem = item.querySelector('.price, .item-price, .goods-price, .product-price, strong');
                const linkElem = item.querySelector('a[href*="item"]');

                const title = titleElem?.textContent?.trim() || '';
                const priceText = priceElem?.textContent || '';
                const link = linkElem?.href || '';

                if (title) {
                    const price = priceText.match(/\\d+(?:\\.\\d+)?/)?.[0];
                    if (price) {
                        items.push({ title, price: parseFloat(price), link });
                    }
                }
            });

            return JSON.stringify(items);
        })()
        '''

        cmd = f'agent-browser --session {SESSION_NAME} eval --stdin <<\'JSEOF\'\n{js_code}\nJSEOF'

        stdout, stderr = run_agent_command(cmd)

        # 解析结果
        try:
            items = json.loads(stdout)
            for item in items:
                link = item.get('link', '')
                if link and not link.startswith('http'):
                    link = 'https://www.goofish.com' + link if link.startswith('/') else 'https://' + link

                results.append({
                    'platform': 'xianyu',
                    'title': item['title'][:100],
                    'price': int(float(item['price'])),
                    'url': link
                })
        except (json.JSONDecodeError, ValueError) as e:
            print(f"闲鱼解析失败: {e}")
            results = extract_fallback_data(stdout, 'xianyu')

    except Exception as e:
        print(f"闲鱼搜索错误: {e}")

    return results


def search_jd(keyword):
    """搜索京东"""
    print(f"正在搜索京东: {keyword}")
    results = []

    try:
        # 打开京东搜索页面
        search_url = f"https://search.jd.com/Search?keyword={keyword.replace(' ', '+')}&enc=utf-8"
        cmd = f'agent-browser --session {SESSION_NAME} open "{search_url}" && agent-browser --session {SESSION_NAME} wait --load networkidle && agent-browser --session {SESSION_NAME} wait 3000'

        stdout, stderr = run_agent_command(cmd)
        print(f"京东页面加载完成")

        # 使用 JavaScript 提取商品数据
        js_code = '''
        (function() {
            const items = [];
            const elements = document.querySelectorAll('.gl-item, .product-item, .jd-item');

            elements.slice(0, 10).forEach(item => {
                const titleElem = item.querySelector('.p-name em, .p-name, .goods-title');
                const priceElem = item.querySelector('.p-price i, .p-price, .goods-price');
                const linkElem = item.querySelector('.p-img a, .goods-img a');

                const title = titleElem?.textContent?.trim() || '';
                const priceText = priceElem?.textContent || '';
                const link = linkElem?.href || '';

                if (title) {
                    const price = priceText.match(/\\d+(?:\\.\\d+)?/)?.[0];
                    if (price) {
                        items.push({ title, price: parseFloat(price), link });
                    }
                }
            });

            return JSON.stringify(items);
        })()
        '''

        cmd = f'agent-browser --session {SESSION_NAME} eval --stdin <<\'JSEOF\'\n{js_code}\nJSEOF'

        stdout, stderr = run_agent_command(cmd)

        # 解析结果
        try:
            items = json.loads(stdout)
            for item in items:
                link = item.get('link', '')
                if link and not link.startswith('http'):
                    link = 'https:' + link if link.startswith('//') else 'https://' + link

                results.append({
                    'platform': 'jd',
                    'title': item['title'][:100],
                    'price': int(float(item['price'])),
                    'url': link
                })
        except (json.JSONDecodeError, ValueError) as e:
            print(f"京东解析失败: {e}")
            results = extract_fallback_data(stdout, 'jd')

    except Exception as e:
        print(f"京东搜索错误: {e}")

    return results


def extract_fallback_data(html_content, platform):
    """备用数据提取方法"""
    results = []
    # 从HTML内容中提取价格和标题
    price_matches = re.findall(r'(\d+(?:\.\d{1,2})?)', html_content)
    return results


def extract_price(price_str):
    """提取价格数字"""
    if not price_str:
        return None

    # 移除非数字字符
    price_str = price_str.replace('¥', '').replace('元', '').replace(',', '').strip()

    # 尝试匹配价格
    match = re.search(r'(\d+(?:\.\d{1,2})?)', price_str)
    if match:
        return int(float(match.group(1)))

    return None


def generate_demo_data(keyword):
    """生成演示数据"""
    print("使用演示模式")

    # 服务器配件示例数据
    demo_templates = [
        # Dell R720 相关
        {
            'keyword_pattern': r'R720',
            'platform': 'taobao',
            'items': [
                {'title': 'Dell R720 服务器主板 全新拆机', 'price': 185, 'url': 'https://item.taobao.com/item.htm?id=123'},
                {'title': 'Dell R720 主板 服务器配件 含CPU导轨', 'price': 420, 'url': 'https://item.taobao.com/item.htm?id=124'},
                {'title': 'Dell PowerEdge R720 主板 性能稳定', 'price': 580, 'url': 'https://item.taobao.com/item.htm?id=125'},
            ]
        },
        {
            'keyword_pattern': r'R720',
            'platform': 'xianyu',
            'items': [
                {'title': 'Dell R720 主板 二手拆机', 'price': 168, 'url': 'https://www.goofish.com/item/123'},
                {'title': 'R720 服务器主板 自提', 'price': 195, 'url': 'https://www.goofish.com/item/124'},
            ]
        },
        {
            'keyword_pattern': r'R720',
            'platform': 'jd',
            'items': [
                {'title': 'Dell R720 服务器主板 官方正品', 'price': 680, 'url': 'https://item.jd.com/123.html'},
                {'title': '戴尔R720 服务器主板 含保修', 'price': 720, 'url': 'https://item.jd.com/124.html'},
            ]
        },
        # Xeon CPU 相关
        {
            'keyword_pattern': r'Xeon\s*6130|Xeon\s*E5',
            'platform': 'taobao',
            'items': [
                {'title': 'Intel Xeon 6130 处理器 服务器CPU', 'price': 890, 'url': 'https://item.taobao.com/item.htm?id=200'},
                {'title': 'Xeon E5-2680 v4 14核28线程', 'price': 650, 'url': 'https://item.taobao.com/item.htm?id=201'},
                {'title': 'Intel Xeon Gold 6130 全新盒装', 'price': 1200, 'url': 'https://item.taobao.com/item.htm?id=202'},
            ]
        },
        {
            'keyword_pattern': r'Xeon\s*6130|Xeon\s*E5',
            'platform': 'xianyu',
            'items': [
                {'title': 'Xeon 6130 二手CPU 便宜出', 'price': 780, 'url': 'https://www.goofish.com/item/200'},
                {'title': 'E5-2680v4 14核 测试正常', 'price': 520, 'url': 'https://www.goofish.com/item/201'},
            ]
        },
        {
            'keyword_pattern': r'Xeon\s*6130|Xeon\s*E5',
            'platform': 'jd',
            'items': [
                {'title': 'Intel Xeon 6130 官方旗舰', 'price': 1450, 'url': 'https://item.jd.com/200.html'},
                {'title': 'Xeon E5 2680 v4 京东自营', 'price': 880, 'url': 'https://item.jd.com/201.html'},
            ]
        },
        # DDR4 ECC 内存相关
        {
            'keyword_pattern': r'DDR4.*ECC|ECC.*DDR4|32GB.*DDR4',
            'platform': 'taobao',
            'items': [
                {'title': '32GB DDR4 ECC 服务器内存 全新', 'price': 280, 'url': 'https://item.taobao.com/item.htm?id=300'},
                {'title': 'Samsung 32G DDR4 ECC RDIMM', 'price': 320, 'url': 'https://item.taobao.com/item.htm?id=301'},
                {'title': '16GB DDR4 ECC 服务器内存 拆机', 'price': 150, 'url': 'https://item.taobao.com/item.htm?id=302'},
            ]
        },
        {
            'keyword_pattern': r'DDR4.*ECC|ECC.*DDR4|32GB.*DDR4',
            'platform': 'xianyu',
            'items': [
                {'title': '32GB DDR4 ECC 内存 自用出', 'price': 245, 'url': 'https://www.goofish.com/item/300'},
                {'title': '服务器 DDR4 ECC 16G 两条', 'price': 180, 'url': 'https://www.goofish.com/item/301'},
            ]
        },
        {
            'keyword_pattern': r'DDR4.*ECC|ECC.*DDR4|32GB.*DDR4',
            'platform': 'jd',
            'items': [
                {'title': '32GB DDR4 ECC 服务器内存 京东自营', 'price': 450, 'url': 'https://item.jd.com/300.html'},
                {'title': 'Samsung 16GB DDR4 ECC 正品保障', 'price': 260, 'url': 'https://item.jd.com/301.html'},
            ]
        },
    ]

    results = []
    keyword_lower = keyword.lower()

    # 匹配模板
    for template in demo_templates:
        if re.search(template['keyword_pattern'], keyword, re.IGNORECASE):
            for item in template['items']:
                item_copy = item.copy()
                item_copy['platform'] = template['platform']
                # 添加一些随机价格波动
                price_variation = random.uniform(-0.1, 0.1)
                item_copy['price'] = int(item_copy['price'] * (1 + price_variation))
                results.append(item_copy)

    # 如果没有匹配，生成通用数据
    if not results:
        platforms = ['taobao', 'xianyu', 'jd']
        platform_names = {'taobao': '淘宝', 'xianyu': '闲鱼', 'jd': '京东'}

        for platform in platforms:
            for i in range(random.randint(2, 4)):
                base_price = random.randint(100, 1500)
                results.append({
                    'platform': platform,
                    'title': f'{keyword} {platform_names[platform]}商品 #{i+1}',
                    'price': base_price,
                    'url': f'https://{"item.taobao.com" if platform == "taobao" else "www.goofish.com" if platform == "xianyu" else "item.jd.com"}/demo_{i}'
                })

    return results


def search_all_platforms(keyword):
    """搜索所有平台"""
    all_results = []

    if DEMO_MODE:
        return generate_demo_data(keyword)

    # 关闭之前的会话（如果存在）
    run_agent_command(f'agent-browser --session {SESSION_NAME} close 2>/dev/null || true')

    # 淘宝搜索
    taobao_results = search_taobao(keyword)
    all_results.extend(taobao_results)
    print(f"淘宝: 找到 {len(taobao_results)} 条结果")
    time.sleep(2)

    # 闲鱼搜索
    xianyu_results = search_xianyu(keyword)
    all_results.extend(xianyu_results)
    print(f"闲鱼: 找到 {len(xianyu_results)} 条结果")
    time.sleep(2)

    # 京东搜索
    jd_results = search_jd(keyword)
    all_results.extend(jd_results)
    print(f"京东: 找到 {len(jd_results)} 条结果")

    # 关闭浏览器
    run_agent_command(f'agent-browser --session {SESSION_NAME} close')

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
    print(f"收到搜索请求: {keyword}")
    print(f"演示模式: {DEMO_MODE}")
    print(f"{'='*50}\n")

    # 执行搜索
    results = search_all_platforms(keyword)

    print(f"\n搜索完成，共找到 {len(results)} 条结果")
    if results:
        prices = [r['price'] for r in results]
        print(f"价格范围: ¥{min(prices)} - ¥{max(prices)}, 平均: ¥{sum(prices)//len(prices)}")
    print(f"{'='*50}\n")

    return jsonify({
        'keyword': keyword,
        'results': results,
        'count': len(results),
        'demo_mode': DEMO_MODE
    })


@app.route('/api/demo-toggle', methods=['POST'])
def demo_toggle():
    """切换演示模式"""
    global DEMO_MODE
    data = request.get_json()
    DEMO_MODE = data.get('enabled', DEMO_MODE)
    return jsonify({'demo_mode': DEMO_MODE})


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'demo_mode': DEMO_MODE})


if __name__ == '__main__':
    print("="*60)
    print("服务器配件价格对比查询工具")
    print("="*60)
    print(f"演示模式: {'启用' if DEMO_MODE else '禁用'}")
    print("启动服务器: http://localhost:5000")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=True)
