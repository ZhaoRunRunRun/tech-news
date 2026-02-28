#!/usr/bin/env python3
"""科技新闻抓取脚本 - 并发版"""
import json, os, re, urllib.request
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

CST = timezone(timedelta(hours=8))
TODAY = datetime.now(CST).strftime("%Y-%m-%d")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[WARN] {url[:60]} → {e}")
        return ""

def fetch_hn():
    items = []
    raw = fetch("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not raw:
        return items
    ids = json.loads(raw)[:15]
    def get_item(sid):
        d = fetch(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        return json.loads(d) if d else {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(get_item, sid): sid for sid in ids}
        for f in as_completed(futures):
            d = f.result()
            if d.get("type") == "story" and d.get("title"):
                items.append({
                    "title": d["title"],
                    "url": d.get("url", f"https://news.ycombinator.com/item?id={d['id']}"),
                    "source": "Hacker News",
                    "score": d.get("score", 0),
                    "time": datetime.fromtimestamp(d.get("time", 0), tz=CST).strftime("%H:%M"),
                    "category": "综合科技"
                })
    return sorted(items, key=lambda x: -x["score"])

def fetch_github_trending():
    items = []
    html = fetch("https://github.com/trending?since=daily")
    if not html:
        return items
    repos = re.findall(r'<h2[^>]*>\s*<a[^>]*href="(/[^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
    descs = re.findall(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL)
    for i, (path, name) in enumerate(repos[:10]):
        clean = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', name)).strip()
        desc = re.sub(r'<[^>]+>', '', descs[i]).strip()[:100] if i < len(descs) else ""
        items.append({
            "title": clean,
            "url": f"https://github.com{path.strip()}",
            "source": "GitHub Trending",
            "score": 0,
            "time": TODAY,
            "category": "开源项目",
            "desc": desc
        })
    return items

def fetch_v2ex():
    items = []
    raw = fetch("https://www.v2ex.com/api/topics/hot.json")
    if not raw:
        return items
    try:
        topics = json.loads(raw)
        tech_nodes = {"tech","python","go","javascript","linux","ai","programmer","cloud","k8s"}
        for t in topics[:20]:
            if t.get("node", {}).get("name", "") in tech_nodes:
                items.append({
                    "title": t["title"],
                    "url": t["url"],
                    "source": "V2EX",
                    "score": t.get("replies", 0),
                    "time": TODAY,
                    "category": "开发者社区"
                })
    except Exception as e:
        print(f"[WARN] V2EX parse: {e}")
    return items

def main():
    print(f"[INFO] 抓取日期: {TODAY}")
    all_news = []

    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(fetch_hn): "HN",
            ex.submit(fetch_github_trending): "GitHub",
            ex.submit(fetch_v2ex): "V2EX",
        }
        for f in as_completed(futures):
            name = futures[f]
            result = f.result()
            print(f"  [{name}] {len(result)} 条")
            all_news.extend(result)

    # 去重
    seen, unique = set(), []
    for item in all_news:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    output = {
        "date": TODAY,
        "generated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST"),
        "total": len(unique),
        "items": unique
    }
    out_path = os.path.join(OUTPUT_DIR, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 保存 {len(unique)} 条 → {out_path}")

if __name__ == "__main__":
    main()
