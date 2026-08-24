# Campaign convergence and strategy reset

Use this reference when a pull request has more than one review/fix session,
when feedback is described as recurring or non-converging, or when another
patch would be justified mainly by code introduced during earlier review
responses.

The normative patch decision is defined by [Architecture-aware review governor](review-governor.md).
This campaign reference preserves pull-request lineage, finding taxonomy,
pause ownership, and strategy history; it MUST NOT invent a separate count
threshold or override the governor's precedence-ordered decision table.

## Purpose

A Review Session bounds one feedback batch. A Review Campaign preserves the
history of the entire pull request across sessions so that opening a fresh
session cannot erase accumulated evidence, reset an unresolved strategy pause,
or make an old mechanism appear new.

The campaign record answers the historical question that supports the governor:

> Does current evidence remain the original defect class, or does it challenge
the remediation mechanism, its premises, or its architecture boundary?

That classification is evidence for the Architecture Context Packet and defect
frontier. It is not, by itself, authorization for another local patch.

## Campaign record

Reconstruct the record from durable pull-request evidence whenever a prior
session record is unavailable. Prefer immutable GitHub timestamps and commit
SHAs over conversational summaries. Bind every observation to its session and
inspected head.

Record:

<!-- markdownlint-disable MD013 -->

| Field | Purpose |
| --- | --- |
| Repository and PR | Bind the campaign to one review lineage. |
| Original base, head, title, and goal | Preserve the requested product change before review-driven expansion. |
| Original non-goals and intended safe boundary | State the repository, behavior, contract, dependency, persistence, migration, and production limits originally authorized. |
| Session lineage | Preserve immutable prior Session IDs, each session's frozen head/snapshot and cutoff/cursor evidence, separate QA verdicts and delivery states, patch rounds, pauses, and outcomes across successor Review Sessions. |
| Patch-producing reviews | Distinguish review observations that caused behavior changes from duplicate or reply-only traffic. |
| Defect classes and frontier identities | Preserve root-cause grouping and `(invariant_id, mechanism_id, boundary_id, obligation_id)` lineage across heads. |
| Finding origins | Separate product defects from remediation-mechanism defects. |
| Strategy memo and premises | Preserve why direct implementation, reuse, dependency, owner-side proof, or follow-up was chosen and which premises remain valid. |
| Architecture Context Packets | Link the snapshot-bound architecture baseline, impact delta, risk, obligations, independent `patch_required` boolean, independent `obligations_blocked` boolean, per-obligation `complete`/`incomplete`/`blocked` status, verdict, and coverage gaps used by the governor. |
| Verification-obligation lineage | Preserve each head's required-obligation set and status. `obligations_blocked: true` means a required capability, prerequisite, or evidence artifact is unavailable or inaccessible; `false` means the obligation is available, even when its separate status is `incomplete`. |
| Semantic surface growth | Describe newly implemented language, protocol, parser, dispatch, persistence, concurrency, migration, or other semantic dimensions. |
| Campaign convergence | `OPEN`, `CONVERGED`, `PAUSED`, `BLOCKED`, or `STOPPED`. `CONVERGED` means the original PR goal and safe boundary are complete, the governor decision is `CONVERGED`, the architecture verdict is `LOCAL_SAFE` or explicitly authorized `APPROVED_EXPANSION`, the independent patch-plane fact is `patch_required: false`, the independent verification-plane fact is `obligations_blocked: false`, every required obligation is complete, and no unresolved campaign pause reason remains; delivery state is reported separately and does not gate campaign convergence; `STOPPED` means the campaign was intentionally ended without convergence. |

| Campaign pause reasons | Name the strategy or external decision required before another patch or reviewer trigger. |

<!-- markdownlint-enable MD013 -->

A campaign's `obligations_blocked` status is a packet/governor evidence field,
not a replacement for the campaign lifecycle state. A packet with
`obligations_blocked: true` requires `INSUFFICIENT_ARCHITECTURE_EVIDENCE` and
cannot authorize `CONTINUE_LOCAL` or `AUTOMATION_FUSE_EXHAUSTED`; a session may
therefore be `PAUSED` while the campaign remains `OPEN`. An available but
unfinished obligation remains `obligations_blocked: false` with an independent
`incomplete` status and cannot be reported as complete or converged.

A Session ID may change. The campaign identity does not change while the pull
request and its original goal remain the same. Ordinary Review Session pauses
do not mutate the campaign state. The campaign becomes `PAUSED` only for a
named campaign-level strategy pause; a session may be `PAUSED` while the
campaign remains `OPEN`.

When a successor Review Session is created, the campaign lineage MUST append
a new Session ID without rewriting the prior session record. It MUST preserve
the prior immutable Session ID, frozen head/snapshot, cutoff and cursor
evidence, QA verdict, and delivery state as historical fields. The successor
Review Session MUST have its own current fields—current Session ID, current
head/snapshot, current cutoff/cursor, current QA verdict, and current delivery
state—recorded separately. New evidence or state transitions MUST NOT overwrite
the prior session's values or be inherited as the successor's current evidence.

## Finding-origin taxonomy

Classify every fresh actionable finding with exactly one primary origin. Add a
secondary note when evidence is mixed. A finding is a lineage record, not a
numeric convergence unit.

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
broken by a prior patch in the campaign. Preserve the causal patch and current
head in the lineage even when the immediate correction is small.

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
findings to claim that the mechanism is non-converging. Queue or follow them
under normal scope rules.

## Mechanism identity and lineage

Group findings by the mechanism whose correctness they challenge, not only by
file or function. Examples:

- `custom PHP source analyzer`
- `home-grown JWT parser`
- `release provenance fallback resolver`
- `retry state machine`
- `schema migration compatibility layer`

A mechanism may span several helpers and defect classes. Renaming or splitting
a helper does not reset its campaign history. Preserve prior mechanism
identity, strategy premises, architecture packets, frontier identities, and
heads when comparing a revised implementation.

## Governor handoff

Apply [Architecture-aware review governor](review-governor.md) before every
patch-producing session and again after the post-implementation rereview. The
governor consumes the campaign's lineage and current Architecture Context
Packet, including the required independent `obligations_blocked: true|false`
input, then owns the decision whether a patch may proceed. The campaign MUST
not substitute comment volume, finding counts, churn, session age, or a new
Session ID for that decision.

The governor's decisions are:

- `CONTINUE_LOCAL`: a bounded local patch is authorized within the current
  approved boundary only when obligations are not blocked;
- `IMPACT_REVIEW_REQUIRED`: automatic local patching pauses for impact review;
- `STRATEGY_RESET_REQUIRED`: a premise, mechanism, boundary, semantic
  dimension, ownership, or risk decision must be reopened;
- `INSUFFICIENT_ARCHITECTURE_EVIDENCE`: current evidence cannot establish a
  safe architecture or impact conclusion; `obligations_blocked: true` is a
  direct insufficient-evidence signal evaluated before impact review, fuse
  exhaustion, or local continuation;
- `AUTOMATION_FUSE_EXHAUSTED`: another patch is needed after the default
  automatic patch fuse and obligations are not blocked;
- `CONVERGED`: the frontier is empty, obligations are complete with
  `obligations_blocked: false`, current-head QA is acceptable, and the
  architecture verdict is `LOCAL_SAFE` or explicitly authorized
  `APPROVED_EXPANSION`; this governor decision is required before the campaign
  can be `CONVERGED`.

An available but unfinished obligation remains distinct from a blocked
obligation: report `obligations_blocked: false` with its independent
`incomplete` status. It prevents convergence but does not, by itself, prohibit
a shrinking local patch or consume the fuse.

A stable, expanding, or regressing defect frontier is an impact-review signal.
An invalid premise, unapproved architecture-boundary expansion, new semantic
dimension, or higher risk is a strategy signal. Unknown or high-risk coverage
gaps block evidence. Follow the governor's precedence order when more than one
condition is present.

The default automatic patch fuse is **two patch rounds**. It is a circuit
breaker only: exhaustion is `AUTOMATION_FUSE_EXHAUSTED`, never evidence of
convergence and never proof of `NON_CONVERGING_REMEDIATION_STRATEGY`. A fresh
session does not silently reset the campaign or authorize a third automatic
round. Duplicate, reply-only, explanation-only, and other no-code dispositions
do not consume the fuse.

This reference intentionally defines no standalone numeric mechanism or
session threshold. Historical counts and churn remain useful context in the
campaign record, for example to show that review attention is increasing or
that a mechanism has repeatedly required examination, but they never make a
strategy decision automatically. The current packet, frontier identity and
trend, risk-adaptive obligations, architecture verdict, and explicit authority
control.

When `STRATEGY_RESET_REQUIRED` is supported by evidence that the remediation
mechanism or its premises are the source of repeated correctness failures, set
the named campaign pause reason to
`NON_CONVERGING_REMEDIATION_STRATEGY`. Do not use that reason for an exhausted
automation fuse alone. A single premise-invalidating or high-risk signal may
be sufficient; repeated observations with the same root cause should be
clustered and recorded as lineage rather than counted as separate defects.

## False-positive controls and evidence quality

Do not pause a campaign merely because the pull request is old, large, or has
many comments. Before recording a strategy pause:

- collapse duplicate and reply-only feedback into the relevant defect class;
- preserve every thread ID and disposition without making each thread a new
  frontier identity;
- distinguish observations that predate the remediation from regressions
  caused by it;
- keep `INDEPENDENT` findings separate;
- bind each material finding and frontier identity to the reviewed head;
- record the mechanism, invariant, boundary, and obligation it challenges;
- distinguish a single incomplete patch from a changed strategy premise;
- distinguish an unavailable or inaccessible required obligation
  (`obligations_blocked: true`) from an available but unfinished obligation
  (`obligations_blocked: false` with `incomplete`);
- record static-tool limitations, dynamic behavior, unsupported languages, and
  stale or inferred edges as coverage gaps;
- treat unknown or high-risk gaps as blockers, not as evidence of safety;
- do not infer convergence from zero unresolved threads, mergeability, green
  CI, silence, a fresh session, or a new head.

Historical count/churn can be included as a descriptive trend, but comments,
files, lines, sessions, and rounds are not defect-frontier identities.

## Strategy reset

A campaign pause invalidates automatic authorization for another local patch.
Reopen the strategy and update the Architecture Context Packet. Compare
credible options such as:

1. reduce the requirement or restore the original bounded fix;
2. move proof or behavior to the component that owns the runtime semantics;
3. use an established parser, protocol library, framework, or analyzer;
4. split the mechanism into a separately reviewed follow-up;
5. roll back the remediation and accept or explicitly document the original
   risk;
6. continue the direct implementation only with explicit approval of the new
   maintenance and semantic surface.

Record which premise changed, which authority approved the new boundary or
risk, and why the previous strategy memo is no longer reusable. The governor
must reassess the current head and obligations under the revised premise.

## Paused behavior

While `NON_CONVERGING_REMEDIATION_STRATEGY` remains unresolved:

- do not modify code to address another mechanism-level finding;
- do not trigger `@codex review` or another automated reviewer;
- do not open a fresh Review Session as a budget reset;
- do not resolve threads only to make the pull request appear clean;
- do not use zero unresolved threads, mergeability, or green CI as completion;
- do not claim that a new head proves convergence;
- do classify duplicates, reply-only feedback, independent findings, and
  evidence gaps so the campaign record remains complete;
- do report architecture options and the exact decision required.

A session-level `IMPACT_REVIEW_REQUIRED`,
`INSUFFICIENT_ARCHITECTURE_EVIDENCE`, or `AUTOMATION_FUSE_EXHAUSTED` pause may
leave the campaign `OPEN`. A blocked obligation specifically requires
`INSUFFICIENT_ARCHITECTURE_EVIDENCE` and cannot be represented as fuse
exhaustion or local continuation; an available but incomplete obligation keeps
`obligations_blocked: false` and its separate `INCOMPLETE` status. QA and
Delivery remain independent outcomes.

## Resume rules

Only explicit user direction or the applicable owner authority may resolve a
campaign strategy pause. Record the chosen strategy, approved scope,
dependency or contract authority, migration boundary, risk, architecture
verdict, verification obligations, and any residual risk accepted.

Resume with a bounded Review Session only when:

- the current PR head and original goal remain valid, or the changed goal is
  explicitly recorded;
- the strategy decision resolves every named campaign pause reason;
- the session inherits the full campaign record and cumulative frontier and
  mechanism lineage;
- the current Architecture Context Packet is rebuilt or rebound to the head;
- the new automatic budget is explicitly authorized, if an extension is
  needed, and is evaluated by the governor rather than assumed from the new
  Session ID.

A strategy reset does not erase history. Later findings are evaluated against
the revised premises, while prior mechanism evidence remains informative.
An automation-fuse extension does not imply that the strategy failed or that
it succeeded; it only permits the governor to evaluate an explicitly
re-authorized next round.

## Required campaign report

A campaign report must include the governor result and separate session, QA,
and delivery outcomes. Every operational governor summary MUST include
`patch_required` as an explicit independent boolean from the patch plane and
`obligations_blocked` as an explicit independent boolean from the
verification plane; no architecture verdict determines either one.
`obligations_blocked: true` MUST be reported as
`INSUFFICIENT_ARCHITECTURE_EVIDENCE` and MUST NOT be reported as
`CONTINUE_LOCAL` or `AUTOMATION_FUSE_EXHAUSTED`. `obligations_blocked: false`
does not mean obligations are complete: report each obligation's separate
`complete`, `incomplete`, or `blocked` status. `patch_required: false` alone
MUST NOT be treated as proof of review convergence, successful or acceptable
QA, or delivery completion.
Its `Campaign state: CONVERGED` entry MUST satisfy the campaign convergence
gate above; a non-`CONVERGED` governor decision, an architecture verdict other
than `LOCAL_SAFE` or explicitly authorized `APPROVED_EXPANSION`,
`obligations_blocked: true`, an incomplete obligation, or `patch_required: true`
cannot be reported as campaign convergence. Delivery state MUST remain
separately reported and MUST NOT be treated as a campaign-state condition.
Report the governor decision, architecture verdict, both independent booleans,
and obligation statuses separately rather than inferring campaign convergence
from any one field alone.

```text
Campaign state: OPEN | PAUSED | BLOCKED | CONVERGED | STOPPED
Campaign pause reason: ...
Governor decision: ...
Architecture verdict: ...
patch_required: true | false
obligations_blocked: true | false
Original PR goal/non-goals and approved boundary: ...
Current remediation mechanism and strategy premises: ...
Finding-origin lineage: ...
Defect frontier identities and trend: ...
Architecture Context Packet and current head: ...
Impact delta and coverage gaps: ...
Historical count/churn context (non-decisional): ...
Verification obligations, obligation statuses, and QA verdict: ...
Session lineage (prior immutable Session IDs, frozen heads/snapshots,
cutoff/cursor evidence, separate QA verdicts and delivery states): ...
Options: simplify | established dependency | owner-side proof | follow-up | rollback
Recommended option: ...
Decision required: ...
Further patch authorized: yes | no | only within approved boundary
Automated reviewer trigger authorized: yes | no
Review convergence: ...
Delivery state: ...
```

For a campaign strategy pause, also identify the invalidated premise or
immediate strategy signal, the evidence snapshot and session lineage, the
migration/rollback boundary, and the exact user decision required. A campaign
pause is not a QA verdict, and passing QA does not resolve it.

## Examples

1. Namespace, inheritance, and control-flow observations expose distinct
   correctness holes in a new custom source analyzer. Classify their origins
   and frontier identities, record the invalidated bounded-parser premise, and
   let the governor return `STRATEGY_RESET_REQUIRED` before another local
   patch.
2. Later comments repeat the same namespace reproducer. Cluster them as
   duplicates; retain thread provenance, but do not create new frontier
   identities or a new strategy signal.
3. A separate typo appears during the pause. Classify it as `INDEPENDENT`; it
   does not justify or resolve the architecture pause.
4. A second automatic patch round leaves a non-empty frontier. The fuse may
   return `AUTOMATION_FUSE_EXHAUSTED`; do not label the mechanism
   `NON_CONVERGING_REMEDIATION_STRATEGY` without separate architecture
   evidence.
5. The user approves replacing the custom parser with an established parser.
   Record the new premise, authority, boundary, obligations, and verdict, then
   open a bounded session under the revised strategy.
