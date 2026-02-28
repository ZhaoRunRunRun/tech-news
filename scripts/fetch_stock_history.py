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
    # 美股科技
    {"symbol": "AAPL",   "name": "苹果",      "currency": "USD"},
    {"symbol": "MSFT",   "name": "微软",      "currency": "USD"},
    {"symbol": "GOOGL",  "name": "谷歌",      "currency": "USD"},
    {"symbol": "AMZN",   "name": "亚马逊",    "currency": "USD"},
    {"symbol": "META",   "name": "Meta",      "currency": "USD"},
    {"symbol": "NVDA",   "name": "英伟达",    "currency": "USD"},
    {"symbol": "TSLA",   "name": "特斯拉",    "currency": "USD"},
    {"symbol": "NFLX",   "name": "Netflix",   "currency": "USD"},
    # 中概/港股
    {"symbol": "BABA",   "name": "阿里巴巴",  "currency": "USD"},
    {"symbol": "0700.HK","name": "腾讯",      "currency": "HKD"},
    {"symbol": "JD",     "name": "京东",      "currency": "USD"},
    {"symbol": "BIDU",   "name": "百度",      "currency": "USD"},
    {"symbol": "PDD",    "name": "拼多多",    "currency": "USD"},
    {"symbol": "BILI",   "name": "哔哩哔哩",  "currency": "USD"},
    # 贵金属（期货）
    {"symbol": "GC=F",   "name": "黄金",      "currency": "USD"},
    {"symbol": "SI=F",   "name": "白银",      "currency": "USD"},
    # 有色金属龙头
    {"symbol": "FCX",    "name": "自由港铜业","currency": "USD"},
    {"symbol": "AA",     "name": "美国铝业",  "currency": "USD"},
    {"symbol": "NEM",    "name": "纽蒙特",    "currency": "USD"},
    {"symbol": "VALE",   "name": "淡水河谷",  "currency": "USD"},
    {"symbol": "RIO",    "name": "力拓集团",  "currency": "USD"},
]

def fetch_history(symbol, range_="5y"):
    """从 Yahoo Finance 拉取日线数据（走代理）"""
    for host in ["query1", "query2"]:
        url = (
            f"https://{host}.finance.yahoo.com/v8/finance/chart/"
            + urllib.parse.quote(symbol)
            + f"?interval=1d&range={range_}"
        )
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://finance.yahoo.com/",
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                d = json.loads(r.read().decode())
            result = d["chart"]["result"][0]
            timestamps = result.get("timestamp", [])
            closes = result["indicators"]["quote"][0].get("close", [])
            currency = result["meta"].get("currency", "USD")
            points = []
            for ts, c in zip(timestamps, closes):
                if c is None:
                    continue
                date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
                points.append({"d": date_str, "c": round(c, 2)})
            return points, currency
        except Exception as e:
            print(f"  [{symbol}] {host} 失败: {e}")
    return [], "USD"

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

        range_ = "5y" if need_full else "1mo"
        print(f"  [{sym}] {'全量' if need_full else '增量'} range={range_}", end="", flush=True)

        try:
            points, currency = fetch_history(sym, range_)
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
