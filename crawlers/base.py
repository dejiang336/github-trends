"""
爬虫基类 — 限速、重试、UA 伪装、GitHub API + 页面抓取。
"""
import time
import random
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

class BaseCrawler(ABC):
    """所有爬虫的抽象基类。"""
    name: str = "base"

    def __init__(self, rate_limit: float = 2.0, max_retries: int = 3, token: str = ""):
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self._last_request_time = 0.0
        self.session = requests.Session()
        # 支持代理（Clash 等），优先读环境变量
        proxy = os.environ.get("HTTP_PROXY", "") or os.environ.get("http_proxy", "")
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _wait(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def _random_ua(self) -> str:
        return random.choice(USER_AGENTS)

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        headers = kwargs.pop("headers", {})
        headers.setdefault("User-Agent", self._random_ua())
        headers.setdefault("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")

        for attempt in range(1, self.max_retries + 1):
            try:
                self._wait()
                resp = self.session.get(url, headers=headers, timeout=30, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                logger.warning("[%s] 请求失败 (%d/%d): %s", self.name, attempt, self.max_retries, e)
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt + random.uniform(0, 1))
        return None

    def soup(self, url: str, **kwargs) -> Optional[BeautifulSoup]:
        resp = self.get(url, **kwargs)
        if resp is None:
            return None
        return BeautifulSoup(resp.text, "lxml")

    def api_get(self, url: str, **kwargs) -> Optional[dict]:
        """请求 GitHub API，返回 JSON。"""
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/vnd.github+json")
        headers.setdefault("X-GitHub-Api-Version", "2022-11-28")
        resp = self.get(url, headers=headers, **kwargs)
        if resp is None:
            return None
        try:
            return resp.json()
        except Exception as e:
            logger.error("[%s] API JSON 解析失败: %s", self.name, e)
            return None

    @abstractmethod
    def crawl(self, **kwargs) -> list[dict]:
        ...
