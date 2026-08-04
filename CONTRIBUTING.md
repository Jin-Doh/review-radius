# Contributing to Review Radius

Thank you for helping improve Review Radius. Keep changes bounded, reviewable,
and supported by evidence.

## Before opening a pull request

1. Start from the latest `main` and use a focused branch.
2. Explain the underlying problem or violated contract, not only the edited
   line.
3. Inspect credible related locations for the same defect class.
4. Update source-of-truth documentation when behavior or workflow changes.
5. Run the repository checks:

```sh
python3 -m unittest discover -s tests -v
npx --yes markdownlint-cli2@0.23.2 '**/*.md' '#.git/**'
npx --yes skills@1.5.21 add "$PWD" --list --agent codex
```

## Pull request policy

All changes to `main` use a pull request and pass the `quality` check. The
repository currently has one human maintainer, so the required approving review
count is intentionally **zero**. CODEOWNERS records responsibility but does not
create an approval requirement.

Automated Codex review is advisory evidence, not a required human approval and
not a substitute for the test suite. Address each actionable Codex finding,
reject incorrect findings with evidence, and resolve every review conversation
before merge.

Only squash merging is enabled. Keep the pull request title suitable for the
resulting commit message.

## Scope and evidence

- Prefer cause-level minimal fixes over line-level patches or unrelated cleanup.
- Record untested scope and remaining uncertainty.
- Do not claim repository-wide completeness from one search tool or a synthetic
  experiment.
- Do not include credentials, private repository content, production data, or
  generated secrets in issues, pull requests, fixtures, or logs.

## Security reports

Do not open a public issue for a suspected vulnerability. Follow
[SECURITY.md](SECURITY.md) and use GitHub's private vulnerability reporting.
