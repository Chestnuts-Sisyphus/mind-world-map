# Contributing

Thanks for taking the map-quality problem seriously. This repository is a *capability* package:
standards, machine gates, protocols and a knowledge base. Concrete maps produced with it belong to
whatever project commissioned them, not here.

## What this repository is for

- `SKILL.md` — the single source of truth for the standards and the delivery gates.
- `references/` — pitfall archive, update protocol, deep-dive knowledge documents.
- `tools/` — the gates that keep the published text honest, plus `publish.py`, the one writer
  (see below).

## Before you open a pull request

Run the gates from a clean checkout; every one must exit 0:

```bash
python tools/publish.py --check           # master / mirror / installed-tools drift, no writes
python tools/preflight.py                 # publication review: traces / secrets / dead links / privacy
python tools/preflight.py --self-test     # proves each check still fires
python tools/sync_check.py                # only meaningful if you keep local skill master copies
```

`sync_check.py` compares the repository against your **local editing masters** with the publication
transform applied. Point it at your own master directories if they live elsewhere:

```bash
python tools/sync_check.py ~/.claude/skills/mindmap-engineering
MINDMAP_SKILL_MASTERS="~/a/skills/mindmap-engineering;~/b/skills/mindmap-engineering" python tools/sync_check.py
```

If you have no local masters, the gate reports that it skipped and exits 0 — CI relies on that.

## Releasing

The changelog is the only source of release notes, so the `[Unreleased]` section has a job:

1. During ordinary work, every user-visible change gets a bullet under `## [Unreleased]`.
2. To release, rename that section to `## vX.Y.Z — YYYY-MM-DD` and open a fresh, empty
   `## [Unreleased]` above it in the same commit. The publication gate checks that
   `[Unreleased]` exists and sits before the first version heading.
3. Push to `main` and wait for CI, then tag: `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`.
4. `.github/workflows/release.yml` re-runs the gates, extracts that version's section with
   `python tools/release_notes.py vX.Y.Z`, and creates the release with it. No section, or an
   empty one, fails the workflow instead of publishing a release with invented notes.

`main` is protected: CI (the gates above) has to pass first, and a maintainer push that
bypasses it is recorded in the release notes of the round that did it.

## Changing the standards

`SKILL.md` is the only place a standard may change. Two rules that come from real rework:

1. **Never soften a rule inside a deliverable.** Loosening a limit (node-length budgets, punctuation
   ban, fan-out caps) because one map is inconvenient has been tried and reverted; if a standard is
   wrong, propose the change on its own with evidence, and it applies going forward to every map.
2. **A gate that cannot fail must not be trusted.** Any new check ships with a synthetic violation
   that proves it fires — add it to `--self-test` in `tools/preflight.py`. A green gate nobody
   injected a fault into is not a green gate.

## Text conventions

- Markdown documents are bilingual pairs where a pair exists (`README.md` / `README.zh-CN.md`); the
  two must keep the same heading structure, which `preflight.py` enforces.
- Workflow YAML is ASCII-only — non-ASCII comments have broken GitHub Actions silently.
- Line endings are LF, pinned in `.gitattributes`. On a host with `core.autocrlf=true`, check that
  your editor did not write CRLF before committing; `git diff` can look empty while the working
  tree diverges.
- Keep machine-local detail out of the published text: no absolute paths with a drive letter, no
  local account names, no references to documents that are not in the package. `preflight.py` names
  the offending file and line.

## Scope discipline

Issues about a specific produced map (its structure, coverage gaps, or triage backlog) belong to the
project that owns that map, not here. Issues here are for the capability: standards, gates,
tooling, and the knowledge documents.
