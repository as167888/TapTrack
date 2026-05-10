import requests
from bs4 import BeautifulSoup
import re
import os
import time
import db

INPUT_FILE = "新增游戏库链接.txt"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}


def main():
    db.init_db()

    print()
    print("=" * 60)
    print("  导入新链接")
    print("=" * 60)
    print()
    print("  文件要求：")
    print(f"    文件名: {INPUT_FILE}")
    print("    编码:   UTF-8")
    print("    格式:   每行一个链接，格式为")
    print("            https://www.taptap.cn/app/<app_id>?os=android")
    print()
    print("  示例:")
    print("    https://www.taptap.cn/app/714119?os=android")
    print("    https://www.taptap.cn/app/123456?os=android")
    print()
    ans = input("  确认导入? (y/n): ").strip().lower()
    if ans != "y":
        print("  已取消。")
        return

    # Read all URLs from file
    if not os.path.exists(INPUT_FILE):
        print(f"\n  错误: 文件 \"{INPUT_FILE}\" 不存在，请先创建该文件。")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    urls = re.findall(r"https://www\.taptap\.cn/app/\d+\?os=android", content)
    print(f"文件中共 {len(urls)} 个链接")

    # Build set of existing URLs for fast lookup
    existing = set(url for _, url in db.get_all_games())

    new_urls = [u for u in urls if u not in existing]
    print(f"已存在: {len(urls) - len(new_urls)}, 需新增: {len(new_urls)}")

    added = 0
    failed = 0

    for idx, full_url in enumerate(new_urls, 1):
        try:
            app_id = re.search(r"/app/(\d+)", full_url).group(1)
            # Fetch detail page (without ?os=android for cleaner response)
            detail_url = f"https://www.taptap.cn/app/{app_id}"

            resp = requests.get(detail_url, headers=HEADERS, timeout=30)
            resp.encoding = "utf-8"

            if resp.status_code != 200:
                print(f"[{idx}/{len(new_urls)}] HTTP {resp.status_code} - {full_url}")
                failed += 1
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            name_meta = soup.find("meta", itemprop="name")
            if not name_meta:
                print(f"[{idx}/{len(new_urls)}] 无名称 - {full_url}")
                failed += 1
                continue

            name = (name_meta.get("content") or "").strip()
            db.insert_game(name, app_id, full_url, "手动导入")

            if idx % 100 == 0 or idx <= 5:
                print(f"[{idx}/{len(new_urls)}] {name} -> OK")

            added += 1
            time.sleep(0.2)

        except Exception as e:
            print(f"[{idx}/{len(new_urls)}] 出错: {e}")
            failed += 1

    print(f"\n完成! 新增 {added}, 失败 {failed}")
    print(f"数据库总计: {db.get_stats()} 个游戏")


if __name__ == "__main__":
    main()
