# Review Radius

![Review Radius 심볼](assets/review-radius-mark.svg)

**리뷰가 드러낸 결함 패턴까지 고치세요.**

Codex를 위한 증거 기반 GitHub 리뷰 대응 스킬입니다.

Review Radius는 리뷰 코멘트를 출발점으로 삼아 같은 원인에서 생긴 결함이
관련 코드에 더 남아 있는지 범위를 정해 점검합니다. 피드백을 검증하고,
깨진 불변 조건(invariant)을 도출하고, 관련 코드 영역을 확인한 뒤, 구현과
검증 결과가 뒷받침될 때 리뷰를 마무리합니다. 설치 가능한 스킬 ID는 기존과
동일한 `review-response`입니다.

[English](README.md) · [简体中文](README.zh-CN.md) · [설계](docs/design.md) ·
[실험](docs/experiments/2026-08-04-code-navigation-tool-routing.md) ·
[브랜드 가이드](BRAND.ko.md)

## 왜 Review Radius인가

리뷰어는 대개 가장 먼저 드러난 증상을 가리킵니다. 지적된 한 줄만 수정하면
같은 결함이 형제 구현, alias caller, 실패 경로, 설정 변형이나 테스트에 남을
수 있습니다.

```text
리뷰 코멘트
    ↓
깨진 불변 조건
    ↓
제한된 관련 표면
    ↓
후보 분류
    ↓
원인 수준 수정과 증거
```

탐색 반경은 검증된 원인과 허용된 PR 범위까지만 확장됩니다. 한 줄만 고치는
대응보다는 넓지만, 기회성 리팩터링보다는 좁습니다.

## 동작 원칙

1. **코멘트는 신호입니다.** 리뷰어가 관찰한 사실을 보존하되, 수정 범위를
   정하기 전에 깨진 불변 조건을 도출합니다.
2. **확장은 제한됩니다.** 관련 코드까지 점검하지만 한 리뷰를 무관한 정리
   작업으로 바꾸지 않습니다.
3. **증거가 있어야 닫습니다.** 후보를 분류하고 불변 조건을 검증한 뒤 실제
   구현 상태에 맞춰 스레드를 해결합니다.

## 설치

```sh
npx skills add <repository-url> \
  --skill review-response \
  --agent codex \
  -y
```

로컬 checkout에서는 다음과 같이 설치할 수 있습니다.

```sh
npx skills add "$PWD" --skill review-response --agent codex -y
```

PR 리뷰 대응 시 `$review-response`로 호출합니다.

## 탐색 전략

질문에 따라 도구를 선택하며 모든 도구를 기계적으로 실행하지 않습니다.

- literal과 설정은 `rg`;
- 구문 구조가 같은 코드는 AST;
- symbol, alias, 구현과 caller는 LSP;
- 제한된 직접·전이 관계는 최신 code graph;
- 동적 동작은 집중 테스트나 runtime 관찰로 확인합니다.

합성 TypeScript 픽스처에서는 압축 라우팅이 재현율과 정밀도 100%, 토큰
대용치 451을 기록했습니다. 이는 라우팅 메커니즘에 대한 증거이며 실제 대형
저장소의 성능 보장은 아닙니다.

## 경계

Review Radius는 다음을 하지 않습니다.

- 하나의 코멘트를 일반적인 리팩터링으로 확대하지 않습니다.
- 텍스트 유사성이나 추론된 graph edge만으로 결함을 확정하지 않습니다.
- 하나의 검색 도구로 탐색 완전성을 주장하지 않습니다.
- 모호하거나 차단된 리뷰를 PR을 깨끗하게 보이게 하려고 닫지 않습니다.
- 저장소 테스트, CI 또는 runtime 증거를 대체하지 않습니다.

프로젝트 이름은 Review Radius이며 `review-response`는 호환성을 유지하는
스킬 ID입니다. GitHub와 주요 패키지 레지스트리의 공개 충돌 점검에서는
동일 이름을 찾지 못했지만, `reviewradius.com`은 이미 등록돼 있고 상표 사용
가능성은 확인되지 않았습니다. 자세한 메시지와 시각 규칙은
[한국어 브랜드 가이드](BRAND.ko.md), 근거와 출시 조건은
[이름·언어 검증 문서](docs/brand/name-and-language-validation.md)에 있습니다.

## 라이선스

Review Radius는 [MIT License](LICENSE)에 따라 사용할 수 있습니다.
