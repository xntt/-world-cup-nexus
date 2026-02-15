import json
import os
import requests

# --- 配置区 ---
CONFIG_TEMPLATES = {
    "casino": {
        "theme": "cyberpunk",
        "layout_order": ["hero", "offers", "seo"],
        "list_style": "grid",
        "geo_target": "Global"
    },
    "finance": {
        "theme": "modern",
        "layout_order": ["offers", "hero", "seo"],
        "list_style": "table",
        "geo_target": "US/CA"
    }
}

# --- 核心功能 1: 更新 sites.json (修正版 - 支持列表格式) ---
def update_sites_config():
    file_path = 'sites.json'
    
    # 1. 读取现有的配置
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # 确保 data 是一个列表，如果不是（或者是空），初始化为空列表
                if not isinstance(data, list):
                    print("Warning: sites.json was not a list. Resetting to [].")
                    data = []
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    # 2. 定义你要添加的新域名 (在此处修改你要添加的子域名)
    # 提示：每次运行前，在这里填入你想生成的新域名
    new_domains_to_add = [
        "mx-bet.yourdomain.com", 
        "loan-usa.yourdomain.com"
    ] 
    
    added_domains = []

    for domain in new_domains_to_add:
        # 检查域名是否已存在于列表中
        # 我们通过查找 hostname 字段来判断
        exists = False
        for site in data:
            if site.get('hostname') == domain:
                exists = True
                break
        
        if not exists:
            # 决定这个站是什么类型
            site_type = "finance" if "loan" in domain or "bank" in domain else "casino"
            template = CONFIG_TEMPLATES[site_type]
            
            # 生成新的站点配置对象
            new_site_config = {
                "id": f"site_{random_id()}",
                "hostname": domain,
                "name": f"Best {site_type.title()} Deals 2026",
                "theme": template["theme"],
                "layout_order": template["layout_order"],
                "list_style": template["list_style"],
                "hero": {
                    "title": f"Top {site_type.title()} Offers",
                    "subtitle": "Exclusive 2026 World Cup Deals",
                    "cta_text": "Check Offers",
                    "background_image": "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?auto=format&fit=crop&w=1920&q=80"
                },
                # 根据类型分配不同的 Offer ID (需要与 content_pool.json 里的 ID 对应)
                "offer_ids": ["1win_global", "stake_us"] if site_type == "casino" else ["bet365_mx"]
            }
            
            # 添加到列表
            data.append(new_site_config)
            added_domains.append(domain)
            print(f"Added config for: {domain}")
        else:
            print(f"Skipping {domain}, already exists.")

    # 3. 保存回文件
    if added_domains:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return added_domains

# 辅助函数：生成随机ID
def random_id():
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

# --- 核心功能 2: 自动绑定域名到 Cloudflare ---
def bind_to_cloudflare(domains):
    token = os.environ.get("CF_API_TOKEN")
    account_id = os.environ.get("CF_ACCOUNT_ID")
    project_name = os.environ.get("CF_PROJECT_NAME")
    
    if not token:
        print("No CF_API_TOKEN found, skipping Cloudflare binding.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    for domain in domains:
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{project_name}/domains"
        payload = {"name": domain}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"SUCCESS: Bound {domain} to Cloudflare Pages")
            else:
                print(f"FAILED to bind {domain}: {response.text}")
        except Exception as e:
            print(f"Error connecting to Cloudflare: {e}")

# --- 主程序 ---
if __name__ == "__main__":
    newly_added = update_sites_config()
    if newly_added:
        bind_to_cloudflare(newly_added)
    else:
        print("No new domains added.")
