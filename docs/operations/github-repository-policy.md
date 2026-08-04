# GitHub repository safety policy

Canonical repository: `Jin-Doh/review-radius`

## Safety posture

The repository balances public contribution safety with a single-maintainer
reality. `main` requires pull requests but deliberately requires **zero**
approving reviews. The enforced controls are deterministic checks and visible
review resolution rather than an impossible second-person approval.

## Enforced `main` ruleset

The API payload in `.github/rulesets/main.json` is the checked-in source of
truth. The active rules are:

- pull request required;
- approving review count `0`;
- CODEOWNER approval disabled;
- last-pusher approval disabled;
- every review conversation resolved;
- required `quality` status check against the latest `main`;
- squash merge only and linear history required;
- force pushes and branch deletion blocked;
- `@Jin-Doh` may bypass only from a pull request for break-glass recovery.

Codex automated review is advisory. Do not configure it as a required approval.
If it later exposes a stable, separately named status check with acceptable
availability, that check may be evaluated independently before becoming a gate.

## Repository settings

- Public visibility; issues and pull requests enabled; wiki and projects off.
- Squash merge and auto-merge enabled; merge commits and rebase merge disabled.
- Head branches deleted after merge and branch updates allowed.
- GitHub Actions receives read-only `GITHUB_TOKEN` permissions and cannot
  approve pull requests.
- Secret scanning, push protection, dependency alerts, automated security fixes,
  and private vulnerability reporting enabled when supported for the repository.
- Dependabot checks GitHub Actions weekly.

## Break-glass procedure

Use the pull-request-only bypass only when the required check itself is broken
and cannot be repaired through the normal green path.

1. Open a focused repair pull request.
2. Record the failing check, why it cannot pass, and the smallest repair.
3. Run equivalent checks locally and attach the output.
4. Resolve automated review conversations.
5. Use the ruleset bypass from the pull request and squash merge.
6. Confirm the `quality` workflow passes on `main` after merge.

Never disable the ruleset merely to skip ordinary failures. Any lasting policy
change must update the checked-in payload and this document in the same pull
request.

## Audit

After changing settings, compare the live repository, Actions permissions, and
ruleset JSON with this document and `.github/rulesets/main.json`. GitHub UI state
or a successful push alone is not proof that every setting is active.
