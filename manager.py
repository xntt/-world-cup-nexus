import json
import os
import urllib.parse
import feedparser
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
import time

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def get_google_news_rss(topic, geo):
    """根据关键词和国家获取真实热点"""
    encoded_topic = urllib.parse.quote(topic)
    # 通过 gl (地理位置) 改写热点源
    geo_code = "MX" if geo == "Mexico" else "US" 
    return f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-{geo_code}&gl={geo_code}"

def fetch_ai_content(site_config):
    topic = site_config['topic']
    lang = site_config.get('lang', 'en')
    geo = site_config.get('geo', 'Global')
    
    rss_url = get_google_news_rss(topic, geo)
    feed = feedparser.parse(rss_url)
    news_context = "\n".join([f"- {entry.title}" for entry in feed.entries[:5]])
    
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    You are an expert SEO Content Creator and Betting Analyst.
    Target Audience: People from {geo}.
    Language MUST BE: {lang}.
    Topic: {topic}.
    
    Here are the latest real news headlines about this topic:
    {news_context}

    Create an engaging website content update. Return strictly in this JSON format:
    {{
      "news": [
        {{"title": "(Exciting headline translated to {lang})", "excerpt": "(2 sentences summary)"}} // Need 3 items
      ],
      "matches": [
        {{"team_a": "Entity 1", "team_b": "Entity 2", "date": "Tomorrow", "odds": "+150"}} // Need 2 items based on topic (can be sports teams, politicians, or esports)
      ],
      "faq": [
        {{"q": "(Common question about {topic})", "a": "(Detailed answer)"}} // Need 2 items
      ],
      "seo_article": "<h3>(H3 Title)</h3><p>(A 300-word SEO optimized analytical article using HTML tags like <b>, <ul> based on the real news.)</p>"
    }}
    """
    try:
        resp = model.generate_content(prompt)
        return json.loads(resp.text)
    except Exception as e:
        print(f"Failed to generate for {topic}: {e}")
        return {
            "news": [{"title": "News updating...", "excerpt": "Please check back later."}],
            "matches": [{"team_a": "TBD", "team_b": "TBD", "date": "TBD", "odds": "-"}],
            "faq": [{"q": "Loading?", "a": "Yes"}],
            "seo_article": "<p>Content is being updated by our system...</p>"
        }

def build_sites():
    with open('sites.json', 'r', encoding='utf-8') as f:
        sites = json.load(f)

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')

    for site in sites:
        print(f"🚀 Processing: {site['hostname']} (Topic: {site['topic']}, Geo: {site['geo']})")
        
        # 1. 让 Agent 获取最新数据
        ai_data = fetch_ai_content(site)
        
        # 2. 合并配置与数据
        context = {**site, "ai_data": ai_data}
        
        # 3. 生成死木一样稳定的纯静态 HTML
        html_content = template.render(context)
        
        # 4. 保存到各自的网站目录
        output_dir = f"dist/{site['hostname']}"
        os.makedirs(output_dir, exist_ok=True)
        
        with open(f"{output_dir}/index.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✅ Built successfully: {output_dir}/index.html")
        time.sleep(3) # 防止触发 API 频率限制

if __name__ == "__main__":
    build_sites()
