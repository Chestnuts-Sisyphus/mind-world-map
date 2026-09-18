---
name: connectome-mindmap-project
description: CM 导图全闭包工程（09-04 深夜）：取代链样板 55 节点过审=密度基准；数据/构建分离
  （cm_data_a/b/c.py+build_cm_closure.py，四道机器检查）；第一期 969 节点十一支交付；栗子确认目标
  8000~12000 规模「赶紧的吧」；量产清单已列
metadata:
  node_type: memory
  type: project
  originSessionId: sess_70ac118f-b284-4866-8a67-701761338609
---

2026-09-04 深夜，栗子对 CM 导图提出根本要求「**只读思维导图就能理解所有全景和所有的细节**」，并判定此前所有版本与该要求的差距是**指数级**（381 节点 vs 完整闭包 8000~12000）——不是微调能解决，须从生产方式底层改。

**标准定稿（栗子确认）**：图=项目知识闭包——任意概念合理追问 2 跳内有答案；冻结资产每句有信息量的话都入图（对账保证）；停止权在**追问穷尽程序**手里，不在 agent 手感里。**密度基准=取代链样板 55 节点/概念**（`D:/AI/HERMES/取代链闭包demo-20260904.xmind`，九问答面：是什么/为什么存在/怎么运作/何时发生/谁执行/在哪承载/不做会怎样/边界/现状），栗子看过后拍板「按这个标准来做 CM 的」。

**架构（数据/构建分离，量产基础设施）**：
- 内容数据=`workspace/cm_data_a.py`（这图讲什么/先认识几个词词汇层/怎么来的/原料/蒸馏/格式）+ `cm_data_b.py`（注入/运行/效果/版本[含取代链全闭包 55 节点整体并入]/检验/分工）+ `cm_data_c.py`（深化包：误差实例库 R1-R19/承载力细节/HC·NC 映射抽样/词汇扩充/判定树细节）
- 组装器=`workspace/build_cm_closure.py`：merge_into_tree 按一级标题并入数据 C；四道机器检查（禁用符含逗号顿号/2-7 字/递归折叠+单链不折/Georgia 字体克隆）；right-number 自动=一级分支数
- 产出=`D:/AI/HERMES/Connectome-全景-20260904.xmind`（**第一期 969 节点**，11 一级分支：这图讲什么/先认识几个词/原料/蒸馏/格式/注入/运行/效果/版本/检验/分工）

**量产清单（每批 800~1500 节点，目标 8000~12000，栗子原话「赶紧的吧」）**：B-v2 正确性六步全链细节、C-v1 四层作用点证明、C-v2 五平台矩阵、A-v1 例证池 65 条、E-v1/E-v6 主权与缺失感知细节、D-v2 判卷四防线、立项讨论记录（不变量分析法故事）、HC/NC/CB 交付物实例。每批=新数据文件+合并+机器检查，追加即增产。

**工程坑（本轮实踩）**：①mark 递归里 `folded.extend(mark(...))` 共享列表自倍增=MemoryError（正确=直接调用不 extend）；②括号配平靠数数必错，用 `ast.literal_eval` 自检或 `str(list)` 程序化构造；③Mimosa 拦 Bash 直写 .py 源码（cp/heredoc 均拦），必须走 Write/Edit；④超长 heredoc 会截断（SyntaxError 中断），大改动用 Write 全量重写；⑤ Edit 报 modified-since-read 时重新 Read 即可。

**配套**：十课底层课程（第 1 课已讲待复述）与导图工程互喂。标准全集见 [[xmind-style-baseline]]（含标题 2-7 字铁律「定下的标准不能动」教训：我曾两次擅改被栗子打回），技术坑见 [[xmind-cli-local-generation]]，讲解法见 [[chestnut-explanation-protocol]]，沟通剂量见 [[decision-briefing-before-ask]]。
