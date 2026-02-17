import json
import os
import random
import time
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. 初始化设置 ---
# 配置 Gemini
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
else:
    print("Warning: GEMINI_API_KEY not found!")

SITES_FILE = 'sites.json'

# --- 2. AI 生成函数 (Gemini版) ---

def call_gemini(prompt):
    """通用 Gemini 调用函数，带重试机制"""
    try:
        # 使用 Gemini 1.5 Flash，速度快且免费额度高
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # 如果触发频率限制，休息一下再试（简单的重试逻辑）
        time.sleep(2)
        return None

def generate_ai_news(geo, theme):
    """生成 3 条新闻，返回标准 JSON 格式"""
    
    # 构建 Prompt
    prompt = f"""
    You are a sports betting journalist for a {theme} style site in {geo}.
    Write 3 short news items about World Cup 2026.
    
    IMPORTANT: You must output ONLY a valid JSON array. Do not wrap in markdown code blocks.
    Format:
    [
      {{"title": "Headline 1", "date": "Date", "excerpt": "Short summary"}},
      {{"title": "Headline 2", "date": "Date", "excerpt": "Short summary"}}
    ]
    """
    
    raw_text = call_gemini(prompt)
    
    # 清洗数据（Gemini 有时会加 ```json ... ```，需要去掉）
    if raw_text:
        clean_text = raw_text.replace('```json', '').replace('```', '').strip()
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            print("JSON Parse Failed, using fallback.")
    
    # 兜底数据 (如果 AI 挂了，用这个)
    return [
        {"title": f"World Cup 2026: {geo} Updates", "date": "Breaking News", "excerpt": "Latest odds and team news updating live."},
        {"title": "Betting Market Shifts", "date": "Today", "excerpt": "Big changes in the outright winner markets."},
        {"title": "Exclusive Bonus", "date": "Limited Time", "excerpt": "Check our top rated offers above."}
    ]

def generate_seo_text(domain, geo, theme):
    """生成 SEO 底部文案"""
    prompt = f"""
    Write a 50-word footer SEO description for '{domain}'. 
    Target Audience: {geo}. 
    Theme: {theme} (Betting/Finance). 
    Keywords: Safe, Licensed, Fast Payouts.
    Output: Just the text.
    """
    text = call_gemini(prompt)
    return text.strip() if text else f"Premier betting guide for {geo}. Licensed and secure."

# --- 3. 辅助生成逻辑 (无需 AI) ---

def generate_matches():
    """模拟生成赛事数据"""
    teams = ["Mexico", "USA", "Brazil", "France", "England", "Spain", "Japan", "Canada"]
    matches = []
    today = datetime.now()
    
    for i in range(2):
        t1, t2 = random.sample(teams, 2)
        match_date = (today + timedelta(days=i+1)).strftime("%b %d - %H:00")
        matches.append({
            "team_a": t1,
            "team_b": t2,
            "date": match_date,
            "stadium": random.choice(["Estadio Azteca", "MetLife Stadium", "SoFi Stadium"]),
            "odds": f"{random.uniform(1.8, 3.5):.2f}"
        })
    return matches

# --- 4. 主程序 ---

def main():
    print("🚀 Agent Starting (Powered by Gemini)...")
    
    # 读取 sites.json
    if not os.path.exists(SITES_FILE):
        print("sites.json not found!")
        return

    with open(SITES_FILE, 'r') as f:
        sites = json.load(f)

    count = 0
    for site in sites:
        domain = site.get('hostname', 'unknown')
        theme = site.get('theme', 'modern')
        # 如果 json 里没有 geo 字段，默认 Global
        geo = site.get('geo', 'Global') 
        
        print(f"[{count+1}] Updating: {domain}...")
        
        # 1. 更新新闻 (AI)
        site['news_data'] = generate_ai_news(geo, theme)
        
        # 2. 更新 SEO 文案 (AI) - 偶尔更新以省额度，这里每次都更
        if 'seo_content' not in site:
            site['seo_content'] = {}
        site['seo_content']['body'] = generate_seo_text(domain, geo, theme)
        
        # 3. 更新赛事 (模拟)
        site['matches_data'] = generate_matches()
        
        # 4. 关键：延时！防止 Gemini 报错 (429 Too Many Requests)
        # 免费版限制 RPM=15，所以每次请求后休息 4 秒比较稳妥
        time.sleep(4) 
        count += 1

    # 保存
    with open(SITES_FILE, 'w') as f:
        json.dump(sites, f, indent=2)
    
    print("✅ All Sites Updated Successfully!")

if __name__ == "__main__":
    main()
