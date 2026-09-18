# 🧠 Mindmap Engineering

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

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
# Claude Code / Qoder-style skill discovery (repo name ≠ skill name on purpose;
# the trigger name stays `mindmap-engineering`):
cp -r mind-world-map ~/.claude/skills/mindmap-engineering
```

Then trigger it with `/mindmap-engineering` (or let the agent load it automatically on any mind-map task).

> **Scope note.** This repo is the *capability* (standards, gates, protocols, knowledge base). Concrete maps produced with it belong to their respective subject projects, not here. The reference pipeline scripts (builders, restructurers, validators) were developed against a personal local workspace and are not part of this public package; the methodology docs describe their required behavior in full detail.

## 🗂️ Repository layout

```
mind-world-map/
├── SKILL.md                      # entry point: standards & delivery gates (single source of truth)
├── references/
│   ├── pitfalls.md               # full pitfall archive (4 classes)
│   ├── update-protocol.md        # six-step update protocol + anti-regression safeguards
│   └── memory/                   # 6 deep-dive knowledge docs (style baseline, CLI flow, ...)
├── README.md / README.zh-CN.md
├── LICENSE (MIT)
└── CHANGELOG.md
```

## 📄 License

[MIT](LICENSE)
