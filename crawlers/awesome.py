"""
Awesome 清单发现 — 搜索新创建的 awesome-* 仓库，识别新兴技术领域。
修复 2026.7.12: 之前返回总星数排行（老面孔），改为按创建时间过滤 + 星速排序。
策略:
  1. 限定最近 365 天内创建的仓库（created:>YYYY-MM-DD）
  2. 按 star 数降序排（新生仓库里星多的 = 增速快的）
  3. 抓取仓库主页提取 created_at / stars_per_day（不做额外请求——从搜索页解析）
"""
import re
from datetime import datetime, timezone, timedelta
from crawlers.base import BaseCrawler, logger

# 以创建当天为起点算日均星数；搜不到创建时间的用 365 天兜底
FALLBACK_DAYS = 365
# created: 限定最近一年
since_dt = datetime.now(timezone.utc) - timedelta(days=FALLBACK_DAYS)
CREATED_SINCE = since_dt.strftime("%Y-%m-%d")

QUERIES = [
    f"awesome created:>{CREATED_SINCE} stars:>10",
    f"awesome-list created:>{CREATED_SINCE} stars:>50",
]


class AwesomeDiscoverer(BaseCrawler):
    name = "awesome"
    SEARCH_URL = "https://github.com/search"

    def crawl(self, per_query: int = 20) -> list[dict]:
        results = []
        seen = set()

        for query in QUERIES:
            resp = self.get(self.SEARCH_URL, params={
                "q": query, "type": "repositories",
                "s": "stars", "o": "desc",
            })
            if resp is None:
                logger.warning("[awesome] 搜索失败: %s", query)
                continue

            repos = self._parse_list(resp.text)
            new = 0
            for r in repos[:per_query]:
                key = r["name"].lower()
                if key in seen:
                    continue
                seen.add(key)
                results.append(r)
                new += 1
            logger.info("[awesome] query=%-40s | +%d repos", query, new)

        # 按 stars_per_day 降序排列（增速榜），同速按总星数
        results.sort(key=lambda r: (r.get("stars_per_day", 0), r.get("stars", 0)), reverse=True)
        return results

    def _parse_list(self, html: str) -> list[dict]:
        """从搜索页提取仓库列表 + star 数 + 创建时间（匹配相邻链接避免侧边栏干扰）"""
        repos = []

        # 1. 提取所有 (链接, 位置, 语言, 主题)
        link_positions = []
        for m in re.finditer(
            r'<a[^>]*href="(/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+)"[^>]*>',
            html
        ):
            path = m.group(1)
            if "/search" in path or "/topics" in path or "/github" in path:
                continue
            parts = path.strip("/").split("/")
            if len(parts) != 2:
                continue
            # 排除 UI shell 路径
            if parts[0] in ("login", "features", "enterprise", "pricing", "settings"):
                continue
            link_positions.append((path, m.start()))

        # 2. 提取所有 star 数（格式: "N stars" 或 "N.Nk stars"）——只取附近有 repo 链接的
        star_positions = []
        for m in re.finditer(r'([\d,]+[km]?)\s*stars?', html, re.IGNORECASE):
            pos = m.start()
            nearby = html[max(0, pos - 400):pos]
            if 'href="/' in nearby:
                star_positions.append((_parse_num(m.group(1)), pos))

        # 3. 提取相对时间标签（"2 days ago", "last week", "on Jun 15" 等）用于估算创建天数
        time_positions = []
        for m in re.finditer(
            r'(?:created\s+)?(\d+)\s+(day|week|month|year)s?\s+ago',
            html, re.IGNORECASE
        ):
            num = int(m.group(1))
            unit = m.group(2).lower()
            if unit == "day" or unit == "days":
                days = num
            elif unit == "week" or unit == "weeks":
                days = num * 7
            elif unit == "month" or unit == "months":
                days = num * 30
            else:
                days = num * 365
            time_positions.append((days, m.start()))

        # 4. 按 HTML 出现顺序配对：链接 → star → 相对时间
        all_items = []
        for pos, kind, val in [(p, 'link', l) for l, p in link_positions]:
            all_items.append((pos, kind, val))
        for pos, kind, val in [(p, 'star', s) for s, p in star_positions]:
            all_items.append((pos, kind, val))
        for pos, kind, val in [(p, 'time', d) for d, p in time_positions]:
            all_items.append((pos, kind, val))
        all_items.sort()

        current_link = None
        current_star = 0
        current_days = FALLBACK_DAYS
        for pos, what, val in all_items:
            if what == 'link':
                if current_link:
                    repos.append(self._make_repo(current_link, current_star, current_days))
                current_link = val
                current_star = 0
                current_days = FALLBACK_DAYS
            elif what == 'star':
                if current_link and current_star == 0:
                    current_star = val
            elif what == 'time':
                if current_link and current_days == FALLBACK_DAYS:
                    current_days = max(val, 1)

        # 最后一个
        if current_link:
            repos.append(self._make_repo(current_link, current_star, current_days))

        return repos

    def _make_repo(self, link: str, stars: int, days: int) -> dict:
        spd = round(stars / max(days, 1), 1) if stars > 0 else 0
        return {
            "name": link.strip("/"),
            "url": f"https://github.com{link}",
            "stars": stars,
            "description": "",
            "stars_per_day": spd,
            "days_old": days,
            "topics": [],
            "language": "",
            "created_at": "",
        }


def _parse_num(s: str) -> int:
    from crawlers.base import parse_number
    return parse_number(s)
