# Review Radius brand guide

## Brand idea

**Review Radius** is the bounded distance a review comment should travel through
a codebase before the response can be considered complete.

The product promise is:

> Fix the pattern, not just the comment.

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

> Fix the pattern, not just the comment.

### One-sentence description

Review Radius turns GitHub review feedback into a bounded, evidence-driven audit
of the defect class it reveals.

### Short repository description

An evidence-driven Codex skill that fixes the defect pattern behind a GitHub
review comment without expanding beyond the validated cause.

### Korean equivalents

- Tagline: **코멘트만 고치지 말고, 패턴을 고치세요.**
- Description: **리뷰 코멘트가 드러낸 결함군을 제한된 범위에서 점검하고
  증거와 함께 닫는 Codex 스킬.**

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
- Choose and add an explicit open-source license before public distribution;
  the repository currently has no license file.
- Replace `<repository-url>` in install examples with the canonical URL.
- Set the GitHub repository description from the short description above.
- Use `assets/review-radius-mark.svg` as the basis for the social preview.
- Recheck GitHub, package-registry, domain, and trademark conflicts before a
  formal public launch; the initial name search is not legal clearance.
- Preserve `review-response` as the skill ID through the first public release.
