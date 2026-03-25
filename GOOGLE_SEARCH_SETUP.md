# Google Custom Search API 免费配置指南

## 🎯 免费额度
- **每天 100 次搜索**
- **每月 10000 次搜索**（足够个人使用）

## 📝 申请步骤（完全免费）

### 1. 创建 Google Cloud 项目
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 点击左上角项目下拉菜单 → **新建项目**
3. 项目名：`server-parts-search`（任意）
4. 点击 **创建**

### 2. 启用 Google Custom Search JSON API
1. 在左侧菜单选择 **API 和服务** → **库**
2. 搜索 "Custom Search JSON API"
3. 点击进入 → **启用**

### 3. 创建 API 密钥
1. 左侧菜单：**API 和服务** → **凭据**
2. 点击 **创建凭据** → **API 密钥**
3. 复制生成的 **API 密钥**（形如 `AIzaSyD...abc`）

### 4. 创建 Custom Search Engine (CSE)
1. 访问 [Custom Search Engine 控制台](https://programmablesearchengine.google.com/)
2. 点击 **新建搜索引擎**
3. **要搜索的网站**：填写以下网站（每行一个）：
   ```
   *.taobao.com/*
   *.tmall.com/*
   *.jd.com/*
   *.goofish.com/*
   ```
4. **搜索引擎名称**：`Server Parts Price Search`
5. 点击 **创建**
6. 在搜索结果页面，找到 **搜索引擎 ID**（形如 `012345678901234567890:abcdefg`）
7. 复制 **搜索引擎 ID**

### 5. 测试搜索
1. 在浏览器中测试搜索 API：
   ```
   https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_CSE_ID&q=R720+taobao
   ```
2. 确认能返回淘宝商品信息

## 🔧 配置到 Render

### 在 Render Dashboard 配置：
1. 打开 https://dashboard.render.com/
2. 找到你的 `server-parts-price-comparator` 服务
3. 点击 **Environment**
4. 添加两个环境变量：

| Key | Value | 备注 |
|-----|-------|------|
| `GOOGLE_API_KEY` | `AIzaSyD...abc` | 第3步创建的 API 密钥 |
| `GOOGLE_CSE_ID` | `012345678901234567890:abcdefg` | 第4步创建的搜索引擎 ID |

### 重新部署
1. 配置完成后，服务会自动重新部署
2. 等待 2-3 分钟完成

## 🚀 验证功能

### 测试步骤：
1. 访问：https://server-parts-price-comparator.onrender.com
2. 输入关键词：`R720 主板`
3. 点击 **查询**
4. 结果中的链接应该是 **商品详情页** 而不是搜索页

### 预期结果：
- 显示真实的淘宝/闲鱼/京东商品
- 价格从商品描述中提取
- 点击"去淘宝查看" → 直接跳转商品详情页

## ⚠️ 注意事项

### 权限配置：
1. 在 Google Cloud Console → **API 和服务** → **凭据**
2. 点击你的 API 密钥 → **API 限制**
3. 选择 **限制密钥** → 只勾选 **Custom Search JSON API**
4. 点击 **保存**

### 限制：
- 每天 100 次查询限制，超出后第二天恢复
- 搜索结果仅限配置的网站（淘宝、京东、闲鱼等）
- 可能需要配置中国区域 `gl=cn` `cr=countryCN`

### 故障排除：
- **403错误**：API 密钥未启用或配置错误
- **400错误**：搜索引擎 ID 不正确
- **无结果**：未正确配置要搜索的网站
- **搜索页链接**：无法提取商品 ID，保持为搜索页

## 📞 支持
如有问题，可：
1. 查看 Google Custom Search [官方文档](https://developers.google.com/custom-search/v1/overview)
2. 在 Google Cloud Console 查看 **配额和使用情况**
3. 联系技术支持

---

**完成时间：约 15-20 分钟**

**成本：完全免费** 💰