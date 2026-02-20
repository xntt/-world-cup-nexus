import json
import os
import time
import feedparser
import google.generativeai as genai
import random
from datetime import datetime

# --- 配置 ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY: genai.configure(api_key=GEMINI_KEY)

SITES_FILE = 'sites.json'

# --- 1. 多样化数据源 (覆盖足球、篮球、格斗) ---
RSS_SOURCES = {
    "Global": "https://www.espn.com/espn/rss/news", # 综合体育
    "Soccer": "https://www.espn.com/espn/rss/soccer/news",
    "NBA": "https://www.espn.com/espn/rss/nba/news",
    "UFC": "https://www.mmafighting.com/rss/current"
}

# --- 2. 智能热点识别 ---
def get_trending_event(geo="Global"):
    """
    抓取 RSS，分析出今天最值得推的赛事。
    返回：{title, summary, sport_type, image_keyword}
    """
    # 默认抓取综合源
    rss_url = RSS_SOURCES["Global"]
    
    # 针对 GEO 优化数据源 (比如美国多推 NBA)
    if geo == "US": rss_url = RSS_SOURCES["NBA"]
    
    print(f"🔥 Hunting trends from: {rss_url}")
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        return None

    # 取第一条头条新闻作为“今日热点”
    top_story = feed.entries[0]
    
    # 简单判断运动类型 (用于配图)
    sport_type = "stadium" # 默认
    title_lower = top_story.title.lower()
    if "nba" in title_lower or "lakers" in title_lower: sport_type = "basketball"
    elif "ufc" in title_lower or "fight" in title_lower: sport_type = "boxing_ring"
    elif "soccer" in title_lower or "league" in title_lower: sport_type = "soccer"

    return {
        "title": top_story.title,
        "summary": top_story.summary[:200],
        "link": top_story.link,
        "sport_type": sport_type,
        "raw_title": top_story.title # 用于给 AI 改写
    }

# --- 3. AI 伪装大师 (根据热点改写网站) ---
def ai_generate_daily_content(domain, event_data, theme):
    """
    让 AI 根据今天的热点，重写网站的 H1、SEO 和 预测。
    """
    if not GEMINI_KEY: return None

    prompt = f"""
    You are a betting expert managing the site: {domain}.
    
    TODAY'S HOT EVENT: "{event_data['raw_title']}"
    
    TASK:
    1. Write a catchy H1 Title for the homepage (e.g., "Bet on [Team A] vs [Team B]").
    2. Write a Subtitle with a Call-to-Action.
    3. Write a 3-sentence "Betting Prediction" or "Analysis" for this event.
    4. Generate 3 related News Headlines.
    
    OUTPUT JSON:
    {{
        "hero_title": "...",
        "hero_subtitle": "...",
        "prediction_text": "...",
        "news": [
            {{"title": "...", "date": "Today", "excerpt": "..."}}
        ]
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        resp = model.generate_content(prompt)
        text = resp.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# --- 4. 模拟赛事 (配合热点) ---
def generate_dynamic_matches(sport_type):
    """根据运动类型生成看起来像真的比赛列表"""
    today = datetime.now().strftime("%b %d")
    
    if sport_type == "basketball":
        return [
            {"team_a": "Lakers", "team_b": "Warriors", "date": today, "odds": "1.90 / 1.90"},
            {"team_a": "Celtics", "team_b": "Heat", "date": today, "odds": "1.50 / 2.60"}
        ]
    elif sport_type == "boxing_ring":
        return [
            {"team_a": "McGregor", "team_b": "Chandler", "date": "Sat Night", "odds": "2.10 / 1.70"},
            {"team_a": "Jones", "team_b": "Miocic", "date": "Co-Main", "odds": "1.40 / 2.80"}
        ]
    else: # Soccer default
        return [
            {"team_a": "Real Madrid", "team_b": "Barcelona", "date": today, "odds": "2.30 / 3.10"},
            {"team_a": "Man City", "team_b": "Arsenal", "date": today, "odds": "1.95 / 3.40"}
        ]

# --- 主程序 ---
def main():
    with open(SITES_FILE, 'r') as f:
        sites = json.load(f)

    for site in sites:
        domain = site.get('hostname')
        
        # 1. 探测 GEO
        geo = "Global"
        if 'usa' in domain: geo = 'US'
        
        # 2. 抓取今日热点
        trend = get_trending_event(geo)
        
        if trend:
            print(f"🔥 {domain} is creating content for: {trend['title']}")
            
            # 3. AI 生成针对性内容
            ai_content = ai_generate_daily_content(domain, trend, site.get('theme', 'modern'))
            
            if ai_content:
                # A. 更新 Hero (让网站看起来像专门为此赛事建立的)
                site['hero'] = {
                    "title": ai_content['hero_title'],
                    "subtitle": ai_content['hero_subtitle'],
                    "cta_text": "Bet Now & Win",
                    # 动态配图：根据运动类型换背景
                    "background_image": f"https://source.unsplash.com/1600x900/?{trend['sport_type']},stadium"
                }
                
                # B. 更新 SEO 长文 (放入预测分析)
                site['seo_content'] = {
                    "body": f"<h3>Expert Prediction</h3><p>{ai_content['prediction_text']}</p><h3>Why Bet Here?</h3><p>Best odds for {trend['raw_title']}.</p>"
                }
                
                # C. 更新新闻
                site['news'] = ai_content['news']
                
                # D. 更新比赛列表
                site['matches'] = generate_dynamic_matches(trend['sport_type'])
                
        # 4. 确保板块完整
        site['layout_order'] = ["hero", "matches", "offers", "seo", "news", "partners"]
        
        time.sleep(3)

    with open(SITES_FILE, 'w') as f:
        json.dump(sites, f, indent=2)
    print("✅ Daily Trends Updated!")

if __name__ == "__main__":
    main()
