"""
Awesome 清单发现 — 用搜索 API 找新创建的 awesome-* 仓库，识别新兴领域。
修复 2026.8.13: 从网页搜索改用 API（token 生效，30次/分），created_at 直接从 JSON 拿。
策略:
  1. 限定最近 365 天内创建（created:>YYYY-MM-DD）
  2. 按 star 数降序排
  3. created_at 从 API 返回，直接算 stars_per_day
"""
from datetime import datetime, timezone, timedelta
from crawlers.base import BaseCrawler, logger

FALLBACK_DAYS = 365
since_dt = datetime.now(timezone.utc) - timedelta(days=FALLBACK_DAYS)
CREATED_SINCE = since_dt.strftime("%Y-%m-%d")

QUERIES = [
    f"awesome created:>{CREATED_SINCE} stars:>10",
    f"awesome-list created:>{CREATED_SINCE} stars:>50",
]


class AwesomeDiscoverer(BaseCrawler):
    name = "awesome"
    SEARCH_URL = "https://api.github.com/search/repositories"

    def crawl(self, per_query: int = 20) -> list[dict]:
        results = []
        seen = set()

        for query in QUERIES:
            data = self.api_get(self.SEARCH_URL, params={
                "q": query, "sort": "stars", "order": "desc", "per_page": per_query,
            })
            if data is None:
                logger.warning("[awesome] 搜索失败: %s", query)
                continue

            new = 0
            for item in data.get("items", []):
                r = self._make_repo(item)
                key = r["name"].lower()
                if key in seen:
                    continue
                seen.add(key)
                results.append(r)
                new += 1
            logger.info("[awesome] query=%-40s | +%d repos", query, new)

        results.sort(key=lambda r: (r.get("stars_per_day", 0), r.get("stars", 0)), reverse=True)
        return results

    def _make_repo(self, item: dict) -> dict:
        full_name = item.get("full_name", "")
        stars = item.get("stargazers_count", 0)
        created_at = item.get("created_at", "")

        days = FALLBACK_DAYS
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                days = max((datetime.now(timezone.utc) - dt).days, 1)
            except (ValueError, AttributeError):
                days = FALLBACK_DAYS

        spd = round(stars / days, 1) if stars > 0 else 0
        return {
            "name": full_name,
            "url": item.get("html_url", ""),
            "stars": stars,
            "description": item.get("description", "") or "",
            "stars_per_day": spd,
            "days_old": days,
            "topics": item.get("topics", []),
            "language": item.get("language", "") or "",
            "created_at": created_at,
        }
