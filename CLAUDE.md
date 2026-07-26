# github-trends · 工作室

## Commands
- 运行: `python main.py --report --view`
- 自动采集: `auto_run.bat`（周日触发）

## Stack
- Python 3 + requests + BeautifulSoup
- 输出: `output/insights.json` + HTML 报告

## 代理
- Clash 7897（首选）/ UniClash 7993（备用）

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

**-1. 先读 PROGRESS + 上周 insights**
`Desktop/Last30Days/PROGRESS.md` + `Desktop/github-trends/output/insights.json` ——确认当前轮转周、上次分析结论、季度深度是否到期。**如果是 W2 或 W4：今天有覆盖检查，情报日结束后开 Explore Agent 查。** 写本周 insights 时显式引用上周结论（续写/修正/推翻），保持跨周连贯。

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
W2 过半 + W4 完整周期结束时，开 Explore Agent 做覆盖检查（不能自己检查）：
- 四周 insights.json 结论是否连贯，有无前后矛盾？
- 三连问解读角度是否单一——是否每次都落在"你的路线是对的"？反向压力测试（什么情况下推荐会错？）做了吗？
- 有没有应该关心但四周都没覆盖到的盲点？
- 下周期方向需要倾斜吗？同一类误判不超过一次。

**固定盲点扫描项（每次覆盖检查必过）：**
- Rust vs C++ 相对增速——Rust 是否在系统性侵蚀 C++ 地盘？
- Java 冰点假设——是否用实际就业数据验证过，还是每次都在重复同一句？
- 国产工具→就业——工具成熟度变化是否反映了面试市场对技能要求的变化？
- 雇主/HR 视角——分析是站在开发者侧还是用人侧？
- 爬虫数据质量——Topics 是否有 -1 采集失败？docker 是否仍然异常 5M？数据异常是否已被标记而非当真实数据写入 insights？

**跨周写作规则（每期执行）：**
- 三连问最后一条改为"什么情况下本周核心推荐是错的？"——强制反向压力测试，一句话即可。
- 引用标签统一：同轮引用用"上周 W{N} 回顾"，跨轮引用用"上月 W{N} 回顾"。
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
| 2 | 就业市场 | `CS graduate job market AI coding entry level 2026` · **加雇主/HR 视角：简历筛选第一轮看什么？** |
| 3 | 技术方向 | `C++ embedded systems autonomous driving computer vision AI compiler infrastructure hiring` |
| 4 | 开源模型 | `DeepSeek open source models vs proprietary frontier 2026` |

B站/知乎搜索词见 `Desktop/Last30Days/CLAUDE.md`（临时研究窗口执行）。

