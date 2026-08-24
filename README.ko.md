# Review Radius

![Review Radius 영문 히어로 이미지와 코멘트 뒤의 패턴을 고친다는 메시지](assets/readme/review-radius-hero.png)

**리뷰가 드러낸 결함 패턴까지 고치세요.**

Codex를 위한 증거 기반 GitHub 리뷰 대응 스킬입니다.

Review Radius는 리뷰 코멘트를 출발점으로 삼아 같은 원인에서 생긴 결함이
관련 코드에 더 남아 있는지 범위를 정해 점검합니다. 피드백을 검증하고,
깨진 불변 조건(invariant)을 도출하고, 관련 코드 영역을 확인한 뒤, 구현과
검증 결과가 뒷받침될 때 리뷰를 마무리합니다. 저장소와 설치 가능한 스킬,
호출 ID는 모두 `review-radius`입니다.
[![skills.sh](https://skills.sh/b/Jin-Doh/review-radius)](https://skills.sh/Jin-Doh/review-radius/review-radius)

[English](README.md) · [简体中文](README.zh-CN.md) · [설계](docs/design.md) ·
[실험](docs/experiments/2026-08-04-code-navigation-tool-routing.md) ·
[브랜드 가이드](BRAND.ko.md)

## 왜 Review Radius인가

리뷰어는 대개 가장 먼저 드러난 증상을 가리킵니다. 지적된 한 줄만 수정하면
같은 결함이 나란히 존재하는 구현, 별칭을 거치는 호출부, 실패 경로, 설정
변형이나 테스트에 남을 수 있습니다.

![리뷰 코멘트가 결함군 탐색, 제한된 점검, 증거 기반 수정으로 이어지는 과정](assets/readme/review-radius-workflow.png)

탐색 반경은 검증된 원인과 허용된 PR 범위까지만 확장됩니다. 한 줄만 고치는
대응보다는 넓지만, 기회성 리팩터링보다는 좁습니다.

## 동작 원칙

1. **코멘트는 신호입니다.** 리뷰어가 관찰한 사실을 보존하되, 수정 범위를
   정하기 전에 깨진 불변 조건을 도출합니다.
2. **확장은 제한됩니다.** 관련 코드까지 점검하지만 한 리뷰를 무관한 정리
   작업으로 바꾸지 않습니다.
3. **증거가 있어야 닫습니다.** 후보를 분류하고 불변 조건을 검증한 뒤 실제
   구현 상태에 맞춰 스레드를 해결합니다.

Review Radius는 세 plane을 분리합니다. 검사 plane은 신뢰할 수 있는
아키텍처와 영향 범위를 넓게 확인하고, 수정 plane의 권한은 승인된 경계에
머무르며, 판정 plane은 증거 governor를 적용합니다. 각 세션에는 base/head SHA,
목표와 비목표, 승인된 경계, 아키텍처 기준선, 전략 전제, **아키텍처
컨텍스트**와 **영향 델타**, 결함 프론티어, 검증 의무를 담은 패킷이
기록됩니다. 프론티어는 불변 조건·메커니즘·경계·의무로 식별하고
`empty`, `shrinking`, `stable`, `expanding`, `regressing` 추세를 기록하며,
중복 코멘트는 별도 결함으로 세지 않습니다. 세션 중지 결정은 아키텍처 판정이
아니라 증거 governor가 내립니다. 증거가 부족하면
`INSUFFICIENT_ARCHITECTURE_EVIDENCE`, 영향 검토가 필요하면
`IMPACT_REVIEW_REQUIRED`를 사용합니다. 독립적으로 평가된 아키텍처 판정은
별도의 evaluator 입력·결과이며 governor 결정·QA·전달과 독립적으로 보고합니다.

## 제한된 리뷰 세션

Review Radius는 저장소, PR, 현재 헤드와 세션 시작 시 보인 피드백에 묶인
제한된 리뷰 세션으로 동작합니다. 초기 동결 묶음의 실행 가능한 스레드는
비차단 피드백을 포함해 모두 현재 세션에서 분류하고 처리합니다. 이후 피드백이
현재 묶음에 조용히 추가되지는 않습니다. 컷오프 시점까지 생성된 같은 결함군의
차단성 피드백은 예산이 남아 있을 때만 합류할 수 있고, 이후의 비차단 피드백은
대기열에 추가됩니다. 컷오프 이후 생성된 같은 결함군의 차단성 피드백은 동결된
스레드에서도 세션을 일시 중지하고 사용자의 명시적 지시를 기다립니다.

기본 자동 패치 예산은 **두 라운드**지만, 이는 수렴이나 전략 실패의 증거가
아닌 **안전 퓨즈**일 뿐입니다. 증거 governor는 잘못된 전제, 승인되지 않은
경계 확장, 새 의미 차원, 높아진 위험, 부족한 아키텍처 증거 또는 영향 검토가
필요할 때 더 일찍 멈출 수 있습니다. 구현 전후의 2단계 리뷰는 퓨즈와
별개입니다. 퓨즈가 소진된 뒤 추가 패치에는 명시적 지시가 필요하지만,
코드가 없는 중복·답변 전용 처리는 계속할 수 있습니다.

수정에 새로운 프로덕션 의존성, 중요 서브시스템, 공개 계약 변경 또는 이에
준하는 전략 선택이 실질적으로 필요하면 Review Radius는 build-versus-buy
방안으로 직접 구현, 기존 의존성, 새로운 오픈소스 또는 후속 작업을
제시합니다. 사용자의 명시적 승인 없이 프로덕션 의존성을 바꾸지 않습니다.

일반 세션에서는 `Traceknot` QA 핸드오프를 선택할 수 있고, R2/R3 또는 반복
리뷰 루프에서는 필요한 QA 핸드오프입니다. 리뷰 수렴과 QA 판정은 서로
별개입니다. 제한된 피드백 묶음이 수렴했다고 해서 QA 통과, 전달 완료 또는
Review Radius의 자동 호출이 보장되는 것은 아닙니다. 세션을 시작할 때
`$review-radius`를 명시적으로 호출하는 방법이 가장 확실합니다.

## 설치

Review Radius는 [skills.sh](https://skills.sh/Jin-Doh/review-radius/review-radius)에
`review-radius` 스킬로 등록되어 있습니다.
원본 저장소: [Jin-Doh/review-radius](https://github.com/Jin-Doh/review-radius).

저장소에서 제공하는 스킬을 확인합니다.

```sh
npx skills add Jin-Doh/review-radius --list
```

Codex에 전역 설치합니다.

```sh
npx skills add Jin-Doh/review-radius \
  --skill review-radius \
  --agent codex \
  --global \
  -y
```

프로젝트별로 설치하려면 `--global`을 생략합니다.

```sh
npx skills add Jin-Doh/review-radius --skill review-radius --agent codex -y
```

로컬 체크아웃에서는 다음과 같이 설치할 수 있습니다.

```sh
npx skills add "$PWD" --skill review-radius --agent codex -y
```

PR 리뷰 대응 시 `$review-radius`로 호출합니다.

## 탐색 전략

질문에 따라 도구를 선택하며 모든 도구를 기계적으로 실행하지 않습니다.

- 문자열과 설정은 `rg`;
- 구문 구조가 같은 코드는 AST;
- 심볼·별칭·구현·호출부는 LSP;
- 제한된 직접·전이 관계는 최신 코드 그래프;
- 동적 동작은 집중 테스트나 런타임 관찰로 확인합니다.

합성 TypeScript 픽스처에서는 압축 라우팅이 재현율과 정밀도 100%, 토큰
대용치 451을 기록했습니다. 이는 라우팅 메커니즘에 대한 증거이며 실제 대형
저장소의 성능 보장은 아닙니다.

## 경계

Review Radius는 다음을 하지 않습니다.

- 하나의 코멘트를 일반적인 리팩터링으로 확대하지 않습니다.
- 텍스트 유사성이나 추론된 그래프 관계만으로 결함을 확정하지 않습니다.
- 하나의 검색 도구로 탐색 완전성을 주장하지 않습니다.
- 모호하거나 차단된 리뷰를 PR을 깨끗하게 보이게 하려고 닫지 않습니다.
- 저장소 테스트, CI 또는 런타임 증거를 대체하지 않습니다.

**Review Radius**는 제품 이름이고, 저장소·스킬·호출 ID는 모두
`review-radius`입니다. 문체와 시각 규칙은
[한국어 브랜드 가이드](BRAND.ko.md), 언어별 용어와 표기 원칙은
[이름·언어 체계](docs/brand/naming-and-language.md)를 참고하세요.

## 라이선스

Review Radius는 [MIT License](LICENSE)에 따라 사용할 수 있습니다.
선택형 벤치마크가 호출하는 Graphify `graphifyy==0.9.32`의 명시 라이선스는
Apache License 2.0입니다. 원본 라이선스와 저작자 표시, 사용 범위는
[제3자 고지](THIRD_PARTY_NOTICES.md)를 참고하세요.

## 기여와 보안

1인 메인테이너를 고려한 PR 정책은 [CONTRIBUTING.md](CONTRIBUTING.md), 비공개
취약점 신고 방법은 [SECURITY.md](SECURITY.md)를 참고하세요.
