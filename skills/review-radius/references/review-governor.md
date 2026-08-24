# Architecture-aware review governor

This is the normative policy for deciding whether a Review Session may continue
patching, must obtain an impact or architecture decision, or has converged. It
applies before every patch-producing session, after each post-implementation
rereview, and at the bounded recheck. The governor does not replace comment
validation, QA, delivery controls, or the Review Campaign record. It decides
patch authority from evidence; it does not turn review traffic into an
unbounded response loop.

Read this reference together with [Campaign convergence and strategy reset](review-campaign.md).
The campaign preserves lineage and taxonomy; this reference owns the decision
rules for another patch.

## Partial observability

Review is a partial-observability problem. A comment is an observation, not a
complete sample of the defect surface. Static search can miss aliases,
generated code, reflection, dependency injection, runtime registration,
data-driven dispatch, persistence state, and other dynamic behavior. A clean
review page, zero unresolved threads, a green check, or a new head is not proof
that the mechanism is correct or that the architecture remains bounded.

Every observation must be bound to a repository, session, base/head SHA, and
freshness state. Preserve uncertainty instead of treating an unavailable,
stale, inferred, or unsupported surface as safe. Unknown or high-risk coverage
gaps block the evidence needed to converge. A graph edge, reviewer count, or
comment count is context only; it is not a defect unit and never decides a
strategy by itself.

## Three planes of evidence

Keep the following planes separate. A locally successful patch does not settle
its impact or architecture.

<!-- markdownlint-disable MD013 -->

| Plane | Question | Required evidence |
| --- | --- | --- |
| **Patch** | Does the proposed change restore the violated invariant within the authorized local boundary? | Defect-class validation, negative/error/cleanup paths, sibling and caller audit, and verification obligations bound to the current head. |
| **Impact** | What reachable behavior, contract, state, owner, or runtime flow can change beyond the edited lines? | Impact delta, direct and transitive callers/consumers, persistence and compatibility effects, dynamic-surface checks, and the defect-frontier trend. |
| **Architecture** | Does the mechanism still fit the approved design and strategy premises? | Architecture baseline, ownership, public contracts, dependencies, semantic dimensions, risk comparison, authority for any boundary change, and an architecture verdict. |

<!-- markdownlint-enable MD013 -->

The Patch plane may support `CONTINUE_LOCAL` only when the Impact and
Architecture planes do not contain a stronger signal. Impact review is not
permission to expand the boundary. Architecture approval for an expansion
requires explicit authority, a recorded rationale, and new obligations.

## Architecture Context Packet

Construct an **Architecture Context Packet** for the current session and
current head. Rebind it whenever the head, approved boundary, strategy premise,
risk, or material architecture evidence changes. Earlier packets remain
lineage evidence but cannot prove the current head.

Record at least:

<!-- markdownlint-disable MD013 -->

| Field | Contents |
| --- | --- |
| Base/head SHA | The immutable comparison base and inspected head; include repository and session identity. |
| Original goal/non-goals | The product behavior requested and behavior explicitly excluded before review-driven work. |
| Approved boundary | Authorized repository surface, behavior, public-contract, dependency, persistence, migration, and production limits. |
| Architecture baseline | Components, dependencies, public contracts, persistence, ownership, runtime flows, and dynamic gaps as understood at the bound head. |
| Mechanism/strategy premises | The mechanism selected, why it fits, its assumed semantic scope, ownership, risk, maintenance, and comparison premises. |
| Impact delta | What the proposed or completed patch changes relative to the baseline, including callers, consumers, state, contracts, runtime flows, and risk. |
| Defect frontier | The current set of distinct unresolved or unverified invariant/boundary obligations, each with its frontier identity, status, provenance, and risk. |
| Verification obligations | Focused tests, runtime observations, static inspections, independent reviews, gates, and architecture/impact checks required for this head and risk. |

<!-- markdownlint-enable MD013 -->

The packet is an evidence ledger, not a design document detached from source.
Record the search capabilities used, their freshness, unsupported or dynamic
surfaces, and the smallest evidence supporting each material conclusion. A
missing architecture baseline, an unknown high-risk flow, or an obligation
whose result is unavailable means the packet is insufficient; do not infer a
safe architecture from silence.

## Defect frontier identity and trends

The defect frontier is the set of distinct work or proof obligations still
open after duplicate clustering and defect-class analysis. Its identity is
exactly:

```text
(invariant_id, mechanism_id, boundary_id, obligation_id)
```

Comments, replies, duplicate clusters, files, line counts, and patch rounds are
not frontier identities. One observation can support several identities only
when separate invariants, mechanisms, boundaries, or verification obligations
are evidenced. Keep provenance and current-head freshness on every frontier
entry.

Compare equivalent packets and identities across heads. Use these qualitative
trends, rather than raw counts, to describe progress:

<!-- markdownlint-disable MD013 -->

| Trend | Meaning |
| --- | --- |
| `empty` | No unresolved, unclassified, or unverified frontier identity remains. |
| `shrinking` | Previously open identities are closed or proven, with no new identity or boundary introduced. |
| `stable` | The same material frontier remains open or the attempted patch changes no meaningful obligation. |
| `expanding` | A new distinct identity, reachable boundary, semantic dimension, or verification obligation appears. |
| `regressing` | A previously closed/proven identity reopens, or the current head breaks a previously accepted invariant. |

<!-- markdownlint-enable MD013 -->

A shrinking frontier is evidence of progress, not convergence. A stable,
expanding, or regressing frontier requires impact review unless a stronger
strategy or evidence signal in the decision table applies. Historical
comment/churn and finding-origin counts may explain a trend but cannot replace
identity, provenance, or current-head evidence.

## Architecture verdict

Every packet that is used for a convergence decision has one architecture
verdict:

<!-- markdownlint-disable MD013 -->

| Verdict | Meaning |
| --- | --- |
| `NOT_ASSESSED` | No current, snapshot-bound architecture assessment exists. |
| `LOCAL_SAFE` | The change remains within the approved boundary; its mechanism and risk fit the baseline and premises. |
| `APPROVED_EXPANSION` | A material boundary expansion is explicitly authorized, its architecture impact is recorded, and its new obligations are accepted. |
| `STRATEGY_REVIEW_REQUIRED` | The mechanism, ownership, premises, semantic scope, or risk needs an architecture/strategy decision before more patching. |
| `BLOCKED` | A required authority, architecture fact, or prerequisite is unavailable or disallowed, so the decision cannot proceed. |

<!-- markdownlint-enable MD013 -->

`NOT_ASSESSED` and `BLOCKED` cannot support convergence. `STRATEGY_REVIEW_REQUIRED`
requires a strategy decision, not a local patch. `APPROVED_EXPANSION` is not an
automatic authorization: it is valid only when the packet identifies the
authority and the resulting verification obligations.

## Executable signal projection

Before evaluating a packet, the session owner projects the current, head-bound
evidence into the evaluator's required signals. `architecture_verdict` is an
independent assessment from the architecture plane, and must be one of the
five verdicts above; it is not inferred from the frontier, coverage, or patch
outcome. `patch_required` is a required independent boolean (`true` or `false`)
from the patch plane. No architecture verdict determines it. Set it only when
an affected invariant or failed verification obligation requires a behavior or
code change. Reply-only, duplicate-classification, explanation, and other
no-code dispositions set it to `false`.

`obligations_blocked` is a required independent boolean from the verification
and authority planes. Set it to `true` when any mandatory obligation is
unavailable, disallowed, or cannot be completed with the evidence or authority
available for the current head. Set it to `false` when the required work is
available to perform; `obligations_complete` remains a separate completion
signal and may still be `false`. In particular, an incomplete but available
obligation on a shrinking frontier preserves bounded local continuation. A
blocked mandatory obligation never grants local, fuse, or impact authority.

An operational `out-of-scope` finding is not an acceptance example. When it is
confirmed, record and report the evidence immediately, set
`obligations_blocked: true`, and make that report evidence-only: it does not
authorize an edit or an automatically assigned follow-up. Acceptance examples
in a request do not by themselves set `obligations_blocked`.

The projection must include all three independent signals on every packet and
preserve uncertainty. `patch_required: false` alone is not proof of review
convergence, QA success, or delivery completion; those outcomes require their
own evidence. A locally plausible boundary or a shrinking frontier cannot be
used to replace a blocking or strategy verdict. The evaluator validates the
projection and applies the precedence table; it does not create an
architecture verdict from the other fields.

Projection consistency is part of the evidence contract. An acceptable
architecture verdict must agree with the projected boundary:

<!-- markdownlint-disable MD013 -->

| Architecture verdict | Required boundary |
| --- | --- |
| `LOCAL_SAFE` | `within` |
| `APPROVED_EXPANSION` | `approved_expansion` |

<!-- markdownlint-enable MD013 -->

The cross-pairs (`LOCAL_SAFE` with `approved_expansion`, or
`APPROVED_EXPANSION` with `within`) are contradictory evidence and return
`INSUFFICIENT_ARCHITECTURE_EVIDENCE`. This check runs after immediate strategy
signals: a stronger signal such as an `expanded` boundary still returns
`STRATEGY_RESET_REQUIRED`.

### No-code fallback

No-code work is not edit authority. If `patch_required` is `false` while any
frontier identity remains unresolved, or while an empty frontier still has
incomplete obligations or unacceptable current-head QA, the packet is
`INSUFFICIENT_ARCHITECTURE_EVIDENCE`. Obtain the missing evidence or classify
the work explicitly; do not continue locally and do not pause a nonexistent
patch fuse. Only an empty frontier with complete obligations, acceptable QA,
and `LOCAL_SAFE` or `APPROVED_EXPANSION` can converge without a patch.

This fallback also applies after fuse exhaustion: a no-code packet cannot be
converted into `AUTOMATION_FUSE_EXHAUSTED` or `CONTINUE_LOCAL` merely by
retaining the prior patch-round count.

## Immediate strategy signals

Treat any verified signal below as a strategy concern, not as another local
finding:

- an approved mechanism or comparison premise is invalidated;
- the proposed work expands the architecture boundary without approval;
- keeping the mechanism correct requires a new semantic dimension;
- the change raises the risk level beyond the approved strategy or obligations.

A stronger signal can override a weaker progress disposition. For example, a
small frontier cannot justify local patching after an invalidated premise.
When the signal is evidenced, the governor returns
`STRATEGY_RESET_REQUIRED`; the campaign may record the named campaign pause
`NON_CONVERGING_REMEDIATION_STRATEGY`. Do not manufacture the signal from a
large PR, an old session, or duplicate comments.

## Risk-adaptive triggers

Classify the highest applicable risk before selecting obligations. `R0` is
documentation or inert metadata; `R1` is localized low-impact implementation;
`R2` covers runtime behavior, persistence, UI, concurrency, security,
compatibility, or public-contract changes; `R3` covers release, migration,
destructive operation, production infrastructure, or unknown material scope.
Unknown scope resolves upward.

<!-- markdownlint-disable MD013 -->

| Risk | Trigger and minimum governor evidence |
| --- | --- |
| `R0` | Confirm the change is inert, inspect references and generated/packaged surfaces where applicable, and record a compact packet. A dynamic or runtime effect raises the risk. |
| `R1` | Inspect the changed invariant, direct callers/consumers, negative paths, and sibling implementations. `LOCAL_SAFE` requires a current architecture baseline and no material impact delta. |
| `R2` | Require impact and architecture review, current contract/state/ownership evidence, focused runtime or equivalent evidence, and independent validation for ambiguity, security, compatibility, concurrency, or regression-sensitive work. Unknown dynamic coverage blocks convergence. |
| `R3` | Require full packet review, explicit authority for boundary or production changes, owner-side/independent architecture review, and every release/migration/destructive obligation. Any unknown material surface or missing authority blocks evidence. |

<!-- markdownlint-enable MD013 -->

A transition to a higher risk level is itself an immediate strategy signal. A
risk label alone is not failure: it determines the depth of obligations and
whether an unknown surface is blocking. Traceknot remains the required QA
handoff for `R2` and `R3` under the Review Radius skill; its verdict is
independent of this governor's decision.

## Precedence-ordered decision table

Evaluate rows from top to bottom against the current packet, head, frontier,
risk, obligations, and QA. The first applicable row wins. Known strategy-reset
signals and the `STRATEGY_REVIEW_REQUIRED` architecture verdict are evaluated
before insufficient evidence, impact review, convergence, fuse exhaustion, or
local continuation. A blocked mandatory obligation is an evidence condition,
not an impact or local-progress condition. “Another patch is needed” means at
least one affected frontier identity or failed obligation requires a behavior
or code change, not merely a duplicate classification, reply, explanation, or
no-code disposition.

<!-- markdownlint-disable MD013 -->

| Precedence | Condition | Governor decision | Authority/effect |
| --- | --- | --- | --- |
| 1 | A verified immediate strategy signal exists: invalid premise, unapproved architecture boundary expansion, new semantic dimension, or higher risk; or the architecture verdict is `STRATEGY_REVIEW_REQUIRED`. | `STRATEGY_RESET_REQUIRED` | Pause before patching. Reopen the strategy and record the evidence; this may establish the campaign pause `NON_CONVERGING_REMEDIATION_STRATEGY`. |
| 2 | `obligations_blocked` is `true`; or architecture evidence is missing, stale, contradictory, or insufficient for the risk; an unknown or coverage gap prevents an impact or architecture conclusion; the architecture verdict is `NOT_ASSESSED` or `BLOCKED`; or a no-code packet still has unresolved work or incomplete/unacceptable empty-frontier obligations. | `INSUFFICIENT_ARCHITECTURE_EVIDENCE` | Pause the current session and obtain the missing evidence or authority. Do not treat the gap as safe or converged. A blocked obligation permits evidence-only reporting, never local, fuse, or impact authority. |
| 3 | The frontier trend is `stable`, `expanding`, or `regressing`, `obligations_blocked` is `false`, and no stronger condition above applies. | `IMPACT_REVIEW_REQUIRED` | Pause automatic local patching for an impact review. The review can narrow, approve, or escalate; it does not itself authorize expansion. |
| 4 | The frontier is `empty`, all verification obligations are complete, QA is acceptable for the current head, `obligations_blocked` is `false`, the architecture verdict is `LOCAL_SAFE` or `APPROVED_EXPANSION`, and `patch_required` is `false`. | `CONVERGED` | No further patch is authorized by the governor. Report review convergence, QA, and delivery independently. |
| 5 | `patch_required` is `true`, `obligations_blocked` is `false`, the frontier is locally actionable (`shrinking`), and the default automatic patch fuse is exhausted. | `AUTOMATION_FUSE_EXHAUSTED` | Pause automatic patching and request explicit direction or a new authorized budget. This is not evidence of convergence or strategy failure. |
| 6 | `patch_required` is `true`, `obligations_blocked` is `false`, the packet is current, architecture verdict is `LOCAL_SAFE` (or an already authorized `APPROVED_EXPANSION`), the frontier is `shrinking` or otherwise locally actionable, and the fuse remains available. | `CONTINUE_LOCAL` | A bounded local patch may proceed within the approved boundary. Recompute the packet and decision after the patch. |

<!-- markdownlint-enable MD013 -->

If no row can be established, use `INSUFFICIENT_ARCHITECTURE_EVIDENCE` rather
than guessing. `CONVERGED` is impossible while `obligations_blocked` is true,
`patch_required` is true, any unknown/high-risk coverage gap, unresolved
frontier identity, incomplete obligation, unacceptable QA, or unacceptable
architecture verdict remains.

## Automatic patch fuse

The default automation circuit breaker permits **two automatic patch rounds**
for a Review Session. A round is a behavior or code change followed by its
analysis, patch, verification, response, and bounded recheck. Duplicate
classification, duplicate-cluster maintenance, reply-only or explanation-only
responses, and other no-code dispositions do not consume a round.

The fuse is a safety limit, not an evidence model:

- exhausting it never proves convergence;
- exhausting it never proves `NON_CONVERGING_REMEDIATION_STRATEGY`;
- no automatic round three is authorized;
- a required patch after exhaustion returns `AUTOMATION_FUSE_EXHAUSTED`, even
  when the frontier is shrinking;
- an immediate strategy signal still takes precedence over the fuse;
- an explicit user decision may extend the budget, but the extension, scope,
  head, and obligations must be recorded and reevaluated through this governor.

A new Session ID does not reset the campaign's lineage, cumulative evidence,
strategy pause, or risk. It may receive a new explicitly authorized budget
only after session/campaign pause rules and the current packet permit it.

## Pause, resume, and state separation

A governor pause concerns patch authority. Keep it separate from QA and
Delivery state.

- **Current Review Session:** ordinary feedback requiring direction,
  `IMPACT_REVIEW_REQUIRED`, `INSUFFICIENT_ARCHITECTURE_EVIDENCE`,
  `AUTOMATION_FUSE_EXHAUSTED`, a stale head, a post-cutoff blocking arrival,
  or another named session condition sets the session `PAUSED`. The campaign
  may remain `OPEN`.
- **Review Campaign:** set the campaign `PAUSED` only for a named campaign-level
  strategy pause, normally `NON_CONVERGING_REMEDIATION_STRATEGY` after
  `STRATEGY_RESET_REQUIRED`. A new session is not a budget-reset mechanism.
  External inability to obtain a required prerequisite may make the campaign
  `BLOCKED`; intentional termination is `STOPPED`.
- **QA:** `NOT_RUN`, `PASS`, `PASS_WITH_ACCEPTED_RISK`, `FAIL`, `BLOCKED`, and
  `INCOMPLETE` remain independent. A passing gate does not clear a governor or
  campaign pause; a pause does not by itself make QA fail.
- **Delivery:** replies, reactions, resolutions, commits, and pushes remain
  independently authorized and reported. Inspection evidence never authorizes
  a GitHub write.

To resume, record the decision-maker, accepted evidence, approved boundary,
strategy premises, risk, architecture verdict, migration/dependency or public-
contract authority, and obligations. Re-read the current head and rebuild or
rebind the packet; evidence from an earlier head is informative but cannot
satisfy current-head obligations. Resolve the named session pause before
continuing that session. Resolve a campaign strategy pause only with explicit
user direction or the applicable owner authority, then open a bounded session
that inherits the full campaign history. Do not silently reuse a disproved
premise or erase frontier history.

## Inspection versus edit authority

Inspection answers what may be true; it does not authorize changing it. A
reviewer or tool may nominate a candidate, classify provenance, expose a
coverage gap, or recommend an architecture option. Only the approved scope,
explicit user/owner authority, and a `CONTINUE_LOCAL` governor decision can
authorize an automatic local patch. `IMPACT_REVIEW_REQUIRED`,
`STRATEGY_RESET_REQUIRED`, `INSUFFICIENT_ARCHITECTURE_EVIDENCE`, and
`AUTOMATION_FUSE_EXHAUSTED` prohibit automatic patching; `CONVERGED` ends it.

An `APPROVED_EXPANSION` verdict records that an authorized decision already
occurred; it does not let an inspector grant itself authority. New production
dependencies, public-contract changes, migrations, semantic dimensions,
architecture-boundary expansion, and higher-risk operations require the
specific authority required by the repository and user. GitHub reactions,
replies, resolutions, commits, and pushes are delivery actions governed by
separate authorization and head guards.

## Required governor report

Include the following compact evidence in every decision report:

<!-- markdownlint-disable MD013 -->
```text

Governor decision: CONTINUE_LOCAL | IMPACT_REVIEW_REQUIRED | STRATEGY_RESET_REQUIRED | INSUFFICIENT_ARCHITECTURE_EVIDENCE | AUTOMATION_FUSE_EXHAUSTED | CONVERGED
Architecture verdict: NOT_ASSESSED | LOCAL_SAFE | APPROVED_EXPANSION | STRATEGY_REVIEW_REQUIRED | BLOCKED
Patch required: true | false
Obligations blocked: true | false
Risk: R0 | R1 | R2 | R3
Repository/session and base/head SHA: ...
Original goal/non-goals and approved boundary: ...
Architecture baseline and mechanism/strategy premises: ...
Impact delta: ...
Defect frontier and trend: ...
Immediate strategy signal or coverage gap: ...
Verification obligations and current-head QA: ...
Automatic rounds used / fuse status: ...
Session state: OPEN | PAUSED | BLOCKED | CONVERGED
Campaign state and pause reason: OPEN | PAUSED | BLOCKED | CONVERGED | STOPPED / ...
Inspection evidence and provenance: ...
Edit authority and decision-maker: ...
Resume condition or next evidence required: ...

```

<!-- markdownlint-enable MD013 -->

Never report convergence from a count threshold, comment silence, a fresh
session, a green gate, or a new head alone. Convergence requires an `empty`
frontier, complete obligations, acceptable current-head QA, and an acceptable
architecture verdict.
