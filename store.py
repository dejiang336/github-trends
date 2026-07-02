"""
数据存储 — JSON / 趋势报告 HTML 导出。
"""
import json
import os
from datetime import datetime


def to_json(data: list[dict], path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return os.path.abspath(path)


def save_snapshot(name: str, data: list[dict]) -> str:
    """保存带时间戳的 JSON 快照，用于后续对比。"""
    os.makedirs("output/snapshots", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"output/snapshots/{name}_{ts}.json"
    return to_json(data, path)


def auto_filename(name: str = "report") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"output/{name}_{ts}.html"
