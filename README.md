# Review Radius

![Review Radius — Fix the pattern behind the comment](assets/readme/review-radius-hero.png)

**Fix the pattern behind the comment.**

An evidence-driven GitHub review-response skill for Codex.

Review Radius turns a review comment into a bounded audit of the defect class it
reveals. It validates the feedback, derives the violated invariant, checks
credible related surfaces, and closes the review with evidence. The installable
skill ID remains `review-response`.

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

## Install

List the skills exposed by a checkout or published repository:

```sh
npx skills add https://github.com/Jin-Doh/review-radius --list
```

Install Review Radius for Codex:

```sh
npx skills add https://github.com/Jin-Doh/review-radius \
  --skill review-response \
  --agent codex \
  -y
```

For local development, use the checkout path:

```sh
npx skills add "$PWD" --skill review-response --agent codex -y
```

Then invoke it as `$review-response` when handling PR feedback.

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
skills/review-response/   Installable skill and operational references
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

Review Radius is the project and product name. `review-response` is the stable
skill ID and command-facing identity. The public collision screen found a clear
GitHub and package-registry path, but `reviewradius.com` is already registered
and trademark clearance remains unresolved. See [BRAND.md](BRAND.md) for the
identity system and
[name and language validation](docs/brand/name-and-language-validation.md) for
the evidence and launch constraints.

## License

Review Radius is available under the [MIT License](LICENSE).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for the single-maintainer pull request
policy and [SECURITY.md](SECURITY.md) for private vulnerability reporting.
