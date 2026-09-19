#!/usr/bin/env python3
"""发布面预检闸（零写盘）：提交前扫描整个公开包，抓「本机痕迹 / 本机网络细节 /
凭据形态 / 个人标识形态 / 死链 / 私有件点名 / 双语章节结构 / 身份回归 /
包外脚本命令引用」九类问题。

用法：
    python tools/preflight.py                 # 扫全仓，0=干净
    python tools/preflight.py --self-test     # 每类注入一例人造违规，验证闸真的会响

同一道闸也可从本地 skill 正本目录运行（tools/ 已随包同步到安装点）：扫描前先套
发布面变换表，因此正本里的原文身份词与盘符路径会先被变换掉，剩下的才是真泄露。

输出只给「文件:行号 + 规则名」，绝不打印命中内容——扫描产物本身不得成为泄露载体。
退出码：0=无问题，1=有问题（或 self-test 有类不响）。
"""
import argparse
import getpass
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_notes import UNRELEASED_HEADING, VERSION_HEADING, section_for  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

def _decode_terms(text: str) -> str:
    """把清单/规则里以 \\uXXXX 转义存放的字面量解出来。
    公开包里因此不承载身份词原文——词表本身也是发布面的一部分。"""
    return text.encode("utf-8", "backslashreplace").decode("unicode_escape") if "\\u" in text else text


# ---------------------------------------------------------------- 发布面变换表
# 本地正本保留原文，公开包由这张表确定性变换得到（身份匿名化 + 本机路径通用化）。
# sync_check 比对时同样先套这张表，因此「正本改了没发布」与「发布了没脱敏」都会报警。
# 身份类字面量以 \uXXXX 转义存放，见 _decode_terms。
LITERAL_RULES = [
    (_decode_terms("\\u6817\\u5b50"), "作者"),
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

# 身份类词表：不写死在代码里，改由人工审词清单 tools/identity-terms.tsv 承载
# （block=命中即失败；exempt=命中不报但必须留理由）。加词/改判都改那张表，不改代码。
IDENTITY_TERMS_FILE = Path(__file__).resolve().parent / "identity-terms.tsv"


def load_identity_terms(path=None):
    """解析审词清单，返回 (block 词, exempt 词)。清单缺失或无可判定行=直接报错：
    「词表读不到」绝不能退化成「没有需要拦的词」。"""
    terms_file = IDENTITY_TERMS_FILE if path is None else Path(path)
    if not terms_file.is_file():
        raise FileNotFoundError(f"身份审词清单缺失：{terms_file}")
    blocked, exempted = [], []
    for line in terms_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [c.strip() for c in line.split("\t")]
        if len(parts) < 3 or not parts[1]:
            continue
        verdict, term = parts[0].lower(), _decode_terms(parts[1])
        if verdict == "block":
            blocked.append(term)
        elif verdict == "exempt":
            exempted.append(term)
    if not blocked and not exempted:
        raise ValueError(f"身份审词清单无任何可判定行：{terms_file}")
    return blocked, exempted


IDENTITY_BLOCK_TERMS, IDENTITY_EXEMPT_TERMS = load_identity_terms()


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

# 本机网络细节：回环端点与代理端口都是「这台机器」的指纹，与本机路径同级处理。
# 端口按形态拦（代理语境内 4 位以上数字），不写死具体端口号——否则闸退化成单点黑名单。
LOCAL_NETWORK_RULES = [
    ("loopback-endpoint", re.compile(
        r"(?:127\.0\.0\.1|\blocalhost\b|0\.0\.0\.0|\[?::1\]?)(?:[:：]\s*\d{2,5})?")),
    ("local-proxy-port", re.compile(
        r"(?i)(?:proxy|proxies|clash|v2ray|surge|shadowsocks|socks|代理|端口)[^\n]{0,8}?\b\d{4,5}\b")),
]

# 个人标识形态：邮箱（含 @ 的账号形态）。占位与noreply 域名不报，文档示例才能留。
EMAIL_PLACEHOLDER = re.compile(r"(?i)@(?:example\.(?:com|org|net)|localhost|noreply\.|gitlab\.)")
PERSONAL_IDENTITY_RULES = [
    # 域名最后一段必须是纯字母 TLD：npm 的 pkg@1.2.3 形态不是邮箱，实测会假阳性
    ("personal-email", re.compile(
        r"\b[A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9][A-Za-z0-9\-]*(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}\b")),
]

# 包外脚本命令引用：文档里写成可执行命令的 `python X.py`，脚本必须是本包发布物；
# 否则同一行须显式标注「非本包发布物」，让读者知道这条命令不在包里。
PYTHON_CMD_REF = re.compile(r"\bpython[3]?\s+([A-Za-z0-9_./\\:\-<>]+\.py)")
NON_PACKAGE_MARKERS = ("非本包发布物", "未随包发布", "not shipped with this package")


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


def private_present_hits(present):
    """私有件相对路径集合 → 位置清单。刻意做成不依赖目录布局的纯函数，
    好让 --self-test 在仓库与安装点两种布局下都能自证这条检测会响。"""
    return [f"{rel}:1 private-doc-in-package" for rel in sorted(present)]


def check_private_present(existing=None):
    """被 .gitignore 排除的私有文档出现在仓库目录里 = 误拷入包（虽不被跟踪，仍是泄露隐患）。
    安装点视角（无 .gitignore）下私有件留在正本里是设计口径，不做此项检查。"""
    if not is_repo_layout():
        return []
    present = {rel for rel in gitignored_doc_paths() if (REPO / rel).is_file()} if existing is None else set(existing)
    return private_present_hits(present)


def iter_public_md():
    for rel, p in tracked_text_files():
        if p.suffix.lower() != ".md":
            continue
        yield rel, p


def known_doc_stems():
    return {p.stem for _, p in tracked_text_files() if p.suffix.lower() == ".md"}


# 与仓库 .gitignore 同源的私有件清单：安装点目录没有 .gitignore，靠这份常量识别私有文档。
LOCAL_PRIVATE_RELS = [
    "QODER-MIGRATION.md",
    "references/memory/cm-closure-mindmap-pipeline.md",
    "references/memory/cm-zhongshen-mindmap-delivered.md",
    "references/memory/connectome-cm-core-definition.md",
    "references/memory/connectome-mindmap-project.md",
]


def is_repo_layout():
    """有 .gitignore = 发布镜像仓库；没有 = 本地 skill 正本目录（安装点视角）。"""
    return (REPO / ".gitignore").is_file()


def gitignored_doc_paths(repo=None):
    """.gitignore 中显式列出的 *.md 相对路径 = 有意留在本地的私有件。
    安装点目录无 .gitignore，退回用 LOCAL_PRIVATE_RELS 同口径识别。
    repo 参数供发布器的临时假仓库自测使用，默认取当前运行布局。"""
    repo = REPO if repo is None else Path(repo)
    gi = repo / ".gitignore"
    if not gi.is_file():
        return set(LOCAL_PRIVATE_RELS)
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
    """规则名固定为 identity-term：被跟踪词本身绝不进输出（扫描产物不得含命中原文）。"""
    rules = [("identity-term", re.compile(re.escape(term))) for term in IDENTITY_BLOCK_TERMS]
    return scan_pattern(rel, text, rules)


def check_local_network(rel, text):
    return scan_pattern(rel, text, LOCAL_NETWORK_RULES)


def check_personal_identity(rel, text):
    """邮箱形态的个人标识：占位/noreply 域名放行，其余一律点名。"""
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in PERSONAL_IDENTITY_RULES[0][1].finditer(line):
            if not EMAIL_PLACEHOLDER.search(m.group(0)):
                hits.append(f"{rel}:{lineno} personal-email")
                break
    return hits


def check_external_script_ref(rel, text):
    """文档里的 `python X.py` 必须指向包内脚本，否则同一行须标注非本包发布物。
    只点名行号，不回显命令内容。"""
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in PYTHON_CMD_REF.finditer(line):
            script = m.group(1).replace("\\", "/").lstrip("./")
            if (REPO / script).is_file():
                continue
            if any(marker in line for marker in NON_PACKAGE_MARKERS):
                continue
            hits.append(f"{rel}:{lineno} external-script-ref")
    return hits


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


ROOT_TOKEN = "mind-world-map/"
README_FILES = ("README.md", "README.zh-CN.md")
INSIDE_HEADING = re.compile(r"(?i)what's inside|仓库里有什么")
BOX_CHARS = re.compile(r"[├└│─┌┐└┘]")


def git_tracked_files():
    """跟踪文件集 = README 承诺的对照面。取不到（非仓库/无 git）返回空，检查随之跳过。"""
    try:
        out = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=30)
    except Exception:
        return []
    return [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]


def _join_path(parts):
    out = ""
    for part in parts:
        if not out or out.endswith("/"):
            out += part
        else:
            out += "/" + part
    return out


def tree_claims(text):
    """目录树围栏块里的路径承诺：去注释与框线，按缩进还原层级拼成完整路径。
    不还原层级会把 `pitfalls.md` 当根路径，整棵树都会误报；同一行的多个兄弟路径
    （`README.md / README.zh-CN.md`）只能各自成一条，括号里的是注解不是路径。"""
    claims, stack, in_fence = [], [], False
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            continue
        marker = min((line.find(ch) for ch in ("├", "└") if ch in line), default=-1)
        if marker < 0:
            continue
        del stack[marker // 4:]
        body = BOX_CHARS.sub(" ", line[marker:]).split("#")[0].replace(" / ", " ")
        tokens = [t.strip("()（）") for t in body.split() if not t.startswith(("(", "（"))]
        tokens = [t for t in tokens if t and t != ROOT_TOKEN.rstrip("/")]
        for token in tokens:
            claims.append((lineno, _join_path(stack + [token])))
        if tokens:
            stack.append(tokens[-1])
    return claims


def inside_claims(text):
    """'What's inside' 一节的相对链接同样是公开承诺（其余章节的跨文档链接由死链检查管）。"""
    claims, inside = [], False
    for lineno, line in enumerate(text.splitlines(), 1):
        if re.match(r"^##\s", line):
            inside = bool(INSIDE_HEADING.search(line))
            continue
        if inside:
            for m in MD_LINK.finditer(line):
                target = m.group(1).strip()
                if not target.startswith(("http://", "https://", "#", "mailto:")):
                    claims.append((lineno, target.lstrip("/")))
    return claims


def layout_hits(rel, claims, tracked):
    """正向：README 点名的每条路径都必须真存在；反向：每个跟踪文件都必须被点名，
    或被「折叠目录」（该目录下列了任何子项即不算折叠）覆盖。"""
    files = {t for _, t in claims if not t.endswith("/")}
    dirs = {t if t.endswith("/") else t + "/" for _, t in claims if t.endswith("/")}
    collapsed = {d for d in dirs if not any(o.startswith(d) for o in files | dirs if o != d)}
    hits = []
    tracked_set = set(tracked)
    for lineno, token in claims:
        if token.endswith("/"):
            if not any(f.startswith(token) for f in tracked_set):
                hits.append(f"{rel}:{lineno} stale-tree-entry ({token})")
        elif token not in tracked_set:
            hits.append(f"{rel}:{lineno} stale-tree-entry ({token})")
    for f in sorted(tracked_set):
        if f in files or any(f.startswith(d) for d in collapsed):
            continue
        hits.append(f"{rel}:1 unlisted-tracked-file ({f})")
    return hits


def check_readme_layout():
    """README 的目录树与 What's inside 是对外承诺的文件清单；靠人工同步必然漂移（本轮
    加 publish.py / AGENTS.md / release.yml 就是下一次漂移现场），故钉成机器闸。"""
    if not is_repo_layout():
        return []
    tracked = git_tracked_files()
    if not tracked:
        return []
    hits = []
    for rel in README_FILES:
        path = REPO / rel
        if not path.is_file():
            continue
        text = read(path)
        hits += layout_hits(rel, tree_claims(text) + inside_claims(text), tracked)
    return hits


def latest_local_tag():
    """本机可见的最新 vX.Y.Z tag；取不到（浅克隆/无 tag）就跳过该子检查，不假报。"""
    try:
        out = subprocess.run(["git", "-C", str(REPO), "tag", "--sort=-v:refname"],
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=30)
    except Exception:
        return ""
    for line in out.stdout.splitlines():
        if re.fullmatch(r"v\d+\.\d+\.\d+", line.strip()):
            return line.strip()
    return ""


def check_changelog():
    """发布口径三处一致：PR 模板要求在 [Unreleased] 下写条目 → CHANGELOG 必须有该段且在最前；
    release.yml 从 CHANGELOG 抽正文 → 最新 tag 必须有对应段，否则本机就该拦。"""
    if not is_repo_layout():
        return []
    path = REPO / "CHANGELOG.md"
    if not path.is_file():
        return ["CHANGELOG.md:1 changelog-missing"]
    text = read(path)
    lines = text.splitlines()
    hits = []
    unreleased = next((i for i, ln in enumerate(lines)
                       if UNRELEASED_HEADING.match(ln.strip())), None)
    first_version = next((i for i, ln in enumerate(lines)
                          if VERSION_HEADING.match(ln.strip())), None)
    if unreleased is None:
        hits.append("CHANGELOG.md:1 changelog-unreleased-missing")
    elif first_version is not None and unreleased > first_version:
        hits.append("CHANGELOG.md:1 changelog-unreleased-not-first")
    tag = latest_local_tag()
    if tag and not section_for(tag, text)[1]:
        hits.append(f"CHANGELOG.md:1 changelog-tag-without-section ({tag})")
    return hits


def crlf_hits(rels, repo: Path = REPO):
    """字节级 CRLF 检测（纯函数，取数由调用方给）。

    为什么按字节而不是文本读：Windows 下 Git Bash 的 grep 判 \\r 会假报（本轮踩过），
    而行尾恰恰是 `.gitattributes` 已钉 LF、但编辑工具仍可能写回 CRLF 的地方。"""
    hits = []
    for rel in rels:
        p = repo / rel
        if not p.is_file():
            continue
        try:
            if b"\r\n" in p.read_bytes():
                hits.append(f"{rel}:1 crlf-in-tracked-file")
        except OSError:
            continue
    return hits


def check_crlf():
    """仓库布局扫跟踪文件清单；安装点布局没有 git，扫包里全部文本发布件——
    两种布局都在真检，不做「取不到就静默跳过」（那正是本轮被抓住的自证式漏洞）。"""
    if is_repo_layout():
        tracked = git_tracked_files()
        if tracked:
            return crlf_hits(tracked)
    return crlf_hits([p.relative_to(REPO).as_posix() for _, p in tracked_text_files()])


SKILL_VERSION = re.compile(r"^\s+version:\s*[\"']?(\d+\.\d+\.\d+)[\"']?\s*$", re.M)


def version_drift(skill_text: str, tag: str):
    """SKILL.md 的 metadata.version 与最新 tag 必须对齐（纯函数）。

    tag 为空 = 拿不到 tag（浅克隆、CI 的默认 checkout）：此时不假报，但也不算通过——
    CI 侧靠 `fetch-depth: 0` 把 tag 取全，让这条闸真的咬得住。"""
    m = SKILL_VERSION.search(skill_text)
    if not m:
        return ["SKILL.md:2 version-tag-drift (metadata.version 读不到)"]
    version = m.group(1)
    if not tag:
        return []
    if tag.strip() != f"v{version}":
        return [f"SKILL.md:2 version-tag-drift (SKILL {version} vs {tag.strip()})"]
    return []


def check_version_tag():
    skill = REPO / "SKILL.md"
    if not skill.is_file():
        return []
    return version_drift(read(skill), latest_local_tag())


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
    # 本轮注入实验证实的三类漏网：合成样本，不含任何真实本机端口/真实邮箱
    ("local-network", check_local_network, "回环端点 127.0.0.1:9999 与 Clash 代理 9999 下载稳"),
    ("personal-identity", check_personal_identity, "联系作者 " + "who" + "@" + "author.internal-host.test"),
    ("external-script", check_external_script_ref, "先跑 python not_shipped_tool.py 一遍"),
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
    # 阴性自证：闸不能只会响——三条例外通路必须真的放行，否则它是噪音源
    negatives = [
        ("identity-exempt", check_identity(SYNTH, "上一代工具 " + IDENTITY_EXEMPT_TERMS[0] + " 的历史语境"),
         "审词清单 exempt 词不报"),
        ("external-script-marked",
         check_external_script_ref(SYNTH, "跑 python not_shipped.py（该脚本非本包发布物）"),
         "已标注非本包发布物的命令不报"),
        ("email-placeholder", check_personal_identity(SYNTH, "示例 someone@example.com"),
         "占位邮箱不报"),
    ]
    for name, hits, why in negatives:
        print(("PASS" if not hits else "FAIL") + f" negative/{name}: {why}")
        ok = ok and not hits

    # 双语结构闸用两个内存文档自证
    en_lv = [lv for lv, _ in headings("# A\n## B\n")]
    zh_lv = [lv for lv, _ in headings("# A\n")]
    print(("PASS" if en_lv != zh_lv else "FAIL") + " bilingual-structure: 人造层级差被识别")
    ok = ok and en_lv != zh_lv

    # 私有件误拷入包：注入一个「仓库里存在」的路径，不碰磁盘。走纯函数故两种布局都能自证。
    sample_private = next(iter(gitignored_doc_paths()), "x.md")
    hits = private_present_hits([sample_private])
    print(("PASS" if hits else "FAIL") + " private-in-package: 人造误拷被拦（位置已点名）")
    ok = ok and bool(hits)

    # 发布面变换表：必须生效且幂等（同一张表被 sync_check 与发布脚本共用）
    src = IDENTITY_BLOCK_TERMS[0] + "定的标准见 [[cm-closure-mindmap-pipeline]]，落盘于 D:/AI/HERMES/a.md"
    once = apply_publish_rules(src)
    twice = apply_publish_rules(once)
    clean = ("栗" not in once) and ("[[cm-" not in once) and (":/" not in once.replace("https://", ""))
    print(("PASS" if once == twice else "FAIL") + " publish-rules: 幂等")
    print(("PASS" if clean else "FAIL") + " publish-rules: 人造原文经变换后三类痕迹均消失")
    ok = ok and once == twice and clean

    # README 目录树闸：正反两个方向都要响（用内存文档 + 人造跟踪清单，不碰磁盘）
    fake_tracked = ["SKILL.md", "tools/preflight.py", "CHANGELOG.md"]
    fake_doc = ("```\nproj/\n├── SKILL.md   # 入口\n├── tools/\n"
                "│   └── preflight.py\n└── GHOST.md   # 早已删掉的旧文件\n```\n")
    fake_hits = layout_hits("README.md", tree_claims(fake_doc), fake_tracked)
    forward = any("stale-tree-entry" in h and "GHOST.md" in h for h in fake_hits)
    backward = any("unlisted-tracked-file" in h and "CHANGELOG.md" in h for h in fake_hits)
    print(("PASS" if forward else "FAIL") + " readme-layout: 树里列了不存在的文件被点名")
    print(("PASS" if backward else "FAIL") + " readme-layout: 未写进树的跟踪文件被点名")
    ok = ok and forward and backward

    # CHANGELOG 结构闸（内存文档自证，不碰磁盘）
    fake_cl = "# Changelog\n\n## v9.9.9 - 2026-01-01\n\n- something real\n"
    cl_has_unreleased = any(UNRELEASED_HEADING.match(ln.strip()) for ln in fake_cl.splitlines())
    cl_missing_tag = section_for("v8.8.8", fake_cl)[1]
    cl_found_tag = section_for("v9.9.9", fake_cl)[1]
    print(("PASS" if not cl_has_unreleased else "FAIL") + " changelog: 缺 [Unreleased] 段的文档被识别")
    print(("PASS" if not cl_missing_tag else "FAIL") + " changelog: 无对应版本段的 tag 被识别")
    print(("PASS" if cl_found_tag else "FAIL") + " changelog: 有版本段的 tag 能正常抽出（非永远失败）")
    ok = ok and (not cl_has_unreleased) and (not cl_missing_tag) and cl_found_tag

    # frontmatter 五键：注入一个只有 name/description 的块
    hits = frontmatter_issues("name: x\ndescription: y\n")
    print(("PASS" if hits else "FAIL") + f" frontmatter: 人造缺键块被拦（{len(hits)} 项）")
    ok = ok and len(hits) == 5

    # workflow YAML 非 ASCII：注入一行中文注释
    hits = non_ascii_hits(".github/workflows/ci.yml", "# comment ok\n# 中文注释\n")
    print(("PASS" if hits else "FAIL") + " workflow-ascii: 人造非 ASCII 行被点名")
    ok = ok and len(hits) == 1

    # 行尾闸（本轮新检）：临时目录里造一份 CRLF、一份 LF，正例点名、负例放行。
    # 走纯函数 + 注入目录，所以在仓库/安装点/clone 三种布局下结论一致。
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "crlf.md").write_bytes(b"line one\r\nline two\r\n")
        (tmp / "lf.md").write_bytes(b"line one\nline two\n")
        hits = crlf_hits(["crlf.md", "lf.md"], repo=tmp)
        pos = hits == ["crlf.md:1 crlf-in-tracked-file"]
        neg = not crlf_hits(["lf.md"], repo=tmp)
        # 反向接线：把字节读取改成文本读取（文本模式会把 CRLF 吞成 LF）就检不出来
        original_read = Path.read_bytes
        try:
            globals()["Path"].read_bytes = lambda self: original_read(self).replace(b"\r\n", b"\n")
            weakened = crlf_hits(["crlf.md"], repo=tmp)
        finally:
            globals()["Path"].read_bytes = original_read
        print(("PASS" if pos else "FAIL") + " crlf: 人造 CRLF 文件被点名（不含内容）")
        print(("PASS" if neg else "FAIL") + " negative/crlf: LF 文件不误报")
        print(("PASS" if not weakened else "FAIL")
              + " crlf: 去掉字节级读取后该检失效（反向接线证明）")
        ok = ok and pos and neg and not weakened

    # 版本对齐闸（本轮新检）：漂移必报、对齐放行、拿不到 tag 时不假报
    skill_text = 'name: x\nmetadata:\n  version: "1.2.3"\n'
    drift = version_drift(skill_text, "v1.2.4")
    aligned = version_drift(skill_text, "v1.2.3")
    no_tag = version_drift(skill_text, "")
    no_version = version_drift("metadata:\n  author: 作者\n", "v1.2.3")
    print(("PASS" if drift and "version-tag-drift" in drift[0] else "FAIL")
          + " version-tag: SKILL 版本与最新 tag 不等被点名")
    print(("PASS" if not aligned else "FAIL") + " negative/version-tag: 对齐时不报")
    print(("PASS" if not no_tag else "FAIL") + " negative/version-tag: 取不到 tag 时不假报")
    print(("PASS" if no_version else "FAIL") + " version-tag: 读不到 version 也报（不许静默通过）")
    ok = ok and bool(drift) and not aligned and not no_tag and bool(no_version)
    return 0 if ok else 1


def scan_text(path: Path) -> str:
    """决定「扫什么」：
    仓库镜像布局 → 扫原文。发布物本就不该带本机痕迹，若先套匿名化再扫，等于把真泄露洗白后
    宣布干净（本轮端到端注入实测过这个自证式漏洞）。
    安装点布局 → 扫变换后的文本，即它将被发布成的样子。"""
    raw = read(path)
    return raw if is_repo_layout() else apply_publish_rules(raw)


def main() -> int:
    ap = argparse.ArgumentParser(description="公开包发布面预检（零写盘）")
    ap.add_argument("--self-test", action="store_true", help="注入人造违规验证每类检测会响")
    ap.add_argument("--only", metavar="RULE", help="只跑指定规则名前缀，便于定位")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    findings = []
    for rel, path in iter_public_md():
        text = scan_text(path)
        findings += check_local_trace(rel, text)
        findings += check_local_network(rel, text)
        findings += check_personal_identity(rel, text)
        findings += check_identity(rel, text)
        findings += check_credentials(rel, text)
        findings += check_links(rel, text)
        findings += check_private_mentions(rel, text)
        findings += check_external_script_ref(rel, text)
    findings += check_bilingual_structure()
    findings += check_private_present()
    findings += check_skill_frontmatter()
    findings += check_workflows_ascii()
    findings += check_readme_layout()
    findings += check_changelog()
    findings += check_crlf()
    findings += check_version_tag()

    # 非 md 的发布文件（LICENSE / yml 配置）只跑泄露类检测
    for rel, path in tracked_text_files():
        if path.suffix.lower() == ".md":
            continue
        text = scan_text(path)
        findings += check_local_trace(rel, text)
        findings += check_local_network(rel, text)
        findings += check_personal_identity(rel, text)
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
