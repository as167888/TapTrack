import db
import openpyxl
import os
from datetime import datetime

PAGE_SIZE = 20
OUTPUT_DIR = "./export/view"


def _print_header(title):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def show_stats():
    _print_header("数据库统计")
    total = db.get_stats()
    print(f"  游戏总数: {total}")
    print()
    print("  分类统计:")
    print(f"  {'分类':<16} {'数量':>6}")
    print(f"  {'-'*16} {'-'*6}")
    for cat, count in db.get_game_count_by_category():
        print(f"  {cat:<16} {count:>6}")
    print()
    input("按回车键返回...")


def browse_all():
    offset = 0
    while True:
        rows, total = db.get_paginated_games(offset, PAGE_SIZE)
        if not rows:
            print("\n暂无数据")
            input("按回车键返回...")
            return

        _print_header(f"浏览游戏列表 (第 {offset + 1}-{min(offset + PAGE_SIZE, total)} 条, 共 {total} 条)")
        print(f"  {'ID':<6} {'名称':<20} {'分类':<10} {'添加时间':<20} {'详情页链接'}")
        print(f"  {'-'*6} {'-'*20} {'-'*10} {'-'*20} {'-'*56}")
        for row in rows:
            gid, name, app_id, url, cat, created = row
            display_name = name[:18] + ".." if len(name) > 20 else name
            display_cat = (cat or "-")[:8]
            display_url = url[:53] + "..." if len(url) > 56 else url
            print(f"  {gid:<6} {display_name:<20} {display_cat:<10} {created:<20} {display_url}")

        print()
        print(f"  [N] 下一页  [P] 上一页  [E] 导出当前页  [Q] 返回")
        choice = input("  请选择: ").strip().upper()

        if choice == "N":
            if offset + PAGE_SIZE < total:
                offset += PAGE_SIZE
            else:
                print("  已经是最后一页")
        elif choice == "P":
            if offset >= PAGE_SIZE:
                offset -= PAGE_SIZE
            else:
                print("  已经是第一页")
        elif choice == "E":
            _export_to_excel(rows)
        elif choice == "Q":
            return


def browse_by_category():
    cats = db.get_all_categories()
    if not cats:
        print("\n暂无分类数据")
        input("按回车键返回...")
        return

    _print_header("按分类筛选")
    for i, cat in enumerate(cats, 1):
        print(f"  {i}. {cat}")

    print()
    choice = input("请选择分类编号 (0 返回): ").strip()
    if choice == "0" or not choice:
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(cats):
            print("无效选择")
            return
    except ValueError:
        print("无效输入")
        return

    selected_cat = cats[idx]
    rows = db.get_games_by_category(selected_cat)

    _print_header(f"分类: {selected_cat} ({len(rows)} 条)")
    print(f"  {'ID':<6} {'名称':<20} {'添加时间':<20} {'详情页链接'}")
    print(f"  {'-'*6} {'-'*20} {'-'*20} {'-'*56}")
    for row in rows:
        gid, name, app_id, url, cat, created = row
        display_name = name[:18] + ".." if len(name) > 20 else name
        display_url = url[:53] + "..." if len(url) > 56 else url
        print(f"  {gid:<6} {display_name:<20} {created:<20} {display_url}")

    print()
    print(f"  [E] 导出  [Q] 返回")
    choice = input("  请选择: ").strip().upper()
    if choice == "E":
        _export_to_excel(rows)
    elif choice == "Q":
        return


def search():
    _print_header("搜索游戏")
    keyword = input("请输入游戏名称关键词 (留空返回): ").strip()
    if not keyword:
        return

    rows = db.search_games(keyword)
    if not rows:
        print(f"\n未找到包含 \"{keyword}\" 的游戏")
        input("按回车键返回...")
        return

    _print_header(f"搜索结果: \"{keyword}\" ({len(rows)} 条)")
    print(f"  {'ID':<6} {'名称':<24} {'分类':<12} {'添加时间':<20}")
    print(f"  {'-'*6} {'-'*24} {'-'*12} {'-'*20}")
    for row in rows:
        gid, name, app_id, url, cat, created = row
        display_name = name[:22] + ".." if len(name) > 24 else name
        display_cat = (cat or "-")[:10]
        print(f"  {gid:<6} {display_name:<24} {display_cat:<12} {created:<20}")

    print()
    print(f"  [E] 导出  [D] 删除游戏  [Q] 返回")
    choice = input("  请选择: ").strip().upper()
    if choice == "E":
        _export_to_excel(rows)
    elif choice == "D":
        del_id = input("  输入要删除的游戏 ID: ").strip()
        try:
            if db.delete_game(int(del_id)):
                print(f"  已删除 ID={del_id}")
            else:
                print(f"  未找到 ID={del_id}")
        except ValueError:
            print("  无效 ID")
        input("按回车键继续...")


def _export_to_excel(rows):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(OUTPUT_DIR, f"{timestamp}_view_export.xlsx")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "游戏数据"
    ws["A1"] = "ID"
    ws["B1"] = "游戏名称"
    ws["C1"] = "App ID"
    ws["D1"] = "详情页链接"
    ws["E1"] = "分类"
    ws["F1"] = "添加时间"
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 60
    ws.column_dimensions["E"].width = 16
    ws.column_dimensions["F"].width = 22

    for i, row in enumerate(rows, start=2):
        for j, val in enumerate(row, start=1):
            ws.cell(row=i, column=j, value=val)

    wb.save(filepath)
    print(f"  已导出: {filepath}")


def run():
    db.init_db()

    while True:
        _print_header("数据库查看器")
        total = db.get_stats()
        print(f"  当前数据库共有 {total} 条游戏记录\n")
        print("  1. 浏览全部游戏（分页）")
        print("  2. 按分类筛选")
        print("  3. 搜索游戏")
        print("  0. 返回主菜单")
        print()

        choice = input("请选择: ").strip()

        if choice == "1":
            browse_all()
        elif choice == "2":
            browse_by_category()
        elif choice == "3":
            search()
        elif choice == "0":
            break
        else:
            print("无效选项，请重试。")


if __name__ == "__main__":
    run()
