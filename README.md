# 科技日报 Tech News

每日自动抓取科技圈新闻，通过 GitHub Actions 在北京时间每天 08:00 更新。

## 访问地址

🌐 https://143709123.xyz/news

## 数据来源

- **Hacker News** - 全球技术社区热帖
- **GitHub Trending** - 每日热门开源项目
- **V2EX** - 国内开发者社区
- **Product Hunt** - 最新科技产品

## 本地运行

```bash
pip install -r requirements.txt  # 无额外依赖，纯标准库
python scripts/fetch_news.py     # 抓取新闻
python scripts/generate_html.py  # 生成页面
```

## 自动更新

GitHub Actions 每天 UTC 00:00（北京时间 08:00）自动运行，更新 `docs/` 目录并推送。
