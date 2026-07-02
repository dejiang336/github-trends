#!/usr/bin/env python3
"""
🚀 GitHub 技术趋势探测器 — 爬数据 → AI 分析 → 可视化报告

用法:
    python main.py                      # 采集三维数据，存 output/latest_data.json
    python main.py --report --view      # 从已有数据 + AI 洞察生成 HTML 报告
    python main.py --trending           # 只抓 Trending（1 分钟）
    python main.py --save               # 采集并保存历史快照（用于下次对比）
"""

import argparse, logging, sys, os, json, webbrowser, glob as globmod, traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawlers.trending import TrendingCrawler
from crawlers.topics import TopicsCrawler
from crawlers.awesome import AwesomeDiscoverer
from store import to_json, auto_filename
from analyzer import (
    analyze_language_heat, analyze_topic_size,
    analyze_rising_domains,
)

DATA_FILE      = "output/latest_data.json"
INSIGHTS_FILE  = "output/insights.json"
SNAPSHOT_DIR   = "output/snapshots"


def build_parser():
    p = argparse.ArgumentParser(description="GitHub 技术趋势探测器")
    p.add_argument("--trending", action="store_true", help="仅 Trending")
    p.add_argument("--topics",   action="store_true", help="仅 Topics")
    p.add_argument("--awesome",  action="store_true", help="仅 Awesome")
    p.add_argument("--report",   action="store_true", help="从已存数据生成 HTML 报告")
    p.add_argument("--view",     action="store_true", help="打开浏览器")
    p.add_argument("--save",     action="store_true", help="保存历史快照（自动）")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def _dedup_top(items: list[dict], key: str, sort_by: str, top_n: int = 20) -> list[dict]:
    """去重后取 Top-N——同 key 只保留 sort_by 最高的。"""
    deduped = {}
    for item in items:
        k = item[key]
        if k not in deduped or item[sort_by] > deduped[k][sort_by]:
            deduped[k] = item
    return sorted(deduped.values(), key=lambda r: r[sort_by], reverse=True)[:top_n]


# ═══════════════════════════════════════════════════════════════
#  采集模式
# ═══════════════════════════════════════════════════════════════

def collect_mode(args):
    run_all = not any([args.trending, args.topics, args.awesome])

    # GitHub token：优先读环境变量，其次读 claude 配置
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        try:
            claude_cfg = json.load(open(os.path.expanduser("~/.claude.json"), encoding="utf-8"))
            for proj in claude_cfg.get("projects", {}).values():
                token = proj.get("mcpServers", {}).get("github", {}).get("env", {}).get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
                if token:
                    break
        except Exception:
            pass

    trending_data, topics_data, awesome_data = [], [], []

    if run_all or args.trending:
        print("\n" + "=" * 55)
        print("  📈  维度一：编程语言热度（GitHub Trending）")
        print("=" * 55)

    if run_all or args.topics:
        print("=" * 55)
        print("  📊 维度二：技术赛道体量（搜索统计）")
        print("=" * 55)

    if run_all or args.awesome:
        print("=" * 55)
        print("  🆕 维度三：新兴领域（Awesome 发现）")
        print("=" * 55)

    # ── 并行采集（三个爬虫互不依赖） ──
    if run_all:
        with ThreadPoolExecutor(max_workers=3) as ex:
            jobs = {}
            jobs["trending"] = ex.submit(TrendingCrawler(token=token).crawl)
            jobs["topics"]   = ex.submit(TopicsCrawler(rate_limit=10.0, token=token).crawl)
            jobs["awesome"]  = ex.submit(AwesomeDiscoverer(rate_limit=10.0, token=token).crawl)
            trending_data = jobs["trending"].result()
            topics_data   = jobs["topics"].result()
            awesome_data  = jobs["awesome"].result()
        print(f"\n  → Trending: {len(trending_data)} | Topics: {sum(1 for d in topics_data if d['repo_count']>0)}/{len(topics_data)} | Awesome: {len(awesome_data)}")
    else:
        if args.trending:
            trending_data = TrendingCrawler(token=token).crawl()
            print(f"  → {len(trending_data)} 条\n")
        if args.topics:
            topics_data = TopicsCrawler(rate_limit=10.0, token=token).crawl()
            ok = sum(1 for d in topics_data if d["repo_count"] > 0)
            print(f"  → {ok}/{len(topics_data)} 个主题成功\n")
        if args.awesome:
            awesome_data = AwesomeDiscoverer(rate_limit=10.0, token=token).crawl()
            print(f"  → {len(awesome_data)} 个仓库\n")

    # ── 汇总分析 ──
    lang_heat  = analyze_language_heat(trending_data) if trending_data else {}
    topic_size = analyze_topic_size(topics_data) if topics_data else {}
    rising     = analyze_rising_domains(awesome_data) if awesome_data else []

    # ── 去重 ──
    top_trending = _dedup_top(trending_data, "repo", "stars_period", 20)
    top_awesome  = _dedup_top(awesome_data, "name", "stars", 20)

    # ── 存 data JSON（原子写入） ──
    os.makedirs("output", exist_ok=True)
    data_pkg = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lang_heat": lang_heat,
        "topic_size": {k: {"total_repos": v["total_repos"], "keywords": v["keywords"]}
                       for k, v in topic_size.items()},
        "rising_domains": rising,
        "top_trending": top_trending,
        "top_awesome": top_awesome,
    }
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data_pkg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)  # 原子 rename

    # ── 保存快照 ──
    if args.save or run_all:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        to_json(data_pkg, f"{SNAPSHOT_DIR}/data_{ts}.json")

    # ── 终端摘要 ──
    print("=" * 55)
    print(f"  📦 数据已保存: {DATA_FILE}")
    if args.save or run_all:
        print(f"  📁 快照已保存: {SNAPSHOT_DIR}/")
    print("=" * 55)

    if lang_heat:
        print("\n  语言热度 Top 5:")
        for lang, s in list(lang_heat.items())[:5]:
            print(f"    {lang:<12} {s['repo_count']} repos | +{s['total_new_stars']:,} ☆ | 均 {s['avg_new_stars']:,}")

    print(f"""
  ┌──────────────────────────────────────────────┐
  │  下一步：在 Claude Code 中说：                 │
  │                                              │
  │  "分析 {DATA_FILE} 的趋势数据"                │
  │                                              │
  │  然后运行: python main.py --report --view     │
  └──────────────────────────────────────────────┘
""")


# ═══════════════════════════════════════════════════════════════
#  报告模式
# ═══════════════════════════════════════════════════════════════

def report_mode(args):
    if not os.path.exists(DATA_FILE):
        print(f"❌ 找不到 {DATA_FILE}，请先运行 python main.py 采集数据")
        sys.exit(1)

    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    # ── 读 AI 洞察 ──
    insights = []
    if os.path.exists(INSIGHTS_FILE):
        with open(INSIGHTS_FILE, encoding="utf-8") as f:
            insights = json.load(f).get("insights", [])
    if not insights:
        insights = ["💡 AI 洞察尚未生成。在 Claude Code 中说：分析 output/latest_data.json"]

    # ── 历史对比 ──
    prev_data = _load_previous_snapshot()
    changes = _compute_changes(data, prev_data) if prev_data else None

    path = build_html_report(data, insights, changes)
    print(f"✅ 报告: {path}")

    if args.view:
        webbrowser.open(f"file:///{path.replace(os.sep, '/')}")
        print("🌐 浏览器已打开")
    return path


def _load_previous_snapshot() -> dict | None:
    """加载上一次的历史快照（跳过最当前这一次）。"""
    files = sorted(globmod.glob(f"{SNAPSHOT_DIR}/data_*.json"), reverse=True)
    if len(files) < 2:
        return None
    # files[0] 是当前采集的快照，取 files[1] 即上一次
    for f in files[1:]:
        try:
            with open(f, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            continue
    return None


def _compute_changes(curr: dict, prev: dict) -> dict | None:
    """对比两次快照，计算排名变化。"""
    if not prev:
        return None

    changes = {}

    # 语言热度排名变化
    curr_langs = list(curr.get("lang_heat", {}).keys())
    prev_langs = list(prev.get("lang_heat", {}).keys())
    lang_changes = {}
    for i, lang in enumerate(curr_langs):
        prev_rank = prev_langs.index(lang) + 1 if lang in prev_langs else None
        curr_rank = i + 1
        delta = prev_rank - curr_rank if prev_rank else 0  # 正=上升 负=下降
        lang_changes[lang] = {"rank": curr_rank, "prev_rank": prev_rank, "delta": delta}
    changes["langs"] = lang_changes

    # 赛道大小变化
    curr_topics = curr.get("topic_size", {})
    prev_topics = prev.get("topic_size", {})
    topic_deltas = {}
    for cat, info in curr_topics.items():
        prev_count = prev_topics.get(cat, {}).get("total_repos", 0)
        curr_count = info.get("total_repos", 0)
        if prev_count:
            pct = (curr_count - prev_count) / prev_count * 100
            topic_deltas[cat] = round(pct, 1)
    changes["topics"] = topic_deltas

    changes["prev_timestamp"] = prev.get("timestamp", "未知")
    return changes


# ═══════════════════════════════════════════════════════════════
#  HTML 报告
# ═══════════════════════════════════════════════════════════════

def build_html_report(data: dict, insights: list[str], changes: dict | None = None) -> str:
    path = auto_filename("github_trends")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lang_heat    = data.get("lang_heat", {})
    topic_size   = data.get("topic_size", {})
    rising       = data.get("rising_domains", [])
    top_trending = data.get("top_trending", [])
    top_awesome  = data.get("top_awesome", [])

    # ── 语言热度（带排名变化箭头） ──
    lang_rows = ""
    for lang, s in lang_heat.items():
        arrow = ""
        if changes and lang in changes.get("langs", {}):
            d = changes["langs"][lang]
            if d["delta"] > 0:
                arrow = f' <span style="color:#3fb950;">↑{d["delta"]}</span>'
            elif d["delta"] < 0:
                arrow = f' <span style="color:#f85149;">↓{abs(d["delta"])}</span>'
            elif d["prev_rank"] is None:
                arrow = ' <span style="color:#d2a8ff;">新</span>'
        lang_rows += (
            f"<tr><td>{esc(lang)}{arrow}</td><td>{s['repo_count']}</td>"
            f"<td>{s['total_new_stars']:,}</td><td>{s['avg_new_stars']:,}</td></tr>"
        )

    # ── 赛道体量 ──
    topic_rows = ""
    for cat, s in topic_size.items():
        delta_str = ""
        if changes and cat in changes.get("topics", {}):
            pct = changes["topics"][cat]
            if abs(pct) > 0.01:  # 增长率接近 0 不显示
                color = "#3fb950" if pct > 0 else "#f85149"
                delta_str = f' <span style="color:{color};font-size:11px;">({pct:+.1f}%)</span>'
        topic_rows += (
            f"<tr><td>{esc(cat)}</td><td>{s['total_repos']:,}{delta_str}</td>"
            f"<td>{esc(', '.join(k['kw'] for k in s['keywords'][:3]))}</td></tr>"
        )

    # ── 新兴领域 ──
    has_desc = any(d.get('description','').strip() for d in rising[:15])
    has_spd  = any(d.get('stars_per_day',0) for d in rising[:15])
    if not rising:
        rising_rows = '<tr><td colspan="4" style="color:#8b949e;">暂无数据（Awesome 模块限流或未运行）</td></tr>'
        rising_headers = "<th>仓库</th><th>描述</th><th>⭐</th><th>日均</th>"
    else:
        cols = ["<th>仓库</th>"]
        if has_desc: cols.append("<th>描述</th>")
        cols.append("<th>⭐</th>")
        if has_spd: cols.append("<th>日均</th>")
        rising_headers = "".join(cols)
        rising_rows = ""
        for d in rising[:15]:
            name = esc(d.get('name',''))
            url  = esc(d.get('url',''))
            desc = esc(d.get('description',''))[:100] if has_desc else ""
            stars = f"{d.get('stars',0):,}"
            spd   = f"{d.get('stars_per_day',0)}/天" if has_spd else ""
            rising_rows += (
                f"<tr><td><a href='{url}' target='_blank'>{name}</a></td>"
                + (f"<td>{desc}</td>" if has_desc else "")
                + f"<td>{stars}</td>"
                + (f"<td>{spd}</td>" if has_spd else "")
                + "</tr>"
            )

    # ── Trending Top（已去重） ──
    trending_rows = "".join(
        f"<tr><td><a href='{esc(r.get('url',''))}' target='_blank'>{esc(r.get('repo',''))}</a></td>"
        f"<td>{esc(r.get('description',''))[:120]}</td>"
        f"<td>{esc(r.get('language',''))}</td><td>+{r.get('stars_period',0):,}</td></tr>"
        for r in top_trending[:15]
    )

    # ── AI 洞察 ──
    insights_html = "".join(f"<li>{esc(line)}</li>" for line in insights)

    # ── 历史对比信息（同一天不显示） ──
    compare_html = ""
    if changes:
        curr_ts = data.get('timestamp','')[:10]  # YYYY-MM-DD
        prev_ts = changes.get("prev_timestamp","")[:10]
        if prev_ts and prev_ts != curr_ts:
            compare_html = (
                f'<p style="color:#8b949e;font-size:12px;margin-bottom:16px;">'
                f'📅 上次采集: {changes["prev_timestamp"]} &nbsp;|&nbsp; ↑↓ 表示排名变化</p>'
            )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GitHub 技术趋势报告 — {now}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,"Microsoft YaHei",sans-serif; background:#0d1117; color:#c9d1d9; padding:24px 16px; }}
  .wrap {{ max-width:1100px; margin:0 auto; }}
  h1 {{ color:#58a6ff; font-size:24px; margin-bottom:4px; }}
  h2 {{ color:#f0883e; font-size:18px; margin:28px 0 12px; border-bottom:1px solid #21262d; padding-bottom:8px; }}
  .meta {{ color:#8b949e; font-size:12px; margin-bottom:24px; }}
  .card {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; margin-bottom:16px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th {{ background:#21262d; color:#8b949e; padding:8px 10px; text-align:left; font-size:12px; }}
  td {{ padding:7px 10px; border-bottom:1px solid #21262d; }}
  tr:hover td {{ background:#1c2129; }}
  a {{ color:#58a6ff; text-decoration:none; }} a:hover {{ text-decoration:underline; }}
  .bar {{ background:#21262d; border-radius:4px; height:14px; overflow:hidden; }}
  .bar-fill {{ background:linear-gradient(90deg,#238636,#3fb950); height:100%; border-radius:4px; }}
  .insights {{ background:#161b22; border:1px solid #30363d; border-left:4px solid #d2a8ff; border-radius:8px; padding:16px 20px; margin-bottom:24px; }}
  .insights li {{ margin:6px 0; line-height:1.7; font-size:14px; }}
  .insights h3 {{ color:#d2a8ff; margin-top:0; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  @media (max-width:800px) {{ .grid {{ grid-template-columns:1fr; }} }}
  footer {{ margin-top:32px; text-align:center; color:#484f58; font-size:11px; }}
  .ai-badge {{ display:inline-block; background:linear-gradient(135deg,#6e40c9,#d2a8ff); color:#fff; font-size:11px;
               padding:2px 10px; border-radius:10px; margin-left:8px; }}
  .history-badge {{ display:inline-block; background:#1f2a37; color:#8b949e; font-size:11px;
                    padding:2px 8px; border-radius:10px; margin-left:4px; }}
</style>
</head>
<body>
<div class="wrap">
<h1>🚀 GitHub 技术趋势报告</h1>
<p class="meta">
  采集: {data.get('timestamp','')} &nbsp;|&nbsp; 报告: {now}
  <span class="ai-badge">🤖 AI 分析</span>
  {f'<span class="history-badge">📅 对比: {changes["prev_timestamp"]}</span>' if (changes and changes.get("prev_timestamp","")[:10] != data.get('timestamp','')[:10]) else ''}
</p>

{compare_html}

<div class="insights">
  <h3>🧠 AI 趋势洞察 & 建议</h3>
  <ul style="list-style:none;padding-left:0;">{insights_html}</ul>
</div>

<h2>📈 编程语言热度排名</h2>
<div class="card">
  <table><thead><tr><th>语言</th><th>上榜</th><th>新增 Star</th><th>均值</th></tr></thead><tbody>{lang_rows}</tbody></table>
  <p style="font-size:11px;color:#8b949e;margin-top:8px;">* GitHub Daily + Weekly Trending 去重后排名 &nbsp;|&nbsp; ↑↓ 相对上次变化</p>
</div>

<h2>📊 技术赛道体量</h2>
<div class="card">
  <table><thead><tr><th>赛道</th><th>仓库数</th><th>代表关键词</th></tr></thead><tbody>{topic_rows}</tbody></table>
</div>

<div class="grid">
<div>
<h2>🔥 本周最热 Top 15</h2>
<div class="card" style="overflow-x:auto;">
  <table><thead><tr><th>仓库</th><th>描述</th><th>语言</th><th>+Star</th></tr></thead><tbody>{trending_rows}</tbody></table>
</div>
</div>
<div>
<h2>🆕 新兴领域增速榜</h2>
<div class="card" style="overflow-x:auto;">
  <table><thead><tr>{rising_headers}</tr></thead><tbody>{rising_rows}</tbody></table>
</div>
</div>
</div>


<footer>GitHub 技术趋势探测器 © 2026 — 数据: github.com  洞察: Claude AI</footer>
</div>
</body>
</html>"""

    os.makedirs("output", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.abspath(path)


def esc(val):
    if val is None: return ""
    return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    crash_file = "output/CRASH.txt"
    try:
        if args.report:
            report_mode(args)
        else:
            collect_mode(args)
        # 采集/报告成功后清除上次崩溃标记
        if os.path.exists(crash_file):
            os.remove(crash_file)
    except Exception:
        os.makedirs("output", exist_ok=True)
        with open(crash_file, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now()}\n{traceback.format_exc()}")
        print(f"\n❌ 写入 {crash_file} — 请检查并手动补跑", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
