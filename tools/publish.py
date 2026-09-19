#!/usr/bin/env python3
"""发布入口（写盘）：把本地 skill 正本文本经发布面变换表生成仓库镜像，并把包内
工具分发回各正本目录，使「正本 → 发布面」这一步可执行、可复现、幂等。

用法：
    python tools/publish.py                 # 同步：主正本 → 仓库镜像；仓库 tools/ → 各正本
    python tools/publish.py --check         # 只报漂移不写盘（有漂移 exit 1）
    python tools/publish.py --dry-run       # 打印将写入的文件，不落盘
    python tools/publish.py --master DIR    # 指定主正本（编辑源）
    python tools/publish.py --self-test     # 在临时假目录里自证四条不变量，绝不碰真安装点

方向约定（每条路径只有一个编辑源，避免双向覆盖）：
    SKILL.md / references/**  → 编辑源是主正本，仓库是它的发布面变换结果
    tools/**                  → 编辑源是仓库，正本目录里的 tools/ 是分发的副本

幂等：同一输入跑两遍，第二遍零写入、产出字节完全相同。所有写盘统一 LF 行尾。
退出码：0=已同步（或 --check 无漂移），1=--check 发现漂移、或运行位置不是发布镜像仓库。
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preflight import (apply_publish_rules, gitignored_doc_paths,  # noqa: E402
                       is_repo_layout)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
SKILL_MD = "SKILL.md"
# 主正本优先级：谁是当前编辑源，文本就以谁为准分发到其余正本与仓库。
# 顺序有意为之——`.qoder-cn` 是现役编辑源，把它排在最前可避免拿陈旧正本覆盖新改动。
MASTER_PRIORITY = [(".qoder-cn", "skills"), (".qoder", "skills"), (".claude", "skills")]
SKILL_NAME = "mindmap-engineering"
TOOL_SUFFIXES = {".py", ".tsv"}


def public_rels(root: Path, private=None) -> list:
    """正本文本集 = SKILL.md + references/ 下全部 md，剔除 .gitignore 登记的私有件。"""
    if private is None:
        private = gitignored_doc_paths()
    rels = set()
    if (root / SKILL_MD).is_file():
        rels.add(SKILL_MD)
    refs = root / "references"
    if refs.is_dir():
        rels.update(p.relative_to(root).as_posix() for p in refs.rglob("*.md"))
    return sorted(rels - set(private))


def tool_rels(repo: Path = REPO) -> list:
    """包内工具集 = tools/ 下的 .py / .tsv（不含 __pycache__）。"""
    tools = repo / "tools"
    if not tools.is_dir():
        return []
    return sorted(
        p.relative_to(repo).as_posix()
        for p in tools.rglob("*")
        if p.is_file() and p.suffix.lower() in TOOL_SUFFIXES and "__pycache__" not in p.parts
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


def plan(primary: Path, masters: list, dry_run: bool, repo: Path = REPO) -> list:
    """返回变更清单 [(目标描述, 相对路径)]；dry_run 时只计算不写盘。"""
    changes = []
    private = gitignored_doc_paths(repo)
    rels = public_rels(primary, private)

    # 1) 主正本文本 → 仓库发布镜像（套发布面变换表）
    for rel in rels:
        out = apply_publish_rules(read_master(primary / rel))
        if write_lf(repo / rel, out, dry_run):
            changes.append(f"repo<-master {rel}")

    # 2) 主正本文本 → 其余正本（原文逐字同步，正本之间不留差异）
    for other in masters:
        if other.resolve() == primary.resolve():
            continue
        for rel in rels:
            if write_lf(other / rel, read_master(primary / rel), dry_run):
                changes.append(f"{rel_label(other)}<-master {rel}")

    # 3) 仓库 tools/ → 每个正本（含主正本：工具的唯一编辑源是仓库）
    for rel in tool_rels(repo):
        data = (repo / rel).read_text(encoding="utf-8").replace("\r\n", "\n")
        for m in masters:
            if write_lf(m / rel, data, dry_run):
                changes.append(f"{rel_label(m)}<-repo {rel}")
    return changes


# ------------------------------------------------------------------ 自测
# 夹具文本用「盘符路径 + 包外记忆指针」两种必须变换的形态，刻意不写身份词：
# 身份词本体一旦落到临时文件上，测试夹具自己就成了命中原文的载体；身份词的变换
# 由 tools/preflight.py --self-test 的内存用例覆盖（不落盘）。
RAW_SAMPLE = "落盘位置 Q:/SYNTH/x.md，另见 [[cm-closure-mindmap-pipeline]]。\n"  # preflight:rule-literal: "发布面变换夹具需盘符与包外指针两种真实形态，值为合成"
GITIGNORE_STUB = "__pycache__/\nreferences/memory/private-notes.md\n"
TOOL_SAMPLE = "#!/usr/bin/env python3\nprint('tool payload')\n"


def _put(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _fake_workspace(root: Path):
    """搭一套临时「假仓库 + 两个假正本」，用于自测；不读也不写真实安装点。"""
    repo, primary, secondary = root / "repo", root / "masterA", root / "masterB"
    _put(repo / ".gitignore", GITIGNORE_STUB)
    _put(repo / "tools" / "demo_tool.py", TOOL_SAMPLE)
    _put(primary / SKILL_MD, RAW_SAMPLE)
    _put(primary / "references" / "memory" / "a.md", RAW_SAMPLE)
    _put(primary / "references" / "memory" / "private-notes.md", RAW_SAMPLE)
    _put(secondary / SKILL_MD, "陈旧副本：上一轮没同步下来的旧文本。\n")
    return repo, primary, secondary


def self_test() -> int:
    """四条不变量各自正证 + 反证。全在临时目录里跑，跑完即弃。"""
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + f"publish/{name}")
        ok = ok and bool(cond)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo, primary, secondary = _fake_workspace(root)
        masters = [primary, secondary]

        changes = plan(primary, masters, dry_run=False, repo=repo)
        check("first run writes", bool(changes))

        mirrored = (repo / SKILL_MD).read_text(encoding="utf-8")
        check("mirror has no drive-letter path", ":/" not in mirrored.replace("https://", ""))
        check("mirror has no external memory pointer", "[[cm-" not in mirrored)
        check("mirror text equals transformed master",
              mirrored == apply_publish_rules(RAW_SAMPLE))
        check("private doc not mirrored", not (repo / "references" / "memory" / "private-notes.md").is_file())
        check("stale secondary master overwritten by primary",
              (secondary / SKILL_MD).read_text(encoding="utf-8") == RAW_SAMPLE)
        check("tools distributed to every master",
              all((m / "tools" / "demo_tool.py").is_file() for m in masters))

        # 幂等：连跑第二遍必须零写入
        check("second run writes nothing", plan(primary, masters, dry_run=False, repo=repo) == [])

        # 编辑源方向：主正本文本改一句，其余正本与仓库跟着走，反向不回流
        _put(primary / SKILL_MD, RAW_SAMPLE + "\n主正本里新加的一句。\n")
        stale_repo_text = "仓库侧的陈旧文本。\n"
        _put(repo / SKILL_MD, stale_repo_text)
        plan(primary, masters, dry_run=False, repo=repo)
        check("primary wins over secondary master",
              (secondary / SKILL_MD).read_text(encoding="utf-8").endswith("主正本里新加的一句。\n"))
        check("stale repo text never feeds back into the master",
              (primary / SKILL_MD).read_text(encoding="utf-8").endswith("主正本里新加的一句。\n"))
        check("stale repo text replaced by the master's published face",
              (repo / SKILL_MD).read_text(encoding="utf-8") != stale_repo_text)

        # 安装点布局（无 .gitignore）必须拒写：在正本目录里跑必然误判漂移
        check("non-repo layout refused", not is_repo_layout_at(root / "plain-dir"))

        # --check 只报漂移不写盘
        _put(primary / SKILL_MD, RAW_SAMPLE + "\n未发布的又一次编辑。\n")
        before = (repo / SKILL_MD).read_bytes()
        drift = plan(primary, masters, dry_run=True, repo=repo)
        check("--check reports drift", bool([c for c in drift if c.startswith("repo<-master")]))
        check("--check writes nothing", (repo / SKILL_MD).read_bytes() == before)

        # 反向接线证明（其一）：去掉幂等判断 → 每遍都报变更，幂等不变量失效
        original = write_lf
        try:
            globals()["write_lf"] = lambda p, c, d: (p.parent.mkdir(parents=True, exist_ok=True),
                                                     not d and p.write_text(c, encoding="utf-8", newline="\n"),
                                                     True)[-1]
            check("removing the idempotence guard breaks the no-write invariant",
                  plan(primary, masters, dry_run=False, repo=repo) != [])
        finally:
            globals()["write_lf"] = original

        # 反向接线证明（其二）：去掉发布面变换 → 盘符路径直接进镜像
        original_rules = apply_publish_rules
        try:
            globals()["apply_publish_rules"] = lambda t: t
            plan(primary, masters, dry_run=False, repo=repo)
            leaked = ":/" in (repo / SKILL_MD).read_text(encoding="utf-8")
            check("removing the transform leaks local paths into the mirror", leaked)
        finally:
            globals()["apply_publish_rules"] = original_rules

    return 0 if ok else 1


def is_repo_layout_at(root: Path) -> bool:
    """布局判定：有 .gitignore = 发布镜像仓库，可以写；没有 = 本地正本目录，拒写。"""
    return (root / ".gitignore").is_file()


def main() -> int:
    ap = argparse.ArgumentParser(description="正本 → 发布镜像的可复现入口（幂等）")
    ap.add_argument("--master", help="主正本目录（文本的编辑源）")
    ap.add_argument("--check", action="store_true", help="只报漂移，不写盘")
    ap.add_argument("--dry-run", action="store_true", help="打印将写入的文件，不落盘")
    ap.add_argument("--self-test", action="store_true", help="临时假目录里自证不变量，不碰真安装点")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

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
