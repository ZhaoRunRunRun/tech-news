#!/usr/bin/env python3
"""科技新闻抓取脚本 - 四栏目版"""
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

# ── 国际新闻 ──────────────────────────────────────────────
def fetch_hn():
    """Hacker News Top Stories"""
    items = []
    raw = fetch("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not raw:
        return items
    ids = json.loads(raw)[:20]
    def get_item(sid):
        d = fetch(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        return json.loads(d) if d else {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        for d in ex.map(get_item, ids):
            if d.get("type") == "story" and d.get("title"):
                items.append({
                    "title": d["title"],
                    "url": d.get("url", f"https://news.ycombinator.com/item?id={d['id']}"),
                    "source": "Hacker News",
                    "score": d.get("score", 0),
                    "time": datetime.fromtimestamp(d.get("time", 0), tz=CST).strftime("%H:%M"),
                    "category": "international",
                    "desc": ""
                })
    return sorted(items, key=lambda x: -x["score"])[:15]

def fetch_github_trending():
    """GitHub Trending"""
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
            "category": "international",
            "desc": desc
        })
    return items

# ── 国内新闻 ──────────────────────────────────────────────
def fetch_v2ex():
    """V2EX 技术热帖"""
    items = []
    raw = fetch("https://www.v2ex.com/api/topics/hot.json")
    if not raw:
        return items
    try:
        tech_nodes = {"tech","python","go","javascript","linux","ai","programmer","cloud"}
        for t in json.loads(raw)[:20]:
            if t.get("node", {}).get("name", "") in tech_nodes:
                items.append({
                    "title": t["title"],
                    "url": t["url"],
                    "source": "V2EX",
                    "score": t.get("replies", 0),
                    "time": TODAY,
                    "category": "domestic",
                    "desc": ""
                })
    except Exception as e:
        print(f"[WARN] V2EX: {e}")
    return items

def fetch_juejin():
    """掘金热门文章"""
    items = []
    try:
        payload = json.dumps({
            "id_type": 2, "sort_type": 200,
            "cate_id": "6809637767543259144",
            "tag_id": "", "cursor": "0", "limit": 10
        }).encode()
        req = urllib.request.Request(
            "https://api.juejin.cn/recommend_api/v1/article/recommend_cate_feed",
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        for art in data.get("data", [])[:10]:
            info = art.get("article_info", {})
            items.append({
                "title": info.get("title", ""),
                "url": f"https://juejin.cn/post/{art.get('article_id','')}",
                "source": "掘金",
                "score": info.get("digg_count", 0),
                "time": TODAY,
                "category": "domestic",
                "desc": info.get("brief_content", "")[:80]
            })
    except Exception as e:
        print(f"[WARN] 掘金: {e}")
    return items

# ── 实时热点 ──────────────────────────────────────────────
def fetch_weibo_hot():
    """微博实时热搜"""
    items = []
    try:
        req = urllib.request.Request(
            "https://weibo.com/ajax/side/hotSearch",
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://weibo.com/",
                "Accept": "application/json, text/plain, */*",
            }
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
        realtime = data.get("data", {}).get("realtime", [])
        for item in realtime[:50]:
            # 跳过广告
            if item.get("is_ad"):
                continue
            word = item.get("word", "")
            note = item.get("note", word)
            if not word:
                continue
            scheme = item.get("word_scheme", "")
            url = f"https://s.weibo.com/weibo?q={urllib.parse.quote(scheme or word)}"
            label = item.get("label_name", "")
            items.append({
                "title": note or word,
                "url": url,
                "source": "微博热搜",
                "score": item.get("num", 0),
                "time": datetime.now(CST).strftime("%H:%M"),
                "category": "trending",
                "desc": f"#{label}# 热度 {item.get('num',0):,}" if label else f"热度 {item.get('num',0):,}",
            })
    except Exception as e:
        print(f"[WARN] 微博热搜: {e}")
        # fallback 百度热搜
        try:
            req2 = urllib.request.Request(
                "https://top.baidu.com/api/board?tab=realtime&_=1",
                headers={"User-Agent": "Mozilla/5.0", "Referer": "https://top.baidu.com/"}
            )
            with urllib.request.urlopen(req2, timeout=12) as r:
                data2 = json.loads(r.read().decode("utf-8", "ignore"))
            content = data2["data"]["cards"][0]["content"]
            for item in content[:20]:
                title = item.get("word", "") or item.get("query", "")
                url   = item.get("appUrl", "") or f"https://www.baidu.com/s?wd={urllib.parse.quote(title)}"
                if not title:
                    continue
                items.append({
                    "title": title, "url": url, "source": "百度热搜",
                    "score": item.get("hotScore", 0),
                    "time": datetime.now(CST).strftime("%H:%M"),
                    "category": "trending", "desc": item.get("desc", "")[:80]
                })
        except Exception as e2:
            print(f"[WARN] 百度热搜 fallback: {e2}")
    return items

def fetch_zhihu_hot():
    """知乎热榜"""
    items = []
    try:
        raw = fetch("https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=15&desktop=true")
        data = json.loads(raw)
        for item in data.get("data", [])[:15]:
            t = item.get("target", )
            items.append({
                "title": t.get("title", ""),
                "url": f"https://www.zhihu.com/question/{t.get('id','')}",
                "source": "知乎热榜",
                "score": item.get("detail_text", "0").replace("万热度", ""),
                "time": datetime.now(CST).strftime("%H:%M"),
                "category": "trending",
                "desc": t.get("excerpt", "")[:80]
            })
    except Exception as e:
        print(f"[WARN] 知乎: {e}")
    return items

import urllib.parse

def main():
    print(f"[INFO] 抓取日期: {TODAY}")
    tasks = {
        "HN": fetch_hn,
        "GitHub": fetch_github_trending,
        "V2EX": fetch_v2ex,
        "掘金": fetch_juejin,
        "微博": fetch_weibo_hot,
        "知乎": fetch_zhihu_hot,
    }
    all_news = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(fn): name for name, fn in tasks.items()}
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

    # 按栏目分组
    categories = {"international": [], "domestic": [], "trending": []}
    for item in unique:
        cat = item.get("category", "international")
        categories.setdefault(cat, []).append(item)

    output = {
        "date": TODAY,
        "generated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST"),
        "total": len(unique),
        "categories": categories,
    }
    out_path = os.path.join(OUTPUT_DIR, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 保存 {len(unique)} 条新闻 → {out_path}")

    # 维护历史索引
    import shutil
    history_index_path = os.path.join(OUTPUT_DIR, "history.json")
    history = []
    if os.path.exists(history_index_path):
        with open(history_index_path, encoding="utf-8") as f:
            history = json.load(f)
    if not any(h["date"] == TODAY for h in history):
        history.insert(0, {"date": TODAY, "total": len(unique), "file": f"news_{TODAY}.json"})
        history = history[:30]
        with open(history_index_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    archive_path = os.path.join(OUTPUT_DIR, f"news_{TODAY}.json")
    shutil.copy(out_path, archive_path)
    print(f"[INFO] 归档 → {archive_path}")

if __name__ == "__main__":
    main()
