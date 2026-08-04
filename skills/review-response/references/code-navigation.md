# Code navigation and evidence routing

Use this reference after deriving the defect root, invariant, and bounded search
surface. The goal is to answer a specific relationship question with the least
expensive trustworthy capability, not to collect every available tool output.

## Capability snapshot

Before relying on AST, LSP, or a code graph, bind the navigation state to the
current repository, worktree, language, and PR head or commit. Record:

- available tools and supported languages;
- index or graph revision and whether it includes current changes;
- language-server initialization and advertised capabilities;
- exclusions, generated code, submodules, or dynamic behavior not represented;
- the fallback used when a capability is missing, stale, or fails.

Refresh a stale graph before using it as evidence. Ensure changed files are
opened or synchronized with the language server before requesting definitions,
references, implementations, or call hierarchy. If freshness cannot be proven,
treat the output as discovery-only and record a coverage gap.

## Question router

<!-- markdownlint-disable MD013 -->

| Question | First capability | Escalate when |
| --- | --- | --- |
| Where does this literal, key, flag, route, or config occur? | `rg` | Syntax differences or generated variants hide matches. |
| Which code has the same syntax-shaped failure mechanism? | AST query | Symbol aliases or wrappers determine meaning. |
| What defines, references, implements, or aliases this symbol? | LSP | A broad or transitive path crosses modules. |
| Which bounded direct or transitive relationships surround these roots? | Fresh code-graph query | Edges are inferred, ambiguous, missing aliases, or incomplete. |
| Does the behavior occur under reflection, dependency injection, runtime registration, or data-driven dispatch? | Focused tests or runtime evidence | Static tools only nominate candidates. |

<!-- markdownlint-enable MD013 -->

For structural or semantic review lenses, prefer this compact route when all
capabilities are available and justified:

1. Use AST queries to identify defect roots and structural analogues.
2. Ask a fresh graph only for the bounded direct and transitive neighborhood of
   those roots.
3. Use LSP to verify symbol identity and add only graph omissions or contested
   edges.
4. Read source around the final candidates and classify them against the
   invariant.
5. Use tests or runtime observations where static evidence cannot establish the
   behavior.

Do not make Graphify, an AST engine, or an LSP server an unconditional
dependency. A small editorial or configuration review may need only `rg` and
source inspection. Unsupported languages and failed initialization use the
best available fallback plus an explicit coverage statement.

## Provenance and authority

Use one or more of these exact provenance labels:

- `text-matched`: a literal or regular-expression match;
- `AST-matched`: a syntax-aware structural match;
- `graph-extracted`: a relationship extracted directly from parsed source;
- `graph-inferred`: an inferred or ambiguous graph relationship;
- `LSP-resolved`: a language server resolved symbol identity or relationship;
- `runtime-proven`: a focused test or runtime observation established behavior.

These labels describe how a candidate was found; they do not automatically
prove a defect. In particular, `graph-inferred` stays a candidate until source,
LSP, or runtime evidence confirms the relevant relationship. Runtime evidence
is authoritative for dynamic behavior, but it does not prove that the static
search surface was complete.

## Compact evidence ledger

Expose a normalized ledger to the reasoning context rather than concatenating
raw protocols or whole files:

<!-- markdownlint-disable MD013 -->

| Candidate | Anchor | Relation | Provenance | Freshness or confidence | Disposition |
| --- | --- | --- | --- | --- | --- |
| `rotateCredential` | `src/app.ts:12` | aliased caller | `LSP-resolved` | current head | `affected` |

<!-- markdownlint-enable MD013 -->

Preserve raw outputs outside the reasoning context when they are needed for
reproduction. Include only the smallest source slices required to validate the
invariant and classification.

## Stop and fallback rules

Stop expanding when every bounded root and credible direct/transitive candidate
has a disposition, another capability adds no new candidate class, and dynamic
or unsupported surfaces are either tested or reported as coverage gaps.

Fall back to `rg`, source inspection, repository tests, and explicit uncertainty
when an index is stale, a capability is unavailable, results conflict, or the
language uses relationships the tools cannot model. Never convert tool failure
into a completeness claim.

The experiment supporting this route is documented in
[`docs/experiments/2026-08-04-code-navigation-tool-routing.md`](../../../docs/experiments/2026-08-04-code-navigation-tool-routing.md).
