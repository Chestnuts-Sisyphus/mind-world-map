# Instructions for AI agents working in this repository

This repo is a **skill package**: standards, gates and knowledge about producing mind
maps. It is not an application, and it does not contain the maps themselves. Read this
file before editing anything here.

## Where text is authored

`SKILL.md` and `references/**` are mirrors of an editing master that lives in a local
skill directory. The public face is a **deterministic transform** of that master
(anonymised author identity, generalised machine-local paths), and the transform table
lives in `tools/preflight.py`.

- Do not hand-edit the repo copy of `SKILL.md` / `references/**` as if it were the
  source: the next publish would overwrite it. Edit the master, then run
  `python tools/publish.py` from the repo root, which regenerates the mirror and
  distributes `tools/**` back to every install point.
- If no master directory exists on this machine, the repo copy is the only copy — edit
  it directly, and `tools/sync_check.py` will exit 0 instead of pretending to compare.
- `tools/**` is authored **in the repo**. Masters receive copies; never edit a master's
  `tools/` file expecting it to flow back.

## Gates (all three must exit 0 before you commit)

```bash
python tools/publish.py --check     # drift between master, mirror and installed tools
python tools/preflight.py           # publication surface: traces, secrets, dead links, privacy
python tools/preflight.py --self-test   # proves every check category still fires
python tools/sync_check.py          # master <-> mirror equality (skips absent masters)
```

Every new detection rule needs an end-to-end demonstration before it ships: write a real
violation into a copy of the package, run the documented command, read stdout, and confirm
the gate exits non-zero **without echoing the matched text**. A unit self-test alone is not
evidence. Equally, prove the exemptions: a gate that fires on everything is noise.

## Hard rules

- **Standards are not negotiable inside a deliverable.** `SKILL.md` is the single source of
  truth for the mind-map standard. Do not relax a threshold (node-length bands, top-level
  budget, fan-out cap, punctuation ban) to make a check pass. If a standard is wrong,
  propose the revision in the PR description and keep the numbers untouched.
- **Deliverables belong elsewhere.** Maps produced with this skill are owned by the subject
  project that commissioned them, not by this repo. Do not add `.xmind` files or
  per-project build scripts here.
- **No machine-local traces.** Absolute drive paths, user-directory segments, 8.3 short
  names, local hostnames or ports, personal identity shapes, and commands that point at
  scripts this package does not ship. If a document must reference an out-of-package
  script, the same line has to say it is not part of this package.
- **Reviewed word list, not ad-hoc banning.** Identity/anonymisation terms are configured in
  `tools/identity-terms.tsv`; every entry is either `block` or `exempt` **with a reason**.
- **Line endings are LF**, pinned by `.gitattributes`. After editing, verify no CRLF bytes
  slipped in (`b"\r\n"` in the file), because an editor on Windows can add them silently.
- **Workflow YAML stays ASCII.** Non-ASCII text in `.github/workflows/*.yml` can silently
  disable the workflow; `preflight` fails the build on it.
- **Never echo detection payloads.** Scan output reports `file:line rule` and nothing else.

## Adding or removing a file

The repository layout block and the "What's inside" table in `README.md` /
`README.zh-CN.md` are machine-checked against `git ls-files` in both directions: a listed
path that does not exist, and a tracked file that is not listed, are both failures. So when
you add a file, update the tree, the table, and `CHANGELOG.md` in the same change.

## Releasing

`main` is protected: CI (the gates above) must pass. A tag triggers
`.github/workflows/release.yml`, which builds the release body from the matching
`CHANGELOG.md` section and **fails if that section is missing** — so cut the changelog
entry first, then tag. Release notes are never written by hand twice.

## Credentials and accounts

Do not commit tokens, cookies, private keys or connection strings, and do not put a
credential's value in an issue, PR or log — record only where it lives. Publishing here
touches one repository only; do not push, tag or change settings for any other project
from this one.
