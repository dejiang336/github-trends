"""
爬虫基类 — 限速、重试、UA 伪装、GitHub API + 页面抓取、共享工具函数。
支持主/备用代理自动切换（主代理 2 次失败后切备用）。
"""
import time
import random
import os
import re
import logging
from abc import ABC, abstractmethod
from typing import Optional
import requests
from requests.exceptions import ConnectionError as ReqConnectionError
from requests.exceptions import SSLError as ReqSSLError
from requests.exceptions import ConnectTimeout as ReqConnectTimeout
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_number(s: str) -> int:
    """将 '1.5k' / '2,300' / '1,234' 等人类可读数字转为 int。"""
    s = str(s).strip().lower()
    if not s:
        return 0
    s = s.replace(",", "")
    m = re.match(r"([\d.]+)\s*(k|m)?", s)
    if not m:
        return 0
    val = float(m.group(1))
    suffix = m.group(2)
    if suffix == "k":
        return int(val * 1000)
    elif suffix == "m":
        return int(val * 1_000_000)
    return int(val)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]


def _is_proxy_error(err: Exception) -> bool:
    """代理层错误（连接不上/SSL 握手失败/连接超时）。ReadTimeout 不在此列——那是 GitHub 慢，换代理没用。"""
    return isinstance(err, (ReqConnectionError, ReqSSLError, ReqConnectTimeout))


class BaseCrawler(ABC):
    """所有爬虫的抽象基类。

    代理容灾：主代理 max_retries 次失败后自动切备用代理，备用再 max_retries 次失败该 URL 放弃。
    HTTP 层错误（429/404/503 等）不切代理——那是 GitHub 的问题，换代理没用。
    """

    name: str = "base"

    def __init__(self, rate_limit: float = 2.0, max_retries: int = 1, token: str = "",
                 backup_proxy: str = ""):
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self._last_request_time = 0.0
        self.session = requests.Session()

        # 主代理（Clash 7897），读环境变量
        self._primary_proxy = os.environ.get("HTTP_PROXY", "") or os.environ.get("http_proxy", "")
        # 备用代理（UniClash 7993），参数优先 > HTTP_PROXY_BACKUP 环境变量
        self._backup_proxy = backup_proxy or os.environ.get("HTTP_PROXY_BACKUP", "")
        self._proxy_switched = False

        if self._primary_proxy:
            self.session.proxies = {"http": self._primary_proxy, "https": self._primary_proxy}

        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _wait(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def _random_ua(self) -> str:
        return random.choice(USER_AGENTS)

    def _switch_to_backup(self) -> bool:
        """切到备用代理。返回 False 表示无备用可用。"""
        if not self._backup_proxy or self._proxy_switched:
            return False
        self._proxy_switched = True
        self.session.proxies = {"http": self._backup_proxy, "https": self._backup_proxy}
        logger.warning("[%s] 🔁 主代理不通，切到备用: %s", self.name, self._backup_proxy)
        return True

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        headers = kwargs.pop("headers", {})
        headers.setdefault("User-Agent", self._random_ua())
        headers.setdefault("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")

        # 每代理最多 max_retries 次，总共最多 2× max_retries 次
        proxy_tries = 0

        while True:
            proxy_tries += 1

            try:
                self._wait()
                resp = self.session.get(url, headers=headers, timeout=(5, 15), **kwargs)
                resp.raise_for_status()
                return resp

            except requests.RequestException as e:
                logger.warning("[%s] 请求失败 (%d/%d on %s): %s",
                               self.name, proxy_tries, self.max_retries,
                               "backup" if self._proxy_switched else "primary", e)

                # 主代理 max_retries 次都失败 + 是代理层错误 + 有备用 → 切
                if (not self._proxy_switched
                        and proxy_tries >= self.max_retries
                        and _is_proxy_error(e)
                        and self._switch_to_backup()):
                    proxy_tries = 0  # 重置计数，给备用全新 max_retries 次
                    continue

                # 当前代理也试够 max_retries 次 → 放弃
                if proxy_tries >= self.max_retries:
                    return None

                # 计算退避等待
                wait = 2 ** proxy_tries + random.uniform(0, 1)
                if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                    retry_after = e.response.headers.get("Retry-After", "")
                    if retry_after.isdigit():
                        wait = int(retry_after)
                        logger.warning("[%s] 429 限流，Retry-After: %ss", self.name, wait)

                time.sleep(wait)

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
