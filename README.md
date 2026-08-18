# Review Radius

![Review Radius — Fix the pattern behind the comment](assets/readme/review-radius-hero.png)

**Fix the pattern behind the comment.**

An evidence-driven GitHub PR review skill for Codex.

Review Radius turns a review comment into a bounded audit of the defect class it
reveals. It validates the feedback, derives the violated invariant, checks
credible related surfaces, and closes the review with evidence. The installable
skill, command, and repository share one name: `review-radius`.
[![skills.sh](https://skills.sh/b/Jin-Doh/review-radius)](https://skills.sh/Jin-Doh/review-radius/review-radius)

[한국어](README.ko.md) · [简体中文](README.zh-CN.md) ·
[Design](docs/design.md) ·
[Experiment](docs/experiments/2026-08-04-code-navigation-tool-routing.md) ·
[Brand guide](BRAND.md)

## Why Review Radius

A reviewer usually points to the first visible symptom. Fixing only that line
can leave the same defect in a sibling implementation, aliased caller, failure
path, configuration variant, or test.

![A review comment expands into a defect class, bounded audit, and evidence-backed fix](assets/readme/review-radius-workflow.png)

The radius expands only as far as the validated cause and authorized PR scope.
This is broader than line-level patching and narrower than opportunistic
refactoring.

## What it changes

<!-- markdownlint-disable MD013 -->

| Mechanical response | Review Radius |
| --- | --- |
| Treats the comment as the complete task | Treats the comment as evidence of a defect class |
| Searches the reported text | Searches textual, structural, and semantic analogues |
| Edits the named line | Fixes every verified in-scope occurrence of the cause |
| Reports a green test | Reconciles candidates, diff, threads, and gates |
| Ignores adjacent findings | Classifies them as safe, uncertain, affected, or out of scope |

<!-- markdownlint-enable MD013 -->

## Operating principles

1. **Comment as signal.** Preserve what the reviewer observed, then derive the
   invariant before deciding the fix boundary.
2. **Bounded expansion.** Inspect credible related code without turning one
   review into an unrelated cleanup campaign.
3. **Evidence before closure.** Classify candidates, test the invariant, and
   resolve threads only when the implementation state supports it.

## Bounded review sessions

Review Radius works in a bounded review session tied to the repository, PR,
current head, and feedback visible when the session starts. Every actionable
thread in that initial frozen batch, including non-blocking feedback, is
classified and dispositioned in the current session. Later feedback does not
silently expand that batch: same-class blocking feedback created by the cutoff
may join while budget remains; later non-blocking feedback is queued; same-class
blocking feedback created after the cutoff pauses the session for user
direction, even on a frozen thread.

The default automatic patch budget is **two rounds**. A two-pass review—before
implementation and after implementation—is distinct from that budget. When a
fix materially needs a new production dependency, nontrivial subsystem,
public-contract change, or similar strategy choice, Review Radius presents
build-versus-buy options: direct implementation, an existing dependency, new
open source, or a follow-up. It does not change production dependencies without
explicit user approval.

An optional `Traceknot` QA handoff is available for ordinary sessions and is the
required QA handoff for R2/R3 or recurring review loops. Review convergence and
the QA verdict remain separate: convergence of the bounded feedback batch does
not itself mean QA passed, delivery is complete, or Review Radius will invoke
itself. Explicitly invoking `$review-radius` is the most reliable way to start a
session.

## Install

Review Radius is published on [skills.sh](https://skills.sh/Jin-Doh/review-radius/review-radius)
as the `review-radius` skill.
Source repository: [Jin-Doh/review-radius](https://github.com/Jin-Doh/review-radius).

List the skills exposed by the repository:

```sh
npx skills add Jin-Doh/review-radius --list
```

Install Review Radius globally for Codex:

```sh
npx skills add Jin-Doh/review-radius \
  --skill review-radius \
  --agent codex \
  --global \
  -y
```

For project-local installation, omit `--global`:

```sh
npx skills add Jin-Doh/review-radius --skill review-radius --agent codex -y
```

For local development, use the checkout path:

```sh
npx skills add "$PWD" --skill review-radius --agent codex -y
```

Then invoke it as `$review-radius` when handling PR feedback.

## Evidence-backed navigation

The included TypeScript experiment compares text, AST, LSP, and Graphify-based
candidate discovery. On its synthetic fixture, a compact routed ledger retained
100% recall and precision with a 451-token proxy, versus 1694 for raw text
search. This validates the routing mechanism, not repository-scale performance.

Review Radius therefore routes by question instead of invoking every tool:

- `rg` for literals and configuration;
- AST for syntax-shaped analogues;
- LSP for symbol identity, aliases, implementations, and callers;
- a fresh code graph for bounded direct or transitive neighborhoods;
- focused tests or runtime observations for dynamic behavior.

## Boundaries

Review Radius does not:

- convert one comment into a general refactor;
- treat textual similarity or inferred graph edges as proof of a defect;
- claim completeness from one search tool;
- resolve ambiguous or blocked feedback to make a PR appear clean;
- replace repository tests, CI, or runtime evidence.

## Repository layout

```text
skills/review-radius/   Installable skill and operational references
docs/design.md            Workflow design and acceptance scenarios
docs/experiments/         Durable experiment decisions and limitations
docs/qa/                  Traceknot completion evidence
experiments/tool-routing/ Reproducible search-tool comparison
assets/                   Review Radius visual identity
tests/                    Skill, brand, and experiment contract tests
```

The installable skill is the operational source of truth. Design and experiment
documents explain why the workflow has those boundaries and how future changes
should be evaluated.

## Verify

```sh
python3 -m unittest discover -s tests -v
python3 experiments/tool-routing/run_benchmark.py
npx skills add "$PWD" --list
```

## Brand

**Review Radius** is the product name; `review-radius` is the repository, skill,
and command ID. See the [brand guide](BRAND.md) for voice and visual rules and
the [naming and language system](docs/brand/naming-and-language.md) for locale
and terminology decisions.

## License

Review Radius is available under the [MIT License](LICENSE).
The optional benchmark invokes Graphify `graphifyy==0.9.32`, which declares the
Apache License 2.0; see [Third-party notices](THIRD_PARTY_NOTICES.md) for its
upstream license, attribution, and integration boundary.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for the single-maintainer pull request
policy and [SECURITY.md](SECURITY.md) for private vulnerability reporting.
