import json
import os
import time
import feedparser
import google.generativeai as genai
from datetime import datetime

# --- 配置区 ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

SITES_FILE = 'sites.json'

# 定义针对不同地区的 RSS 源 (这里只是示例，你可以找更多)
RSS_SOURCES = {
    "Global": "https://www.espn.com/espn/rss/soccer/news",
    "MX": "https://www.espn.com.mx/espn/rss/soccer/news", # 墨西哥源
    "US": "https://www.espn.com/espn/rss/soccer/news",
    "BR": "https://www.espn.com.br/espn/rss/soccer/news"
}

# --- 核心功能 1: 抓取真实新闻 ---
def fetch_real_news(geo_code):
    """抓取 RSS 并返回前 3 条真实新闻数据"""
    rss_url = RSS_SOURCES.get(geo_code, RSS_SOURCES["Global"])
    print(f"📡 Fetching RSS for {geo_code}: {rss_url}")
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    # 只取前 3 条
    for entry in feed.entries[:3]:
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary if 'summary' in entry else entry.title
        })
    return news_items

# --- 核心功能 2: Gemini 深度本地化改写 ---
def ai_rewrite_content(domain, geo, theme, raw_news):
    """
    让 AI 做两件事：
    1. 改写新闻：把普通体育新闻变成 '博彩诱导' 新闻。
    2. 生成长文 SEO：写一篇针对该域名的 500字 HTML 攻略。
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # A. 准备新闻素材
    news_context = "\n".join([f"- {n['title']}: {n['summary']}" for n in raw_news])
    
    # B. 构建超级 Prompt
    prompt = f"""
    You are a professional SEO content writer for a betting site: {domain}.
    Target Audience: {geo} (Country Code). Theme: {theme}.
    
    TASK 1: Rewrite these 3 real news summaries into engaging betting news.
    - Translate to the local language of {geo} (e.g., Spanish for MX, Portuguese for BR).
    - Add a "Betting Angle" (e.g., mention odds, predictions).
    - Source News:
    {news_context}
    
    TASK 2: Write a Long-form SEO Guide (HTML format) for the bottom of the homepage.
    - Title: "Why Bet on World Cup 2026 in {geo}?"
    - Length: ~300 words.
    - Content: Local payment methods, legal status in {geo}, and popular local teams.
    - Format: Use <h3>, <p>, <ul> tags.
    
    OUTPUT FORMAT (Strict JSON):
    {{
      "news_data": [
        {{"title": "...", "date": "Today", "excerpt": "...", "link": "original_link"}}
      ],
      "seo_html": "<h3>...</h3><p>...</p>..."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return None

# --- 主程序 ---
def main():
    with open(SITES_FILE, 'r') as f:
        sites = json.load(f)

    for site in sites:
        domain = site.get('hostname')
        
        # 1. 简单的 GEO 判定 (实际可以写在 CSV 里)
        if 'mx' in domain or 'mexico' in domain: geo = 'MX'
        elif 'br' in domain: geo = 'BR'
        else: geo = 'US'
        
        print(f"👉 Processing {domain} [GEO: {geo}]...")

        # 2. 抓取真实数据
        raw_news = fetch_real_news(geo)
        
        # 3. AI 加工
        if raw_news:
            ai_result = ai_rewrite_content(domain, geo, site.get('theme'), raw_news)
            
            if ai_result:
                # 填入新闻
                site['news_data'] = ai_result.get('news_data', [])
                
                # 填入 SEO 长文
                if 'seo_content' not in site: site['seo_content'] = {}
                site['seo_content']['body'] = ai_result.get('seo_html', "Default SEO Text")
                site['seo_content']['title'] = f"Official Betting Guide: {domain}"

        # 4. 休息 (避免 API 限制)
        time.sleep(3)

    # 保存
    with open(SITES_FILE, 'w') as f:
        json.dump(sites, f, indent=2)
    print("✅ Real News & Long SEO Content Updated!")

if __name__ == "__main__":
    main()
