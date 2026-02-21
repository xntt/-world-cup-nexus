import json
import os
import urllib.parse
import feedparser
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
import time

# 配置 API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def get_google_news_rss(topic):
    """根据关键词获取 Google News 热点"""
    encoded_topic = urllib.parse.quote(topic)
    return f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-US&gl=US&ceid=US:en"

def fetch_and_generate_content(topic):
    """抓取热点并让 AI 生成符合 SEO 的内容"""
    rss_url = get_google_news_rss(topic)
    feed = feedparser.parse(rss_url)
    
    news_items = []
    for entry in feed.entries[:5]: # 抓取前5条热点
        news_items.append(f"- {entry.title}")
    
    news_text = "\n".join(news_items)
    
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    Topic is: {topic}. 
    Latest Trending Headlines: {news_text}

    TASK:
    Generate a JSON output for a website based on these events. Focus on engagement and predictions.
    
    REQUIRED JSON FORMAT:
    {{
      "news": [
        {{"title": "Clickbaity SEO Headline 1", "summary": "Exciting 2 sentence summary of the trend..."}}
      ],
      "events": [
        {{"name": "Event related to topic", "date": "Soon", "prediction_odds": "75% chance"}}
      ],
      "faqs": [
        {{"q": "What is the latest about {topic}?", "a": "Detailed answer optimized for SEO..."}}
      ],
      "seo_article": "<h3>In-depth Analysis</h3><p>Write a 400-word engaging article using LSI keywords, facts, and predictions about {topic}. Provide HTML code.</p>"
    }}
    """
    
    try:
        resp = model.generate_content(prompt)
        # Gemini API 配置了返回 JSON，所以直接读取
        return json.loads(resp.text)
    except Exception as e:
        print(f"AI Error for {topic}: {e}")
        return None

def build_static_sites():
    """读取集中文档，并生成纯 HTML，彻底避免前端 Bug"""
    
    # 我们只维护 site_config.json 这个“集中文档”！
    with open('sites.json', 'r', encoding='utf-8') as f:
        sites = json.load(f)

    # 准备 HTML 模板引擎
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')

    for site in sites:
        topic = site['topic']
        print(f"--> Updating content for {site['hostname']} (Topic: {topic})")
        
        # 1. 自动生成内容
        ai_data = fetch_and_generate_content(topic)
        time.sleep(3) # 避免请求过快
        
        if ai_data:
            # 2. 将基础配置与 AI 生成的内容合并
            context = {**site, **ai_data}
            
            # 3. 渲染出无 bug 的纯静态 HTML 页面
            html_content = template.render(context)
            
            # 4. 创建站点文件夹并保存
            os.makedirs(f"dist/{site['hostname']}", exist_ok=True)
            output_path = f"dist/{site['hostname']}/index.html"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"Successfully built: {output_path}")

if __name__ == "__main__":
    build_static_sites()
