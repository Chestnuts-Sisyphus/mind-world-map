# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://www.keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Release notes for each tag are
generated from the matching section below, so a version without a section here cannot be released.

## v1.0.3 — 2026-09-19

Gate self-fix found by end-to-end injection testing rather than by the checklist.

- **Fixed (`tools/preflight.py`)**: the identity check labelled its findings with the tracked term
  itself (`identity:<term>`), so the scan output reproduced exactly the text the gate exists to keep
  out of the package — contradicting this release's own promise that output is `file:line rule` only.
  The rule name is now the fixed token `identity-term`; the term list stays internal to the checker.
  Found by injecting a real violation into a copy of the package and reading the gate's stdout.
- `SKILL.md` frontmatter `metadata.version` follows the release.
- No previously published tag was moved; v1.0.2 remains as released.

## v1.0.2 — 2026-09-19

Publication-hardening release: the publication review stopped being a manual sweep and became
two executable gates, and the package was aligned with the conventions of the author's other
public repositories.

- **Publication gate (`tools/preflight.py`, new)**: read-only scanner that blocks, by file and
  line number, the six classes of defect a docs-only package actually accumulates — local-machine
  traces (drive-letter paths, 8.3 short-name form as a general pattern rather than a hard-coded
  user name, user-directory segments, the local account name), credential shapes, dead relative
  links and dead document pointers, project-private documents named in public text, EN/ZH
  heading-structure drift, and identity-term regression. It also pins two conventions that used
  to live only in memory: the `SKILL.md` frontmatter key set, and ASCII-only workflow YAML
  (non-ASCII comments have silently broken GitHub Actions before). Output is `file:line rule`
  only — never the matched text — so the scan result cannot itself leak. `--self-test` injects
  one synthetic violation per category and fails if any check stops firing.
- **Identity handling (ruling of 2026-09-19)**: the public package is anonymised. The local
  editing masters keep their original wording; publication is now a deterministic transform
  (identity terms → neutral role wording, machine-local paths → a generic placeholder, pointers
  to documents outside the package → plain description) defined by the rule table in
  `tools/preflight.py`. This replaces the previous session's assumption that the retained
  mentions were deliberate attribution — that assumption was wrong and is retracted here.
- **Sync gate is portable and covers three masters (`tools/sync_check.py`)**: master directories
  are now overridable by positional arguments or `MINDMAP_SKILL_MASTERS`, the default list covers
  the `~/.claude`, `~/.qoder-cn` and `~/.qoder` install points, a missing directory is reported as
  skipped instead of failing, and a host with no local master exits 0. Comparison applies the
  publication transform, so "master edited but not published" and "published but not sanitised"
  both fail. Previously this gate could not pass on any machine but the author's while being
  documented as a pre-commit requirement.
- **No more mandatory reference to files outside the package (`SKILL.md`)**: the pipeline
  components and the map-validation gate are described by role and required behaviour, with an
  explicit note that their reference implementations live in the author's local workspace and are
  **not** shipped. The executable floor for external users is `xmind validate` plus the
  two-generation QA checklist. Option chosen over publishing a generic validator: a validation
  script that cannot be exercised against real maps on this machine would be an unverified claim.
- **Release surface**: `.github/workflows/ci.yml` runs both gates on every push and pull request;
  `ISSUE_TEMPLATE/`, `pull_request_template.md`, [CONTRIBUTING.md](CONTRIBUTING.md),
  [SECURITY.md](SECURITY.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) added; README gained
  badges that all resolve, and its repository layout now lists the files it previously referenced
  without showing them.
- **Corrections to claims made in v1.0.1's notes**:
  - "Zero local-username hits" was **not true at the time of that release** — the follow-up scan
    found one residual path written in the 8.3 short-name form, which the
    `home-directory → ~` sanitisation rule did not match. Fixed in the master copies and the
    mirror; the credential-shape conclusion is unaffected (no real secrets in the package).
  - "Master copies and mirror identical by SHA" was true of the file contents but the working
    trees still carried CRLF in several files at the time, so a later checkout would have shown a
    drift that was not a real content difference. Line endings are now normalised in the masters,
    the mirror and the derived copies alike, and the byte-level check is part of the workflow.
- **Fixed**: the local entry-point path recorded in `references/memory/mindmap-engineering-skill.md`
  pointed at a skill directory that no longer exists at that path; it now names the installed
  skill directory generically and states that the public repository is a mirror, not an editing
  entry point.

## v1.0.1 — 2026-09-18

Release-integrity follow-up on v1.0.0: the sync mechanism, the publication review, and one new
field-tested verification criterion.

- **Sync mechanism**: `tools/sync_check.py` — read-only three-way SHA256 gate between this repo mirror and the local skill master copies (exits non-zero and lists divergent files); README gains a bilingual "How to update" section establishing local skill directories as the **editing master** and this repo as the **public mirror**.
- **Line endings**: `.gitattributes` pins `eol=lf` for text files — on a machine with `core.autocrlf=true` a plain checkout silently rewrites the mirror and diverges it from the masters (hit once for real, then fixed at the source).
- **Publication review**: 5 local user home paths sanitized to `~/` across the public file set; 4 project-specific knowledge documents excluded from the public package and registered in `.gitignore` (they stay in the local masters); credential re-scan over the whole package → zero real secrets. The local-username re-scan was judged clean at the time; see the v1.0.2 corrections.
- **Rendering verification criterion** (from the first successful headless render run): capture must **poll on non-white content ratio, >2% = rendered; fixed sleep durations are forbidden** — cold start measured ~55 s of all-blank frames, so a 15 s blind grab is a guaranteed false negative. Codified in `references/pitfalls.md` §1.7 and in the new bilingual "How to verify a map" README section, together with the two machine-level facts that came out of the same run (`--disable-gpu-compositing` on a virtual-display host; Windows OCR needs a backslash-absolute path).
- README "What's inside" tables now list `tools/sync_check.py` (EN + ZH).

## v1.0.0 — 2026-09-18

First public release. Standards distilled from six rounds of real rework (2026-08-18 → 2026-09-13) on production XMind maps up to 7,600+ nodes.

- `SKILL.md`: single source of truth — pre-flight checklist, dual baselines (visual + content), total definition, term ledger & note-ification, two generations of machine QA gates, delivery gate iron rules, four-piece delivery checklist.
- `references/pitfalls.md`: full pitfall archive (file format / content organization / pipeline / collaboration).
- `references/update-protocol.md`: six-step update protocol for existing maps + three anti-regression safeguards + cold-reader narrative contracts.
- `references/memory/`: 6 deep-dive knowledge documents (style baseline, CLI local generation, narrative calibration, render-flicker compatibility, meta-memory, progress loop). Project-specific detail docs are intentionally kept out of the public package.
- Governance boundary clause (2026-09-18): the skill owns the capability only; all produced artifacts belong to the subject project that commissioned the map.
