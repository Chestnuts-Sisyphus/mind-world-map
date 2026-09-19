#!/usr/bin/env python3
# 同步校验（零写盘）：本地 skill 编辑正本 → 仓库发布镜像的一致性闸门。
#
# 用法：
#   python tools/sync_check.py [正本目录 ...]
#   MINDMAP_SKILL_MASTERS="目录1;目录2" python tools/sync_check.py
#
# 口径：本地正本是编辑源，仓库是发布镜像；两者之间隔着 tools/preflight.py 里那张
# 发布面变换表（身份匿名化 + 本机路径通用化）。因此比对的是
# 「仓库文件 == 变换后的正本文件」——正本改了没发布、发布面漏了脱敏，都会报警。
# 退出码 0=一致（或本机没有任何正本，外部用户可忽略）；1=有不一致，stdout 点名文件。
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preflight import apply_publish_rules  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
SKILL_NAME = "mindmap-engineering"
DEFAULT_MASTER_RELATIVES = [
    (".claude", "skills"),
    (".qoder-cn", "skills"),
    (".qoder", "skills"),
]


def default_masters():
    home = Path.home()
    return [home.joinpath(*parts).joinpath(SKILL_NAME) for parts in DEFAULT_MASTER_RELATIVES]


def master_dirs(argv):
    """CLI 位置参数 > MINDMAP_SKILL_MASTERS（分号/冒号分隔）> 默认三处。"""
    if argv:
        return [Path(a).expanduser() for a in argv]
    env = os.environ.get("MINDMAP_SKILL_MASTERS", "").strip()
    if env:
        return [Path(p).expanduser() for p in env.replace(os.pathsep, ";").split(";") if p.strip()]
    return default_masters()


def private_rels() -> set:
    """.gitignore 中显式列出的 *.md 路径 = 有意不进公开包的私有文档。"""
    gitignore = REPO / ".gitignore"
    if not gitignore.is_file():
        return set()
    return {
        line.strip()
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip().endswith(".md") and not line.strip().startswith("#")
    }


def public_rels(root: Path) -> set:
    """公开文件集 = SKILL.md + references/ 下全部 md（与仓库侧同口径）。"""
    rels = set()
    if (root / "SKILL.md").is_file():
        rels.add("SKILL.md")
    refs = root / "references"
    if refs.is_dir():
        rels.update(p.relative_to(root).as_posix() for p in refs.rglob("*.md"))
    return rels


def published_bytes(path: Path) -> bytes:
    """读文本 → 套发布面变换 → 归一 LF。用于跨「正本/镜像」两种形态比对。"""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return apply_publish_rules(text).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv) -> int:
    private = private_rels()
    repo_rels = public_rels(REPO) - private
    if not repo_rels:
        print("仓库侧未发现任何公开文件，检查运行位置")
        return 1

    present, skipped = [], []
    for d in master_dirs(argv):
        (present if d.is_dir() else skipped).append(d)

    for d in skipped:
        print(f"跳过正本（目录不存在，可忽略）：{d}")
    if not present:
        print(f"未发现本地正本，外部用户可忽略本闸；仓库公开文件 {len(repo_rels)} 个已就位")
        return 0

    problems = []
    for local in present:
        local_rels = public_rels(local) - private
        for rel in sorted(repo_rels | local_rels):
            rp, lp = REPO / rel, local / rel
            if not rp.is_file():
                problems.append(f"{local} 有而仓库缺：{rel}")
            elif not lp.is_file():
                problems.append(f"仓库有而 {local} 缺：{rel}")
            elif digest(published_bytes(rp)) != digest(published_bytes(lp)):
                problems.append(f"发布面不一致：{rel}（{local} vs 仓库）")

    if problems:
        print("同步校验失败：")
        for p in problems:
            print(f"  - {p}")
        return 1
    tail = f"（另有 {len(skipped)} 处正本目录不存在，已跳过）" if skipped else ""
    print(f"一致：仓库 + {len(present)} 个本地 skill 正本，共 {len(repo_rels)} 个公开文件{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
