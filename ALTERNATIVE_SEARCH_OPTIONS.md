# 备选搜索方案（完全免费无限制）

如果不想申请 Google API，这里有 **完全免费无限制** 的方案：

## 方案 A：SearXNG 自建搜索引擎（推荐）

**优点：**
- 完全免费
- 无查询次数限制
- 支持多个搜索引擎（Google、Bing、DuckDuckGo 等）
- 隐私保护

### 部署方法：

#### 1. 一键部署到 Railway（最简单）
```bash
# 创建 Railway 项目
# 模板：https://github.com/searxng/searxng-docker
# Railway 会自动部署
```

#### 2. 获取 API 接口
部署后访问：
```
https://你的-searxng-实例地址/search?q=R720&format=json&language=zh-CN
```

#### 3. 修改代码使用 SearXNG
在 `app_v2.py` 中添加：

```python
import requests

def searxng_search(query, n=20, instance_url="https://searx.example.com"):
    """
    使用 SearXNG 自建搜索引擎
    """
    try:
        params = {
            'q': query,
            'format': 'json',
            'language': 'zh-CN',
            'safesearch': 0,
        }
        
        response = requests.get(f"{instance_url}/search", params=params, timeout=15)
        data = response.json()
        
        items = []
        for result in data.get('results', [])[:n]:
            items.append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'snippet': result.get('content', ''),
            })
        return items
    except Exception as e:
        print(f"[SearXNG Error] {e}")
        return []
```

## 方案 B：DuckDuckGo HTML 解析（无需 API）

**优点：**
- 完全免费
- 无需注册
- 简单直接

```python
import requests
from bs4 import BeautifulSoup

def duckduckgo_search(query, n=20):
    """
    解析 DuckDuckGo 搜索结果
    """
    try:
        # 直接访问网页版
        url = f"https://html.duckduckgo.com/html/?q={query}+site:taobao.com"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = []
        results = soup.find_all('a', class_='result__url')
        
        for result in results[:n]:
            link_elem = result.find_next_sibling('a', class_='result__snippet')
            if link_elem:
                items.append({
                    'title': link_elem.text[:100],
                    'url': result.get('href', ''),
                    'snippet': link_elem.text,
                })
        return items
    except Exception as e:
        print(f"[DuckDuckGo Error] {e}")
        return []
```

## 方案 C：使用公共 SearXNG 实例（无需部署）

**公共实例列表：**
- https://searx.be/
- https://search.disroot.org/
- https://searx.tiekoetter.com/

**使用示例：**
```python
# 直接调用公共实例
brave_search = searxng_search(instance_url="https://searx.be")
```

## 方案 D：Bing Web Search API（免费 1000次/月）

**申请：**
1. 访问：https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
2. 创建 Azure 账户（有免费额度）
3. 获取 API Key

**配置：**
```python
def bing_search(query, n=20):
    subscription_key = os.getenv('BING_API_KEY')
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": query, "count": n, "responseFilter": "Webpages"}
    
    response = requests.get(endpoint, headers=headers, params=params)
    return response.json()['webPages']['value']
```

## 📊 方案对比

| 方案 | 免费额度 | 配置难度 | 稳定性 | 推荐度 |
|------|---------|---------|--------|--------|
| **Google Custom Search** | 100次/天 | 中等 | 高 | ⭐⭐⭐⭐ |
| **SearXNG 自建** | 无限制 | 中等 | 中高 | ⭐⭐⭐⭐⭐ |
| **SearXNG 公共实例** | 无限制 | 简单 | 中 | ⭐⭐⭐⭐ |
| **DuckDuckGo HTML** | 无限制 | 简单 | 中低 | ⭐⭐⭐ |
| **Bing API** | 1000次/月 | 中等 | 高 | ⭐⭐⭐⭐ |

## 🚀 快速开始建议

### 想立即使用：
1. 使用 **SearXNG 公共实例**（无需配置）
2. 修改代码中的 `instance_url` 参数

### 想长期稳定：
1. 部署 **SearXNG 到 Railway**（30分钟）
2. 配置到 Render 环境变量

### 想最简单：
1. 直接使用 **DuckDuckGo HTML 解析**
2. 代码已提供，无需 API Key

## 🔧 代码集成

选择任一方案后，只需替换 `app_v2.py` 中的 `brave_search` 函数即可。

**默认使用 Google API**，如需切换，修改：
```python
# 启用 SearXNG
# brave_search = searxng_search(instance_url="https://searx.be")

# 启用 DuckDuckGo
# brave_search = duckduckgo_search

# 启用 Bing
# brave_search = bing_search
```

## 💡 提示

1. **SearXNG 是最佳选择**：免费、无限制、多搜索引擎聚合
2. **Google API 适合简单使用**：每天100次足够个人用
3. **多实例备用**：可以配置多个搜索源，一个失败时自动切换
4. **缓存结果**：对相同查询缓存结果，减少 API 调用