# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://www.keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Release notes for each tag are
generated from the matching section below, so a version without a section here cannot be released.

## [Unreleased]

- **Added (`tools/publish.py`, `tools/sync_check.py`, `tools/release_notes.py`)**: each now
  carries its own `--self-test`, run inside a throwaway temp directory so no real install
  point is ever written. The publisher proves mirror hygiene, idempotence, edit-source
  direction and the non-repo refusal; the sync gate proves drift and unredacted-mirror
  detection in both layouts; the extractor proves heading variants and refuses a
  bare-version title. CI runs all four self-tests.
- **Added (`tools/validate_xmind.py`)**: the delivery gate is finally executable from inside the
  package. It unpacks `content.json` and enforces the content minimum set -- punctuation ban,
  graded node length (2-7 organisational / 2-12 leaf, ASCII term keys exempt), top-level budget
  <= 9, fan-out <= 13, the four note invariants (line shape, flush-left term present in the
  title, one term once, dependency chain closed and acyclic) and `right-number` vs the real
  branch count. Exit 0 / 1 (names `node id + rule`, excerpt capped at 40 characters) / 2
  (unreadable file). `--self-test` carries synthetic fixtures for every check plus a reverse
  wiring proof (unregister one check and its fixture goes green); `--emit-fixture` dumps any
  fixture as a real `.xmind`.
- **Added (`examples/`)**: a runnable data/build pair. `example_data.py` holds the content, the
  term ledger and the structure plan; `example_build.py` assembles `content.json`, zips an
  `.xmind`, sets `right-number` automatically, asserts plan coverage (missing or extra child
  titles fail the build) and verifies the output with the gate above. `--self-test` is the
  reverse proof: corrupt one title in the data and the chain goes red. README gained the
  "Run your first map" / 「跑通第一张图」 four-command section.
- **Changed (docs)**: SKILL.md delivery gate #1 and README now point at the in-package
  validator instead of declaring that map validation lives only in the author's workspace; the
  remaining "not shipped" boundary is the project-specific builders, nothing else.
- **Changed (`tools/preflight.py`)**: the publication scan now covers `.py` files outside
  `tools/`, i.e. the example content (node titles and term definitions are published surface and
  must carry no local-machine trace). End-to-end proof: adding a drive-letter path to
  `examples/example_data.py` made the gate exit 1 naming that file; removing it returned 0.
- **Added (`tools/preflight.py`)**: the external-reference check no longer recognizes only
  `python X.py`. It now covers script files (`.ps1/.cmd/.bat/.vbs/.psm1/.pyw`), scheduled-task
  names (`schtasks /TN`, 计划任务 X), Startup `.lnk` entries, registry shapes (`ProgId`,
  `shell\open\command`, `HKLM\...`) and reboot commands -- all reported as
  `external-command-ref`, location + rule name only. A reasoned allow-list keeps the official
  CLI's `xmind.cmd` (and friends) from being false positives, proven by a negative case in
  `--self-test`.
- **Changed (`references/memory/xmind-render-flicker-compat.md`)**: the eight lines that the new
  shapes caught are annotated in place as author-machine history (「作者本机历史，外部不可
  复用」) rather than deleted -- the reusable conclusions (GPU compositing is the root cause,
  SendKeys lands in the node editor, PS 5.1 misreads BOM-less UTF-8 scripts) stay, while the
  task names, workspace script paths, ProgId guard and reboot window are now explicitly marked
  as not shipped and not reproducible elsewhere.
- **Added (SKILL.md)**: a one-line glossary for the three private names that appear in the docs
  (`Connectome`, `ZCode`, `MindmapLoop`), so an outside reader can parse the references without
  the names being stripped from the history.

## v1.0.7 — 2026-09-19

Last gate-correctness patch of this round, found by running the documented commands from the
install-point layout rather than only from the repo.

- **Fixed (`tools/preflight.py`)**: `--self-test` exited 1 when run from an installed skill
  directory. The private-doc case asserted through `check_private_present`, which by design
  returns nothing outside a repo layout (masters legitimately keep private docs), so the
  injected violation could never fire there -- the gate's own self-proof was layout-dependent
  while the "all three gates green from either layout" claim was not. The reporting step is now
  a layout-independent function the self-test asserts against; the real scan still skips the
  install layout. Measured: 22 PASS / 0 FAIL and exit 0 in the repo and in all three masters.

## v1.0.6 — 2026-09-19

Gate-integrity patches after v1.0.5; released so `main` and the newest tag stay equal.

- **Fixed (`tools/preflight.py`, security of the gate itself)**: the gate applied the
  publication transform *before* scanning, so a published file that actually contained a
  drive-letter path or an identity term was anonymised into cleanliness and reported green.
  Proven by injection: writing the term into a copy exited 0. Repo mirrors are now scanned as
  written; only an install-point run (where the master legitimately holds raw text) scans the
  transformed view. Injection then exits 1 naming file:line, without echoing the matched text.
- **Changed (`tools/identity-terms.tsv`)**: the block term is stored escaped, because the word
  list ships with the package -- keeping it in plain text published the very word the gate
  exists to keep out. No tracked file now contains it.
- **Fixed (`SECURITY.md`)**: the public description of the gate's coverage lagged reality on two
  counts (it undercounted the tools and omitted the three new check categories).

## v1.0.5 — 2026-09-19

One-line workflow fix, released as a patch so that `main` and the newest tag stay equal.

- **Fixed (`release.yml`)**: releases the workflow creates now carry a title. The first
  workflow-created release came out nameless while every hand-made release in this repo had one.

## v1.0.4 — 2026-09-19

Second hardening round, driven by artifacts rather than by the previous round's self-report.

- **Added (`tools/publish.py`)**: the master-to-mirror publication transform finally has an
  executable, idempotent entry point in the package; the step used to be performed by a
  throwaway script that was never published. `tools/**` is distributed back to every skill
  install point, so the gate commands documented in `SKILL.md` are runnable there too.
- **Added (gates)**: three detection categories the injection tests proved were missing --
  local network details (loopback endpoints, proxy ports), personal-identity shapes (email
  forms), and documentation that commands a script this package does not ship. The identity
  word list moved out of code into `tools/identity-terms.tsv`, where every exemption carries
  a reason. Repository layout and the "What's inside" table are checked against
  `git ls-files` in both directions.
- **Added (release path)**: `tools/release_notes.py` extracts a release body from the matching
  changelog section, and `.github/workflows/release.yml` publishes a tag with it -- no
  section, no release.
- **Added (governance)**: `AGENTS.md`, `.github/CODEOWNERS`, branch protection on `main`
  requiring CI, and Dependabot security alerts enabled.
- **Fixed**: four `references/**` lines told readers to run scripts that are not in the
  package; they now say so on the same line and point at the executable landing spot.
  A local proxy port in the render-flicker notes was machine detail with no documentation
  value. `xmind validate` is now described by what it actually measures (structure, five
  classes, exit-code semantics) rather than by hope.
- **Process note**: branch protection landed the same round as this release, so the release
  commit went to `main` directly by the maintainer (`enforce_admins` is off). CONTRIBUTING
  asks that such bypasses be booked here rather than left implicit.

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
