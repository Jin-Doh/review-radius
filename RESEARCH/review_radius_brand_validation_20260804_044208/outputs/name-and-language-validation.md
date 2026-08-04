# Name and language validation

Status: conditional go  
Observed: 2026-08-04  
Locales: English (`en`), Korean (`ko`), mainland Simplified Chinese (`zh-CN`)

## Decision

Keep **Review Radius** for the open-source project, preserve
`review-response` as the installable skill ID, and use the following primary
lines:

<!-- markdownlint-disable MD013 -->

| Locale | Primary line | Why this form |
| --- | --- | --- |
| `en` | **Fix the pattern behind the comment.** | Removes the awkward implication that the comment itself is fixed and makes the comment an evidence anchor. |
| `ko` | **리뷰가 드러낸 결함 패턴까지 고치세요.** | Reads naturally in Korean developer language and makes the expansion beyond the named symptom explicit. |
| `zh-CN` | **修复审查意见所揭示的同类缺陷。** | Uses `审查意见` to anchor code review and `同类缺陷` to express same-cause occurrences without a stiff literal translation. |

<!-- markdownlint-enable MD013 -->

This is a semantic localization system. The three lines preserve one promise:
a review comment is the starting signal, the same defect class is the unit of
work, and evidence bounds the search.

## Collision screen

The following checks are snapshots, not reservations or legal clearance.

<!-- markdownlint-disable MD013 -->

| Surface | Query | Observed result |
| --- | --- | --- |
| GitHub repositories | exact `review-radius` and `ReviewRadius` names | No exact repository name returned by the checked searches. |
| GitHub code | old and selected exact English taglines | No exact phrase returned by the checked searches. |
| npm | `review-radius`, `reviewradius` | Exact endpoints returned not found. |
| PyPI | `review-radius`, `reviewradius` | Exact endpoints returned not found. |
| crates.io | `review-radius`, `reviewradius` | Query result contained zero crates. |
| RubyGems | `review-radius`, `reviewradius` | Exact endpoints returned not found. |
| `.com` registry | `reviewradius.com` | Already registered; registry record includes a 2019-08-06 registration event. |
| Trademarks | USPTO and WIPO public search surfaces | Incomplete; no legal-clearance conclusion. |

<!-- markdownlint-enable MD013 -->

The repository and package namespace signal is favorable, while the domain and
legal signals require explicit limits. Do not claim that Review Radius is
globally unique, do not imply control of `reviewradius.com`, and do not attach a
trademark symbol based on this screen.

## Name fitness

The brand metaphor is coherent. Standard English dictionary senses define a
radius as the distance from a center to a boundary and also as a bounded area.
That maps cleanly to the workflow:

```text
review comment = center
related candidates = points within the investigated area
validated cause and authorized scope = boundary
```

The metaphor fails if the product implies an exhaustive repository scan. Brand
copy must therefore pair *radius* with boundedness, evidence, candidate
classification, and explicit gaps.

## Expression review

The original line, “Fix the pattern, not just the comment,” had three problems:

1. A review comment is feedback, not normally the object being fixed.
2. *Pattern* was underspecified and could mean textual similarity rather than a
   shared violated invariant.
3. A literal translation amplified the ambiguity in Korean and Chinese.

“Fix the pattern behind the comment” repairs the grammatical relationship and
keeps a compact rhythm. Supporting copy must define *pattern* as the defect
class caused by the same violated invariant, not any neighboring resemblance.

## Locale contract

`brand/messages.json` is the machine-readable source of truth. A supported
locale is complete only when all of the following exist:

- a primary line, one-sentence description, and short description;
- a localized README and brand guide;
- language navigation from every README and brand guide;
- explicit terminology and tone guidance;
- contract tests that compare rendered copy with the message registry.

The identifier is `zh-CN`, not `Zn`. BCP 47 casing uses a lower-case language
subtag and upper-case region subtag. `zh-Hans` is the script-specific option;
this repository uses `zh-CN` because the selected copy targets mainland
Simplified Chinese rather than every Simplified Chinese market.

## Terminology decisions

<!-- markdownlint-disable MD013 -->

| Concept | English | Korean | Simplified Chinese |
| --- | --- | --- | --- |
| Review activity | code review / PR review | 코드 리뷰 / PR 리뷰 | 代码审查 / PR 审查 |
| Concrete reviewer message | review comment | 리뷰 코멘트 | 审查意见 |
| Same-cause occurrences | defect class | 동종 결함 / 결함 패턴 | 同类缺陷 |
| Behavioral contract | invariant | 불변 조건 | 不变量 |
| Bounded inspected surface | review radius | 리뷰 반경 | 审查半径 |

<!-- markdownlint-enable MD013 -->

GitHub's [English](https://docs.github.com/en/pull-requests/reference/pull-request-reviews),
[Korean](https://docs.github.com/ko/pull-requests/reference/pull-request-reviews),
and [Simplified Chinese](https://docs.github.com/zh/pull-requests/reference/pull-request-reviews)
review documentation served as terminology anchors. The final copy is
editorially localized rather than copied or translated word for word.

## Evidence and limitations

The English metaphor was checked against
[Merriam-Webster](https://www.merriam-webster.com/dictionary/radius) and the
[Cambridge Dictionary](https://dictionary.cambridge.org/dictionary/english/radius).
The locale decision follows W3C guidance on
[choosing language tags](https://www.w3.org/International/questions/qa-choosing-language-tags),
[RFC 5646](https://www.rfc-editor.org/rfc/rfc5646.html), and the
[IANA Language Subtag Registry](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry).

Trademark availability is unresolved. The official
[USPTO search entry point](https://www.uspto.gov/trademarks/search) was reachable,
but the WIPO Global Brand Database presented an automated-access challenge, and
no class-specific, jurisdiction-complete, phonetic, translation, or common-law
search was performed. Re-run the technical collision checks and obtain an
appropriate legal clearance before a commercial or registered-mark launch.
