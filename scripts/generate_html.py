#!/usr/bin/env python3
import json, os
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "docs", "data")
OUTPUT_FILE = os.path.join(BASE_DIR, "docs", "index.html")

def load_json(filename, default):
    p = os.path.join(DATA_DIR, filename)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"','&quot;')

def render_cards(items, limit=None):
    if not items:
        return '<div class="empty">暂无数据</div>'
    if limit:
        items = items[:limit]
    out = ""
    src_colors = {
        "Hacker News": "tag-hn", "GitHub": "tag-gh", "掘金": "tag-jj",
        "36氪": "tag-36", "虎嗅": "tag-hx", "微博": "tag-wb",
        "知乎": "tag-zh", "V2EX": "tag-v2", "澎湃": "tag-pp",
    }
    for item in items:
        title = esc(item.get("title", ""))
        url   = esc(item.get("url", "#"))
        src   = item.get("source", "")
        score = item.get("score", 0)
        time_ = esc(item.get("time", ""))
        desc  = esc(item.get("desc", ""))
        tag_cls = src_colors.get(src, "tag-default")
        s_html = f'<span class="score">&#9650; {score}</span>' if score else ""
        d_html = f'<p class="desc">{desc}</p>' if desc else ""
        out += (
            f'<a class="card" href="{url}" target="_blank" rel="noopener">'
            f'<div class="card-top"><span class="tag {tag_cls}">{esc(src)}</span>{s_html}</div>'
            f'<div class="card-title">{title}</div>{d_html}'
            f'<div class="card-time">{time_}</div></a>'
        )
    return out

def main():
    news    = load_json("news.json", {})
    history = load_json("history.json", [])

    date = news.get("date", "")
    gen  = news.get("generated_at", "")
    cats = news.get("categories", {})

    intl  = cats.get("international", [])
    dom   = cats.get("domestic", [])
    trend = cats.get("trending", [])
    total = len(intl) + len(dom) + len(trend)

    history_json = json.dumps(history, ensure_ascii=False)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(_head(date))
        f.write(_nav())
        f.write(_overview(intl, dom, trend, date, total))
        f.write(_panel_intl(render_cards(intl)))
        f.write(_panel_dom(render_cards(dom)))
        f.write(_panel_trend(render_cards(trend)))
        f.write(_panel_market())
        f.write(_panel_archive())
        f.write(_modal())
        f.write(_footer(gen))
        f.write(_script(history_json, date, total))
    print(f"[INFO] HTML generated -> {OUTPUT_FILE}")


def _head(date):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>日知录 · {date}</title>
<style>
:root{{
  --bg:#0d1117;--sf:#161b22;--sf2:#1c2128;--bd:#30363d;--bd2:#21262d;
  --ac:#58a6ff;--gn:#3fb950;--rd:#f85149;--pu:#bc8cff;--yw:#d29922;
  --tx:#c9d1d9;--mu:#8b949e;--hv:#1f2937;--hv2:#262c36;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--tx);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;min-height:100vh;font-size:14px}}
a{{color:inherit;text-decoration:none}}

/* ── 顶部 Header ── */
.site-header{{background:var(--sf);border-bottom:1px solid var(--bd);padding:0 2rem}}
.header-inner{{max-width:1400px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:56px}}
.site-logo{{display:flex;align-items:center;gap:.6rem}}
.logo-text{{font-size:1.3rem;font-weight:800;background:linear-gradient(90deg,var(--ac),var(--pu));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.logo-sub{{font-size:.72rem;color:var(--mu);border-left:1px solid var(--bd);padding-left:.6rem;margin-left:.2rem}}
.header-meta{{font-size:.78rem;color:var(--mu);display:flex;gap:1.2rem;align-items:center}}
.header-meta span{{display:flex;align-items:center;gap:.3rem}}

/* ── 导航 Tab ── */
.site-nav{{background:var(--sf2);border-bottom:1px solid var(--bd);position:sticky;top:0;z-index:50}}
.nav-inner{{max-width:1400px;margin:0 auto;display:flex;overflow-x:auto;scrollbar-width:none}}
.nav-inner::-webkit-scrollbar{{display:none}}
.nav-tab{{padding:.7rem 1.4rem;font-size:.85rem;font-weight:600;cursor:pointer;border-bottom:2px solid transparent;color:var(--mu);white-space:nowrap;transition:color .2s,border-color .2s;user-select:none}}
.nav-tab:hover{{color:var(--tx)}}
.nav-tab.active{{color:var(--ac);border-bottom-color:var(--ac)}}

/* ── 主布局 ── */
.site-main{{max-width:1400px;margin:0 auto;padding:1.5rem 1.5rem}}
.layout{{display:grid;grid-template-columns:1fr 320px;gap:1.5rem;align-items:start}}
.layout-full{{display:block}}

/* ── 面板 ── */
.panel{{display:none}}.panel.active{{display:block}}

/* ── 区块标题 ── */
.section-title{{font-size:.95rem;font-weight:700;color:var(--tx);padding:.5rem 0 .8rem;border-bottom:2px solid var(--ac);margin-bottom:1rem;display:flex;align-items:center;gap:.4rem}}
.section-more{{margin-left:auto;font-size:.75rem;font-weight:400;color:var(--ac);cursor:pointer}}
.section-more:hover{{text-decoration:underline}}

/* ── 新闻卡片 ── */
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.9rem}}
.card{{background:var(--sf);border:1px solid var(--bd2);border-radius:8px;padding:.9rem 1rem;display:flex;flex-direction:column;gap:.3rem;transition:background .15s,border-color .15s,transform .12s;cursor:pointer}}
.card:hover{{background:var(--hv);border-color:var(--ac);transform:translateY(-2px)}}
.card-top{{display:flex;justify-content:space-between;align-items:center}}
.tag{{font-size:.68rem;font-weight:700;padding:.12rem .4rem;border-radius:3px}}
.tag-hn{{background:rgba(255,102,0,.15);color:#ff6600}}
.tag-gh{{background:rgba(63,185,80,.12);color:var(--gn)}}
.tag-jj{{background:rgba(30,128,255,.12);color:#1e80ff}}
.tag-36{{background:rgba(232,60,60,.12);color:#e83c3c}}
.tag-hx{{background:rgba(255,165,0,.12);color:orange}}
.tag-wb{{background:rgba(255,68,68,.12);color:#ff4444}}
.tag-zh{{background:rgba(0,148,255,.12);color:#0094ff}}
.tag-v2{{background:rgba(188,140,255,.12);color:var(--pu)}}
.tag-pp{{background:rgba(63,185,80,.12);color:var(--gn)}}
.tag-default{{background:rgba(139,148,158,.12);color:var(--mu)}}
.score{{font-size:.7rem;color:var(--gn);font-weight:600}}
.card-title{{font-size:.88rem;font-weight:600;line-height:1.55;color:var(--tx)}}
.desc{{font-size:.78rem;color:var(--mu);line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.card-time{{font-size:.7rem;color:var(--mu);margin-top:auto;padding-top:.2rem}}
.empty{{color:var(--mu);padding:2rem;text-align:center;font-size:.85rem}}

/* ── 侧边栏 ── */
.sidebar{{display:flex;flex-direction:column;gap:1.2rem}}
.sidebar-block{{background:var(--sf);border:1px solid var(--bd2);border-radius:8px;padding:1rem}}
.sidebar-title{{font-size:.82rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.8rem;padding-bottom:.5rem;border-bottom:1px solid var(--bd2)}}
.hot-list{{display:flex;flex-direction:column;gap:.5rem}}
.hot-item{{display:flex;align-items:flex-start;gap:.6rem;cursor:pointer;padding:.3rem .2rem;border-radius:4px;transition:background .15s}}
.hot-item:hover{{background:var(--hv2)}}
.hot-rank{{font-size:.72rem;font-weight:800;min-width:1.2rem;color:var(--mu);padding-top:.1rem}}
.hot-rank.r1{{color:var(--rd)}}.hot-rank.r2{{color:var(--yw)}}.hot-rank.r3{{color:var(--ac)}}
.hot-title{{font-size:.8rem;line-height:1.45;color:var(--tx)}}

/* ── 速览首页 ── */
.overview-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.5rem}}
.ov-block{{background:var(--sf);border:1px solid var(--bd2);border-radius:8px;padding:1rem}}
.ov-block-title{{font-size:.78rem;font-weight:700;color:var(--mu);margin-bottom:.7rem;display:flex;align-items:center;gap:.3rem}}
.ov-list{{display:flex;flex-direction:column;gap:.5rem}}
.ov-item{{font-size:.82rem;line-height:1.45;color:var(--tx);padding:.25rem 0;border-bottom:1px solid var(--bd2);cursor:pointer;transition:color .15s}}
.ov-item:last-child{{border-bottom:none}}
.ov-item:hover{{color:var(--ac)}}
.stat-row{{display:flex;gap:1.5rem;margin-bottom:1.5rem;flex-wrap:wrap}}
.stat-card{{background:var(--sf);border:1px solid var(--bd2);border-radius:8px;padding:.9rem 1.2rem;flex:1;min-width:120px}}
.stat-num{{font-size:1.6rem;font-weight:800;color:var(--ac)}}
.stat-label{{font-size:.75rem;color:var(--mu);margin-top:.2rem}}

/* ── 行情面板 ── */
.market-section{{margin-bottom:1.5rem}}
.market-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.8rem}}
.mcard{{background:var(--sf);border:1px solid var(--bd2);border-radius:8px;padding:.9rem 1rem;display:flex;flex-direction:column;gap:.25rem;transition:border-color .15s}}
.mcard:hover{{border-color:var(--ac)}}
.mcard.up{{border-left:3px solid var(--gn)}}.mcard.down{{border-left:3px solid var(--rd)}}.mcard.flat{{border-left:3px solid var(--mu)}}
.mc-name{{font-size:.88rem;font-weight:700}}
.mc-sym{{font-size:.68rem;color:var(--mu)}}
.mc-price{{font-size:1.1rem;font-weight:800;margin-top:.15rem}}
.mc-chg.up{{color:var(--gn);font-size:.8rem;font-weight:600}}
.mc-chg.down{{color:var(--rd);font-size:.8rem;font-weight:600}}
.mc-chg.flat{{color:var(--mu);font-size:.8rem}}
.mc-na{{color:var(--mu);font-size:.78rem;margin-top:.3rem}}
.skel{{background:linear-gradient(90deg,var(--sf) 25%,var(--hv) 50%,var(--sf) 75%);background-size:200% 100%;animation:shimmer 1.4s infinite;border-radius:8px;height:88px;border:1px solid var(--bd2)}}
@keyframes shimmer{{0%{{background-position:200% 0}}100%{{background-position:-200% 0}}}}
.market-ts{{font-size:.75rem;color:var(--mu);margin-bottom:1rem;display:flex;align-items:center;gap:.8rem}}
.market-ts a{{color:var(--ac)}}

/* ── 归档 ── */
.archive-list{{display:flex;flex-direction:column;gap:.6rem;max-width:600px}}
.arc-item{{display:flex;justify-content:space-between;align-items:center;background:var(--sf);border:1px solid var(--bd2);border-radius:8px;padding:.75rem 1rem;cursor:pointer;transition:background .15s,border-color .15s}}
.arc-item:hover{{background:var(--hv);border-color:var(--ac)}}
.arc-date{{font-weight:600;font-size:.88rem}}
.arc-count{{font-size:.78rem;color:var(--mu)}}

/* ── 模态框 ── */
.ov-modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.8);z-index:100;overflow-y:auto;padding:2rem 1rem}}
.ov-modal.open{{display:block}}
.modal-box{{background:var(--sf);border:1px solid var(--bd);border-radius:12px;max-width:1100px;margin:0 auto;padding:1.5rem}}
.modal-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.2rem}}
.modal-head h2{{font-size:1rem;font-weight:700}}
.modal-close{{background:none;border:none;color:var(--mu);font-size:1.4rem;cursor:pointer;padding:.2rem .5rem;border-radius:4px}}
.modal-close:hover{{color:var(--tx);background:var(--hv)}}

footer{{text-align:center;padding:2rem;color:var(--mu);font-size:.75rem;border-top:1px solid var(--bd);margin-top:2rem}}
@media(max-width:900px){{
  .layout{{grid-template-columns:1fr}}
  .sidebar{{display:none}}
  .overview-grid{{grid-template-columns:1fr}}
}}
@media(max-width:600px){{
  .site-header{{padding:0 1rem}}
  .site-main{{padding:1rem}}
  .market-grid,.cards{{grid-template-columns:1fr 1fr}}
  .stat-row{{gap:.8rem}}
}}
</style>
</head>
<body>"""


def _nav():
    return """
<header class="site-header">
  <div class="header-inner">
    <div class="site-logo">
      <span class="logo-text">&#128218; 日知录</span>
      <span class="logo-sub">每日资讯 · 行情 · 热点</span>
    </div>
    <div class="header-meta">
      <span id="hd-date">&#128197; --</span>
      <span id="hd-total">&#128240; -- 条资讯</span>
    </div>
  </div>
</header>
<nav class="site-nav">
  <div class="nav-inner">
    <div class="nav-tab active" onclick="switchTab('overview',this)">&#9889; 今日速览</div>
    <div class="nav-tab" onclick="switchTab('intl',this)">&#127760; 国际</div>
    <div class="nav-tab" onclick="switchTab('dom',this)">&#127464;&#127475; 国内</div>
    <div class="nav-tab" onclick="switchTab('trend',this)">&#128293; 热点</div>
    <div class="nav-tab" onclick="switchTab('market',this)">&#128200; 行情</div>
    <div class="nav-tab" onclick="switchTab('archive',this)">&#128218; 归档</div>
  </div>
</nav>
<main class="site-main">"""


def _overview(intl, dom, trend, date, total):
    def top3(items):
        html = ""
        for i, item in enumerate(items[:5]):
            title = esc(item.get("title",""))
            url   = esc(item.get("url","#"))
            html += f'<a class="ov-item" href="{url}" target="_blank" rel="noopener">{title}</a>'
        return html or '<div class="empty">暂无数据</div>'

    intl_count  = len(intl)
    dom_count   = len(dom)
    trend_count = len(trend)

    return f"""
<div id="overview" class="panel active">
  <div class="stat-row">
    <div class="stat-card"><div class="stat-num">{total}</div><div class="stat-label">今日资讯总数</div></div>
    <div class="stat-card"><div class="stat-num">{intl_count}</div><div class="stat-label">国际新闻</div></div>
    <div class="stat-card"><div class="stat-num">{dom_count}</div><div class="stat-label">国内资讯</div></div>
    <div class="stat-card"><div class="stat-num">{trend_count}</div><div class="stat-label">实时热点</div></div>
  </div>
  <div class="overview-grid">
    <div class="ov-block">
      <div class="ov-block-title">&#127760; 国际 TOP5 <span class="section-more" onclick="switchTabByName('intl')">查看全部 &rsaquo;</span></div>
      <div class="ov-list">{top3(intl)}</div>
    </div>
    <div class="ov-block">
      <div class="ov-block-title">&#127464;&#127475; 国内 TOP5 <span class="section-more" onclick="switchTabByName('dom')">查看全部 &rsaquo;</span></div>
      <div class="ov-list">{top3(dom)}</div>
    </div>
    <div class="ov-block">
      <div class="ov-block-title">&#128293; 热点 TOP5 <span class="section-more" onclick="switchTabByName('trend')">查看全部 &rsaquo;</span></div>
      <div class="ov-list">{top3(trend)}</div>
    </div>
  </div>
  <div class="section-title">&#128200; 行情速览 <span class="section-more" onclick="switchTabByName('market')">查看全部 &rsaquo;</span></div>
  <div class="market-grid" id="ov-market-grid">
    <div class="skel"></div><div class="skel"></div><div class="skel"></div>
    <div class="skel"></div><div class="skel"></div><div class="skel"></div>
  </div>
</div>"""


def _panel_intl(cards_html):
    return f"""
<div id="intl" class="panel">
  <div class="layout">
    <div>
      <div class="section-title">&#127760; 国际新闻</div>
      <div class="cards">{cards_html}</div>
    </div>
    <div class="sidebar" id="sidebar-intl"></div>
  </div>
</div>"""


def _panel_dom(cards_html):
    return f"""
<div id="dom" class="panel">
  <div class="layout">
    <div>
      <div class="section-title">&#127464;&#127475; 国内资讯</div>
      <div class="cards">{cards_html}</div>
    </div>
    <div class="sidebar" id="sidebar-dom"></div>
  </div>
</div>"""


def _panel_trend(cards_html):
    return f"""
<div id="trend" class="panel">
  <div class="section-title">&#128293; 实时热点</div>
  <div class="cards">{cards_html}</div>
</div>"""


def _panel_market():
    return """
<div id="market" class="panel">
  <div class="market-ts" id="market-ts">
    <span>正在加载行情数据...</span>
    <a href="#" onclick="loadMarket(true);return false">&#8635; 刷新</a>
  </div>
  <div class="market-section">
    <div class="section-title">&#127482;&#127480; 美股科技</div>
    <div class="market-grid" id="mg-us">
      <div class="skel"></div><div class="skel"></div><div class="skel"></div><div class="skel"></div>
    </div>
  </div>
  <div class="market-section">
    <div class="section-title">&#127464;&#127475; 中概 / 港股</div>
    <div class="market-grid" id="mg-cn">
      <div class="skel"></div><div class="skel"></div><div class="skel"></div>
    </div>
  </div>
  <div class="market-section">
    <div class="section-title">&#129351; 贵金属</div>
    <div class="market-grid" id="mg-metal">
      <div class="skel"></div><div class="skel"></div>
    </div>
  </div>
  <p style="color:var(--mu);font-size:.73rem;margin-top:.5rem">数据来源：Yahoo Finance &nbsp;·&nbsp; 延迟约15分钟 &nbsp;·&nbsp; 每5分钟自动刷新</p>
</div>"""


def _panel_archive():
    return """
<div id="archive" class="panel">
  <div class="section-title">&#128218; 历史归档</div>
  <div class="archive-list" id="archive-list"></div>
</div>"""


def _modal():
    return """
</main>
<div class="ov-modal" id="modal">
  <div class="modal-box">
    <div class="modal-head">
      <h2 id="modal-title">历史日报</h2>
      <button class="modal-close" onclick="closeModal()">&#10005;</button>
    </div>
    <div id="modal-body"></div>
  </div>
</div>"""


def _footer(gen):
    return f"""
<footer>
  数据来源：Hacker News &middot; GitHub Trending &middot; 掘金 &middot; 微博 &middot; 知乎 &nbsp;|&nbsp;
  新闻每日 08:00 更新 &nbsp;·&nbsp; 行情实时拉取 &nbsp;|&nbsp;
  更新于 {gen}
</footer>"""


def _script(history_json, date, total):
    return f"""
<script>
// ── 初始化 ──
document.getElementById('hd-date').textContent = '📅 {date}';
document.getElementById('hd-total').textContent = '📰 {total} 条资讯';

const HISTORY = {history_json};

const FINNHUB_KEY = 'd6hdma9r01qnjnco9un0d6hdma9r01qnjnco9ung';
const MARKET = {{
  us: [
    {{s:"AAPL",n:"苹果",cur:"USD"}},{{s:"MSFT",n:"微软",cur:"USD"}},
    {{s:"GOOGL",n:"谷歌",cur:"USD"}},{{s:"AMZN",n:"亚马逊",cur:"USD"}},
    {{s:"META",n:"Meta",cur:"USD"}},{{s:"NVDA",n:"英伟达",cur:"USD"}},
    {{s:"TSLA",n:"特斯拉",cur:"USD"}},{{s:"NFLX",n:"Netflix",cur:"USD"}},
  ],
  cn: [
    {{s:"BABA",n:"阿里巴巴",cur:"USD"}},{{s:"HK:700",n:"腾讯",cur:"HKD"}},
    {{s:"JD",n:"京东",cur:"USD"}},{{s:"BIDU",n:"百度",cur:"USD"}},
    {{s:"PDD",n:"拼多多",cur:"USD"}},{{s:"BILI",n:"哔哩哔哩",cur:"USD"}},
  ],
  metal: [
    {{s:"OANDA:XAU_USD",n:"黄金",unit:"oz",cur:"USD"}},
    {{s:"OANDA:XAG_USD",n:"白银",unit:"oz",cur:"USD"}},
  ],
}};

// ── Tab 切换 ──
function switchTab(id, el) {{
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  el.classList.add('active');
  if (id === 'market')  loadMarket(false);
  if (id === 'archive') renderArchive();
  if (id === 'overview') loadOverviewMarket();
}}
function switchTabByName(id) {{
  const tabs = document.querySelectorAll('.nav-tab');
  const panels = ['overview','intl','dom','trend','market','archive'];
  const idx = panels.indexOf(id);
  if (idx >= 0) switchTab(id, tabs[idx]);
}}

// ── 行情拉取 ──
let marketLoaded = false;
let ovMarketLoaded = false;

async function fetchQuote(symbol) {{
  try {{
    const ctrl = new AbortController();
    const tid  = setTimeout(() => ctrl.abort(), 8000);
    const url  = 'https://finnhub.io/api/v1/quote?symbol=' + encodeURIComponent(symbol) + '&token=' + FINNHUB_KEY;
    const r    = await fetch(url, {{signal: ctrl.signal}});
    clearTimeout(tid);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    if (!d.c || d.c === 0) throw new Error('no data');
    return {{ price: d.c, chg: d.d, pct: d.dp, currency: '' }};
  }} catch(e) {{
    throw e;
  }}
}}

function mCard(name, sym, extra, q, cur) {{
  if (!q || !q.price) return `<div class="mcard flat"><div class="mc-name">${{name}}</div><div class="mc-sym">${{sym}}</div><div class="mc-na">暂无数据</div></div>`;
  const cls   = q.chg > 0 ? 'up' : q.chg < 0 ? 'down' : 'flat';
  const arrow = q.chg >= 0 ? '▲' : '▼';
  const sign  = q.chg >= 0 ? '+' : '';
  const label = cur ? cur + ' ' : '';
  return `<div class="mcard ${{cls}}">
    <div class="mc-name">${{name}}</div>
    <div class="mc-sym">${{sym}}${{extra}}</div>
    <div class="mc-price">${{label}}${{q.price.toFixed(2)}}</div>
    <div class="mc-chg ${{cls}}">${{arrow}} ${{sign}}${{q.chg.toFixed(2)}} (${{sign}}${{q.pct.toFixed(2)}}%)</div>
  </div>`;
}}

async function loadMarket(force) {{
  if (marketLoaded && !force) return;
  const all = [...MARKET.us, ...MARKET.cn, ...MARKET.metal];
  const results = await Promise.allSettled(all.map(x => fetchQuote(x.s)));
  const map = {{}};
  all.forEach((x, i) => {{ map[x.s] = results[i].status === 'fulfilled' ? results[i].value : null; }});
  document.getElementById('mg-us').innerHTML    = MARKET.us.map(x    => mCard(x.n, x.s, '', map[x.s], x.cur)).join('');
  document.getElementById('mg-cn').innerHTML    = MARKET.cn.map(x    => mCard(x.n, x.s, '', map[x.s], x.cur)).join('');
  document.getElementById('mg-metal').innerHTML = MARKET.metal.map(x => mCard('🥇 '+x.n, x.s, ' / '+x.unit, map[x.s], x.cur)).join('');
  const now = new Date().toLocaleTimeString('zh-CN', {{hour:'2-digit',minute:'2-digit'}});
  document.getElementById('market-ts').innerHTML = `<span>行情更新于 ${{now}}（延迟约15分钟）</span><a href="#" onclick="loadMarket(true);return false">↻ 刷新</a>`;
  marketLoaded = true;
  setTimeout(() => {{
    marketLoaded = false;
    if (document.getElementById('market').classList.contains('active')) loadMarket(false);
  }}, 5 * 60 * 1000);
}}

async function loadOverviewMarket() {{
  if (ovMarketLoaded) return;
  const picks = [...MARKET.us.slice(0,3), ...MARKET.cn.slice(0,3)];
  const results = await Promise.allSettled(picks.map(x => fetchQuote(x.s)));
  const map = {{}};
  picks.forEach((x, i) => {{ map[x.s] = results[i].status === 'fulfilled' ? results[i].value : null; }});
  document.getElementById('ov-market-grid').innerHTML = picks.map(x => mCard(x.n, x.s, '', map[x.s], x.cur)).join('');
  ovMarketLoaded = true;
}}

// ── 归档 ──
function renderArchive() {{
  const el = document.getElementById('archive-list');
  if (!HISTORY.length) {{ el.innerHTML = '<div class="empty">暂无历史记录</div>'; return; }}
  el.innerHTML = HISTORY.map(h =>
    `<div class="arc-item" onclick="loadHistory('${{h.file}}','${{h.date}}')">
      <span class="arc-date">📅 ${{h.date}}</span>
      <span class="arc-count">${{h.total}} 条 ›</span>
    </div>`).join('');
}}

function loadHistory(file, date) {{
  fetch('data/' + file)
    .then(r => {{ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }})
    .then(d => showModal(date, d))
    .catch(e => alert('加载失败：' + e));
}}

function showModal(date, data) {{
  document.getElementById('modal-title').textContent = date + ' 历史归档';
  const cats = data.categories || {{}};
  const sections = [
    ['🌍 国际新闻', cats.international || []],
    ['🇨🇳 国内资讯', cats.domestic || []],
    ['🔥 实时热点', cats.trending || []]
  ];
  let html = '';
  for (const [label, items] of sections) {{
    if (!items.length) continue;
    html += `<h3 style="margin:1rem 0 .6rem;font-size:.9rem;color:var(--mu)">${{label}}</h3><div class="cards">`;
    for (const item of items) {{
      const t = (item.title||'').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      const d = (item.desc ||'').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      html += `<a class="card" href="${{item.url}}" target="_blank" rel="noopener">
        <div class="card-top"><span class="tag tag-default">${{item.source||''}}</span></div>
        <div class="card-title">${{t}}</div>
        ${{d?`<p class="desc">${{d}}</p>`:''}}
        <div class="card-time">${{item.time||''}}</div></a>`;
    }}
    html += '</div>';
  }}
  document.getElementById('modal-body').innerHTML = html || '<div class="empty">暂无内容</div>';
  document.getElementById('modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function closeModal() {{
  document.getElementById('modal').classList.remove('open');
  document.body.style.overflow = '';
}}
document.getElementById('modal').addEventListener('click', e => {{ if (e.target === e.currentTarget) closeModal(); }});

// 首页默认加载速览行情
loadOverviewMarket();
</script>
</body>
</html>"""


if __name__ == "__main__":
    main()
