# 服务器配件价格对比查询器

快速查询淘宝、闲鱼、京东的服务器配件价格。

## 功能特性

- 多平台价格对比：同时搜索淘宝、闲鱼、京东
- 价格汇总：显示最低价、最高价、平均价
- 排序筛选：按价格、平台排序
- 平台过滤：支持按平台筛选
- 链接直达：一键跳转商品页面

## 技术栈

- **前端**: HTML5, CSS3, JavaScript (原生)
- **后端**: Python Flask
- **浏览器自动化**: agent-browser

## 快速开始

### 1. 安装依赖

```bash
cd server-parts-price-comparator/backend
pip install -r requirements.txt
```

### 2. 启动服务器

#### 演示模式（无需配置）
```bash
DEMO_MODE=true python app_demo.py
```

#### 真实爬虫模式
```bash
# 确保已安装 agent-browser
npm install -g agent-browser

# 启动服务器
python app.py
```

### 3. 访问

打开浏览器访问: http://localhost:5000

## 使用方法

1. 在搜索框输入服务器配件型号（如：Xeon 6130, Dell R720 主板, 32GB DDR4 ECC）
2. 点击"查询"按钮
3. 查看价格对比结果

## 项目结构

```
server-parts-price-comparator/
├── index.html              # 主页面
├── static/
│   ├── css/
│   │   └── style.css       # 样式文件
│   └── js/
│       └── app.js          # 前端逻辑
└── backend/
    ├── app.py              # 正式版后端
    ├── app_demo.py         # 演示版后端
    └── requirements.txt    # Python 依赖
```

## 注意事项

- 演示模式提供模拟数据，用于快速预览功能
- 真实爬虫模式需要稳定的网络连接
- 部分平台可能有反爬机制，必要时可配合代理使用
- 数据仅供参考，实际价格以各平台为准

## 未来规划

- [ ] 批量查询多个型号
- [ ] 价格趋势图表
- [ ] 历史查询记录
- [ ] Excel 导出功能
- [ ] 更多平台支持
