#!/usr/bin/env python3
"""
fetch_wechat_ai.py — 通过 RSSHub 抓取 AI 公众号内容
每天 08:00 和 21:00 各运行一次，晚上在早上基础上追加
"""
import json, os, time
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
import xml.etree.ElementTree as ET

CST = timezone(timedelta(hours=8))
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "docs", "data")
OUT_FILE = os.path.join(DATA_DIR, "ai_news.json")

# RSSHub 公共实例（可换自建）
RSSHUB_BASE = "https://rsshub.app"

# 目标公众号：(显示名, 搜狗微信ID)
ACCOUNTS = [
    ("数字生命卡兹克", "shuzishengmingkazike"),
    ("量子位",         "QbitAI"),
    ("机器之心",       "almosthuman2014"),
    ("新智元",         "AI_era"),
    ("AI科技评论",     "aitechtalk"),
    ("硅星人Pro",      "guixingren"),
    ("AIGC开放社区",   "aigc_open"),
    ("人工智能学家",   "almosthuman"),
    ("差评",           "chaping321"),
    ("深度学习NLP",    "deeplearning_nlp"),
]

def fetch_rss(name, wechat_id):
    url = f"{RSSHUB_BASE}/wechat/sogou/{wechat_id}"
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as r:
            raw = r.read()
        root = ET.fromstring(raw)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = []

        # RSS 2.0
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link  = (item.findtext("link") or "").strip()
            desc  = (item.findtext("description") or "").strip()
            pub   = (item.findtext("pubDate") or "").strip()
            if not title or not link:
                continue
            ts = parse_rss_date(pub)
            items.append({
                "source": name,
                "title":  title,
                "desc":   desc[:120] if desc else "",
                "url":    link,
                "date":   ts_to_date(ts),
                "time":   ts_to_time(ts),
                "timestamp": ts,
            })

        # Atom
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
            link_el = entry.find("atom:link", ns)
            link  = link_el.get("href", "") if link_el is not None else ""
            desc  = (entry.findtext("atom:summary", namespaces=ns) or "").strip()
            pub   = (entry.findtext("atom:published", namespaces=ns) or "").strip()
            if not title or not link:
                continue
            ts = parse_iso_date(pub)
            items.append({
                "source": name,
                "title":  title,
                "desc":   desc[:120] if desc else "",
                "url":    link,
                "date":   ts_to_date(ts),
                "time":   ts_to_time(ts),
                "timestamp": ts,
            })

        print(f"  [{name}] {len(items)} 条")
        return items
    except Exception as e:
        print(f"  [{name}] 失败: {e}")
        return []

def parse_rss_date(s):
    """解析 RFC 2822 日期，如 Sat, 28 Feb 2026 10:30:00 +0800"""
    if not s:
        return int(time.time())
    try:
        from email.utils import parsedate_to_datetime
        return int(parsedate_to_datetime(s).timestamp())
    except Exception:
        return int(time.time())

def parse_iso_date(s):
    """解析 ISO 8601 日期"""
    if not s:
        return int(time.time())
    try:
        s = s.replace("Z", "+00:00")
        return int(datetime.fromisoformat(s).timestamp())
    except Exception:
        return int(time.time())

def ts_to_date(ts):
    return datetime.fromtimestamp(ts, tz=CST).strftime("%Y-%m-%d")

def ts_to_time(ts):
    return datetime.fromtimestamp(ts, tz=CST).strftime("%H:%M")

def main():
    print("[INFO] 抓取 AI 公众号...")
    os.makedirs(DATA_DIR, exist_ok=True)

    # 加载已有数据（晚上追加模式）
    existing = []
    if os.path.exists(OUT_FILE):
        try:
            old = json.load(open(OUT_FILE, encoding="utf-8"))
            existing = old.get("items", [])
            print(f"  [已有] {len(existing)} 条")
        except Exception:
            pass

    # 抓取新数据
    new_items = []
    for name, wid in ACCOUNTS:
        items = fetch_rss(name, wid)
        new_items.extend(items)
        time.sleep(1)  # 避免限速

    # 合并去重（按 url 去重）
    existing_urls = {x["url"] for x in existing}
    added = [x for x in new_items if x["url"] not in existing_urls]
    all_items = existing + added

    # 按时间倒序，只保留最近 7 天
    cutoff = int(time.time()) - 7 * 86400
    all_items = [x for x in all_items if x.get("timestamp", 0) >= cutoff]
    all_items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

    now_cst = datetime.now(tz=CST).strftime("%Y-%m-%d %H:%M:%S CST")
    out = {
        "updated_at": now_cst,
        "total": len(all_items),
        "items": all_items,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 保存 {len(all_items)} 条 AI 资讯 → {OUT_FILE}")
    print(f"  [新增] {len(added)} 条")

if __name__ == "__main__":
    main()
