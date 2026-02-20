import json
import os
import feedparser
import google.generativeai as genai
import random
import time

# 配置
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY: genai.configure(api_key=GEMINI_KEY)

SITES_FILE = 'sites.json'

def get_real_news(geo="MX"):
    # 模拟真实 RSS 抓取，你可以换成真实 URL
    # 这里为了演示稳定，返回带链接的结构
    return [
        {
            "title": f"Real News for {geo} - Update 1",
            "date": "Just Now",
            "excerpt": "This is a real news item fetched from RSS...",
            "link": "https://www.espn.com/soccer/"
        },
        {
            "title": f"Real News for {geo} - Update 2",
            "date": "1 Hour ago",
            "excerpt": "Another update about the World Cup teams...",
            "link": "https://www.espn.com/soccer/"
        },
        {
            "title": f"Real News for {geo} - Update 3",
            "date": "2 Hours ago",
            "excerpt": "Betting odds are shifting rapidly...",
            "link": "https://www.espn.com/soccer/"
        }
    ]

def main():
    with open(SITES_FILE, 'r') as f:
        sites = json.load(f)

    for site in sites:
        domain = site.get('hostname')
        print(f"Updating {domain}...")

        # 1. 更新新闻 (保留链接)
        site['news'] = get_real_news()

        # 2. 确保结构完整 (防止缺少板块)
        if 'faq' not in site:
            site['faq'] = [{"q": "Sample Q?", "a": "Sample A"}]
        
        if 'matches' not in site:
            site['matches'] = [{"team_a": "Team A", "team_b": "Team B", "date": "Soon", "odds": "2.0"}]

        # 3. 确保布局顺序包含所有板块
        site['layout_order'] = ["hero", "matches", "offers", "news", "faq", "partners", "seo"]

    with open(SITES_FILE, 'w') as f:
        json.dump(sites, f, indent=2)
    print("All sites updated.")

if __name__ == "__main__":
    main()
