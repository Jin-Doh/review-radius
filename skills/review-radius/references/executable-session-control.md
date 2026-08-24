# Executable session control

Use the bundled controller when a Review Radius session may produce a patch or
request another automated review. The controller turns the architecture-aware
governor from advisory prose into a head-bound action gate.

The agent still performs review analysis and projects evidence. The controller
owns the state that must not be reconstructed from model memory:

- session identity, repository, PR, base SHA, initial head, and current head;
- immutable feedback cutoff and non-resetting recheck deadline;
- initial thread IDs and post-cutoff deferred feedback;
- automatic patch rounds and the current patch budget;
- named pause reasons, campaign/session state, and scope fingerprint;
- the current governor signals, decision, and pending action authorization;
- automated-review requests already made for a head.

Do not manually lower `patch_rounds`, raise `automatic_patch_budget`, change the
current head, move deferred feedback into the current batch, or clear a pause.
Use the controller commands so those transitions are validated and recorded.

## State location

Keep the working state in the target repository, normally outside committed
source:

```text
.review-radius/pr-<number>/session.json
```

The state is an operational ledger, not a source artifact. Add
`.review-radius/` to the target repository's local or committed ignore policy
when appropriate. Preserve the file until the Review Campaign report has
captured the session lineage.

## Initialize the frozen session

Create the state before reading or changing code. The cutoff and deadline must
be server-comparable timestamps; the deadline must be at least 90 seconds after
the cutoff.

```bash
python3 <skill>/scripts/session_control.py init \
  --state .review-radius/pr-79/session.json \
  --repository sugarcube-networks/sugarcube-platform \
  --pr 79 \
  --base-sha "$BASE_SHA" \
  --head-sha "$HEAD_SHA" \
  --cutoff "$CUTOFF" \
  --deadline "$DEADLINE" \
  --scope-fingerprint "$SCOPE_FINGERPRINT" \
  --thread-id PRRT_example
```

Initialization fails rather than replacing an existing state file. Open a new
path for a successor session; do not overwrite the prior lineage.

## Project evidence

Write the current Architecture Context Packet projection to a JSON file using
the same signal contract as `evaluate_governor.py`, except that
`patch_rounds` and `automatic_patch_budget` may be omitted. Those two fields are
controller-owned and cannot be reset by a projection.

```json
{
  "architecture_verdict": "LOCAL_SAFE",
  "boundary": "within",
  "premise": "valid",
  "semantic_delta": "expected",
  "frontier": "shrinking",
  "coverage": "sufficient",
  "risk": "same_or_lower",
  "patch_required": true,
  "obligations_complete": false,
  "obligations_blocked": false,
  "qa_acceptable": false
}
```

Bind and evaluate it against the observed remote head:

```bash
python3 <skill>/scripts/session_control.py project \
  --state .review-radius/pr-79/session.json \
  --signals /tmp/review-radius-signals.json \
  --head "$HEAD_SHA"
```

A head mismatch is an error. Fetch and rebind the changed head before taking an
action.

## Guard every patch

Immediately before editing behavior or code, request a patch authorization:

```bash
python3 <skill>/scripts/session_control.py guard \
  --state .review-radius/pr-79/session.json \
  --action patch \
  --head "$HEAD_SHA"
```

A patch is authorized only when all of these are true:

- session and campaign state are `OPEN`;
- no named pause reason remains;
- the supplied head equals the persisted current head;
- the fresh deterministic decision is exactly `CONTINUE_LOCAL`.

The command exits `0` and returns a single-use authorization token when allowed.
It exits `3` with `allowed:false` when policy denies the action. Any nonzero
result means **do not patch**.

After the patch is committed or otherwise has an immutable new head, consume
the token and advance the session:

```bash
python3 <skill>/scripts/session_control.py record-patch \
  --state .review-radius/pr-79/session.json \
  --authorization "$TOKEN" \
  --from-head "$OLD_HEAD" \
  --to-head "$NEW_HEAD"
```

This transition increments the automatic patch round, changes the bound head,
consumes the token, and invalidates snapshot-bound architecture and QA evidence.
Project fresh evidence for the new head before another action.

A third required patch under the default budget produces
`AUTOMATION_FUSE_EXHAUSTED`; a new Session ID or signal file cannot reset it.
An explicit user decision may extend, but never reset, the budget:

```bash
python3 <skill>/scripts/session_control.py extend-fuse \
  --state .review-radius/pr-79/session.json \
  --head "$HEAD_SHA" \
  --additional-rounds 1 \
  --direction "Authorize one additional bounded patch round for this head and scope."
```

The command works only while the fresh decision is
`AUTOMATION_FUSE_EXHAUSTED`.

## Guard automated review retriggers

Do not treat a bot review as a queue consumer. Another automated review may be
requested only after the current head is `CONVERGED`, with complete obligations
and acceptable QA, and only once per head:

```bash
python3 <skill>/scripts/session_control.py guard \
  --state .review-radius/pr-79/session.json \
  --action request-review \
  --head "$HEAD_SHA"

python3 <skill>/scripts/session_control.py record-review-request \
  --state .review-radius/pr-79/session.json \
  --authorization "$TOKEN" \
  --head "$HEAD_SHA"
```

A repeated request for the same head is denied. New feedback is admitted only
by the frozen-cutoff rules, never merely because a reviewer emitted it.

## Defer post-cutoff feedback

Persist feedback created strictly after the cutoff outside the current batch:

```bash
python3 <skill>/scripts/session_control.py defer-feedback \
  --state .review-radius/pr-79/session.json \
  --head "$HEAD_SHA" \
  --thread-id PRRT_late \
  --created-at "$CREATED_AT" \
  --classification later-nonblocking \
  --reason "Editorial feedback for a future session."
```

Use `post-cutoff-blocking` for a blocking late arrival. That classification
records `admitted_to_current_session:false`, creates a named pause, and makes
patch authorization fail until recorded explicit user direction resolves the
pause or selects a successor session.

The field is named `deferred_feedback`, not a work queue. The current session
must not consume it.

## Named pauses and resume

Record a pause when direction, authority, impact review, strategy review, or an
external prerequisite is required:

```bash
python3 <skill>/scripts/session_control.py pause \
  --state .review-radius/pr-79/session.json \
  --head "$HEAD_SHA" \
  --pause-id strategy-choice \
  --code STRATEGY_RESET_REQUIRED \
  --detail "The approved mechanism premise is invalid."
```

Resolve one pause only with recorded explicit direction and the unchanged head
and scope fingerprint:

```bash
python3 <skill>/scripts/session_control.py resume \
  --state .review-radius/pr-79/session.json \
  --head "$HEAD_SHA" \
  --pause-id strategy-choice \
  --scope-fingerprint "$SCOPE_FINGERPRINT" \
  --direction "Use the approved replacement strategy."
```

A changed head or scope requires a successor session rather than silently
reopening the old one.

## Inspect and report

```bash
python3 <skill>/scripts/session_control.py inspect \
  --state .review-radius/pr-79/session.json \
  --full
```

Include the persisted current head, patch rounds/budget, deferred-feedback
count, named pauses, deterministic decision, architecture verdict, independent
`patch_required` and `obligations_blocked` values, QA, and delivery state in the
final report.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Command succeeded; a guarded action was allowed when applicable. |
| `2` | Invalid input, stale head, malformed signals, or invalid state. |
| `3` | The requested action was validly evaluated and denied by policy. |

Never reinterpret exit `2` or `3` as permission to continue. Repair the state
or evidence, or stop for the required direction.
