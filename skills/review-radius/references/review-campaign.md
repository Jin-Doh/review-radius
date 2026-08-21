# Campaign convergence and strategy reset

Use this reference when a pull request has more than one review/fix session,
when feedback is described as recurring or non-converging, or when another
patch would be justified mainly by code introduced during earlier review
responses.

## Purpose

A Review Session bounds one feedback batch. A Review Campaign preserves the
history of the entire pull request across sessions so that opening a fresh
session cannot reset accumulated evidence that the remediation strategy itself
is failing.

The campaign governor answers a different question from ordinary review
validation:

> Are reviewers still finding the original defect class, or are they now
> finding correctness holes in the mechanism introduced to repair it?

The second pattern is an architecture signal. It must not be converted into an
unbounded sequence of locally reasonable patches.

## Campaign record

Reconstruct the record from durable pull-request evidence whenever a prior
session record is unavailable. Prefer immutable GitHub timestamps and commit
SHAs over conversational summaries.

Record:

<!-- markdownlint-disable MD013 -->

| Field | Purpose |
| --- | --- |
| Repository and PR | Bind the campaign to one review lineage. |
| Original base, head, title, body, and goal | Preserve the requested product change before review-driven expansion. |
| Intended safe boundary | State the repository, behavior, contract, and dependency boundary originally authorized. |
| Session lineage | Record Session IDs, cutoffs, heads, patch rounds, pauses, and outcomes. |
| Patch-producing reviews | Distinguish review observations that caused behavior changes from duplicate or reply-only traffic. |
| Defect classes | Preserve the root-cause grouping across sessions. |
| Finding origins | Separate product defects from remediation-mechanism defects. |
| Strategy memo and premises | Preserve why direct implementation, reuse, dependency, or follow-up was chosen. |
| Semantic surface growth | Record newly implemented language, protocol, parser, dispatch, persistence, concurrency, or migration semantics. |
| Campaign convergence | `OPEN`, `CONVERGED`, `PAUSED`, `BLOCKED`, or `STOPPED`. `CONVERGED` means the original PR goal and safe boundary are complete with no unresolved campaign pause reason; `STOPPED` means the campaign was intentionally ended without convergence. |
| Pause reasons | Name the decision required before another patch or reviewer trigger. |

<!-- markdownlint-enable MD013 -->

A Session ID may change. The campaign identity does not change while the pull
request and its original goal remain the same.
Ordinary Review Session pauses do not mutate the campaign state. The campaign
becomes `PAUSED` only for a named campaign-level strategy pause; a session may
be `PAUSED` while the campaign remains `OPEN`.

## Finding-origin taxonomy

Classify every fresh actionable finding with exactly one primary origin. Add a
secondary note when evidence is mixed.

### `ORIGINAL_DEFECT`

The finding is another direct manifestation of the defect that motivated the
pull request. Example: a second cleanup path leaks the same resource as the
reported path.

### `SAME_INVARIANT`

The finding is outside the originally named line but violates the same bounded
invariant in an authorized sibling, caller, or consumer. This is the normal
Review Radius expansion case.

### `REMEDIATION_REGRESSION`

The finding describes behavior that worked before the review response and was
broken by a prior patch in the campaign. Count the patch against campaign churn
even when the regression is easy to fix.

### `MECHANISM_DEFECT`

The finding exposes a correctness hole in a mechanism introduced to implement
or verify the fix. Typical mechanisms include custom parsers, protocol
implementations, static analyzers, dependency-resolution logic, concurrency
coordination, migration frameworks, and policy engines.

A finding remains a `MECHANISM_DEFECT` even when the reviewer supplies a small
one-line reproducer. The classification follows the failing abstraction, not
the size of the immediate patch.

### `INDEPENDENT`

The finding is a real but separate defect that neither shares the original
invariant nor arises from the remediation mechanism. Do not use independent
findings to claim that the mechanism is non-converging. Queue or follow them up
under the normal scope rules.

## Mechanism identity

Group findings by the mechanism whose correctness they challenge, not only by
file or function. Examples:

- `custom PHP source analyzer`
- `home-grown JWT parser`
- `release provenance fallback resolver`
- `retry state machine`
- `schema migration compatibility layer`

A mechanism may span several helpers and defect classes. Renaming or splitting
a helper does not reset its campaign history.

## Convergence governor

Apply the governor before every patch-producing session and again after the
post-implementation review.

Pause with `NON_CONVERGING_REMEDIATION_STRATEGY` when any of the following is
supported by current-head evidence:

1. Three fresh `MECHANISM_DEFECT` findings have accumulated against the same
   remediation mechanism across at least two patch-producing Review Sessions
   (and therefore at least two patch-producing heads).
2. Two consecutive patch-producing Review Sessions are dominated by fresh
   `MECHANISM_DEFECT` or `REMEDIATION_REGRESSION` findings for that mechanism.
3. A material strategy premise is disproved. For example, a "small tokenizer"
   now requires namespace, inheritance, dispatch, reachability, or equivalent
   semantic modeling that was not part of the approved premise.
4. The next patch requires another semantic dimension, public contract,
   production dependency, migration, or nontrivial subsystem merely to keep the
   remediation mechanism correct.
5. A new Session ID is being used primarily to bypass an exhausted automatic
   patch budget or an unresolved architecture pause.

The numeric thresholds are defaults, not permission to ignore stronger earlier
evidence. One high-severity mechanism flaw may be sufficient when it disproves
the strategy premise or makes the gate unsafe for production.

## False-positive controls

Do not pause a campaign merely because the pull request is old, large, or has
many comments.

Before escalating:

- collapse duplicates and reply-only comments;
- exclude findings already present before the remediation mechanism;
- keep `INDEPENDENT` findings separate;
- verify that each counted finding is fresh against the reviewed head;
- distinguish a single incomplete patch from repeated abstraction failure;
- confirm that the findings challenge the same mechanism or strategy premise;
- record the evidence that links each finding to the mechanism.
- do not count three findings first observed in one patch-producing Review
  Session toward threshold 1; treat them as one incomplete patch unless a
  separate premise-invalidation or other condition above applies.

One hundred duplicate comments remain one defect class and zero additional
mechanism findings.

## Strategy reset

A campaign pause invalidates automatic authorization for another local patch.
Reopen the build-versus-buy decision and compare credible options:

1. reduce the requirement or restore the original bounded fix;
2. move the proof to the component that owns the runtime semantics;
3. use an established parser, protocol library, framework, or analyzer;
4. split the mechanism into a separately reviewed follow-up;
5. roll back the remediation and accept or explicitly document the original
   risk;
6. continue the direct implementation only with explicit approval of the new
   maintenance and semantic surface.

Record which premise changed and why the previous strategy memo is no longer
reusable.

## Paused behavior

While `NON_CONVERGING_REMEDIATION_STRATEGY` remains unresolved:

- do not modify code to address another mechanism-level finding;
- do not trigger `@codex review` or another automated reviewer;
- do not open a fresh Review Session as a budget reset;
- do not resolve threads only to make the pull request appear clean;
- do not use zero unresolved threads, mergeability, or green CI as completion;
- do not claim that a new head proves convergence.

No-code actions remain allowed when they preserve evidence: classify duplicate
feedback, explain the pause, queue independent findings, and report architecture
options.

## Resume rules

Only explicit user direction may resolve the campaign pause. Record the chosen
strategy, approved scope, dependency or contract authority, migration boundary,
and the campaign evidence accepted as residual risk.

Resume with a new Review Session only when:

- the current PR head and original goal are still valid;
- the strategy decision resolves every named campaign pause reason;
- the session inherits the full campaign record and cumulative churn;
- the new automatic patch budget is explicitly authorized or starts under a
  materially changed strategy rather than the same failed mechanism.

A strategy reset does not erase history. Later findings are evaluated against
the revised premise and the prior mechanism evidence remains informative.

## Required report

A campaign pause report must include:

```text
Campaign state: PAUSED
Pause reason: NON_CONVERGING_REMEDIATION_STRATEGY
Original PR goal: ...
Current remediation mechanism: ...
Finding-origin counts: ...
Mechanism-level evidence: ...
Invalidated strategy premise: ...
Current-head and session lineage: ...
Options: simplify | established dependency | owner-side proof | follow-up | rollback
Recommended option: ...
Decision required: ...
Further patch authorized: no
Automated reviewer trigger authorized: no
```

Keep Review convergence, QA verdict, and Delivery state independent in the same
report. A campaign pause is not a QA verdict, and a passing QA run does not
resolve the campaign pause.

## Acceptance examples

1. Three reviews expose namespace, inheritance, and control-flow holes in a new
   custom source analyzer. Classify all three as `MECHANISM_DEFECT`, invalidate
   the bounded-parser premise, and pause before another patch.
2. Two later comments repeat the same namespace reproducer. Cluster them as
   duplicates; they do not increase the mechanism count.
3. A separate typo appears during the pause. Classify it as `INDEPENDENT`; it
   does not justify or resolve the architecture pause.
4. A new session is requested after two patch rounds without a strategy change.
   Preserve campaign history and keep the campaign paused.
5. The user approves replacing the custom parser with an established parser.
   Record the new premise and open a bounded session under the revised strategy.
