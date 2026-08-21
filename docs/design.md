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
| Automatic round and budget | Bound repeated patch cycles; default to two. |
| Scope boundary | Preserve the authorized behavior and repository surface. |
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

The default automatic budget is two rounds. Budget exhaustion pauses only when
another patch is required; duplicates, reply-only responses, and other no-code
dispositions remain permitted. A user may explicitly resolve a named pause
reason and extend the budget. Record the extension and transition `PAUSED ->
OPEN` only while the current head, cutoff, and scope assumptions remain valid;
otherwise start a new session.

Feedback that introduces a new defect class, expands the behavior surface, or
requires a new dependency or public-contract decision also pauses the session.
A paused session cannot be converged until every review pause reason is resolved
or moved to a new session. The QA verdict does not create or resolve a
review-convergence pause; it remains an independent overall-completion outcome.

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
frozen thread; record it as a named pause and assign it to a new session or
explicit follow-up. Later non-blocking comments and replies are queued. A new
defect class or material strategy decision pauses for user direction.
If admitted feedback causes a new patch, run closed-set reconciliation for that
admitted set and the new head without admitting feedback created after the
original cutoff. Any new patch makes earlier evidence informative but
insufficient for the new snapshot.

## Review-campaign model

A Review Campaign preserves the full review/fix lineage for one pull request
across sessions. Opening a new session never resets prior patch-producing heads,
finding origins, cumulative remediation churn, or an unresolved strategy pause.

The campaign state is `OPEN` while sessions may proceed, `CONVERGED` when the
original PR goal and safe boundary are complete with no unresolved campaign
pause reason, `PAUSED` only for a named campaign-level strategy pause,
`BLOCKED` when an external prerequisite prevents that decision, and `STOPPED`
when the campaign is intentionally ended without convergence. An ordinary
session pause does not mutate the campaign state.

Classify fresh findings as `ORIGINAL_DEFECT`, `SAME_INVARIANT`,
`REMEDIATION_REGRESSION`, `MECHANISM_DEFECT`, or `INDEPENDENT`. Pause with
`NON_CONVERGING_REMEDIATION_STRATEGY` when three fresh mechanism findings span
at least two patch-producing sessions, when two consecutive patch-producing
sessions are dominated by mechanism findings or remediation regressions, or
when a material strategy premise is disproved. Three findings first observed
in one patch-producing session are one incomplete patch, not repeated
abstraction failure, unless a separate premise-invalidation condition applies.

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
  boundary; propose a follow-up and do not silently expand the change.

An unclassified high-risk candidate blocks completion. A low-confidence search
hit does not become a defect merely because it resembles the reported code.

## Scope control

Allow expansion when all of the following hold:

- the same root cause or invariant applies;
- the candidate is in the authorized repository and behavior surface;
- the change can be validated with proportionate tests and gates;
- the expansion does not introduce a conflicting product or architecture
  decision.

Pause or create a follow-up when the candidate crosses repositories, changes a
public contract, requires a new production dependency, migration, or production
authority, conflicts with another requirement, introduces a product or
architecture decision, or makes the PR substantially harder to review safely.

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

Evaluate three independent outcomes:

- Review convergence is `CONVERGED` only when every thread in the frozen batch
  and every admitted same-class thread has a disposition, every credible
  in-scope candidate is classified, every `affected` candidate is fixed or
  explicitly blocked, later non-blocking feedback is queued or assigned to a
  new session, post-cutoff same-class blocking feedback is recorded as a named
  pause or follow-up, and no unresolved pause reason remains. Feedback
  requiring user direction keeps the session `PAUSED`; classification alone
  cannot satisfy convergence.
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

Overall completion requires review convergence, an acceptable QA verdict, and
the authorized delivery state. `FAIL`, `BLOCKED`, or `INCOMPLETE` QA never
becomes success because threads were resolved. The bounded final recheck is
review-convergence evidence; it does not replace QA evaluation or restart the
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
5. A real same-class issue outside the safe PR boundary is reported as a
   follow-up instead of being silently fixed or ignored.
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
