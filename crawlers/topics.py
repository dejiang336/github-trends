"""
GitHub Topics 趋势探测 — 用搜索 API 获取仓库数量（token 认证，30次/分）。
"""
from crawlers.base import BaseCrawler, logger

# 精选核心关键词（减少查询量，避免限流）
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
    SEARCH_URL = "https://api.github.com/search/repositories"

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
                status = f"{count:,}" if count >= 0 else "限流/失败"
                logger.info("[topics] %-12s | %-18s | %s repos", category, kw, status)
        return results

    def _search_count(self, query: str) -> int:
        data = self.api_get(self.SEARCH_URL, params={"q": query, "per_page": 1})
        if data is None:
            return -1  # 请求失败，不是零结果
        return data.get("total_count", -1)
