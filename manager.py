import json
import os
import random
import time
import google.generativeai as genai
from datetime import datetime, timedelta

# --- config ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

SITES_FILE = 'sites.json'
OFFERS_FILE = 'offers.json'

# --- AI 生成函数 ---
def generate_ai_content(domain, theme, geo, focus_sport): 
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if not focus_sport or focus_sport == "General":
            sport_topic = "current trending sports events (like NBA, NFL, Champions League)"
        else:
            sport_topic = focus_sport

        news_prompt = f"""
        Act as a sports betting journalist for a {geo} site ({domain}).
        Current Date: {datetime.now().strftime("%Y-%m-%d")}.
        
        Write 3 short, exciting news headlines about: {sport_topic}.
        Focus on: Betting odds, match predictions, and player injuries.
        
        Output ONLY a JSON array: [
            {{"title": "Headline", "date": "Today", "excerpt": "Summary"}}
        ]
        """
        
        # 1. 
        news_prompt = f"""
        Act as a sports editor for a {geo} betting site ({domain}).
        Write 3 short, exciting news headlines about World Cup 2026.
        Output ONLY a JSON array: [{{"title": "...", "date": "...", "excerpt": "..."}}]
        """
        news_resp = model.generate_content(news_prompt)
        news_text = news_resp.text.replace('```json', '').replace('```', '').strip()
        news_data = json.loads(news_text)

        # 2. 
        seo_prompt = f"Write a 50-word SEO footer for {domain} targeting {geo} players. Keywords: Bonus, Safe, App."
        seo_resp = model.generate_content(seo_prompt)
        seo_body = seo_resp.text.strip()
        
        return news_data, seo_body
    except Exception as e:
        print(f"AI Error for {domain}: {e}")
        # 兜底数据
        return [], "Best betting guide 2026."

def generate_matches():
    teams = ["Mexico", "USA", "Brazil", "France", "England"]
    matches = []
    today = datetime.now()
    for i in range(2):
        matches.append({
            "team_a": random.choice(teams),
            "team_b": random.choice(teams),
            "date": (today + timedelta(days=i+1)).strftime("%b %d"),
            "stadium": "MetLife Stadium",
            "odds": f"{random.uniform(1.5, 3.5):.2f}"
        })
    return matches

# --- main ---
def main():
    # 1. 
    with open(OFFERS_FILE, 'r') as f:
        all_offers = json.load(f)
    
    # 2.
    with open(SITES_FILE, 'r') as f:
        sites = json.load(f)

    # 3. 
    print(f"🔄 Updating {len(sites)} sites...")
    
    for site in sites:
    domain = site.get('hostname')
    geo = site.get('geo', 'Global')
    theme = site.get('theme', 'modern')

         focus_sport = site.get('focus_sport', 'General Sports')

    print(f"Updating {domain} covering {focus_sport}...")

    # 传入 focus_sport
    news, seo = generate_ai_content(domain, theme, geo, focus_sport)

        # A. 自动分配 Offer (硬数据)
        site['offer_ids'] = [o['id'] for o in all_offers[:3]]

        # B. AI 生成新闻和 SEO (软数据)
        news, seo = generate_ai_content(domain, theme, geo)
        site['news_data'] = news
        if 'seo_content' not in site: site['seo_content'] = {}
        site['seo_content']['body'] = seo
        site['seo_content']['title'] = f"{domain} - Official Guide"

        # C. 更新赛事
        site['matches_data'] = generate_matches()

        # D. 休息一下防止 API 报错
        time.sleep(2)

    # 4. 保存
    with open(SITES_FILE, 'w') as f:
        json.dump(sites, f, indent=2)
    print("✅ Update Complete!")

if __name__ == "__main__":
    main()
