---
name: mindmap-engineering-skill
description: 导图工程 skill 已建成（skills/mindmap-engineering）：导图任务的发现入口+QA
  机器防线两代+更新协议+踩坑全集；做任何导图（新做或更新）前先走它的开工三件事
metadata:
  node_type: memory
  type: project
  created: 2026-09-05
  updated: 2026-09-06
  originSessionId: sess_268cf7a8-07b7-424b-98a6-f66a49332384
---

## 导图工程 skill（2026-09-05 建，栗子令「工程化保证以后导图质量」+「图随主体状态更新」）

- **入口**：`C:/Users/Administrator/.zcode/skills/mindmap-engineering/SKILL.md` + `references/pitfalls.md`（踩坑全集）+ `references/update-protocol.md`（更新六步协议）
- **触发场景**：任何「导图/思维导图/xmind/全景图/结构图」任务——新做、**更新**、验收都算
- **开工三件事**：①读记忆库 xmind-style-baseline + xmind-cli-local-generation ②改标准须栗子点头 ③确认一口气到终形态
- **出图闸门（09-06 升级）**：一代闸（禁标点/**首现即释**【术语首用2跳内须白话定义+命名讨论后置，check_term_locality】/**词条合同**【复述式定义阻断】/**一级预算≤9**/字数/黑话/扇出）+ 二代 QA 七检+2（链条改名、家族canon毒化【阻断】；字母码、变体兄弟、机械组、导览、**类目导览缺失、跨支重复**【报告级须分诊】）
- **QA 模块通用**：任何 [title, kids] 树可 import run_all；已出图 xmind 用 qa_xmind(path) 事后体检 + diff_xmind(old, new) 新旧比对；`python mindmap_qa.py` 跑自测（每个坏例子=一次真实返工标本）
- **冷读者叙事铁律（09-06 栗子定稿，最高验收线）**：见 [[mindmap-narrative-calibration]]——首现即释/词条合同/类目合同/一级预算四闸 + 归类优先更新纪律（禁新开词典支与平行类目）
- **更新协议（CM 图=推进标准时代）**：图是构建产物禁手改 xmind，唯一路径=改数据→重建；构建自动产出时间戳备份（D:/AI/HERMES/Connectome-backups/，可整版回滚）+diff_report.txt（增/删/改名三分类）+build_history.jsonl 台账；闸门与 QA 每次扫全图，标准只紧不松；幂等已验证（同数据重建自动报无更新）
- **交付四件套**：validate 0 错、闸门+QA 全绿、覆盖清单（含 diff 摘要/分诊台账/留白及原因）、冷读者四问抽查

**Why**: 六轮返工的教训证明「人眼把关」不可靠——链条改名静默漏改 15 条、变体兄弟 68 对、字母码 57 处都是通读 7973 节点才抓到的；机器防线+skill 发现入口+记忆库三层沉淀后，同类问题在构建期即被拦截。图升格为推进标准后，更新路径=关键基础设施，手改图/跳过闸门=破坏对账。

**How to apply**: 接到导图任务先调 Skill(mindmap-engineering)；构建类导图直接复用 workspace 流水线范式；更新走六步协议（落盘→改名对账→结构对账→构建→分诊复核→交付）；QA 报告逐条分诊写进覆盖清单，禁静默忽略。关联 [[xmind-style-baseline]] [[cm-closure-mindmap-pipeline]] [[xmind-cli-local-generation]]。
