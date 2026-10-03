# github-trends · 工作室 · 角色卡

> 🚀 **唤醒：周日 10:00 后，无论第一句话是什么，先进情报日。先读本文件 + `Desktop/github-trends/PROGRESS.md` + 上周 insights + 快照，读完才算初始化。**

| 字段 | 内容 |
|---|---|
| 身份 | 情报日工作室（单窗口）：**采集 + 分析一条龙**——先派 Flash 子代理采集，再 Pro 主会话做三连问 + 反向压力测试 + 写 insights |
| 档位 | **Pro 主会话**（分析要推理）；**采集派 Flash 子代理**（量大机械省钱） |
| 启动必读 | ① 本文件 ② `Desktop/github-trends/PROGRESS.md` ③ 上周 insights.json + 快照 |
| 铁律 | 采集用 Flash 子代理（读 `Desktop/Last30Days/CLAUDE.md`），分析用 Pro 主会话；W2/W4 覆盖检查开子代理（不能自己查）；每次收尾更新两个 PROGRESS + 备份 insights |
| 收工 | 情报日收尾自检清单（两个 PROGRESS + insights 备份 + HTML + push） |

## Commands
- 运行: `python main.py --report --view`
- 自动采集: `auto_run.bat`（计划任务：周日 10:00 + 每次登录；经 `run_hidden.vbs` 隐藏启动，**不要直接双击或从任务里改回 cmd**）
- 强制补跑: `cmd /c "C:\Users\jd\Desktop\github-trends\auto_run.bat" force`（绕开幂等闸门）
- 状态查询: `python main.py --check-fresh`（rc=0 本周已有有效快照）

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

### 2026.9.27 加固（"静默失败"专项）

**背景：** 9.13 和 9.27 两次采集被中途杀掉（用户误关可见的 cmd 窗口 → `0xC000013A`），
**两次都没留任何痕迹**——没快照、没 CRASH.txt、日志只多一行 `^C`。整套机制失效的根因是
"失败不可见 + 失败不重来"。

| # | 文件 | 改动 |
|---|------|------|
| 19 | `run_hidden.vbs`（新增） | `wscript` + `Run(..., 0, True)` 隐藏启动 bat。**第三个参数必须是 `True`**，写成 `False` 会让 wscript 立刻退 0，失败重启永远不触发 |
| 20 | 计划任务 | Action `cmd.exe /c` → `wscript.exe //B run_hidden.vbs`；加登录触发器（Delay PT2M）+ `RestartOnFailure` 3 次/PT10M；`ExecutionTimeLimit` PT72H→PT6H |
| 21 | `auto_run.bat` | 重写：写/删 `RUNNING.lock`（残留 = 被杀）、`python` 退出码检查（**原先是无效的**，失败也写 "Done at" 退 0）、`--check-fresh` 幂等闸门、失败重试 3 次、日志按 512KB 改名轮转 |
| 22 | `main.py` | 新增 `week_start()` / `validate_data_pkg()` / `week_is_fresh()` / `--check-fresh`；采集后**写盘前**校验，不过就抛错（坏数据不许入库）；**修假绿**——`--report` 不再清除 CRASH.txt |
| 23 | `store.py` | `to_json()` 改原子写（`.tmp` → `os.replace`）。原先是截断写，中途被杀会留下"存在但内容截断"的快照，而幂等闸门正是靠快照判定的 |

**回退检查：**
- 屏幕上又出现黑窗口 → 检查任务 Action 是不是被改回 `cmd.exe /c auto_run.bat`
- 爬虫静默不产出 → `python main.py --check-fresh` 是否卡在"fresh"；再看 `RUNNING.lock` 有无残留
- 采集成"成功"但快照是空的 → 检查 `validate_data_pkg` 是否被绕过
- 任务显示成功但没数据 → 查 TaskScheduler 操作日志的 action result code（VBS 链路静默失败时唯一的证据）

## 规则
- 改爬虫代码 → 自动更新 `PROGRESS.md` 功能清单
- **每次情报日收尾 → 更新 `PROGRESS.md` 每周运行记录 + 数据快照（不等提醒）**
- 推送前 `git status --short --branch` 确认
- 攒到自然节点再 push，不每改一行就推
- 不在 Pro 主会话跑 /last30days——采集派 Flash 子代理做，主会话只接结果做分析

---

## 情报日（周日）

**⚠️ 周日 10:00 后，无论用户第一句话是什么，先进情报日。**

### 情报日流程

**-1. 先读 PROGRESS + 上周 insights + 查快照**
`Desktop/Last30Days/PROGRESS.md` + `Desktop/github-trends/output/insights.json` + `ls output/snapshots/` 最新文件日期——确认当前轮转周、上次分析结论、季度深度是否到期。**如果最新快照 ≤ 2 天 → 爬虫已跑，直接用现有数据，不要重跑浪费限额（2026.9.27 起这条由代码强制：`python main.py --check-fresh` 返回 0 时 `auto_run.bat` 直接跳过采集，跑 `force` 才能绕开）。如果是 W2 或 W4：今天有覆盖检查，情报日结束后开 Explore Agent（显式指定 opus）查。** 写本周 insights 时显式引用上周结论（续写/修正/推翻），保持跨周连贯。

**0. 爬虫状态自检（2026.9.27 改口径）**

```bash
cd ~/Desktop/github-trends
ls output/RUNNING.lock 2>/dev/null      # 有输出 = 🔴 残留锁（上次被中途杀掉）；无输出 = ✅ 干净
python main.py --check-fresh            # rc=0 本周有有效快照 / 非0 本周没采到
cat output/CRASH.txt 2>/dev/null        # 无输出 = 无崩溃记录
```

> 上面三条全是免弹窗命令（`ls` / `cat` 在用户白名单，`python main.py --check-fresh` 于 2026.10.3 加入）。
> 这里不写 `echo` 标签——`echo` 不在白名单，会为了一行提示多弹一次确认；判据含义见下表。

**三条判据缺一不可。原先只看 `CRASH.txt` 会漏报**——2026.9.13 那次就是这么漏的：进程被
Ctrl+C/关窗口杀掉属于 `KeyboardInterrupt`，`main.py` 的 `except Exception` 抓不到，
什么都不写，自检却报「✅ 爬虫正常」。

| 判据 | 异常含义 | 动作 |
|---|---|---|
| `RUNNING.lock` 残留 | 没跑完就被杀 | 看 `auto_log.txt.1` 确认死在哪一步，再决定补跑 |
| `--check-fresh` 非 0 | 本周无有效快照 | **必须补跑**，情报日等不了自动补 |
| `CRASH.txt` | 见下 | 按前缀分类处理 |

`CRASH.txt` 四种内容，含义不同，别一律当"挂了"：

- `INTERRUPTED …` —— 跑一半被杀，但本周数据完好（或已有）。**不必重爬**
- `CRAWL-FAILED … rc=N attempts=3` —— bat 内部重试 3 次仍失败，翻日志找根因
- `PROXY-DEAD …` —— 7897/7993 两个端口都不通
- 首行是时间戳、随后是 Python traceback —— `main.py` 抛异常（含「数据不完整，拒绝写入快照」）

**先让爬虫自己修**：被杀的运行会在下次登录时自动补跑（登录触发器 + 幂等闸门，不用人管）。
只有闸门说「本周无有效快照」且你不想再等一次开机，才手动强制：

```bash
cmd /c "C:\Users\jd\Desktop\github-trends\auto_run.bat" force
```

补跑成功后 `rm output/CRASH.txt`（正常采集也会自动清）。

**1. 派 Flash 子代理采集**（子代理显式指定 Flash，读 `Desktop/Last30Days/CLAUDE.md` + `Desktop/Last30Days/PROGRESS.md` 周轮转表，按本周 W1-W4 方向采）：
- 社区脉搏 `/last30days`（英文引擎，按周轮转表选话题）
- 中文扫描 B站(bili-cli) + 知乎(zhihu-cli，详见 `available-skills` 记忆)
- AI 政策雷达

**1.5 新面孔 diff 扫描（2026.9.10 新增；派采集的同时主会话自己跑，用快照不耗采集额度）**
本周快照 top_trending + top_awesome **全量 40 条** vs 前两周快照并集 → diff 出本周新面孔 → 对照上周 insights（含 supplement）已分析名单 → 剩余的逐个过目，不许只挑主线。产出并入三连问第 1 问与「新兴领域」条目；判定无关的也要一句话留痕（「看过且判无关」才算覆盖）。
- 铁律①：必须用快照全量。HTML 报告每榜只渲染 Top 15（30/40 条），会漏——实例：9/6 awesome-zhuiju-free 排第 18 被截，唯一 Awesome 新面孔在 HTML 上不可见。
- 铁律②：Awesome 是星速榜换血慢（9/6 实测 19/20 老面孔），新面孔主要出自 Trending 周榜——两榜都要 diff，不能只看一边。

**2. 三连问**（工作室提炼进 insights.json）：
  **分析对象 = 信息收集（社区脉搏/中文扫描/AI 政策）+ 具体仓库（Trending/Awesome 榜单里的新工具新项目）。加载本周+上周快照时，只看 Top Trending/Awesome 的具体仓库「有什么新东西进出」，不看语言热度（lang_heat）和赛道体量（topic_size）的排名涨跌——语言数据保留但只当背景，不驱动路线判断（用户的路线由就业/地缘/AI 替代难度决定，不由 GitHub 语言热度决定，2026.8.23 定位调整）。**
  1. 本周最热的 3 个东西（来自信息收集 + 具体仓库），对你意味着什么
  2. 什么在熄火——具体工具/品类的退潮（如某合集停更、某工具失势），不是语言排名涨跌
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
- Java 就业验证——要么用一次真实就业数据（招聘平台 JD/岗位数统计）验证 Java 在国内是否仍是保底岗，要么降级为不追踪项。禁止用「GitHub 冰点」或「知乎建议」这类非就业数据反复打转（语言数据不驱动路线，2026.8.23 定位调整）。
- 国产工具→就业——工具成熟度变化是否落到「面试 JD 技能要求变化」，不只停在「你是安全网」。
- 雇主/HR 视角——W2 必须回答「HR 第一轮筛简历的具体标准是什么」，不许空转。
- 爬虫数据质量——Topics 是否有 -1？数据异常是否被标记而非当真实写入？
- **Agent Skills 泡沫信号**——四周只庆祝增长，必须问「会不会像 prompt 工程一样消退？拥挤度到哪了？」（补一个反向指标，不只追星数）。
- **开源基础设施下沉**——Agent memory / 推理引擎 / 云环境是否在持续出现（W4 首现，后续追踪）。

**跨周写作规则（每期执行）：**
- 三连问最后一条反向压力测试：**必须直接攻击本周核心结论**（如「如果 AI 也能写安全 C++，系统编程还难替代吗」），不许只挂尾部风险（如 16% 封禁概率）。
- 引用标签统一：同轮引用用"上周 W{N} 回顾"，跨轮引用用"上月 W{N} 回顾"。写前核对数字归属哪一周（历史教训：曾把本轮 W2 的仓库星数误归因到上月 W4）。
- 分离"对你"和"对路线"——操作建议和战略修正不要混在同一段。

每次 15 分钟，结果写入 insights.json。写入前先备份：`cp output/insights.json output/insights/insights_W{N}_{YYYYMMDD}.json`。

**情报日收尾自检清单（每周都做，不等提醒）：**
- [ ] Last30Days PROGRESS → 周轮转表已更新
- [ ] github-trends PROGRESS → 运行记录 + 快照列表已更新
- [ ] PROGRESS 表格编辑后 → grep 验证旧行仍在（追加式编辑，不许用新行替换旧行）
- [ ] insights.json → 已备份到 insights/ 目录
- [ ] HTML 报告 → **写完 insights 后重新 `python main.py --report`**（爬虫跑的 HTML 用的是旧 insights，必须重跑再删爬虫那份）
- [ ] 两个仓库 → 已 push
- [ ] 本次会话有无代码改动未记录到 PROGRESS？
- [ ] 爬虫收尾干净：`RUNNING.lock` 无残留 · `CRASH.txt` 已清 · 本周有有效快照（`--check-fresh` = 0）

**注意：执行层面的覆盖（数据缺口、漏扫、来源多样性）和思考质量现在都在一个窗口——执行覆盖由 Flash 采集子代理自查（读 `Desktop/Last30Days/CLAUDE.md` #执行覆盖检查），思考覆盖由 Pro 主会话做（读本文 #编排覆盖检查）。W2/W4 情报日结束后两边各自跑覆盖检查，在下次情报日（W3/W1）三连问前过一遍——有执行缺口优先补，有思考盲点下周期调整方向。同一个错误不超过一次。**

---

## 周轮转速查

| 周 | 方向 | /last30days 搜索词 |
|----|------|-------------------|
| 1 | 工具生态 | 英文: `Claude Code vs Codex vs Cursor vs Hermes` · 中文: `Kimi CLI vs Trae vs WorkBuddy vs Qoder 国产AI编程` · 跨周追踪: Agent Skills 星数变化（VoltAgent 合集+新增项目） |
| 2 | 就业市场 | `CS graduate job market AI coding entry level 2026` · **落到具体标准：HR 第一轮筛简历看什么（不空转）+ 国产工具成熟度 → 面试 JD 技能要求变化** |
| 3 | 技术方向 | `C++ systems programming career backend infrastructure hiring 2026` · 分向: `embedded software jobs` / `autonomous driving robotics C++` / `AI compiler infrastructure` |
| 4 | 开源模型 | `DeepSeek open source models vs proprietary frontier 2026` · 追踪: 参数效率（QwQ 3B激活追平671B类信号）+ 开源基础设施下沉（记忆/推理引擎/云环境） |

B站/知乎搜索词见 `Desktop/Last30Days/CLAUDE.md`（由 Flash 采集子代理执行）。

