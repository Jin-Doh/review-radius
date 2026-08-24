---
name: review-radius
description: Handle repeated GitHub PR review/fix cycles, GitHub PR review churn, and non-converging GitHub PR feedback end to end when asked to inspect or address review comments, requested changes, unresolved threads, or follow-up reviews; validate each comment, derive the underlying invariant, audit related code for the same defect class, implement bounded fixes, and report independent review, QA, and delivery states.
---

# Review Radius

Fix the pattern behind the comment. Handle GitHub PR feedback end to end by
treating each comment as evidence of a potential defect class, not as an
exhaustive boundary. Keep the review radius bounded by the validated root cause
and authorized PR scope, even when feedback repeats or the PR does not
converge.

This routing description helps a host select the Skill for GitHub PR feedback;
the Skill cannot monitor, dispatch, call, or invoke itself when it was not
selected.
The architecture-aware policy is normative in
[Review governor](references/review-governor.md). Read it before deriving a
lens or making a governor decision.

## Review Session

A `Review Session` is the bounded execution unit for one feedback batch and its
validated defect classes. Initialize it before inspecting or changing code. Do
not treat an unbounded response loop as a session.

Record at least:

<!-- markdownlint-disable MD013 -->

| Field | Purpose |
| --- | --- |
| Session ID | Distinguish this bounded batch from retries and later feedback. |
| Repository, PR, initial head, and current head | Bind source inspection and each round's evidence to one snapshot. |
| Initial thread cursor and thread IDs | Freeze the feedback batch observed at session start. |
| Server-comparable cutoff and comment high-water marks | Classify arrivals by immutable `createdAt` metadata. |
| Queued thread IDs | Preserve later feedback without silently expanding the batch. |
| Duplicate clustering and defect classes | Make the root cause, rather than an individual thread, the work unit. |
| Architecture Context Packet | Bind the base/head SHA, original goal/non-goals, approved boundary, architecture baseline (components, dependencies, public contracts, persistence, ownership, runtime flows, dynamic gaps), mechanism/strategy premises, per-head impact delta, defect frontier, verification obligations, the required independent patch-plane `patch_required` boolean (`true` or `false`), and the required independent verification-plane `obligations_blocked` boolean (`true` or `false`). |
| Architecture verdict | Record `NOT_ASSESSED`, `LOCAL_SAFE`, `APPROVED_EXPANSION`, `STRATEGY_REVIEW_REQUIRED`, or `BLOCKED` separately from review convergence and QA. |
| Patch required | Record `patch_required: true` or `false` as an independent patch-plane fact; no architecture verdict determines it, and `false` alone does not prove convergence, QA success, or delivery completion. |
| Verification-obligation status | Record `obligations_blocked: true` or `false` independently of patch, architecture, QA, and delivery outcomes; preserve each obligation's `complete`, `incomplete`, or `blocked` status. |
| Governor decision and evidence | Record the architecture-aware governor decision identifier and the packet/frontier evidence that produced it; comments and duplicates are not decision units. |
| Operational governor summary | Summarize the current governor decision, architecture verdict, and the independent `patch_required` and `obligations_blocked` booleans without collapsing them into a single outcome. |
| Automatic patch round and fuse state | The default is exactly two automatic patch rounds as a circuit breaker/fuse; `AUTOMATION_FUSE_EXHAUSTED` is not convergence evidence. |
| Fixed recheck deadline | Bound the final recheck; new arrivals never reset it. |
| Scope boundary and authorization | Preserve the approved behavior and repository surface. |
| Strategy-decision memo and premises | Reuse an approved choice only while every material comparison premise remains valid. |
| Review convergence | `OPEN`, `CONVERGED`, `PAUSED`, or `BLOCKED`. |
| QA verdict | `NOT_RUN`, `PASS`, `PASS_WITH_ACCEPTED_RISK`, `FAIL`, `BLOCKED`, or `INCOMPLETE`. |
| Delivery state | `NOT_STARTED`, `READY`, `REPLIED`, `RESOLVED`, or `PUSHED`. |

<!-- markdownlint-enable MD013 -->

Every Session Architecture Context Packet and operational governor summary MUST
include `patch_required` as a required independent boolean (`true` or `false`).
It is a patch-plane fact independent of the architecture plane: no architecture
verdict determines it. `patch_required: false` alone MUST NOT be treated as
proof of review convergence, successful or acceptable QA, or delivery
completion.
Every packet and operational governor summary MUST also include
`obligations_blocked` as a required independent verification-plane boolean
(`true` or `false`). `obligations_blocked: true` means that at least one
required obligation is blocked by an unavailable or inaccessible capability,
prerequisite, or evidence artifact. The governor MUST map that state to
`INSUFFICIENT_ARCHITECTURE_EVIDENCE` after any stronger strategy signal and
before impact review, fuse exhaustion, or local continuation; it MUST NOT map a
blocked obligation to `CONTINUE_LOCAL` or `AUTOMATION_FUSE_EXHAUSTED`.
`obligations_blocked: false` means the required obligations are available to
execute or inspect, not that they are complete. An available obligation whose
execution or evidence is unfinished remains independently `incomplete`; it is
not `blocked`, cannot establish convergence, and may remain eligible for local
patch work only when the governor's other conditions permit it.

All observations, candidate dispositions, tests, gates, replies, and decisions
must identify the session and the head/snapshot from which they were obtained.
This makes the evidence snapshot-bound. A later head makes earlier pass evidence
informative but insufficient: rerun the required evidence against the new head
before calling that head verified.

Each Session record carries the Architecture Context Packet and architecture
verdict above. Each Review Campaign record carries the Architecture Context
Packet lineage for the base and every patch-producing head, each head's impact
delta, its defect frontier and trend, its verification-obligation statuses,
the independent `obligations_blocked` boolean, and the campaign architecture
verdict.
The packet's defect-frontier identity is `(invariant_id, mechanism_id,
boundary_id, obligation_id)`; comments and duplicate clusters are evidence,
not frontier units.

When a successor Review Session is opened, its lineage record MUST preserve,
without rewriting, the prior immutable Session ID, frozen head/snapshot,
cutoff and cursor evidence, QA verdict, and delivery state. The successor MUST
create its own current Session ID, head/snapshot, cutoff/cursor, QA verdict, and
delivery state as separate fields; new evidence or state transitions MUST NOT
overwrite the prior session's values.

One automatic round is:

```text
analyze -> plan -> patch -> verify -> respond -> bounded recheck
```

A duplicate classification, duplicate-cluster update, reply-only response, or
explanation that changes no code does not consume a round. A new patch or
behavior-contract change consumes one. A new defect class, material scope
expansion, or new strategy decision pauses for direction rather than silently
spending a round.

The required two-pass review is not the two-round fuse. Every patch round
receives both pre-implementation analysis and post-implementation rereview.
The default automatic circuit breaker is exactly two rounds. When another patch
is required after those rounds, the governor decision is
`AUTOMATION_FUSE_EXHAUSTED`; it is distinct from convergence and from
`NON_CONVERGING_REMEDIATION_STRATEGY`. Duplicates, reply-only responses, and
other no-code dispositions remain permitted. No automatic round three is
authorized.

A user may explicitly resolve a named pause reason and extend the fuse.
Record the extension and transition `PAUSED -> OPEN` only while the current
head, cutoff, and scope assumptions remain valid. If any of those assumptions
changed, remain `PAUSED` until recorded explicit user direction selects a
successor Review Session and the Review Campaign independently permits it;
changed assumptions never auto-open a session.

## Review Campaign

A `Review Campaign` is the cumulative review/fix lineage for one pull request
across every Review Session. Reconstruct it before opening a session whenever
the PR already has review history. Starting a new session never resets campaign
history, cumulative churn, or an unresolved strategy pause.

Record at least the original PR goal and safe boundary, prior sessions and
patch-producing heads, defect-class lineage, remediation strategy and premises,
cumulative semantic-surface growth, campaign pause reasons, the Architecture
Context Packet lineage including each head's independent `obligations_blocked`
boolean and per-obligation status, and the campaign architecture verdict.
Classify each fresh finding as `ORIGINAL_DEFECT`, `SAME_INVARIANT`,
`REMEDIATION_REGRESSION`, `MECHANISM_DEFECT`, or `INDEPENDENT`.

Before another patch, apply the architecture-aware campaign governor. Every
operator MUST read [Review governor](references/review-governor.md), the single
normative human/agent policy, and record its evidence decision identifier.
This SKILL does not duplicate numeric campaign thresholds. A
`STRATEGY_RESET_REQUIRED` decision pauses patching and reopens the remediation
strategy; do not infer strategy failure from comment or session counts.
`AUTOMATION_FUSE_EXHAUSTED` is an automatic circuit-breaker state, not a
`NON_CONVERGING_REMEDIATION_STRATEGY` finding. The latter requires the
governor's independent evidence decision and must never be used to conceal
fuse exhaustion.

Independent defects and duplicate comments do not create defect-frontier units.
When the campaign is paused for strategy review, do not patch, trigger
another automated reviewer such as `@codex review`, or use zero unresolved
threads as a completion condition. Report the evidence, viable strategy
choices, migration or rollback boundary, and the exact user decision required
to continue.
Ordinary feedback that needs user direction pauses only the active Review
Session. It changes the campaign state only when it satisfies a named
campaign-level strategy pause.
The campaign state is `OPEN` while sessions may proceed, `CONVERGED` only when
the original PR goal and safe boundary are complete with no unresolved campaign
pause reason, the governor decision is `CONVERGED`, the current architecture
verdict is `LOCAL_SAFE` or explicitly authorized `APPROVED_EXPANSION`, the
independent patch-plane fact is `patch_required: false`, the independent
verification-plane fact is `obligations_blocked: false`, all required
obligations are complete, and acceptable QA is complete. Delivery remains
separately reported and does not gate campaign convergence. `PAUSED` only for
a named campaign-level strategy pause, `BLOCKED` when an external prerequisite
prevents that decision, and `STOPPED` when the campaign is intentionally ended
without convergence.

Use
[Campaign convergence and strategy reset](references/review-campaign.md) as the
campaign-history reference for cross-session lineage, finding-origin taxonomy,
campaign reconstruction, and resume rules after a strategy pause. It is not the
normative authority for whether another patch may proceed.

Use [Review governor](references/review-governor.md) as the normative
patch-decision reference. Its authorization, fuse, and circuit-breaker
decisions are separate from campaign-history reconstruction and do not replace
the campaign record.

## Architecture-aware review governor

The architecture-aware governor is mandatory before deriving a review lens for
any risk-appropriate review (at minimum `R2`/`R3`, architecture-sensitive work,
or work whose inspection may cross the approved boundary). First create or
refresh an Architecture Context Packet with a base-SHA architecture baseline
and a per-head impact delta. The baseline covers components, dependencies,
public contracts, persistence, ownership, runtime flows, and known dynamic
gaps; the delta explains what the current head changes against that baseline.
Missing or stale baseline/delta evidence is `INSUFFICIENT_ARCHITECTURE_EVIDENCE`:
do not derive the lens, patch, or claim completion until the packet is repaired.

Wide inspection and edit authority are different. Wide inspection MAY traverse
related components, dependencies, contracts, persistence, ownership, runtime
flows, and dynamic surfaces to establish impact. An `APPROVED_EXPANSION`
verdict only widens the approved edit boundary when explicit authorization and
impact evidence are recorded; it never grants automatic patch authority.
Automatic edits still require explicit authority and a current `CONTINUE_LOCAL`
governor decision. Otherwise classify the candidate as `out-of-scope`, record
the coverage gap, and pause as required by the governor.

Use the following decision identifiers exactly as the governor output:

- `CONTINUE_LOCAL`: the packet and impact delta support a bounded edit within
  the approved boundary.
- `IMPACT_REVIEW_REQUIRED`: the frontier or impact delta is stable, expanding,
  or regressing, or the inspection found a material boundary effect; stop local
  patching and perform an independent architecture review.
- `STRATEGY_RESET_REQUIRED`: a premise is invalid, the mechanism is defective,
  the boundary expansion is unapproved, a new semantic dimension appears, or
  risk is higher than authorized; stop patching and reopen strategy.
- `INSUFFICIENT_ARCHITECTURE_EVIDENCE`: the baseline, per-head delta,
  obligation coverage, or dynamic-surface evidence is missing, stale, unknown,
  or high-risk; `obligations_blocked: true` is itself sufficient to block the
  decision until evidence is complete.
- `AUTOMATION_FUSE_EXHAUSTED`: the exact two-round automatic circuit breaker
  has stopped a further required patch while obligations are not blocked; this
  is neither convergence nor strategy-failure evidence by itself.
- `CONVERGED`: the defect frontier is `empty`, verification obligations are
  complete, `obligations_blocked: false`, QA is acceptable, the architecture
  verdict is acceptable, and `patch_required: false`.

An available but unfinished obligation is represented as `obligations_blocked:
false` with an independent `incomplete` status. It is not silently promoted to
`complete` or conflated with the blocked state; it prevents convergence but
does not by itself prohibit a shrinking local patch or consume the fuse.

Track frontier trends as `empty`, `shrinking`, `stable`, `expanding`, or
`regressing`. Unknown or high-risk coverage gaps block evidence. A stable,
expanding, or regressing frontier requires `IMPACT_REVIEW_REQUIRED` unless a
stronger decision applies. The architecture verdict remains separate from the
governor decision:

- `NOT_ASSESSED`: no architecture completion claim is permitted.
- `LOCAL_SAFE`: the inspected change is safe within the approved boundary.
- `APPROVED_EXPANSION`: a broader boundary is safe only because explicit
  authorization and impact evidence are recorded.
- `STRATEGY_REVIEW_REQUIRED`: architecture evidence invalidates the current
  mechanism or strategy; do not patch locally.
- `BLOCKED`: a required architecture prerequisite or evidence obligation is
  unavailable or unresolved.

## Workflow

1. Initialize and freeze the target.
   - Prefer the current branch PR via
     `gh pr view --json number,url,headRefName,baseRefName,headRefOid`.
   - If no current PR exists, ask for the PR URL or number.
   - Reconstruct the Review Campaign from the PR goal, commits, review
     submissions, thread history, and prior session or strategy records. Apply
     the campaign convergence governor before creating a new Session ID. If it
     pauses, stop before patching or triggering another automated review.
   - Confirm the active repository, worktree, branch, and PR head. Create the
     Session ID, record the initial head, and set a server-comparable feedback
     cutoff plus a fixed recheck deadline at least one minute and thirty seconds
     in the future before reading feedback. The deadline is non-resetting.
   - Freeze the initial thread cursor and IDs for this session, but do not use
     cursor membership as admission. Include a comment or reply in the initial
     batch only when its own `createdAt` is at or before the cutoff; anything
     fetched during the initial read with a later timestamp is classified as
     post-cutoff feedback and cannot become `current` through the frozen IDs.
   - Confirm `gh auth status` immediately before any GitHub write. Reading
     public or already-authorized review state does not authorize a write.

2. Read thread-aware review state and cluster duplicates.
   - Use `gh api graphql` because flat comment APIs lose `isResolved`,
     `isOutdated`, and thread anchors.
   - Record unresolved thread ID, comment ID, path, line, author, body,
     `createdAt` or equivalent immutable arrival metadata, and outdated or
     resolved state, along with the session cursor and snapshot.
   - Refetch known thread IDs as well as pages after the initial cursor so a
     reply on an existing thread is classified against the same cutoff. Treat
     each newly observed comment or reply as its own arrival for cutoff
     classification; a frozen parent thread does not make a late reply current.
   - Cluster duplicate and reply-only feedback by root cause. Keep every thread
     ID and disposition visible, but do not spend one automatic round per
     duplicate or reply.
   - Ignore resolved or outdated threads by default, but include them when they
     provide evidence that the same defect still exists at the current head.

3. Classify incoming feedback without silently extending the session.
   - `current`: every actionable thread in the frozen batch, including initial
     non-blocking feedback, plus same-class blocking feedback created by the
     cutoff while budget remains and the behavior surface does not materially
     expand.
   - `queued`: later non-blocking comments or replies, including feedback on a
     frozen thread that can wait for a later session.
   - Duplicate, reply-only, and other no-code feedback is always dispositioned
     without consuming a round or triggering budget-exhaustion pause, whether
     current or queued.
   - `pause`: a new defect class, material behavior or scope expansion, new
     public-contract or production-dependency decision, a same-class blocking
     comment or reply created after the cutoff (even on a frozen thread), a
     campaign-level strategy pause, or a required patch after the automatic
     budget is exhausted. Pause for user direction; do not turn adjacency or a
     fresh Session ID into automatic authorization.
   - A paused session cannot be `CONVERGED` until every named review pause
     reason is resolved or a recorded explicit user direction selects an explicit
     follow-up, new session, or successor session and the Review Campaign
     independently permits that disposition. Assign a named pause to an explicit
     follow-up only after recorded explicit user direction
     selects that disposition and the Review Campaign independently permits it.
     Move a named pause to a new session or successor session only after
     recorded explicit user direction selects that disposition and the Review
     Campaign independently permits it. Campaign `OPEN` or permission,
     classification, and a fresh Session ID never authorize either disposition
     by themselves. The QA verdict does not create or resolve the
     review-convergence pause. It remains independent.
   - A new head is not proof that the session converged. Mark prior evidence
     stale for pass purposes, bind the next analysis and QA obligations to the
     new snapshot, and keep the cutoff and fixed deadline unchanged.

4. Validate the feedback.
   - Determine whether each comment is correct, incorrect, ambiguous,
     duplicate, informational, or already addressed.
   - Validate simple editorial feedback locally and perform a quick repeated-
     occurrence scan. Skip broader analysis only with an explicit reason.
   - Use an independent validation pass when feedback is security-, data-,
     operations-, architecture-, or regression-sensitive, ambiguous, or
     conflicting. Keep the raw comment and relevant artifacts free of a
     preferred conclusion.
   - Record why a lightweight validation was sufficient when skipping the
     independent pass.

5. Establish architecture evidence and extract the review lens.
   - Before deriving a review lens for a risk-appropriate review (at minimum
     `R2`/`R3` or architecture-sensitive work), require a base-SHA architecture
     baseline and a per-head impact delta in the Architecture Context Packet.
     Bind both to the current `headRefOid`; stale, unknown, or high-risk gaps
     produce `INSUFFICIENT_ARCHITECTURE_EVIDENCE`.
   - Project `obligations_blocked` explicitly in the packet and governor input.
     Set it to `true` only when a required capability, prerequisite, or
     evidence artifact is unavailable or inaccessible. When the capability is
     available but execution or evidence has not reached a terminal result, set
     it to `false` and retain the obligation's separate `incomplete` status.
   - Distinguish wide inspection from bounded edit authority. Inspecting
     related architecture may establish impact, but only the approved boundary
     or an explicitly approved expansion authorizes edits.
   - For each actionable feedback cluster, record the observed symptom,
     root-cause hypothesis, violated invariant, likely failure modes, search
     anchors, bounded search surface, risk, and campaign finding origin.
   - Do not plan the final edit until the cause, credible search boundary, and
     architecture impact are understood. Map every thread, including reply-only
     threads, to a cluster or an explicit disposition.

6. Audit the related surface.
   - Inspect the reported function, including error, cleanup, retry, and early
     return paths.
   - Inspect sibling implementations, callers, callees, producers, and
     consumers that share the same contract or invariant.
   - Search exact textual or structural patterns, then inspect semantic
     analogues that may use different syntax.
   - Inspect related tests, configuration variants, migrations, and
     documentation when they encode the same behavior.
   - Route navigation by question and capability instead of running every tool:
     use `rg` for literal/configuration discovery, AST for syntax-shaped
     analogues, LSP for symbol relationships, and a fresh code graph for
     bounded direct or transitive traversal.
   - Prefer the compact route when those capabilities are justified: AST roots
     -> bounded graph candidates -> LSP verification and delta. Do not expose
     accumulated raw tool output when a compact evidence ledger is sufficient.
   - Read [Code navigation and evidence routing](references/code-navigation.md)
     before using AST, LSP, or Graphify. Record capability and freshness checks,
     fallbacks, and any resulting coverage gap.
   - Do not claim completeness from one text search, one graph query, or one
     language-server response.

7. Classify every credible candidate.
   - Mark it `affected` when the same invariant is violated within the current
     fix boundary.
   - Mark it `safe` only with differentiating evidence.
   - Mark it `uncertain` when more evidence is required; do not silently discard
     it.
   - Mark it `out-of-scope` when the defect is real but requires a materially
     broader product, architecture, repository, migration, or production
     decision.
   - In the operational policy, when a candidate is confirmed `out-of-scope`,
     record it in the ledger and report the evidence to the user immediately;
     do not defer either action until the final report. If its required
     follow-up obligation is unavailable or unauthorized, explicitly set
     `obligations_blocked: true` for that obligation in the packet, ledger, and
     governor input. Do not project `obligations_blocked: false` or continue
     locally for this finding while that obligation remains blocked. Reporting
     alone never clears the blocked state; only a recorded authorized
     disposition that closes the obligation or newly available required
     capability, prerequisite, or evidence can clear it. This is evidence-only
     and does not authorize an edit or follow-up assignment. The
     immediate-reporting rule applies to operational findings only, not
     acceptance examples or other illustrative scenarios.
   - Treat any unclassified high-risk candidate as a completion blocker.
   - Keep candidate provenance distinct: `text-matched`, `AST-matched`,
     `graph-extracted`, `graph-inferred`, `LSP-resolved`, or `runtime-proven`.
     A graph-inferred or ambiguous edge is a lead, not defect confirmation.
   - Maintain a compact ledger containing candidate, `path:line`, relation,
     provenance, freshness/confidence, and disposition.

8. Plan by defect class.
   - Group fixes by root cause or invariant and map each review thread to its
     defect class.
   - Include all `affected` candidates, reply-only threads, uncertain items, and
     `out-of-scope` candidates as named `PAUSED` items; in the operational
     policy, record and report each confirmed out-of-scope candidate immediately
     rather than deferring evidence until the final report. For a confirmed
     operational out-of-scope defect whose required follow-up is unavailable or
     unauthorized, preserve `obligations_blocked: true` on the named obligation;
     reporting does not clear it, and it must not be projected as `false` or
     mapped to `CONTINUE_LOCAL`. Only a recorded authorized disposition or
     newly available required capability, prerequisite, or evidence can clear
     that blocked state. Reporting does not authorize editing or follow-up
     assignment, and do not create or assign an explicit follow-up
     automatically. Acceptance examples and illustrative scenarios do not
     create an immediate-reporting obligation.
   - Record an `out-of-scope` follow-up only after recorded explicit user
     direction selects that candidate and the Review Campaign independently
     permits the new-session or follow-up disposition. Campaign `OPEN` or
     permission, and classification alone, never authorizes the disposition.
   - Pause before editing when the safe boundary is materially larger than the
     requested PR or conflicts with another requirement.
   - Do not convert a campaign-level mechanism failure into another local
     defect-class patch. Reopen the implementation strategy first.

9. Apply the build-versus-buy gate and memoize the strategy when it is warranted.
   - Do not turn every review into a build-versus-buy exercise. Open the gate
     only when the fix needs a new production dependency, a nontrivial
     subsystem, a public-contract change, or implementation of a protocol,
     parser, cryptographic primitive, or concurrency mechanism.
   - Present credible options: direct implementation, reuse of an existing
     project dependency, a new open-source dependency, and a follow-up PR.
   - Compare requirement fit, implementation size, maintenance ownership,
     security, license compatibility, transitive dependencies, performance,
     integration cost, and replacement cost. Recommend one option with
     evidence.
   - Require explicit user approval before adding a production dependency or
     materially expanding the authorized architecture. A new dependency is an
     option, not an authorization.
   - Memoize the chosen strategy and every material comparison premise in both
     the campaign and current session. Reuse it only while
     those premises remain valid. Repeated `MECHANISM_DEFECT` evidence is
     material premise invalidation and reopens the strategy decision. Reopen the
     decision when requirements, implementation size, maintenance, security,
     license, dependency, performance, integration, or replacement assumptions
     materially change; otherwise do not relitigate it during review churn.

10. Validate reaction dispositions without mutating GitHub during intake.
    - Classify each validated comment as `+1` for correct/actionable feedback or
      `-1` for incorrect/not-actionable feedback, with a concise evidence-based
      explanation for `-1`.
    - Do not react to ambiguous comments until resolving the ambiguity.
    - Record the intended reaction and check existing reactions where practical
      to avoid duplicates, but defer the GitHub reaction write until the
      post-push response phase whenever this session produces a patch.
    - For a no-code disposition, a reaction, reply, or resolution may be written
      only after a fresh `headRefOid` read confirms that no patch is required
      and the current-head no-code verification path is complete.
    - GitHub writes remain subject to explicit user authorization or a request
      for end-to-end review response; a review session never grants authority
      by itself.

11. Execute bounded patch rounds.
    - Re-read `headRefOid` and confirm that the Review Campaign remains `OPEN`
      before each patch cycle. If the remote PR head differs from the session's
      current head, do not patch against stale analysis; rebind or pause
      according to the authorized scope.
    - Before each patch, perform the pre-implementation review using the defect
      lens, Architecture Context Packet baseline and current-head impact delta,
      defect frontier, and candidate ledger. Scope edits to verified feedback
      and same-class `affected` candidates, not merely to the exact lines named
      by the reviewer.
    - Record and obey the governor decision before editing. Only a current
      `CONTINUE_LOCAL` decision permits an automatic bounded edit;
      `IMPACT_REVIEW_REQUIRED`, `STRATEGY_RESET_REQUIRED`, or
      `INSUFFICIENT_ARCHITECTURE_EVIDENCE` stops local patching. An
      `APPROVED_EXPANSION` may widen the approved boundary only with explicit
      authority; it never substitutes for `CONTINUE_LOCAL` or authorizes
      patching by itself.
    - Implement cause-level minimal fixes. Exclude weakly related cleanup and
      speculative refactoring. Preserve unrelated worktree changes and follow
      repository patterns.
    - Add or update tests that encode the invariant and meaningful failure
      paths, not only the reported example.
    - After the patch, reread the complete diff through the same defect lens.
      Then perform an independent post-review with a fresh architecture lens:
      compare the base baseline with the new head's impact delta, boundary,
      contracts, persistence, ownership, runtime flows, strategy premises,
      dynamic gaps, frontier, and obligations. Do not reuse the pre-review
      architecture conclusion.
    - Record the independent architecture verdict and governor decision as
      preliminary results before verification and response. A patch changes the
      head, so bind all new evidence to that head; the preliminary decision
      cannot establish convergence or completion.
    - A duplicate, reply-only response, or explanation-only response may be
      handled between rounds without incrementing the automatic round counter.
      Never use that rule to conceal a code or behavior change.

12. Verify the pre-push candidate and bind final QA to the pushed head.
    - Re-read `headRefOid` immediately before verification. A mismatch
      invalidates QA readiness and requires obligations bound to the new head.
    - Run focused tests for the invariant and the repository's canonical local
      or CI gate. If the canonical gate is unavailable or too broad, run the
      nearest documented gate and state the gap. These pre-push results are
      candidate evidence because the remote PR head has not changed yet.
    - Record command or scenario identity, target snapshot, timestamps, exit
      status, relevant output, artifacts, and the linked obligation. An
      unavailable required capability, prerequisite, or evidence artifact sets
      `obligations_blocked: true`; an available capability whose mandatory
      execution or evidence does not reach a terminal result sets
      `obligations_blocked: false` with an independent `incomplete` status.
      Neither state is a pass.
    - A blocked obligation requires
      `INSUFFICIENT_ARCHITECTURE_EVIDENCE` and prohibits both `CONTINUE_LOCAL`
      and `AUTOMATION_FUSE_EXHAUSTED`; do not conflate it with an
      available-but-incomplete obligation.
    - For a risk-appropriate review, bind the architecture verdict and the
      current head's impact delta to pre-push evidence. `NOT_ASSESSED`,
      missing baseline/delta, or unresolved high-risk coverage gaps cannot
      satisfy the architecture obligation.
    - After current-head QA and all verification obligations are complete,
      reevaluate the governor decision against that evidence. Do not record
      `CONVERGED` before this reevaluation; the post-rereview decision remains
      preliminary until current-head QA and obligations finish.
    - Do not use `--no-verify` unless the repository's exception policy is
      satisfied.
    - Keep QA separate from review convergence. `FAIL`, `BLOCKED`, and
      `INCOMPLETE` QA can never be called complete because threads were replied
      to or resolved.

13. Push, rebind, and verify the delivered head before response writes.
    - Re-read `headRefOid` immediately before commit and push. A mismatch
      invalidates delivery readiness; do not write or push stale-head work.
    - Commit with a message that identifies the corrected behavior and record
      the exact local commit SHA that will be pushed. Push normally so hooks
      run. If environment restrictions break hooks, rerun the same normal push
      in an authorized environment instead of bypassing verification.
    - After push, read the remote head again and require it to equal the
      recorded pushed commit SHA before binding evidence. If it differs,
      invalidate delivery and QA readiness, do not bind local evidence to the
      other contributor's head, and fetch/rebind that head before rerunning the
      complete verification.
    - Only after the equality check passes, bind the session to the pushed SHA.
    - If the source worktree has any uncommitted edits—including related,
      generated, or hook-created changes—create a clean detached or temporary
      worktree at the recorded pushed SHA. Preserve the source worktree; dirty
      worktree evidence is not snapshot-bound.
    - Rerun the required focused verification and canonical gate against the
      pushed SHA from that clean worktree when the source worktree was dirty;
      otherwise use the clean source worktree. Pre-push evidence remains
      informative but cannot satisfy the pushed-head QA obligation by itself.
    - Where a patch is pushed, reevaluate the governor after pushed-head
      verification and bind any convergence claim to the verified pushed SHA.
      Pre-push or preliminary governor evidence cannot satisfy the pushed-head
      obligation.
    - Before every GitHub write—each reaction, each reply, and each
      resolution—re-read `headRefOid` immediately. Do not reuse one head reread
      as the guard for a later mutation. A mismatch invalidates response
      readiness; rebind and reverify before that write.
    - Add the recorded reactions only after the per-write head reread and the
      pushed-head verification for a patch session. For a no-code disposition,
      use the current-head no-code path from step 10; never react from stale
      pre-patch evidence.
    - Reply to each addressed thread with the direct fix, same-class audit
      result, and snapshot identity. Cite the post-push gate for a patch, or
      the current-head no-code verification for an explanation-only response.
    - Resolve only threads whose requested change or explanation is complete.
      Leave ambiguous, invalid, uncertain, or blocked threads unresolved with a
      clear evidence-based reply.
    - Record delivery independently as `NOT_STARTED`, `READY`, `REPLIED`,
      `RESOLVED`, or `PUSHED`; delivery events do not establish QA or review
      convergence.

14. Perform one bounded feedback admission and closed-set reconciliation.
    - At the fixed observation deadline, inspect the current head, known thread
      IDs, pages after the frozen cursor, new comments, duplicate clusters,
      review decision, mergeability, and CI or required-check status.
    - Classify each newly observed comment or reply by its immutable
      `createdAt` metadata against the server-comparable cutoff. The cutoff and
      deadline do not reset because feedback was fetched late or arrived near
      them.
    - Same-class blocking comments or replies created by the cutoff may join
      only while patch budget remains. A same-class blocking comment or reply
      created after the cutoff cannot join this session, even on a frozen
      thread: record it as a named `PAUSED` reason. Assign it to a new session
      or explicit follow-up only after recorded explicit user direction selects
      that disposition and the Review Campaign independently permits it.
      Campaign `OPEN` or permission, and classification alone, never authorizes
      a new-session or follow-up assignment.
      Non-blocking comments and replies are queued. A new defect class, material
      strategy decision, campaign-level strategy pause, or required patch after
      exhausted budget also pauses the review session; QA retains its
      independent verdict.
    - If admitted feedback causes a patch and a new head, rerun the independent
      architecture post-review, recompute the per-head impact delta and defect
      frontier, and record the new architecture verdict before reconciling
      QA and delivery readiness. Never admit feedback created after the
      original cutoff into this session.
    - At this bounded recheck, reevaluate the governor again against the
      current head, final frontier, obligations, QA, architecture verdict, and
      delivery/review state before declaring completion. A pre-verification or
      earlier-head `CONVERGED` result cannot satisfy this final recheck.
    - Do not repeat feedback admission as an unbounded response loop. If another
      patch would be needed after two automatic rounds, record
      `AUTOMATION_FUSE_EXHAUSTED`, stop at `PAUSED`, and request explicit user
      direction. Do not relabel fuse exhaustion as
      `NON_CONVERGING_REMEDIATION_STRATEGY`; a new session is not a fuse reset,
      and the Review Campaign must independently permit it.

15. Report the evidence and independent outcomes.
    - Summarize the Campaign state and finding-origin counts, Session ID, frozen
      head and cursor, current head, deadline, thread dispositions, duplicate
      clusters, review lenses, search boundaries, candidate classifications,
      same-class fixes, explicit follow-ups, strategy memo, Architecture
      Context Packet fields including the independent `patch_required` and
      `obligations_blocked` booleans, base and per-head impact deltas,
      defect-frontier identity and trend, per-obligation complete/incomplete/
      blocked statuses, architecture obligations, governor decisions,
      architecture verdicts, reactions, commits, tests, gates, and final
      recheck results.
    - Report review convergence, governor decision, architecture verdict,
      `patch_required`, `obligations_blocked`, obligation completeness/status,
      QA verdict, and delivery state as separate fields. A true
      `obligations_blocked` value MUST be reported with
      `INSUFFICIENT_ARCHITECTURE_EVIDENCE` and never as `CONTINUE_LOCAL` or
      `AUTOMATION_FUSE_EXHAUSTED`; `obligations_blocked: false` MUST NOT be
      reported as proof that obligations are complete. Likewise,
      `patch_required: false` alone MUST NOT be reported as proof of any of
      those other outcomes. State which navigation capabilities were used,
      whether their state was current for the inspected snapshot, and which
      semantic or dynamic surfaces remain unverified.

    - If no related defect was found, report what surfaces and patterns were
      checked instead of stating only that none existed.

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

## Optional Traceknot handoff

Traceknot is an optional integration for ordinary lower-risk sessions, not an
unconditional dependency. It is the required QA handoff for every `R2`/`R3`
change and recurring review loop. Bind the handoff to the session's current
head, review-lens obligations, risk, and test basis.

Accept only evidence-backed Traceknot observations and verdicts; an agent's
completion claim, a lifecycle event, or a green gate alone is not QA proof. A
Traceknot `FAIL`, `BLOCKED`, or `INCOMPLETE` verdict keeps QA in that state
until resolved or explicitly accepted under the applicable policy. When
Traceknot is selected or required, an unavailable required capability makes the
handoff `BLOCKED` and sets `obligations_blocked: true`. If the capability
exists but mandatory execution or evidence does not reach a terminal result,
the handoff is `INCOMPLETE` with `obligations_blocked: false`. Neither state
may silently fall back to a self-check or add a dependency. An ordinary
session for which the handoff is neither selected nor required uses its
canonical focused obligations; Traceknot absence alone does not block that QA.
Traceknot does not own review convergence, GitHub thread resolution, or delivery
state.

## Completion contract

`patch_required` is not a completion verdict or a substitute for any of the
four outcomes below. Its `false` value means only that no behavior or code
patch is currently required; it MUST NOT by itself establish review
convergence, successful or acceptable QA, or delivery completion.
`obligations_blocked` is likewise an independent verification-plane status, not
a completeness verdict. `obligations_blocked: true` means evidence is
insufficient; `false` still permits an independent `incomplete` status.

Evaluate four independent outcomes:

- Review convergence is `CONVERGED` only when every thread in the frozen batch
  and every admitted same-class thread has a disposition, every credible
  in-scope candidate is classified, every `affected` candidate is fixed or
  explicitly blocked, later non-blocking feedback remains queued unless it is
  assigned to an explicit follow-up or a new session only after recorded
  explicit user direction selects that assignment and the Review Campaign
  independently permits it, and no unresolved session pause reason remains.
  Feedback requiring user direction keeps the session `PAUSED`; it changes the
  campaign state only when it is a named campaign-level strategy pause.
  Classification alone cannot satisfy convergence. Duplicates and reply-only
  threads are dispositioned without consuming a round.
- Architecture outcome is acceptable only when the current head has an
  independent architecture post-review, `obligations_blocked: false`, its
  obligations and impact delta are complete, and the architecture verdict is
  `LOCAL_SAFE` or explicitly authorized `APPROVED_EXPANSION`. `NOT_ASSESSED`,
  `STRATEGY_REVIEW_REQUIRED`, and `BLOCKED` verdicts, missing architecture
  evidence, or unresolved high-risk architecture coverage gaps cannot
  complete.
- The QA verdict is acceptable only when mandatory verification obligations for
  the current head pass, or the user explicitly accepts every remaining
  material risk. An earlier-head result, lifecycle event, or green gate alone
  cannot establish this outcome. `FAIL`, `BLOCKED`, and `INCOMPLETE` never
  become success; `obligations_blocked: true` is insufficient evidence, not
  completeness.
- Delivery is complete only when replies, reactions, resolution, commits, and
  pushes match the authorized implementation state.

Overall completion requires campaign and session review convergence, a
`CONVERGED` governor decision recorded after current-head QA and obligations,
after pushed-head verification where applicable, and again at the bounded
recheck, `obligations_blocked: false` with complete obligations, an acceptable
architecture verdict, an acceptable QA verdict, and the authorized delivery
state. The bounded final recheck is review-convergence evidence; it does not
replace architecture or QA evaluation, restart the session indefinitely, or
reset campaign churn.

## GitHub CLI notes

- Use `gh api graphql` for thread reads and resolution.
- Perform GitHub writes only when the user explicitly authorizes them or asks
  for end-to-end review response.
- Use `+1` for 👍 and `-1` for 👎 reaction content.
