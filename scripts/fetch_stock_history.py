#!/usr/bin/env python3
"""
fetch_stock_history.py — 增量抓取历史股价，存为 docs/data/stock_history.json
数据源：Twelvedata（免费 demo key，每天800次，14支股票够用）
"""
import json, os, time
import urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUT_FILE = os.path.join(OUTPUT_DIR, "stock_history.json")

# Twelvedata demo key（无需注册，每天800次免费）
API_KEY = "e9cb5ea9f935484285feb0ef4597db1d"
MAX_DAYS = 1300  # 约5年

STOCKS = [
    {"symbol": "AAPL",  "name": "苹果",    "currency": "USD"},
    {"symbol": "MSFT",  "name": "微软",    "currency": "USD"},
    {"symbol": "GOOGL", "name": "谷歌",    "currency": "USD"},
    {"symbol": "AMZN",  "name": "亚马逊",  "currency": "USD"},
    {"symbol": "META",  "name": "Meta",    "currency": "USD"},
    {"symbol": "NVDA",  "name": "英伟达",  "currency": "USD"},
    {"symbol": "TSLA",  "name": "特斯拉",  "currency": "USD"},
    {"symbol": "NFLX",  "name": "Netflix", "currency": "USD"},
    {"symbol": "BABA",  "name": "阿里巴巴","currency": "USD"},
    {"symbol": "JD",    "name": "京东",    "currency": "USD"},
    {"symbol": "BIDU",  "name": "百度",    "currency": "USD"},
    {"symbol": "PDD",   "name": "拼多多",  "currency": "USD"},
]

def fetch_history(symbol, outputsize=1300):
    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol={urllib.parse.quote(symbol)}"
        f"&interval=1day&outputsize={outputsize}&apikey={API_KEY}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read().decode())
    if d.get("status") == "error" or "values" not in d:
        raise Exception(d.get("message", "no values"))
    points = []
    for row in reversed(d["values"]):  # 倒序变正序（旧→新）
        points.append({"d": row["datetime"], "c": round(float(row["close"]), 2)})
    currency = d.get("meta", {}).get("currency", "USD")
    return points, currency

def main():
    print(f"[INFO] 抓取历史股价 @ {datetime.now(CST).strftime('%Y-%m-%d %H:%M CST')}")

    existing = {}
    if os.path.exists(OUT_FILE):
        try:
            old = json.load(open(OUT_FILE, encoding="utf-8"))
            existing = old.get("stocks", {})
            print(f"  [已有] {len(existing)} 支股票历史")
        except Exception:
            pass

    updated = {}
    for stock in STOCKS:
        sym = stock["symbol"]
        old_data = existing.get(sym, {})
        old_points = old_data.get("points", [])

        # 判断是否需要全量
        need_full = True
        if old_points:
            last_date = old_points[-1]["d"]
            last_ts = datetime.strptime(last_date, "%Y-%m-%d").timestamp()
            if (time.time() - last_ts) < 4 * 86400:
                need_full = False

        outputsize = 1300 if need_full else 30
        print(f"  [{sym}] {'全量' if need_full else '增量'} outputsize={outputsize}", end="", flush=True)

        try:
            points, currency = fetch_history(sym, outputsize)
            if not need_full and old_points:
                existing_dates = {p["d"] for p in old_points}
                new_pts = [p for p in points if p["d"] not in existing_dates]
                merged = old_points + new_pts
            else:
                merged = points
            merged.sort(key=lambda x: x["d"])
            merged = merged[-MAX_DAYS:]
            updated[sym] = {
                "name": stock["name"],
                "currency": currency,
                "points": merged,
            }
            print(f" → {len(merged)} 条")
        except Exception as e:
            print(f" → 失败: {e}")
            if sym in existing:
                updated[sym] = existing[sym]

        time.sleep(1)  # 避免限速

    out = {
        "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST"),
        "stocks": updated,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = os.path.getsize(OUT_FILE) / 1024
    print(f"[INFO] 保存完成 → {OUT_FILE} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    main()
