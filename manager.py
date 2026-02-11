import json
import random
import os
import requests # 需要在requirements.txt里添加

# --- 配置区 ---
# 定义不同类型的配置模板
CONFIG_TEMPLATES = {
    "casino": {
        "theme": "dark_neon",
        "layout": ["hero", "offers_table", "guide_content"],
        "geo_target": "Global"
    },
    "finance": {
        "theme": "light_blue",
        "layout": ["credit_card_grid", "calculator", "faq"],
        "geo_target": "US/CA"
    }
}

# --- 核心功能 1: 更新 sites.json ---
def update_sites_config():
    # 读取现有的配置
    try:
        with open('sites.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    # 读取你想要添加的新域名列表 (可以是从 csv 读取，这里模拟直接添加)
    # 实际操作中，你可以上传一个 new_domains.txt 让 Agent 读取
    new_domains = ["mx.worldcup-guide.com", "loan-usa.yourdomain.com"] 

    for domain in new_domains:
        if domain not in data:
            # 决定这个站是什么类型
            site_type = "casino" if "bet" in domain else "finance"
            
            # 生成配置
            data[domain] = {
                "type": site_type,
                "config": CONFIG_TEMPLATES[site_type],
                "content": {
                    "h1": f"Best {site_type.title()} Offers for 2026",
                    "hero_bg": f"assets/{site_type}_bg.jpg"
                },
                "offer_ids": ["1win", "stake"] if site_type == "casino" else ["bank_a", "bank_b"]
            }
            print(f"Added config for: {domain}")

    # 保存回文件
    with open('sites.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return new_domains

# --- 核心功能 2: 自动绑定域名到 Cloudflare ---
def bind_to_cloudflare(domains):
    token = os.environ.get("CF_API_TOKEN")
    account_id = os.environ.get("CF_ACCOUNT_ID")
    project_name = os.environ.get("CF_PROJECT_NAME")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    for domain in domains:
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{project_name}/domains"
        payload = {"name": domain}
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"SUCCESS: Bound {domain} to Cloudflare Pages")
        else:
            print(f"FAILED: {domain} - {response.text}")

# --- 主程序 ---
if __name__ == "__main__":
    newly_added = update_sites_config()
    if newly_added:
        bind_to_cloudflare(newly_added)
