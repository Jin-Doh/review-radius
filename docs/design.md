# Review Radius Design

## Problem

The previous workflow was reliable at closing GitHub review threads but made
the thread itself the unit of work. That encouraged a direct mapping from one
comment to one edit. A reviewer often points at one visible symptom, while the
same violated assumption may exist in sibling implementations, callers,
failure paths, configuration variants, or tests.

The workflow must use the reviewer's observation as a lens for inspecting a
bounded defect class without turning review response into an unrelated
repository-wide refactor.

## Design principles

1. Treat a comment as evidence, not as an exhaustive statement of scope.
2. Derive a violated invariant before choosing the final fix boundary.
3. Search for both textual duplicates and semantic analogues.
4. Classify every credible candidate with evidence before editing.
5. Bound expansion by the validated invariant, affected behavior, PR, and
   repository constraints.
6. Encode the invariant in tests instead of protecting only the reported line.
7. Keep GitHub thread closure and CI proof as necessary, but not sufficient,
   completion evidence.
8. Freeze each review session to a PR head and initial thread cursor so newly
   arriving feedback cannot silently extend the active batch.
9. Bound automatic patch cycles independently from the required pre- and
   post-implementation review passes.
10. Keep review convergence, QA verdict, and delivery state independent.

## Three-plane model

Review Radius separates three authorities that must not be collapsed into a
single notion of "scope":

1. **Inspection plane:** inspect the credible defect surface, including
   architecture components, dependencies, contracts, persistence, ownership,
   runtime flows, and dynamic gaps. Inspection may cross the eventual edit
   boundary when that is necessary to understand impact.
2. **Edit plane:** change only the approved repository, behavior, contract,
   dependency, and architecture boundary. Evidence discovered during broad
   inspection does not itself grant edit authority.
3. **Decision plane:** evaluate the defect frontier, verification obligations,
   risk, and architecture verdict with the evidence governor. This plane may
   continue locally, require an impact review, reset the strategy, or block
   without authorizing another edit.

This separation makes inspection-vs-edit authority explicit: a broad search is
required for trustworthy impact analysis, while an edit remains bounded by the
approved context packet and user-authorized decisions.

## Architecture Context Packet

Every patch-producing session, and every session that asks the governor to assess
a disposition, binds its reasoning to an Architecture Context Packet (ACP). The
packet is an evidence record and snapshot binding, not a license to expand the
change. It records:

- base and head SHA;
- original goal and non-goals;
- approved behavior, repository, contract, dependency, and architecture
  boundary;
- architecture baseline: components, dependencies, public contracts,
  persistence, ownership, runtime flows, and dynamic gaps;
- mechanism or strategy premises;
- impact delta;
- defect frontier;
- whether a code or behavior change is required (`patch_required`: a required
  independent boolean, `true` or `false`);
- verification obligations and their availability;
- whether any mandatory verification obligation is blocked
  (`obligations_blocked`: a required independent boolean, `true` or `false`).

`obligations_blocked` is projected independently from the verification and
authority planes. `true` means a mandatory obligation is unavailable,
disallowed, or cannot be completed with the evidence or authority available
for the current head; `false` means the work is available to perform even
when `obligations_complete` is still `false`. The evaluator validates both
independent obligation signals and MUST NOT infer `obligations_blocked` from
incompleteness. A blocked obligation returns
`INSUFFICIENT_ARCHITECTURE_EVIDENCE` after stronger strategy-reset signals and
before impact review, fuse exhaustion, or local continuation. An incomplete but
available obligation (`obligations_blocked: false`) may remain while a
`shrinking` frontier continues bounded patch work.

The ACP is refreshed when a new head, material premise, or approved boundary
changes. A missing or stale architecture baseline is an evidence gap, not
permission to infer safety from a green test or an empty comment list.

The defect frontier is the set of unresolved obligations that can still change
the decision. Its identity is
`(invariant_id, mechanism_id, boundary_id, obligation_id)`, so comments and
duplicate comments are not count units. Record its trend as `empty`,
`shrinking`, `stable`, `expanding`, or `regressing`.

The architecture verdict is independent of review convergence, QA, and
delivery. It is a required, independently assessed input named
`architecture_verdict`, with one of `NOT_ASSESSED`, `LOCAL_SAFE`,
`APPROVED_EXPANSION`, `STRATEGY_REVIEW_REQUIRED`, or `BLOCKED`; only an
acceptable verdict can support convergence. Do not infer this verdict from the
frontier, QA, or a no-code disposition.

The normative human/agent governor policy is
[`skills/review-radius/references/review-governor.md`](../skills/review-radius/references/review-governor.md).

The `patch_required` input is a required independent boolean (`true` or
`false`) from the patch plane. No architecture verdict determines it. It is
true only when an unresolved frontier identity or failed obligation requires a
code or behavior change; duplicate classification, reply-only responses,
explanations, and other no-code dispositions set it to false. The value
`patch_required: false` alone does not prove review convergence, QA success, or
delivery completion; those outcomes require their own evidence.

## Core model

```text
review comment
  -> observed symptom
  -> root-cause hypothesis
  -> violated invariant
  -> bounded search surface
  -> candidate inventory
  -> disposition
  -> fix and invariant-level regression proof
```

The defect class, rather than the individual thread, is the planning and
implementation unit. Multiple threads may map to one defect class, and one
thread may reveal multiple candidates.

## Review-session model

A review session is the bounded execution unit around one or more defect
classes. Record:

<!-- markdownlint-disable MD013 -->

| Field | Purpose |
| --- | --- |
| Session ID | Distinguish retries and later feedback batches. |
| Repository, PR, initial head, and current head | Bind source inspection and evidence to one snapshot at a time. |
| Initial thread cursor and IDs | Freeze the feedback batch observed at session start. |
| Server-comparable cutoff and comment high-water marks | Classify arrivals deterministically by immutable `createdAt` metadata. |
| Queued thread IDs | Preserve later feedback without silently expanding the batch. |
| Defect classes | Cluster duplicate or related threads by root cause. |
| Automatic patch round and safety fuse | Bound repeated patch cycles; default to two rounds as an automatic safety fuse, never as convergence evidence. |
| Scope boundary | Preserve the authorized behavior and repository surface. |
| Architecture Context Packet | Bind the snapshot, architecture baseline, premises, impact delta, frontier, obligations, and `obligations_blocked`. |
| Patch required | Required independent boolean (`true` or `false`) from the patch plane; no architecture verdict determines it. Only `true` can reach fuse or local-continuation authority. |
| Obligations blocked | Required independent boolean (`true` or `false`) from verification and authority planes; distinct from incomplete obligations. |
| Evidence governor decision | Record `CONTINUE_LOCAL`, `IMPACT_REVIEW_REQUIRED`, `STRATEGY_RESET_REQUIRED`, `INSUFFICIENT_ARCHITECTURE_EVIDENCE`, `AUTOMATION_FUSE_EXHAUSTED`, or `CONVERGED`. |
| Architecture verdict | Record `NOT_ASSESSED`, `LOCAL_SAFE`, `APPROVED_EXPANSION`, `STRATEGY_REVIEW_REQUIRED`, or `BLOCKED` independently of QA and delivery. |
| Strategy decisions and premises | Reuse approved choices only while every material comparison premise remains valid. |
| Review convergence | `OPEN`, `CONVERGED`, `PAUSED`, or `BLOCKED`. |
| QA verdict | `NOT_RUN`, `PASS`, `PASS_WITH_ACCEPTED_RISK`, `FAIL`, `BLOCKED`, or `INCOMPLETE`. |
| Delivery state | `NOT_STARTED`, `READY`, `REPLIED`, `RESOLVED`, or `PUSHED`. |

<!-- markdownlint-enable MD013 -->
The initial cursor and IDs are navigation boundaries, not admission proof.
Include a comment or reply in the initial frozen batch only when its immutable
`createdAt` is at or before the cutoff. A later-timestamped item fetched during
the initial read remains post-cutoff feedback and cannot become `current` merely
because its thread ID was frozen.

One automatic round is `analyze -> plan -> patch -> verify -> respond ->
bounded recheck`. A duplicate classification, reply-only response, or
explanation that changes no code does not consume a round. A new patch,
behavior-contract change, or newly authorized defect class does. The required
two-pass review is not a two-round budget: every patch round still receives
pre-implementation analysis and post-implementation rereview.

The default automatic budget is two patch rounds, but this is a safety fuse
only. It is neither evidence of convergence nor evidence that the remediation
strategy is failing. The evidence governor or an independent architecture and
impact review may stop the session earlier when the frontier is not safely
understood, a strategy premise is invalid, the approved boundary would expand,
a new semantic dimension or higher risk appears, or architecture evidence is
insufficient.

When the fuse is exhausted while `patch_required` is `true` (another patch is
still required), record `AUTOMATION_FUSE_EXHAUSTED` and pause for explicit
direction. Duplicates, reply-only responses, and other no-code dispositions
remain permitted and do not exhaust or invoke the fuse. A user may explicitly
resolve a named pause reason and extend the fuse. Record the extension and
transition `PAUSED -> OPEN` only while the current head, cutoff, and scope
assumptions remain valid. If any of those assumptions changed, remain `PAUSED`
until recorded explicit user direction selects a successor Review Session and
the Review Campaign independently permits it; changed assumptions never
auto-open a session. Campaign `OPEN` or permission, classification, and a
fresh Session ID never authorize the move by themselves.

Feedback that introduces a new defect class, expands the behavior surface, or
requires a new dependency or public-contract decision also pauses the session
for explicit user direction before any new-session or follow-up choice. A
paused session cannot be converged until every review pause reason is resolved
by recorded explicit user direction, or moved to a new session or explicit
follow-up only after recorded explicit user direction selects that disposition
and the Review Campaign independently permits it. The QA verdict does not
create or resolve a review-convergence pause. It remains an independent
overall-completion outcome.

The bounded recheck uses the current head, initial thread cursor, an immutable
server-comparable cutoff, and per-comment `createdAt` or equivalent high-water
metadata. New arrivals do not reset the cutoff or fixed observation deadline.
Initialization sets the fixed observation deadline at least one minute and
thirty seconds in the future, or uses a longer repository-defined interval. The
deadline is non-resetting and cannot be satisfied by an immediate same-time
check.
Refetch known thread IDs as well as cursor pages so replies on existing threads
are classified against the same cutoff. Treat each newly observed comment or
reply as its own arrival; a frozen parent thread does not make a late reply
current. Revalidate the remote PR head before each patch and verification cycle
and immediately before delivery writes.

All actionable threads in the initial frozen batch are `current`, including
initial non-blocking feedback. Same-class blocking comments or replies created
by the cutoff may join only while a patch budget remains. A same-class blocking
comment or reply created after the cutoff cannot join this session, even on a
frozen thread; record it as a named pause and pause for explicit user direction.
Only after recorded explicit user direction selects that disposition may it be
assigned to a new session or an explicit follow-up, and only after the Review
Campaign independently permits that disposition. Later non-blocking comments
and replies remain queued by default and may be assigned to a new session or
follow-up only after recorded explicit user direction selects that disposition
and the Review Campaign independently permits it.
Campaign `OPEN` or permission, and classification alone, never
authorizes a new-session or follow-up assignment. A new defect class or
material strategy decision also pauses for user direction. Neither handoff is
automatic.
If admitted feedback causes a new patch, run closed-set reconciliation for that
admitted set and the new head without admitting feedback created after the
original cutoff. Any new patch makes earlier evidence informative but
insufficient for the new snapshot.

## Review-campaign model

A Review Campaign preserves the full review/fix lineage for one pull request
across sessions. Opening a new session never resets prior patch-producing heads,
finding origins, cumulative remediation churn, or an unresolved strategy pause.

The campaign state is `OPEN` while sessions may proceed. It is `CONVERGED`
only when the original PR goal and safe boundary are complete, the evidence
governor is `CONVERGED`, the independent architecture verdict is acceptable,
and no unresolved campaign pause reason remains. It is `PAUSED` only for a named
campaign-level strategy pause, `BLOCKED` when an external prerequisite prevents
that decision, and `STOPPED` when the campaign is intentionally ended without
convergence. An ordinary session pause does not mutate the campaign state.

Classify fresh findings as `ORIGINAL_DEFECT`, `SAME_INVARIANT`,
`REMEDIATION_REGRESSION`, `MECHANISM_DEFECT`, or `INDEPENDENT`. These origins
explain frontier movement and strategy risk; they are not count units.

The evidence governor is the primary authority for patch decisions and review
convergence. Apply it before each patch-producing session, after
post-implementation rereview, after current-head verification, and again at
the bounded recheck. When multiple outcomes apply, use this precedence without
skipping an earlier applicable result:

1. known strategy-reset signals or `architecture_verdict` equal to
   `STRATEGY_REVIEW_REQUIRED` -> `STRATEGY_RESET_REQUIRED`;
2. `obligations_blocked` equal to `true`, or other insufficient architecture
   evidence -> `INSUFFICIENT_ARCHITECTURE_EVIDENCE`;
3. impact review (only with `obligations_blocked: false`) ->
   `IMPACT_REVIEW_REQUIRED`;
4. convergence -> `CONVERGED`;
5. the automation fuse (only with `obligations_blocked: false`) ->
   `AUTOMATION_FUSE_EXHAUSTED`; and
6. continuation (only with `obligations_blocked: false`) ->
   `CONTINUE_LOCAL`.

- `CONTINUE_LOCAL` is permitted only when `patch_required` is `true`, the
  frontier is non-empty and shrinking or otherwise locally actionable, the
  current Architecture Context Packet and approved strategy premises remain
  valid, the architecture verdict is acceptable, and
  `obligations_blocked` is `false`; the automation fuse must remain available.
  `obligations_complete` may still be `false` when the available work is
  shrinking and locally actionable. An empty frontier or a no-code packet never
  authorizes `CONTINUE_LOCAL` or a local patch.
- `IMPACT_REVIEW_REQUIRED` applies only when the frontier is `stable`,
  `expanding`, or `regressing`, `obligations_blocked` is `false`, and no
  stronger strategy or evidence signal applies. An empty frontier never maps
  to impact review.
- `STRATEGY_RESET_REQUIRED` applies when a material premise is invalid, an
  architecture boundary would expand without approval, a new semantic
  dimension is needed, the risk is higher than the approved strategy, or the
  independently supplied architecture verdict is `STRATEGY_REVIEW_REQUIRED`.
- `INSUFFICIENT_ARCHITECTURE_EVIDENCE` applies when
  `obligations_blocked` is `true`, the independently supplied architecture
  verdict is `NOT_ASSESSED` or `BLOCKED`, the architecture baseline or
  coverage has an unknown or high-risk gap, when an empty frontier has
  incomplete verification obligations or unacceptable QA, or when no decision
  row matches (including an unmatched or no-code evidence packet). A blocked
  obligation is distinct from an incomplete but available obligation:
  `obligations_blocked: false` may continue shrinking patch work, but
  `obligations_blocked: true` is insufficient evidence before impact, fuse, or
  local authority. These cases require evidence or authority; they never become
  impact review by default.
- `AUTOMATION_FUSE_EXHAUSTED` applies only when `patch_required` is `true`,
  `obligations_blocked` is `false`, the default two-round safety fuse is spent,
  and another patch needs authorization. This is distinct from
  `NON_CONVERGING_REMEDIATION_STRATEGY`; fuse exhaustion alone is not strategy
  failure and never applies to no-code work.
- `CONVERGED` is permitted only when `patch_required` is `false`,
  `obligations_blocked` is `false`, the frontier is `empty`, all verification
  obligations are complete, QA is acceptable, and the independent architecture
  verdict is acceptable. Review and delivery remain independent outcomes and
  must also satisfy the completion contract.

An explicitly authorized `APPROVED_EXPANSION` widens the inspection and edit
boundary but does not itself grant patch authority; automatic patching still
requires `CONTINUE_LOCAL`.

The architecture verdict is assessed independently as `NOT_ASSESSED`,
`LOCAL_SAFE`, `APPROVED_EXPANSION`, `STRATEGY_REVIEW_REQUIRED`, or `BLOCKED`.
`LOCAL_SAFE` and an explicitly authorized `APPROVED_EXPANSION` can support
convergence; `NOT_ASSESSED`, `STRATEGY_REVIEW_REQUIRED`, and `BLOCKED` cannot.
An unmatched packet, including a no-code packet that does not satisfy a
precedence row, returns `INSUFFICIENT_ARCHITECTURE_EVIDENCE` rather than
`IMPACT_REVIEW_REQUIRED`; it never grants patch or delivery authority.
One severe premise invalidation may require a strategy reset immediately;
comment, duplicate, or patch counts cannot postpone that decision. Use the
normative [review governor policy](../skills/review-radius/references/review-governor.md)
for the complete human/agent procedure.

## Review-lens record

Create one record for each actionable feedback cluster:

| Field | Purpose |
| --- | --- |
| Symptom | Preserve what the reviewer directly observed. |
| Validity | Record why the feedback is correct, incorrect, or ambiguous. |
| Root cause | State the causal mechanism, not only the bad line. |
| Invariant | State the behavior or safety property that must always hold. |
| Search anchors | List symbols, helpers, call edges, and code patterns. |
| Search boundary | Define the smallest surface that may share the invariant. |
| Risk | Record security, data, operations, compatibility, or regression risk. |

Purely editorial feedback may use a lightweight record, but still requires a
quick check for repeated spelling, naming, documentation, or generated-source
occurrences. Skip broader analysis only with an explicit reason.

## Concentric search strategy

Search outward until the bounded surface is exhausted:

1. Inspect the exact function and all of its branches and cleanup paths.
2. Inspect sibling implementations of the same interface or abstraction.
3. Inspect callers, callees, producers, and consumers of the same contract.
4. Search for exact textual and structural copies.
5. Inspect semantic analogues that protect the same invariant with different
   syntax.
6. Inspect tests, configuration variants, migrations, and documentation when
   they encode or expose the same behavior.

Prefer repository search and language-aware navigation. Do not claim that no
similar issue exists from a single text search.

## Candidate disposition

Classify each credible candidate as:

- `affected`: the same invariant is violated and the candidate belongs in the
  current fix boundary.
- `safe`: the candidate is protected; record the differentiating evidence.
- `uncertain`: evidence is insufficient; investigate further or keep the item
  open.
- `out-of-scope`: the issue is real but materially exceeds the authorized PR
  boundary; record it as a named pause awaiting explicit user direction. Only
  after recorded explicit user direction selects that follow-up disposition may
  it be assigned, and only after the Review Campaign independently permits that
  disposition; do not silently expand the change.

### Operational out-of-scope handling

When a real out-of-scope defect is confirmed, immediately record it and report
the evidence while the session remains `PAUSED`; set `obligations_blocked: true`
for the unavailable or unauthorized follow-up obligation, and do not defer
either action to the final report. Acceptance examples alone never set this
blocked signal. That report is evidence-only and does not authorize an edit
or a follow-up assignment. A follow-up assignment requires recorded explicit
user direction selecting the candidate, and only after the Review Campaign
independently permits that disposition; reporting, classification, or campaign
`OPEN` status alone never authorizes it.

`obligations_blocked` remains `true` and the session remains `PAUSED` until
recorded explicit user direction selects the candidate and the Review Campaign
independently permits the disposition; reporting alone does not clear the
blocked signal.

An unclassified high-risk candidate blocks completion. A low-confidence search
hit does not become a defect merely because it resembles the reported code.

## Scope control

Inspection may cross the eventual edit boundary to establish architecture and
impact evidence, but inspection authority is not edit authority. A candidate
outside the approved boundary is recorded as `out-of-scope`, an architecture
gap, or a decision requiring approval; it is not changed merely because it was
found. The evidence governor can stop before the two-round safety fuse when
impact or architecture review is required.

Allow expansion when all of the following hold:

- the same root cause or invariant applies;
- the candidate is in the authorized repository and behavior surface;
- the change can be validated with proportionate tests and gates;
- the expansion does not introduce a conflicting product or architecture
  decision.

Pause for explicit user direction when the candidate crosses repositories,
changes a public contract, requires a new production dependency, migration, or
production authority, conflicts with another requirement, introduces a product
or architecture decision, or makes the PR substantially harder to review
safely. After that direction, a follow-up option may be presented when
appropriate; presenting the option is not an assignment or automatic
disposition.

This replaces line-level minimalism with cause-level minimalism.

## Implementation-strategy decisions

Do not turn every review into a build-versus-buy exercise. Open a strategy gate
only when the fix needs a new production dependency, a nontrivial subsystem, a
public-contract change, or implementation of a protocol, parser, cryptographic
primitive, or concurrency mechanism.

Present direct implementation, reuse of an existing project dependency, a new
open-source dependency, and a follow-up PR when they are credible options.
Compare requirement fit, implementation size, maintenance ownership, security,
license compatibility, transitive dependencies, performance, integration cost,
and replacement cost. Recommend one option with evidence, but require explicit
user approval before adding a production dependency or materially expanding the
authorized architecture. Preserve the decision and every material comparison
premise in the session. Reuse it only while those premises remain valid; reopen
the decision when requirements, implementation size, maintenance, security,
license, dependency, performance, integration, or replacement assumptions
materially change.

## Two-pass review

Run two distinct reviews:

1. Before implementation, use the review lens to find the existing blast
   radius.
2. After implementation, reread the resulting diff through the same lens to
   detect incomplete fixes, new asymmetry, missed failure paths, and tests that
   assert only the example rather than the invariant.

Passing the repository's existing test suite does not replace either pass.

## Pushed-head verification

Verification before commit and push is candidate evidence because the remote
pull request still points at the previous head. Record the exact local commit
SHA that will be pushed. After push, read the remote head and require equality
with that recorded SHA before binding evidence or rerunning verification. If
the OIDs differ, invalidate delivery and QA readiness, do not bind local
evidence to another contributor's head, and fetch/rebind that head before
rerunning the complete verification.

Only after the equality check passes, bind the session to the pushed SHA and
rerun the required focused verification and canonical gate against that SHA. If
the source worktree has any uncommitted edits—including related, generated, or
hook-created changes—run this post-push verification from a clean detached or
temporary worktree at the recorded SHA. Preserve the source worktree because
dirty-worktree evidence is not snapshot-bound. Pre-push evidence remains
informative but cannot satisfy the pushed-head QA obligation alone.

Reactions are dispositions during intake, not GitHub mutations. For a session
that produces a patch, add them only after pushed-head verification succeeds
and their own immediate remote-head reread. No-code dispositions use a fresh
current-head verification path for reactions, explanation replies, and
resolutions. Re-read the remote head immediately before every reaction, reply,
or resolution write; do not reuse one reread as the guard for a later mutation.
A mismatch invalidates response readiness; rebind and reverify before that
write. Patch replies cite the post-push gate; explanation-only replies cite the
current-head no-code verification.
Delivery completion and QA completion therefore both refer to the pushed head,
not merely to the local commit before push.

## Risk levels

Classify the highest applicable level before selecting the QA handoff:

- `R0`: documentation or inert metadata only.
- `R1`: localized low-impact implementation.
- `R2`: runtime behavior, persistence, UI, concurrency, security,
  compatibility, or public-contract changes.
- `R3`: release, migration, destructive operation, production infrastructure,
  or unknown material scope.

Choose the highest matching level; `R3` supersedes `R2`, and unknown scope
resolves upward. Traceknot is mandatory for `R2` and `R3`; `R0`/`R1` sessions
use canonical focused obligations unless a recurring review loop independently
requires the handoff. Use the Traceknot risk-classification procedure as the
authoritative rubric when a category is ambiguous.

## Completion contract

Evaluate four independent outcomes:

- Review convergence is `CONVERGED` only when every thread in the frozen batch
  and every admitted same-class thread has a disposition, every credible
  in-scope candidate is classified, every `affected` candidate is fixed or
  explicitly blocked, later non-blocking feedback remains queued by default
  and may be assigned to a new session or follow-up only after recorded
  explicit user direction selects that disposition and the Review Campaign
  independently permits it; post-cutoff same-class blocking feedback is
  recorded as a named pause awaiting explicit user direction. Only after
  recorded explicit user direction selects the new-session or follow-up
  disposition may it be assigned, and only after the Review Campaign
  independently permits that disposition; no unresolved pause reason remains.
  Feedback requiring user direction keeps the session `PAUSED`; classification
  alone cannot satisfy convergence. Duplicates and reply-only threads are
  dispositioned without consuming a round.
- Architecture outcome is acceptable only when the current head has an
  independent architecture post-review, its obligations and impact delta are
  complete, and the architecture verdict is `LOCAL_SAFE` or explicitly
  authorized `APPROVED_EXPANSION`.
  `NOT_ASSESSED`, `STRATEGY_REVIEW_REQUIRED`, and `BLOCKED` verdicts, or
  missing architecture evidence, cannot complete.
- The QA verdict is acceptable only when mandatory verification obligations for
  the current head pass, or the user explicitly accepts every remaining
  material risk. An earlier-head result, lifecycle event, or green gate alone
  cannot establish this outcome.
  Traceknot is the required QA handoff for `R2`/`R3` changes and recurring
  review loops; it remains optional for ordinary lower-risk sessions.
  For a selected or required Traceknot handoff, an unavailable required
  capability is `BLOCKED`; available capability with unfinished mandatory
  execution or evidence is `INCOMPLETE`. Traceknot absence alone does not block
  a session for which the handoff is neither selected nor required.
- Delivery is complete only when replies, reactions, resolution, commits, and
  pushes match the authorized implementation state.

Overall completion requires all four independent outcomes: review convergence,
an acceptable architecture outcome and verdict, an acceptable QA verdict, and
the authorized delivery state, plus an evidence governor decision of
`CONVERGED`. `FAIL`, `BLOCKED`, or `INCOMPLETE` QA never becomes success because
threads were resolved. The bounded final recheck is review-convergence
evidence; it does not replace architecture or QA evaluation or restart the
session indefinitely.

## Non-goals

- Do not turn one review comment into a general cleanup campaign.
- Do not modify candidates based only on textual similarity.
- Do not use CI success as evidence that the search surface was complete.
- Do not hide a discovered adjacent defect because the reviewer did not name it.
- Do not resolve an ambiguous or blocked thread to make the PR appear clean.

## Acceptance scenarios

The skill is acceptable when it produces the following behavior:

1. A resource-cleanup comment causes inspection of all exits and sibling users,
   with double-close safety and failure-path tests considered.
2. An authorization comment causes inspection of equivalent routes and shared
   middleware, while unrelated authorization refactors remain out of scope.
3. A strict-identity comparison comment causes inspection of normalization,
   persistence, and comparison sites that share the identity invariant.
4. A typo comment receives a lightweight repeated-occurrence scan rather than a
   full architectural analysis.
5. A real same-class issue outside the safe PR boundary is immediately recorded
   and reported as evidence-only; immediate reporting does not authorize either
   editing or follow-up assignment, and the session remains paused for explicit
   user direction. Assignment to an explicit follow-up requires recorded
   explicit user direction selecting that disposition and independent Review
   Campaign permission. It is never silently fixed or ignored.
6. One hundred duplicate comments for the same root cause form one defect class
   and do not consume one automatic round per thread.
7. A third patch cycle after two automatic rounds pauses for user direction
   instead of continuing because the new request is adjacent to prior code.
8. Feedback arriving near the bounded recheck deadline is classified without
   resetting the observation window indefinitely.
9. A new PR head invalidates earlier evidence for pass purposes and triggers
   verification against the new snapshot.
10. A new dependency or architecture choice produces build-versus-buy options
    and does not modify production dependencies before user approval.
11. Review convergence, QA verdict, and delivery state remain separate when one
    succeeds and another is blocked or incomplete.
12. After two patch rounds, one, two, or one hundred no-code duplicate replies
    are dispositioned without a third round or a budget-exhaustion pause.
13. Explicit direction resolves a named pause reason and resumes `PAUSED ->
    OPEN` only when the frozen head, cutoff, and scope remain valid.
14. A remote head change before verification or delivery invalidates readiness
    and requires evidence bound to the new head before any delivery write.
15. Feedback created before the immutable cutoff but fetched after it receives
    the same classification on every run.
16. Feedback admitted at the cutoff may cause a patch and closed-set
    reconciliation, but cannot reopen admission for later feedback.
17. A memoized strategy is reused unchanged and reopened when any material
    comparison premise changes.
18. Missing Traceknot capability blocks QA only when that handoff is selected
    or required for the session's risk profile.
19. A newly disproved strategy premise stops the session immediately with
    `STRATEGY_RESET_REQUIRED`, before the two-round safety fuse is exhausted;
    it is not deferred until another local patch fails.
20. A dynamic dispatch or ownership gap that prevents a trustworthy impact
    boundary produces `INSUFFICIENT_ARCHITECTURE_EVIDENCE` (and an
    appropriate `BLOCKED` architecture verdict) rather than an inferred
    `LOCAL_SAFE` verdict or an unauthorized edit.
21. Two local patch rounds that leave a bounded frontier while
    `patch_required` is `true` require `AUTOMATION_FUSE_EXHAUSTED`; that result
    is distinct from `NON_CONVERGING_REMEDIATION_STRATEGY`, which requires
    strategy-level evidence such as premise invalidation.
22. A session converges only after the frontier is `empty`, `patch_required` is
    `false`, verification obligations are complete, QA is acceptable, and the
    independent architecture verdict is `LOCAL_SAFE` or approved
    `APPROVED_EXPANSION`.
23. Broad inspection discovers a real sibling defect outside the approved edit
    boundary; the sibling is recorded and reported, but inspection alone does
    not authorize changing it.
24. An empty frontier with incomplete verification obligations, unacceptable
    QA, or an unmatched/no-code evidence packet returns
    `INSUFFICIENT_ARCHITECTURE_EVIDENCE`, never `IMPACT_REVIEW_REQUIRED`; fuse
    exhaustion and `CONTINUE_LOCAL` are unavailable when `patch_required` is
    `false`.

## Tool-routing experiment

The initial synthetic TypeScript benchmark is maintained under
`experiments/tool-routing/`. It models a review against a loose,
case-insensitive identity comparison with direct calls, an aliased import, a
re-export, a transitive wrapper caller, a structurally equivalent helper, and
safe decoys.

The 2026-08-04 run produced these stable candidate results across three
repetitions:

| Method | Recall | Precision | Token proxy |
| --- | ---: | ---: | ---: |
| `rg+raw` | 75.0% | 75.0% | 1694 |
| `rg+ast` | 87.5% | 87.5% | 1988 |
| `rg+ast+lsp` | 100.0% | 100.0% | 2191 |
| `graphify-query` | 87.5% | 100.0% | 589 |
| `graphify+ast+lsp` raw accumulation | 100.0% | 100.0% | 2480 |
| compact routed evidence | 100.0% | 100.0% | 451 |

Graphify found the transitive wrapper path with a small result but missed the
aliased call. LSP supplied that missing semantic edge. AST found the
structurally equivalent helper. Accumulating all raw outputs cost more than text
search, while exposing only a compact roots/candidates/delta ledger reduced the
token proxy by about 73% with full recall and precision. The benchmark removes
ripgrep's nondeterministic timing and self-sized fields before scoring; exact
byte-based proxy values remain specific to this fixture and adapter format.

Treat this as evidence for the routing mechanism, not as a repository-scale
performance claim. Before making Graphify or LSP a default dependency, repeat
the experiment against a larger real repository and include stale-index,
unsupported-language, dynamic-dispatch, and setup-cost cases.

The provisional routing contract is:

1. Use AST to identify structural defect roots.
2. Query an existing or justified Graphify graph for bounded direct and
   transitive candidates.
3. Use LSP to verify semantic relationships and add only candidates absent from
   the graph result.
4. Expose a compact provenance ledger to the model instead of raw tool output.
5. Fall back to text search and source inspection whenever a capability is
   missing or stale.

The durable experiment record, limitations, and reproduction contract are in
[`docs/experiments/2026-08-04-code-navigation-tool-routing.md`](experiments/2026-08-04-code-navigation-tool-routing.md).
The installable operational contract is intentionally separated into
[`skills/review-radius/references/code-navigation.md`](../skills/review-radius/references/code-navigation.md)
so the core skill remains compact while agents can load the routing details at
the point of use.
