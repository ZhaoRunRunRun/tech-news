#!/usr/bin/env python3
"""
生成静态 HTML 页面
"""
import json, os
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "data", "news.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "index.html")

CATEGORY_ICONS = {
    "综合科技": "🌐",
    "开源项目": "💻",
    "开发者社区": "👨‍💻",
    "新产品": "🚀",
}

def load_news():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

def group_by_category(items):
    groups = {}
    for item in items:
        cat = item.get("category", "其他")
        groups.setdefault(cat, []).append(item)
    return groups

def render_html(data):
    date = data["date"]
    generated_at = data["generated_at"]
    groups = group_by_category(data["items"])

    cards_html = ""
    for cat, items in groups.items():
        icon = CATEGORY_ICONS.get(cat, "📌")
        cards_html += f'<div class="section"><h2>{icon} {cat} <span class="count">{len(items)}</span></h2><div class="cards">'
        for item in items:
            title = item["title"].replace("<", "&lt;").replace(">", "&gt;")
            url = item["url"]
            source = item.get("source", "")
            score = item.get("score", 0)
            time_str = item.get("time", "")
            desc = item.get("desc", "")
            score_html = f'<span class="score">▲ {score}</span>' if score else ""
            desc_html = f'<p class="desc">{desc}</p>' if desc else ""
            cards_html += f"""
<a class="card" href="{url}" target="_blank" rel="noopener">
  <div class="card-header">
    <span class="source-tag">{source}</span>
    {score_html}
  </div>
  <div class="card-title">{title}</div>
  {desc_html}
  <div class="card-time">{time_str}</div>
</a>"""
        cards_html += "</div></div>"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>科技日报 · {date}</title>
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --accent: #6c63ff;
    --accent2: #00d4aa;
    --text: #e2e8f0;
    --muted: #8892a4;
    --card-hover: #22263a;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; min-height: 100vh; }}
  header {{ background: linear-gradient(135deg, #1a1d27 0%, #0f1117 100%); border-bottom: 1px solid var(--border); padding: 2rem 1.5rem 1.5rem; text-align: center; }}
  header h1 {{ font-size: 2rem; font-weight: 800; background: linear-gradient(90deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  header .meta {{ color: var(--muted); font-size: 0.85rem; margin-top: 0.5rem; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }}
  .section {{ margin-bottom: 2.5rem; }}
  .section h2 {{ font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem; color: var(--text); display: flex; align-items: center; gap: 0.5rem; }}
  .count {{ background: var(--accent); color: #fff; font-size: 0.75rem; padding: 0.1rem 0.5rem; border-radius: 999px; font-weight: 600; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }}
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1rem 1.2rem; text-decoration: none; color: inherit; display: flex; flex-direction: column; gap: 0.4rem; transition: background 0.2s, border-color 0.2s, transform 0.15s; }}
  .card:hover {{ background: var(--card-hover); border-color: var(--accent); transform: translateY(-2px); }}
  .card-header {{ display: flex; justify-content: space-between; align-items: center; }}
  .source-tag {{ font-size: 0.72rem; background: rgba(108,99,255,0.15); color: var(--accent); padding: 0.15rem 0.5rem; border-radius: 4px; font-weight: 600; }}
  .score {{ font-size: 0.75rem; color: var(--accent2); font-weight: 600; }}
  .card-title {{ font-size: 0.95rem; font-weight: 600; line-height: 1.5; color: var(--text); }}
  .desc {{ font-size: 0.82rem; color: var(--muted); line-height: 1.5; }}
  .card-time {{ font-size: 0.75rem; color: var(--muted); margin-top: auto; padding-top: 0.3rem; }}
  footer {{ text-align: center; padding: 2rem; color: var(--muted); font-size: 0.8rem; border-top: 1px solid var(--border); }}
  @media (max-width: 600px) {{ .cards {{ grid-template-columns: 1fr; }} header h1 {{ font-size: 1.5rem; }} }}
</style>
</head>
<body>
<header>
  <h1>🛸 科技日报</h1>
  <div class="meta">📅 {date} &nbsp;·&nbsp; 共 {data['total']} 条 &nbsp;·&nbsp; 更新于 {generated_at}</div>
</header>
<div class="container">
{cards_html}
</div>
<footer>数据来源：Hacker News · GitHub Trending · V2EX · Product Hunt &nbsp;|&nbsp; 每日 08:00 自动更新</footer>
</body>
</html>"""

def main():
    data = load_news()
    html = render_html(data)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[INFO] HTML 已生成 → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
