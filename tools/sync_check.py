#!/usr/bin/env python3
# 三处同步校验（零写盘）：比对本地 skill 编辑正本与仓库发布镜像的共享文件 SHA256。
# 用法：python tools/sync_check.py ；退出码 0=三处一致，1=有不一致（stdout 列出文件）。
import hashlib
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
LOCAL_DIRS = [
    Path.home() / ".qoder-cn" / "skills" / "mindmap-engineering",
    Path.home() / ".qoder" / "skills" / "mindmap-engineering",
]


def private_rels() -> set[str]:
    """.gitignore 中显式列出的 *.md 路径 = 有意不进公开包的私有文档。"""
    gitignore = REPO / ".gitignore"
    if not gitignore.is_file():
        return set()
    return {
        line.strip()
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip().endswith(".md") and not line.strip().startswith("#")
    }


def public_rels(root: Path) -> set[str]:
    rels = set()
    if (root / "SKILL.md").is_file():
        rels.add("SKILL.md")
    refs = root / "references"
    if refs.is_dir():
        rels.update(p.relative_to(root).as_posix() for p in refs.rglob("*.md"))
    return rels


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    problems = []
    private = private_rels()
    repo_rels = public_rels(REPO)
    if not repo_rels:
        print("仓库侧未发现任何公开文件，检查运行位置")
        return 1
    for local in LOCAL_DIRS:
        local_rels = public_rels(local) - private
        for rel in sorted(repo_rels | local_rels):
            rp, lp = REPO / rel, local / rel
            if not rp.is_file():
                problems.append(f"{local} 有而仓库缺：{rel}")
            elif not lp.is_file():
                problems.append(f"仓库有而 {local} 缺：{rel}")
            elif sha256(rp) != sha256(lp):
                problems.append(f"内容不一致：{rel}（{local} vs 仓库）")
    if problems:
        print("同步校验失败：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"三处一致：仓库 + {len(LOCAL_DIRS)} 个本地 skill 目录，共 {len(repo_rels)} 个公开文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
