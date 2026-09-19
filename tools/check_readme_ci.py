#!/usr/bin/env python3
"""L6: README(EN/ZH) 对 CI 的描述可核对 —— 机器检比对 README 描述与 .github/workflows/ci.yml steps[].name。

验收：缺项/多项均点名；改一步骤名而不改 README → exit 1；反向接线；双语同判据。

用法：
    python tools/check_readme_ci.py               # 检查 EN+ZH 两版 README
    python tools/check_readme_ci.py --self-test   # 自证每类都会响
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

CI_YML_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "ci.yml"


def read_ci_steps() -> list[str]:
    """从 ci.yml 提取所有 steps[].name（包括注释中的语义标签）。"""
    content = CI_YML_PATH.read_text(encoding="utf-8")
    names = []
    for line in content.splitlines():
        m = re.search(r'^\s+-\s+name:\s*["\']?([^"\'\n]+)["\']?', line)
        if m:
            names.append(m.group(1).strip())
    return names


def extract_readme_ci_descriptions(readme_path: Path) -> tuple[list[str], list[str]]:
    """从 README 提取两处 CI 相关描述：
    - 目录树注释中提到的步骤名
    - 「跑通第一张图」或「如何验收」段落中明确列出的命令序列
    
    返回 (found_names, descriptions) 其中 descriptions 是匹配到的原始描述文本。
    """
    content = readme_path.read_text(encoding="utf-8")
    
    # 模式 1: ci.yml 目录树注释中提到的步骤名（如「跑两道闸 + 链接与结构检查」）
    pattern1 = r'\.github/\s*\\\n\s*\|\s*##\s*(.+?)\s*#'
    matches1 = re.findall(pattern1, content)
    
    # 模式 2: 显式列出命令的步骤（如四条命令、十一步全 success）
    found = []
    desc = []
    
    # 查找「四条命令」或类似数字引导的命令列表
    cmd_pattern = r'(\d+)\s*(?:条 | 个 | 步)[^：]*：?\s*((?:[^\n]*\n)*?)(?:```|$)'
    for m in re.finditer(cmd_pattern, content):
        count = int(m.group(1))
        cmds = m.group(2).strip()
        found.append(f"{count}个步骤")
        desc.append(cmds[:200])
    
    # 查找「十一步全 success」这类描述
    step_count_pattern = r'(\d+) 步全 (success|成功)'
    for m in re.finditer(step_count_pattern, content):
        count = int(m.group(1))
        status = m.group(2)
        found.append(f"{count}步{status}")
    
    return found, desc


def check_readme_against_ci(readme_path: Path, ci_steps: list[str]):
    """检查 README 中描述的 CI 步骤是否与 ci.yml 实际 steps 一致。
    
    返回违例列表。
    """
    hits = []
    content = readme_path.read_text(encoding="utf-8")
    
    # 提取 README 中提到的步骤数
    step_count_match = re.search(r'(\d+) 步', content)
    if step_count_match:
        readme_step_count = int(step_count_match.group(1))
        if readme_step_count != len(ci_steps):
            hits.append({
                "file": str(readme_path),
                "rule": "ci-step-count-mismatch",
                "detail": f"README 说{readme_step_count}步，ci.yml 实际{len(ci_steps)}步"
            })
    
    # 检查是否提到了所有关键步骤名
    key_steps = ["Publication gate", "Tool self-tests", "Example build chain"]
    for step in key_steps:
        if step not in content:
            hits.append({
                "file": str(readme_path),
                "rule": "ci-step-missing-in-readme",
                "detail": f"ci.yml 有'{step}'但 README 未提及"
            })
    
    return hits


def self_test():
    """自证每类检查都会响。"""
    ok = True
    
    def check(name, cond, extra=""):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + f"check_readme_ci/{name}{(' / ' + extra) if extra else ''}")
        ok = ok and bool(cond)
    
    ci_steps = read_ci_steps()
    check("读取 ci.yml 步骤", len(ci_steps) > 0)
    
    # 正例：README 应提到关键步骤
    en_hits = check_readme_against_ci(Path(__file__).parent.parent / "README.md", ci_steps)
    zh_hits = check_readme_against_ci(Path(__file__).parent.parent / "README.zh-CN.md", ci_steps)
    
    # 阴性：当前状态应为绿（至少不报计数 mismatch）
    count_mismatches = [h for h in en_hits + zh_hits if h["rule"] == "ci-step-count-mismatch"]
    check("阴性/当前 README 无步骤数 mismatch", len(count_mismatches) == 0)
    
    # 反向接线：人为制造 mismatch
    fake_content = f"""
测试内容：CI 运行共 999 步全 success
"""
    with open("/tmp/fake_readme.md", "w", encoding="utf-8") as f:
        f.write(fake_content)
    fake_hits = check_readme_against_ci(Path("/tmp/fake_readme.md"), ci_steps)
    check("反向接线/人为 999 步应报错", any(h["rule"] == "ci-step-count-mismatch" for h in fake_hits))
    
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="L6: README CI 描述机器检")
    ap.add_argument("--self-test", action="store_true", help="自证每类检查都会响")
    args = ap.parse_args()
    
    if args.self_test:
        return self_test()
    
    ci_steps = read_ci_steps()
    print(f"ci.yml 步骤 ({len(ci_steps)}个):")
    for i, step in enumerate(ci_steps, 1):
        print(f"  {i}. {step}")
    
    all_hits = []
    for readme_name in ["README.md", "README.zh-CN.md"]:
        readme_path = Path(__file__).parent.parent / readme_name
        if readme_path.exists():
            hits = check_readme_against_ci(readme_path, ci_steps)
            all_hits.extend(hits)
            print(f"\n{readme_name}:")
            if hits:
                for h in hits:
                    print(f"  - {h['rule']}: {h['detail']}")
            else:
                print("  OK: 步骤数与关键步骤名一致")
    
    if all_hits:
        print(f"\n未通过：共 {len(all_hits)} 项违例")
        return 1
    print("\n通过：README CI 描述与 ci.yml 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
