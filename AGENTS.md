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
python tools/preflight.py --check-links-online   # external links: reports, never blocks
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

A tag triggers `.github/workflows/release.yml`, and four things are machine-enforced there, so do
them in one commit rather than hoping to notice:

1. The `CHANGELOG.md` section for that version must exist and be non-empty — no section, no
   release. Its heading is `## vX.Y.Z — YYYY-MM-DD — <subject>`; the subject becomes the GitHub
   release title (and the tag annotation), so a heading with only a date is rejected.
2. `metadata.version` in `SKILL.md` must equal the tag. Cutting a release therefore also bumps the
   version, and the gate that compares the two is why version and tag always travel together.
3. The tag must point at `main` HEAD. A tag on an older commit fails the workflow before anything
   is published.
4. Push the branch and the tag in one command (`git push origin main vX.Y.Z`), otherwise the CI run
   for the version bump sees a version with no tag yet and reports the drift.

Protection tier as actually configured: CI is a required status check on `main`, force-push and
deletion are off, `.github/CODEOWNERS` merely suggests reviewers because required review is **not**
enabled, and administrators can still bypass the required check (which is then recorded in the
release notes of the round that did it).

## Credentials and accounts

Do not commit tokens, cookies, private keys or connection strings, and do not put a
credential's value in an issue, PR or log — record only where it lives. Publishing here
touches one repository only; do not push, tag or change settings for any other project
from this one.
