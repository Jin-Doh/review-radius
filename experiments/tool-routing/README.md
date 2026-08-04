# Tool-routing experiment

This experiment compares six candidate-discovery paths for one review-driven
defect class:

1. `rg` plus full-file reads
2. `rg` plus AST structural search
3. `rg` plus AST plus TypeScript LSP
4. Graphify query as a component diagnostic
5. Graphify plus AST plus TypeScript LSP
6. Compact routing: AST roots, Graphify candidates, then only the LSP delta

The review seed is `samePrincipalLoose`: canonical principal identifiers are
case-sensitive, so case-folding equality is unsafe. The task is to find the
seed, structurally equivalent implementations, and direct or transitive
consumers while excluding display-only normalization and strict comparisons.

Ground truth is stored separately from source under `ground-truth.json`. The
runner does not use ground truth for discovery; it reads it only when scoring
the candidate sets returned by each method.

## Run

```sh
python3 experiments/tool-routing/run_benchmark.py
```

Requirements:

- `rg`
- `ast-grep`
- `typescript-language-server`
- `node`
- `uv` for the pinned, isolated Graphify run

Graphify is executed with `uvx --from graphifyy==0.9.32`; it is not installed
globally. Set `SKIP_GRAPHIFY=1` to run the first three methods only.

The runner writes `results/latest.json` and `results/REPORT.md`. Graphify builds
its index in an isolated temporary copy of the fixture so every run measures a
fresh graph build without dirtying the worktree.

## Measurement limits

`estimated_tokens` is a deterministic byte-based proxy, not an API token bill.
It divides tool output plus modeled source reads by four. Full files are charged
to text and AST methods; LSP methods are charged only small source windows
around returned symbols. Cold index time and warm query time are reported
separately for Graphify.

Before scoring ripgrep JSON, the runner removes elapsed-time and self-sized
`bytes_printed` fields and canonicalizes the remaining JSON. Those fields vary
between equivalent executions and would otherwise make the proxy
nondeterministic. Wall-clock measurements remain observational and may vary.

The cumulative method charges raw outputs from every stage. The compact routing
method represents the intended adapter contract: tools may process rich data,
but the model receives only roots, graph candidates, LSP-only additions, and
source locations.
