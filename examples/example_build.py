#!/usr/bin/env python3
"""示例构建层：把 example_data.py 里的内容与计划表拼成一份真 .xmind，再用包内校验器自证。

跑法（在仓库根目录）：
    python examples/example_build.py                 # 构建 → 校验，产出 examples/out/example.xmind
    python examples/example_build.py --self-test     # 反证：故意把数据改坏一处，看闸是否拦得住

它演示的正是这个包主张的流水线：**内容在数据文件、结构在构建脚本、机器检查在闸门**。
成品 .xmind 是构建产物，不入版本库（见 .gitignore），要改图就改数据再重建。
"""
import argparse
import json
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT_DIR = HERE.parent
sys.path.insert(0, str(ROOT_DIR / "tools"))
sys.path.insert(0, str(HERE))

import validate_xmind as V  # noqa: E402
import example_data as D  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = HERE / "out" / "example.xmind"


def note_text(term):
    """一条笔记 = 一棵文字小树：顶格行是词条本身，用到的别的词条缩进两格挂在它下面。"""
    lines = [f"{term} {D.TERMS[term]}"]
    for dep in D.TERM_DEPS.get(term, []):
        lines.append(f"  {dep} {D.TERMS[dep]}")
    return "\n".join(lines)


def assert_coverage():
    """计划表与内容源必须严丝合缝：漏挂、多挂、拼错标题都在构建期就炸，不留到看图时。"""
    problems = []
    for block, kids in D.PLANS.items():
        found = next((b for b in D.TREE[1] if b[0] == block), None)
        if found is None:
            problems.append(f"计划表点了 {block}，内容源里没有这一支")
            continue
        actual = [c[0] for c in found[1]]
        if actual != kids:
            problems.append(f"{block} 的计划与实际不符：{kids} vs {actual}")
    unplanned = [b[0] for b in D.TREE[1] if b[0] not in D.PLANS]
    if unplanned:
        problems.append(f"内容源里有未经计划表声明的块：{unplanned}")
    if problems:
        raise SystemExit("构建中止（计划表覆盖断言未过）：" + "；".join(problems))


def build_topic(spec, counter, path):
    """递归把 [标题, [孩子]] 拼成 content.json 的 topic 形态，并按使用点附笔记。"""
    title, kids = spec[0], spec[1]
    counter[0] += 1
    topic = {"id": f"ex-{'-'.join(map(str, path))}-{counter[0]}", "title": title}
    notes = [note_text(term) for term in D.TERMS if term in title]
    if notes:
        body = "\n".join(notes)
        topic["notes"] = {"plain": {"content": body}, "realHTML": {"content": body}}
    if kids:
        topic["children"] = {"attached": [build_topic(k, counter, path + [i])
                                          for i, k in enumerate(kids)]}
    return topic


def build_sheet():
    root = build_topic(D.TREE, [0], [0])
    # 方向真源在 rootTopic.extensions：right-number 必须等于一级分支数，靠人记必翻车
    branches = len(root.get("children", {}).get("attached", []))
    root["extensions"] = [{"provider": "org.xmind.ui.map.unbalanced",
                           "content": [{"name": "right-number", "content": str(branches)}]}]
    return [{"id": "ex-sheet-1", "class": "map", "title": D.ROOT, "rootTopic": root,
             "topicPositioning": "free"}]


def write(out: Path, sheets):
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(sheets, ensure_ascii=False, separators=(",", ":"))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("content.json", payload)
        zf.writestr("metadata.json", json.dumps({"dataStructureVersion": "2",
                                                 "creator": {"name": "example_build"}}))
        zf.writestr("manifest.json", json.dumps(
            {"file-entries": {"content.json": {}, "metadata.json": {}}}))
    return out


def self_test():
    """反向接线证明：闸不在链上时，故意改坏的样例本应 exit 0——所以正证比绿字更要紧。"""
    ok = True
    original = D.TREE[1][0][1][0][0]

    def check(name, cond, extra=""):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + f"example/{name}{(' / ' + extra) if extra else ''}")
        ok = ok and bool(cond)

    sheets = build_sheet()
    check("计划表覆盖断言通过", True)
    check("构建出的图内容标准零违例", V.validate_map(sheets) == [],
          str([h["rule"] for h in V.validate_map(sheets)]))
    check("right-number 自动等于一级分支数",
          V.validate_map(sheets, exclude={"right-number"}) == [])

    # 旧示例自测：改标题长度违规
    try:
        D.TREE[1][0][1][0][0] = original + "明显超过七个字的组织节点标题"
        broken = build_sheet()
        hits = V.validate_map(broken)
        check("旧示例自测：标题超长被闸拦下",
              bool(hits) and any(h["rule"] == "tiered-length" for h in hits),
              str(sorted({h["rule"] for h in hits})))
    finally:
        D.TREE[1][0][1][0][0] = original
    check("复原后再次构建结果字节相同",
          json.dumps(build_sheet(), ensure_ascii=False) == json.dumps(build_sheet(), ensure_ascii=False))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="示例：数据层 + 构建层 → .xmind → 包内校验器自证")
    ap.add_argument("--self-test", action="store_true", help="反向证明：改坏数据必须被闸拦下")
    ap.add_argument("--out", default=str(OUT), help="产出路径（默认 examples/out/example.xmind）")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    assert_coverage()
    out = write(Path(args.out), build_sheet())
    print(f"已构建：{out}")
    hits, code = V.validate_file(out)
    for h in hits:
        print(f"  - {h['node']} {h['rule']} {h.get('detail', '')}")
    print(f"内容标准 {len(V.CHECKS)} 检：通过" if code == 0
          else f"内容标准 {len(V.CHECKS)} 检：{len(hits)} 项违例")
    return code


if __name__ == "__main__":
    sys.exit(main())
