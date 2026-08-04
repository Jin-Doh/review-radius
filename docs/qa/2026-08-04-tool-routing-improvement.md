<!-- markdownlint-disable MD013 -->

# Traceknot completion report: tool-routing improvement

Date: 2026-08-04

## 1. Target snapshot and change scope

The verification target is the change from base commit `8761007` on branch
`feat/tool-routing-improvement`. It adds the durable experiment record, changes
the installable `review-response` workflow, adds a progressively loaded
navigation reference, refreshes benchmark evidence, and adds contract tests.

No GitHub, production, dependency, or global skill installation write is in
scope.

## 2. Test basis and acceptance criteria

| Basis | Source | Acceptance criterion |
| --- | --- | --- |
| `BASIS-001` | User request | Preserve the comparison experiment as a reproducible document. |
| `BASIS-002` | User request and existing design | Improve related-code discovery from the experiment without making every tool mandatory. |
| `BASIS-003` | Recorded benchmark | Keep observed results, provenance, and limitations consistent with machine-readable evidence. |
| `BASIS-004` | Installable skill contract | The repository remains discoverable by `npx skills`, and the operational reference is reachable from `SKILL.md`. |
| `BASIS-005` | Traceknot | Separate observed evidence, inference, untested scope, defects, and final verdict. |

## 3. Risk-discovery execution profile

The discovery profile was `single-context`. The runtime supplied command
execution, artifact capture in the worktree, and snapshot binding through Git,
but no independent read-only reviewer was invoked. Model self-review is not
claimed as independent evidence. Deterministic test, lint, benchmark, and skill
discovery processes provide the verification boundary for machine-checkable
obligations.

The universal cheap trigger scan produced:

- Protocol: LSP initialization, synchronization, and capability advertisement
  can change the meaning of an empty result.
- Performance: the benchmark makes a relative token-proxy claim.
- Data realism: the evidence uses a small synthetic fixture.
- Identity: the fixture's defect lens is a case-sensitive identity invariant.

Predicates were `scopeUnknown=true`, `materialTrigger=true`,
`syntheticBoundaryBypass=true`, and `recurringDefectClusterOverlap=true`. The
last predicate reflects the reported recurring pattern of addressing only the
reviewed line. These predicates required a bounded challenge.

## 4. Discovery findings and capability limits

The current-context challenge covered stale indexes, unsupported languages,
aliases, inferred graph edges, dynamic dispatch, raw-output accumulation, and
model compliance.

| Finding | Taxonomy | Result |
| --- | --- | --- |
| `FIND-001` | `COVERAGE_GAP` | Real-repository scale, dynamic dispatch, and agent-level old/new behavior remain untested. Kept as explicit non-production scope. |
| `FIND-002` | `SOURCE_CANDIDATE` | Ripgrep timing fields made the byte proxy vary on regeneration. The adapter now removes nondeterministic fields, a contract test covers normalization, and two consecutive runs produced identical non-timing data. Closed. |
| `FIND-003` | `CONFIRMED_DEFECT` | Initial Markdown validation found 10 formatting errors. Corrected and the same validator passed with zero errors. Closed. |
| `FIND-004` | `SOURCE_CANDIDATE` | Graphify missed the aliased caller `rotateCredential`. Promoted into the LSP semantic-delta obligation and confirmed by the benchmark. Closed. |

No browser or production runtime was required. No language-specific published
prose analyzer is configured in this repository, so Traceknot's optional prose
quality obligation was not selected; Markdown lint is not represented as a
substitute authorship or style detector.

## 5. Product risks

| Risk | Initial | Mitigation and residual |
| --- | --- | --- |
| `RISK-001` public workflow misses related code when a capability is stale or absent | `R2` | Freshness snapshot, fallback, and coverage-gap contract; residual `R1` generalizability risk. |
| `RISK-002` inferred graph edges are treated as confirmed defects | `R2` | Exact provenance labels and explicit source/LSP/runtime confirmation boundary; no material residual found. |
| `RISK-003` raw tool accumulation increases token use | `R1` | Compact ledger and question router; fixture evidence passed, with `R1` scale risk retained. |
| `RISK-004` experiment prose drifts from generated results | `R1` | Contract test reads `latest.json`; regenerated outputs and Markdown gate passed. |

The affected surface remains an R2 public workflow contract. The bounded
repository acceptance criteria have no open material defect; broader behavioral
efficacy is not claimed.

## 6. Conditions and techniques

- `COND-001` result integrity: decision-table comparison of six methods and
  boundary checks for recall, precision, missed aliases, and token proxy.
- `COND-002` routing contract: checklist-based static contract verification for
  capability, freshness, provenance, fallback, and ledger fields.
- `COND-003` installability: command-based discovery of the packaged skill.
- `COND-004` prose structure: deterministic Markdown validation.
- `COND-005` reproducibility: full benchmark rerun using pinned Graphify and the
  recorded AST/LSP toolchain.

## 7. Verification obligations

| Obligation | Required independence | Result and evidence |
| --- | --- | --- |
| `OBL-001` experiment record matches structured evidence | deterministic verifier | PASS: unit-test result plus regenerated JSON/report. |
| `OBL-002` operational skill contains routing and trust boundaries | deterministic verifier | PASS: four contract tests. |
| `OBL-003` compact route preserves fixture accuracy and Graphify alias gap remains represented | external tool execution | PASS: benchmark shows 100%/100% compact and Graphify missing `rotateCredential`. |
| `OBL-004` skill remains package-discoverable | external CLI | PASS: `npx skills` found exactly `review-response`. |
| `OBL-005` repository Markdown is structurally valid | deterministic verifier | PASS after defect correction: zero errors. |

Agent-level comparative behavior is a follow-up experiment, not a hidden
mandatory obligation for this mechanism-focused change.

## 8. Entry-criteria deviations

The repository has no canonical CI workflow, prose-quality configuration, or
real-repository benchmark corpus. Verification therefore used the documented
local commands and explicitly limits the conclusion to this repository and
fixture.

## 9. Commands and scenarios executed

```sh
python3 -m unittest discover -s tests -v
npx --yes markdownlint-cli2@0.19.0 '**/*.md' \
  '#experiments/tool-routing/.graphify-out/**'
npx --yes skills@1.5.21 add "$PWD" --list
python3 experiments/tool-routing/run_benchmark.py
jq '(.methods[] |= del(.elapsed_ms, .cold_index_ms))' RUN1.json > RUN1.stable
jq '(.methods[] |= del(.elapsed_ms, .cold_index_ms))' RUN2.json > RUN2.stable
diff -u RUN1.stable RUN2.stable
git diff --check
```

The first Markdown run failed with 10 errors. After this report was added, its
wide evidence tables produced 20 additional line-length findings and were given
a scoped `MD013` exception; the repeated repository run passed with zero.
The benchmark exercised all six strategies and regenerated both structured and
human-readable evidence. `RUN1.json` and `RUN2.json` above denote the two
preserved temporary snapshots used in the repeated-run comparison.

## 10. Evidence and independence

- Four unit tests passed.
- Seven Markdown files were checked in the pre-report pass with zero final
  errors; the final gate includes this report as an additional file.
- Six benchmark methods produced terminal results.
- One installable skill was discovered.
- Benchmark candidate sets remained stable; elapsed time and a small portion of
  byte-derived proxy output varied.

Lifecycle completion messages are not counted as evidence. Test assertions,
tool exit status, generated result artifacts, and Git diff checks are counted.

## 11. Coverage

- Basis: `BASIS-001` through `BASIS-005` covered.
- Risks: `RISK-001` through `RISK-004` covered at the declared synthetic scope.
- Conditions: `COND-001` through `COND-005` executed.
- Obligations: `OBL-001` through `OBL-005` passed.
- Uncovered: real-repository and agent-behavior partitions in `FIND-001`.

## 12. Defects

| Defect | Severity | Status |
| --- | --- | --- |
| `DEF-001` Markdown list/table violations | Minor | Ten initial violations were fixed; 20 report-table line-length findings received a scoped exception; the whole repository was retested. |
| `DEF-002` proxy drift from ripgrep timing fields | Minor | Fixed by deterministic normalization; two-run comparison passed. |
| `DEF-003` stale contract-test wording after normalization fix | Minor | Updated to assert the new determinism and interpretation contract; retested. |

No open material defect was observed in the declared scope.

## 13. Accepted exceptions

None. No material risk was converted to accepted risk, and no external approval
was used.

## 14. Untested scope and residual risk

Untested scope includes large real repositories, stale-index experiments,
unsupported languages, generated code, reflection and runtime registration,
setup-cost amortization, and an old-vs-new agent behavior trial. These prevent a
production-scale accuracy or token-savings claim, but do not invalidate the
fixture-backed routing and evidence-contract change.

## 15. Final QA verdict

`PASS` for the bounded repository change: every mandatory obligation has a
terminal pass, the two observed defects were fixed and retested, and no material
defect remains within the declared test basis. This verdict does not claim that
the revised skill has already improved agent behavior on real repositories.

## 16. Harness completion

Traceknot workflow execution is complete for this snapshot. Host task
completion remains separate until the changes are committed and integrated.
