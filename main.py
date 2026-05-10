"""
TapTap 游戏数据爬取系统 - 主程序入口
"""

import db
import crawl_bangdan
import crawl_detail
import import_new_links
import view_database


def show_banner():
    print()
    print("=" * 44)
    print("    TapTap 游戏数据爬取系统")
    print("=" * 44)
    print()
    print("  工作原理：")
    print("    爬取榜单   → 从各榜单页面获取游戏链接")
    print("    对比去重   → 与数据库中的链接比对，新链接加入数据库")
    print("    爬取详情   → 从数据库读取完整链接进行详情爬取")
    print("    查看数据   → 浏览数据库中已保存的游戏链接")


def show_menu():
    total = db.get_stats()
    print("=" * 44)
    print(f"  数据库中游戏链接数量: {total}")
    print()
    print("  请输入序号，选择以下功能")
    print("  1. 爬取榜单    - 从榜单获取游戏链接并入数据库")
    print("  2. 导入新链接  - 从文件导入新增游戏链接")
    print("  3. 爬取详情    - 从数据库读取链接并爬取详情")
    print("  4. 查看数据    - 浏览数据库中已保存的数据")
    print("  0. 退出")
    print("=" * 44)


def main():
    db.init_db()

    while True:
        show_banner()
        show_menu()
        choice = input("请选择: ").strip()

        if choice == "1":
            crawl_bangdan.run()
        elif choice == "2":
            import_new_links.main()
        elif choice == "3":
            crawl_detail.run()
        elif choice == "4":
            view_database.run()
        elif choice == "0":
            print("再见!")
            break
        else:
            print("无效选项，请重试。")


if __name__ == "__main__":
    main()
