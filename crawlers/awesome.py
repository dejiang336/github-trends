"""
Awesome 清单发现 — 搜索 awesome-* 仓库，识别新兴技术领域。
纯搜索页提取，不访问仓库主页（避免额外 HTTP 请求）。
"""
import re
from datetime import datetime, timezone
from crawlers.base import BaseCrawler, logger

QUERIES = [
    "awesome-2025 stars:>100",
    "awesome-2026 stars:>50",
    "awesome-list stars:>500",
]


class AwesomeDiscoverer(BaseCrawler):
    name = "awesome"
    SEARCH_URL = "https://github.com/search"

    def crawl(self, per_query: int = 15) -> list[dict]:
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
                if r["name"] in seen:
                    continue
                seen.add(r["name"])
                results.append(r)
                new += 1
            logger.info("[awesome] query=%-26s | +%d repos", query, new)

        return results

    def _parse_list(self, html: str) -> list[dict]:
        """从搜索页提取仓库列表 + star 数（匹配相邻链接避免侧边栏干扰）。"""
        repos = []
        # 1. 提取所有 (链接, 位置)
        link_positions = []
        for m in re.finditer(r'href="(/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+)"', html):
            p = m.group(1)
            if len(p.strip("/").split("/")) == 2 and not any(
                x in p.lower() for x in ["search", "topics", "github", "login", "features"]
            ):
                link_positions.append((p, m.start()))

        # 2. 提取所有 ("N stars", 位置), 只保留附近有链接的
        star_positions = []
        for m in re.finditer(r'([\d,]+[km]?)\s*stars?', html, re.IGNORECASE):
            pos = m.start()
            # 检查前后 300 字符内是否有 repo 链接
            nearby = html[max(0,pos-300):pos]
            if 'href="/' in nearby:
                star_positions.append((_parse_num(m.group(1)), pos))

        # 3. 按 HTML 出现顺序配对
        all_items = [(pos, 'link', path) for path, pos in link_positions] + \
                    [(pos, 'star', count) for count, pos in star_positions]
        all_items.sort()

        current_link = None
        current_star = 0
        for pos, kind, val in all_items:
            if kind == 'link':
                if current_link:
                    repos.append({
                        "name": current_link.strip("/"), "url": f"https://github.com{current_link}",
                        "stars": current_star, "description": "", "stars_per_day": 0,
                        "days_old": 365, "topics": [], "language": "", "created_at": "",
                    })
                current_link = val
                current_star = 0
            else:  # star
                if current_link and current_star == 0:
                    current_star = val
        # 最后一个
        if current_link:
            repos.append({
                "name": current_link.strip("/"), "url": f"https://github.com{current_link}",
                "stars": current_star, "description": "", "stars_per_day": 0,
                "days_old": 365, "topics": [], "language": "", "created_at": "",
            })

        return repos


def _parse_num(s: str) -> int:
    from crawlers.base import parse_number
    return parse_number(s)
