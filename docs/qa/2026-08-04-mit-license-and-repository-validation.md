# MIT license and repository validation

> Historical record: this report predates the canonical `review-radius` skill
> identity. Mentions of `review-response` describe the contract that was tested
> at the time and do not define a current compatibility alias.

Date: 2026-08-04  
Implementation snapshot: `5cb63e697daba9b44fd78b453e9c4c7eeace68d8`  
QA method: Traceknot evidence-bound repository verification

## 1. Target and change scope

The target is Review Radius after the multilingual brand work and the addition
of an MIT license. The changed contract is:

- the repository grants the permissions and warranty limitations in the MIT
  License;
- English, Korean, and mainland Simplified Chinese readers can discover that
  license from their README;
- the brand guide no longer says that the repository is unlicensed;
- the existing `review-response` skill identity, localized brand contract,
  research evidence, and tool-routing experiment remain valid.

The copyright line uses `2026 KyungHo Kim`, derived from the current year and
the sole author identity observed across the repository's Git history. That
observation supports repository consistency; it is not an independent legal
ownership opinion.

## 2. Test basis and acceptance criteria

<!-- markdownlint-disable MD013 -->

| Basis | Origin | Observable acceptance criterion |
| --- | --- | --- |
| `BASIS-001` | Explicit user request | A root `LICENSE` contains the MIT terms. |
| `BASIS-002` | Explicit user request | Current repository work receives a Traceknot-based verdict. |
| `BASIS-003` | Derived from public install contract | `npx skills` discovers exactly `review-response`. |
| `BASIS-004` | Derived from `brand/messages.json` | EN, KO, and `zh-CN` surfaces remain complete and message-consistent. |
| `BASIS-005` | Derived from experiment claims | The six-method synthetic benchmark remains reproducible within its declared limits. |
| `BASIS-006` | Derived from brand research | Claim validation and evaluation gates retain their verified/unresolved boundary. |

<!-- markdownlint-enable MD013 -->

## 3. Discovery profile and trigger scan

No canonical `quality-capability` handshake was supplied. Traceknot therefore
used the `single-context` discovery profile and did not infer reviewer
independence from the Codex host name. Command execution and repository artifact
persistence were available, but no separate reviewer context was used.

The universal cheap trigger scan found:

- **Identity:** the stable skill ID and the three exact locale keys could drift.
- **Protocol/public contract:** installation discovery and the root license are
  externally consumed repository contracts.
- **Data realism:** the navigation benchmark uses a synthetic fixture and may
  not support production-scale conclusions.

Predicates: `scopeUnknown=false`, `materialTrigger=true`,
`syntheticBoundaryBypass=true`, and
`recurringDefectClusterOverlap=true`. The recurring cluster is the original
review-response failure mode of checking only the named occurrence. Because
the license and install identity are public contracts and the benchmark is
synthetic, a bounded current-context challenge was required.

## 4. Discovery findings and capability limits

The challenge tested malformed or incomplete license text, an incorrect or
missing holder line, stale unlicensed copy, a missing locale link, a changed
skill ID, package-discovery failure, benchmark drift, and leakage of unresolved
brand claims.

<!-- markdownlint-disable MD013 -->

| Finding | Taxonomy | Disposition |
| --- | --- | --- |
| `FIND-001` | `NOT_APPLICABLE` | Runtime, persistence, authentication, authorization, concurrency, interaction, and deployment profiles are not touched by this change. |
| `FIND-002` | `COVERAGE_GAP` | No configured independent Korean, English, or Chinese prose-quality analyzer exists. Deterministic copy parity and Markdown structure were checked; natural-language taste remains nonmaterial review scope. |
| `FIND-003` | `COVERAGE_GAP` | The synthetic benchmark still does not establish real-repository or agent-level efficacy. Existing limitations remain visible and no broader claim was introduced. |
| `FIND-004` | `POLICY_QUESTION` | Legal title to the copyright is not established by Git author metadata. The requested MIT grant and sole observed author identity support the selected line, but this QA is not a legal ownership opinion. |

<!-- markdownlint-enable MD013 -->

No source candidate indicated a concrete material failure requiring promotion
to a new confirmation obligation. No confirmed defect was observed. The
challenge completed in the current context; it contributes discovery, while
the official license references and deterministic tools provide the executable
verification evidence.

## 5. Product risks

<!-- markdownlint-disable MD013 -->

| Risk | Initial | Mitigation | Residual |
| --- | --- | --- | --- |
| `RISK-001` license text omits or changes a material MIT term | `R2` | Full normalized comparison with official SPDX and GitHub MIT templates plus a repository contract test | No observed material mismatch |
| `RISK-002` license is not discoverable or brand copy remains stale | `R1` | Three-locale link assertions and stale-text assertion | No observed mismatch |
| `RISK-003` licensing edit breaks skill packaging or stable identity | `R2` | Unit contract tests and pinned `npx skills` discovery | No observed regression |
| `RISK-004` localized brand surfaces drift | `R1` | Message-registry parity tests and repository Markdown gate | Natural-language judgment remains a nonmaterial limit |
| `RISK-005` prior research or benchmark evidence is no longer reproducible | `R2` | Isolated ledger/evaluation gates and two benchmark repetitions | Synthetic and real-repository generalizability limit remains |

<!-- markdownlint-enable MD013 -->

## 6. Conditions and techniques

- `COND-001` MIT text equivalence: positive equivalence partition and error
  guessing for missing permission, notice, or warranty clauses.
- `COND-002` attribution boundary: exact year/holder assertion and history
  consistency inspection.
- `COND-003` locale discoverability: three-partition decision table over EN,
  KO, and `zh-CN` README paths.
- `COND-004` compatibility: package discovery and stable skill-ID regression.
- `COND-005` brand/research integrity: structured contract tests plus verified,
  unresolved, and refuted state checks.
- `COND-006` experiment reproducibility: repeated-run comparison with
  nondeterministic timing fields removed.

## 7. Verification obligations

<!-- markdownlint-disable MD013 -->

| Obligation | Conditions | Minimum evidence | Result |
| --- | --- | --- | --- |
| `OBL-001` canonical MIT grant | `COND-001`, `COND-002` | Official templates plus deterministic full-text comparison | PASS: SPDX and GitHub template comparisons matched after holder substitution and whitespace normalization. |
| `OBL-002` locale-visible license | `COND-003` | Repository test | PASS: all three README files link root `LICENSE`. |
| `OBL-003` install compatibility | `COND-004` | External CLI observation | PASS: pinned `skills@1.5.21` found one skill, `review-response`. |
| `OBL-004` brand and Markdown integrity | `COND-003`, `COND-005` | Unit and lint results | PASS: 9 tests and 18 Markdown files passed. |
| `OBL-005` research claim boundary | `COND-005` | Deterministic ledger and report evaluators | PASS: 7 verified, 1 unresolved, 0 refuted; evaluation PASS with zero dangling citations or leaks. |
| `OBL-006` benchmark regression | `COND-006` | Two isolated executions and stable-output diff | PASS: six methods completed twice and non-timing results were identical. |

<!-- markdownlint-enable MD013 -->

## 8. Entry-criteria deviations

The repository has no canonical CI workflow, release workflow, license scanner,
or configured multilingual prose-quality analyzer. Official MIT templates,
repository tests, Markdown lint, the install CLI, research validators, and an
isolated benchmark copy supplied the available test surfaces. No browser,
production system, or destructive operation was applicable.

## 9. Commands and scenarios executed

```sh
python3 -m unittest discover -s tests -v
npx --yes markdownlint-cli2@0.23.2 '**/*.md' '#.git/**'
npx --yes skills@1.5.21 add "$PWD" --list
gh api licenses/mit --jq .body
python3 experiments/tool-routing/run_benchmark.py
jq '(.methods[] |= del(.elapsed_ms, .cold_index_ms))' RUN.json
diff -u RUN1.stable.json RUN2.stable.json
python3 validate_ledger.py --session RESEARCH/review_radius_brand_validation_20260804_044208
python3 eval_report.py --session RESEARCH/review_radius_brand_validation_20260804_044208
git diff --check
```

The benchmark and research gates ran in an isolated temporary copy so their
generated timing and verification timestamps could not dirty the target
snapshot. The MIT comparison replaced only the template holder placeholder and
normalized whitespace before comparing the entire license text.

## 10. Evidence and independence

- 9 unit-test cases passed.
- 18 Markdown files passed with zero findings before this report was added. The
  final repository pass covered 19 files after the report-table defect was
  corrected.
- 1 installable skill was discovered with the stable ID.
- 2 benchmark runs completed; 6 methods per run produced identical non-timing
  results.
- The research gate produced 7 verified, 1 unresolved, and 0 refuted claims.
- Research evaluation recorded 100% citation resolution, 0% orphan sources,
  0% unresolved/refuted leakage, and 100% verified-claim coverage.
- SPDX and GitHub license data were independent primary references. Repository
  tests, Markdown lint, the package CLI, and research scripts were deterministic
  or external tool producers rather than agent completion claims.

The adversarial challenge itself was a self-check in the current context. No
subagent, lifecycle event, or model identity is counted as independent evidence.

## 11. Coverage

- Basis: `BASIS-001` through `BASIS-006` covered.
- Risks: `RISK-001` through `RISK-005` covered at the declared repository and
  synthetic-fixture boundary.
- Conditions: `COND-001` through `COND-006` executed.
- Obligations: `OBL-001` through `OBL-006` passed.
- Uncovered nonmaterial scope: independent prose-style judgment.
- Uncovered pre-existing scope: production-scale and real-repository routing
  behavior, already excluded by the experiment contract.

## 12. Defects

`DEF-001` (`S4`, closed) recorded 10 `MD013` findings in two wide traceability
tables when the completion report entered the repository gate. The tables were
given locally scoped line-length exceptions, and the same full Markdown command
was rerun. No material defect was observed.

The stale “no license file” checklist item was an identified affected
occurrence in the implementation scope and was removed before the verification
snapshot.

## 13. Accepted exceptions

None. No material failure or risk was converted to accepted risk, and no
external approval was used.

## 14. Untested scope and residual risk

This QA does not establish legal ownership, trademark clearance, or the effect
of the MIT license in a particular jurisdiction. The copyright holder line is
consistent with repository history, but ownership disputes require legal
evidence outside repository QA.

The navigation result remains limited to a small synthetic TypeScript fixture.
No claim of repository-scale accuracy, billed-token savings, or observed agent
behavior is added. Multilingual tests establish surface completeness and exact
message parity, not universal native-speaker preference.

## 15. Final QA verdict

`PASS` for the declared repository contract. Every mandatory obligation passed,
no open material defect was observed, and the remaining limitations do not
contradict the license, installation, localization, research, or synthetic
experiment claims. This verdict demonstrates bounded confidence, not defect
absence or legal advice.

## 16. Harness completion

The Traceknot QA workflow reached a terminal verdict for implementation snapshot
`5cb63e697daba9b44fd78b453e9c4c7eeace68d8`. Branch integration and worktree
cleanup are host delivery activities and are reported separately from the QA
verdict.
