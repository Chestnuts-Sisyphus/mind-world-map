#!/usr/bin/env python3
"""成品校验闸（交付闸第 1 条所说的 validate_map 在包内的落点）。

解 `.xmind` 里的 content.json，对成品树跑「内容标准最低集」六项机器检查：

1. banned-punctuation —— 标题禁标点（`：·→—/，、；。！？`）
2. tiered-length      —— 分级字数：组织节点（有孩子）2-7，叶子节点 2-12
3. first-level-budget —— root 直系一级分支 ≤9
4. fanout             —— 单节点子点数 ≤13
5. note-invariants    —— 笔记结构不变量：行形态 / 顶格词名在标题 / 一词一次 / 依赖链闭无环
6. right-number       —— rootTopic.extensions 的 right-number 与一级分支数一致

用法：
    python tools/validate_xmind.py <文件.xmind>            # 0=全过，1=有违例
    python tools/validate_xmind.py <文件.xmind> --json     # 机器可读输出
    python tools/validate_xmind.py <文件.xmind> --quiet    # 只报计数
    python tools/validate_xmind.py --self-test             # 合成夹具自证六检

它**不查**官方 `xmind validate` 管的结构五类（id 唯一、range、summary 配对、关系端点、
theme 角色）——那条线由 CLI 守，本器只守内容标准，两者相加才是完整验收线。

输出纪律：违例只给「节点 ID + 规则名 + 至多 40 字标题摘句」。摘句是定位用的，
不是命中原文的回显通道——标准检查项违例本来就只涉及标题片段，不含任何本机痕迹。
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BANNED_PUNCT = "：·→—/，、；。！？"
ORG_MIN, ORG_MAX = 2, 7
LEAF_MIN, LEAF_MAX = 2, 12
FIRST_LEVEL_BUDGET = 9
FANOUT_MAX = 13
ASCII_RUN = re.compile(r"[0-9A-Za-z_.\-+/]+")
EXCERPT = 40


# ------------------------------------------------------------------ 读包
def read_content(path: Path):
    """content.json 是新版 Xmind 的真数据（content.xml 只是占位警告页）。"""
    if not path.is_file():
        raise ValueError(f"文件不存在：{path}")
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if "content.json" not in names:
            raise ValueError("不是有效的 .xmind：包里缺 content.json")
        data = json.loads(zf.read("content.json").decode("utf-8"))
    if not isinstance(data, list):
        raise ValueError("content.json 顶层必须是 sheet 数组")
    return data


def attached(topic):
    kids = (topic.get("children") or {}).get("attached") or []
    return [k for k in kids if isinstance(k, dict)]


def walk(topic, depth=0):
    """先序遍历，产出 (topic, depth)。depth=0 即该表的根。"""
    yield topic, depth
    for kid in attached(topic):
        yield from walk(kid, depth + 1)


def title_units(title: str) -> int:
    """字数口径：CJK 每字算 1，连续 ASCII 串算 1 单位（与构建期闸门同一把尺）。"""
    collapsed = ASCII_RUN.sub("A", title)
    return len([c for c in collapsed if not c.isspace()])


def is_ascii_title(title: str) -> bool:
    return bool(title) and all(ord(c) < 128 for c in title)


def violation(topic, rule, note=""):
    tid = str(topic.get("id") or "?")
    title = str(topic.get("title") or "")
    excerpt = title if len(title) <= EXCERPT else title[:EXCERPT] + "…"
    return {"node": tid, "rule": rule, "detail": note, "excerpt": excerpt}


# ------------------------------------------------------------------ 六项检查
def check_punctuation(sheet_root):
    hits = []
    for topic, depth in walk(sheet_root):
        title = str(topic.get("title") or "")
        found = sorted({c for c in title if c in BANNED_PUNCT})
        if found:
            hits.append(violation(topic, "banned-punctuation", f"含 {len(found)} 个禁用标点"))
    return hits


def check_tiered_length(sheet_root):
    hits = []
    for topic, depth in walk(sheet_root):
        title = str(topic.get("title") or "")
        if depth == 0:
            continue  # 根口号是主体名，历史上允许整句（样例即「We shall never surrender.」）
        if is_ascii_title(title):
            continue  # 纯 ASCII 标题=词条表键/代号，字数豁免（可读性由黑话闸管）
        kids = attached(topic)
        lo, hi = (ORG_MIN, ORG_MAX) if kids else (LEAF_MIN, LEAF_MAX)
        n = title_units(title)
        if not lo <= n <= hi:
            kind = "组织节点" if kids else "叶子"
            hits.append(violation(topic, "tiered-length", f"{kind} {n} 字，应 {lo}-{hi}"))
    return hits


def check_first_level_budget(sheet_root):
    kids = attached(sheet_root)
    if len(kids) > FIRST_LEVEL_BUDGET:
        return [violation(sheet_root, "first-level-budget", f"一级分支 {len(kids)} 支，超 {FIRST_LEVEL_BUDGET}")]
    return []


def check_fanout(sheet_root):
    hits = []
    for topic, depth in walk(sheet_root):
        kids = attached(topic)
        if len(kids) > FANOUT_MAX:
            hits.append(violation(topic, "fanout", f"子节点 {len(kids)} 个，超 {FANOUT_MAX}"))
    return hits


NOTE_HEAD = 0


def note_lines(topic):
    """返回 [(缩进空格数, 词名, 整行)]，取不到笔记返回空。"""
    notes = topic.get("notes") or {}
    plain = ((notes.get("plain") or {}).get("content") or "").strip("\n")
    if not plain:
        return []
    out = []
    for line in plain.splitlines():
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        term = line.strip().split(maxsplit=1)[0]
        out.append((indent, term, line.strip()))
    return out


def check_note_invariants(sheet_root):
    """四不变量：行形态 / 顶格词名在标题 / 一词一次 / 词条依赖链闭且无环。"""
    hits = []
    heads = {}
    for topic, depth in walk(sheet_root):
        lines = note_lines(topic)
        if not lines:
            continue
        title = str(topic.get("title") or "")
        if lines[0][0] != NOTE_HEAD:
            hits.append(violation(topic, "note-invariants", "首行未顶格"))
        for indent, term, _line in lines:
            if indent % 2 or "\t" in _line[:len(_line) - len(_line.lstrip())]:
                hits.append(violation(topic, "note-invariants", f"缩进不合规（{term}）"))
        seen = {}
        for _indent, term, _line in lines:
            seen[term] = seen.get(term, 0) + 1
        dup = [t for t, c in seen.items() if c > 1]
        if dup:
            hits.append(violation(topic, "note-invariants", f"一词出现多次（{len(dup)} 个）"))
        head = lines[0][1]
        if head and head not in title:
            hits.append(violation(topic, "note-invariants", f"顶格词条「{head[:EXCERPT]}」不在标题里"))
        heads.setdefault(head, "\n".join(l for _i, _t, l in lines))

    # 依赖图：只连词条表里真实存在的词（否则等于要求释义不得用到任何未定义词，过严）
    edges = {}
    for head, text in heads.items():
        deps = set()
        for other in heads:
            if other == head or not other:
                continue
            pat = rf"\b{re.escape(other)}" if is_ascii_title(other) else re.escape(other)
            if re.search(pat, text):
                deps.add(other)
        edges[head] = deps

    state = {}

    def visit(node, stack):
        state[node] = 1
        for nxt in edges.get(node, ()):
            if state.get(nxt) == 1:
                cycle = stack[stack.index(nxt):] + [nxt]
                return cycle
            if state.get(nxt) is None:
                found = visit(nxt, stack + [nxt])
                if found:
                    return found
        state[node] = 2
        return None

    for head in heads:
        state.setdefault(head, None)
    for head in list(heads):
        if state[head] is None:
            cycle = visit(head, [head])
            if cycle:
                pseudo = {"id": f"term-chain:{cycle[0]}"}
                hits.append(violation(pseudo, "note-invariants",
                                      f"词条依赖成环（长度 {len(cycle)}）"))
    return hits


def check_right_number(sheet_root):
    kids = attached(sheet_root)
    expected = len(kids)
    value = None
    for ext in sheet_root.get("extensions") or []:
        if not isinstance(ext, dict):
            continue
        for item in ext.get("content") or []:
            if isinstance(item, dict) and item.get("name") == "right-number":
                value = str(item.get("content") or "")
    if value is None:
        return [violation(sheet_root, "right-number", "缺 right-number 声明")]
    if value != str(expected):
        return [violation(sheet_root, "right-number", f"right-number={value}，一级分支={expected}")]
    return []


CHECKS = [
    ("banned-punctuation", check_punctuation),
    ("tiered-length", check_tiered_length),
    ("first-level-budget", check_first_level_budget),
    ("fanout", check_fanout),
    ("note-invariants", check_note_invariants),
    ("right-number", check_right_number),
]


def validate_sheet(sheet_root, exclude=()):
    hits = []
    for name, fn in CHECKS:
        if name in exclude:
            continue
        hits += fn(sheet_root)
    return hits


def validate_map(sheets, exclude=()):
    hits = []
    for sheet in sheets:
        root = sheet.get("rootTopic")
        if not isinstance(root, dict):
            hits.append({"node": f"sheet:{sheet.get('id', '?')}", "rule": "sheet-missing-root",
                         "detail": "表里没有 rootTopic", "excerpt": ""})
            continue
        hits += validate_sheet(root, exclude)
    return hits


def validate_file(path: Path, exclude=()):
    try:
        sheets = read_content(path)
    except (ValueError, json.JSONDecodeError, zipfile.BadZipFile, OSError) as exc:
        return ([{"node": str(path.name), "rule": "unreadable-xmind",
                  "detail": str(exc)[:EXCERPT], "excerpt": ""}], 2)
    hits = validate_map(sheets, exclude)
    return hits, (1 if hits else 0)


# ------------------------------------------------------------------ 夹具与自测
def node(title, children=None, notes=None, extra=None):
    topic = {"id": f"t-{abs(hash((title, str(children)))) % 10**8}", "title": title}
    if children:
        topic["children"] = {"attached": children}
    if notes:
        topic["notes"] = {"plain": {"content": notes}, "realHTML": {"content": notes}}
    if extra:
        topic.update(extra)
    return topic


def ext(right_number=None):
    if right_number is None:
        return {}
    return {"extensions": [{"provider": "org.xmind.ui.map.unbalanced",
                            "content": [{"name": "right-number", "content": str(right_number)}]}]}


# 合规夹具：两个一级支，一支带词条笔记（顶格词就在标题里，子条目挂在引入者下面）
GOOD_NOTE = "词条闸门 图里非日常词的释义表，随标题出现在使用点\n闸门 机器拦违规的那道检查"
GOOD = lambda: node("示例导图", [
    node("词条闸门", [node("释义全附"), node("使用点挂上")], notes=GOOD_NOTE),
    node("验收块", [node("先跑校验器"), node("红点不许盖")]),
], extra=ext(2))


def one_child(child, right=1):
    return node("根题", [child], extra=ext(right))


# 每个违例夹具：(用例名, 造法, 期望定向命中的规则名)
FIXTURES = [
    ("标点违例", lambda: one_child(node("这里：带冒号")), "banned-punctuation"),
    ("组织节点超长", lambda: one_child(node("这个组织节点的标题明显超过七个字上限",
                                        [node("孩子")])), "tiered-length"),
    ("一级预算超支", lambda: node("根题", [node(f"分支{i}") for i in range(10)],
                             extra=ext(10)), "first-level-budget"),
    ("扇出超上限", lambda: one_child(node("子块", [node(f"叶子{i}") for i in range(14)])),
     "fanout"),
    ("顶格词不在标题", lambda: one_child(node("验收块", [node("先跑校验器")],
                                         notes="陌生词条 这个词根本没出现在标题里")),
     "note-invariants"),
    ("缩进不合规", lambda: one_child(node("词条闸门", [node("释义全附")],
                                      notes="词条闸门 顶格行\n   闸门 缩进三个空格不合规")),
     "note-invariants"),
    ("一词出现两次", lambda: one_child(node("词条闸门", [node("释义全附")],
                                       notes="词条闸门 顶格行\n闸门 第一次\n闸门 第二次")),
     "note-invariants"),
    ("词条依赖成环", lambda: node("根题", [
        node("甲块", [node("说明一")], notes="甲块 解释里指向乙块那条"),
        node("乙块", [node("说明二")], notes="乙块 解释里又指回甲块那条"),
    ], extra=ext(2)), "note-invariants"),
    ("right-number 不符", lambda: node("根题", [node("分支一"), node("分支二")],
                                   extra=ext(1)), "right-number"),
    ("缺 right-number", lambda: node("根题", [node("分支一")]), "right-number"),
]


def sheets_of(root):
    return [{"id": "s1", "class": "map", "title": "sheet1", "rootTopic": root}]


def write_xmind(path: Path, root):
    """按新版 Xmind 的最小包结构打包：content.json 是真数据，content.xml 只是占位警告页。"""
    payload = json.dumps(sheets_of(root), ensure_ascii=False).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("content.json", payload)
        zf.writestr("metadata.json", json.dumps({"creator": {"name": "validate_xmind self-test"}}))
        zf.writestr("manifest.json", json.dumps({"file-entries": {"content.json": {}, "metadata.json": {}}}))
    return path


def fixture_map():
    """用例名 → (造法, 期望规则)，供 --emit-fixture 与自测共用同一份定义。"""
    return {label: (make, rule) for label, make, rule in FIXTURES}


def self_test():
    """六检各自的正例（人造违例必响）+ 定向例（只响该响的那一检）+ 阴性例（合规图全绿）
    + 反向接线证明（把那一检从注册表摘掉，对应用例必须变绿）。内存与 .xmind 文件两条入口
    都跑，因此 zip 往返也被覆盖；全部落在临时目录，与运行布局无关。"""
    ok = True

    def check(name, cond, extra=""):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + f"validate/{name}{(' / ' + extra) if extra else ''}")
        ok = ok and bool(cond)

    check("合规夹具全绿", validate_map(sheets_of(GOOD())) == [],
          f"实际 {len(validate_map(sheets_of(GOOD())))} 项")

    for label, make, rule in FIXTURES:
        hits = validate_map(sheets_of(make()))
        fired = [h for h in hits if h["rule"] == rule]
        others = sorted({h["rule"] for h in hits if h["rule"] != rule})
        check(f"正例/{label}", bool(fired), f"{len(fired)} 项命中")
        check(f"定向/{label}", not others, f"顺带命中 {others}" if others else "")
        check(f"反向接线/{label}", validate_map(sheets_of(make()), exclude={rule}) == [])

    global CHECKS
    saved = CHECKS
    try:
        CHECKS = []
        empty = validate_map(sheets_of(GOOD()))
        check("反向接线/注册表清空后无人拦", validate_map(sheets_of(fixture_map()[u"标点违例"][0]())) == [])
    finally:
        CHECKS = saved
    check("恢复注册表后仍能拦", not empty and bool(
        validate_map(sheets_of(node("根题", [node("分支一")])))))

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        good_file = write_xmind(Path(td) / "good.xmind", GOOD())
        hits, code = validate_file(good_file)
        check("文件入口/合规图 exit 0", code == 0 and not hits)
        bad_file = write_xmind(Path(td) / "bad.xmind", fixture_map()["扇出超上限"][0]())
        hits, code = validate_file(bad_file)
        check("文件入口/违例图 exit 1 且点名规则",
              code == 1 and any(h["rule"] == "fanout" for h in hits))
        notzip = Path(td) / "not-zip.xmind"
        notzip.write_bytes(b"plain text, not a zip")
        hits, code = validate_file(notzip)
        check("文件入口/坏包不静默通过", code == 2 and hits[0]["rule"] == "unreadable-xmind")
        missing = Path(td) / "nope.xmind"
        hits, code = validate_file(missing)
        check("文件入口/文件不存在也报错", code == 2)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="导图成品内容标准校验闸（交付闸第 1 条的包内落点）")
    ap.add_argument("path", nargs="?", help="要验的 .xmind 文件")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--quiet", action="store_true", help="只报计数")
    ap.add_argument("--only", metavar="RULE", help="只跑指定规则名")
    ap.add_argument("--self-test", action="store_true", help="合成夹具自证六检")
    ap.add_argument("--list-fixtures", action="store_true", help="列出内置夹具名")
    ap.add_argument("--emit-fixture", metavar="NAME", help="把指定夹具打成 .xmind 供查看")
    ap.add_argument("--out", default=None, help="--emit-fixture 的输出路径")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.list_fixtures:
        print(*(["good"] + [label for label, _m, _r in FIXTURES]), sep=chr(10))
        return 0
    if args.emit_fixture:
        import tempfile
        name = args.emit_fixture
        if name == "good":
            root = GOOD()
        elif name in fixture_map():
            root = fixture_map()[name][0]()
        else:
            print(f"没有这个夹具：{name}（用 --list-fixtures 看清单）", file=sys.stderr)
            return 2
        out = Path(args.out) if args.out else Path(tempfile.gettempdir()) / f"{name}.xmind"
        write_xmind(out, root)
        print(f"已写出夹具：{out}")
        hits, code = validate_file(out)
        for h in hits:
            print(f"  - {h['node']} {h['rule']} {h.get('detail', '')}")
        return code
    if not args.path:
        print("缺少 .xmind 路径（或使用 --self-test）", file=sys.stderr)
        return 2

    hits, code = validate_file(Path(args.path))
    if args.only:
        hits = [h for h in hits if h["rule"] == args.only]
    if args.json:
        print(json.dumps({"path": args.path, "violations": hits,
                          "count": len(hits)}, ensure_ascii=False, indent=2))
    elif not hits:
        print(f"通过：{args.path} 六项内容标准零违例")
    else:
        if not args.quiet:
            print(f"未通过：{args.path} 共 {len(hits)} 项违例")
            for h in hits:
                detail = f" {h['detail']}" if h.get("detail") else ""
                excerpt = f"｜{h['excerpt']}" if h.get("excerpt") else ""
                print(f"  - {h['node']} {h['rule']}{detail}{excerpt}")
        else:
            print(f"未通过：{len(hits)} 项")
    return 0 if not hits else code


if __name__ == "__main__":
    sys.exit(main())
