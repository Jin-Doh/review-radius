# Code-navigation tool-routing experiment

Date: 2026-08-04

## Decision

Adopt a capability-routed, compact evidence pipeline for structurally or
semantically related-code audits:

```text
AST roots -> bounded Graphify candidates -> LSP verification/delta
          -> compact provenance ledger -> source/runtime classification
```

This is a routing rule, not a requirement to invoke every tool. Text search
remains the default for literal and configuration questions. Missing, stale, or
unsupported capabilities fall back to source search and inspection with an
explicit coverage gap.

## Test basis and hypothesis

- `EXP-BASIS-001`: a review comment is evidence of a defect class, so discovery
  must find syntactic copies, semantic aliases, and bounded transitive callers.
- `EXP-BASIS-002`: navigation evidence must preserve enough provenance to
  classify candidates without loading all raw tool output into the model.
- `EXP-BASIS-003`: no single static tool is assumed complete across aliases,
  wrappers, inferred edges, and dynamic behavior.

Hypothesis: routing AST, a code graph, and LSP by their strengths can retain the
fixture's candidate recall and precision while presenting fewer proxy tokens
than raw text-search output or naive tool-output accumulation.

## Fixture and ground truth

The synthetic TypeScript fixture models a case-sensitive identity invariant.
It contains direct calls, an aliased import, a re-export, a transitive wrapper
caller, a structurally equivalent helper, and safe decoys. Ground truth contains
eight affected candidates. Discovery code does not read the ground-truth file;
the benchmark loads it only after discovery for scoring.

This synthetic boundary deliberately isolates navigation behavior. It does not
represent repository-scale indexing cost, unsupported languages, reflection,
runtime registration, or stale-index behavior.

## Compared methods

- `rg+raw`: review-anchor text search and modeled full matched-file reads.
- `rg+ast`: text search plus structural AST matches.
- `rg+ast+lsp`: structural discovery plus language-server relationships.
- `graphify-query`: bounded direct and transitive graph query.
- `graphify+ast+lsp`: naive accumulation of all raw outputs.
- `routed-compact`: AST roots, graph candidates, LSP-only delta, and a normalized
  provenance ledger.

Token proxy is `ceil((tool output bytes + modeled source-read bytes) / 4)`. It is
a relative fixture metric, not a billed-token measurement.

## Observed results

The candidate sets below were stable across three repetitions. Query timings
varied and are not used as a correctness conclusion.

| Method | Recall | Precision | Token proxy | Missed |
| --- | ---: | ---: | ---: | --- |
| `rg+raw` | 75.0% | 75.0% | 1694 | `readAuditLog`, `transferAccount` |
| `rg+ast` | 87.5% | 87.5% | 1988 | `readAuditLog` |
| `rg+ast+lsp` | 100.0% | 100.0% | 2191 | None |
| `graphify-query` | 87.5% | 100.0% | 589 | `rotateCredential` |
| naive `graphify+ast+lsp` | 100.0% | 100.0% | 2480 | None |
| `routed-compact` | 100.0% | 100.0% | 451 | None |

Observed facts:

- Graphify found the transitive wrapper path but missed the aliased call
  `rotateCredential`.
- LSP supplied that semantic alias edge.
- AST supplied the structurally equivalent helper.
- Naively concatenating tool outputs cost more proxy tokens than `rg+raw`.
- The compact ledger retained full fixture recall and precision with 73.38%
  fewer proxy tokens than `rg+raw`.

Candidate sets were stable, while timings varied. An initial rerun revealed that
ripgrep embeds timing and self-sized byte fields in its JSON summary, making the
raw byte proxy vary between otherwise equivalent runs. The benchmark now removes
those nondeterministic fields and canonicalizes the remaining JSON before
scoring. Two consecutive runs produced identical non-timing result data. The
proxy should still be interpreted directionally; `latest.json` is the
authoritative result snapshot.

The inference supported by these observations is that tool selection and output
normalization matter more than merely adding tools.

## Reproduction and provenance

From the repository root:

```sh
python3 experiments/tool-routing/run_benchmark.py
```

The recorded run used Python 3.14.6, ast-grep 0.45.0, TypeScript language server
5.3.0, and `graphifyy==0.9.32` through `uvx`. Graphify is pinned for the run and
is not installed globally. The release declares the Apache License 2.0; its
upstream license and attribution are recorded in
[the third-party notices](../../THIRD_PARTY_NOTICES.md). Machine-readable
evidence is in
[`latest.json`](../../experiments/tool-routing/results/latest.json), and the
generated detailed report is in
[`REPORT.md`](../../experiments/tool-routing/results/REPORT.md).

## Limits and next experiment

This experiment establishes the mechanism only on a small synthetic fixture.
It does not establish production-scale latency or token savings, whole-repository
recall, language coverage, model compliance with the skill, or runtime behavior.

A real-repository comparison should add:

- clean, incremental, and intentionally stale graph/index states;
- supported and unsupported language partitions;
- aliases, re-exports, dynamic dispatch, reflection, and generated code;
- setup/amortization cost and compact-ledger construction cost;
- blinded candidate scoring and an independent review of false negatives;
- an agent-level scenario comparing the old and revised skill behavior.
