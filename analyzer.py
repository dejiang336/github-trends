"""
趋势分析引擎 — 输入三维爬虫数据，输出趋势洞察。

三个分析维度：
  1. 语言热度 — Trending 各语言 star 增量排名
  2. 赛道体量 — Topics 仓库数量对比
  3. 新兴领域 — Awesome 仓库 star 增速排行
"""


# ── 1. 语言热度分析 ────────────────────────────────────────────

def analyze_language_heat(trending_data: list[dict]) -> dict:
    """
    按语言汇总 Trending 数据：
    - repo_count: 上榜仓库数
    - total_stars_period: 周期内新增 star 数
    - avg_stars: 上榜仓库平均 star 增量
    """
    lang_stats = {}
    for r in trending_data:
        lang = r.get("lang_filter", "Other")
        if lang == "全语言":  # 跳过全语言汇总，无意义
            continue
        if lang not in lang_stats:
            lang_stats[lang] = {"repo_count": 0, "total_new_stars": 0, "repos": []}
        lang_stats[lang]["repo_count"] += 1
        sp = r.get("stars_period", 0)
        lang_stats[lang]["total_new_stars"] += sp
        lang_stats[lang]["repos"].append(r)

    result = {}
    for lang, stats in lang_stats.items():
        count = stats["repo_count"]
        total = stats["total_new_stars"]
        result[lang] = {
            "repo_count": count,
            "total_new_stars": total,
            "avg_new_stars": round(total / count) if count else 0,
        }

    # 按 total_new_stars 降序排
    return dict(
        sorted(result.items(), key=lambda x: x[1]["total_new_stars"], reverse=True)
    )


# ── 2. 赛道体量分析 ────────────────────────────────────────────

def analyze_topic_size(topics_data: list[dict]) -> dict:
    """按类别汇总仓库数，排出最大赛道。"""
    cat_stats = {}
    for t in topics_data:
        cat = t.get("category", "Other")
        if cat not in cat_stats:
            cat_stats[cat] = {"total_repos": 0, "keywords": []}
        cat_stats[cat]["total_repos"] += t.get("repo_count", 0)
        cat_stats[cat]["keywords"].append({
            "kw": t.get("keyword", ""),
            "count": t.get("repo_count", 0),
        })

    return dict(
        sorted(cat_stats.items(), key=lambda x: x[1]["total_repos"], reverse=True)
    )


# ── 3. 新兴领域分析 ────────────────────────────────────────────

def analyze_rising_domains(awesome_data: list[dict], top_n: int = 20) -> list[dict]:
    """识别新兴领域：有创建时间的按 stars/天排序，没有的按总 stars 估算日均。"""
    def _stars_per_day(r):
        spd = r.get("stars_per_day", 0)
        if spd == 0 and r.get("stars", 0) > 0:
            spd = round(r["stars"] / max(r.get("days_old", 365), 1), 1)
        return spd
    sorted_list = sorted(awesome_data, key=_stars_per_day, reverse=True)
    return sorted_list[:top_n]


def find_new_awesome_topics(awesome_data: list[dict], min_days: int = 30, max_days: int = 730) -> list[dict]:
    """（保留，但不依赖创建时间数据）"""
    return [r for r in awesome_data if r.get("stars", 0) > 1000][:20]
