# README visual system

Date: 2026-08-04

## Purpose

The README visual system gives Review Radius two complementary assets:

- `assets/readme/review-radius-hero.png` establishes the product identity and
  primary promise;
- `assets/readme/review-radius-workflow.png` explains the operating model with
  one visual sequence and four short English labels.

Both assets were generated with OpenAI image generation using
`assets/review-radius-mark.svg` as the identity reference. They intentionally
reuse the mark's ink, cyan, blue, amber, mint, and paper palette.

## Narrative

The hero combines the product name, “Fix the pattern behind the comment,” the
radius mark, and a bounded code-node network. It is the brand surface, not a
technical completeness claim.

The workflow image prioritizes recognition over explanation:

```text
COMMENT -> DEFECT CLASS -> BOUNDED AUDIT -> EVIDENCE
```

Amber marks the review signal and affected candidates, blue marks inspected
safe candidates, gray stays outside the credible boundary, and mint marks
evidence-backed completion.

## Usage contract

- Use the same two raster files in EN, KO, and `zh-CN` READMEs.
- Keep the localized primary line as searchable text next to the hero.
- Give each image meaningful localized alt text; embedded English text is not a
  substitute for accessible prose.
- Do not resize, crop, recolor, add gradients, or overlay additional text.
- Do not imply exhaustive analysis. The ring represents a bounded,
  evidence-backed inspection surface.
- Keep the SVG mark as the canonical compact identity. The raster assets are
  narrative applications of that mark.

## Production properties

<!-- markdownlint-disable MD013 -->

| Asset | Dimensions | Format | Role |
| --- | ---: | --- | --- |
| `review-radius-hero.png` | 1600 × 640 | RGB PNG | README identity banner |
| `review-radius-workflow.png` | 1400 × 788 | RGB PNG | Intuitive workflow explanation |

<!-- markdownlint-enable MD013 -->

The source generation outputs remain outside the repository. The optimized
files under `assets/readme/` are the published artifacts and must pass the
repository dimension, size, README-reference, and Markdown contracts.
