# 完全免费搜索方案 - SearXNG 公共实例

## 🎯 方案优势

**完全免费**，无需：
- ❌ 绑定信用卡
- ❌ 注册账号  
- ❌ 申请 API Key
- ❌ 配置 CSE ID

**无限制查询**，不受：
- ❌ 每日次数限制
- ❌ 每月额度限制
- ❌ IP 限制
- ❌ 付费升级

## 🔧 工作原理

系统使用 **SearXNG 公共实例** 进行搜索：

1. **SearXNG** 是一个开源元搜索引擎
2. 它会同时查询多个搜索引擎（Google、Bing、DuckDuckGo等）
3. 将结果聚合后返回
4. 我们使用了多个公共实例作为备份，一个失败自动切换到另一个

## 📋 已配置的公共实例

```python
SEARXNG_INSTANCES = [
    "https://searx.be",
    "https://search.disroot.org", 
    "https://searx.tiekoetter.com",
    "https://searx.info",
    "https://searx.work"
]
```

## 🚀 快速部署

### 方式一：直接部署到 Render（推荐）

1. 访问 [render.com](https://render.com)
2. 点击 "New +" → "Web Service"
3. 连接到你的 GitHub 仓库
4. 配置如下：
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --chdir backend app_v2:app --bind 0.0.0.0:$PORT`
   - **Python Version:** `3.11.0`
   - **Environment Variable:** `DEMO_MODE=false`

5. 点击 "Create Web Service"，等待部署完成

### 方式二：本地运行

```bash
# 1. 进入项目目录
cd server-parts-price-comparator

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 运行后端
cd backend
python app_v2.py

# 6. 浏览器访问
http://localhost:5001
```

## ⚙️ 配置选项

### 1. 完全免费模式（默认）
无需任何配置，直接使用即可。

### 2. 演示模式
如果需要完全离线演示：
```bash
export DEMO_MODE=true
```

### 3. 自定义 SearXNG 实例
如果你想使用自己的实例：
```python
# 修改 app_v2.py 中的 SEARXNG_INSTANCES 列表
SEARXNG_INSTANCES = [
    "https://your-searxng-instance.com"
]
```

## 🔍 搜索逻辑

1. **智能平台识别**：自动识别淘宝、天猫、京东、闲鱼链接
2. **商品详情页转换**：将搜索结果页链接转换为商品详情页链接
3. **价格提取**：从搜索结果中自动提取价格
4. **多线程搜索**：同时搜索淘宝、闲鱼、京东三个平台

## 📊 性能特点

- ✅ **零成本**：完全免费，无需付费
- ✅ **高可用**：多个公共实例自动切换
- ✅ **隐私保护**：SearXNG 不记录用户数据
- ✅ **多引擎**：聚合 Google、Bing 等多个搜索引擎结果
- ✅ **自动降级**：如果搜索失败，自动使用演示数据

## 🛠️ 故障排除

### 问题：搜索返回空结果
**原因：** 当前公共实例可能暂时不可用
**解决：** 系统会自动尝试下一个实例，或者可以：
1. 等待几分钟后重试
2. 手动切换到另一个实例
3. 使用演示模式：`export DEMO_MODE=true`

### 问题：链接无法点击
**原因：** 某些电商平台可能有反爬虫机制
**解决：**
1. 链接是真实可用的，但在某些情况下可能需要手动复制到浏览器
2. 系统已尽可能转换为商品详情页链接

### 问题：价格提取不准确
**原因：** 搜索结果中的价格格式多样
**解决：**
1. 系统会尽量从 snippet 中提取价格
2. 用户也可以根据标题和商品成色判断大致价格范围

## 💡 使用建议

1. **直接部署到 Render**：最简单快捷的方式
2. **使用具体关键词**：如 "Dell R720 主板" 比 "R720" 更好
3. **批量查询**：可以一次输入多个关键词，用逗号或换行分隔
4. **检查商品成色**：注意标题中的"全新"、"二手"、"拆机"等关键词

## 📞 技术支持

- **GitHub Issues**: 提交问题和建议
- **SearXNG 社区**: https://github.com/searxng/searxng
- **实时状态监控**: 查看控制台日志了解搜索状态

## 🎉 开始使用

现在你的服务器配件价格对比查询器已经**完全免费**可用！无需任何付费 API，立即部署即可开始搜索服务器配件价格。

**一句话总结：** 零成本、零配置、零限制的完全免费方案！