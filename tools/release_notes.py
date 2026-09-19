#!/usr/bin/env python3
"""Release 正文抽取器（零写盘）：从 CHANGELOG.md 里取出某个版本对应章节的正文。

用法：
    python tools/release_notes.py v1.0.3              # 打印该版本的发布说明
    python tools/release_notes.py v1.0.3 --check      # 只判定有无对应段，不打印

口径：CHANGELOG 是唯一事实源，Release 正文由这里抽，抽不到就必须失败——
「有 tag 却没有 changelog 段」正是发布纪律想拦住的形态。
退出码：0=取到非空正文；1=没有对应段或正文为空。
"""
import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "CHANGELOG.md"

# 版本标题形如 `## v1.0.3 — 2026-09-19` 或 `## [1.0.3] - 2026-09-19`；[Unreleased] 单独一类
VERSION_HEADING = re.compile(r"^##\s+\[?(v?\d+\.\d+\.\d+)\]?\s*[—\-–].*$|^##\s+(v?\d+\.\d+\.\d+)\s*$")
UNRELEASED_HEADING = re.compile(r"^##\s+\[Unreleased\]", re.I)


def normalize(tag: str) -> str:
    return tag.strip().lstrip("vV")


def section_for(tag: str, text: str):
    """返回 (章节正文, 是否找到标题)。标题匹配 v 前缀可选。"""
    want = normalize(tag)
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = VERSION_HEADING.match(line.strip())
        if not m:
            continue
        if normalize(m.group(1) or m.group(2)) == want:
            start = i + 1
            break
    if start is None:
        return "", False
    body = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body).strip(), True


def unreleased_block(text: str) -> str:
    """[Unreleased] 段的正文，用于判定它是否为空（空段=还没攒条目）。"""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if UNRELEASED_HEADING.match(line.strip()):
            body = []
            for nxt in lines[i + 1:]:
                if nxt.startswith("## "):
                    break
                body.append(nxt)
            return "\n".join(body).strip()
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="从 CHANGELOG 抽 Release 正文")
    ap.add_argument("tag", help="要抽出版本号的 git tag，例如 v1.0.3")
    ap.add_argument("--check", action="store_true", help="只判定，不打印正文")
    ap.add_argument("--changelog", default=str(CHANGELOG), help="CHANGELOG 路径（测试用）")
    args = ap.parse_args()

    path = Path(args.changelog)
    if not path.is_file():
        print(f"CHANGELOG 不存在：{path}", file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8")
    body, found = section_for(args.tag, text)
    if not found:
        print(f"CHANGELOG 里没有 {args.tag} 对应的版本段，拒绝发布", file=sys.stderr)
        return 1
    if not body:
        print(f"{args.tag} 的版本段是空的，没有可发布的说明", file=sys.stderr)
        return 1
    if not args.check:
        print(body)
    else:
        print(f"OK：{args.tag} 有非空版本段（{len(body.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
