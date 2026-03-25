# Google Custom Search API 极速配置指南（5分钟完成）

## 📋 当前状态
✅ **代码已更新**：支持 Google Custom Search API  
✅ **商品详情页**：点击直接跳转商品页面（非搜索列表）  
⚠️ **需要配置**：API Key 和 Search Engine ID

## 🚀 5分钟配置步骤

### 第1步：获取 Google API Key（2分钟）
1. 访问：https://console.cloud.google.com/
2. **新建项目** → 项目名：`server-parts-search` → 创建
3. 左侧菜单：**API 和服务** → **库**
4. 搜索 "Custom Search JSON API" → **启用**
5. 左侧菜单：**API 和服务** → **凭据**
6. 点击 **创建凭据** → **API 密钥**
7. 复制生成的 **API 密钥**（形如 `AIzaSyD...abc`）

### 第2步：创建 Custom Search Engine（2分钟）
1. 访问：https://programmablesearchengine.google.com/
2. 点击 **新建搜索引擎**
3. **要搜索的网站**（每行一个）：
   ```
   *.taobao.com/*
   *.tmall.com/*
   *.jd.com/*
   *.goofish.com/*
   ```
4. **搜索引擎名称**：`Server Parts Search`
5. 点击 **创建**
6. 复制 **搜索引擎 ID**（形如 `012345678901234567890:abcdefg`）

### 第3步：配置到 Render（1分钟）
1. 打开：https://dashboard.render.com/
2. 找到你的 `server-parts-price-comparator` 服务
3. 点击 **Environment**
4. 添加两个环境变量：

| 环境变量 | 值 | 说明 |
|----------|-----|------|
| `GOOGLE_API_KEY` | `AIzaSyD...abc` | 第1步的 API 密钥 |
| `GOOGLE_CSE_ID` | `012345678901234567890:abcdefg` | 第2步的搜索引擎 ID |

5. 服务会自动重新部署（2-3分钟）

## 🎯 功能验证

### 配置成功后：
1. 访问：https://server-parts-price-comparator.onrender.com
2. 搜索 `R720 主板`
3. 点击结果中的 **"去淘宝查看"**
4. **验证**：应该直接跳转到 **商品详情页**（不是搜索列表）

### 链接类型对比：
| 状态 | 链接类型 | 示例 |
|------|----------|------|
| **配置前** | 搜索页 | `https://s.taobao.com/search?q=R720` |
| **配置后** | 商品详情页 | `https://item.taobao.com/item.htm?id=123456789012` |

## 🔧 技术细节

### 已实现功能：
1. **智能链接转换**：自动将搜索页链接转为商品详情页
2. **价格提取**：从商品描述中提取价格
3. **多平台支持**：淘宝、京东、闲鱼
4. **演示模式**：未配置 API 时自动使用演示数据
5. **错误处理**：API 失败时自动降级到演示模式

### 支持的链接转换：
- `s.taobao.com/search?q=...&id=123` → `item.taobao.com/item.htm?id=123`
- `item.jd.com/123.html` → 保持不变（已经是详情页）
- `goofish.com/item/123` → `2.taobao.com/item.htm?id=123`

## ⚠️ 注意事项

### 免费额度：
- **每天 100 次搜索**（足够个人使用）
- 超出后第二天自动恢复
- 可以在 Google Cloud Console 查看使用量

### 限制：
- 搜索结果仅限配置的网站（淘宝、京东、闲鱼）
- 需要正确配置中国区域（已设置 `gl=cn` `cr=countryCN`）

### 故障排除：
- **403错误**：API 密钥未启用或配置错误
- **400错误**：搜索引擎 ID 不正确
- **无结果**：未正确配置要搜索的网站
- **仍显示搜索页**：无法提取商品 ID，保持为搜索页

## 📞 快速帮助

### 如果遇到问题：
1. **检查环境变量**：确保两个环境变量都正确配置
2. **查看日志**：在 Render Dashboard 查看服务日志
3. **测试 API**：在浏览器中测试：
   ```
   https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_CSE_ID&q=R720+taobao
   ```

### 备用方案：
如果 Google API 配置太复杂，可以使用：
1. **公共 SearXNG 实例**：无需配置，立即使用
2. **DuckDuckGo HTML 解析**：完全免费，无限制

---

## ✅ 完成标志
当你点击搜索结果能直接跳转到 **商品详情页** 时，说明配置成功！

**预计完成时间：5-10分钟** ⏱️