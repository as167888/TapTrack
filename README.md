# TapTrack - TapTap 游戏数据爬取系统

一个用于爬取 [TapTap](https://www.taptap.cn) 热门榜单游戏数据的工具，支持自动发现新游戏、爬取游戏详情、数据持久化存储和导出。

## 功能

- **爬取榜单** — 从 TapTap 各热门榜单（热门榜、热玩榜、新品榜、分类榜等）爬取游戏详情页链接，自动去重后存入 SQLite 数据库
- **导入链接** — 支持从文件批量导入游戏链接
- **爬取详情** — 从数据库读取游戏链接，爬取游戏名称、发布日期、下载量、关注量、评分、评价数量等信息
- **数据查看** — 支持分页浏览、按分类筛选、关键词搜索，可导出 Excel

## 项目结构

```
download/
├── main.py              # 主程序入口，提供菜单界面
├── db.py                # 数据库模块（SQLite）
├── crawl_bangdan.py     # 爬取榜单，提取游戏链接并入数据库
├── crawl_detail.py      # 爬取游戏详情页数据并导出
├── import_new_links.py  # 从文件批量导入游戏链接
├── view_database.py     # 数据库查看器（浏览、搜索、导出）
├── games.db             # SQLite 数据库
├── 榜单链接.txt          # 榜单链接配置文件
└── 新增游戏库链接.txt    # 手动导入链接配置文件
```

## 环境要求

- Python 3.7+
- 依赖包：`requests`, `beautifulsoup4`, `lxml`, `openpyxl`, `pandas`

```bash
pip install requests beautifulsoup4 lxml openpyxl pandas
```

## 使用方法

### 主程序入口

```bash
python main.py
```

菜单选项：

```
========================================
    TapTap 游戏数据爬取系统
========================================
  1. 爬取榜单    - 从榜单获取游戏链接并入数据库
  2. 导入新链接  - 从文件导入新增游戏链接
  3. 爬取详情    - 从数据库读取链接并爬取详情
  4. 查看数据    - 浏览数据库中已保存的数据
  0. 退出
========================================
```

### 各模块独立运行

```bash
python crawl_bangdan.py     # 仅爬取榜单链接
python crawl_detail.py      # 仅爬取游戏详情
python import_new_links.py  # 仅导入新链接
python view_database.py     # 仅查看数据库
```

## 工作流程

1. **爬取榜单** → 从 `榜单链接.txt` 读取榜单 URL，爬取每页的游戏名称和详情链接
2. **去重入库** → 将爬取的链接与数据库中已有链接比对，新链接自动写入数据库
3. **爬取详情** → 从数据库读取所有游戏链接，逐个请求详情页，解析并提取数据
4. **输出结果** → 将爬取结果导出为带时间戳的 Excel 文件
5. **查看数据** → 通过数据库查看器浏览、筛选、搜索已保存的游戏数据

## 数据库

使用 SQLite 数据库 `games.db`，表结构：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键自增 |
| name | TEXT | 游戏名称 |
| app_id | TEXT | TapTap App ID |
| detail_url | TEXT | 游戏详情页链接（唯一） |
| category | TEXT | 来源榜单分类 |
| created_at | TEXT | 添加时间 |

## 注意事项

- 爬取时有请求间隔，避免对目标服务器造成压力
- 如需修改榜单链接，编辑 `榜单链接.txt` 文件（格式：`分类名\tURL`）
- 导入新链接时，确保 `新增游戏库链接.txt` 中每行一个完整 URL
- 导出的 Excel 文件位于当前目录或 `export/` 目录下
