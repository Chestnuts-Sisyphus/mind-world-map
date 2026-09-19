---
name: xmind-cli-local-generation
description: 本机官方 Xmind CLI 本地出 .xmind 流程与坑（SYS-0818-01 实测两版）：create/from-markdown+batch 覆盖、全右向必须用 TreeChart（layout 对根/一级分支被渲染层忽略）、Dawn=白底彩虹、PrintWindow+Windows OCR 可验证被遮挡的桌面渲染、auth 只有作者能点、Git Bash /tmp 与 <local-workdir>/tmp 路径分裂
metadata:
  node_type: memory
  type: project
  originSessionId: sess_3e9be600-d138-4c40-9391-3a1ef0a6ef12
---

本机官方 Xmind CLI（@xmindltd/xmind-cli@0.2.3，npm 全局，命令 `xmind`）已可用、已登录（cn 区）。本地出 `.xmind` 流程：草稿 markdown → `xmind create` → `xmind batch` 视觉覆盖 → `validate/describe/read` 自检 → 桌面 Xmind 实际打开验证。

- 文档：官方网页命令常被藏；skill 全文在 npm 包内 `skills/`（xmind-file/SKILL.md=总流程、markdown-grammar.md=`#`→根/`##`→分支/`> `→备注/`- `→叶、visual/node-style.md=themeColor/background/callout/emphasis op、visual/layout-style.md、recipe/quick-map=免费路径）。`xmind skill list/show` 需登录；本地包文件免登录可读。
- 免费路径：`xmind create --from-markdown <md> --skeleton <SK> --color <C> -o <file>.xmind`（billing consumed=0）。skeleton 名格式 `XXX-N`。
- **骨架←→方向（关键实测，08-19 修正）**：MindMap-1~12 全是 `org.xmind.ui.map.clockwise`（根在中间两侧展开）；**决定方向的真源=rootTopic.extensions 里的结构声明**，写 `[{"provider":"org.xmind.ui.map.unbalanced","content":[{"name":"right-number","content":"N"}]}]`（N=右侧一级分支数）才是右向（作者样例图即如此），`structureClass` 字段和 sheet 级 extensions 的 centralTopic 都不是最终裁决（CLI `xmind layout --layout map-right` 只改 structureClass+不动 rootTopic.extensions → 渲染仍回落 clockwise 平衡，这正是之前误判「layout 无效」的根因）；TreeChart-1/2（org.xmind.ui.tree.right）与 LogicChart（logic.right）的 rootTopic.extensions 天然一致所以开箱即右向。平衡图无法用 CLI 精确控制左右归位（map.clockwise 4 等分支=前二右半后二左半，可近似）。
- 配色：Dawn=白底彩虹六色（#FF6B6B #FF9F69 #97D3B6 #88E2D7 #6FD0F9 #E18BEE）；Space=#0D2F42 深蓝黑；Code=#2C2D30 深灰；Sophisticated=白底咖啡棕。无现成暗紫主题（暗紫需 batch themeColor 覆盖）。
- 视觉覆盖：`xmind batch <file> --input <json>` 支持 `{"op":"background","color":...}`、`{"op":"themeColor","branchColor":...,"fontColor":...,"lineColor":...,"borderColor":...}`（themeColor 会禁用彩虹调色板）、`{"op":"callout","topic":"根标题","text":"..."}`（图上可见标记）。`xmind describe` 输出 structureClass/canvas/theme overrides/callout 数可机器确认。
- 登录：`xmind auth login cn|global` 开浏览器只有作者能点，无头硬登被拒；`xmind auth status` 查 authenticated；文件命令与 skill list 全要登录。
- 环境坑：① Git Bash 的 `/tmp` 实为**当前用户临时目录**（`~/AppData/Local/Temp`），而 Write 工具把 `/tmp/x` 解释成**盘根** `tmp/x` → 两者分裂，CLI 传路径一律显式 Windows 绝对路径否则 ENOENT。② 桌面 Xmind=Electron（AppData/Local/Programs/Xmind/Xmind.exe v26.2.4171），PowerShell CopyFromScreen 抓不到其画布（GPU 合成+前台锁，屏幕可见的是其他前台窗口；本机有 GameViewer 虚拟显示器）；`Xmind.exe --help` 只会再拉实例无导出。③ **同名文件在 Xmind 开着时被覆盖，重开会显示旧渲染并标「已编辑」**——验证渲染必须用副本换文件名+taskkill 干净重启。④ Get-Process MainWindowTitle=文件名可确认打开成功。
- **默认折叠（2026-08-19 实测逆向自建正确格式）**：JSON v3 中让分支默认折叠=给 topic 直接加 `"branch":"folded"`（值折叠 else null/省略=展开）；桌面在 topic 模型里叫 `branchState`（`To.Folded="folded"`），序列化映射 `branchState→"branch"`、反序列化 `"branch"→branchState`。`xmind validate` 对未知字段宽容（加 `collapsed:true` 也 0 错但那是无效字段，桌面只认 `branch:"folded"`）。`app.asar` 里的 `collapsed`/`isCollapsed` 多是 Excel 表格渲染器与富文本 Selection，与思维导图分支无关。全景版已加：第 4 层 22 个有子分支节点全部标 `branch:folded`，打开只看前 4 层。脚本：ZCode 工作区 `collapse_panorama.py`。参考：Xmind SDK（xmindltd/xmind-sdk-js，v1 无折叠概念，旧格式才有）。
- **被遮挡窗口验证法（实测可靠）**：PrintWindow API（PW_RENDERFULLCONTENT=2）抓指定窗口位图 + Windows.Media.Ocr（需先加载 Windows.Storage/Graphics.Imaging/Media.Ocr/Globalization.Language WinRT 类型，`[Windows.Globalization.Language 'zh-Hans-CN']`）OCR 出文本+坐标 → 由 X 坐标判断布局（树形图右向：根 X 最小、子节点 X 递增）。比 CopyFromScreen 稳。
- 踩坑 CLI 内部：C# 结构体不能挂 DllImport（要拆开声明）；PowerShell Add-Type 的 WinRT 类型先 `$null = [Type, Namespace, ContentType=WindowsRuntime]` 加载。

**Why:** 作者要求「真的像思维导图」且禁云端 MCP/禁 html/Mermaid/MindElixir 当成品；风格被否两版后，作者以自己样例 `<local-workdir>/MD/We shall never surrender..xmind` 为唯一风格来源（全量复刻，见 [[xmind-style-baseline]] 与 作者侧交接文档（未随包发布））。
**How to apply:** 再出导图：先 `xmind auth status`；**风格一律照作者样例模板全量复刻**（模板移植法，见 [[xmind-style-baseline]]），方向用 rootTopic.extensions 的 unbalanced 声明保证；skill 内容读本地包；验证走 validate/describe/read + PrintWindow+OCR（副本文件+干净重启）；不硬搞 CopyFromScreen 截屏。

- **折叠算法升级（2026-09-04，作者定）**：折叠深度按预算算法定，不死数——可见节点预算 B（默认 50 含根，按图可调），逐层累计「当级+下级连带标题数」，取最大深度 D 使 visible(D)=1+Σ各层节点数 ≤ B，深度 D 的有子节点标 `branch:"folded"`；层多主题少可展到四五级以下，层少主题多第三级就折叠。同日实测：`branch:"folded"` 键再次验证有效（模型 branchState→序列化 branch 的映射成立）； Connectome 全景图（299 节点，预算 50→可见 16 节点）已按此算法折叠。
- **递归折叠实现两坑（2026-09-04 晚，C18 试验图实测）**：①mark 里 `folded.extend(mark(kid,…))` 是共享列表自 extend→每次调用翻倍，嵌套一深即 MemoryError（此前 720/801 节点图靠标记幂等侥幸存活）；修法=直接调用 `mark(kid,…)` 不 extend。②构建脚本必须自动设 rootTopic.extensions right-number=一级分支数（样例默认 3，C18 试验 8 支翻车 5 支跑左边被作者抓到）。字体：模板仅一级主题带内联样式，深层节点走主题回退——新节点须按深度克隆模板 style 或显式挂 `fo:font-family`，**且字体必须系统实装才渲染**（Lora 未安装→换装不生效，改用 Georgia；作者偏好=Georgia+思源宋体，实测自 Codex config.toml，见 [[xmind-style-baseline]]）。

- **递归多层折叠（2026-09-04 晚二次升级，作者定）**：折叠从「全局单层」升级为**递归多层**——对每个节点独立判定：其全部下级总数 > 子树预算 B（默认 50）→ 在该子树内部逐层累计找最大可见层，该层有子节点的节点标 `branch:"folded"`；被折叠节点自身子树再超标→**递归嵌套**预置折叠。保证任何一次展开的单屏宽度可控（防止同级主题总体宽度过宽）。同日 Connectome 全景图 467 节点/最深 7 层，49 个折叠点多层嵌套（如注入内部 R1至R5+三级预算再折、检验内部 HC/NC 检验+判据三步法再折）。同日配套**深度规则**：叶子细分到无可再细分（原子事实=数字/专名/例子/机制），概括主题必须列全成员——标准全集沉淀在 [[xmind-style-baseline]]。

- **单链不折叠（2026-09-04 晚，作者补）**：一个主题展开只多一条线（单孩子链）不加宽度→放行不折；折叠标记沿单链下推，只打在「展开会变宽」的分叉节点（≥2 孩子）上（fold_chain 实现）。同日关系线裁决：**不用联系线**（试验 7 条后作者判观感乱，sheet.relationships 键位留档备查）。同日 v8 重写后规模：801 节点/448 叶/72 折叠点。
