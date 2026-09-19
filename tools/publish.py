#!/usr/bin/env python3
"""发布入口（写盘）：把本地 skill 正本文本经发布面变换表生成仓库镜像，并把包内
工具分发回各正本目录，使「正本 → 发布面」这一步可执行、可复现、幂等。

用法：
    python tools/publish.py                 # 同步：主正本 → 仓库镜像；仓库 tools/ → 各正本
    python tools/publish.py --check         # 只报漂移不写盘（有漂移 exit 1）
    python tools/publish.py --dry-run       # 打印将写入的文件，不落盘
    python tools/publish.py --master DIR    # 指定主正本（编辑源）

方向约定（每条路径只有一个编辑源，避免双向覆盖）：
    SKILL.md / references/**  → 编辑源是主正本，仓库是它的发布面变换结果
    tools/**                  → 编辑源是仓库，正本目录里的 tools/ 是分发的副本

幂等：同一输入跑两遍，第二遍零写入、产出字节完全相同。所有写盘统一 LF 行尾。
退出码：0=已同步（或 --check 无漂移），1=--check 发现漂移、或主正本缺失。
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preflight import apply_publish_rules, gitignored_doc_paths, is_repo_layout  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
SKILL_MD = "SKILL.md"
# 主正本优先级：谁是当前编辑源，文本就以谁为准分发到其余正本与仓库。
# 顺序有意为之——`.qoder-cn` 是现役编辑源，把它排在最前可避免拿陈旧正本覆盖新改动。
MASTER_PRIORITY = [(".qoder-cn", "skills"), (".qoder", "skills"), (".claude", "skills")]
SKILL_NAME = "mindmap-engineering"


def public_rels(root: Path) -> list:
    """正本文本集 = SKILL.md + references/ 下全部 md，剔除 .gitignore 登记的私有件。"""
    private = gitignored_doc_paths()
    rels = set()
    if (root / SKILL_MD).is_file():
        rels.add(SKILL_MD)
    refs = root / "references"
    if refs.is_dir():
        rels.update(p.relative_to(root).as_posix() for p in refs.rglob("*.md"))
    return sorted(rels - private)


def tool_rels() -> list:
    """包内工具集 = tools/ 下的 .py / .tsv（不含 __pycache__）。"""
    tools = REPO / "tools"
    if not tools.is_dir():
        return []
    return sorted(
        p.relative_to(REPO).as_posix()
        for p in tools.rglob("*")
        if p.is_file() and p.suffix.lower() in {".py", ".tsv"} and "__pycache__" not in p.parts
    )


def master_dirs(argv_master) -> list:
    """--master > MINDMAP_SKILL_MASTERS > 按 MASTER_PRIORITY 顺序取存在的目录。
    返回列表的第一项即主正本（文本编辑源）。"""
    if argv_master:
        return [Path(argv_master).expanduser()]
    env = os.environ.get("MINDMAP_SKILL_MASTERS", "").strip()
    if env:
        return [Path(p).expanduser() for p in env.replace(os.pathsep, ";").split(";") if p.strip()]
    home = Path.home()
    return [home.joinpath(*parts).joinpath(SKILL_NAME) for parts in MASTER_PRIORITY
            if home.joinpath(*parts).joinpath(SKILL_NAME).is_dir()]


def rel_label(path: Path) -> str:
    """用相对 home 的路径标注目录：三处正本同名 mindmap-engineering，光看目录名分不出是谁。"""
    try:
        return "~/" + path.relative_to(Path.home()).as_posix()
    except ValueError:
        return path.as_posix()


def read_master(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def write_lf(path: Path, content: str, dry_run: bool) -> bool:
    """只在内容确有变化时落盘——这条判断就是幂等的来源。"""
    if path.is_file() and path.read_text(encoding="utf-8").replace("\r\n", "\n") == content:
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    return True


def plan(primary: Path, masters: list, dry_run: bool) -> list:
    """返回变更清单 [(目标描述, 相对路径)]；dry_run 时只计算不写盘。"""
    changes = []

    # 1) 主正本文本 → 仓库发布镜像（套发布面变换表）
    for rel in public_rels(primary):
        out = apply_publish_rules(read_master(primary / rel))
        if write_lf(REPO / rel, out, dry_run):
            changes.append(f"repo<-master {rel}")

    # 2) 主正本文本 → 其余正本（原文逐字同步，正本之间不留差异）
    for other in masters:
        if other.resolve() == primary.resolve():
            continue
        for rel in public_rels(primary):
            if write_lf(other / rel, read_master(primary / rel), dry_run):
                changes.append(f"{rel_label(other)}<-master {rel}")

    # 3) 仓库 tools/ → 每个正本（含主正本：工具的唯一编辑源是仓库）
    for rel in tool_rels():
        data = (REPO / rel).read_text(encoding="utf-8").replace("\r\n", "\n")
        for m in masters:
            if write_lf(m / rel, data, dry_run):
                changes.append(f"{rel_label(m)}<-repo {rel}")
    return changes


def main() -> int:
    ap = argparse.ArgumentParser(description="正本 → 发布镜像的可复现入口（幂等）")
    ap.add_argument("--master", help="主正本目录（文本的编辑源）")
    ap.add_argument("--check", action="store_true", help="只报漂移，不写盘")
    ap.add_argument("--dry-run", action="store_true", help="打印将写入的文件，不落盘")
    args = ap.parse_args()

    if not is_repo_layout():
        print("publish 只能在发布镜像仓库里运行（当前目录没有 .gitignore = 本地 skill 正本目录）。")
        print("理由：正本文本要先套发布面变换才写进仓库，在正本目录里跑等于拿原文与变换文本比对，必然误报漂移。")
        print("去仓库根目录执行：cd <仓库目录> && python tools/publish.py")
        print("安装点里可跑的是另两条只读闸：python tools/preflight.py 与 python tools/sync_check.py。")
        return 1

    masters = [d for d in master_dirs(args.master) if d.is_dir()]
    if not masters:
        print("未发现任何本地 skill 正本目录；publish 只在作者机器上有意义。")
        print("外部使用方可改用 sync_check.py（无正本时它退出码 0）。")
        return 0

    primary = masters[0]
    check_mode = args.check or args.dry_run
    changes = plan(primary, masters, dry_run=check_mode)

    if not changes:
        print(f"已同步，无需写入（主正本：{primary}；正本 {len(masters)} 处 + 仓库镜像）")
        return 0
    if args.check:
        print(f"漂移 {len(changes)} 处（--check 不写盘）：")
        for c in changes:
            print(f"  - {c}")
        return 1
    print(f"写入 {len(changes)} 处（主正本：{primary}）")
    for c in changes:
        print(f"  - {c}")
    if args.dry_run:
        print("--dry-run：以上均未落盘")
    return 0


if __name__ == "__main__":
    sys.exit(main())
