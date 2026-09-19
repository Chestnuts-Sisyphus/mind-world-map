#!/usr/bin/env python3
"""发布面预检闸（零写盘）：提交前扫描整个公开包，抓「本机痕迹 / 凭据形态 / 死链 /
私有件点名 / 双语章节结构 / 身份回归」六类问题。

用法：
    python tools/preflight.py                 # 扫全仓，0=干净
    python tools/preflight.py --self-test     # 每类注入一例人造违规，验证闸真的会响

输出只给「文件:行号 + 规则名」，绝不打印命中内容——扫描产物本身不得成为泄露载体。
退出码：0=无问题，1=有问题（或 self-test 有类不响）。
"""
import argparse
import getpass
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- 发布面变换表
# 本地正本保留原文，公开包由这张表确定性变换得到（身份匿名化 + 本机路径通用化）。
# sync_check 比对时同样先套这张表，因此「正本改了没发布」与「发布了没脱敏」都会报警。
LITERAL_RULES = [
    ("栗子", "作者"),
    ("[[cm-closure-mindmap-pipeline]]", "作者侧流水线记忆（未随包发布）"),
    ("[[tool-zero-friction-principle]]", "零摩擦工具原则（作者侧记忆，未随包发布）"),
    ("[[handoff-sys-0818-01-yuanben-tree]]", "作者侧交接文档（未随包发布）"),
    ("[[chestnut-calibration-mode]]", "作者侧口径校准记忆（未随包发布）"),
    ("[[atype-retest-gold-standard-r1-r4]]", "复测金标准记忆（作者侧，未随包发布）"),
]

# 盘符绝对路径（含用户目录段）→ 通用占位；保留项目内相对结构，只抹掉本机根。
REGEX_RULES = [
    (re.compile(r"(?<![\w:])[A-Za-z]:[/\\]+(?:Users[/\\][\w.~\- ]+[/\\])?(?:AI[/\\])?"), "<local-workdir>/"),
]

# 身份类关键词：公开包一旦回归即由本闸拦下（本地正本不受影响）。
IDENTITY_TERMS = ["栗子"]


def apply_publish_rules(text: str) -> str:
    """本地正本原文 → 公开包发布面文本。幂等：对已是发布面的文本无副作用。"""
    for src, dst in LITERAL_RULES:
        text = text.replace(src, dst)
    for pat, repl in REGEX_RULES:
        text = pat.sub(repl, text)
    return text


# ---------------------------------------------------------------- 检测规则
# 每条规则：(规则名, 编译好的正则)。命中输出为 `文件:行号 规则名`。
LOCAL_TRACE_RULES = [
    # 8.3 短名通用式（任意名 + ~数字）——必须夹在路径分隔符之间才算，避免数值区间误报
    ("short-83-name", re.compile(r"(?<=[/\\])[A-Za-z0-9_$.\-]{1,12}~\d(?=[/\\])")),
    # 盘符绝对路径；前置断言排除 https:// 这类 URL scheme 误伤
    ("drive-letter-path", re.compile(r"(?<![\w:])[A-Za-z]:[/\\][\w.~\- /\\]")),
    # 用户目录段（无盘符前缀的形态，如 /Users/xxx、/home/xxx 的手工残留）
    ("users-dir", re.compile(r"(?<![A-Za-z0-9])[/\\]Users[/\\]\w")),
]

CREDENTIAL_RULES = [
    ("token-ghp", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}\b")),
    ("token-github-pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("token-sk", re.compile(r"\bsk-[A-Za-z0-9]{16,}\b")),
    ("token-aws", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("token-slack", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    # 形如 password/token/api-key = 值的赋值（占位示例除外：值里含 < 或 xxx 视为占位）
    ("credential-assignment", re.compile(
        r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)\b\s*[:=]\s*"
        r"[\"'`]?[A-Za-z0-9/+_\-\.]{8,}[\"'`]?\s*$")),
]

PRIVATE_FILE_HINT = re.compile(r"\b([\w.\-]+)\.md\b")
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def tracked_text_files():
    """扫描范围 = 仓库内所有文本类跟踪文件（工具脚本自身承载规则字面量，排除之）；
    .gitignore 登记的私有文档不属于发布包，跳过其内容扫描（改由「私有件入包」检查拦截）。"""
    private = gitignored_doc_paths()
    out = []
    for p in sorted(REPO.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(REPO).as_posix()
        parts = set(p.relative_to(REPO).parts)
        if {".git", "__pycache__"}.intersection(parts) or "tools" in parts:
            continue
        if rel in private:
            continue
        if p.suffix.lower() not in {".md", ".txt", ".yml", ".yaml"} and p.name != "LICENSE":
            continue
        out.append((rel, p))
    return out


def check_private_present(existing=None):
    """被 .gitignore 排除的私有文档出现在仓库目录里 = 误拷入包（虽不被跟踪，仍是泄露隐患）。"""
    present = {rel for rel in gitignored_doc_paths() if (REPO / rel).is_file()} if existing is None else set(existing)
    return [f"{rel}:1 private-doc-in-package" for rel in sorted(present)]


def iter_public_md():
    for rel, p in tracked_text_files():
        if p.suffix.lower() != ".md":
            continue
        yield rel, p


def known_doc_stems():
    return {p.stem for _, p in tracked_text_files() if p.suffix.lower() == ".md"}


def gitignored_doc_paths():
    """.gitignore 中显式列出的 *.md 相对路径 = 有意留在本地的私有件。"""
    gi = REPO / ".gitignore"
    if not gi.is_file():
        return set()
    return {
        line.strip()
        for line in gi.read_text(encoding="utf-8").splitlines()
        if line.strip().endswith(".md") and not line.strip().startswith("#")
    }


def gitignored_doc_names():
    names = set()
    for rel in gitignored_doc_paths():
        names.add(Path(rel).name)
        names.add(Path(rel).stem)
    return names


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def scan_pattern(rel: str, text: str, rules):
    """逐行匹配；只报位置。"""
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pat in rules:
            if pat.search(line):
                hits.append(f"{rel}:{lineno} {name}")
    return hits


def check_local_trace(rel, text):
    return scan_pattern(rel, text, LOCAL_TRACE_RULES)


def check_identity(rel, text):
    rules = [(f"identity:{term}", re.compile(re.escape(term))) for term in IDENTITY_TERMS]
    return scan_pattern(rel, text, rules)


def check_credentials(rel, text):
    hits = scan_pattern(rel, text, CREDENTIAL_RULES)
    # 用户名出现在包内文件里也算凭据邻域泄露（本机账号名）
    user = ""
    try:
        user = getpass.getuser()
    except Exception:
        user = ""
    if user and len(user) > 3 and not user.lower().startswith("runner"):
        rules = [("local-username", re.compile(r"(?<![A-Za-z0-9])" + re.escape(user) + r"(?![A-Za-z0-9])"))]
        hits += scan_pattern(rel, text, rules)
    return hits


def check_links(rel, text):
    """相对链接与 [[wikilink]] 必须能在包内解析。"""
    hits = []
    here = REPO / rel
    stems = known_doc_stems()
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in WIKILINK.finditer(line):
            if m.group(1).strip() not in stems:
                hits.append(f"{rel}:{lineno} dead-wikilink")
        for m in MD_LINK.finditer(line):
            target = m.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = target.split("#")[0]
            if not clean:
                continue
            base = here.parent if clean.startswith(("/",)) is False else REPO
            resolved = (REPO / clean) if clean.startswith("/") else (base / clean)
            if not resolved.exists():
                hits.append(f"{rel}:{lineno} dead-relative-link")
    return hits


def check_private_mentions(rel, text):
    """公开文档点名了被 .gitignore 排除、外部取不到的私有件。"""
    names = gitignored_doc_names()
    if not names:
        return []
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in PRIVATE_FILE_HINT.finditer(line):
            if m.group(1) in names:
                hits.append(f"{rel}:{lineno} private-doc-mentioned")
    return hits


FRONTMATTER_KEYS = ["name", "description", "license", "metadata"]
FRONTMATTER_META_KEYS = ["author", "version", "homepage"]


def frontmatter_issues(block_text):
    """SKILL.md frontmatter 的五键检查（name/description/license + metadata.{author,version,homepage}）。"""
    hits = []
    for key in FRONTMATTER_KEYS:
        if not re.search(rf"^{key}:", block_text, re.M):
            hits.append(f"SKILL.md frontmatter 缺 {key}")
    meta_body = []
    in_meta = False
    for line in block_text.splitlines():
        if in_meta and re.match(r"^[ \t]+\S", line):
            meta_body.append(line)
            continue
        in_meta = bool(re.match(r"^metadata:\s*$", line))
    body = "\n".join(meta_body)
    for key in FRONTMATTER_META_KEYS:
        if not re.search(rf"^[ \t]+{key}:", body, re.M):
            hits.append(f"SKILL.md metadata 缺 {key}")
    return [f"SKILL.md:2 frontmatter-incomplete ({h})" for h in hits]


def non_ascii_hits(rel, text):
    """GitHub Actions YAML 里的非 ASCII 注释会让 workflow 静默失效——钉成机器闸。"""
    return [f"{rel}:{n} non-ascii-in-workflow"
            for n, line in enumerate(text.splitlines(), 1)
            if any(ord(c) > 127 for c in line)]


def check_skill_frontmatter():
    skill = REPO / "SKILL.md"
    if not skill.is_file():
        return []
    m = re.match(r"^---\n(.*?)\n---\n", read(skill), re.S)
    if not m:
        return ["SKILL.md:1 frontmatter-missing"]
    return frontmatter_issues(m.group(1))


def check_workflows_ascii():
    hits = []
    for rel, p in tracked_text_files():
        if p.suffix.lower() in {".yml", ".yaml"}:
            hits += non_ascii_hits(rel, read(p))
    return hits


def headings(text):
    """提取 1-3 级标题；跳过 ``` 围栏内的行（shell 注释不是标题）。"""
    out = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            out.append((len(m.group(1)), m.group(2).strip()))
    return out


def check_bilingual_structure():
    """README 与中文 README 的章节层级序列必须一一对应。"""
    en, zh = REPO / "README.md", REPO / "README.zh-CN.md"
    if not (en.is_file() and zh.is_file()):
        return []
    a = [lv for lv, _ in headings(read(en))]
    b = [lv for lv, _ in headings(read(zh))]
    if a == b:
        return []
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return [f"README.md vs README.zh-CN.md heading#{i + 1} bilingual-structure-drift"]
    extra = "README.md" if len(a) > len(b) else "README.zh-CN.md"
    return [f"{extra} 多出 {abs(len(a) - len(b))} 个标题 bilingual-structure-drift"]


# ---------------------------------------------------------------- 人造违规样本
# self-test 用：每类一例，喂进对应检测函数，断言闸会响（零写盘，不落任何文件）。
SYNTH = "a/b.md"
SELFTEST_CASES = [
    ("local-trace", check_local_trace, "样例路径 C:" + chr(92) + "Users" + chr(92) + "ADM" + "INI~1" + chr(92) + "t.txt"),
    ("identity", check_identity, "本节由" + "栗" + "子定稿"),
    ("credentials", check_credentials, "export access_token = " + "a" * 24),
    ("dead-link", check_links, "参见 [[no-such-doc-here]] 与 [文本](tools/nope.py)"),
    ("private-doc", check_private_mentions, "详见 " + "connectome" + "-cm-core-definition.md"),
]


def self_test():
    ok = True
    for name, fn, sample in SELFTEST_CASES:
        try:
            hits = fn(SYNTH, sample)
        except Exception as exc:  # 检测器自身异常也算不响
            print(f"FAIL {name}: 检测器异常 {type(exc).__name__}")
            ok = False
            continue
        if hits:
            print(f"PASS {name}: 人造违规被拦（位置已点名）")
        else:
            print(f"FAIL {name}: 人造违规未触发")
            ok = False
    # 双语结构闸用两个内存文档自证
    en_lv = [lv for lv, _ in headings("# A\n## B\n")]
    zh_lv = [lv for lv, _ in headings("# A\n")]
    print(("PASS" if en_lv != zh_lv else "FAIL") + " bilingual-structure: 人造层级差被识别")
    ok = ok and en_lv != zh_lv

    # 私有件误拷入包：注入一个「仓库里存在」的路径，不碰磁盘
    sample_private = next(iter(gitignored_doc_paths()), "x.md")
    hits = check_private_present([sample_private])
    print(("PASS" if hits else "FAIL") + " private-in-package: 人造误拷被拦（位置已点名）")
    ok = ok and bool(hits)

    # 发布面变换表：必须生效且幂等（同一张表被 sync_check 与发布脚本共用）
    src = "栗子定的标准见 [[cm-closure-mindmap-pipeline]]，落盘于 D:/AI/HERMES/a.md"
    once = apply_publish_rules(src)
    twice = apply_publish_rules(once)
    clean = ("栗" not in once) and ("[[cm-" not in once) and (":/" not in once.replace("https://", ""))
    print(("PASS" if once == twice else "FAIL") + " publish-rules: 幂等")
    print(("PASS" if clean else "FAIL") + " publish-rules: 人造原文经变换后三类痕迹均消失")
    ok = ok and once == twice and clean

    # frontmatter 五键：注入一个只有 name/description 的块
    hits = frontmatter_issues("name: x\ndescription: y\n")
    print(("PASS" if hits else "FAIL") + f" frontmatter: 人造缺键块被拦（{len(hits)} 项）")
    ok = ok and len(hits) == 5

    # workflow YAML 非 ASCII：注入一行中文注释
    hits = non_ascii_hits(".github/workflows/ci.yml", "# comment ok\n# 中文注释\n")
    print(("PASS" if hits else "FAIL") + " workflow-ascii: 人造非 ASCII 行被点名")
    ok = ok and len(hits) == 1
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="公开包发布面预检（零写盘）")
    ap.add_argument("--self-test", action="store_true", help="注入人造违规验证每类检测会响")
    ap.add_argument("--only", metavar="RULE", help="只跑指定规则名前缀，便于定位")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    findings = []
    for rel, path in iter_public_md():
        text = read(path)
        findings += check_local_trace(rel, text)
        findings += check_identity(rel, text)
        findings += check_credentials(rel, text)
        findings += check_links(rel, text)
        findings += check_private_mentions(rel, text)
    findings += check_bilingual_structure()
    findings += check_private_present()
    findings += check_skill_frontmatter()
    findings += check_workflows_ascii()

    # 非 md 的发布文件（LICENSE / yml 配置）只跑泄露类三检
    for rel, path in tracked_text_files():
        if path.suffix.lower() == ".md":
            continue
        text = read(path)
        findings += check_local_trace(rel, text)
        findings += check_credentials(rel, text)
        findings += check_identity(rel, text)

    if args.only:
        findings = [f for f in findings if args.only in f]

    findings = sorted(set(findings))
    if findings:
        print(f"发布面预检失败：{len(findings)} 项")
        for f in findings:
            print(f"  - {f}")
        return 1
    n = len(list(iter_public_md())) + 1
    print(f"发布面预检通过：全部规则零命中，已扫 {n} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
