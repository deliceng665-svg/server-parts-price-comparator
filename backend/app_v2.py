"""
服务器配件价格对比查询工具 v2
新增：批量查询、20+ 条结果、价格趋势、Brave Search 真实搜索
"""

import json, subprocess, re, time, os, random, threading, hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAVE_SEARCH_JS = os.path.expanduser('~/.workbuddy/skills/brave-search/search.js')
DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'
SESSION_NAME = "parts-search"
PORT = int(os.getenv('PORT', 5001))

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'))
CORS(app, origins='*')


# ─────────────────────────────────────────────
# Brave Search
# ─────────────────────────────────────────────
def brave_search(query, n=20):
    try:
        r = subprocess.run(
            f'node {BRAVE_SEARCH_JS} "{query}" -n {n}',
            shell=True, capture_output=True, text=True, timeout=30
        )
        return _parse_brave(r.stdout)
    except Exception as e:
        print(f"[Brave] {e}")
        return []

def _parse_brave(text):
    items, cur = [], {}
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('--- Result'):
            if cur: items.append(cur)
            cur = {}
        elif line.startswith('Title:'):   cur['title']   = line[6:].strip()
        elif line.startswith('Link:'):    cur['url']     = line[5:].strip()
        elif line.startswith('Snippet:'): cur['snippet'] = line[8:].strip()
    if cur: items.append(cur)
    return items


# ─────────────────────────────────────────────
# agent-browser
# ─────────────────────────────────────────────
def agent_run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    return r.stdout, r.stderr


# ─────────────────────────────────────────────
# 价格提取
# ─────────────────────────────────────────────
def extract_price(text):
    for pat in [r'[¥￥]\s*(\d[\d,]*(?:\.\d{1,2})?)',
                r'(\d[\d,]*(?:\.\d{1,2})?)\s*元',
                r'券后[：:]?\s*(\d+)',
                r'(\d{2,5})']:
        m = re.search(pat, text)
        if m:
            v = int(float(m.group(1).replace(',', '')))
            if 1 < v < 999999:
                return v
    return None

def platform_of(url):
    if not url: return 'other'
    if 'taobao' in url or 'tmall' in url: return 'taobao'
    if 'goofish' in url or 'xianyu' in url: return 'xianyu'
    if 'jd.com' in url or '360buy' in url: return 'jd'
    return 'other'


# ─────────────────────────────────────────────
# 生成演示价格趋势（近 7 天）
# ─────────────────────────────────────────────
def gen_trend(base_price):
    today = datetime.now()
    trend = []
    price = base_price
    for i in range(7, -1, -1):
        d = today - timedelta(days=i)
        price = max(int(price * random.uniform(0.92, 1.08)), 10)
        trend.append({'date': d.strftime('%m-%d'), 'price': price})
    return trend


# ─────────────────────────────────────────────
# 演示数据（20+ 条，高/中/低价段全覆盖）
# ─────────────────────────────────────────────
DEMO_DB = {
    r'R720': {
        'taobao': [
            ('Dell R720 服务器主板 0FW88J 全新拆机',          165, '6889001'),
            ('Dell R720 主板 0FW88J 带挡板 测试正常',          198, '6889002'),
            ('Dell PowerEdge R720 主板 原装 稳定',             240, '6889003'),
            ('R720 主板 高配版 支持双路 带 CPU 插槽',           310, '6889004'),
            ('Dell R720 主板 9 成新 含导轨 拆机出',             360, '6889005'),
            ('Dell R720 主板 带 iDRAC7 企业 Enterprise',       420, '6889006'),
            ('R720 服务器主板 原厂件 三个月质保',               490, '6889007'),
            ('Dell R720 主板 含散热器支架 全套出',             560, '6889008'),
        ],
        'xianyu': [
            ('Dell R720 主板 二手拆机 自用闲置',               140, '1000001'),
            ('R720 主板 单卖 不含 CPU 好价',                   155, '1000002'),
            ('服务器换代 R720 主板 便宜出了',                  160, '1000003'),
            ('Dell R720 主板 验货满意再付款',                  178, '1000004'),
            ('R720 主板 9 成新 送散热器',                      195, '1000005'),
            ('Dell R720 0FW88J 拆机主板 正常使用',             210, '1000006'),
            ('R720 主板两块打包 数据中心淘汰',                 350, '1000007'),
        ],
        'jd': [
            ('Dell R720 服务器主板 原厂认证',                  680, '100012001'),
            ('戴尔 PowerEdge R720 主板 全新',                  720, '100012002'),
            ('Dell 服务器配件 R720 主板 含一年质保',           780, '100012003'),
            ('Dell R720 主板 京东自营 急速配送',               850, '100012004'),
        ],
    },
    r'R730': {
        'taobao': [
            ('Dell R730 服务器主板 全新拆机 0H21J3',            280, '6890001'),
            ('Dell PowerEdge R730 主板 0H21J3 测试好',          330, '6890002'),
            ('R730 主板 含 iDRAC8 企业版 全功能',               420, '6890003'),
            ('Dell R730 主板 双路高配 支持 E5-2600v4',          520, '6890004'),
            ('R730 主板 9 成新 拆机出售',                       460, '6890005'),
            ('Dell R730 主板 带挡板 三个月质保',                380, '6890006'),
        ],
        'xianyu': [
            ('Dell R730 主板 二手 自用换代出',                  240, '1001001'),
            ('R730 主板 好价出 验货满意',                       260, '1001002'),
            ('Dell R730 主板 数据中心淘汰批量出',               310, '1001003'),
            ('R730 主板 测试正常 支持双路',                     280, '1001004'),
        ],
        'jd': [
            ('Dell R730 服务器主板 官方正品',                   860, '100013001'),
            ('戴尔 R730 主板 全新 含质保',                      920, '100013002'),
            ('Dell PowerEdge R730 主板 京东发货',               980, '100013003'),
        ],
    },
    r'Xeon.{0,4}6130|Gold.{0,4}6130': {
        'taobao': [
            ('Intel Xeon Gold 6130 16 核 32 线程 服务器 CPU',   840, '5889001'),
            ('Xeon 6130 盒装 三年质保 性能强劲',               1050, '5889002'),
            ('Intel Xeon Gold 6130 散片 测试满速',              800, '5889003'),
            ('Xeon Gold 6130 两颗打包 最优惠',                 1520, '5889004'),
            ('Intel 至强 6130 正显 功能完整',                   860, '5889005'),
            ('Xeon 6130 二手 9 成新 正常运行',                  720, '5889006'),
            ('Intel Xeon Gold 6130 拆机 无氧化',                750, '5889007'),
        ],
        'xianyu': [
            ('Xeon 6130 自用出 价格实惠',                       700, '2000001'),
            ('Intel 6130 服务器 CPU 测试无问题',                 720, '2000002'),
            ('Xeon Gold 6130 数据中心淘汰',                     650, '2000003'),
            ('6130 两颗 IDC 拆机打包出',                       1200, '2000004'),
            ('Xeon 6130 拆机 99 新',                            760, '2000005'),
        ],
        'jd': [
            ('Intel Xeon Gold 6130 官方授权店',                1380, '200001'),
            ('至强 6130 盒装 京东自营',                        1450, '200002'),
            ('Intel Xeon Gold 6130 CPU 正品保障',              1320, '200003'),
        ],
    },
    r'E5.{0,4}2680|E5.{0,4}2690': {
        'taobao': [
            ('Intel Xeon E5-2680 v4 14 核 28 线程',             580, '5880001'),
            ('E5-2680 v4 散片 全新正显',                        620, '5880002'),
            ('Xeon E5-2680v4 性能强 功耗低',                    600, '5880003'),
            ('E5-2680 v4 两颗打包超值',                        1050, '5880004'),
            ('Intel E5-2690 v4 14 核高主频版',                   780, '5880005'),
            ('E5-2680v4 拆机 9 成新 无氧化',                    540, '5880006'),
        ],
        'xianyu': [
            ('E5-2680v4 自用闲置 低价出',                       480, '2010001'),
            ('两颗 2680v4 IDC 淘汰机器拆机',                    900, '2010002'),
            ('E5-2680 v4 测试正常 好用',                        500, '2010003'),
            ('Xeon 2680v4 无氧化 成色好',                       520, '2010004'),
        ],
        'jd': [
            ('Intel E5-2680 v4 京东自营 正品',                   980, '300001'),
            ('Xeon E5-2680v4 官方旗舰 保真',                   1080, '300002'),
        ],
    },
    r'DDR4.{0,6}ECC|ECC.{0,6}DDR4|32G.{0,8}DDR4|16G.{0,8}DDR4': {
        'taobao': [
            ('16GB DDR4 ECC RDIMM 2133 服务器内存',             108, '3880001'),
            ('16GB DDR4 ECC 2400 Samsung 拆机',                 125, '3880002'),
            ('32GB DDR4 ECC RDIMM 2133 全新',                   260, '3880003'),
            ('32GB DDR4 ECC Samsung 原装 2400',                  295, '3880004'),
            ('32GB DDR4 ECC Hynix 2666 服务器内存',              310, '3880005'),
            ('64GB DDR4 ECC RDIMM 高频版',                      620, '3880006'),
            ('8GB DDR4 ECC 低价清仓',                            55, '3880007'),
            ('32GB DDR4 ECC 2 根打包 全套内存',                  520, '3880008'),
        ],
        'xianyu': [
            ('32GB DDR4 ECC 自用闲置 好价出',                   235, '3000001'),
            ('16G DDR4 ECC 两条 服务器拆机',                    180, '3000002'),
            ('DDR4 ECC 32G Samsung 99 新',                      250, '3000003'),
            ('服务器升级换下 32G DDR4 ECC',                     220, '3000004'),
            ('64G DDR4 ECC 两条 IDC 淘汰',                      580, '3000005'),
            ('8G DDR4 ECC 若干条 批量出',                        40, '3000006'),
        ],
        'jd': [
            ('32GB DDR4 ECC 服务器内存 京东自营',                420, '400001'),
            ('Samsung 32G DDR4 ECC 官方正品',                   460, '400002'),
            ('Kingston 16GB DDR4 ECC 服务器内存',               230, '400003'),
            ('Hynix 32GB DDR4 ECC 2666 正品',                   390, '400004'),
        ],
    },
    r'SSD|固态|SATA|NVMe': {
        'taobao': [
            ('企业级 SSD 1.92TB SATA 服务器专用',               680, '7880001'),
            ('Intel P4510 1TB NVMe 企业 SSD',                   920, '7880002'),
            ('三星 PM883 960GB SATA SSD',                       580, '7880003'),
            ('DELL 服务器 SSD 480GB SATA 拆机',                  260, '7880004'),
            ('Micron 5300 960GB SATA SSD',                      540, '7880005'),
            ('Intel S4510 480GB SATA 企业级',                   320, '7880006'),
            ('服务器 NVMe SSD 3.84TB 大容量',                  1680, '7880007'),
        ],
        'xianyu': [
            ('企业 SSD 960GB SATA 拆机出',                      380, '7000001'),
            ('Intel SSD 1.2TB NVMe 便宜出',                     720, '7000002'),
            ('SATA SSD 480GB 服务器拆机 好价',                  180, '7000003'),
            ('三星 PM883 960G SATA 自用出',                     500, '7000004'),
        ],
        'jd': [
            ('Intel 企业级 SSD 1.92TB SATA 京东',              1280, '700001'),
            ('Micron 5300 960GB SATA 正品',                     780, '700002'),
            ('三星 PM883 960G 企业 SSD',                         860, '700003'),
        ],
    },
}

def _match_demo(keyword):
    kw = keyword.strip()
    for pattern, data in DEMO_DB.items():
        if re.search(pattern, kw, re.I):
            return data
    return None

DEMO_SELLERS = {
    'taobao': ['数码配件专营店', '服务器零件铺', '云图IT配件', '企业IT直供', '矩阵二手数码', 'IDC拆机行'],
    'xianyu': ['IDC运维老王', '服务器发烧友', '二手IT淘淘', '机房小哥', '数字游民', '闲置数码达人'],
    'jd':     ['京东自营', 'Dell官方旗舰店', 'Intel官方旗舰', '超数码企业店', '云谷IT旗舰'],
}
DEMO_CONDITIONS = {
    'taobao': ['全新拆机', '9成新', '九五新', '全新未拆封', '二手测试好'],
    'xianyu': ['8成新', '9成新', '二手闲置', '全新拆机', '正常使用'],
    'jd':     ['全新', '全新正品', '原厂正品'],
}
DEMO_RATINGS = {
    'taobao': ['4.8', '4.9', '4.7', '5.0', '4.6'],
    'xianyu': ['信用良好', '芝麻信用800+', '实名认证卖家', '好评如潮', ''],
    'jd':     ['京东评分4.9', '4.8分', '99%好评', ''],
}
DEMO_SHIPPING = {
    'taobao': ['包邮', '快递12元', '顺丰包邮', '快递8元', '免运费'],
    'xianyu': ['同城可自提', '邮费到付', '包快递', '顺丰到付', ''],
    'jd':     ['京东配送', '次日达', '当日达', '免邮费'],
}

def _demo_extras(platform):
    return {
        'seller':   random.choice(DEMO_SELLERS.get(platform, [''])),
        'condition':random.choice(DEMO_CONDITIONS.get(platform, [''])),
        'rating':   random.choice(DEMO_RATINGS.get(platform, [''])),
        'shipping': random.choice(DEMO_SHIPPING.get(platform, [''])),
        'sales':    f'{random.randint(5,800)}笔' if platform != 'xianyu' else f'{random.randint(1,50)}次交易',
    }

def generate_demo_data(keyword):
    data = _match_demo(keyword)
    results = []

    # 搜索链接（点击后跳转到平台搜索页，而非具体商品页）
    import urllib.parse
    kw_enc = urllib.parse.quote(keyword)
    search_url_map = {
        'taobao':  f'https://s.taobao.com/search?q={kw_enc}',
        'xianyu':  f'https://www.goofish.com/search?q={kw_enc}',
        'jd':      f'https://search.jd.com/Search?keyword={kw_enc}',
    }

    if data:
        for platform, items in data.items():
            for title, base_price, pid in items:
                price = max(1, int(base_price * random.uniform(0.93, 1.07)))
                entry = {
                    'platform': platform,
                    'title':    title,
                    'price':    price,
                    'url':      search_url_map[platform],
                }
                entry.update(_demo_extras(platform))
                results.append(entry)
    else:
        # 通用随机数据
        for platform in ['taobao', 'xianyu', 'jd']:
            for i in range(random.randint(6, 9)):
                price = random.randint(50, 3000)
                entry = {
                    'platform': platform,
                    'title':    f'{keyword} {["全新", "二手", "拆机", "正品"][i%4]}商品 #{i+1}',
                    'price':    price,
                    'url':      search_url_map[platform],
                }
                entry.update(_demo_extras(platform))
                results.append(entry)
    
    # 生成趋势（基于最低价）
    prices = [r['price'] for r in results]
    trend  = gen_trend(min(prices)) if prices else []
    
    return results, trend


# ─────────────────────────────────────────────
# 真实搜索（Brave Search + agent-browser）
# ─────────────────────────────────────────────
def real_search_platform(keyword, platform_query, platform_id, out_list, lock):
    query = f'{keyword} {platform_query}'
    brave_items = brave_search(query, 25)
    
    local = []
    for item in brave_items:
        url  = item.get('url', '')
        p    = platform_of(url)
        if platform_id != 'any' and p != platform_id:
            continue
        price = extract_price(item.get('snippet', '') + ' ' + item.get('title', ''))
        title = re.sub(r'[-_|·—]+.*$', '', item.get('title', '')).strip()[:100]
        if title and price and 1 < price < 500000:
            local.append({'platform': p or platform_id, 'title': title, 'price': price, 'url': url})
    
    with lock:
        out_list.extend(local)

def real_search(keyword):
    all_results, lock = [], threading.Lock()
    tasks = [
        (f'{keyword} site:taobao.com OR site:tmall.com',   'taobao'),
        (f'{keyword} 闲鱼 二手 site:goofish.com',           'xianyu'),
        (f'{keyword} site:jd.com',                          'jd'),
    ]
    threads = [threading.Thread(target=real_search_platform,
                                args=(keyword, q, p, all_results, lock))
               for q, p in tasks]
    for t in threads: t.start()
    for t in threads: t.join()
    
    prices = [r['price'] for r in all_results]
    trend  = gen_trend(min(prices)) if prices else []
    return all_results, trend


# ─────────────────────────────────────────────
# 主搜索入口
# ─────────────────────────────────────────────
def search_keyword(keyword):
    if DEMO_MODE:
        return generate_demo_data(keyword)
    return real_search(keyword)


# ─────────────────────────────────────────────
# Flask 路由
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), path)


@app.route('/api/search', methods=['POST'])
def search():
    body = request.get_json() or {}
    raw  = body.get('keywords') or body.get('keyword') or ''
    
    # 批量：逗号 / 换行 分隔
    keywords = [k.strip() for k in re.split(r'[,，\n]+', raw) if k.strip()]
    if not keywords:
        return jsonify({'error': '请输入搜索关键词'}), 400
    
    batch = []
    for kw in keywords:
        results, trend = search_keyword(kw)
        if not results:
            continue
        prices = [r['price'] for r in results]
        batch.append({
            'keyword':  kw,
            'results':  results,
            'count':    len(results),
            'trend':    trend,
            'stats': {
                'min':    min(prices),
                'max':    max(prices),
                'avg':    round(sum(prices) / len(prices)),
                'median': sorted(prices)[len(prices) // 2],
                'by_platform': {
                    p: {
                        'min': min(r['price'] for r in results if r['platform'] == p),
                        'max': max(r['price'] for r in results if r['platform'] == p),
                        'avg': round(sum(r['price'] for r in results if r['platform'] == p)
                                     / len([r for r in results if r['platform'] == p]))
                    }
                    for p in ['taobao', 'xianyu', 'jd']
                    if any(r['platform'] == p for r in results)
                }
            }
        })
    
    return jsonify({'batch': batch, 'demo_mode': DEMO_MODE})


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'demo_mode': DEMO_MODE})


if __name__ == '__main__':
    print(f"[v2] 服务器启动 demo={DEMO_MODE}  http://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
