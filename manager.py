import json
import os
import time
import feedparser
import google.generativeai as genai
import random
from datetime import datetime

# --- 配置 ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

SITES_FILE = 'sites.json'

# --- 1. GEO 配置 (针对不同国家的 RSS 源和提示词) ---
GEO_CONFIG = {
    "MX": {
        "rss": "https://www.espn.com.mx/espn/rss/soccer/news",
        "lang": "Spanish",
        "currency": "MXN",
        "payment": "OXXO, SPEI, Todito Cash",
        "team": "Mexico National Team"
    },
    "BR": {
        "rss": "https://www.espn.com.br/espn/rss/soccer/news",
        "lang": "Portuguese",
        "currency": "BRL",
        "payment": "Pix, Boleto, PicPay",
        "team": "Brazil National Team"
    },
    "US": {
        "rss": "https://www.espn.com/espn/rss/soccer/news",
        "lang": "English",
        "currency": "USD",
        "payment": "Crypto, Credit Card, Zelle",
        "team": "USMNT"
    },
    "Global": { # 默认
        "rss": "https://www.espn.com/espn/rss/soccer/news",
        "lang": "English",
        "currency": "USD",
        "payment": "Crypto, Visa",
        "team": "World Cup Teams"
    }
}

# --- 2. 功能函数 ---

def fetch_real_news(geo_code):
    """抓取真实 RSS 新闻"""
    config = GEO_CONFIG.get(geo_code, GEO_CONFIG["Global"])
    print(f"📡 Fetching RSS from {config['rss']}...")
    
    feed = feedparser.parse(config['rss'])
    news_items = []
    
    # 取前 3 条
    for entry in feed.entries[:3]:
        news_items.append({
            "title": entry.title,
            "date": datetime.now().strftime("%b %d, %Y"),
            "excerpt": entry.summary[:150] + "...", # 截取摘要
            "link": entry.link # 👈 关键：抓取真实链接
        })
    return news_items

def generate_geo_content(domain, geo_code, theme):
    """利用 Gemini 生成深度 GEO 内容 (FAQ + Guide)"""
    if not GEMINI_KEY:
        return None, None

    config = GEO_CONFIG.get(geo_code, GEO_CONFIG["Global"])
    
    prompt = f"""
    You are a localized SEO expert for a betting site: {domain}.
    Target: {config['lang']} speakers in {geo_code}.
    
    TASK 1: Generate 3 FAQ items about betting on World Cup 2026 in {geo_code}.
    - Include keywords: {config['payment']}, {config['currency']}, Legal.
    - Format: JSON Array [{{ "q": "Question?", "a": "Answer" }}]
    
    TASK 2: Write a detailed HTML Guide (300 words).
    - Title: "How to Bet on {config['team']} from {geo_code}"
    - Content: Explain how to deposit using {config['payment']}, claim bonuses in {config['currency']}.
    - Format: HTML string with <h3>, <p>, <ul>.
    
    OUTPUT JSON format:
    {{
        "faq_data": [...],
        "seo_html": "<h3>...</h3>..."
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        resp = model.generate_content(prompt)
        text = resp.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return None

# --- 3. 主程序 ---

def main():
    with open(SITES_FILE, 'r') as f:
        sites = json.load(f)

    for site in sites:
        domain = site.get('hostname')
        
        # 简单的 GEO 探测 (根据域名判断)
        if 'mx' in domain: geo = 'MX'
        elif 'br' in domain: geo = 'BR'
        elif 'usa' in domain: geo = 'US'
        else: geo = 'Global'
        
        print(f"👉 Processing {domain} [GEO: {geo}]...")

        # A. 更新新闻 (真实链接)
        real_news = fetch_real_news(geo)
        if real_news:
            site['news_data'] = real_news

        # B. 更新深度内容 (FAQ + Guide)
        ai_data = generate_geo_content(domain, geo, site.get('theme'))
        if ai_data:
            site['faq'] = ai_data.get('faq_data', [])
            
            if 'seo_content' not in site: site['seo_content'] = {}
            site['seo_content']['body'] = ai_data.get('seo_html', "")
            site['seo_content']['title'] = f"Complete Betting Guide for {geo}"

        # C. 确保布局包含新板块
        # 强制把 faq 加入布局
        if 'faq' not in site['layout_order']:
            site['layout_order'].append('faq')

        time.sleep(3) # 防止 API 超限

    with open(SITES_FILE, 'w') as f:
        json.dump(sites, f, indent=2)
    print("✅ All Content Updated!")

if __name__ == "__main__":
    main()
