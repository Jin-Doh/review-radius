# Review Response Skill

An evidence-driven GitHub PR review-response skill. It treats each review
comment as a signal for a potentially broader defect class, audits related
code through the same review lens, and keeps any expansion bounded and
traceable.

## Install

List the skills exposed by this repository:

```sh
npx skills add <repository-url> --list
```

Install `review-response` for Codex:

```sh
npx skills add <repository-url> --skill review-response --agent codex -y
```

For local development, replace `<repository-url>` with the absolute path to
this checkout.

## Repository layout

```text
skills/review-response/  Installable skill
docs/design.md           Workflow design and acceptance criteria
docs/experiments/        Durable experiment decisions and limitations
docs/qa/                 Traceknot completion evidence
experiments/tool-routing/ Reproducible search-tool comparison
tests/                    Skill and experiment contract tests
```

The installable skill is the operational source of truth. The design document
explains why the workflow is structured this way and how future changes should
be evaluated.

## Verify

```sh
python3 -m unittest discover -s tests -v
python3 experiments/tool-routing/run_benchmark.py
npx skills add "$PWD" --list
```
