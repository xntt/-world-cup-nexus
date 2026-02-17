import json
import os
import random
import time
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 配置 ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

SITES_FILE = 'sites.json'
OFFERS_FILE = 'offers.json'

# --- AI 生成函数 ---
def generate_ai_content(domain, theme, geo):
    """调用 Gemini 生成新闻和 SEO 文案"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 1. 生成新闻
        news_prompt = f"""
        Act as a sports editor for a {geo} betting site ({domain}).
        Write 3 short, exciting news headlines about World Cup 2026.
        Output ONLY a JSON array: [{{"title": "...", "date": "...", "excerpt": "..."}}]
        """
        news_resp = model.generate_content(news_prompt)
        news_text = news_resp.text.replace('```json', '').replace('```', '').strip()
        news_data = json.loads(news_text)

        # 2. 生成 SEO 文案
        seo_prompt = f"Write a 50-word SEO footer for {domain} targeting {geo} players. Keywords: Bonus, Safe, App."
        seo_resp = model.generate_content(seo_prompt)
        seo_body = seo_resp.text.strip()
        
        return news_data, seo_body
    except Exception as e:
        print(f"AI Error for {domain}: {e}")
        # 兜底数据
        return [], "Best betting guide 2026."

def generate_matches():
    """生成模拟赛事"""
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

# --- 主程序 ---
def main():
    # 1. 读取 Offer 库
    with open(OFFERS_FILE, 'r') as f:
        all_offers = json.load(f)
    
    # 2. 读取站点配置
    with open(SITES_FILE, 'r') as f:
        sites = json.load(f)

    # 3. 遍历并强制更新每个站
    print(f"🔄 Updating {len(sites)} sites...")
    
    for site in sites:
        domain = site.get('hostname')
        geo = "Global" # 这里你可以根据域名判断，比如 if 'mx' in domain: geo='MX'
        theme = site.get('theme', 'modern')

        print(f"Writing content for: {domain}")

        # A. 自动分配 Offer (硬数据)
        # 逻辑：把所有 Offer ID 塞进去，或者根据 Geo 筛选
        # 这里简单粗暴：把 offers.json 里前 3 个 ID 给它
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
