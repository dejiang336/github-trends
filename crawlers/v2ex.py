"""
V2EX 热门话题爬虫 — 国内技术社区今日讨论什么。
纯 HTML 抓取，无需 API key，无需登录。
"""
import re
from crawlers.base import BaseCrawler, logger

HOT_URL = "https://www.v2ex.com/?tab=hot"
TOPIC_URL = "https://www.v2ex.com/t/{}"


class V2EXCrawler(BaseCrawler):
    name = "v2ex"

    def crawl(self) -> list[dict]:
        soup = self.soup(HOT_URL)
        if soup is None:
            return []

        results = []
        cells = soup.select("div.cell.item")
        for cell in cells:
            # 标题 + 链接
            title_el = cell.select_one("span.item_title a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            # href 格式: /t/123456#reply123
            tid_match = re.search(r"/t/(\d+)", href)
            tid = tid_match.group(1) if tid_match else ""

            # 节点
            node_el = cell.select_one("a.node")
            node = node_el.get_text(strip=True) if node_el else ""

            # 回复数
            count_el = cell.select_one("a.count_livid")
            replies = self._number(count_el.get_text(strip=True)) if count_el else 0

            # 用户
            user_el = cell.select_one("strong a")
            user = user_el.get_text(strip=True) if user_el else ""

            results.append({
                "title": title,
                "url": f"https://www.v2ex.com{href}" if href else "",
                "node": node,
                "replies": replies,
                "user": user,
                "tid": tid,
            })

        logger.info("[v2ex] 热门话题 | %d 条", len(results))
        return results

    @staticmethod
    def _number(s: str) -> int:
        try:
            return int(s)
        except (ValueError, TypeError):
            return 0

    def get_topic_detail(self, tid: str) -> dict | None:
        """获取单个话题的详细内容（正文 + 第一条回复）。"""
        url = TOPIC_URL.format(tid)
        soup = self.soup(url)
        if soup is None:
            return None

        # 正文
        content_el = soup.select_one("div.topic_content")
        content = content_el.get_text(strip=True) if content_el else ""

        # 第一条高赞回复
        reply_el = soup.select_one("div.reply_content")
        top_reply = reply_el.get_text(strip=True) if reply_el else ""

        return {
            "content": content[:500],
            "top_reply": top_reply[:300],
        }
