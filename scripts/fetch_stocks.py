#!/usr/bin/env python3
"""股价抓取脚本 - 通过 GitHub Actions 每2小时运行"""
import json, os, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

CST = timezone(timedelta(hours=8))
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

STOCKS = [
    {"symbol": "AAPL",    "name": "苹果",     "region": "us"},
    {"symbol": "MSFT",    "name": "微软",     "region": "us"},
    {"symbol": "GOOGL",   "name": "谷歌",     "region": "us"},
    {"symbol": "AMZN",    "name": "亚马逊",   "region": "us"},
    {"symbol": "META",    "name": "Meta",     "region": "us"},
    {"symbol": "NVDA",    "name": "英伟达",   "region": "us"},
    {"symbol": "TSLA",    "name": "特斯拉",   "region": "us"},
    {"symbol": "NFLX",    "name": "Netflix",  "region": "us"},
    {"symbol": "9988.HK", "name": "阿里巴巴", "region": "cn"},
    {"symbol": "0700.HK", "name": "腾讯",     "region": "cn"},
    {"symbol": "9618.HK", "name": "京东",     "region": "cn"},
    {"symbol": "BIDU",    "name": "百度",     "region": "cn"},
    {"symbol": "PDD",     "name": "拼多多",   "region": "cn"},
    {"symbol": "BABA",    "name": "阿里(美)", "region": "cn"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finance.yahoo.com/",
}

def fetch_quote(stock):
    symbol = stock["symbol"]
    last_err = None
    for host in ["query1", "query2"]:
        url = (
            f"https://{host}.finance.yahoo.com/v8/finance/chart/"
            + urllib.parse.quote(symbol)
            + "?interval=1d&range=2d"
        )
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as r:
                d = json.loads(r.read().decode())
            meta  = d["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice", 0)
            prev  = meta.get("chartPreviousClose") or meta.get("previousClose") or price
            chg   = price - prev
            pct   = (chg / prev * 100) if prev else 0
            return {
                "symbol":     symbol,
                "name":       stock["name"],
                "region":     stock["region"],
                "price":      round(price, 2),
                "change":     round(chg, 2),
                "change_pct": round(pct, 2),
                "currency":   meta.get("currency", "USD"),
                "updated":    datetime.now(CST).strftime("%H:%M"),
            }
        except Exception as e:
            last_err = e
    print(f"[WARN] {symbol}: {last_err}")
    return {
        "symbol": symbol, "name": stock["name"], "region": stock["region"],
        "price": 0, "change": 0, "change_pct": 0,
        "currency": "USD", "updated": "--", "error": True,
    }

def main():
    print(f"[INFO] 抓取股价 @ {datetime.now(CST).strftime('%Y-%m-%d %H:%M CST')}")
    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(fetch_quote, s): s for s in STOCKS}
        for f in as_completed(futures):
            r = f.result()
            ok = "✓" if not r.get("error") else "✗"
            print(f"  [{ok}] {r['symbol']:12s} {r['price']}")
            results.append(r)

    order = {s["symbol"]: i for i, s in enumerate(STOCKS)}
    results.sort(key=lambda x: order.get(x["symbol"], 99))

    output = {
        "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST"),
        "stocks": results,
    }
    out_path = os.path.join(OUTPUT_DIR, "stocks.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 已保存 {len(results)} 支 → {out_path}")

if __name__ == "__main__":
    main()
