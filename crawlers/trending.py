"""
GitHub Trending 爬虫 — 多语言 × 多时间窗口。
"""
from crawlers.base import BaseCrawler, logger

# 七大编程语言
LANGUAGES = {
    "Python":     "python",
    "JavaScript": "javascript",
    "Java":       "java",
    "Go":         "go",
    "Rust":       "rust",
    "C++":        "c++",
    "TypeScript": "typescript",
}

TIME_RANGES = {
    "daily":   "今日",
    "weekly":  "本周",
}


class TrendingCrawler(BaseCrawler):
    name = "trending"

    BASE = "https://github.com/trending"

    def crawl(self) -> list[dict]:
        """遍历所有语言×时间窗口，返回趋势数据。"""
        results = []
        for label, path in LANGUAGES.items():
            for since, since_cn in TIME_RANGES.items():
                url = f"{self.BASE}/{path}?since={since}" if path else f"{self.BASE}?since={since}"
                data = self._parse_page(url, lang=label, since=since)
                results.extend(data)
                logger.info("[trending] %-12s | %s | %d repos", label, since_cn, len(data))
        return results

    def _parse_page(self, url: str, lang: str, since: str) -> list[dict]:
        soup = self.soup(url)
        if soup is None:
            return []

        rows = []
        articles = soup.select("article.Box-row")
        for art in articles:
            h2 = art.select_one("h2.h3 a")
            if not h2:
                continue
            name = h2.get_text(strip=True).replace(" ", "").replace("\n", "")
            href = h2.get("href", "")
            repo_url = f"https://github.com{href}" if href else ""

            desc_el = art.select_one("p.col-9")
            description = desc_el.get_text(strip=True) if desc_el else ""

            lang_el = art.select_one('[itemprop="programmingLanguage"]')
            repo_lang = lang_el.get_text(strip=True) if lang_el else ""

            stars_el = art.select_one(f"a[href='/{name.strip()}/stargazers']")
            stars = self._number(stars_el.get_text(strip=True)) if stars_el else 0

            forks_el = art.select_one(f"a[href='/{name.strip()}/forks']")
            forks = self._number(forks_el.get_text(strip=True)) if forks_el else 0

            # 今日/本周 star 增量
            today_els = art.select("span.d-inline-block.float-sm-right")
            stars_period = ""
            for el in today_els:
                txt = el.get_text(strip=True)
                if "star" in txt:
                    stars_period = txt.split()[0].replace(",", "")
                    break

            rows.append({
                "repo": name.strip(),
                "url": repo_url,
                "description": description,
                "language": repo_lang or lang,
                "stars": stars,
                "forks": forks,
                "stars_period": self._number(stars_period),
                "period": since,
                "lang_filter": lang,
            })
        return rows

    @staticmethod
    def _number(s: str) -> int:
        s = s.replace(",", "").replace(".", "")
        try:
            return int(s)
        except ValueError:
            return 0
