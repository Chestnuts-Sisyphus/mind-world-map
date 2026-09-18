# 🧠 导图工程（Mindmap Engineering）

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**一套给 AI Agent 用的思维导图工程化 Skill——实战淬炼的产出标准、机器 QA 闸门、数据/构建分离流水线，专治「好看但没人看得懂」的脑图。**

[English](README.md) · [标准正本](SKILL.md) · [踩坑全集](references/pitfalls.md) · [更新协议](references/update-protocol.md) · [版本记录](CHANGELOG.md)

---

大多数「思维导图」只是加了样式的提纲。本 skill 把导图当作**严谨的知识工件**：针对单一主体的穷尽延伸，每条根到叶的路径连读必须成立完整命题，第一次了解的人**只靠读这张图**就能理解主体的全景和全部细节——不依赖任何图外文档。

这里每条规则都是一道疤：全部沉淀自六轮真实返工（2026-08 → 2026-09），每道闸都因为它要拦的事故曾经漏过而存在。

## ✨ 仓库里有什么

| 组成 | 内容 |
|---|---|
| [SKILL.md](SKILL.md) | 唯一正本：开工三件事、视觉+内容双基线、总定义（「导图=针对一个主体的穷尽延伸」）、词条表与定义笔记化规则、交付闸门。 |
| [references/pitfalls.md](references/pitfalls.md) | 踩坑全集四类：文件格式坑、内容组织坑、管线坑、协作纪律。 |
| [references/update-protocol.md](references/update-protocol.md) | 更新已有导图的六步协议（图是构建产物，禁手改 xmind）+ 防倒退三道保险。 |
| [references/memory/](references/memory/) | 6 份深度知识文档：视觉基线全字段、CLI 出图流程、叙事校准、渲染闪黑排障等。 |
| [tools/sync_check.py](tools/sync_check.py) | 零写盘三处同步闸：逐文件比对仓库镜像与本地 skill 正本的 SHA256，任何漂移都以非 0 退出码列出差异文件。每次提交前跑一次。 |

## 🔑 60 秒看懂核心思想

- **闭包铁律**——任何不了解导图所讲内容的正常人，只看这张图就能理解所有东西。这是最高验收线。
- **路径连读成命题**——理解的最小单位是命题不是名词；根到叶每条路径连读必须是一句人话；没有内涵子节点的裸名词直接删。
- **词条→笔记流水线**——定义不进树节点，活在数据层词条表里；构建时把释义全附到该词的每个使用点 notes（「一条笔记=一棵文字小树」）。树保持干净（组织节点 2-7 字、禁标点），术语在首次出现处就地讲清。
- **两代机器 QA**——构建期阻断闸（禁标点、词条五闸、成绩口径闸、一级预算 ≤9、扇出 ≤13）+ 事后八检，每一检都由一次真实返工沉淀。
- **数据/构建分离**——内容进数据文件、结构进构建脚本，图是数据的确定性函数：幂等重建、时间戳备份、diff 报告。**永远不手改 .xmind。**
- **预算折叠**——递归多层预算折叠（子树预算 50）+ 单链不折；折叠键是 `"branch": "folded"`（不是 `"folded": true`，那是踩过的坑）。

## 📦 安装

把本仓库复制进你的 Agent 技能目录即可，例如：

```bash
git clone https://github.com/Chestnuts-Sisyphus/mind-world-map.git
# Claude Code / Qoder 等支持 skill 发现的客户端（仓名与 skill 名有意不同，触发名保持 mindmap-engineering）：
cp -r mind-world-map ~/.claude/skills/mindmap-engineering
```

之后用 `/mindmap-engineering` 触发，或让 Agent 在任何导图任务开工前自动加载。

> **边界说明。** 本仓库是「能力面」——标准、闸门、协议、知识库。用它产出的具体导图归各自的主题项目管辖，不放这里。参考实现中的管线脚本（构建器/重组器/校验器）长在某人的本地工作区上，不随本公开包发布；方法论文档对其应有行为的描述是完整的。

## 🧪 如何验收一张图

- `xmind validate` 0 错只是底线，不是验收线。
- 无头渲染取证：开**副本**文件（绝不动正本）、禁用 GPU 合成启动、用 PrintWindow 抓窗，并且**按非白内容占比轮询——占比 >2% 才算渲染就绪**。固定秒数盲抓会出全白假阴性（基准机实测冷启动约 55 秒空白期）；Windows OCR 读图须传反斜杠绝对路径。
- 任何 `git checkout` 之后复跑 `python tools/sync_check.py`：换行符已由 `.gitattributes` 钉为 LF，该闸兜住残余漂移。

## 🗂️ 目录结构

```
mind-world-map/
├── SKILL.md                      # 入口：标准与交付闸（唯一正本）
├── references/
│   ├── pitfalls.md               # 踩坑全集（四类）
│   ├── update-protocol.md        # 更新六步协议 + 防倒退三保险
│   └── memory/                   # 6 份深度知识文档
├── README.md / README.zh-CN.md
├── LICENSE (MIT)
├── CHANGELOG.md
└── tools/sync_check.py           # 三处同步校验（仓库镜像 vs 本地 skill 正本）
```

## 🔄 如何更新（How to update）

**本地 skill 目录 = 编辑正本**，本仓库 = **发布镜像**。流程：

1. 在本地 skill 目录（如 `~/.claude/skills/mindmap-engineering/`）编辑 `SKILL.md` / `references/**`。
2. 把改动的文件按相同相对路径复制进本仓库。
3. 运行 `python tools/sync_check.py` —— 逐文件比对仓库与本地 skill 目录的 SHA256，零写盘；任何不一致都以非 0 退出码列出差异文件。退出码 0 才允许提交。

> `.gitignore` 中列出的项目私有知识文档（含 `QODER-MIGRATION.md`）按设计只留在本地；同步校验只比对公开文件集。

## 📄 许可

[MIT](LICENSE)
