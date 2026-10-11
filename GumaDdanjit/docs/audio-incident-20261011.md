# 짧은 대사 음량 오류 수정 — 2026-10-11

사용자가 피자설기 Video 6의 CUT 3에서 음성이 들리지 않는다고 보고했다. 원본 WAV는 정상 신호였으나 GumaTTS worker의 단일 패스 동적 loudnorm 보정이 일부 짧은 대사를 크게 감쇠했다. 피자설기 CUT 3은 평균 -19.3dBFS 원본이 보정 후 -39.0dBFS로 낮아졌다. 이전 검수는 파일 해시·디코딩·전체 평균 음량에 의존해 컷별 이상을 놓쳤다.

## 확인 범위와 발견

- GumaShop 최신 ready 영상 12편의 88컷: 원본 음성, 컷 영상, 최종 내레이션 타임라인 및 최종 믹스 구간 검사.
- 이상 감쇠 5컷: 대추야자 Video 5 CUT 3·5, 누룽지팝 Video 4 CUT 5, 피자설기 Video 6 CUT 3·6.
- 미지아 Video 11 CUT 1·4의 원본 대비 신호 차이는 기존 속도 조정(1.036184배) 및 앞 무음 0.18초 제거 기록과 대조했다. 해당 편집을 적용하면 신호 패턴 유사도 0.99999 이상으로 일치하며 누락으로 판정하지 않았다.
- Story·GumaX 제작 폴더의 기존 MP3 120개도 디코딩·신호 음량 검사했다. 평균 -28dBFS 미만 파일은 없었다. 이는 단어 정확성이나 실제 청취 검수의 대체물이 아니다.

## 수정본

| 영상 | 보존한 이전 버전 | 수정 버전 |
|---|---:|---|
| 대추야자 | 5 | [Video 6](https://home.guma3d.com/gumaddanjit/shorts/ideas/3219f31dbcaf884c?video=6#Video) |
| 누룽지팝 | 4 | [Video 5](https://home.guma3d.com/gumaddanjit/shorts/ideas/12681a1f9b25c2e8?video=5#Video) |
| 피자설기 | 6 | [Video 7](https://home.guma3d.com/gumaddanjit/shorts/ideas/e9d3b5997cf329dd?video=7#Video) |

25컷 모두 보존된 F4 원본 WAV에서 측정 기반 고정 게인으로 다시 보정했다. 모델을 재생성하거나 유료 API를 사용하지 않았다. 새 MP3 해시와 원본 작업 ID를 연결하고, 컷 및 합성 타임라인 음량을 각각 검사했다. 영상 스트림 해시가 이전 버전과 동일하므로 화면·자막·전환·모든 프레임의 로고가 유지된다. 기존 BGM 파일과 고정 게인도 유지한다. 정확한 새 버전에 썸네일을 연결했다. YouTube는 변경하지 않았다.

GumaTTS는 보정 전후 LUFS·true peak와 예상 게인을 대조하고 무음·과도한 감쇠를 실패 처리한다. 작업 캐시 버전을 올려 이전 보정 결과가 새 요청에 재사용되지 않게 했다. 쇼핑 컷 합성에서는 각 컷의 내레이션 음량을 검사하여 -24 LUFS 미만을 차단한다. 실제 청취 여부는 계속 별도로 기록한다.

검사 원자료와 복구 스크립트는 `storage/shorts/handoffs/food-audio-fix-20261011/`, 오류 원본 분석은 `storage/shorts/handoffs/food-f4-20261011/audio-investigation.json`에 보존한다.
