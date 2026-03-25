"""
服务器配件价格对比查询工具 - 后端服务器
使用 agent-browser 进行多平台数据采集
"""

import json
import subprocess
import re
import time
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

# 配置文件
SESSION_NAME = "server-parts-search"


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

        # 截取页面快照
        cmd = f'agent-browser --session {SESSION_NAME} snapshot -i'
        stdout, stderr = run_agent_command(cmd)

        # 使用 JavaScript 提取商品数据
        js_code = '''
        JSON.stringify({
            items: Array.from(document.querySelectorAll('.item')).slice(0, 10).map(item => {
                const title = item.querySelector('.title')?.textContent || '';
                const price = item.querySelector('.price')?.textContent || '';
                const link = item.querySelector('a')?.href || '';
                return { title, price, link };
            })
        })
        '''

        cmd = f'agent-browser --session {SESSION_NAME} eval --stdin <<\'JSEOF\'\n{js_code}
JSEOF'

        stdout, stderr = run_agent_command(cmd)

        # 解析结果
        try:
            data = json.loads(stdout)
            for item in data.get('items', []):
                if item.get('title') and item.get('price'):
                    price = extract_price(item['price'])
                    if price:
                        results.append({
                            'platform': 'taobao',
                            'title': item['title'].strip(),
                            'price': price,
                            'url': item['link'] if item['link'].startswith('http') else f"https:{item['link']}"
                        })
        except json.JSONDecodeError:
            print(f"淘宝解析失败: {stdout[:200]}")

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

        # 截取页面快照
        cmd = f'agent-browser --session {SESSION_NAME} snapshot -i'
        stdout, stderr = run_agent_command(cmd)

        # 使用 JavaScript 提取商品数据
        js_code = '''
        JSON.stringify({
            items: Array.from(document.querySelectorAll('.feed-card')).slice(0, 10).map(item => {
                const title = item.querySelector('.title')?.textContent || item.querySelector('.item-title')?.textContent || '';
                const price = item.querySelector('.price')?.textContent || item.querySelector('.item-price')?.textContent || '';
                const link = item.querySelector('a')?.href || '';
                return { title, price, link };
            })
        })
        '''

        cmd = f'agent-browser --session {SESSION_NAME} eval --stdin <<\'JSEOF\'\n{js_code}
JSEOF'

        stdout, stderr = run_agent_command(cmd)

        # 解析结果
        try:
            data = json.loads(stdout)
            for item in data.get('items', []):
                if item.get('title') and item.get('price'):
                    price = extract_price(item['price'])
                    if price:
                        results.append({
                            'platform': 'xianyu',
                            'title': item['title'].strip(),
                            'price': price,
                            'url': item['link'] if item['link'].startswith('http') else f"https://www.goofish.com{item['link']}"
                        })
        except json.JSONDecodeError:
            print(f"闲鱼解析失败: {stdout[:200]}")

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

        # 截取页面快照
        cmd = f'agent-browser --session {SESSION_NAME} snapshot -i'
        stdout, stderr = run_agent_command(cmd)

        # 使用 JavaScript 提取商品数据
        js_code = '''
        JSON.stringify({
            items: Array.from(document.querySelectorAll('.gl-item')).slice(0, 10).map(item => {
                const title_elem = item.querySelector('.p-name em') || item.querySelector('.p-name');
                const title = title_elem?.textContent || '';
                const price = item.querySelector('.p-price i')?.textContent || item.querySelector('.p-price')?.textContent || '';
                const link = item.querySelector('.p-img a')?.href || '';
                return { title, price, link };
            })
        })
        '''

        cmd = f'agent-browser --session {SESSION_NAME} eval --stdin <<\'JSEOF\'\n{js_code}
JSEOF'

        stdout, stderr = run_agent_command(cmd)

        # 解析结果
        try:
            data = json.loads(stdout)
            for item in data.get('items', []):
                if item.get('title') and item.get('price'):
                    price = extract_price(item['price'])
                    if price:
                        results.append({
                            'platform': 'jd',
                            'title': item['title'].strip(),
                            'price': price,
                            'url': item['link'] if item['link'].startswith('http') else f"https://{item['link']}"
                        })
        except json.JSONDecodeError:
            print(f"京东解析失败: {stdout[:200]}")

    except Exception as e:
        print(f"京东搜索错误: {e}")

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


def search_all_platforms(keyword):
    """搜索所有平台"""
    all_results = []

    # 关闭之前的会话（如果存在）
    run_agent_command(f'agent-browser --session {SESSION_NAME} close 2>/dev/null || true')

    # 淘宝搜索
    taobao_results = search_taobao(keyword)
    all_results.extend(taobao_results)
    time.sleep(1)

    # 闲鱼搜索
    xianyu_results = search_xianyu(keyword)
    all_results.extend(xianyu_results)
    time.sleep(1)

    # 京东搜索
    jd_results = search_jd(keyword)
    all_results.extend(jd_results)

    # 关闭浏览器
    run_agent_command(f'agent-browser --session {SESSION_NAME} close')

    return all_results


@app.route('/')
def index():
    """主页"""
    return send_from_directory('.', 'index.html')


@app.route('/api/search', methods=['POST'])
def search():
    """搜索接口"""
    data = request.get_json()
    keyword = data.get('keyword', '').strip()

    if not keyword:
        return jsonify({'error': '请输入搜索关键词'}), 400

    print(f"收到搜索请求: {keyword}")

    # 执行搜索
    results = search_all_platforms(keyword)

    print(f"搜索完成，共找到 {len(results)} 条结果")

    return jsonify({
        'keyword': keyword,
        'results': results,
        'count': len(results)
    })


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    print("启动服务器...")
    app.run(host='0.0.0.0', port=5000, debug=True)
