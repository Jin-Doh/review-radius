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
| Automatic round and two-round automatic patch budget | Bound repeated review/fix cycles; the default budget is two automatic patch rounds. |
| Fixed recheck deadline | Bound the final recheck; new arrivals never reset it. |
| Scope boundary and authorization | Preserve the approved behavior and repository surface. |
| Strategy-decision memo and premises | Reuse an approved choice only while every material comparison premise remains valid. |
| Review convergence | `OPEN`, `CONVERGED`, `PAUSED`, or `BLOCKED`. |
| QA verdict | `NOT_RUN`, `PASS`, `PASS_WITH_ACCEPTED_RISK`, `FAIL`, `BLOCKED`, or `INCOMPLETE`. |
| Delivery state | `NOT_STARTED`, `READY`, `REPLIED`, `RESOLVED`, or `PUSHED`. |

<!-- markdownlint-enable MD013 -->

All observations, candidate dispositions, tests, gates, replies, and decisions
must identify the session and the head/snapshot from which they were obtained.
This makes the evidence snapshot-bound. A later head makes earlier pass evidence
informative but insufficient: rerun the required evidence against the new head
before calling that head verified.

One automatic round is:

```text
analyze -> plan -> patch -> verify -> respond -> bounded recheck
```

A duplicate classification, duplicate-cluster update, reply-only response, or
explanation that changes no code does not consume a round. A new patch or
behavior-contract change consumes one. A new defect class, material scope
expansion, or new strategy decision pauses for direction rather than silently
spending a round.

The required two-pass review is not the two-round budget. Every patch round
receives both pre-implementation analysis and post-implementation rereview.
The default automatic budget is two rounds. Budget exhaustion pauses only when
another patch is required; duplicates, reply-only responses, and other no-code
dispositions remain permitted. No automatic round three is authorized.

A user may explicitly resolve a named pause reason and extend the budget.
Record the extension and transition `PAUSED -> OPEN` only while the current
head, cutoff, and scope assumptions remain valid; otherwise start a new session.

## Workflow

1. Initialize and freeze the target.
   - Prefer the current branch PR via
     `gh pr view --json number,url,headRefName,baseRefName,headRefOid`.
   - If no current PR exists, ask for the PR URL or number.
   - Confirm the active repository, worktree, branch, and PR head. Create the
     Session ID, record the initial head, and set a server-comparable feedback
     cutoff and fixed recheck deadline before reading feedback.
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
     comment or reply created after the cutoff (even on a frozen thread), or a
     required patch after the automatic budget is exhausted. Pause for user
     direction; do not turn adjacency into automatic authorization.
   - A paused session cannot be `CONVERGED` until every named review pause
     reason is resolved or moved to a new session. The QA verdict does not
     create or resolve a review-convergence pause; it remains independent.
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

5. Extract the review lens.
   - For each actionable feedback cluster, record the observed symptom,
     root-cause hypothesis, violated invariant, likely failure modes, search
     anchors, bounded search surface, and risk.
   - Do not plan the final edit until the cause and credible search boundary are
     understood. Map every thread, including reply-only threads, to a cluster or
     an explicit disposition.

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
   - Treat any unclassified high-risk candidate as a completion blocker.
   - Keep candidate provenance distinct: `text-matched`, `AST-matched`,
     `graph-extracted`, `graph-inferred`, `LSP-resolved`, or `runtime-proven`.
     A graph-inferred or ambiguous edge is a lead, not defect confirmation.
   - Maintain a compact ledger containing candidate, `path:line`, relation,
     provenance, freshness/confidence, and disposition.

8. Plan by defect class.
   - Group fixes by root cause or invariant and map each review thread to its
     defect class.
   - Include all `affected` candidates, reply-only threads, uncertain items,
     and explicit follow-ups for `out-of-scope` defects.
   - Pause before editing when the safe boundary is materially larger than the
     requested PR or conflicts with another requirement.

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
   - Memoize the chosen strategy and every material comparison premise in the
     session. Reuse it only while those premises remain valid. Reopen the
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
    - Re-read `headRefOid` before each patch cycle. If the remote PR head differs
      from the session's current head, do not patch against stale analysis;
      rebind or pause according to the authorized scope.
    - Before each patch, perform the pre-implementation review using the review
      lens and candidate ledger. Scope edits to verified feedback and
      same-class `affected` candidates, not merely to the exact lines named by
      the reviewer.
    - Implement cause-level minimal fixes. Exclude weakly related cleanup and
      speculative refactoring. Preserve unrelated worktree changes and follow
      repository patterns.
    - Add or update tests that encode the invariant and meaningful failure
      paths, not only the reported example.
    - After the patch, reread the complete diff through the same review lens.
      Check incomplete sibling fixes, new asymmetry, missed negative paths,
      unsafe compatibility changes, and tests that overfit the original line.
    - Run the verification and response steps below, then perform the bounded
      recheck. A patch changes the head, so bind all new evidence to that head.
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
      status, relevant output, artifacts, and the linked obligation. A timeout,
      cancellation, unavailable dependency, missing output, or unfinished
      mandatory obligation is not a pass.
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
    - If the source worktree has unrelated uncommitted edits, create a clean
      detached or temporary worktree at the recorded pushed SHA. Preserve the
      source worktree; dirty-worktree evidence is not snapshot-bound.
    - Rerun the required focused verification and canonical gate against the
      pushed SHA from that clean worktree when the source worktree was dirty;
      otherwise use the clean source worktree. Pre-push evidence remains
      informative but cannot satisfy the pushed-head QA obligation by itself.
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
      thread: record it as a named `PAUSED` reason and assign it to a new
      session or explicit follow-up. Non-blocking comments and replies are
      queued. A new defect class, material strategy decision, or required patch
      after exhausted budget also pauses the review session; QA retains its
      independent verdict.
    - If admitted feedback causes a patch and a new head, run closed-set
      reconciliation for that admitted set and the new head. Revalidate QA and
      delivery readiness, but never admit feedback created after the original
      cutoff into this session.
    - Do not repeat feedback admission as an unbounded response loop. If another
      patch would be needed after two automatic rounds, stop at `PAUSED` and
      request explicit user direction or a new session.

15. Report the evidence and independent outcomes.
    - Summarize the Session ID, frozen head and cursor, current head, deadline,
      thread dispositions, duplicate clusters, review lenses, search
      boundaries, candidate classifications, same-class fixes, explicit
      follow-ups, strategy memo, reactions, commits, tests, gates, and final
      recheck results.
    - Report review convergence, QA verdict, and delivery state as separate
      fields. State which navigation capabilities were used, whether their
      state was current for the inspected snapshot, and which semantic or
      dynamic surfaces remain unverified.
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
handoff `BLOCKED`. If the capability exists but mandatory execution or evidence
does not reach a terminal result, the handoff is `INCOMPLETE`. Neither state may
silently fall back to a self-check or add a dependency. An ordinary session for
which the handoff is neither selected nor required uses its canonical focused
obligations; Traceknot absence alone does not block that QA.
Traceknot does not own review convergence, GitHub thread resolution, or delivery
state.

## Completion contract

Evaluate three independent outcomes:

- Review convergence is `CONVERGED` only when every thread in the frozen batch
  and every admitted same-class thread has a disposition, every credible
  in-scope candidate is classified, every `affected` candidate is fixed or
  explicitly blocked, later non-blocking feedback is queued or assigned to a
  new session, and no unresolved pause reason remains. Feedback requiring user
  direction keeps the session `PAUSED`; classification alone cannot satisfy
  convergence. Duplicates and reply-only threads are dispositioned without
  consuming a round.
- The QA verdict is acceptable only when mandatory verification obligations for
  the current head pass, or the user explicitly accepts every remaining
  material risk. An earlier-head result, lifecycle event, or green gate alone
  cannot establish this outcome. `FAIL`, `BLOCKED`, and `INCOMPLETE` never
  become success.
- Delivery is complete only when replies, reactions, resolution, commits, and
  pushes match the authorized implementation state.

Overall completion requires review convergence, an acceptable QA verdict, and
the authorized delivery state. The bounded final recheck is
review-convergence evidence; it does not replace QA evaluation or restart the
session indefinitely.

## GitHub CLI notes

- Use `gh api graphql` for thread reads and resolution.
- Perform GitHub writes only when the user explicitly authorizes them or asks
  for end-to-end review response.
- Use `+1` for 👍 and `-1` for 👎 reaction content.
