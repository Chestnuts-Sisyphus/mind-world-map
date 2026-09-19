# 🧠 Mindmap Engineering

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![release](https://img.shields.io/github/v/release/Chestnuts-Sisyphus/mind-world-map.svg)](https://github.com/Chestnuts-Sisyphus/mind-world-map/releases)
[![CI](https://img.shields.io/github/actions/workflow/status/Chestnuts-Sisyphus/mind-world-map/ci.yml.svg?label=CI)](https://github.com/Chestnuts-Sisyphus/mind-world-map/actions/workflows/ci.yml)
[![skill](https://img.shields.io/badge/skill-mindmap--engineering-informational.svg)](SKILL.md)

**An agent skill for engineering mind maps — battle-tested standards, machine QA gates, and a data/build pipeline for producing XMind files a cold reader can understand completely.**

[中文说明](README.zh-CN.md) · [Standard entry](SKILL.md) · [Pitfall archive](references/pitfalls.md) · [Update protocol](references/update-protocol.md) · [Changelog](CHANGELOG.md)

---

Most "mind map" outputs are decorated outlines. This skill treats a mind map as a **rigorous knowledge artifact**: the exhaustive expansion of exactly one subject, where every root-to-leaf path reads as a complete proposition, and every first-time reader can grasp the full picture and every detail *from the map alone* — no external documents.

Every rule in here is a scar: distilled from six real rounds of rework (2026-08 → 2026-09), each gate exists because something slipped past the previous one.

## ✨ What's inside

| Component | What you get |
|---|---|
| [SKILL.md](SKILL.md) | The single source of truth: pre-flight checklist, dual baselines (visual + content), the total definition ("a mind map is the exhaustive extension of one subject"), term ledger & note-ification rules, delivery gates. |
| [references/pitfalls.md](references/pitfalls.md) | Full pitfall archive in four classes: file-format traps, content-organization traps, pipeline traps, collaboration rules. |
| [references/update-protocol.md](references/update-protocol.md) | The six-step protocol for updating an existing map (maps are build artifacts — hand-editing XMind is forbidden), plus three anti-regression safeguards. |
| [references/memory/](references/memory/) | 6 deep-dive knowledge documents: visual style baseline, CLI generation flow, narrative calibration, render-flicker troubleshooting, and more. |
| [tools/sync_check.py](tools/sync_check.py) | Read-only sync gate: SHA256-compares the repo mirror against your local skill master copies (publish rules applied); exits non-zero and names divergent files. Missing master directories are skipped, so it is safe to run anywhere. |
| [tools/preflight.py](tools/preflight.py) | Read-only publication gate: local-machine traces (drive-letter paths, 8.3 short names, user-directory segments, local account name), credential shapes, dead relative links and dead document pointers, private files named in public docs, EN/ZH heading-structure drift, identity-term regression. Reports `file:line rule` only — never the matched text. `--self-test` proves every category actually fires. |

## 🔑 Core ideas in 60 seconds

- **Closure law** — any person unfamiliar with the subject, reading only the map, understands everything. This is the acceptance bar.
- **Proposition paths** — the unit of understanding is a proposition, not a noun; every root-to-leaf path must read as a coherent sentence. Bare noun nodes without substance get deleted.
- **Term → note pipeline** — definitions live in a data-layer term ledger and are auto-injected into notes at every usage point ("one note = one small text tree"), so the tree stays clean (2–7 character labels, zero punctuation) while every term is explained exactly where it first appears.
- **Two generations of machine QA** — build-time blocking gates (punctuation ban, five term gates, number-grounding gate, top-branch budget ≤ 9, fan-out ≤ 13) plus eight post-hoc checks, every one sunk from a real regression.
- **Data/build separation** — content lives in data files, structure in builder scripts; the map is a deterministic function of its data. Idempotent rebuilds, timestamped backups, diff reports. Never hand-edit an `.xmind`.
- **Budget folding** — recursive multi-layer folding (subtree budget 50) with single-chain exemption, using the correct XMind key `"branch": "folded"`.

## 📦 Install

Copy this repository into your agent's skills directory, e.g.:

```bash
git clone https://github.com/Chestnuts-Sisyphus/mind-world-map.git
# Claude Code / Qoder-style skill discovery (repo name != skill name on purpose;
# the trigger name stays `mindmap-engineering`):
cp -r mind-world-map ~/.claude/skills/mindmap-engineering
```

Then trigger it with `/mindmap-engineering` (or let the agent load it automatically on any mind-map task).

> **Scope note.** This repo is the *capability* (standards, gates, protocols, knowledge base). Concrete maps produced with it belong to their respective subject projects, not here. The reference pipeline and map-validation scripts were developed against a personal local workspace and are **not** part of this public package — [SKILL.md](SKILL.md) specifies what each component must do, so you can implement it in your own toolchain; `xmind validate` plus the two-generation QA checklist in SKILL.md is the executable floor.

## 🧪 How to verify a map

- `xmind validate <file>` → 0 errors is the floor, not the bar. Measured against the official
  CLI (v0.2.3) on this machine: it checks **structure only** — id uniqueness, range bounds,
  summary pairing, relation endpoints, theme roles. Warnings do not move the exit code; each of
  these does, with a distinguishable message: missing file, file that is not a zip, zip without
  `content.json`, truncated file, missing argument, unknown subcommand. Clearing `PATH` still
  exits 1 ("node" not found) instead of passing silently. On Windows, non-shell callers must
  invoke `xmind.cmd` (the bare `xmind` is an npm shim).
- The **content** standard is not machine-checked by that CLI: the minimum set (no punctuation,
  graded node length, top-level budget, fan-out cap, note invariants) has to be self-built per
  the two-generation checklist in [SKILL.md](SKILL.md).
- Headless render check: open a **copy** of the file (never the original) with GPU compositing disabled, capture the window via PrintWindow, and **poll on non-white content ratio — >2% counts as rendered**. Fixed sleep durations produce all-white false negatives (cold start measured at ~55 s of blank on the reference machine). Windows OCR requires a backslash-absolute image path.
- After any `git checkout`, re-run both gates — see [How to update](#-how-to-update).

## 🗂️ Repository layout

```
mind-world-map/
├── SKILL.md                      # entry point: standards & delivery gates (single source of truth)
├── references/
│   ├── pitfalls.md               # full pitfall archive (4 classes)
│   ├── update-protocol.md        # six-step update protocol + anti-regression safeguards
│   └── memory/                   # 6 deep-dive knowledge docs (style baseline, CLI flow, ...)
├── tools/
│   ├── sync_check.py             # master <-> mirror consistency gate (read-only)
│   └── preflight.py              # publication gate: traces / secrets / dead links / privacy (read-only)
├── .github/
│   ├── workflows/ci.yml          # runs both gates + link & structure checks
│   ├── ISSUE_TEMPLATE/           # bug / feature templates
│   └── pull_request_template.md  # contributor checklist (gates included)
├── README.md / README.zh-CN.md
├── CONTRIBUTING.md / SECURITY.md / CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── LICENSE (MIT)
├── .gitattributes                # pins eol=lf for text (see update notes on line endings)
└── .gitignore                    # keeps project-local knowledge docs out of the package
```

## 🔄 How to update

The **local skill directory is the editing master** (正本); this repository is the **public mirror**. Two facts shape the workflow:

- **Publication rules are a deterministic transform.** Local masters keep their original wording; the published face anonymises the author's identity and generalises machine-local paths, and the table lives in `tools/preflight.py`. So the mirror is *not* a byte copy of the master — it is the transform of it.
- **Line endings are pinned to LF** by `.gitattributes`; on a Windows host with `core.autocrlf=true` an editor can silently write CRLF and diverge the mirror.

Steps:

1. Edit `SKILL.md` / `references/**` in your local skill directory (e.g. `~/.claude/skills/mindmap-engineering/`).
2. Copy the changed files to the repo at the same relative paths and apply the publication rules from `tools/preflight.py`.
3. Run the two gates — both must exit 0 before you commit:

```bash
python tools/sync_check.py      # names every divergent file; pass master dirs as args, or set MINDMAP_SKILL_MASTERS
python tools/preflight.py       # names file:line for every publication-rule violation
python tools/preflight.py --self-test   # proves each check still fires
```

> Project-specific knowledge documents listed in `.gitignore` stay local by design (this repo's own migration log among them); the sync check only compares the public file set, and preflight fails if a private document ever lands inside the package.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — the short version: edit the standards in `SKILL.md` only (it is the single source of truth), never soften a rule inside a deliverable, and run both gates before opening a PR. Report suspected security issues per [SECURITY.md](SECURITY.md); participants agree to [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## 📄 License

[MIT](LICENSE)
