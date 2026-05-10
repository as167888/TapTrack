import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
import random
import db

def run():
    print("步骤 1：从数据库读取游戏链接...")
    db.init_db()
    games = db.get_all_games_full()
    if not games:
        print("数据库中无游戏链接，请先运行 crawl_bangdan.py 或 import_new_links.py。")
        return
    urls = [(row[0], row[3]) for row in games]  # (id, detail_url)
    print(f"成功从数据库读取，共找到 {len(urls)} 个游戏链接待爬取。\n")

    # 设置请求头，伪装成正常浏览器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    results = []

    print("步骤 2 & 3 & 4：开始请求并解析网页数据...")
    for index, (game_id, original_url) in enumerate(urls, start=1):
        # 数据库中的链接已包含 ?os=android，直接使用
        target_url = str(original_url).strip()
            
        print(f"\n[{index}/{len(urls)}] 正在爬取...")
        
        # 定义要保存的字段（移除了“详情页链接”）
        game_data = {
            "请求链接": target_url,
            "游戏名称": "获取失败",
            "发布日期": "获取失败",
            "下载量": "获取失败",
            "关注量": "获取失败",
            "评分": "获取失败",
            "评价数量": "获取失败"
        }

        try:
            # 2. 发送 GET 请求
            response = requests.get(target_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # 3. 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- 解析第一部分：从 JSON-LD 中获取名称、发布日期、下载量、评分等 ---
            json_scripts = soup.find_all('script', type='application/ld+json')
            parsed_success = False
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "VideoGame":
                        game_data["游戏名称"] = data.get("name", "未找到")
                        
                        # 优化：处理发布日期，只保留年月日
                        raw_date = data.get("datePublished", "未找到")
                        if raw_date and raw_date != "未找到":
                            # 取 "T" 或 空格 前面的部分
                            game_data["发布日期"] = str(raw_date).split('T')[0].split(' ')[0]
                        else:
                            game_data["发布日期"] = "未找到"
                        
                        interaction = data.get("interactionStatistic", {})
                        game_data["下载量"] = interaction.get("userInteractionCount", "未找到")
                        
                        aggregate = data.get("aggregateRating", {})
                        game_data["评分"] = aggregate.get("ratingValue", "未找到")
                        game_data["评价数量"] = aggregate.get("ratingCount", "未找到")
                        
                        parsed_success = True
                        break
                except json.JSONDecodeError:
                    continue
            
            # --- 解析第二部分：从 Nuxt 数据包中获取 fans_count (关注量) ---
            try:
                nuxt_script = soup.find('script', id='__NUXT_DATA__')
                if nuxt_script:
                    nuxt_data = json.loads(nuxt_script.string)
                    if isinstance(nuxt_data, list):
                        # 遍历 Nuxt 数据数组，寻找包含 fans_count 的字典
                        for item in nuxt_data:
                            if isinstance(item, dict) and "fans_count" in item:
                                # 获取指针索引
                                fans_count_idx = item["fans_count"]
                                # 通过索引去数组里拿真实的数据
                                if isinstance(fans_count_idx, int) and fans_count_idx < len(nuxt_data):
                                    game_data["关注量"] = nuxt_data[fans_count_idx]
                                break
            except Exception as e:
                print(f"  -> 解析关注量出现异常: {e}")

            # 5. 实时输出当前步骤提取到的所有内容
            if parsed_success:
                print("  -> 成功提取数据：")
                for key, value in game_data.items():
                    print(f"     - {key}: {value}")
            else:
                print("  -> 提取失败：未能在页面中找到匹配的 JSON 数据结构。")
                
        except requests.exceptions.RequestException as e:
            print(f"  -> 请求失败 | 错误信息: {e}")
            
        results.append(game_data)

        # 随机休眠 1~3 秒，防封
        time.sleep(random.uniform(1, 3))

    # 7. 输出文件，增加时间日期前缀
    print("\n步骤 7：正在保存爬取结果...")
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{current_time}_taptap_spider_result.xlsx"
    
    try:
        output_df = pd.DataFrame(results)
        output_df.to_excel(output_filename, index=False)
        print(f"爬虫执行完毕！成功将结果保存至当前目录下的: {output_filename}")
    except Exception as e:
        print(f"保存文件失败: {e}")

if __name__ == "__main__":
    run()