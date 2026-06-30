# github-trends

## Commands
- 运行: `python main.py --report --view`
- 自动采集: `auto_run.bat`（周日触发）
- CRASH 检查: `ls output/CRASH.txt`

## Stack
- Python 3 + requests + BeautifulSoup
- 输出: `output/insights.json` + HTML 报告

## CRASH 处理
1. `ls output/CRASH.txt` 存在 → 通知用户「爬虫挂了，手动补跑」
2. 补跑成功 → `rm output/CRASH.txt`

## 规则
- 改爬虫代码 → 自动更新 `PROGRESS.md`
- 推送前 `git status --short --branch` 确认
- 攒到自然节点再 push，不每改一行就推
- 不在工作室窗口跑 /last30days（用临时研究窗口）

## 代理
- Clash 7897（首选）/ UniClash 7993（备用）
