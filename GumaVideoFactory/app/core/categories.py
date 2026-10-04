"""Category identities shared by research, UI and final rendering."""
SLOT_CATEGORIES = {'09:00': 'tech', '15:00': 'food', '21:00': 'household'}
PRESETS = {
    'tech': dict(label='신형 테크', accent='37DEB4',
        style='Clean dark technical editorial. Exact official product closeups, measured callouts, restrained transitions.',
        direction='생활 문제를 기술 원리와 연결하고 핵심 기술·추가 기능 2개·실사용 한계를 근거로 설명한다.'),
    'food': dict(label='트렌드 음식', accent='FFBE73',
        style='Warm authentic food closeups, real textures and cooking steps. No synthetic food or invented tasting.',
        direction='최근 음식 유행의 근거 → 쿠팡 완제품 또는 재료·조리법 → 즐기는 방법. 비교 근거 없이 동일한 맛·감동을 보장하지 않는다.'),
    'household': dict(label='생활용품', accent='87BFFF',
        style='Bright practical demonstration. Problem-before-use and verified result-after-use framing.',
        direction='생활 불편·계절 수요·신기한 쓰임 → 사용 시연 → 편리한 이유와 한계. 신제품·트렌드는 날짜와 근거를 검증한다.'),
}
for preset in PRESETS.values():
    preset.update(font='Noto Sans CJK KR', voice='ko-KR-HyunsuMultilingualNeural', voice_rate='+15%', target_age='20-40', style_revision='category-v2')
