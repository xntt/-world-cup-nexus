import json
import os
import urllib.parse
import feedparser
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
import time
import random

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def get_google_news_rss(topic, geo):
    """动态获取最新的真实世界新闻"""
    encoded_topic = urllib.parse.quote(topic)
    geo_code = "MX" if "Mexico" in geo else "US" 
    return f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-{geo_code}&gl={geo_code}"

def fetch_ai_content(site_config):
    topic = site_config.get('topic', 'Sports')
    lang = site_config.get('lang', 'en')
    geo = site_config.get('geo', 'Global')
    
    # 1. 抓取 RSS 喂给 AI
    rss_url = get_google_news_rss(topic, geo)
    feed = feedparser.parse(rss_url)
    
    news_titles = [entry.title for entry in feed.entries[:5]]
    news_context = "\n".join([f"- {title}" for title in news_titles])
    
    if not news_context:
        news_context = f"General updates and predictions regarding {topic} in {geo}."

    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    You are an expert SEO Content Creator and Betting Analyst.
    Target Audience: {geo}. Language MUST BE: {lang}. Topic: {topic}.
    
    Latest real news context:
    {news_context}

    Return strictly in this JSON format:
    {{
      "news": [
        {{"title": "Translating exciting headline to {lang}", "excerpt": "2 sentences SEO rich summary"}} // Generate 4 items
      ],
      "matches": [
        {{"team_a": "Entity 1", "team_b": "Entity 2", "date": "Tomorrow", "odds": "+150 or 2.50"}} // Generate 3 trending matchups
      ],
      "faq": [
        {{"q": "Popular question about {topic}", "a": "Detailed answer matching search intent"}} // Generate 3 items
      ],
      "seo_article": "<h2>SEO optimized H2 Title</h2><p>A professional, engaging 300+ word article analyzing the current news context. Use <strong>, <ul> and other HTML tags.</p>"
    }}
    """
    
    # 容错机制设计：如果大模型罢工，网站内容不能空，使用兜底数据
    fallback_data = {
        "news": [{"title": f"Latest Updates on {topic}", "excerpt": "We are gathering the newest information. Please check back shortly for full updates."}],
        "matches": [{"team_a": "TBD", "team_b": "TBD", "date": "Soon", "odds": "-"}],
        "faq": [{"q": "How to start betting?", "a": "Choose a trusted platform from our recommended list above and sign up."}],
        "seo_article": f"<h2>Guide to {topic}</h2><p>Stay tuned for our deep-dive analysis and expert predictions...</p>"
    }

    try:
        resp = model.generate_content(prompt)
        ai_data = json.loads(resp.text)
        
        # 验证返回的 JSON 结构是否完整
        if "news" in ai_data and "seo_article" in ai_data:
            return ai_data
        return fallback_data
    except Exception as e:
        print(f"⚠️ AI Generation Error for {topic}: {e} -> Using Fallback Data.")
        return fallback_data

def build_sites():
    print("🚀 Starting the pSEO Engine...")
    
    try:
        with open('sites.json', 'r', encoding='utf-8') as f:
            sites = json.load(f)
    except Exception as e:
        print(f"❌ Error loading sites.json: {e}")
        return

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')

    for site in sites:
        hostname = site['hostname']
        print(f"⏳ Processing Website: {hostname}")
        
        # 1. 抓取 AI 动态内容
        ai_data = fetch_ai_content(site)
        
        # 2. 将 settings 与 ai_data 合并注入模板
        context = {**site, "ai_data": ai_data}
        
        try:
            html_content = template.render(context)
            
            output_dir = f"dist/{hostname}"
            os.makedirs(output_dir, exist_ok=True)
            
            with open(f"{output_dir}/index.html", 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"✅ SUCCESS: Built {output_dir}/index.html")
            
        except Exception as e:
            print(f"❌ Error rendering HTML for {hostname}: {e}")
            
        time.sleep(random.randint(2, 5)) # API 速率保护，防止被封 IP 或限制

    print("🎉 All websites generated successfully in 'dist' folder!")

if __name__ == "__main__":
    build_sites()
