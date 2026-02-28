#!/usr/bin/env python3
"""
generate_daily_report.py — 用 Claude API 汇总近几天新闻，生成日报 JSON
输出: docs/data/daily_report.json
"""
import json, os, glob, urllib.request
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
OUT_FILE  = os.path.join(DATA_DIR, "daily_report.json")

CLAUDE_API   = "https://code.newcli.com/claude/aws/v1/messages"
CLAUDE_KEY   = "sk-ant-oat01-mUp6ez3MzQxiwGXe1GFXLgYoQgX75zGGHvG9G6N6dSSYqxCb2AhtIccqVylRvOWRxlyapmoZvtsVZ2mnc9EiR4rToTTLkAA"
CLAUDE_MODEL = "claude-sonnet-4-6"


def load_recent_news(days=5):
    all_items = []
    today_file = os.path.join(DATA_DIR, "news.json")
    if os.path.exists(today_file):
        try:
            d = json.load(open(today_file, encoding="utf-8"))
            cats = d.get("categories", {})
            date = d.get("date", "今天")
            for cat, items in cats.items():
                for item in items:
                    all_items.append({"date": date, "cat": cat,
                        "title": item.get("title",""), "desc": item.get("desc",""),
                        "source": item.get("source","")})
        except Exception as e:
            print("[WARN] news.json:", e)

    hist_dir = os.path.join(DATA_DIR, "history")
    if os.path.exists(hist_dir):
        files = sorted(glob.glob(os.path.join(hist_dir, "*.json")), reverse=True)
        for f in files[:days-1]:
            try:
                d = json.load(open(f, encoding="utf-8"))
                cats = d.get("categories", {})
                date = d.get("date", os.path.basename(f).replace(".json",""))
                for cat, items in cats.items():
                    for item in items:
                        all_items.append({"date": date, "cat": cat,
                            "title": item.get("title",""), "desc": item.get("desc",""),
                            "source": item.get("source","")})
            except Exception as e:
                print("[WARN]", f, e)
    return all_items


def load_ai_news():
    f = os.path.join(DATA_DIR, "ai_news.json")
    if not os.path.exists(f):
        return []
    try:
        d = json.load(open(f, encoding="utf-8"))
        return d.get("items", [])[:30]
    except:
        return []


def build_prompt(news_items, ai_items):
    by_date = {}
    for item in news_items:
        date = item["date"]
        cat  = item["cat"]
        if date not in by_date:
            by_date[date] = {}
        if cat not in by_date[date]:
            by_date[date][cat] = []
        by_date[date][cat].append(item["title"])

    news_text = ""
    for date in sorted(by_date.keys(), reverse=True):
        news_text += "\n【%s】\n" % date
        cats = by_date[date]
        if "trending" in cats:
            news_text += "热点：" + "、".join(cats["trending"][:15]) + "\n"
        if "international" in cats:
            news_text += "国际：" + "、".join(cats["international"][:10]) + "\n"
        if "domestic" in cats:
            news_text += "国内：" + "、".join(cats["domestic"][:10]) + "\n"

    ai_text = ""
    if ai_items:
        ai_text = "\n【AI资讯（近期）】\n"
        for item in ai_items[:20]:
            ai_text += "- %s\n" % item.get("title","")

    today = datetime.now(CST).strftime("%Y年%m月%d日")
    return (
        "你是一位专业的科技与时事分析师。请根据以下近几天的新闻数据，撰写一份综合日报。\n\n"
        "要求：\n"
        "1. 总字数在2000-3000字之间\n"
        "2. 分为以下几个板块：\n"
        "   - 【今日要闻摘要】：用2-3段话概括最重要的事件\n"
        "   - 【国际局势分析】：重点分析中东、大国博弈等重要国际动态，梳理事件脉络\n"
        "   - 【科技与AI动态】：结合AI资讯，分析近期科技领域重要进展\n"
        "   - 【国内热点】：梳理国内重要事件和社会热点\n"
        "   - 【市场与经济】：如有相关内容，分析市场动向\n"
        "   - 【编辑点评】：用一段话点评近期最值得关注的趋势或现象\n"
        "3. 语言专业、客观，有深度，避免流水账\n"
        "4. 对重要事件要有分析和判断，不只是罗列标题\n"
        "5. 今天日期：%s\n\n"
        "新闻数据：\n%s\n%s\n\n"
        "请直接输出日报正文，不需要额外说明。"
    ) % (today, news_text, ai_text)


def call_claude(prompt):
    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")
    req = urllib.request.Request(
        CLAUDE_API, data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_KEY,
            "anthropic-version": "2023-06-01",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read().decode("utf-8"))
    return resp["content"][0]["text"]


def main():
    now = datetime.now(CST)
    print("[INFO] 生成日报 @ %s" % now.strftime("%Y-%m-%d %H:%M CST"))

    news_items = load_recent_news(days=5)
    ai_items   = load_ai_news()
    print("  新闻条目: %d，AI资讯: %d" % (len(news_items), len(ai_items)))

    if not news_items:
        print("[WARN] 无新闻数据，跳过")
        return

    prompt = build_prompt(news_items, ai_items)
    print("  Prompt 长度: %d 字符" % len(prompt))

    try:
        report_text = call_claude(prompt)
        print("  日报生成成功，%d 字" % len(report_text))
    except Exception as e:
        print("[ERROR] 生成失败: %s" % e)
        return

    out = {
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S CST"),
        "date": now.strftime("%Y-%m-%d"),
        "report": report_text,
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("[INFO] 保存完成 → %s" % OUT_FILE)


if __name__ == "__main__":
    main()
