# 🚀 GitHub 技术趋势探测器

从 GitHub 抓取四维数据，AI 分析技术趋势，生成可视化 HTML 报告。

## 快速开始

```bash
# 1. 采集数据（需要梯子，约 5-8 分钟）
python main.py

# 2. 把 output/latest_data.json 发给 Claude，让它分析
#    在 Claude Code 里说："分析 output/latest_data.json"

# 3. 生成报告
python main.py --report --view
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `python main.py` | 完整采集（Trending + Topics + Awesome + 校招） |
| `python main.py --trending` | 只看 Trending（1 分钟） |
| `python main.py --report --view` | 从已有数据生成报告 |
| `python main.py --save` | 采集并保存带时间戳的快照 |

## 报告内容

- 📈 编程语言热度排名（按 star 增量）
- 📊 技术赛道体量对比（AI / 前端 / 后端 / 云原生…）
- 🔥 本周最热项目 Top 15
- 🆕 新兴领域增速榜
- 🧠 AI 趋势洞察 & 个人建议

## 数据维度

| 维度 | 来源 | 爬虫 |
|------|------|------|
| 语言热度 | `github.com/trending` | `crawlers/trending.py` |
| 赛道体量 | `github.com/search` 结果数 | `crawlers/topics.py` |
| 新兴领域 | Awesome-* 仓库发现 | `crawlers/awesome.py` |

## 依赖

```bash
pip install requests beautifulsoup4 lxml
```

## 项目结构

```
github-trends/
├── crawlers/           # 四个爬虫 + 基类
├── analyzer.py         # 数据分析（排名/汇总）
├── store.py            # JSON/HTML 输出
├── main.py             # CLI 入口
├── output/             # 报告和数据
│   ├── latest_data.json    # 最新采集数据
│   ├── insights.json       # AI 洞察（Claude 生成）
│   └── snapshots/          # 历史快照
└── requirements.txt
```
