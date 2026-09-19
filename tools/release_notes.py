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

# 版本标题形如 `## v1.0.3 — 2026-09-19` 或 `## [1.0.3] - 2026-09-19`；[Unreleased] 单独一类。
# 版本号后必须是 `]` 或空白 + 分隔符：否则 `## v1.2.0-rc1 — 日期` 会被读成 v1.2.0 段，
# 预发布 tag 静默复用稳定版正文（实测过的误配形态，故钉紧）。
VERSION_HEADING = re.compile(
    r"^##\s+\[?(v?\d+\.\d+\.\d+)\]?(?:\s+[—–-]\s*|$)"
    r"|^##\s+\[?(v?\d+\.\d+\.\d+)\s*$",
    re.M,
)
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


def section_heading(tag: str, text: str) -> str:
    """版本段的标题行原文，取不到返回空串。"""
    want = normalize(tag)
    for line in text.splitlines():
        m = VERSION_HEADING.match(line.strip())
        if m and normalize(m.group(1) or m.group(2)) == want:
            return line.strip()
    return ""


def section_title(tag: str, text: str) -> str:
    """Release 标题的唯一来源：`vX.Y.Z — <小节描述性主题>`。

    小节标题约定 `## vX.Y.Z — YYYY-MM-DD — 主题`，日期之后的那截才是主题；只有日期
    （或什么都没有）时返回空串，由调用方拒绝发布——这正是 C3 的形态：`--title "$TAG"`
    把标题退化成 6 个字符，对外等于没有标题。
    """
    heading = section_heading(tag, text)
    if not heading:
        return ""
    m = VERSION_HEADING.match(heading)
    rest = (heading[m.end():] if m and m.end() else "")
    rest = re.sub(r"^[—–\-]+\s*", "", rest.strip())
    rest = re.sub(r"^\d{4}-\d{2}-\d{2}\s*[—–\-]*\s*", "", rest).strip()
    rest = rest.strip("—–- ").strip()
    version = normalize(tag)
    return f"v{version} — {rest}" if rest else ""


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


SELFTEST_DOC = """# Changelog

## [Unreleased]

- one pending item
- another pending item

## v1.2.0 — 2026-09-19 — capability closure round three

Lead paragraph explaining the release.

- **Added**: validator in package
- **Fixed**: gate blind spot

## v1.1.0 – 2026-09-18 — en dash separator variant

- only one item here

## [1.0.9] - 2026-09-17 - bracketed keep-a-changelog form

- bracketed body line

## v1.0.8 — 2026-09-16

## v1.2.0-rc1 — 2026-09-15 — prerelease must not shadow the stable section

- prerelease-only line
"""


def self_test() -> int:
    """检测器自证：全部用人造文本，不读真 CHANGELOG、不落盘，因此在仓库、安装点正本、
    干净 clone 三种布局下结论必须完全一致（本轮教训：靠布局的自测在安装点必红）。"""
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + f"release-notes/{name}")
        ok = ok and bool(cond)

    text = SELFTEST_DOC
    body, found = section_for("v1.2.0", text)
    check("em-dash heading parsed", found and body.startswith("Lead paragraph"))
    check("body stops at next section", "en dash separator" not in body and "prerelease" not in body)
    check("line count matches section", len(body.splitlines()) == 4)
    check("en-dash heading parsed", "only one item here" in section_for("v1.1.0", text)[0])
    check("bracketed form parsed", "bracketed body line" in section_for("v1.0.9", text)[0])
    check("hyphen-as-dash parsed", "capability closure" in section_heading("v1.2.0", text))
    empty_body, empty_found = section_for("v1.0.8", text)
    check("empty section found but rejected", empty_found and not empty_body)
    check("missing tag not invented", not section_for("v9.9.9", text)[1])
    check("unreleased block read", "one pending item" in unreleased_block(text))
    # 本包只发稳定版：预发布标题不进解析器，rc tag 因此拿不到自己的段，也就无法
    # 复用稳定版正文（收紧正则前它会冒充 v1.2.0，实测过的误配形态）。
    check("prerelease does not shadow stable", "prerelease-only line" not in body)
    check("prerelease heading is not a stable section", not section_for("v1.2.0-rc1", text)[1])
    check("prerelease tag needs its own section", not section_for("v1.2.1", text)[1])
    # 标题口径：版本号 + 描述性主题；只有日期 = 无主题 = 拒发
    check("title carries descriptive subject",
          section_title("v1.2.0", text) == "v1.2.0 — capability closure round three")
    check("title falls back to date-less subject",
          section_title("v1.0.9", text) == "v1.0.9 — bracketed keep-a-changelog form")
    check("date-only heading yields no title",
          section_title("v1.0.7", SELFTEST_DOC + "\n## v1.0.7 — 2026-09-15\n\n- x\n") == "")
    check("bump-only heading has no subject", section_title("v1.0.8", text) == "")
    check("missing tag has no title", section_title("v9.9.9", text) == "")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="从 CHANGELOG 抽 Release 正文与标题")
    ap.add_argument("tag", nargs="?", help="要抽出版本号的 git tag，例如 v1.0.3")
    ap.add_argument("--check", action="store_true", help="只判定，不打印正文")
    ap.add_argument("--title", action="store_true", help="打印发布标题（ vX.Y.Z — 主题 ）")
    ap.add_argument("--self-test", action="store_true", help="用人造 CHANGELOG 自证解析行为")
    ap.add_argument("--changelog", default=str(CHANGELOG), help="CHANGELOG 路径（测试用）")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.tag:
        print("缺少 tag 参数（或使用 --self-test）", file=sys.stderr)
        return 2

    path = Path(args.changelog)
    if not path.is_file():
        print(f"CHANGELOG 不存在：{path}", file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8")
    if args.title:
        title = section_title(args.tag, text)
        if not title:
            print(f"{args.tag} 的小节标题没有描述性主题，拒绝以裸版本号发布", file=sys.stderr)
            return 1
        print(title)
        return 0
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
