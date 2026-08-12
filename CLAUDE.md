# github-trends · 工作室

## Commands
- 运行: `python main.py --report --view`
- 自动采集: `auto_run.bat`（周日触发）

## Stack
- Python 3 + requests + BeautifulSoup
- 输出: `output/insights.json` + HTML 报告

## 代理
- Clash 7897（首选）/ UniClash 7993（备用）
- 启动阶段：`auto_run.bat` TCP 端口检测，选通的启动，设 `HTTP_PROXY_BACKUP` 为另一个端口
- 运行阶段：Python 层自动 fallback——主代理 ConnectionError/SSLError/ConnectTimeout → 切备用
- 不用 ReadTimeout 触发切代理（那是 GitHub 慢，换代理没用）

## 修复记录

**⚠️ 如果环境重装或代码回退，按此清单恢复。所有修复在 Windows + Python 3.14 环境。**

### 2026.7.2 重构

| # | 文件 | 修复内容 |
|------|------|------|
| 1 | `crawlers/base.py` | `parse_number()` 统一——trending/topics/awesome 三个文件不再各自实现 |
| 2 | `main.py` | `_dedup_top()`——Trending 和 Awesome 的去重逻辑合并 |
| 3 | `main.py` | 三个爬虫改为 `ThreadPoolExecutor` 并行采集 |
| 4 | `main.py` | CRASH.txt 现在 Python 异常也会写入（try/except/traceback） |
| 5 | `main.py` | 文件写入改为原子操作——先写 `.tmp` 再 `os.replace()` |
| 6 | `main.py` | `_load_previous_snapshot()` 修复——`files[1:]` 跳过当前快照 |
| 7 | `auto_run.bat` | curl 改用 PATH 查找、PROGRESS 追加格式对齐、日志保留最近 300 行 |
| 8 | `crawlers/base.py` | 429 响应使用 GitHub Retry-After 头 |
| 9 | `store.py` | 删除未使用的 `import csv` |

### 2026.7.12 Awesome 新兴领域修复

| # | 文件 | 修复内容 |
|------|------|------|
| 10 | `crawlers/awesome.py` | 重写——搜索从 `stars:>N` 改为 `created:>{365天前}` + `stars:>10`，限定最近一年新建仓库 |
| 11 | `crawlers/awesome.py` | 从搜索页解析相对时间标签（"2 days ago"/"last week"等），估算创建天数 |
| 12 | `crawlers/awesome.py` | 排序从总星数降序→`stars_per_day` 星速降序（`stars / max(days, 1)`），真增速榜 |
| 13 | `crawlers/awesome.py` | 查询精简——`awesome-2025/2026` 年份标签改为直接 `created:` 过滤，年份无关 |
| 14 | `crawlers/awesome.py` | `_make_repo()` 统一封装——stars_per_day/days_old 在构造时计算 |

**回退检查：** 如果 Awesome 榜又显示老面孔（build-your-own-x 等）→ 检查 `CREATED_SINCE` 是否过期；如果星速全为 0 → 检查相对时间解析是否匹配页面新结构。

### 2026.8.2 Python 层代理 fallback

| # | 文件 | 修复内容 |
|------|------|------|
| 15 | `crawlers/base.py` | `get()` 重写为 while 循环——主代理 `max_retries` 次失败后自动切备用，`_is_proxy_error()` 只匹配 ConnectionError/SSLError/ConnectTimeout（不含 ReadTimeout） |
| 16 | `auto_run.bat` | 设 `HTTP_PROXY_BACKUP` 环境变量（主 7897→备 7993，反之亦然），Python 层可读到备用地址 |
| 17 | `crawlers/base.py` | `BaseCrawler.__init__()` 新增 `backup_proxy` 参数 + `HTTP_PROXY_BACKUP` 环境变量读取 |
| 18 | `main.py` | f-string `\"` 转义改为直接 `"`（Python 3.12+ 弃用 f-string 内反斜杠） |

**回退检查：** 如果爬虫代理挂了还在傻等 → 检查 `HTTP_PROXY_BACKUP` 是否已设、`_is_proxy_error()` 异常类型是否匹配。

## 规则
- 改爬虫代码 → 自动更新 `PROGRESS.md` 功能清单
- **每次情报日收尾 → 更新 `PROGRESS.md` 每周运行记录 + 数据快照（不等提醒）**
- 推送前 `git status --short --branch` 确认
- 攒到自然节点再 push，不每改一行就推
- 不在工作室窗口跑 /last30days（用临时研究窗口）

---

## 情报日（周日）

**⚠️ 周日 10:00 后，无论用户第一句话是什么，先进情报日。**

### 情报日流程

**-1. 先读 PROGRESS + 上周 insights + 查快照**
`Desktop/Last30Days/PROGRESS.md` + `Desktop/github-trends/output/insights.json` + `ls output/snapshots/` 最新文件日期——确认当前轮转周、上次分析结论、季度深度是否到期。**如果最新快照 ≤ 2 天 → 爬虫已跑，直接用现有数据，不要重跑浪费限额。如果是 W2 或 W4：今天有覆盖检查，情报日结束后开 Explore Agent（显式指定 opus）查。** 写本周 insights 时显式引用上周结论（续写/修正/推翻），保持跨周连贯。

**0. CRASH 自检**
```bash
ls Desktop/github-trends/output/CRASH.txt 2>/dev/null && echo "🔴 爬虫挂了！" || echo "✅ 爬虫正常"
```
存在 → 立刻告诉用户「爬虫挂了，手动补跑」。补跑成功后 `rm` CRASH.txt。

**1. 派任务给临时研究窗口**
- 社区脉搏 `/last30days`（英文引擎，按周轮转表选话题）
- 中文扫描 B站(bili-cli) + 知乎(zhihu-cli，详见 `available-skills` 记忆)
- AI 政策雷达

**2. 三连问**（工作室提炼进 insights.json）：
  **先加载本周+上周快照做纵向对比（语言排名涨跌、Top 3 进出）。如果是新轮转 W1，额外加载上月 W1 快照——同话题四周跨度，看趋势不只看波动。同时加载新兴领域增速榜（rising_domains）——看 Awesome 合集增速变化。**
  1. 本周最热的 3 个东西，对你意味着什么
  2. 什么在熄火——正常波动还是趋势反转
  3. 你应该关心但还没在雷达上的
  4. **反向压力测试**——什么情况下本周核心推荐是错的？（一句话即可，强制引入非自证视角）

**3. 更新两个 PROGRESS.md**
- `Desktop/Last30Days/PROGRESS.md` → 周轮转表（日期+来源+关键发现+已发工作室）
- `Desktop/github-trends/PROGRESS.md` → 每周运行记录 + 数据快照列表

**4. 编排覆盖检查（W2、W4 结束后触发，开子代理）**
W2 过半 + W4 完整周期结束时，开 Explore Agent（**显式指定 opus**，判断型任务用 Pro，不继承主会话）做覆盖检查（不能自己检查）：
- 四周 insights.json 结论是否连贯，有无前后矛盾？
- 三连问解读角度是否单一——是否每次都落在"你的路线是对的"？反向压力测试（什么情况下推荐会错？）做了吗？
- 有没有应该关心但四周都没覆盖到的盲点？
- 下周期方向需要倾斜吗？同一类误判不超过一次。

**固定盲点扫描项（每次覆盖检查必过）：**
- Rust vs C++ 相对增速——Rust 是否在系统性侵蚀 C++ 地盘？
- Java 冰点假设——要么用一次真实就业数据验证「企业不在 GitHub」假设，要么降级为不追踪项。禁止每轮重复同一句不验证。
- 国产工具→就业——工具成熟度变化是否落到「面试 JD 技能要求变化」，不只停在「你是安全网」。
- 雇主/HR 视角——W2 必须回答「HR 第一轮筛简历的具体标准是什么」，不许空转。
- 爬虫数据质量——Topics 是否有 -1？数据异常是否被标记而非当真实写入？
- **Agent Skills 泡沫信号**——四周只庆祝增长，必须问「会不会像 prompt 工程一样消退？拥挤度到哪了？」（补一个反向指标，不只追星数）。
- **开源基础设施下沉**——Agent memory / 推理引擎 / 云环境是否在持续出现（W4 首现，后续追踪）。

**跨周写作规则（每期执行）：**
- 三连问最后一条反向压力测试：**必须直接攻击本周核心结论**（如「如果 AI 也能写安全 C++，系统编程还难替代吗」），不许只挂尾部风险（如 16% 封禁概率）。
- 引用标签统一：同轮引用用"上周 W{N} 回顾"，跨轮引用用"上月 W{N} 回顾"。写前核对数字归属哪一周（W4 曾把本轮 W2 的 Rust 135% 误归因到上月 W4）。
- 分离"对你"和"对路线"——操作建议和战略修正不要混在同一段。

每次 15 分钟，结果写入 insights.json。写入前先备份：`cp output/insights.json output/insights/insights_W{N}_{YYYYMMDD}.json`。

**情报日收尾自检清单（每周都做，不等提醒）：**
- [ ] Last30Days PROGRESS → 周轮转表已更新
- [ ] github-trends PROGRESS → 运行记录 + 快照列表已更新
- [ ] insights.json → 已备份到 insights/ 目录
- [ ] HTML 报告 → 已生成
- [ ] 两个仓库 → 已 push
- [ ] 本次会话有无代码改动未记录到 PROGRESS？

**注意：执行层面的覆盖（数据缺口、漏扫、来源多样性）由临时研究窗口负责，工作室只管思考质量。W2/W4 情报日结束后两边各自跑覆盖检查，临时窗口结果发给工作室，在下次情报日（W3/W1）三连问前过一遍——有执行缺口优先补，有思考盲点下周期调整方向。同一个错误不超过一次。**

---

## 周轮转速查

| 周 | 方向 | /last30days 搜索词 |
|----|------|-------------------|
| 1 | 工具生态 | 英文: `Claude Code vs Codex vs Cursor vs Hermes` · 中文: `Kimi CLI vs Trae vs WorkBuddy vs Qoder 国产AI编程` · 跨周追踪: Agent Skills 星数变化（VoltAgent 合集+新增项目） |
| 2 | 就业市场 | `CS graduate job market AI coding entry level 2026` · **落到具体标准：HR 第一轮筛简历看什么（不空转）+ 国产工具成熟度 → 面试 JD 技能要求变化** |
| 3 | 技术方向 | `C++ systems programming career backend infrastructure hiring 2026` · 分向: `embedded software jobs` / `autonomous driving robotics C++` / `AI compiler infrastructure` |
| 4 | 开源模型 | `DeepSeek open source models vs proprietary frontier 2026` · 追踪: 参数效率（QwQ 3B激活追平671B类信号）+ 开源基础设施下沉（记忆/推理引擎/云环境） |

B站/知乎搜索词见 `Desktop/Last30Days/CLAUDE.md`（临时研究窗口执行）。

