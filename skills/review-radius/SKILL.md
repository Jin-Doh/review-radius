---
name: review-radius
description: Handle repeated GitHub PR review/fix cycles, GitHub PR review churn, and non-converging GitHub PR feedback end to end when asked to inspect or address review comments, requested changes, unresolved threads, or follow-up reviews; validate each comment, derive the underlying invariant, audit related code for the same defect class, implement bounded fixes, and report independent review, QA, and delivery states.
---

# Review Radius

Fix the pattern behind the comment. Treat review comments as observations of a
possible defect class, not as a work queue and not as the complete defect
surface. Keep inspection broad enough to establish impact, but keep edits inside
the approved PR boundary unless the user explicitly authorizes an expansion.

This routing description helps a host select the Skill for GitHub PR feedback.
The Skill cannot monitor, dispatch, call, or invoke itself when it was not
selected.

## Mandatory entry path

For every session that may patch code or request another automated review:

- initialize persisted state with
  [`scripts/session_control.py`](scripts/session_control.py) before changing
  code;
- read
  [Executable session control](references/executable-session-control.md) before
  the first controller command;
- read [Review governor](references/review-governor.md) before projecting
  architecture, impact, verification, or patch signals;
- reconstruct prior PR history with
  [Campaign convergence and strategy reset](references/review-campaign.md) when
  the PR already has review/fix history;
- use a successful, current-head controller guard immediately before every
  patch and automated review request;
- never reinterpret a denied, stale, malformed, blocked, or incomplete result as
  permission to continue.

The executable controller owns session identity, repository and PR binding,
base/current head, immutable cutoff, fixed deadline, initial thread set,
deferred feedback, patch rounds, fuse budget, named pauses, scope fingerprint,
governor result, and single-use action authorization. Do not reconstruct or
rewrite those fields from model memory.

## Non-negotiable controls

- **Patch authority:** only a fresh `CONTINUE_LOCAL` decision followed by a
  successful `guard --action patch` permits an automatic edit. Consume its
  single-use token with `record-patch` after an immutable new head exists.
- **Review retrigger authority:** request another automated review only after a
  fresh `CONVERGED` decision and successful
  `guard --action request-review`. The controller permits at most one request
  per head.
- **Fuse:** the default automatic patch budget is two rounds. A third required
  patch is denied as `AUTOMATION_FUSE_EXHAUSTED`. A recorded user direction may
  extend the budget; it never resets earlier rounds.
- **Frozen admission:** feedback created after the immutable cutoff is not part
  of the current batch. Later non-blocking feedback remains deferred. Later
  blocking feedback creates a named pause. Deferred feedback is not a queue and
  must not be consumed by the current session.
- **Snapshot binding:** a new head invalidates earlier architecture and QA pass
  evidence. Rebind, re-inspect, re-project, and re-verify before another action.
- **Pause authority:** a named pause is cleared only through the recorded
  direction and unchanged-head/scope path defined by the controller. A fresh
  Session ID, campaign `OPEN`, adjacency, or a valid new comment is not
  authorization.
- **GitHub writes:** explicit user authority or an end-to-end response request is
  still required. Re-read the remote head immediately before every reaction,
  reply, resolution, review request, commit, or push; do not reuse one read for
  a later mutation.

## Evidence before action

Build a current-head Architecture Context Packet before asking for action
authority. Keep these planes separate:

- **Patch:** violated invariant, validated defect class, affected candidates,
  negative/error/cleanup paths, and whether code or behavior must change.
- **Impact:** reachable callers, consumers, contracts, state, ownership,
  runtime flows, dynamic surfaces, and the defect-frontier trend.
- **Architecture:** original goal and non-goals, approved boundary, baseline,
  mechanism or strategy premises, risk, dependency/contract effects, and an
  independently assessed architecture verdict.
- **Verification:** focused tests, canonical gates, runtime observations,
  independent review, Traceknot when required, evidence freshness, and each
  obligation's `complete`, `incomplete`, or `blocked` status.

Project `patch_required` and `obligations_blocked` as independent booleans.
`patch_required: false` does not prove convergence, QA success, or delivery.
`obligations_blocked: false` means required work is available, not complete.

Defect-frontier identity is:

```text
(invariant_id, mechanism_id, boundary_id, obligation_id)
```

Comments, replies, duplicate clusters, files, line counts, and patch counts are
evidence, not frontier units.

## Feedback admission summary

- **Current:** every actionable item in the initial frozen batch whose own
  immutable `createdAt` is at or before the cutoff, including initial
  non-blocking feedback; same-class blocking feedback created by the cutoff may
  join only when the frozen rules and remaining authority permit it.
- **Deferred:** later non-blocking comments or replies. Record them outside the
  current batch with `admitted_to_current_session: false`.
- **Pause:** a post-cutoff blocking item, new defect class, material scope or
  contract expansion, new strategy decision, unavailable mandatory evidence,
  or required patch after fuse exhaustion.
- **No-code disposition:** duplicate, reply-only, informational, invalid, or
  already-addressed feedback does not consume a patch round, but still requires
  current-head evidence before a GitHub response write.

Classify every credible candidate as `affected`, `safe`, `uncertain`, or
`out-of-scope`, with provenance and differentiating evidence. Report a confirmed
operational out-of-scope defect immediately as evidence-only; it authorizes
neither an edit nor an automatically assigned follow-up.

## Compact execution loop

- **Bind:** identify repository, PR, base/head, worktree, scope, user authority,
  prior campaign history, server-comparable cutoff, fixed deadline, and initial
  thread IDs; initialize the controller state.
- **Read:** fetch thread-aware review state, immutable arrival metadata,
  resolved/outdated state, review submissions, and current checks.
- **Cluster:** map every item to a defect class or explicit no-code disposition;
  keep duplicate thread IDs visible without counting them as new work units.
- **Validate:** determine whether feedback is correct, incorrect, ambiguous,
  duplicate, informational, or already addressed. Use an independent pass for
  security, data, operations, architecture, compatibility, concurrency, or
  regression-sensitive claims.
- **Audit:** inspect the reported path, negative/error/cleanup branches,
  siblings, callers, callees, producers, consumers, tests, configuration,
  migrations, and semantic analogues inside the evidence boundary.
- **Project:** refresh the Architecture Context Packet, per-head impact delta,
  frontier, obligations, architecture verdict, and governor inputs; submit them
  through the controller for the observed head.
- **Guard:** request the intended action. Any nonzero controller exit means stop
  the action and report the exact decision or state defect.
- **Patch:** when authorized, implement the smallest cause-level fix, add
  invariant-focused tests, reread the complete diff, and perform an independent
  post-implementation architecture/impact review.
- **Verify and deliver:** run focused and canonical pre-push checks, push
  normally, require the remote head to equal the recorded commit, then rerun
  required pushed-head verification from a clean snapshot when needed.
- **Respond and reconcile:** guard any automated review request, perform
  per-write head checks, reply or resolve only completed threads, admit feedback
  once at the fixed deadline, reevaluate the governor, and stop rather than
  forming an unbounded response loop.

## Reference routing

Do not load every detailed policy file by default. Read only the material needed
for the current decision.

| Situation | Required material |
| --- | --- |
| Initialize, inspect, project, guard, patch, defer, pause, resume, or request review | [Executable session control](references/executable-session-control.md) |
| Decide patch authority, architecture evidence, frontier trend, coverage, blocked obligations, fuse, or convergence | [Review governor](references/review-governor.md) |
| Reconstruct multiple sessions, finding origin, cumulative churn, strategy reset, or campaign resume | [Review campaign](references/review-campaign.md) |
| Use `rg`, AST, LSP, Graphify, or runtime evidence | [Code navigation and evidence routing](references/code-navigation.md) |
| Need detailed intake, classification, build-versus-buy, GitHub-write, pushed-head, bounded-recheck, risk, Traceknot, completion, or report rules | [Detailed operational policy](operational-policy.md) |

For the detailed operational policy, locate headings first and read only the
relevant section, for example:

```bash
rg '^## |^[0-9]+\.' <skill>/operational-policy.md
```

The detailed file preserves the complete pre-refactor contract so edge cases and
existing integrations remain available without loading them into every session.

## Navigation discipline

Use the smallest capability that answers the question:

- `rg` for literal/configuration discovery;
- AST for syntax-shaped analogues;
- LSP for symbol relationships;
- a fresh bounded code graph for direct or transitive candidates;
- runtime evidence for behavior that static inspection cannot establish.

Record capability, freshness, fallback, coverage gap, provenance, and candidate
disposition. A text hit, inferred graph edge, or unsupported dynamic surface is
a lead, not proof.

## Risk and QA handoff

Classify the highest applicable risk before selecting obligations:

- `R0`: documentation or inert metadata;
- `R1`: localized low-impact implementation;
- `R2`: runtime behavior, persistence, UI, concurrency, security,
  compatibility, or public-contract change;
- `R3`: release, migration, destructive operation, production infrastructure,
  or unknown material scope.

Traceknot is required for `R2`, `R3`, and recurring review loops; it remains
optional for ordinary lower-risk sessions. Its verdict does not own review
convergence, GitHub thread resolution, architecture, or delivery. An unavailable
required handoff is `BLOCKED`; an available but unfinished handoff is
`INCOMPLETE`. Neither is a pass.

## Independent outcomes

Report these independently:

- review convergence;
- deterministic governor decision;
- architecture verdict;
- `patch_required`;
- `obligations_blocked` and per-obligation status;
- QA verdict;
- delivery state.

Overall completion requires a current-head `CONVERGED` decision after complete
obligations and acceptable QA, an acceptable architecture verdict, campaign and
session convergence, pushed-head verification where applicable, the bounded
final recheck, and the authorized delivery state. A clean thread list, green
check, no requested patch, or exhausted fuse is not a substitute for those
conditions.

## Final report

Include the campaign/session identity and lineage, frozen and current heads,
cutoff/deadline, admitted and deferred feedback, named pauses, duplicate
clusters, defect classes, search boundary, candidate ledger, packet and impact
delta, frontier identity/trend, obligations, controller decisions and tokens
consumed, patch rounds/budget, commits, tests, gates, per-write head checks,
GitHub responses, residual gaps, and the independent outcomes above.

When no related defect is found, report the exact surfaces, patterns, and
capabilities checked rather than stating only that none was found.
