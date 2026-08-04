# GitHub live repository verification

Observed: 2026-08-04

Repository: `Jin-Doh/review-radius`

Ruleset ID: `20354884`

## Activation evidence

- The repository is public and `main` is the default branch.
- The first repaired pull request merged without a human approval and only
  after the `quality` check passed.
- The merge result passed `Quality` again on `main` in
  [run 30881280765](https://github.com/Jin-Doh/review-radius/actions/runs/30881280765).
- The active ruleset API returned approving reviews `0`, CODEOWNER approval
  disabled, last-pusher approval disabled, conversation resolution enabled,
  squash-only merge, required `quality`, linear history, deletion protection,
  and non-fast-forward protection.
- The only bypass actor is `@Jin-Doh`, and the API reports bypass mode
  `pull_request` rather than `always` or `exempt`.
- Repository Actions permissions are read-only and workflows cannot approve
  pull requests.
- Actions are restricted to GitHub-owned actions and full-length commit SHA
  references.
- Secret scanning, push protection, dependency alerts, automated security
  fixes, and private vulnerability reporting are enabled.

## Post-activation merge-path proof

Verification pull request:
[PR #3](https://github.com/Jin-Doh/review-radius/pull/3).

The verification pull request adds this record after ruleset activation. It
must demonstrate that a maintainer-authored change is blocked while `quality`
is pending and becomes mergeable with zero approving reviews after the check
passes. Merge must use squash and leave `main` green.

## Interpretation

This snapshot proves the configured state at the observation time. It does not
prevent a repository administrator from changing settings later. The checked-
in ruleset payload, policy tests, and periodic live audits are the drift
detection boundaries.
