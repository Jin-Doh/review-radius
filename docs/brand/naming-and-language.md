# Naming and language system

Review Radius uses one public identity across the repository, installable skill,
and command surface.

<!-- markdownlint-disable MD013 -->

| Surface | Canonical form |
| --- | --- |
| Product name | **Review Radius** |
| Repository | `Jin-Doh/review-radius` |
| Skill folder and frontmatter | `review-radius` |
| Invocation | `$review-radius` |
| Supported locales | English (`en`), Korean (`ko`), mainland Simplified Chinese (`zh-CN`) |

<!-- markdownlint-enable MD013 -->

Compatibility aliases are not part of the current contract. Add one only when
an existing released integration needs a documented migration path.

## Message system

<!-- markdownlint-disable MD013 -->

| Locale | Primary line | Short description |
| --- | --- | --- |
| `en` | **Fix the pattern behind the comment.** | An evidence-driven skill that finds and fixes the defect class a review comment reveals. |
| `ko` | **리뷰가 드러낸 결함 패턴까지 고치세요.** | 리뷰가 드러낸 동종 결함을 근거가 확인된 범위까지 추적합니다. |
| `zh-CN` | **修复审查意见所揭示的同类缺陷。** | 追踪并修复审查意见所揭示的同类缺陷。 |

<!-- markdownlint-enable MD013 -->

The three lines carry the same promise without forcing a word-for-word
translation: a review comment starts the investigation, the same defect class
defines the work, and evidence bounds the search.

`brand/messages.json` is the machine-readable source of truth. Each supported
locale must provide a README, brand guide, primary line, and short description.
Contract tests keep these surfaces aligned.

## Terminology

<!-- markdownlint-disable MD013 -->

| Concept | English | Korean | Simplified Chinese |
| --- | --- | --- | --- |
| Review activity | code review / PR review | 코드 리뷰 / PR 리뷰 | 代码审查 / PR 审查 |
| Reviewer message | review comment | 리뷰 코멘트 | 审查意见 |
| Same-cause occurrences | defect class | 동종 결함 / 결함 패턴 | 同类缺陷 |
| Behavioral contract | invariant | 불변 조건 | 不变量 |
| Bounded inspected surface | review radius | 리뷰 반경 | 审查半径 |

<!-- markdownlint-enable MD013 -->

Use `zh-CN`, not `Zn`. The selected Chinese copy targets mainland Simplified
Chinese. Keep **Review Radius** in Latin script in every locale; translate the
bounded-search idea in the surrounding prose instead of translating the name.

## Copy boundary

README and brand copy should explain what the skill does, how to install it,
and where its evidence boundary ends. Search snapshots, naming-collision logs,
domain availability, and unresolved legal research are working records rather
than product value, so they do not belong in the product introduction.

Do not claim that Review Radius is globally unique, legally cleared, exhaustive,
or guaranteed to find every related defect. Handle any required naming or legal
review as a separate release decision instead of embedding raw research output
in user-facing copy.
