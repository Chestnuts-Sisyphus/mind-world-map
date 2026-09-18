# Changelog

## [Unreleased]

### Fixed

- **Sanitization gap**: one residual local-username path in `references/memory/xmind-cli-local-generation.md` — the 8.3 short form (`ADMINI~1`) bypassed the `C:/Users/<user> → ~` rule used in the v1.0.1 publication review. Reworded to a username-free, drive-letter-free equivalent without losing the pitfall (Git Bash `/tmp` resolves to the user temp dir while the file-writing tool resolves it to a drive root; CLI paths must be explicit Windows absolute paths). All local master copies and the repo mirror re-synced (SHA256 identical).

### Correction

- The v1.0.1 claim "zero local-username hits" was **not true at the time of that release** — the 09-19 re-scan above found and fixed the miss. The credential/secret-shape re-scan conclusion is unaffected (no real secrets in the package).

## v1.0.1 — 2026-09-18

Release-integrity follow-up on v1.0.0: the sync mechanism, the publication review, and one new field-tested verification criterion.

- **Sync mechanism**: `tools/sync_check.py` — read-only three-way SHA256 gate between this repo mirror and the local skill master copies (exits non-zero and lists divergent files); README gains a bilingual "How to update" section establishing local skill directories as the **editing master** and this repo as the **public mirror**.
- **Line endings**: `.gitattributes` pins `eol=lf` for text files — on a machine with `core.autocrlf=true` a plain checkout silently rewrites the mirror and diverges it from the masters (hit once for real, then fixed at the source).
- **Publication review**: 5 local user home paths sanitized to `~/` across the public file set; 4 project-specific knowledge documents (`cm-closure-mindmap-pipeline`, `cm-zhongshen-mindmap-delivered`, `connectome-cm-core-definition`, `connectome-mindmap-project`) excluded from the public package and registered in `.gitignore` (they stay in the local masters); credential re-scan over the whole package → zero real secrets; the local-username path re-scan was judged clean at the time but missed one 8.3 short-name form, fixed later (see [Unreleased]).
- **Rendering verification criterion** (from the first successful headless render run): capture must **poll on non-white content ratio, >2% = rendered; fixed sleep durations are forbidden** — cold start measured ~55 s of all-blank frames, so a 15 s blind grab is a guaranteed false negative. Codified in `references/pitfalls.md` §1.7 and in the new bilingual "How to verify a map" README section, together with the two machine-level facts that came out of the same run (`--disable-gpu-compositing` on a virtual-display host; Windows OCR needs a backslash-absolute path).
- README "What's inside" tables now list `tools/sync_check.py` (EN + ZH).

## v1.0.0 — 2026-09-18

First public release. Standards distilled from six rounds of real rework (2026-08-18 → 2026-09-13) on production XMind maps up to 7,600+ nodes.

- `SKILL.md`: single source of truth — pre-flight checklist, dual baselines (visual + content), total definition, term ledger & note-ification, two generations of machine QA gates, delivery gate iron rules, four-piece delivery checklist.
- `references/pitfalls.md`: full pitfall archive (file format / content organization / pipeline / collaboration).
- `references/update-protocol.md`: six-step update protocol for existing maps + three anti-regression safeguards + cold-reader narrative contracts.
- `references/memory/`: 6 deep-dive knowledge documents (style baseline, CLI local generation, narrative calibration, render-flicker compatibility, meta-memory, progress loop). Project-specific detail docs (CM pipeline evolution, subject definitions, delivery records) are intentionally kept out of the public package.
- Governance boundary clause (2026-09-18): the skill owns the capability only; all produced artifacts belong to the subject project that commissioned the map.
