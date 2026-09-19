#!/usr/bin/env python3
# 同步校验（零写盘）：本地 skill 编辑正本 → 仓库发布镜像的一致性闸门。
#
# 用法：
#   python tools/sync_check.py [正本目录 ...]
#   MINDMAP_SKILL_MASTERS="目录1;目录2" python tools/sync_check.py
#   python tools/sync_check.py --self-test     # 人造漂移自证这条闸真的会响
#
# 口径：本地正本是编辑源，仓库是发布镜像；两者之间隔着 tools/preflight.py 里那张
# 发布面变换表（身份匿名化 + 本机路径通用化）。因此比对的是
# 「仓库文件 == 变换后的正本文件」——正本改了没发布、发布面漏了脱敏，都会报警。
# 退出码 0=一致（或本机没有任何正本，外部用户可忽略）；1=有不一致，stdout 点名文件。
import argparse
import hashlib
import os
import tempfile
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preflight import (PUBLIC_SURFACE_REL, apply_publish_rules,  # noqa: E402
                       classify_text_rels, gitignored_doc_paths)

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


def public_rels(root: Path, private=()):
    """公开文件集 = 登记表登记的发布件（与 publish / preflight 同一张表、同一个判定）。
    本函数的私有件清单同样取自 preflight，两处不再各存一份常量。"""
    published, _unregistered = classify_text_rels(root, private=private)
    return set(published)


def raw_bytes(path: Path) -> bytes:
    """按字节读，只做行尾归一：用于读仓库镜像——镜像里应该已经是发布面原文，
    再套一次变换会把「未脱敏的原文」洗成「看起来一致的发布面」（实测过的假绿形态）。"""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")


def published_bytes(path: Path) -> bytes:
    """读文本 → 套发布面变换 → 归一 LF。用于读正本侧：正本保留原文。"""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return apply_publish_rules(text).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def private_master_problems(private_rels, masters, reader=None):
    """登记在案的本地私有件（不进公开包，因此镜像侧比不到）改由「正本之间」兜底：
    三处安装正本都在场就必须逐字节一致；任一处没有这件 = 那台机器没装齐，跳过不假报。

    缺件与漂移是两种结论：缺件不报警，漂移必点名——前者是新机器的正常形态，
    后者是「改了 A 没改 B」的历史事故形态（安装点布局互比已经抓过一次）。
    """
    reader = raw_bytes if reader is None else reader
    problems, checked = [], 0
    present = [d for d in masters if d.is_dir()]
    for rel in sorted(private_rels):
        texts = {}
        missing = False
        for d in present:
            path = d / rel
            if path.is_file():
                texts[d.as_posix()] = reader(path)
            else:
                missing = True
        if missing or len(texts) < 2:
            continue
        checked += 1
        if len(set(texts.values())) > 1:
            problems.append(f"私有正本不一致：{rel}（{'、'.join(texts)}）")
    return problems, checked


def private_rels(repo_root: Path = REPO) -> set:
    """有意留在本地的私有文档清单：唯一出处在 preflight（读 .gitignore，安装点退回常量表）。
    本文件不再另存一份副本，否则两处口径迟早漂移——那正是本轮要收的账。"""
    return set(gitignored_doc_paths(repo_root))


def compare(repo_root: Path, masters):
    """比对核心：返回 (问题清单, 仓库公开文件集, 存在的正本, 跳过的正本)。

    两种布局两套口径，都用参数驱动的纯函数实现（不读全局 REPO、不按布局自我裁剪
    检测项），因此自测能在临时假目录里跑，四布局结论一致：

    * 镜像布局（repo_root 里有 .gitignore）＝发布仓库：要求「仓库文件逐字节 ==
      正本套上发布面变换」，于是「正本改了没发布」与「发布了没脱敏」都会报警，
      镜像里残留正本原文时点名得更具体。
    * 安装点布局（无 .gitignore）＝本地 skill 正本目录：这里两侧存的都是原文，
      要求发布面只会假报，故改为各正本之间逐字互比（运行位置自身算一处）。"""
    private = gitignored_doc_paths(repo_root)
    mirror = (repo_root / ".gitignore").is_file()
    repo_rels, repo_unregistered = classify_text_rels(repo_root, private=private)
    present, skipped = [], []
    for d in masters:
        (present if d.is_dir() else skipped).append(d)

    if not mirror:
        sides = [repo_root] + [d for d in present if d.resolve() != repo_root.resolve()]
        present = sides
        universe, unregistered = set(), set()
        for d in sides:
            published, unreg = classify_text_rels(d, private=set())
            universe |= set(published)
            unregistered |= set(unreg)
        problems = [f"未登记公开件类型：{rel}（登记表 {PUBLIC_SURFACE_REL} 未列该类型）"
                    for rel in sorted(unregistered)]
        for rel in sorted(universe):
            texts = {}
            for d in sides:
                p = d / rel
                if p.is_file():
                    texts[d.as_posix()] = raw_bytes(p)
            if len(texts) < len(sides):
                missing = [d.as_posix() for d in sides if d.as_posix() not in texts]
                problems.append(f"正本之间缺文件：{rel}（{'、'.join(missing)} 没有）")
            elif len(set(texts.values())) > 1:
                problems.append(f"正本之间不一致：{rel}（{'、'.join(texts)}）")
        return problems, universe, present, skipped

    problems = [f"未登记公开件类型（仓库侧）：{rel}（登记表 {PUBLIC_SURFACE_REL} 未列该类型）"
                 for rel in repo_unregistered]
    for local in present:
        local_rels, local_unregistered = classify_text_rels(local, private=private)
        problems += [f"未登记公开件类型：{rel}（{local}，登记表 {PUBLIC_SURFACE_REL} 未列该类型）"
                     for rel in local_unregistered]
        for rel in sorted(set(repo_rels) | set(local_rels)):
            rp, lp = repo_root / rel, local / rel
            if not rp.is_file():
                problems.append(f"{local} 有而仓库缺：{rel}")
            elif not lp.is_file():
                problems.append(f"仓库有而 {local} 缺：{rel}"
                                "（正本已删该文档 -> 跑 python tools/publish.py --prune 清镜像残留）")
            elif digest(raw_bytes(rp)) != digest(published_bytes(lp)):
                if digest(raw_bytes(rp)) == digest(raw_bytes(lp)):
                    problems.append(f"镜像未套发布面变换：{rel}（仓库内容与 {local} 原文逐字节相同）")
                else:
                    problems.append(f"发布面不一致：{rel}（{local} vs 仓库）")
    # 私有件不进公开包，镜像侧比不到；改由「正本之间」兜底，缺件不假报、漂移必点名。
    private_problems, _n = private_master_problems(private, present)
    problems += private_problems
    return problems, repo_rels, present, skipped


# 自测样本：含盘符路径与包外记忆指针两种「必须被变换」的形态。刻意不含身份词——
# 测试夹具一旦落盘就成了命中原文的载体，而身份词的变换由 preflight 的内存自测覆盖。
RAW_TEXT = "落盘位置 Q:/SYNTH/x.md，另见 [[cm-closure-mindmap-pipeline]]。\n"  # preflight:rule-literal: "发布面变换夹具需盘符与包外指针两种真实形态，值为合成"
GITIGNORE_STUB = "__pycache__/\nreferences/memory/private-notes.md\n"


def _put(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def self_test() -> int:
    """破坏性自证：人造漂移、人造未脱敏镜像、缺件、无正本四类场景，全部落在临时目录，
    绝不触碰真实安装点。"""
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + f"sync-check/{name}")
        ok = ok and bool(cond)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo, master = root / "repo", root / "master"
        _put(repo / ".gitignore", GITIGNORE_STUB)
        _put(master / "SKILL.md", RAW_TEXT)
        _put(master / "references" / "memory" / "a.md", RAW_TEXT)
        _put(master / "references" / "memory" / "private-notes.md", RAW_TEXT)
        published = apply_publish_rules(RAW_TEXT)
        _put(repo / "SKILL.md", published)
        _put(repo / "references" / "memory" / "a.md", published)

        problems, repo_rels, present, _skipped = compare(repo, [master])
        check("clean mirror passes", present and not problems)
        check("gitignored private doc excluded", "references/memory/private-notes.md" not in repo_rels)

        _put(master / "SKILL.md", RAW_TEXT + "\n正本里新加了一句还没发布的话。\n")
        problems, _r, _p, _s = compare(repo, [master])
        check("unpublished master edit named", any("SKILL.md" in p for p in problems))

        _put(repo / "references" / "memory" / "a.md", RAW_TEXT)
        problems, _r, _p, _s = compare(repo, [master])
        check("raw mirror named as unredacted",
              any("references/memory/a.md" in p and "未套发布面变换" in p for p in problems))

        _put(repo / "references" / "memory" / "a.md", published)
        _put(master / "references" / "memory" / "only-master.md", RAW_TEXT)
        problems, _r, _p, _s = compare(repo, [master])
        check("file present only in master named", any("only-master.md" in p for p in problems))
        _put(master / "references" / "memory" / "only-master.md", "")
        os.remove(master / "references" / "memory" / "only-master.md")
        _put(repo / "references" / "memory" / "only-repo.md", published)
        problems, _r, _p, _s = compare(repo, [master])
        check("file present only in repo names the prune switch",
              any("only-repo.md" in p and "--prune" in p for p in problems))
        _put(master / "references" / "x.tsv", "合成未登记件\n")
        problems, _r, _p, _s = compare(repo, [master])
        check("unregistered public type named",
              any("未登记公开件类型" in p and "references/x.tsv" in p for p in problems))
        os.remove(master / "references" / "x.tsv")
        os.remove(repo / "references" / "memory" / "only-repo.md")
        problems, _r, _p, _s = compare(repo, [master])
        check("residue cleared -> sync gate green", not problems)

        problems, _r, present, skipped = compare(repo, [root / "no-such-master"])
        check("no masters -> zero problems (portable)", not present and not problems and skipped)

        # 反向接线证明：把发布面变换从比对里摘掉，一个本来正确的镜像会被判成漂移，
        # 说明这张表真的接在线路上（而不是「写了没接」）。
        synth = "新的一句落盘位置 Q:/SYNTH/y.md。\n"  # preflight:rule-literal: "接线夹具需盘符形态，值为合成"
        fresh = apply_publish_rules(synth)
        _put(master / "SKILL.md", synth)
        _put(repo / "SKILL.md", fresh)
        problems, _r, _p, _s = compare(repo, [master])
        check("clean pair passes again", not any("SKILL.md" in p for p in problems))

        original_reader = published_bytes
        try:
            globals()["published_bytes"] = raw_bytes
            problems, _r, _p, _s = compare(repo, [master])
            check("removing the transform turns a correct mirror into false drift",
                  any("SKILL.md" in p for p in problems))
        finally:
            globals()["published_bytes"] = original_reader

        # 安装点布局（无 .gitignore）：两侧存的都是原文，只能正本互比。四布局实跑
        # 抓出来的漏项——按镜像口径比对会把私有件与未发布原文全判成「未套变换」。
        side_a, side_b = root / "masterA", root / "masterB"
        for side in (side_a, side_b):
            _put(side / "SKILL.md", RAW_TEXT)
            _put(side / "references" / "memory" / "a.md", RAW_TEXT)
            _put(side / "references" / "memory" / "private-notes.md", RAW_TEXT)
        problems, rels, sides, _s = compare(side_a, [side_a, side_b])
        check("identical masters pass in install-point layout", len(sides) == 2 and not problems)
        _put(side_b / "references" / "memory" / "private-notes.md", RAW_TEXT + "\n只在正本侧演进的一句。\n")
        problems, _r, _p, _s = compare(side_a, [side_a, side_b])
        check("private-doc divergence still caught between masters",
              any("private-notes.md" in p for p in problems))
        _put(side_b / "references" / "memory" / "private-notes.md", RAW_TEXT)
        os.remove(side_b / "references" / "memory" / "a.md")
        problems, _r, _p, _s = compare(side_a, [side_a, side_b])
        check("missing file between masters named",
              any("references/memory/a.md" in p and "缺文件" in p for p in problems))
        check("install-point layout compares private docs too",
              "references/memory/private-notes.md" in rels)

        # 私有正本一致性（本轮新增）：三处都在场才判，缺件不假报、漂移必点名。
        priv = "references/memory/private-notes.md"
        m_a, m_b, m_c = root / "mA", root / "mB", root / "mC"
        for side in (m_a, m_b, m_c):
            _put(side / priv, RAW_TEXT)
        problems, counted = private_master_problems({priv}, [m_a, m_b, m_c])
        check("identical private masters pass", not problems and counted == 1)
        _put(m_c / priv, RAW_TEXT + "\nC 处独自演进了一句。\n")
        problems, counted = private_master_problems({priv}, [m_a, m_b, m_c])
        check("diverging private master named",
              any(priv in p and "私有正本不一致" in p for p in problems))
        os.remove(m_c / priv)
        problems, counted = private_master_problems({priv}, [m_a, m_b, m_c])
        check("missing private file skips instead of crying",
              not problems and counted == 0)

        # 反向接线证明：把「逐字节比较」换成「只看首个字节」，同样的漂移就成了绿灯。
        original_cmp = raw_bytes
        try:
            globals()["raw_bytes"] = lambda p: original_cmp(p)[:1]
            _put(m_b / priv, RAW_TEXT + "\nB 处漂移。\n")
            problems, counted = private_master_problems({priv}, [m_a, m_b])
            check("weakening the byte comparison hides real drift", not problems and counted == 1)
        finally:
            globals()["raw_bytes"] = original_cmp
            _put(m_b / priv, RAW_TEXT)

    return 0 if ok else 1


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="正本与发布镜像的一致性闸门（零写盘）")
    ap.add_argument("masters", nargs="*", help="本地 skill 正本目录（可多个）")
    ap.add_argument("--self-test", action="store_true", help="人造漂移自证这条闸会响")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    masters = master_dirs(args.masters)
    problems, repo_rels, present, skipped = compare(REPO, masters)
    if not repo_rels:
        print("仓库侧未发现任何公开文件，检查运行位置")
        return 1

    for d in skipped:
        print(f"跳过正本（目录不存在，可忽略）：{d}")
    if not present:
        print(f"未发现本地正本，外部用户可忽略本闸；仓库公开文件 {len(repo_rels)} 个已就位")
        return 0

    if problems:
        print("同步校验失败：")
        for p in problems:
            print(f"  - {p}")
        return 1
    tail = f"（另有 {len(skipped)} 处正本目录不存在，已跳过）" if skipped else ""
    if (REPO / ".gitignore").is_file():
        _p, checked = private_master_problems(private_rels(REPO), present)
        print(f"一致：仓库 + {len(present)} 个本地 skill 正本，共 {len(repo_rels)} 个公开文件，"
              f"私有正本逐字比对 {checked} 件{tail}")
    else:
        print(f"一致：{len(present)} 处本地 skill 正本逐字互比，共 {len(repo_rels)} 个文档"
              f"（安装点存的是原文，发布面比对只在镜像仓库里做）{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
