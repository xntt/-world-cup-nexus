import json
import os
import google.generativeai as genai
from jinja2 import Template
import markdown

# 1. 唤醒大模型 (请确保 Github Actions 的 Secrets 里面存了 GEMINI_API_KEY)
# 这里用的是完全免费的 Gemini 模型，速度极快
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ 警告: 没有找到 GEMINI_API_KEY，将生成无 AI 内容的占位页面。")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 读取配置和模板
with open('sites.json', 'r', encoding='utf-8') as f:
    sites = json.load(f)

with open('template.html', 'r', encoding='utf-8') as f:
    template_str = f.read()
template = Template(template_str)

# 3. 循环为每个网站生成定制化内容
for site in sites:
    hostname = site['hostname']
    print(f"[{hostname}] ⚙️ 正在生成站点...")

    ai_html_content = "<p>Coming soon...</p>" # 默认占位内容

    # 4. 指挥 AI 自动写 SEO 文章 (关键点：针对该国家的语言和话题)
    if api_key:
        prompt = f"""
        You are an expert sports journalist and SEO copywriter.
        Write a highly engaging, 3-paragraph article about "{site['topic']}".
        Target Audience Geo: {site['geo']}
        Language: {site['lang']}
        Include: Latest odds, predictions, and tips. Use H3 tags for subheadings.
        Format strictly in Markdown. Do not include a main H1 title.
        """
        try:
            print(f"[{hostname}] 🤖 正在请求 AI 撰写关于 {site['topic']} ({site['lang']}) 的原创文章...")
            response = model.generate_content(prompt)
            # 将 AI 生成的 Markdown 转成 HTML，以便放进网页
            ai_html_content = markdown.markdown(response.text)
            print(f"[{hostname}] ✅ AI 文案生成成功！")
        except Exception as e:
            print(f"[{hostname}] ❌ AI 生成失败: {e}")

    # 5. 把配置和 AI 内容渲染到 HTML 模板中
    final_html = template.render(
        site=site,
        ai_content=ai_html_content
    )

    # 6. 保存为静态网站文件
    output_dir = f"dist/{hostname}"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/index.html", "w", encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"[{hostname}] 🎉 静态文件生成完毕存放于: {output_dir}/index.html\n")

print("🚀 所有站点自动部署构建完成！")
