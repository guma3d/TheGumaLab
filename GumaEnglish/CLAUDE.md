# GumaEnglish — CLAUDE.md

> Context document for Claude to understand and assist with the GumaEnglish project.

---

## Project Overview

**GumaEnglish** — iOS English learning app for kids (ages 7-9).
Kids learn pattern sentences by chatting with AI mech robot characters.
Pass tests to earn robot parts and build your own mech robot.

**Core philosophy**: Master frequently-used pattern sentences. Memorize patterns → speak & listen.

---

## Tech Stack

| Area | Tech |
|------|------|
| Engine | Unreal Engine 5 (5.3+) |
| 3D Assets | Synty Studios POLYGON Mech Pack |
| UI | UMG (Unreal Motion Graphics) |
| Logic | Blueprint (C++ only when needed) |
| AI Chat | Google Gemini API (gemini-1.5-flash) |
| AI Integration | UE5 HTTP Module (FHttpModule) |
| Parts System | UE5 Socket & Attach Component |
| Animation | UE5 Sequencer |
| Save | UE5 SaveGame |
| Build | UE5 → iOS → App Store |

---

## Project Structure

```
GumaEnglish/
├── Content/
│   ├── Robots/          # 10 robots (Scout~Sovereign), 10 stages each
│   ├── Parts/           # Parts Static Meshes
│   ├── UI/              # WBP_Home, WBP_Learning, WBP_Chat, WBP_Test,
│   │                    # WBP_PartSelect, WBP_RobotView, WBP_Garage
│   ├── Blueprints/      # BP_RobotBase, BP_PartsSystem, BP_GeminiAPI,
│   │                    # BP_GameManager, BP_SaveManager, BP_LevelManager
│   ├── Curriculum/      # DA_Stage_001 ~ DA_Stage_100
│   └── FX/              # Synty FX effects
└── Config/
    └── GeminiConfig.ini # API key (DO NOT commit to git)
```

---

## Core Systems

### Stage System (100 stages)
- Each stage = 2 weeks. Learn patterns → AI chat practice → 2 weekly tests
- Test pass → select 1 part. Every 10 stages → robot evolution
- Pattern count scales: 3 (stage 1-14) → 10 (stage 93-100)

### Robot Evolution (10 types)
| Robot | Stages | Type |
|-------|--------|------|
| Scout | 1-10 | Recon |
| Guardian | 11-20 | Defense |
| Striker | 21-30 | Offense |
| Blaze | 31-40 | Flame |
| Frost | 41-50 | Ice |
| Thunder | 51-60 | Storm |
| Stealth | 61-70 | Stealth |
| Titan | 71-80 | Heavy Armor |
| Phantom | 81-90 | Energy |
| Sovereign | 91-100 | Legendary |

### Parts System
- 10 slots per robot: Head, Shoulder, Elbow, Arm Weapon, Hand, Upper Leg, Knee, Shin, Back/Jetpack, Special Weapon
- Socket-based attach (Synty Mech Pack)
- On evolution: parts reset, previous robot stored in garage

### AI Chat (Gemini API)
- Model: `gemini-1.5-flash` (free tier: 15/min, 1,500/day)
- API key loaded from `Config/GeminiConfig.ini` — never hardcode
- Always include error handling for response parsing

---

## Naming Convention

```
Blueprint:   BP_Name        (e.g. BP_RobotBase)
Widget:      WBP_Name       (e.g. WBP_Home)
DataAsset:   DA_Name        (e.g. DA_Stage_001)
Struct:      FName          (e.g. FPatternData)
Enum:        EName          (e.g. ERobotType)
Interface:   IName          (e.g. IInteractable)
```

---

## Development Rules for Claude

- **Blueprint first**, C++ only for performance-critical code
- Target: UE5 5.3+, iOS build (mobile optimization always)
- SaveGame: always use `UGumaSaveGame` class
- UI: UMG Widget Blueprint, iPhone resolution (1170x2532), touch-friendly (min 44pt buttons)
- Gemini API key: read from config file, never hardcode

---

## Dev Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Environment Setup | In Progress |
| 1 | MVP (Scout Stage 1) | Waiting |
| 2 | Core Loop (Scout complete + evolution) | Waiting |
| 3 | 5 Robots (Stages 1-50) | Waiting |
| 4 | Full 100 Stages | Waiting |
| 5 | Release | Waiting |

### Current: Phase 0
- [ ] Import Synty Mech Pack into UE5
- [ ] Display Scout base mech on screen
- [ ] Set up 6 socket points
- [ ] Gemini API key + HTTP test
- [ ] UE5 iOS build setup (Xcode)
