# Review Radius brand validation

## Decision

Keep **Review Radius** as the open-source project name, but treat it as a
qualified choice rather than a globally cleared mark. Replace the original
tagline with **“Fix the pattern behind the comment.”** and ship equal EN, KO,
and `zh-CN` message systems.

The name fits the product because *radius* denotes distance from a center and
can denote a bounded area: the review comment is the center, while the search
stops at an evidence-backed boundary. (`clm_004`; `src_merriam_radius`,
`src_cambridge_radius`)

## Collision screen

The time-bounded public search found no exact `review-radius` or `ReviewRadius`
repository name on GitHub (`clm_001`; `src_github_api`). It also found no exact
package under the checked variants on npm, PyPI, crates.io, or RubyGems
(`clm_002`; `src_npm`, `src_pypi`, `src_crates`, `src_rubygems`). The old and
selected English taglines both returned zero exact GitHub code-search matches
at the observation time (`clm_006`; `src_github_api`).

This is not a clean global namespace. `reviewradius.com` was already registered
and its registry record includes a 2019-08-06 registration event (`clm_003`;
`src_verisign_rdap`). The repository must not imply ownership of that domain.

## Language architecture

Use these canonical lines:

<!-- markdownlint-disable MD013 -->

| Locale | Primary line | Product description |
| --- | --- | --- |
| EN | Fix the pattern behind the comment. | An evidence-driven skill that finds and fixes the defect class a review comment reveals. |
| KO | 리뷰가 드러낸 결함 패턴까지 고치세요. | 리뷰 코멘트가 드러낸 동종 결함을 근거가 확인된 범위까지 추적하고 수정하는 PR 리뷰 대응 스킬. |
| zh-CN | 修复审查意见所揭示的同类缺陷。 | 一项以证据为依据的 PR 审查反馈处理技能，用于追踪并修复审查意见所揭示的同类缺陷。 |

<!-- markdownlint-enable MD013 -->

The locale identifier is `zh-CN`, not `Zn`. It is appropriate here because the
requested target is mainland Simplified Chinese; `zh-Hans` remains the
script-specific alternative when no region is intended (`clm_005`;
`src_w3c_tags`, `src_rfc5646`, `src_iana_registry`).

These are semantic localizations, not literal translations. Korean keeps the
developer-familiar term “리뷰,” while Simplified Chinese makes the review
context explicit with “审查意见” and renders “defect pattern” as the more direct
“同类缺陷.” The terminology review used GitHub's locale-specific documentation
as an anchor (`src_github_en_review`, `src_github_ko_review`,
`src_github_zh_review`), while final phrasing remains an editorial brand
decision.

## Confidence

- **High:** public GitHub, package-registry, domain-registration, and language-
  tag observations for the dated snapshot.
- **Medium:** semantic suitability of the English metaphor and the localized
  copy. These are evidence-informed editorial judgments, not objective facts.
- **Conditional go:** the name is suitable for an open-source repository that
  does not require `reviewradius.com`; re-evaluate if a commercial product,
  domain-led launch, or registered mark is planned.

## Refuted

No candidate claim was classified as refuted.

## Unresolved

The claim that **Review Radius has no conflicting trademark rights** is
unresolved (`clm_007`). The official USPTO search entry point was reachable
(`src_uspto_search`), but the WIPO result surface presented an automated-access
challenge (`src_wipo_branddb`), and no class-specific, jurisdiction-complete, or
common-law clearance was performed. Do not describe the name as trademark-
cleared without a proper clearance search.

The localized lines remain reviewed editorial choices rather than claims of a
single objectively correct translation.
