# GitHub 趋势探测器 · 项目进度

## 当前状态
- 版本：v2.0
- 数据源：GitHub Trending / Topics / Awesome
- 自动化：Windows 任务计划 `GitHub-Trends-Weekly` —— 周日 10:00 + **每次登录**（幂等闸门保证一周最多采一次）
- 部署：本地 Windows + GitHub 备份

## 功能列表

| 功能 | 状态 | 加入时间 |
|------|------|---------|
| GitHub Trending 爬虫 | ✅ | 2026.6.5 |
| Topics 赛道体量 | ✅ | 2026.6.5 |
| Awesome 新兴领域 | ✅ | 2026.6.5 |
| Awesome 增速榜修复（created: 限定 + 星速排序） | ✅ | 2026.7.12 |
| Token 代理自动读取 | ✅ | 2026.6.9 |
| 中文 HTML 报告 | ✅ | 2026.6.9 |
| AI 趋势洞察 | ✅ | 2026.6.9 |
| 历史快照 + 对比 | ✅ | 2026.6.9 |
| Windows 自动任务 | ✅ | 2026.6.9 |
| 代理重试机制 | ✅ | 2026.6.15 |
| 双端口代理检测 | ✅ | 2026.6.18 |
| V2EX 社区爬虫（含详情+节点过滤） | ❌ 已移除 | 2026.6.19 → 2026.7.5 移除 |
| 报告智能隐藏空列 | ✅ | 2026.6.21 |
| 描述截断优化 (80→120) | ✅ | 2026.6.21 |
| 增长率 <0.01% 隐藏 | ✅ | 2026.6.21 |
| 并行采集（ThreadPoolExecutor） | ✅ | 2026.7.2 |
| 原子写入（.tmp → os.replace） | ✅ | 2026.7.2 |
| CRASH 增强（Python 异常写入 CRASH.txt） | ✅ | 2026.7.2 |
| 快照加载修复（跳过当前快照） | ✅ | 2026.7.2 |
| 429 Retry-After 处理 | ✅ | 2026.7.2 |
| 日志旋转（保留最近 300 行） | ✅ | 2026.7.2 |
| GBK emoji 编码修复 | ✅ | 2026.7.12 |
| auto_run.bat TCP 端口检测（替代 curl HTTPS） | ✅ | 2026.7.12 |
| Trending rate_limit 对齐 10s（防止并行时超额） | ✅ | 2026.8.5 |
| 代理预检（爬虫启动前测 GitHub 连通性，不通直接退出） | ✅ | 2026.8.5 |
| 重试+超时优化（max_retries 3→1，timeout 8/25→5/15，SSL不重试秒切备代理） | ✅ | 2026.8.12 |
| Topics/Awesome 改 API 搜索（token 真正生效，限流 30次/分，修掉 token 从没生效的历史 bug） | ✅ | 2026.8.12 |
| SSL 超时拆分（connect=8s read=25s，防止 SSL EOF 卡死） | ✅ | 2026.7.26 |
| Topics 采集失败标记（-1 替代 0，避免限流空结果被当真实数据） | ✅ | 2026.7.26 |
| 报告关键词显示具体数量 + 采集失败红色标记 | ✅ | 2026.7.26 |
| Python 层代理 fallback（主代理失败自动切备用，ConnectionError/SSLError/ConnectTimeout 触发） | ✅ | 2026.8.2 |
| f-string `\"` 兼容修复（Python 3.12+ 已弃用） | ✅ | 2026.8.2 |
| 隐藏窗口启动（wscript+VBS 替代 cmd，杜绝"误关窗口杀爬虫"） | ✅ | 2026.9.27 |
| 运行标记 `output/RUNNING.lock`（残留 = 上次没跑完就被杀） | ✅ | 2026.9.27 |
| 幂等闸门（本周已有有效快照则跳过采集；`force` 参数强制重跑） | ✅ | 2026.9.27 |
| 数据完整性校验（Trending 全空 / Topics 失败≥50% → 拒绝写快照） | ✅ | 2026.9.27 |
| bat 检查 python 退出码（原先失败也写 "Done at" 并退 0） | ✅ | 2026.9.27 |
| 失败自动重试（bat 内 3 次 + 计划任务 RestartOnFailure） | ✅ | 2026.9.27 |
| 登录触发器（开机/登录自动补跑漏掉的周，闸门保证不重复烧限额） | ✅ | 2026.9.27 |
| 快照原子写（`store.to_json` 原先直接截断写） | ✅ | 2026.9.27 |
| 修 CRASH.txt 假绿（`--report` 不再抹掉 collect 留下的崩溃记录） | ✅ | 2026.9.27 |
| 修日志轮转（同文件读写导致 702 行从不裁剪 → 改为超 512KB 改名轮转） | ✅ | 2026.9.27 |
| 日志时间戳 ASCII 化（原先 GBK 星期名导致整份日志无法用一种编码读） | ✅ | 2026.9.27 |
| Windows TaskScheduler 诊断日志启用（下次被杀能查出"谁杀的"） | ✅ | 2026.9.27 |

## 每周运行记录

| 周 | 日期 | 状态 | 快照 | 备注 |
|----|------|------|------|------|
| W1 | 6.9 | ✅ 手动 | 1份 | 首次采集 |
| W2 | 6.15 | ⚠️ 手动补跑 | 1份 | 自动任务首次失败 (Clash SSL)，手动补全 |
| W3 | 6.21 | ✅ auto | 1份 | 自动采集正常 |
| W4 | 6.28 | ✅ 手动（提前） | 1份 | 情报日提前到凌晨，6.30 auto 补跑 |
| W5 | 7.5 | ✅ auto | 1份 | OK |
| W6 | 7.12 | ✅ auto | 1份 | --report GBK 崩溃手动补跑，已修 |
| W7 | 7.19 | ✅ auto | 1份 | OK |
| W8 | 7.26 | ⚠️ 手动补跑 | 1份 | 自动任务 SSL 卡死，手动补跑。已修：timeout (8,25) |
| W9 | 8.3 | ⚠️ 手动补跑 | 1份 | auto 8.2 因 f-string 语法错误崩溃，8.3 手动补跑。已修：f-string 兼容 |
| W10 | 8.12 | ⚠️ 手动补跑 | 1份 | auto 8.10 因语法错误崩溃（代理预检+三路并行+429），手动补跑。已修：Topics/Awesome 改 API 搜索，token 真正生效 |
| W11 | 8.16 | ✅ auto | 1份 | 自动采集正常（8.16 周日 19:53 跑通） |
| W12 | 8.23 | ✅ auto | 1份 | 自动采集正常（8.23 周日 14:17 跑通） |
| W13 | 8.30 | ✅ auto | 1份 | 自动采集正常（8.30 周日 12:25 跑通）；情报日分析 9.3 补做（W3 技术方向） |
| W14 | 9.6 | ✅ auto | 1份 | 自动采集正常（9.6 周日 11:42 跑通）；情报日分析 9.9 补做（W4 开源模型） |
| W14b | 9.10 | ✅ 补做 | 0份 | 新面孔 diff 扫描补分析：40 条全量 vs 8/23+8/30 → 17 新/7 已析 → 10 条补齐（标记 4：patent-disclosure-skill/openclaude/OpenMAIC/video-use；背景级 5），落盘 insights_W4_20260906_supplement.json；情报日流程新增 1.5 步骤（快照全量 diff，HTML Top15 会漏） |
| W15 | 9.13 | ❌ 未完成 | 0份 | 11:22 开始采集，11:24 被杀（爬到 90 秒）。**无快照、无 CRASH.txt、日志无错误**——静默丢失一周 |
| W16 | 9.20 | ✅ auto | 1份 | 自动采集正常（16:22 跑通，3m05s） |
| W17 | 9.27 | ⚠️ 手动补跑 | 1份 | 自动任务 13:38 启动后 **2 秒**被同一原因杀掉；14:05 手动补跑成功。当日定位根因并完成爬虫加固（见下方"2026.9.27 加固"） |
| W17b | 9.29 | ✅ auto | 1份 | 登录触发器补跑（18:41）。⚠️ 注意代码的「周」从**周一**算：9/29 属 9/28–10/4 那一周，与 9/27（属 9/21–9/27）**跨周**；两榜 15/20 重合、Awesome 全同，差异极小 |

### 情报日补做记录（2026.10.3）

爬虫采集一直正常，缺的是情报日的「社区脉搏（/last30days + B站 + 知乎 + 政策）+ 三连问分析」这一环。10/3 一次性补齐三期：

| 期 | 方向 | 补做内容 | insights 文件 |
|----|------|---------|--------------|
| 9/13 W1 | 工具生态 | ⚠️ **快照永久丢失**（静默丢失那期），只补社区内容，仓库面缺位由 9/20 快照 diff 补回 | `insights_W1_20260913.json` |
| 9/20 W2 | 就业市场 | 完整补做（含 HR 筛选 / 实习内推 / Java 验证 / 国产工具→JD 四个专项） | `insights_W2_20260920.json` |
| 9/27 W3 | 技术方向 | 完整补做（含 AI 生成系统代码质量的证伪条件核查，拿到反向证据） | `insights_W3_20260927.json` |

**两条待办备注：**
- **9/13 (W15) 的快照永久缺失**，该期仓库面（Trending/Awesome）不可补，已在 insights 里注明；查历史时别把它当「数据缺失」之外的含义。
- **9/20 (W16) 的覆盖检查推迟**——按流程 W2 结束应开子代理做执行 + 编排覆盖检查，本次未做，**合并到 10/4 与 W4 的覆盖检查一并执行**（不要漏）。

> 补做口径说明：社区内容无法回溯到当时的 30 天窗口（现在采到的是 9/3–10/3），三期分别用各自的**不同搜索词**采集，主体内容不冲突；个别跨期重复的条目已在靠后的期次里备注。

## 数据快照

```
output/snapshots/
  data_20260609_165206.json  (6.9 W1)
  data_20260615_110309.json  (6.15 W2)
  data_20260621_132047.json  (6.21 W3)
  data_20260628_003129.json  (6.28 W4)
  data_20260630_151532.json  (6.30 W5)
  data_20260705_125109.json  (7.5)
  data_20260712_133037.json  (7.12)
  data_20260719_131844.json  (7.19)
  data_20260726_142033.json  (7.26)
  data_20260803_030202.json  (8.3)
  data_20260812_230243.json  (8.12)
  data_20260816_195301.json  (8.16)
  data_20260823_141736.json  (8.23)
  data_20260830_122530.json  (8.30)
  data_20260906_114203.json  (9.6 W14)
  data_20260920_162524.json  (9.20 W16)
  data_20260927_140509.json  (9.27 W17)
  data_20260929_184101.json  (9.29 W17b，属 9/28–10/4 那周)
```

> **9.13（W15）没有快照** —— 那次被中途杀掉。查历史时别把它当"数据缺失"，
> 它是"那周真的没采到"。`python main.py --check-fresh` 对那一周会返回非 0。

## 维护备忘

- 代理挂了 → 首次尝试轮询 2.5h、重试轮询 30min；Python 层自动切备用（运行阶段）
- 代理端口：7897（Clash Verge 首选）→ 7993（UniClash 备用），Python 通过 HTTP_PROXY_BACKUP 知道备用地址

### 计划任务配置（重装/回退时照此重建）

启动链路：**任务计划 → `wscript.exe //B run_hidden.vbs` → `cmd /c auto_run.bat`**。

⚠️ **不要把它改回 `cmd.exe /c auto_run.bat`** —— 那样会弹一个可见的控制台窗口，
用户误关窗口 = 进程收到 CTRL_CLOSE = `0xC000013A`，2026.9.13 和 9.27 两次丢失就是这么来的。
`run_hidden.vbs` 里的 `Run(..., 0, True)` 三个参数缺一不可：`0` 是隐藏窗口，`True` 是等子进程
返回（**写成 `False` 会让 wscript 立刻退 0，失败重启就永远不会触发**）。

| 设置 | 值 | 为什么 |
|---|---|---|
| Action | `wscript.exe //B "…\run_hidden.vbs"` | 隐藏窗口 + 透传退出码 |
| Principal | `InteractiveToken` / `jd` | **不能改**：Clash 代理是用户会话进程 |
| Triggers | 周日 10:00 + 登录时（Delay PT2M） | 登录触发器负责补漏 |
| MultipleInstances | `IgnoreNew` | 防叠加 |
| StartWhenAvailable | `True` | 错过就补 |
| RestartOnFailure | Count 3 / Interval PT10M | 失败自动重试 |
| ExecutionTimeLimit | `PT6H` | 最坏耗时约 3.3h，留 50% 余量；原 PT72H 会让卡死的实例堵死后续触发器 |

原始 XML 备份：项目根目录 `scheduled_task_backup_20260927.xml`（改动前）。
**改这个任务用 `Set-ScheduledTask` 对象模型，不要直接编辑 XML**——`ExecutionTimeLimit`
从 CimInstance 直接赋值会被序列化成 `06:00:00` 而非 `PT6H`，报 `0x80041318` 被拒。
正确做法是用 `New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 6)` 新建。

### 排查入口

- 状态三判据：`output/RUNNING.lock` 残留（被中途杀了）/ `python main.py --check-fresh`（本周有无有效快照）/ `output/CRASH.txt`（崩溃与中断记录，三种前缀含义见 CLAUDE.md 第 0 步）
- 日志：`output/auto_log.txt`（当前）+ `auto_log.txt.1`（上一次，超 512KB 时轮转）
- **谁杀了任务**：TaskScheduler 操作日志已于 2026.9.27 启用 →
  `Get-WinEvent -LogName 'Microsoft-Windows-TaskScheduler/Operational' | Where-Object Message -like '*GitHub-Trends*'`
- 手动强制补跑：`cmd /c "C:\Users\jd\Desktop\github-trends\auto_run.bat" force`
- 端到端验证脚手架（不烧 GitHub 限额）：`output/_smoke/`

- 周日晚上来工作室 → 情报日做三连问
- Token 用量：`npx @yurukusa/cc-context`，缓存 < 90% 提醒
- 模型/链路：**不写死**（会烂），现查 `echo $ANTHROPIC_BASE_URL` + `~/.claude/settings.json`
