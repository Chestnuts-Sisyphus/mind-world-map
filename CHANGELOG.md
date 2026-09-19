# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://www.keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Release notes for each tag are
generated from the matching section below, so a version without a section here cannot be released.

## [Unreleased]

- **Changed (release policy)**: version numbers now follow strict semantic versioning, stated
  rather than implied. New executable checks shipped inside `tools/` are a **minor** bump, a fixed
  or tightened check is a **patch**, documentation-only work rides along with whichever code round
  it lands in. The next cut is therefore **v1.2.0**: this round adds machine checks to
  `tools/preflight.py` (bare script-name reference, tracked-binary guard) and to
  `tools/validate_xmind.py` (folding key, banned visual markers). Published tags are never moved or
  retargeted, and every cut leaves a local `pre-vX.Y.Z` tag at the previous HEAD, unpushed, so a
  rollback point exists without touching the public ref list.
- **Added (`tools/preflight.py`)**: two more shapes of the `external-command-ref` rule -- a bare
  script name with no `python` prefix, and a `module.member` code reference. Both read as
  "run this" to a reader, and the old rule measured 24 unlabelled references across SKILL.md, the
  reference docs and the published memory notes: a project-side builder script name, and a
  project-side module's function -- neither shipped with this package. Package self-pointers are judged
  by directory prefix rather than file existence, because install-point layouts have no `examples/`
  and the verdict must not depend on where the gate runs; config keys and build artefacts are
  excluded after three measured false positives. Each new shape has a positive, negatives (labelled
  line, package self-reference) and a reverse-wiring proof that blinds the shape and watches the
  same violation go quiet. Self-test 40 -> 47 cases.
- **Added (`tools/preflight.py`)**: `tracked-binary` names any binary among the tracked files (NUL
  sniff over the first 8 KB of each), and the whitelist is deliberately empty because this package
  ships no binaries -- one would be unreadable, undiffable and unverifiable from a clean clone. The
  rule keeps working where there is no git: an install-point layout scans the package directory
  instead, so it never quietly switches off, and output is path plus rule name only. Measured end to
  end: staging a probe PNG made the repository gate exit 1 naming it (with `crlf-in-tracked-file`
  and the README's `unlisted-tracked-file` firing alongside), unstaging returned it to 0, and the
  same file dropped into a master skill directory fired there too. Self-test 47 -> 50 cases.
- **Added (`tools/sync_check.py`)**: registered private documents (the local-only notes that
  `.gitignore` deliberately keeps out of the package) are now compared byte-for-byte *between* the
  local masters -- 5 documents measured on this machine. A master that does not carry a given
  private document is skipped rather than reported, because a fresh machine legitimately has fewer
  files, while a real divergence must be named. Proved end to end: one appended line inside a
  second master's copy of the migration handover note made the sync gate exit 1 naming that
  document and all three
  masters, and restoring the bytes returned it to 0. Self-test 13 -> 17 cases, including the
  skip-does-not-cry case and a reverse-wiring proof that comparing only the first byte lets drift
  through. The success line now states how many private documents were actually compared, so the
  check cannot pass by silently checking nothing.
- **Added (`.github/workflows/link-watch.yml`)**: the advisory link sweep now has its own trigger so
  a dead external target surfaces on its own rather than whenever somebody happens to push --
  weekly (Monday 06:30 UTC) and on demand via `workflow_dispatch`, both non-blocking, with the
  outcome written into the run's step summary (which links were unreachable, or that all answered).
  Scheduled workflows only fire from the default branch, so this file is inert until the release
  carrying it lands on `main`.
- **Added (`tools/validate_xmind.py`)**: two more content checks, taking the shipped set from six to
  eight. `folding-key` accepts only `"branch": "folded"` and names `"folded": true`, `"collapsed"`
  and a `branch` value that is not `folded` -- those keys do not fold *at all*, the failure that cost
  a whole rebuild on 09-04. `visual-marks` bans `labels` / `markers` on any topic and relationship
  lines at sheet level (the standard that killed 7 test connectors on 09-04). Fixtures per check, a
  compliant-folding negative so the new rules are not noise, reverse-wiring per rule, `--emit-fixture`
  for all of them, and end-to-end proof on real `.xmind` files: exit 1 naming `folding-key`,
  `visual-marks` and the sheet-level line case, exit 0 for the correct key, zero regression on the
  example map and the older fixtures. Self-test 37 -> 58 cases.

## v1.1.1 — 2026-09-19 — External links get watched, and the docs stop overstating protection

Follow-up to v1.1.0: the last class of unwatched pointer is now covered, and the governance docs
say what branch protection actually enforces rather than what it looks like it enforces.

- **Added (`tools/preflight.py`)**: `--check-links-online` sweeps every http(s) target in the
  package and reports `dead-online-link` with the status code and host only, never the surrounding
  text. It is advisory by default -- somebody else's uptime is not a reason to block a release --
  and becomes blocking under `--strict-links`. A status it cannot determine (offline, DNS failure,
  timeout) is deliberately *not* a dead link, otherwise the check would cry wolf on every laptop.
  Four self-test cases cover 404 / 200 / undecidable / reverse-wiring (blind the collector and the
  check goes quiet); end to end, a real 404 link written into README.md made the blocking run exit
  1 naming that line while the advisory run stayed at 0, and removing it restored both. CI runs the
  advisory form as its own step. Measured on the package as published: 10 distinct links, all 200.
- **Changed (`CONTRIBUTING.md`, `AGENTS.md`)**: the release recipe now matches what the workflow
  actually enforces (subject-bearing section heading, version bumped in the same commit as the tag,
  tag on `main` HEAD, both refs pushed together), and the protection tier is stated honestly:
  CI is required, `.github/CODEOWNERS` only suggests reviewers because required review is off, and
  admins can still bypass the check.
- **Fixed (`README.zh-CN.md`)**: the Chinese component table had never gained the delivery-gate and
  examples rows its English twin got, so the two READMEs disagreed about what ships in the package.

## v1.1.0 — 2026-09-19 — The delivery gate now ships inside the package

The capability loop is closed inside the package: a shipped map can now be verified with code
that lives here, the data/build paradigm has a runnable example, every publisher tool proves
itself, and the publication and release paths gained machine checks.

- **Added (`tools/publish.py`, `tools/sync_check.py`, `tools/release_notes.py`)**: each now
  carries its own `--self-test`, run inside a throwaway temp directory so no real install
  point is ever written. The publisher proves mirror hygiene, idempotence, edit-source
  direction and the non-repo refusal; the sync gate proves drift and unredacted-mirror
  detection in both layouts; the extractor proves heading variants and refuses a
  bare-version title. CI runs all four self-tests.
- **Added (`tools/preflight.py`)**: two more publication checks -- `crlf-in-tracked-file`
  (byte-level carriage-return scan of every tracked text file, because the shell-level
  equivalent false-reports under Git Bash) and `version-tag-drift` (the version declared in
  SKILL.md metadata must equal the newest tag, so the "bumped by hand and forgot" case is now
  machine-caught). Both have a firing case and a whitelisted case in `--self-test`;
  `crlf-in-tracked-file` was additionally proven end to end by writing a real CRLF into
  README.md, watching the gate name it, and restoring the file.
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
- **Added (`tools/preflight.py`)**: the external-reference check no longer recognizes only the
  interpreter-plus-script shape. It now also names script files by extension (ps1, cmd, bat, vbs,
  psm1, pyw), scheduled-task names, startup shortcut entries, registry program-identifier keys
  and their open-command values, and reboot commands -- all reported as
  `external-command-ref`, location + rule name only. A reasoned allow-list keeps the official
  CLI's npm shim name (and friends) from being false positives, proven by a negative case in
  `--self-test`.
- **Changed (`references/memory/xmind-render-flicker-compat.md`)**: the eight lines that the new
  shapes caught are annotated in place as author-machine history (「作者本机历史，外部不可
  复用」) rather than deleted -- the reusable conclusions (GPU compositing is the root cause,
  SendKeys lands in the node editor, PowerShell 5.1 misreads BOM-less UTF-8 scripts) stay, while
  the task names, workspace script paths, file-association guard and reboot window are now
  explicitly marked as not shipped and not reproducible elsewhere.
- **Added (SKILL.md)**: a one-line glossary for the three private names that appear in the docs
  (`Connectome`, `ZCode`, `MindmapLoop`), so an outside reader can parse the references without
  the names being stripped from the history.
- **Added (release workflow)**: the workflow now compares the tag's commit against `main` HEAD and
  fails before creating anything when they differ, so "tagged an old commit and shipped a Release"
  is machine-refused rather than a review habit. Proven red by tagging a historical commit and
  watching the run fail with no Release created.
- **Changed (release workflow, `tools/release_notes.py`)**: the Release title is no longer the bare
  tag. It is assembled as version + the section subject from CHANGELOG, and the extractor refuses
  a heading that carries no subject -- a date-only section can no longer produce a six-character
  release name. Section headings now follow the convention version — date — subject.
- **Changed (workflows)**: both workflows pin their third-party actions by commit SHA instead of
  a mutable major tag, and `.github/dependabot.yml` (github-actions ecosystem, weekly, prefixed
  commit) is what keeps those pins current -- without it a SHA pin silently rots.

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
