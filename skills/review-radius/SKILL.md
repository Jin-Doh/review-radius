---
name: review-radius
description: Handle GitHub PR review feedback end to end. Use when asked to inspect or address review comments, requested changes, unresolved threads, or follow-up reviews; validate each comment, derive the underlying invariant, audit related code for the same defect class, implement bounded fixes, run gates, reply, resolve threads, and recheck review and CI state.
---

# Review Radius

Fix the pattern behind the comment. Handle GitHub review feedback end to end
by treating each comment as evidence of a potential defect class, not as an
exhaustive boundary. Keep the review radius bounded by the validated root cause
and authorized PR scope.

## Workflow

1. Resolve and freeze the target.
   - Prefer the current branch PR via `gh pr view --json number,url,headRefName,baseRefName,headRefOid`.
   - If no current PR exists, ask for the PR URL or number.
   - Confirm the active repository, worktree, branch, and PR head before every
     fix and push cycle.
   - Confirm `gh auth status` before GitHub writes.

2. Read thread-aware review state.
   - Use `gh api graphql` because flat comment APIs lose `isResolved`,
     `isOutdated`, and thread anchors.
   - Record unresolved thread id, comment id, path, line, author, body, and
     outdated or resolved state.
   - Ignore resolved or outdated threads by default, but include them when they
     provide evidence that the same defect still exists at the current head.

3. Validate the feedback.
   - Determine whether each comment is correct, incorrect, ambiguous,
     duplicate, informational, or already addressed.
   - Validate simple editorial feedback locally.
   - Use an independent validation pass when feedback is security-, data-,
     operations-, architecture-, or regression-sensitive, ambiguous, or
     conflicting. Keep the raw comment and relevant artifacts free of a
     preferred conclusion.
   - Record why a lightweight validation was sufficient when skipping the
     independent pass.

4. Extract the review lens.
   - For each actionable feedback cluster, record the observed symptom,
     root-cause hypothesis, violated invariant, likely failure modes, search
     anchors, bounded search surface, and risk.
   - Use a lightweight lens for purely editorial feedback, but still check for
     repeated occurrences. Skip expansion only with an explicit reason.
   - Do not plan the final edit until the cause and credible search boundary are
     understood.

5. Audit the related surface.
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

6. Classify every credible candidate.
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

7. Plan by defect class.
   - Group fixes by root cause or invariant and map each review thread to its
     defect class.
   - Include all `affected` candidates, reply-only threads, uncertain items,
     and explicit follow-ups for `out-of-scope` defects.
   - Pause before editing when the safe boundary is materially larger than the
     requested PR or conflicts with another requirement.

8. React to validated comments when authorized.
   - Add `+1` for correct and actionable feedback.
   - Add `-1` for incorrect or not-actionable feedback and prepare a concise,
     evidence-based explanation.
   - Do not react to ambiguous comments until resolving the ambiguity.
   - Check existing reactions where practical to avoid duplicates.

9. Implement cause-level minimal fixes.
   - Scope edits to verified feedback and same-class `affected` candidates, not
     merely to the exact lines named by the reviewer.
   - Exclude weakly related cleanup and speculative refactoring.
   - Preserve unrelated worktree changes and follow repository patterns.
   - Add or update tests that encode the invariant and meaningful failure
     paths, not only the reported example.
   - Update source-of-truth documentation when behavior, contracts,
     configuration, operations, security assumptions, or workflows change.

10. Rereview the resulting diff.
    - Apply the same review lens to the complete diff after implementation.
    - Check for incomplete sibling fixes, new asymmetry, missed negative paths,
      unsafe compatibility changes, and tests that overfit the original line.
    - Reconcile the candidate inventory with the final diff.

11. Run gates.
    - Run focused tests for the invariant and the repository's canonical local
      or CI gate.
    - If the canonical gate is unavailable or too broad, run the nearest
      documented gate and state the gap.
    - Do not use `--no-verify` unless the repository's exception policy is
      satisfied.

12. Commit and push.
    - Commit with a message that identifies the corrected behavior.
    - Push normally so hooks run.
    - If environment restrictions break hooks, rerun the same normal push in an
      authorized environment instead of bypassing verification.

13. Reply and resolve.
    - Reply to each addressed thread with the direct fix, any same-class audit
      result, and the supporting gate.
    - Resolve only threads whose requested change or explanation is complete.
    - Leave ambiguous, invalid, uncertain, or blocked threads unresolved with a
      clear evidence-based reply.

14. Perform the final completion check.
    - Wait 5 minutes after all known responses are complete.
    - Recheck the PR head, review threads, new comments, review decision,
      mergeability, and CI or required-check status.
    - Repeat the response loop if new actionable feedback or PR-caused failures
      appear.

15. Report the evidence.
    - Summarize thread dispositions, review lenses, search boundaries,
      candidate classifications, same-class fixes, explicit follow-ups,
      reactions, commits, tests, gates, final recheck results, unresolved items,
      and the PR URL.
    - If no related defect was found, report what surfaces and patterns were
      checked instead of stating only that none existed.
    - Report which navigation capabilities were used, whether their state was
      current for the inspected PR head, and which semantic or dynamic surfaces
      remain unverified.

## Completion contract

Declare completion only when every actionable thread is dispositioned, every
credible in-scope candidate is classified, every `affected` candidate is fixed
or blocked explicitly, out-of-scope defects have visible follow-up disposition,
invariant-level tests and required gates pass, and the final wait finds no new
actionable review or PR-caused failing or pending check.

## GitHub CLI notes

- Use `gh api graphql` for thread reads and resolution.
- Perform GitHub writes only when the user explicitly authorizes them or asks
  for end-to-end review response.
- Use `+1` for 👍 and `-1` for 👎 reaction content.
