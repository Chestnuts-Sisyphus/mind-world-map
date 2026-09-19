---
name: xmind-render-flicker-compat
description: XMind 大图闪黑排障：病在上屏合成层（GPU合成），根治=关联烤 --disable-gpu-compositing；**09-12 XMind更新抹掉关联参数→闪黑复发，已重烤+登录自愈守卫(ZCodeXmindAssocGuard)上线**；GUI 禁管道启动/禁强杀等教训
metadata:
  node_type: memory
  type: reference
  created: 2026-09-05
  updated: 2026-09-12
  originSessionId: sess_1ac81822-b5f6-428c-887e-2d670ddffbcb
---

## XMind 大图闪黑/割裂排障（2026-09-05，7516 节点 Connectome 图）

**结论：文件健康，病在渲染层。** 取证链：zip 无坏块、xmind validate 0 错 0 警告、新旧两版（7496→7516）结构逐项一致（仅 +20 节点）、非 content 条目逐字节相同、id/样式唯一、无控制字符；用户时段 XMind 日志仅 1 条无害 API 400、无 GPU 崩溃转储、无显卡驱动 TDR 事件；静置渲染截图完美。XMind 26.5（8/10 装的，未更新过）。字体报错（Unknown font format）自 8-19 起就有，非新变量；NVIDIA 驱动 8/20、UU远程 8/21 升级均早于 9/1-9/4 正常使用期。

**第二阶段实锤（作者报「打开就闪黑+各种错位」后）**：①后台 PrintWindow 抓到渲染现场——黑底根节点被甩到屏幕边缘+幽灵「+」控件残影+「已编辑」脏状态恢复；②XMind file-cache 出现**跨文件缓存串味铁证**（某快照 content.json=Connectome 但 thumbnail 渲染的是 We shall 图）；③处置：10 个 Connectome 缓存条目隔离到 `workspace/_xmind_state_quarantine/`（回滚=复制回 file-cache），建换名副本 `<local-workdir>/HERMES/Connectome-全景-测试副本.xmind`；④干净配置测试被登录墙挡住（新 user-data-dir 无登录态）。⑤排障手法：后台截窗=Python ctypes PrintWindow(PW_RENDERFULLCONTENT)=`xmind_bgshot.py`，不抢焦点；作者在用电脑时禁开 GUI。

**根因终审（作者 A/B 实测 09-05 深夜）**：原图与换名副本在 GPU 模式下同样闪黑错位（排除文件/路径/缓存因素）；`--disable-gpu` 软渲染无闪黑但卡顿；`--disable-gpu-compositing` 混合模式不闪有点卡 → **GPU 硬件合成是根因**。三档启动器在 `<local-workdir>/HERMES/`：Xmind混合模式-Connectome.cmd（--disable-gpu-compositing）/Xmind兼容模式-Connectome.cmd（--disable-gpu）。测试副本与隔离区留作备份可随时删；原图路径仍是流水线唯一更新目标。 〔作者本机历史，外部不可复用：本行的计划任务名、脚本路径、注册表 ProgId、重启命令都是作者这台机器上的处置流水，不随包发布〕

## 09-06 下午：干净重启实验否定拉锁病 → 驱动 616.64 已装，待重启终测

⑪作者 13:42 自行重启（原始配置）→**仍闪** → 拉锁病/强杀触发模型被否定（纯新开机也闪），病=616.56 驱动与 Electron 合成的常驻兼容问题。⑫时间线勘误：此前两次「重启测 MPO/HAGS」全部无效的原因=**两次重启都发生在修复应用之前**（首次是还原后才重启；二次 13:42 早于 14:29 重新应用）——MPO/HAGS 从未真正生效过。⑬已静默安装 **616.64**（939MB 包在 <local-workdir>/HERMES/nvidia-616.64.exe，`-s -noeject -noreboot`，DriverVersion 32.0.16.1656→32.0.16.1664 实证成功；注意：第一次 Start-Process 静默安装会秒退，重试一次即可）。⑭当前待办=一次重启同时生效：新驱动+MPO关+HAGS关 → 作者双击原图终测。仍闪的最后手段=**降级 616.56 之前的旧版驱动**（驱动库无旧包，需查 NVIDIA 历史版本下载）。⑮NVIDIA 直链规律：`us.download.nvidia.com/Windows/<ver>/<ver>-desktop-win10-win11-64bit-international-dch-whql.exe`（CN 镜像不通，直连美区会 RST，走本机代理下载稳）；AjaxDriverService API 已 404 退场，版本查询用 processFind.aspx。

## 09-05 深夜案件重开：作者否决 cmd 启动器，必须根治

①作者拍板：「不接受一直用 cmd 打开思维导图，必须根治」——根治=**双击 .xmind 正常打开不闪**；cmd 启动器降级为诊断工具/最后保底（同款校准见 零摩擦工具原则（作者侧记忆，未随包发布）：绕路方案只能当诊断手段，交付前必须穷尽恢复用户原始使用方式的根治路径）。
②**UU远程 已排除**：作者托盘退出后依旧闪黑。
③**MPO 已系统级关闭**：新建 `HKLM\SOFTWARE\Microsoft\Windows\Dxgk` 键 + `OverlayTestMode=5`（DWORD）——此前该键不存在=MPO 出厂默认开；NVIDIA 驱动升级后 Chromium/Electron 应用闪黑方块的头号惯犯；回滚=删该值。待作者双击原图复测（若无效先重新登录 Windows 让策略彻底生效）。 〔作者本机历史，外部不可复用：本行的计划任务名、脚本路径、注册表 ProgId、重启命令都是作者这台机器上的处置流水，不随包发布〕
④后续阶梯：禁用 GameViewer 虚拟显示适配器设备（Disable-PnpDevice，注意作者远程串流时可能要用）→ NVIDIA 驱动回滚/更新；**保底**=把 `--disable-gpu-compositing` 烤进 .xmind 文件关联的 shell\open\command（双击即带参，绕开 cmd；UserChoice 有哈希保护改不了，改 ProgId 的 command 合法）。 〔作者本机历史，外部不可复用：本行的计划任务名、脚本路径、注册表 ProgId、重启命令都是作者这台机器上的处置流水，不随包发布〕
⑤ops 课：Git Bash 下 reg.exe 的 `/v` 参数被 MSYS 路径转换吃掉报「无效语法」——**注册表操作一律走 PowerShell**。

## 09-06 凌晨进展：排除链收口 + 拉锁病模型 + 静默重启看门狗

⑥**排除链**：禁用 GameViewer 虚拟显示适配器（问题码22，实验后已还原启用）→仍闪；**DWM 复位**→仍闪；**7496 修改前备份同样闪** → 内容/我的+20节点彻底排除；PrintWindow 静态渲染干净 vs 眼睛看闪 → **病在上屏合成层，不在应用**。
⑦**主导模型=616.56 驱动对巨型 DirectComposition 画布的「拉锁病」**：平时没事，强杀进程等触发事件把图形栈锁死在坏档直到重启。吻合全部观察：白天好（无强杀）/驱动早升级却没事（缺触发）/今晚首发时间线与首次 taskkill 强杀 XMind 吻合/换文件也闪（状态跟机器不跟文件）/软渲染干净（绕开合成）。已还原全部实验性系统改动（MPO/HAGS/虚拟适配器/服务）=重启即纯原始配置实验。重启后仍闪的阶梯=**升 616.64**（9/3 新出 WHQL，4070 SUPER pfid=1039 可查 processFind API）→再降级 616.56 之前的版本（驱动库旧包已不在，需下载）。
⑧**强纪律：开着大图的 XMind 禁止 taskkill 强杀**（首发时间线与首次强杀吻合，且强杀还污染过缓存/恢复态——恢复态按内容匹配，换名副本也会中招；已全部隔离）。
⑨**静默重启看门狗已上岗**（作者委托：不打断其他会话长程任务，全结束后自动重启）：`schtasks ZCodeQuietReboot`→`workspace/watchdog_reboot.ps1`，条件=ZCode 全树 CPU 静默+会话存储（db/tasks-index/exec/rollout/artifacts/agents）零写入 30 分钟+无人键鼠 10 分钟→`shutdown /r /t 60 /f`（60 秒内 `shutdown /a` 可取消），6 小时兜底放弃，日志 `_reboot_watchdog.log`。ZCode 已加登录自启动（Startup 文件夹 ZCode.lnk→<local-workdir>/ZCODE\ZCode.exe），重启后自动打开。 〔作者本机历史，外部不可复用：本行的计划任务名、脚本路径、注册表 ProgId、重启命令都是作者这台机器上的处置流水，不随包发布〕
⑩ops 课：**PS5.1 把无 BOM UTF-8 的 .ps1 当 ANSI 读**，中文注释直接炸解析（任务返回码 1 无输出）——含中文的 ps1 必须存 GBK 或纯 ASCII；schtasks /tr 里的路径带引号会原样传给 -File 导致找不到文件（无空格路径别加引号）。

## 09-06 下午终局：610.88 也闪（驱动分支全体出局）→ 关联烤参=现行保底，下次重启测三合一

⑯610.88 旧分支驱动热激活（pnputil /restart-device 免重启换驱动，已实证可用）→ **还是闪** → 616.56/616.64/610.88 三代驱动全闪，驱动版本线全体出局；MPO/HAGS 当时未重启未生效。⑯b 作者确认混合模式**不闪、有点卡**。⑰**已落地：--disable-gpu-compositing 烤进 .xmind 文件关联**（`Xmind Workbook`+`xmind-zen` 两个 ProgId 的 shell\open\command，原值备份 workspace/xmind_assoc_backup.json）——双击习惯不变、确定不闪、略卡。⑱下次重启=三修复首次真正生效（616.64+MPO5+HAGS1）：作者说重启后，**先临时摘关联参数让他双击测全速 GPU**——若痊愈则不恢复参数=根治；仍闪则恢复参数、再测 --disable-direct-composition 变体；全灭则现状=最小代价，XMind/驱动升级后复测。⑲仪器沉淀：`xmind_flicker_test.py <tag> [路径] [启动参数]`（拉起+强制正常矩形+TOPMOST+屏幕连拍量化黑帧率）——但作者用电脑时窗口抢不到顶层、测量无效，**只能作者配合或空闲时段跑**；PrintWindow 系列永远照不到上屏层。 〔作者本机历史，外部不可复用：本行的计划任务名、脚本路径、注册表 ProgId、重启命令都是作者这台机器上的处置流水，不随包发布〕

## 09-12 复发与根治：XMind 更新抹掉关联参数 → 重烤 + 登录自愈守卫

⑲XMind 09-09 更新到 26.5.1107（装在 AppData\Local\Programs\Xmind，非 Program Files），**更新程序重注册 .xmind 文件关联，把当初烤进两个 ProgId（`Xmind Workbook`/`xmind-zen`）的 `--disable-gpu-compositing` 参数抹成裸 `Xmind.exe "%1"`** → GPU 合成回开挂 → 大图闪黑复发。9/12 排查确认：MPO(OverlayTestMode=5)✓、HAGS(HwSchMode=1)✓ 都在，但 NVIDIA 驱动已回落到 610.88（616.64 不知何时没了，三合一从未齐过）；配置无硬件加速开关（Electron v3 档案，Preferences/Local State 无加速键）。**复发=第三次实锤关联参数是唯一有效杠杆**。 〔作者本机历史，外部不可复用：本行的计划任务名、脚本路径、注册表 ProgId、重启命令都是作者这台机器上的处置流水，不随包发布〕
⑳**处置**：①重烤参数（原备份 xmind_assoc_backup.json 仍代表回滚态，未动）②**根治防复发=登录自愈守卫**：`workspace/default/xmind_assoc_guard.ps1`（纯 ASCII 防 PS5.1 解析炸）+ 计划任务 `ZCodeXmindAssocGuard`（ONLOGON/RL LIMITED/无引号路径），登录时检查两个 ProgId 缺参数即补回并写 `xmind_assoc_guard.log`；手动运行验证结果 0，补回分支用临时键模拟实测通过。守卫会造成"想测全速 GPU 会被下次登录自动补回"——要测先停任务（schtasks /Delete /TN ZCodeXmindAssocGuard）。 〔作者本机历史，外部不可复用：本行的计划任务名、脚本路径、注册表 ProgId、重启命令都是作者这台机器上的处置流水，不随包发布〕
㉑后续阶梯不变：XMind/驱动升级后若想试全速 GPU，停守卫→摘参数→双击复测；仍闪则参数是唯一解。NVIDIA 驱动线（610.88/616.56/616.64）三代全闪已出局，勿再花力气升驱动。

## 教训（实踩沉淀）

1. **GUI 应用严禁从 agent Bash 管道启动**（`"Xmind.exe" file &` 这种）：Bash 调用结束管道关闭→EPIPE→报错又写日志→递归死循环，几分钟刷出 1.25GB 日志（已截断清理）。正确姿势=PowerShell `Start-Process` 或 `cmd //c start` 分离启动。
2. **SendKeys 会打进 XMind 节点编辑框**（画布应用键击序列危险）；截屏取证用「AppActivate+GetForegroundWindow 标题校验+CopyFromScreen」原子 PowerShell 脚本（workspace/xmind_capture2.ps1 范本，前台校验失败就放弃，禁抢焦点）；PowerShell 函数调用不能带括号。 〔作者本机历史，外部不可复用：本行的计划任务名、脚本路径、注册表 ProgId、重启命令都是作者这台机器上的处置流水，不随包发布〕
3. **cmd 批处理含中文必须存 GBK**（UTF-8 中文注释被 GBK 解析成乱码命令）；从 Git Bash 调 CJK 文件名的 cmd 不可靠，CJK 路径 GUI 启动走 PowerShell Start-Process。

关联 [[xmind-cli-local-generation]] 作者侧流水线记忆（未随包发布） 零摩擦工具原则（作者侧记忆，未随包发布）
