# 🧠 导图工程（Mindmap Engineering）

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![release](https://img.shields.io/github/v/release/Chestnuts-Sisyphus/mind-world-map.svg)](https://github.com/Chestnuts-Sisyphus/mind-world-map/releases)
[![CI](https://img.shields.io/github/actions/workflow/status/Chestnuts-Sisyphus/mind-world-map/ci.yml.svg?label=CI)](https://github.com/Chestnuts-Sisyphus/mind-world-map/actions/workflows/ci.yml)
[![skill](https://img.shields.io/badge/skill-mindmap--engineering-informational.svg)](SKILL.md)

**面向 agent 的思维导图工程化 skill —— 实战打磨的标准、两代机器 QA 闸门，以及一条数据/构建分离流水线，用来产出冷读者单看图纸就全懂的 XMind。**

[English](README.md) · [标准正本](SKILL.md) · [踩坑全集](references/pitfalls.md) · [更新协议](references/update-protocol.md) · [版本记录](CHANGELOG.md)

---

多数「思维导图」产出只是加了装饰的提纲。本 skill 把思维导图当作**严肃知识制品**：对唯一主体的穷尽延伸，每条根到叶的路径读下来是一个完整命题，第一次接触的人**只读这张图**就能掌握全景与全部细节——不依赖任何外部文档。

这里每条规则都是一道疤：从 2026-08 → 2026-09 六轮真实返工里蒸馏出来，每道闸都存在是因为有东西漏过了上一道闸。

## ✨ 仓库里有什么

| 组成 | 你拿到什么 |
|---|---|
| [SKILL.md](SKILL.md) | 唯一标准正本：开工三件事、双基线（视觉+内容）、总定义（「导图=针对一个主体的穷尽延伸」）、词条台账与笔记化规则、交付闸铁律。 |
| [references/pitfalls.md](references/pitfalls.md) | 四类踩坑全集：文件格式坑、内容组织坑、管线坑、协作规则。 |
| [references/update-protocol.md](references/update-protocol.md) | 更新已有导图的六步协议（图是构建产物，禁手改 XMind）+ 三条防回归机制。 |
| [references/memory/](references/memory/) | 6 份深度知识文档：视觉风格基线、CLI 本地出图流程、叙事校准、渲染闪退兼容等。 |
| [tools/sync_check.py](tools/sync_check.py) | 只读同步闸：把仓库镜像与本地 skill 编辑正本逐文件比 SHA256（比对前先套发布面变换）；点名不一致文件。正本目录不存在则跳过，任何机器上跑都安全。 |
| [tools/preflight.py](tools/preflight.py) | 只读发布闸：本机痕迹（盘符路径、8.3 短名、用户目录段、本机账号名）、凭据形态、相对链接与文档指针死链、公开文档点名私有件、中英章节结构漂移、身份词回归。只输出「文件:行号 + 规则名」，绝不输出命中内容。`--self-test` 自证每类都会响。 |

## 🔑 60 秒看懂核心思想

- **闭包铁律**——不了解主体的人只读图就能懂一切，这是验收线。
- **命题路径**——理解单位是命题不是名词；每条根到叶路径须读成一句人话，无实义的裸名词直接删。
- **词条→笔记管线**——定义活在数据层词条台账里，构建时自动附加到每个使用点的 notes（「一条笔记=一棵文字小树」），树保持干净（2-7 字标签、零标点），术语在首用处被解释。
- **两代机器 QA**——构建期阻断闸（禁标点、词条五闸、成绩口径闸、一级预算 ≤9、扇出 ≤13）+ 事后八检，每检都由一次真实返工沉淀。
- **数据/构建分离**——内容进数据文件、结构进构建脚本，图是数据的确定性函数：幂等重建、时间戳备份、diff 报告。绝不手改 `.xmind`。
- **预算折叠**——递归多层折叠（子树预算 50）+ 单链豁免，折叠键用 XMind 正确写法 `"branch": "folded"`。

## 📦 安装

把本仓库拷进 agent 的 skills 目录，例如：

```bash
git clone https://github.com/Chestnuts-Sisyphus/mind-world-map.git
# 支持 skill 发现的客户端（仓名与 skill 名有意不同，触发名保持 mindmap-engineering）：
cp -r mind-world-map ~/.claude/skills/mindmap-engineering
```

然后用 `/mindmap-engineering` 触发（或让 agent 在任何导图任务上自动加载）。

> **边界说明。** 本仓是**能力**（标准、闸门、协议、知识库）。用它产出的具体成品图归各自的主体项目，不进本仓。管线脚本与成品校验脚本的参考实现在作者的本地工作区开发，**不随公开包发布**——[SKILL.md](SKILL.md) 完整规定了每个组件该做什么，你可以按口径自建；可执行底线是 `xmind validate` + SKILL 里的两代 QA 清单。

## 🧪 如何验收一张图

- `xmind validate` → 0 错只是底线，不是验收线。
- 无头渲染取证：打开文件的**副本**（绝不碰原件），禁用 GPU 硬件合成，用 PrintWindow 抓窗，并**按非白内容占比轮询——占比 >2% 才算渲染就绪**。固定秒数盲抓必然产生全白假阴性（参照机器实测冷启动空白约 55 秒）。Windows OCR 读图须传反斜杠绝对路径。
- 任何 `git checkout` 之后重跑两道闸——见下文「如何更新」。

## 🗂️ 目录结构

```
mind-world-map/
├── SKILL.md                      # 入口：标准与交付闸（唯一正本）
├── references/
│   ├── pitfalls.md               # 四类踩坑全集
│   ├── update-protocol.md        # 六步更新协议 + 防回归
│   └── memory/                   # 6 份深度知识文档
├── tools/
│   ├── sync_check.py             # 正本与镜像一致性闸（只读）
│   └── preflight.py              # 发布闸：痕迹/凭据/死链/隐私（只读）
├── .github/
│   ├── workflows/ci.yml          # 跑两道闸 + 链接与结构检查
│   ├── ISSUE_TEMPLATE/           # 缺陷 / 需求模板
│   └── pull_request_template.md  # 贡献者自查清单（含两道闸）
├── README.md / README.zh-CN.md
├── CONTRIBUTING.md / SECURITY.md / CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── LICENSE (MIT)
├── .gitattributes                # 钉文本文件 eol=lf（见更新说明中的换行符一条）
└── .gitignore                    # 把项目本地知识文档挡在包外
```

## 🔄 如何更新

**本地 skill 目录是编辑正本**，本仓库是**发布镜像**。两个事实决定了流程形态：

- **发布面是一次确定性变换。** 本地正本保留原文；发布面把作者身份匿名化、把本机路径通用化，变换表在 `tools/preflight.py` 里。所以镜像不是正本的字节拷贝，而是正本的变换结果。
- **行尾钉死 LF**（`.gitattributes`）；在 `core.autocrlf=true` 的 Windows 机器上，编辑器可以静默写入 CRLF 并把镜像改漂。

步骤：

1. 在本地 skill 目录（如 `~/.claude/skills/mindmap-engineering/`）改 `SKILL.md` / `references/**`。
2. 把改动文件按同相对路径拷进仓库，并套用 `tools/preflight.py` 里的发布面规则。
3. 跑两道闸，两者退出码都为 0 才允许提交：

```bash
python tools/sync_check.py      # 点名每个不一致文件；正本目录可用位置参数或 MINDMAP_SKILL_MASTERS 指定
python tools/preflight.py       # 每条发布面违规点名到文件与行号
python tools/preflight.py --self-test   # 自证每类检查仍会触发
```

> `.gitignore` 中列出的项目私有知识文档按设计只留本地（含本仓自己的迁移日志）；同步校验只比对公开文件集，而一旦私有件真的落进包里，预检闸会直接失败。

## 🤝 参与贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)——简版口径：标准只改 [SKILL.md](SKILL.md)（唯一正本），不许在具体产出里自行放宽任何规则，开 PR 前跑完两道闸。疑似安全问题按 [SECURITY.md](SECURITY.md) 上报；参与者须遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

## 📄 许可

[MIT](LICENSE)
