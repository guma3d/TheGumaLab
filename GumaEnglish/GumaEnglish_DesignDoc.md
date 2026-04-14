# GumaEnglish — App Design Document

> **AI 로봇 친구와 함께하는 초등 영어 패턴 학습 앱**  
> 대상: 초등 저학년 (7~9세) / 플랫폼: iOS / 엔진: Unreal Engine 5

---

## 1. 앱 개요

### 핵심 철학
> "영어 대화의 핵심은 자주 쓰는 패턴 문장을 몸에 익히는 것이다.  
> 패턴을 외우면 말할 수 있고, 들을 수 있다."

아이들이 매주 5개의 핵심 패턴 문장을 배우고, AI 로봇 캐릭터와 대화 연습을 통해 자연스럽게 체화한다.  
매주 테스트를 통과하면 코인을 획득하고, 코인으로 나만의 로봇을 꾸밀 수 있다.

### 한 줄 요약
**"배우고 → 대화하고 → 테스트하고 → 로봇을 키운다"**

---

## 2. 핵심 기능 구조

```
[매일] 패턴 문장 학습 + AI 로봇과 대화 연습
              ↓
[매주 토요일] 주간 테스트 (퀴즈 + AI 대화)
              ↓
         🪙 코인 획득
              ↓
       🛒 로봇 부품 상점
              ↓
       🤖 나만의 로봇 완성
```

---

## 3. 2주 학습 사이클 (1단계 기준)

| 요일 | 1주차 | 2주차 |
|------|-------|-------|
| 월 | 이번 단계 패턴 문장 전체 소개 + 1번 문장 학습 | 전체 문장 복습 + 1번 문장 심화 대화 |
| 화 | 2번 문장 학습 + AI 로봇과 짧은 대화 | 2번 문장 심화 대화 |
| 수 | 3번 문장 학습 + AI 로봇과 짧은 대화 | 3번 문장 심화 대화 |
| 목 | 전체 복습 + 자유 대화 연습 | 전체 복습 + 자유 대화 연습 |
| 금 | 복습 + 약한 문장 집중 연습 | 복습 + 약한 문장 집중 연습 |
| 토 | 🎯 1차 주간 테스트 | 🎯 2차 주간 테스트 (최종) |
| 일 | 🛒 코인으로 로봇 부품 구매 | 🎉 단계 진급 + 진급 보너스 코인 |

> 4단계 이상부터는 목~금요일에 추가 문장(4번, 5번...) 학습이 더해짐

---

## 4. 학습 화면 설계

### 4-1. 패턴 문장 학습
- 오늘의 패턴 문장 카드 표시 (예: `"Can I have a ___?"`)
- 원어민 음성 듣기 버튼
- 따라 말하기 (음성 인식)
- 빈칸 채우기로 문장 완성 연습

### 4-2. AI 로봇 대화 연습
- AI 로봇이 오늘 배운 패턴이 **자연스럽게 나올 수밖에 없는 상황**을 만들어 줌
- 예시 시나리오:

  > 🤖 로봇: *"We're at a snack shop! What do you want?"*  
  > 👧 아이: *"Can I have a cookie?"*  
  > 🤖 로봇: *"Great choice! Here's your cookie! 🍪"*

- 틀려도 바로 지적하지 않고, 자연스럽게 올바른 표현으로 대화를 이어감
- 대화 후 간단한 피드백 ("You used the pattern perfectly! ⭐")

---

## 5. 주간 테스트 시스템

### 테스트 구성 (복합 방식)

**파트 1 — 퀴즈 (5문제)**
- 빈칸 채우기: `"Can I ___ a cookie?"` → have
- 알맞은 문장 고르기 (4지선다)
- 한국어 보고 영어 문장 완성하기

**파트 2 — AI 대화 테스트 (2~3 턴)**
- AI가 실제 대화 상황을 만들어 줌
- 이번 주 배운 패턴 문장을 자연스럽게 사용하면 통과
- AI가 사용 여부를 판단하여 점수 부여

**합격 기준**
- 퀴즈 4/5 이상 + 대화에서 패턴 문장 2회 이상 사용 → 통과
- 통과 시: 🪙 코인 10개 지급
- 불통과 시: 재도전 가능 (일요일까지), 코인 5개 지급

---

## 6. 로봇 커스터마이징 시스템

### 파츠 획득 방식 (코인 없음)

테스트를 통과하면 코인 없이 **파츠를 직접 선택**해서 획득한다.

- 각 단계(2주)마다 테스트 **2회** 진행
- 테스트 통과 시 → 해당 로봇의 파츠 목록 중 **1개 선택**
- 10단계 동안 최대 **10개의 파츠** 획득 가능 → 로봇 풀 완성
- 테스트 불통과 시 → 재도전 가능, 통과하면 파츠 선택 가능

### 3D 에셋 — Synty Studios POLYGON Mech Pack

- 구매처: **syntystore.com** 또는 **Fab.com** (Unity/Unreal 호환)
- 가격: $99 (개별 구매) 또는 $30/월 Synty 구독
- 총 104개 메카 파츠 포함 → 10단계 × 10파츠로 배분 가능

### 로봇별 파츠 10종 구성 (Synty Mech Pack 기반)

104개 파츠를 단계별 10개씩 배정. 단계가 높아질수록 강력하고 멋있는 파츠 잠금 해제:

| 파츠 번호 | 부위 | Synty 파츠 예시 |
|----------|------|----------------|
| 1 | 머리 | Head (기본형 → 단계별 고급형) |
| 2 | 어깨 | Shoulder Armour |
| 3 | 팔꿈치 | Elbow Armour |
| 4 | 팔 무기 | Arm Weapon (카타나/로켓/캐논) |
| 5 | 손 | Hand Armour |
| 6 | 허벅지 | Upper Leg Armour |
| 7 | 무릎 | Knee Armour |
| 8 | 정강이 | Shin Armour |
| 9 | 등/제트팩 | Jetpack / Saddlebags |
| 10 | 특수 무기 | Gatling Gun / Sword / Rocket |

> 단계가 높아질수록 더 강력한 파츠 배정 — 1단계는 기본 헬멧, 10단계는 개틀링건 장착

### 로봇 진화 시스템 (10단계마다 새 로봇으로 교체)

10단계를 완료하면 로봇이 상위 로봇으로 진화한다. 이전 로봇은 **창고**에 보관되어 수집 목록으로 열람 가능하다.

| 로봇 이름 | 단계 | 등급 | 테마 |
|----------|------|------|------|
| 🤖 Tinbot  | 1~10단계   | ⭐ 입문        | 깡통 로봇, 소박하고 귀여운 기본형 |
| ⚡ Sparky  | 11~20단계  | ⭐⭐ 초급       | 전기 스파크, 활발하고 에너지 넘침 |
| 🌊 Aqua    | 21~30단계  | ⭐⭐⭐ 초중급    | 물/해양 테마, 차분하고 지적 |
| 🔥 Blaze   | 31~40단계  | ⭐⭐⭐⭐ 중급    | 불꽃 테마, 열정적이고 강렬함 |
| 🌿 Lush    | 41~50단계  | ⭐⭐⭐⭐⭐ 중고급 | 자연 테마, 지혜롭고 따뜻함 |
| 🚀 Rocket  | 51~60단계  | 🔥 고급        | 우주/로켓 테마, 목표 지향적 |
| ❄️ Frost   | 61~70단계  | 🔥🔥 고급+     | 얼음 테마, 냉정하지만 속은 따뜻함 |
| ⚡ Thunder | 71~80단계  | 🔥🔥🔥 심화    | 폭풍/번개 테마, 강인하고 믿음직 |
| 🌌 Cosmos  | 81~90단계  | 🔥🔥🔥 마스터  | 은하 테마, 신비롭고 깊은 지혜 |
| 👑 Legend  | 91~100단계 | 🏆 전설        | 황금빛 전설 로봇, 모든 것의 완성 |

### 파츠 시스템 (진화 시 초기화)
- 로봇이 진화하면 장착 중이던 파츠는 **자동 초기화**
- 새 로봇 전용 파츠를 코인으로 다시 구매
- 각 로봇마다 **고유 파츠 디자인** 존재 (Tinbot 파츠 ≠ Sparky 파츠)
- 전설 로봇(Legend)은 특수 파츠만 장착 가능

### 나의 로봇 창고
- 10단계를 완료한 로봇은 장착 파츠 그대로 **창고에 자동 보관**
- 창고에서 과거 로봇 열람 가능 (추억 보존용, 파츠 재활용 불가)
- 최종적으로 10종 로봇 수집이 목표

### 로봇 커스터마이징 화면
- 파츠를 탭해서 장착/교체
- 완성된 로봇은 메인 홈 화면에 항상 표시
- 로봇 이름 직접 짓기 가능
- 주간 테스트 때 내 로봇이 응원해줌 ("You can do it! Let's go! 🤖")

### 로봇 진화 이벤트 (10단계 달성 시)
- 화려한 진화 애니메이션 재생
- 현재 로봇 → 창고로 이동
- 새 로봇 등장 + 파츠 슬롯 10개 초기화
- 🏆 100단계 달성 시: 전설 로봇 Legend 등장 + 특수 파츠 전체 해금

---

## 7. 100단계 레벨 시스템

### 기본 구조
- 각 단계는 **2주** 단위로 구성
- 단계가 높아질수록 **문장 수**와 **난이도** 함께 증가
- 100단계 완주 = 약 **200주 (4년)** 분량의 커리큘럼
- 전체 단계를 8개 구간으로 나눠 난이도 그룹 관리

### 단계별 문장 수 & 난이도 구간

| 구간 | 단계 | 문장 수 | 난이도 레벨 | 학습 목표 |
|------|------|--------|------------|----------|
| 1구간 | 1 ~ 14단계 | 3개 | ⭐ 입문 | 기본 표현, 짧은 문장, 단어 중심 |
| 2구간 | 15 ~ 28단계 | 4개 | ⭐⭐ 초급 | 간단한 패턴, 일상 표현 |
| 3구간 | 29 ~ 42단계 | 5개 | ⭐⭐⭐ 초중급 | 문장 구조 확장, 의문문/부정문 |
| 4구간 | 43 ~ 56단계 | 6개 | ⭐⭐⭐⭐ 중급 | 복합 패턴, 감정/의견 표현 |
| 5구간 | 57 ~ 70단계 | 7개 | ⭐⭐⭐⭐⭐ 중고급 | 시제 변화, 조건/이유 표현 |
| 6구간 | 71 ~ 84단계 | 8개 | 🔥 고급 | 관계절, 간접화법, 복문 |
| 7구간 | 85 ~ 92단계 | 9개 | 🔥🔥 심화 | 숙어, 뉘앙스, 자연스러운 표현 |
| 8구간 | 93 ~ 100단계 | 10개 | 🔥🔥🔥 마스터 | 원어민 수준 패턴, 복잡한 대화 |

### 구간별 상세 커리큘럼 예시

#### ⭐ 1구간 (1~14단계) — 입문 / 문장 3개
| 단계 | 테마 | 패턴 문장 예시 |
|------|------|--------------|
| 1 | 원하는 것 말하기 | I want ~, Can I have ~?, I need ~ |
| 2 | 좋아하는 것 말하기 | I like ~, I love ~, My favorite is ~ |
| 3 | 인사와 소개 | My name is ~, I am ~, Nice to meet ~ |
| 4 | 위치 말하기 | It's in ~, It's on ~, Where is ~? |
| 5 | 숫자/나이 | I am ___ years old, There are ~, I have ~ |
| 6~14 | 색깔, 동물, 음식, 날씨 등 기초 주제 | (단계별 3개 패턴) |

#### ⭐⭐ 2구간 (15~28단계) — 초급 / 문장 4개
| 단계 | 테마 | 패턴 문장 예시 |
|------|------|--------------|
| 15 | 제안하기 | Let's ~, Shall we ~?, How about ~?, Want to ~? |
| 16 | 질문하기 | What is ~?, Where is ~?, Can you ~?, Who is ~? |
| 17 | 감정 표현 | I'm happy, I feel ~, I'm excited about ~, I'm sorry ~ |
| 18 | 일상 묘사 | I usually ~, Every day ~, In the morning ~, I always ~ |
| 19~28 | 학교생활, 가족, 취미, 음식 주문 등 | (단계별 4개 패턴) |

#### ⭐⭐⭐ 3구간 (29~42단계) — 초중급 / 문장 5개
| 단계 | 테마 | 패턴 문장 예시 |
|------|------|--------------|
| 29 | 과거 경험 | I went to ~, I ate ~, Yesterday I ~, I saw ~, It was ~ |
| 30 | 미래 계획 | I'm going to ~, I will ~, Tomorrow I ~, I want to ~ someday, Next week ~ |
| 31 | 비교하기 | ~ is bigger than ~, I like ~ more than ~, ~ is the best, ~ is faster, ~ is better |
| 32~42 | 날씨, 쇼핑, 여행, 건강 등 | (단계별 5개 패턴) |

#### ⭐⭐⭐⭐ 4구간 (43~56단계) — 중급 / 문장 6개
- 현재진행형 (`I am ~ing`), 현재완료 (`I have ~ed`) 패턴 도입
- 의견 표현: `I think ~, In my opinion ~, I believe ~`
- 이유 설명: `Because ~, That's why ~, The reason is ~`

#### ⭐⭐⭐⭐⭐ 5구간 (57~70단계) — 중고급 / 문장 7개
- 조건문: `If ~ , then ~`, `Unless ~`
- 시제 복합: `I had been ~`, `I will have ~`
- 간접 의문문: `I wonder if ~`, `Do you know what ~?`

#### 🔥 6구간 (71~84단계) — 고급 / 문장 8개
- 관계절: `The one who ~`, `Something that ~`
- 가정법: `I wish I could ~`, `If I were ~`
- 수동태: `It was made by ~`, `I was told that ~`

#### 🔥🔥 7구간 (85~92단계) — 심화 / 문장 9개
- 숙어 및 관용 표현: `It's up to ~`, `I'm looking forward to ~`
- 뉘앙스 표현: `I'd rather ~`, `I suppose ~`, `Apparently ~`
- 자연스러운 연결: `By the way ~`, `Come to think of it ~`

#### 🔥🔥🔥 8구간 (93~100단계) — 마스터 / 문장 10개
- 복잡한 복문 패턴
- 원어민이 실제로 쓰는 구어체 표현
- 토론/발표 수준의 문장 구조

---

### 단계 진급 조건
- 해당 단계의 **2주 학습 완료** (매일 출석 10일 이상)
- **주간 테스트 2회** 모두 합격 (또는 재도전 합격)
- 두 조건 충족 시 자동으로 다음 단계로 진급 🎉
- 10단계 단위 진급 시 → 로봇 진화 이벤트 발생

---

## 8. 화면 구성 (Screen Flow)

```
[홈 화면]
  ├── 내 로봇 표시 (현재 파츠 장착 상태)
  ├── 이번 단계 진행률 (예: "3/10 파츠 획득")
  ├── 현재 단계 표시 (예: "3단계 / Tinbot")
  ├── [오늘 학습 시작] 버튼
  └── [테스트] / [대화 연습] / [창고] 탭

[학습 화면]
  ├── 오늘의 패턴 문장 카드
  ├── 음성 듣기
  ├── 따라 말하기
  └── 빈칸 채우기 연습

[대화 화면]
  ├── 로봇 캐릭터 (말풍선)
  ├── 텍스트 입력 or 음성 입력
  └── 대화 히스토리

[테스트 화면]
  ├── 파트 1: 퀴즈 5문제
  ├── 파트 2: AI 대화 테스트
  └── 결과 화면 (파츠 선택 애니메이션 🎉)

[파츠 선택 화면]
  ├── 통과 축하 메시지
  ├── 이번 로봇의 남은 파츠 목록 표시
  └── 1개 선택 → 즉시 로봇에 장착

[로봇 꾸미기 화면]
  ├── 로봇 프리뷰 (획득한 파츠만 표시)
  ├── 미획득 파츠는 잠금 표시
  └── 획득 파츠 간 배치 조정 가능

[로봇 창고 화면]
  ├── 수집한 로봇 목록 (잠금/해금 표시)
  ├── 각 로봇 상세 보기 (장착 파츠 포함)
  └── 진화 히스토리 타임라인
```

---

## 9. AI 연동 설계

### 사용 AI: Google Gemini API (무료 티어)

**왜 Gemini API인가?**
- 무료 티어 제공 (가정용으로 충분한 호출 한도)
- API 키 발급: [Google AI Studio](https://aistudio.google.com) 에서 무료 발급
- 사용 모델: `gemini-1.5-flash` (무료 티어, 빠른 응답)

**무료 티어 한도 (2026년 기준)**
- 분당 15회 요청
- 하루 1,500회 요청
- 가정 내 아이 1~2명 사용 기준으로 충분

### AI 역할
1. **대화 연습 파트너**: 오늘의 패턴이 자연스럽게 나오도록 대화 상황 유도
2. **테스트 평가자**: 아이의 답변에서 패턴 문장 사용 여부 판단
3. **피드백 제공자**: 긍정적이고 격려하는 방식으로 피드백

### UE5에서 Gemini API 호출 방법

```cpp
// UE5 HTTP 모듈로 Gemini API 호출
// Blueprint에서도 동일하게 구현 가능

FHttpModule* Http = &FHttpModule::Get();
TSharedRef<IHttpRequest> Request = Http->CreateRequest();

FString URL = "https://generativelanguage.googleapis.com/v1beta/models/"
              "gemini-1.5-flash:generateContent?key=YOUR_API_KEY";

Request->SetURL(URL);
Request->SetVerb("POST");
Request->SetHeader("Content-Type", "application/json");
Request->SetContentAsString(JsonBody);
Request->OnProcessRequestComplete().BindUObject(
    this, &UGeminiComponent::OnResponseReceived);
Request->ProcessRequest();
```

### AI 시스템 프롬프트 (기본 방향)
```
You are Guma, a friendly robot who loves talking with children aged 7-9.
Your goal is to naturally guide the child to use this week's pattern sentences.
- Always be encouraging and positive
- Never directly correct mistakes; instead, model the correct form naturally
- Keep sentences short and simple
- Use fun emojis and exclamations
- This week's patterns: [패턴 목록 동적 삽입]
```

### 향후 전환 옵션
| 상황 | 대안 |
|------|------|
| 무료 한도 초과 시 | Gemini API 유료 전환 (매우 저렴) |
| 인터넷 없이 사용하고 싶을 때 | Ollama 로컬 모델로 전환 (같은 WiFi 필요) |
| 품질 업그레이드 원할 때 | Claude API 유료 전환 |

---

## 10. 기술 스택

| 영역 | 기술 |
|------|------|
| 게임 엔진 | Unreal Engine 5 (UE5) |
| 3D 에셋 | Synty Studios POLYGON Mech Pack |
| UI 프레임워크 | UMG (Unreal Motion Graphics) |
| 로직 | Blueprint (+ C++ 선택적) |
| AI 대화 | Google Gemini API (gemini-1.5-flash, 무료) |
| AI 연동 | UE5 HTTP 모듈 (FHttpModule) |
| 파츠 시스템 | UE5 Socket & Attach Component |
| 애니메이션 | UE5 Sequencer + Mecanim 리깅 |
| 음성 인식 | iOS Speech Framework (UE5 플러그인) |
| 음성 합성 | iOS AVSpeechSynthesizer (UE5 플러그인) |
| 로컬 저장 | UE5 SaveGame 시스템 |
| 빌드/배포 | UE5 iOS 패키징 → App Store |

### UE5에서 Gemini API 호출 방법 (Blueprint + HTTP)

```cpp
// C++ 또는 Blueprint HTTP Request로 구현
FHttpModule* Http = &FHttpModule::Get();
TSharedRef<IHttpRequest> Request = Http->CreateRequest();
Request->SetURL("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent");
Request->SetVerb("POST");
Request->SetHeader("Content-Type", "application/json");
Request->SetContentAsString(JsonBody);
Request->ProcessRequest();
```

### UE5 파츠 시스템 구현 방식
```
베이스 메카 Skeletal Mesh
    ↓
각 파츠 → Socket에 Attach
(Head_Socket, Shoulder_L_Socket, ...)
    ↓
파츠 획득 시 → Socket에 StaticMesh Attach
파츠 미획득 → 해당 Socket 비활성화
```

---

## 11. 개발 Phase 계획

### 개발 철학
> "작게 만들고, 검증하고, 키워라"
> 각 Phase는 **독립적으로 완성된 결과물**을 목표로 한다.
> Phase가 끝날 때마다 아이에게 실제로 써보게 하고 피드백을 반영한다.

---

### Phase 0 — 환경 세팅 (1~2주)
**목표**: 개발 시작 전 모든 준비 완료

- [ ] Synty POLYGON Mech Pack 구매 및 UE5 임포트
- [ ] UE5 iOS 빌드 환경 세팅 (Xcode, Apple Developer 인증서)
- [ ] Gemini API 키 발급 (aistudio.google.com)
- [ ] Scout 로봇 베이스 메카 UE5에서 동작 확인
- [ ] Socket 포인트 설정 (Head, Shoulder, Arm, Leg, Back, Weapon)

**완료 기준**: UE5에서 Scout 로봇이 화면에 표시되고 파츠 1개를 붙일 수 있다.

---

### Phase 1 — MVP "돌아가는 것" (4~6주)
**목표**: 아이가 실제로 써볼 수 있는 최소 버전

**로봇**
- [ ] Scout 로봇 1종만 사용
- [ ] 파츠 3개만 구현 (Head, Shoulder, Arm Weapon)
- [ ] 홈 화면 — Scout 3D 표시 + 현재 단계 표시

**학습**
- [ ] 1단계 패턴 문장 3개 학습 화면
- [ ] Gemini API 연동 — AI 로봇과 영어 대화

**보상**
- [ ] 테스트 통과 시 파츠 1개 선택 화면 (3개 중 선택)
- [ ] SaveGame으로 진행 상태 저장

**완료 기준**: 아이가 1단계를 처음부터 끝까지 플레이하고 파츠를 1개 받을 수 있다.

> ✅ **이 시점에 아이에게 테스트** — "재미있어?" "로봇 더 꾸미고 싶어?" 반응 확인

---

### Phase 2 — 핵심 게임루프 완성 (6~8주)
**목표**: 1~10단계(Scout 완주)가 완전히 동작

**로봇 & 파츠**
- [ ] Scout 파츠 10개 전체 구현
- [ ] 파츠 획득 시 장착 애니메이션
- [ ] 로봇 3D 뷰어 — 터치로 회전/확대

**학습**
- [ ] 1~10단계 패턴 문장 커리큘럼 콘텐츠 입력
- [ ] 주간 테스트 완성 (퀴즈 5문제 + AI 대화 평가)
- [ ] 2주 학습 사이클 타이머 및 진행률 관리

**진화**
- [ ] 10단계 달성 시 진화 이벤트 연출 (Sequencer)
- [ ] Guardian 로봇 등장 (2번째 로봇 프리뷰)

**완료 기준**: 아이가 Scout를 풀 완성하고 Guardian으로 진화하는 경험을 할 수 있다.

> ✅ **2차 아이 테스트** — 진화 순간의 반응이 핵심. "우와!" 소리가 나야 성공

---

### Phase 3 — 로봇 5종 확장 (8~10주)
**목표**: Scout ~ Frost (1~50단계) 완성

- [ ] Guardian, Striker, Blaze, Frost 로봇 4종 추가
- [ ] 각 로봇별 파츠 10개 + 색상 텍스처 제작
- [ ] 1~50단계 커리큘럼 콘텐츠 완성
- [ ] 창고 화면 — 완료한 로봇 수집 목록
- [ ] Synty FX 적용 (Blaze 불꽃, Frost 얼음 이펙트)
- [ ] iOS 기기 테스트 빌드

**완료 기준**: 50단계까지 플레이 가능한 완성도 높은 버전.

> ✅ **가족 외 아이에게도 테스트** (친구 자녀 등) — 낯선 아이도 혼자 할 수 있는가?

---

### Phase 4 — 전체 완성 (10~12주)
**목표**: 10종 로봇, 100단계 전체 완성

- [ ] Thunder, Stealth, Titan, Phantom, Sovereign 5종 추가
- [ ] 51~100단계 커리큘럼 완성
- [ ] 음성 인식 추가 (따라 말하기)
- [ ] 부모 확인 화면 (학습 기록 + 진행 현황)
- [ ] Sovereign 전설 진화 이벤트 (가장 화려하게)
- [ ] 앱 아이콘, 스플래시, 온보딩 화면

**완료 기준**: App Store 제출 가능한 완성본.

---

### Phase 5 — 출시 & 개선 (지속)
**목표**: App Store 출시 후 지속 업데이트

- [ ] App Store 제출 및 심사
- [ ] 사용자 피드백 수집
- [ ] 버그 수정 및 콘텐츠 추가
- [ ] 커리큘럼 고도화 (패턴 문장 품질 개선)

---

### 전체 타임라인 요약

| Phase | 내용 | 예상 기간 | 결과물 |
|-------|------|----------|--------|
| 0 | 환경 세팅 | 1~2주 | 개발 환경 완비 |
| 1 | MVP | 4~6주 | Scout 1단계 플레이 가능 |
| 2 | 핵심 루프 | 6~8주 | Scout 10단계 완주 + 진화 |
| 3 | 5종 확장 | 8~10주 | 50단계까지 플레이 가능 |
| 4 | 전체 완성 | 10~12주 | 100단계 완성본 |
| 5 | 출시 | 지속 | App Store 출시 |

**총 예상 기간: 약 7~10개월** (주말 개발 기준)

---

### Phase별 핵심 원칙

**"각 Phase마다 반드시 아이에게 써보게 한다"**
아이의 반응이 가장 정직한 피드백이다. 어른 눈에 완성도가 낮아 보여도 아이가 재미있으면 성공이고, 아이가 흥미를 잃으면 방향을 바꿔야 한다.

**"콘텐츠(커리큘럼)와 기술(개발)을 병행한다"**
개발만 하다 보면 콘텐츠가 부족해서 테스트를 못 하고, 콘텐츠만 만들다 보면 개발이 늦어진다. Phase 1~2는 개발 집중, Phase 3~4는 콘텐츠 병행으로 진행한다.

**"완벽한 Phase 4보다 빠른 Phase 1이 낫다"**
Phase 1을 빨리 끝내고 아이 반응을 보는 것이 수개월을 혼자 개발하다 방향을 잃는 것보다 훨씬 낫다.

---

## 12. 성공 지표

- 아이가 **매일 자발적으로** 앱을 열고 싶어하는가?
- 8주 후 아이가 배운 패턴 문장을 **일상에서 자연스럽게** 사용하는가?
- 로봇 꾸미기 욕구가 **학습 지속성**으로 이어지는가?

---

*문서 작성일: 2026년 4월 | 버전: v1.6 (개발 Phase 0~5 상세 계획 추가)*
