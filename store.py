"""
数据存储 — JSON / 趋势报告 HTML 导出。
"""
import json
import os
from datetime import datetime


def to_json(data: list[dict], path: str) -> str:
    """原子写入（先写 .tmp 再 os.replace）。

    2026.9.27 改：原先直接截断写，中途被杀会留下「存在但内容截断」的快照。
    而幂等闸门正是靠快照文件判断本周采过没有，所以这里的原子性是闸门可信的前提。
    顺带：glob("data_*.json") 不会匹配 data_*.json.tmp，残留 .tmp 不会干扰历史对比。
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # 原子 rename
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
