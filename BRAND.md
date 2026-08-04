# Review Radius brand guide

[한국어](BRAND.ko.md) · [简体中文](BRAND.zh-CN.md) ·
[Validation record](docs/brand/name-and-language-validation.md)

## Brand idea

**Review Radius** is the bounded distance a review comment should travel through
a codebase before the response can be considered complete.

The product promise is:

> Fix the pattern behind the comment.

A comment identifies a visible point. Review Radius derives the violated
invariant, follows credible relationships around that point, and stops at the
validated cause and authorized change boundary.

## Brand architecture

<!-- markdownlint-disable MD013 -->

| Surface | Name | Rule |
| --- | --- | --- |
| Project and product | **Review Radius** | Use in prose, headings, repository descriptions, and visual identity. |
| Installable skill | `review-response` | Keep stable for installation and `$review-response` invocation. |
| Suggested repository | `review-radius` | Adopt when a public remote is created; do not rename the local directory merely for appearance. |
| Core workflow concept | review radius | Lowercase when describing the bounded search surface rather than the product. |

<!-- markdownlint-enable MD013 -->

Do not rename the skill ID to `review-radius` without an explicit compatibility
and migration plan.

## Positioning

### Category

Evidence-driven PR review response for coding agents.

### Audience

- engineers who want review feedback handled beyond the named line;
- maintainers who need bounded scope rather than opportunistic cleanup;
- teams that require traceable review, test, and thread-closure evidence.

### Problem

Mechanical review response treats one comment as one edit. That closes the
visible symptom while leaving the same violated assumption in related code.

### Difference

Review Radius makes the defect class the unit of work. It combines invariant
extraction, related-surface discovery, candidate disposition, cause-level
minimal fixes, and evidence-based closure.

## Message hierarchy

### Primary line

> Fix the pattern behind the comment.

### One-sentence description

Review Radius turns GitHub review feedback into a bounded, evidence-driven audit
of the defect class it reveals.

### Short repository description

An evidence-driven Codex skill that fixes the defect pattern behind a GitHub
review comment without expanding beyond the validated cause.

### Localized equivalents

<!-- markdownlint-disable MD013 -->

| Locale | Primary line | Short description |
| --- | --- | --- |
| `en` | **Fix the pattern behind the comment.** | An evidence-driven skill that finds and fixes the defect class a review comment reveals. |
| `ko` | **리뷰가 드러낸 결함 패턴까지 고치세요.** | 리뷰 코멘트가 드러낸 동종 결함을 근거가 확인된 범위까지 추적하고 수정하는 PR 리뷰 대응 스킬. |
| `zh-CN` | **修复审查意见所揭示的同类缺陷。** | 一项以证据为依据的 PR 审查反馈处理技能，用于追踪并修复审查意见所揭示的同类缺陷。 |

<!-- markdownlint-enable MD013 -->

These are semantic equivalents, not literal translations. Do not translate
the word *radius* in the product name. Keep **Review Radius** in Latin script
and explain the bounded-search metaphor in localized prose.

The machine-readable source of truth is `brand/messages.json`. Every supported
locale must have a README, a brand guide, a primary line, a short description,
and terminology choices. Tests enforce parity across these surfaces.

## Voice

Review Radius sounds like a senior engineer explaining a bounded technical
decision.

- Lead with the observed outcome or contract.
- Separate evidence, inference, and uncertainty.
- Prefer concrete nouns: invariant, caller, candidate, boundary, test, gate.
- Explain why expansion is justified and where it stops.
- Use calm, direct language; confidence comes from evidence rather than hype.

Avoid:

- “AI-powered magic,” “ultimate,” “complete,” or unsupported autonomy claims;
- framing every related hit as a defect;
- treating green CI as proof that the review radius was complete;
- describing the product as a generic code reviewer. It responds to reviews.

## Visual identity

The mark uses concentric rings around one review anchor:

- the amber center is the reviewer-observed symptom;
- the inner blue ring is the violated invariant and direct surface;
- the cyan outer ring is the bounded candidate radius;
- the terminal point represents evidence-backed disposition at the boundary.

### Color tokens

| Token | Hex | Use |
| --- | --- | --- |
| Ink | `#0B1220` | Primary background and technical depth |
| Radius cyan | `#38BDF8` | Search boundary and primary accent |
| Signal blue | `#2563EB` | Structural and semantic relationships |
| Review amber | `#F59E0B` | Original review signal |
| Evidence mint | `#34D399` | Terminal evidence or verified disposition |
| Paper | `#F8FAFC` | Text and light-surface background |

Use the mark from `assets/review-radius-mark.svg`. Preserve its proportions,
colors, and clear space of at least one inner-dot diameter. Do not add gradients,
shadows, code brackets, robot imagery, or GitHub-specific marks.

### Typography

Use the host platform's system sans-serif for product prose and a monospaced
face for commands, IDs, evidence labels, and code. The project does not bundle a
font.

## Naming examples

Preferred:

- “Run Review Radius on the unresolved PR feedback.”
- “Install the `review-response` skill.”
- “The review radius includes both implementations but excludes the migration.”

Avoid:

- “Run the Review Response Skill product.”
- “Install the `review-radius` skill.”
- “Review Radius guarantees that no similar defect exists.”

## Terminology

Use **comment** for the reviewer's concrete message, **feedback** for the wider
review input, **defect class** for occurrences caused by the same violated
invariant, and **review radius** for the bounded code surface inspected from the
comment. Do not use *pattern* to mean mere textual similarity.

Localized terminology is intentionally idiomatic:

- Korean uses `리뷰`, `리뷰 코멘트`, `동종 결함`, and `불변 조건` in developer-
  facing prose. Use `검토` only where the formal act matters.
- Simplified Chinese uses `代码审查`, `审查意见`, `同类缺陷`, and `不变量`.
  Avoid the consumer-product sense of `评论` when code review is intended.

## Brand boundaries

The brand does not imply exhaustive repository analysis. Any completeness claim
must name the inspected surface, capabilities, freshness, and remaining gaps.
The benchmark evidence is synthetic and supports the routing mechanism only.

Review Radius remains compatible with the existing `review-response` skill ID.
Brand changes must not silently change installation, invocation, or evidence
contracts.

## Public-launch checklist

- Create the public remote under the chosen owner with repository name
  `review-radius` if available.
- Keep the root `LICENSE` file and localized README license links intact; the
  project is distributed under the MIT License.
- Replace `<repository-url>` in install examples with the canonical URL.
- Set the GitHub repository description from the short description above.
- Use `assets/review-radius-mark.svg` as the basis for the social preview.
- Do not imply ownership of `reviewradius.com`; it was already registered when
  checked on 2026-08-04.
- Recheck GitHub, package registries, domains, and trademarks before a formal
  public launch. The recorded public search is not legal clearance.
- Preserve `review-response` as the skill ID through the first public release.
