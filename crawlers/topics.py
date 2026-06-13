"""
GitHub Topics 趋势探测 — 从 HTML 搜索页面提取仓库数量。
限流规避: 精选关键词 + 大间隔 + 单次会话复用。
"""
import re
from crawlers.base import BaseCrawler, logger

# 精选核心关键词（减少查询量，避免 429）
TOPICS = {
    "AI/大模型":     ["llm", "agent", "rag"],
    "云原生":        ["kubernetes", "docker"],
    "前端":          ["react", "vue", "nextjs"],
    "后端框架":       ["spring-boot", "django", "gin"],
    "数据/AI":       ["machine-learning", "deep-learning"],
    "Rust/WASM":    ["rust", "wasm"],
    "移动开发":       ["flutter", "react-native"],
    "低代码":         ["low-code", "no-code"],
}


class TopicsCrawler(BaseCrawler):
    name = "topics"
    SEARCH_URL = "https://github.com/search"

    def crawl(self) -> list[dict]:
        results = []
        for category, keywords in TOPICS.items():
            for kw in keywords:
                count = self._search_count(kw)
                results.append({
                    "category": category,
                    "keyword": kw,
                    "repo_count": count,
                })
                status = f"{count:,}" if count else "限流"
                logger.info("[topics] %-12s | %-18s | %s repos", category, kw, status)
        return results

    def _search_count(self, query: str) -> int:
        resp = self.get(self.SEARCH_URL, params={
            "q": query, "type": "repositories",
        })
        if resp is None:
            return 0
        m = re.search(r'([\d,]+[km]?)\s*results?\b', resp.text, re.IGNORECASE)
        if not m:
            return 0
        return self._parse(m.group(1))

    @staticmethod
    def _parse(s: str) -> int:
        s = s.strip().lower().replace(",", "")
        if s.endswith("k"):
            return int(float(s[:-1]) * 1000)
        if s.endswith("m"):
            return int(float(s[:-1]) * 1_000_000)
        try:
            return int(s)
        except ValueError:
            return 0
