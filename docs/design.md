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
public contract, requires migration or production authority, conflicts with
another requirement, or makes the PR substantially harder to review safely.

This replaces line-level minimalism with cause-level minimalism.

## Two-pass review

Run two distinct reviews:

1. Before implementation, use the review lens to find the existing blast
   radius.
2. After implementation, reread the resulting diff through the same lens to
   detect incomplete fixes, new asymmetry, missed failure paths, and tests that
   assert only the example rather than the invariant.

Passing the repository's existing test suite does not replace either pass.

## Completion contract

Declare the review response complete only when:

- every actionable thread has a disposition;
- every credible in-scope candidate has been classified;
- every `affected` candidate has been fixed or explicitly blocked;
- every `out-of-scope` defect has a visible follow-up disposition;
- regression evidence protects the invariant and canonical gates pass;
- replies and thread resolution match the actual implementation state;
- the final wait and recheck finds no new actionable review or failing PR gate.

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
