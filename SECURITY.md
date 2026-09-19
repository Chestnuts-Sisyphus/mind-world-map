# Security Policy

## Scope

This repository publishes an agent skill: Markdown standards, knowledge documents and two
read-only Python gates. It ships no service, no network layer, and no credentials. The realistic
security surface is therefore **information disclosure through the published text** — a document
that leaks a machine-local path, an account name, a private file name, or a credential-shaped
string that once existed in a working copy.

The publication gate exists for exactly this: `tools/preflight.py` blocks drive-letter paths,
8.3 short-name forms, user-directory segments, the local account name, credential shapes, and
private documents named in public text, and it is enforced on every push by
[`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Reporting a vulnerability

If you find a disclosure or any other security issue:

1. Do **not** open a public issue.
2. Report it through GitHub's private vulnerability reporting for this repository
   (Security tab → "Report a vulnerability"), or open a draft pull request against a branch you
   control if the fix is public-safe.
3. Do not include the leaked value in the report body. Point at the file and line number instead —
   that is enough to act on, and it keeps the report from becoming a second copy of the leak.

We aim to acknowledge within 7 days. If a credential was ever committed, rotation is the fix —
history rewriting is not, and we will say so plainly.

## Hardening notes for maintainers

- Scan output must never quote matched content. `preflight.py` prints `file:line rule` only; keep
  it that way when adding checks.
- Never commit real tokens, cookies, private keys or connection strings, including in test
  fixtures. Keep secrets in the local toolchain's own credential store and reference them by
  variable name in documentation.
- Archived, pre-sanitisation copies of the skill must be marked as unfixed so they are never
  published from.
