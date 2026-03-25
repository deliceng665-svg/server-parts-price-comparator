/* ═══════════════════════════════════════════════════
   服务器配件价格对比查询器 v3 – app.js
   功能：批量查询 · 可视化图表 · 趋势 · 历史 · Excel 导出
         商品详情弹窗（不直接跳转，先展示详情）
         分类筛选 · Cookie 本地存储
   ═══════════════════════════════════════════════════ */

// ── 全局状态 ──────────────────────────────────────────
let batchData      = [];   // [{keyword, results, stats, trend}]
let activeKwIdx    = 0;
let activePlatform = 'all';
let activeSort     = 'price-asc';
let currentItem    = null; // 当前弹窗商品

const HISTORY_KEY = 'server_parts_history_v3';
const HISTORY_MAX = 10;
const COOKIE_KEY  = 'server_parts_cookies_v1';

// Chart.js 实例（每次重绘前销毁）
const charts = {};

// ── 平台配置 ──────────────────────────────────────────
const PLATFORM = {
  taobao: { label: '淘宝', icon: '🛒', badgeClass: 'pb-taobao', cardClass: 'pt-taobao', iconClass: 'mpi-taobao' },
  xianyu: { label: '闲鱼', icon: '🐟', badgeClass: 'pb-xianyu', cardClass: 'pt-xianyu', iconClass: 'mpi-xianyu' },
  jd:     { label: '京东', icon: '🏪', badgeClass: 'pb-jd',     cardClass: 'pt-jd',     iconClass: 'mpi-jd'     },
  other:  { label: '其他', icon: '🔗', badgeClass: 'pb-other',  cardClass: '',           iconClass: ''           },
};

const CHART_COLORS = {
  taobao: { bg: 'rgba(255,106,0,.75)',   border: '#ff6a00' },
  xianyu: { bg: 'rgba(0,181,120,.75)',   border: '#00b578' },
  jd:     { bg: 'rgba(227,24,55,.75)',   border: '#e31837' },
  other:  { bg: 'rgba(136,144,176,.6)',  border: '#8890b0' },
};

// ── 搜索主流程 ─────────────────────────────────────────
async function doSearch(prefill) {
  let input = prefill || document.getElementById('searchInput').value.trim();
  if (!input) return;

  // 获取分类并附加到关键词
  const category = document.getElementById('categorySelect').value;
  if (category) {
    // 为每个关键词附加分类
    const kws = input.split(/[,，\n]+/).map(k => k.trim()).filter(Boolean);
    input = kws.map(k => `${k} ${category}`).join(', ');
  }

  if (prefill) document.getElementById('searchInput').value = prefill;

  setLoading(true, '正在从各平台获取数据…');

  try {
    // GitHub Pages 静态演示版本 - 使用模拟数据
    // 实际使用时请部署后端 API
    const data = generateDemoData(input);

    batchData      = data.batch || [];
    activeKwIdx    = 0;
    activePlatform = 'all';
    activeSort     = 'price-asc';

    saveHistory(input);
    renderAll();
  } catch (e) {
    alert('查询失败：' + e.message);
  } finally {
    setLoading(false);
  }
}

// ── 演示数据生成（GitHub Pages 静态版本）─────────────────
function generateDemoData(keywords) {
  const kws = keywords.split(/[,，\n]+/).map(k => k.trim()).filter(Boolean);
  const platforms = ['taobao', 'xianyu', 'jd'];
  const conditions = ['全新', '99新', '95新', '9成新', '8成新', '拆机件', '二手'];
  const sellers = ['深圳华强北', '北京中关村', '上海徐汇', '广州天河', '成都高新', '杭州西湖', '南京玄武', '武汉洪山'];

  const batch = kws.map((kw, idx) => {
    const count = Math.floor(Math.random() * 15) + 8;
    const basePrice = Math.floor(Math.random() * 2000) + 200;
    const results = [];

    for (let i = 0; i < count; i++) {
      const platform = platforms[Math.floor(Math.random() * platforms.length)];
      const priceVar = (Math.random() - 0.5) * basePrice * 0.6;
      const price = Math.max(50, Math.floor(basePrice + priceVar));

      const kw_enc = encodeURIComponent(kw);
      const search_url_map = {
        'taobao':  `https://s.taobao.com/search?q=${kw_enc}`,
        'xianyu':  `https://www.goofish.com/search?q=${kw_enc}`,
        'jd':      `https://search.jd.com/Search?keyword=${kw_enc}`,
      };

      results.push({
        platform,
        title: `${kw} ${conditions[Math.floor(Math.random() * conditions.length)]} ${platform === 'taobao' ? '淘宝特惠' : platform === 'xianyu' ? '闲鱼好货' : '京东自营'}`,
        price,
        url: search_url_map[platform],
        condition: conditions[Math.floor(Math.random() * conditions.length)],
        seller: sellers[Math.floor(Math.random() * sellers.length)],
        rating: (4 + Math.random()).toFixed(1),
        sales: Math.floor(Math.random() * 200) + 10,
        shipping: Math.random() > 0.5 ? '包邮' : `¥${Math.floor(Math.random() * 20) + 5}`,
      });
    }

    results.sort((a, b) => a.price - b.price);
    const prices = results.map(r => r.price);

    // 趋势数据
    const trend = [];
    const trendBase = prices[0] || basePrice;
    for (let d = 6; d >= 0; d--) {
      const date = new Date();
      date.setDate(date.getDate() - d);
      trend.push({
        date: `${date.getMonth() + 1}/${date.getDate()}`,
        price: Math.max(50, trendBase + Math.floor((Math.random() - 0.5) * trendBase * 0.2)),
      });
    }

    return {
      keyword: kw,
      count,
      results,
      stats: {
        min: Math.min(...prices),
        max: Math.max(...prices),
        avg: Math.floor(prices.reduce((a, b) => a + b, 0) / prices.length),
        median: prices[Math.floor(prices.length / 2)],
        by_platform: {
          taobao: { min: Math.min(...results.filter(r => r.platform === 'taobao').map(r => r.price)) || 0, max: Math.max(...results.filter(r => r.platform === 'taobao').map(r => r.price)) || 0, avg: 0 },
          xianyu: { min: Math.min(...results.filter(r => r.platform === 'xianyu').map(r => r.price)) || 0, max: Math.max(...results.filter(r => r.platform === 'xianyu').map(r => r.price)) || 0, avg: 0 },
          jd:     { min: Math.min(...results.filter(r => r.platform === 'jd').map(r => r.price)) || 0, max: Math.max(...results.filter(r => r.platform === 'jd').map(r => r.price)) || 0, avg: 0 },
        },
      },
      trend,
    };
  });

  return { batch };
}

// ── 渲染总入口 ────────────────────────────────────────
function renderAll() {
  if (!batchData.length) return;

  const sec = document.getElementById('resultsSection');
  sec.style.display = 'block';

  const count = batchData.reduce((s, d) => s + d.count, 0);
  document.getElementById('resultTitle').innerHTML =
    `共 <em>${batchData.length}</em> 个型号 &nbsp;·&nbsp; <em>${count}</em> 条商品`;

  renderKwTabs();
  renderPanel(activeKwIdx);
  renderHistory();

  // 平滑滚动到结果区
  setTimeout(() => {
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
}

// ── 关键词 Tab ────────────────────────────────────────
function renderKwTabs() {
  const container = document.getElementById('keywordTabs');
  container.innerHTML = '';

  if (batchData.length <= 1) {
    container.style.display = 'none';
    return;
  }
  container.style.display = 'flex';

  batchData.forEach((d, i) => {
    const btn = document.createElement('button');
    btn.className = 'kw-tab' + (i === activeKwIdx ? ' active' : '');
    btn.textContent = `${d.keyword}（${d.count}）`;
    btn.onclick = () => switchKw(i);
    container.appendChild(btn);
  });
}

function switchKw(idx) {
  activeKwIdx    = idx;
  activePlatform = 'all';
  document.querySelectorAll('.kw-tab').forEach((t, i) => {
    t.classList.toggle('active', i === idx);
  });
  renderPanel(idx);
}

// ── 面板渲染 ──────────────────────────────────────────
function renderPanel(idx) {
  const panels = document.getElementById('keywordPanels');
  panels.innerHTML = '';

  const d = batchData[idx];
  if (!d) return;

  const panel = document.createElement('div');
  panel.className = 'kw-panel active';
  panel.id = `panel_${idx}`;
  panel.innerHTML = `
    <!-- 统计卡 -->
    <div class="stats-row">
      <div class="stat-card s-min">
        <div class="stat-label">最低价</div>
        <div class="stat-value">¥${d.stats.min}</div>
        <div class="stat-hint">全平台最低</div>
      </div>
      <div class="stat-card s-med">
        <div class="stat-label">中位价</div>
        <div class="stat-value">¥${d.stats.median}</div>
        <div class="stat-hint">50% 分位价格</div>
      </div>
      <div class="stat-card s-avg">
        <div class="stat-label">平均价</div>
        <div class="stat-value">¥${d.stats.avg}</div>
        <div class="stat-hint">所有商品均价</div>
      </div>
      <div class="stat-card s-max">
        <div class="stat-label">最高价</div>
        <div class="stat-value">¥${d.stats.max}</div>
        <div class="stat-hint">全平台最高</div>
      </div>
    </div>

    <!-- 价格趋势 -->
    <div class="trend-card">
      <div class="trend-header">
        <div class="trend-title">📈 近 7 天价格趋势</div>
        <div class="trend-tabs" id="trendTabs_${idx}">
          <button class="trend-tab active" onclick="onTrendTabChange('all',${idx})">全部平台</button>
          <button class="trend-tab" onclick="onTrendTabChange('taobao',${idx})">淘宝</button>
          <button class="trend-tab" onclick="onTrendTabChange('xianyu',${idx})">闲鱼</button>
          <button class="trend-tab" onclick="onTrendTabChange('jd',${idx})">京东</button>
        </div>
      </div>
      <div class="trend-wrap"><canvas id="trendChart_${idx}"></canvas></div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="filter-bar">
      <div class="filter-tabs" id="filterTabs_${idx}">
        ${buildPlatformTabs(d, idx)}
      </div>
      <span class="count-badge" id="countBadge_${idx}">${d.count} 件</span>
      <select class="sort-select" id="sortSelect_${idx}" onchange="onSortChange(${idx})">
        <option value="price-asc">价格从低到高</option>
        <option value="price-desc">价格从高到低</option>
        <option value="platform">按平台</option>
      </select>
    </div>

    <!-- 商品表格 -->
    <div id="resultsTableWrap_${idx}"></div>
    <div class="no-results" id="noResults_${idx}" style="display:none">未找到商品，换个关键词试试 🔍</div>
  `;
  panels.appendChild(panel);

  // 不再绘制柱状图和箱线图
  drawTrendChart(idx, d, 'all');
  renderGrid(idx);
}

// ── 平台 Tabs HTML ────────────────────────────────────
function buildPlatformTabs(d, idx) {
  const platforms = ['all', 'taobao', 'xianyu', 'jd'];
  const counts = {};
  d.results.forEach(r => counts[r.platform] = (counts[r.platform] || 0) + 1);

  return platforms.map(p => {
    const conf   = PLATFORM[p];
    const label  = p === 'all' ? '全部平台' : (conf?.label || p);
    const cnt    = p === 'all' ? d.count : (counts[p] || 0);
    const active = p === activePlatform ? ' active' : '';
    return `<button class="filter-tab${active}" onclick="onPlatformChange('${p}',${idx})">${label}（${cnt}）</button>`;
  }).join('');
}

// ── 平台 / 排序切换 ───────────────────────────────────
function onPlatformChange(platform, idx) {
  activePlatform = platform;
  document.querySelectorAll(`#filterTabs_${idx} .filter-tab`)
    .forEach(b => b.classList.toggle('active', b.textContent.startsWith(
      platform === 'all' ? '全部' : (PLATFORM[platform]?.label || platform)
    )));
  renderTable(idx);
}

function onSortChange(idx) {
  activeSort = document.getElementById(`sortSelect_${idx}`).value;
  renderTable(idx);
}

// ── 表格渲染（改回表格形式，用索引传参避免 XSS/转义问题） ──
// 用 _tableItems 缓存当前渲染的列表，供弹窗按索引取数据
const _tableItems = {};

function renderTable(idx) {
  const d = batchData[idx];
  let list = [...d.results];

  if (activePlatform !== 'all') list = list.filter(r => r.platform === activePlatform);

  if (activeSort === 'price-asc')  list.sort((a, b) => a.price - b.price);
  if (activeSort === 'price-desc') list.sort((a, b) => b.price - a.price);
  if (activeSort === 'platform')   list.sort((a, b) => a.platform.localeCompare(b.platform));

  // 缓存，供 openDetailByIndex 使用
  _tableItems[idx] = list;

  const minPrice = Math.min(...list.map(r => r.price));
  const maxPrice = Math.max(...list.map(r => r.price));
  const wrap     = document.getElementById(`resultsTableWrap_${idx}`);
  const noRes    = document.getElementById(`noResults_${idx}`);
  const badge    = document.getElementById(`countBadge_${idx}`);

  badge.textContent = `${list.length} 件`;

  if (!list.length) {
    wrap.innerHTML = '';
    noRes.style.display = 'block';
    return;
  }
  noRes.style.display = 'none';

  const rows = list.map((item, i) => {
    const conf = PLATFORM[item.platform] || PLATFORM.other;
    let pc = '';
    if (item.price === minPrice) pc = ' price-low';
    if (item.price === maxPrice) pc = ' price-high';
    return `<tr>
      <td class="idx-cell">${i + 1}</td>
      <td class="price-cell${pc}">¥${item.price.toLocaleString()}</td>
      <td><span class="platform-badge ${conf.badgeClass}">${conf.icon} ${conf.label}</span></td>
      <td class="title-cell" title="${escHtml(item.title)}">${escHtml(item.title)}</td>
      <td class="cond-cell">${escHtml(item.condition || '-')}</td>
      <td class="seller-cell">${escHtml(item.seller || '-')}</td>
      <td><button class="link-btn" onclick="openDetailByIndex(${idx},${i})">查看详情 →</button></td>
    </tr>`;
  }).join('');

  wrap.innerHTML = `
    <div class="results-table-wrap">
      <table>
        <thead><tr>
          <th>#</th>
          <th>价格</th>
          <th>平台</th>
          <th>商品标题</th>
          <th>成色</th>
          <th>卖家</th>
          <th>操作</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

// renderGrid 保留别名（面板中引用的是 renderGrid）
function renderGrid(idx) { renderTable(idx); }

// 通过索引打开弹窗（避免内联 JSON 转义问题）
function openDetailByIndex(kwIdx, itemIdx) {
  const item = (_tableItems[kwIdx] || [])[itemIdx];
  if (item) openDetail(item);
}

// ── 商品详情弹窗 ──────────────────────────────────────
function openDetail(item) {
  currentItem = item;
  const conf  = PLATFORM[item.platform] || PLATFORM.other;

  // 平台图标
  document.getElementById('modalPlatformIcon').className = `modal-platform-icon ${conf.iconClass}`;
  document.getElementById('modalPlatformIcon').textContent = conf.icon;
  document.getElementById('modalPlatformName').textContent = conf.label;
  document.getElementById('modalPlatformBadge').innerHTML =
    `<span class="platform-badge ${conf.badgeClass}">${conf.icon} ${conf.label}</span>`;

  // 价格
  document.getElementById('modalPriceNum').textContent = item.price.toLocaleString();

  // 标题
  document.getElementById('modalTitle').textContent = item.title;

  // Meta 网格
  const metaItems = [];

  if (item.condition) {
    metaItems.push({ label: '商品成色', value: item.condition, cls: item.condition.includes('全新') ? 'good' : 'warn' });
  }
  if (item.seller) {
    metaItems.push({ label: '卖家', value: item.seller });
  }
  if (item.rating) {
    metaItems.push({ label: '信誉评分', value: item.rating, cls: parseFloat(item.rating) >= 4.5 ? 'good' : '' });
  }
  if (item.sales) {
    metaItems.push({ label: '销量/交易', value: item.sales });
  }
  if (item.shipping) {
    metaItems.push({ label: '运费', value: item.shipping });
  }

  const metaGrid = document.getElementById('modalMetaGrid');
  if (metaItems.length) {
    metaGrid.style.display = 'grid';
    metaGrid.innerHTML = metaItems.map(m => `
      <div class="modal-meta-item">
        <div class="modal-meta-label">${m.label}</div>
        <div class="modal-meta-value ${m.cls || ''}">${escHtml(m.value)}</div>
      </div>
    `).join('');
  } else {
    metaGrid.style.display = 'none';
    metaGrid.innerHTML = '';
  }

  // 更新跳转按钮文字
  const visitBtn = document.getElementById('modalVisitBtn');
  visitBtn.innerHTML = `<span>去 ${conf.label} 查看</span><span>→</span>`;

  // 显示弹窗
  const modal = document.getElementById('detailModal');
  modal.style.display = 'flex';
  requestAnimationFrame(() => modal.classList.add('show'));

  // 锁定滚动
  document.body.style.overflow = 'hidden';
}

function closeDetailModal() {
  const modal = document.getElementById('detailModal');
  modal.classList.remove('show');
  setTimeout(() => { modal.style.display = 'none'; }, 260);
  document.body.style.overflow = '';
  currentItem = null;
}

function closeModal(event) {
  // 点击遮罩关闭（不点击 modal-box 内部）
  if (event.target === document.getElementById('detailModal')) {
    closeDetailModal();
  }
}

function visitPlatform() {
  if (!currentItem?.url) return;
  window.open(currentItem.url, '_blank', 'noopener,noreferrer');
}

// 键盘 ESC 关闭弹窗
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeDetailModal();
});

// ── 图表：柱状图（各平台价格对比） ───────────────────────
function drawBarChart(idx, d) {
  destroyChart(`barChart_${idx}`);

  const platforms = Object.keys(d.stats.by_platform);
  const ctx = document.getElementById(`barChart_${idx}`).getContext('2d');

  charts[`barChart_${idx}`] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: platforms.map(p => PLATFORM[p]?.label || p),
      datasets: [
        {
          label: '最低价',
          data: platforms.map(p => d.stats.by_platform[p].min),
          backgroundColor: platforms.map(p => CHART_COLORS[p]?.bg || 'rgba(136,144,176,.6)'),
          borderColor:     platforms.map(p => CHART_COLORS[p]?.border || '#8890b0'),
          borderWidth: 1.5,
          borderRadius: 6,
        },
        {
          label: '平均价',
          data: platforms.map(p => d.stats.by_platform[p].avg),
          backgroundColor: platforms.map(p => (CHART_COLORS[p]?.bg || 'rgba(136,144,176,.6)').replace('.75', '.35')),
          borderColor:     platforms.map(p => CHART_COLORS[p]?.border || '#8890b0'),
          borderWidth: 1,
          borderRadius: 6,
        },
        {
          label: '最高价',
          data: platforms.map(p => d.stats.by_platform[p].max),
          backgroundColor: platforms.map(p => (CHART_COLORS[p]?.bg || 'rgba(136,144,176,.6)').replace('.75', '.15')),
          borderColor:     platforms.map(p => CHART_COLORS[p]?.border || '#8890b0'),
          borderWidth: 1,
          borderRadius: 6,
        },
      ],
    },
    options: chartOptions(true),
  });
}

// ── 图表：箱线图（价格区间） ───────────────────────────
function drawBoxChart(idx, d) {
  destroyChart(`boxChart_${idx}`);

  const platforms = Object.keys(d.stats.by_platform);
  const ctx = document.getElementById(`boxChart_${idx}`).getContext('2d');

  charts[`boxChart_${idx}`] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: platforms.map(p => PLATFORM[p]?.label || p),
      datasets: [
        {
          label: '最低价',
          data: platforms.map(p => {
            const arr = d.results.filter(r => r.platform === p).map(r => r.price);
            return arr.length ? Math.min(...arr) : 0;
          }),
          backgroundColor: 'rgba(16,185,129,.7)',
          borderRadius: 4,
        },
        {
          label: '中位价',
          data: platforms.map(p => {
            const arr = d.results.filter(r => r.platform === p).map(r => r.price).sort((a,b)=>a-b);
            return arr.length ? arr[Math.floor(arr.length/2)] : 0;
          }),
          backgroundColor: 'rgba(67,97,238,.7)',
          borderRadius: 4,
        },
        {
          label: '最高价',
          data: platforms.map(p => {
            const arr = d.results.filter(r => r.platform === p).map(r => r.price);
            return arr.length ? Math.max(...arr) : 0;
          }),
          backgroundColor: 'rgba(239,68,68,.7)',
          borderRadius: 4,
        },
      ],
    },
    options: chartOptions(true),
  });
}

// ── 图表：趋势折线 ────────────────────────────────────
let _activeTrendPlatform = 'all'; // 当前选中的趋势平台

function onTrendTabChange(platform, idx) {
  _activeTrendPlatform = platform;
  // 更新 Tab 高亮
  document.querySelectorAll(`#trendTabs_${idx} .trend-tab`).forEach(btn => {
    const txt = btn.textContent;
    const isActive = (platform === 'all' && txt.includes('全部')) ||
                     (platform === 'taobao' && txt.includes('淘宝')) ||
                     (platform === 'xianyu' && txt.includes('闲鱼')) ||
                     (platform === 'jd' && txt.includes('京东'));
    btn.classList.toggle('active', isActive);
  });
  // 重绘趋势图
  drawTrendChart(idx, batchData[idx], platform);
}

function drawTrendChart(idx, d, platform = 'all') {
  destroyChart(`trendChart_${idx}`);
  if (!d.trend || !d.trend.length) return;

  // 按平台过滤趋势数据（如果有 by_platform 字段）
  let trendData = d.trend;
  if (platform !== 'all' && d.trend_by_platform && d.trend_by_platform[platform]) {
    trendData = d.trend_by_platform[platform];
  }

  const ctx = document.getElementById(`trendChart_${idx}`).getContext('2d');
  const color = platform === 'all' ? 'rgba(67,97,238,.9)' :
                (CHART_COLORS[platform]?.border || 'rgba(67,97,238,.9)');
  const bgColor = platform === 'all' ? 'rgba(67,97,238,.06)' :
                  (CHART_COLORS[platform]?.bg?.replace('.75', '.1') || 'rgba(67,97,238,.06)');

  charts[`trendChart_${idx}`] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: trendData.map(t => t.date),
      datasets: [{
        label: '最低价趋势',
        data:  trendData.map(t => t.price),
        borderColor: color,
        backgroundColor: bgColor,
        borderWidth: 2,
        tension: 0.4,
        fill: true,
        pointRadius: 4,
        pointBackgroundColor: color,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
      }],
    },
    options: chartOptions(false),
  });
}

// ── Chart.js 公共选项 ──────────────────────────────────
function chartOptions(showLegend = true) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: showLegend,
        labels: { color: '#4a5080', font: { size: 11 }, boxWidth: 12, padding: 12 },
      },
      tooltip: {
        backgroundColor: 'rgba(255,255,255,0.97)',
        titleColor: '#1e2047',
        bodyColor: '#4a5080',
        borderColor: '#d0d8f0',
        borderWidth: 1,
        padding: 10,
        callbacks: {
          label: ctx => ` ${ctx.dataset.label}: ¥${ctx.parsed.y?.toLocaleString() ?? ctx.parsed}`,
        },
      },
    },
    scales: {
      x: {
        ticks:  { color: '#8890b0', font: { size: 11 } },
        grid:   { color: 'rgba(200,210,240,0.4)' },
      },
      y: {
        ticks:  { color: '#8890b0', font: { size: 11 },
                  callback: v => `¥${v.toLocaleString()}` },
        grid:   { color: 'rgba(200,210,240,0.4)' },
      },
    },
  };
}

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

// ── 历史记录 ──────────────────────────────────────────
function saveHistory(input) {
  let history = getHistory();
  history = [input, ...history.filter(h => h !== input)].slice(0, HISTORY_MAX);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  renderHistory();
}

function getHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; }
  catch { return []; }
}

function renderHistory() {
  const history = getHistory();
  const bar  = document.getElementById('historyBar');
  const tags = document.getElementById('historyTags');

  if (!history.length) { bar.style.display = 'none'; return; }
  bar.style.display = 'flex';
  // 用 data-keyword 属性传递，避免 JSON.stringify 在 onclick 中破坏语法
  tags.innerHTML = history.map((h, i) =>
    `<button class="history-tag" data-keyword="${escAttr(h)}" onclick="clickHistory(this)">${escHtml(h)}</button>`
  ).join('');
}

function clickHistory(btn) {
  const kw = btn.getAttribute('data-keyword');
  if (kw) doSearch(kw);
}

function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
  renderHistory();
}

// ── 导出 Excel ────────────────────────────────────────
function exportExcel() {
  if (!batchData.length) return;

  const wb = XLSX.utils.book_new();
  const PNAME = { taobao: '淘宝', xianyu: '闲鱼', jd: '京东', other: '其他' };

  batchData.forEach(d => {
    const rows = [['排名', '价格（元）', '平台', '商品标题', '成色', '卖家', '评分', '商品链接']];
    const sorted = [...d.results].sort((a, b) => a.price - b.price);
    sorted.forEach((r, i) => {
      rows.push([
        i + 1, r.price,
        PNAME[r.platform] || r.platform,
        r.title,
        r.condition || '',
        r.seller || '',
        r.rating || '',
        r.url,
      ]);
    });

    rows.push([]);
    rows.push(['统计汇总', '最低价', '平均价', '中位价', '最高价', '商品数量']);
    rows.push(['', d.stats.min, d.stats.avg, d.stats.median, d.stats.max, d.count]);

    rows.push([]);
    rows.push(['平台', '最低价', '平均价', '最高价', '商品数']);
    Object.entries(d.stats.by_platform).forEach(([p, s]) => {
      const cnt = d.results.filter(r => r.platform === p).length;
      rows.push([PNAME[p] || p, s.min, s.avg, s.max, cnt]);
    });

    const ws = XLSX.utils.aoa_to_sheet(rows);
    ws['!cols'] = [{ wch: 6 }, { wch: 12 }, { wch: 8 }, { wch: 50 }, { wch: 10 }, { wch: 20 }, { wch: 10 }, { wch: 60 }];
    const sheetName = d.keyword.replace(/[/\\?*[\]]/g, '_').slice(0, 30);
    XLSX.utils.book_append_sheet(wb, ws, sheetName);
  });

  XLSX.writeFile(wb, `服务器配件价格_${fmtDate()}.xlsx`);
}

function fmtDate() {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,'0')}${String(d.getDate()).padStart(2,'0')}`;
}

// ── 加载状态 ──────────────────────────────────────────
function setLoading(show, text = '') {
  const overlay = document.getElementById('loadingOverlay');
  const btn     = document.getElementById('searchBtn');
  overlay.style.display = show ? 'flex' : 'none';
  btn.disabled = show;
  if (text) document.getElementById('loadingText').textContent = text;
}

// ── 工具函数 ──────────────────────────────────────────
function escHtml(s = '') {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                  .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function escAttr(s = '') {
  return String(s).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// ── 初始化 ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  renderHistory();
  loadCookies();

  document.getElementById('searchInput').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.isComposing) doSearch();
  });
});

// ── Cookie 管理 ────────────────────────────────────────
function toggleCookiePanel() {
  const panel = document.getElementById('cookiePanel');
  const icon  = document.getElementById('cookieToggleIcon');
  if (panel.style.display === 'none') {
    panel.style.display = 'block';
    icon.textContent = '收起';
  } else {
    panel.style.display = 'none';
    icon.textContent = '展开';
  }
}

function getCookies() {
  try {
    const raw = localStorage.getItem(COOKIE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch { return {}; }
}

function loadCookies() {
  const cookies = getCookies();
  document.getElementById('taobaoCookie').value = cookies.taobao || '';
  document.getElementById('xianyuCookie').value = cookies.xianyu || '';
  document.getElementById('jdCookie').value     = cookies.jd || '';
}

function saveCookies() {
  const cookies = {
    taobao:  document.getElementById('taobaoCookie').value.trim(),
    xianyu:  document.getElementById('xianyuCookie').value.trim(),
    jd:      document.getElementById('jdCookie').value.trim(),
  };
  localStorage.setItem(COOKIE_KEY, JSON.stringify(cookies));
  showCookieStatus('✅ Cookie 已保存到本地', 'success');
}

function clearCookies() {
  if (!confirm('确定要清除所有平台 Cookie 吗？')) return;
  localStorage.removeItem(COOKIE_KEY);
  document.getElementById('taobaoCookie').value = '';
  document.getElementById('xianyuCookie').value = '';
  document.getElementById('jdCookie').value     = '';
  showCookieStatus('🗑️ Cookie 已清除', 'cleared');
}

function showCookieStatus(msg, type) {
  const el = document.getElementById('cookieStatus');
  el.textContent = msg;
  el.className = 'cookie-status ' + type;
  el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 3000);
}
