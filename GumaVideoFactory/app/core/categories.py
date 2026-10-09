"""Category identities shared by research, UI and final rendering."""
SLOT_CATEGORIES = {'09:00': 'tech', '15:00': 'food', '21:00': 'household'}
PRESETS = {
    'tech': dict(label='신형 테크', accent='37DEB4',
        style='Clean neutral technical editorial; generated lifestyle uses bright diffused low-contrast daylight. Exact official product closeups, measured callouts, restrained transitions.',
        direction='생활 문제를 기술 원리와 연결하고 핵심 기술·추가 기능 2개·실사용 한계를 근거로 설명한다.'),
    'food': dict(label='트렌드 음식', accent='FFBE73',
        style='Bright, soft, low-contrast food editorial. Vary ingredients, texture, unboxing, preparation, storage and serving; at most one cross-section shot. Preserve exact food and packaging; no invented tasting.',
        direction='뉴스·방송·해외 유행·판매 동향과 레시피를 조사해 로켓배송 완제품/재료로 연결. 검증된 관심 후킹 → 재료·질감 → 개봉·준비 → 제품별 보관·즐기는 장면 → CTA. 승인 콘티처럼 매 컷 소재·행동·구도를 바꾸고 단면은 최대 1컷. 제품별 적합한 과정만 사용하며 동일한 맛을 보장하지 않는다.'),
    'household': dict(label='생활용품', accent='87BFFF',
        style='Bright practical demonstration. Problem-before-use and verified result-after-use framing.',
        direction='판매·리뷰 지표 또는 최근 뉴스 원문으로 후보를 검증하고 생활 불편·계절성·디자인·선명한 동일 제품 시연 가능성을 함께 평가. 리뷰를 판매량으로 환산하지 않는다. 관심 후킹 → 실제 사용 시연 → 편리한 이유와 한계.'),
}
for preset in PRESETS.values():
    preset.update(font='Maplestory', voice='Zephyr', voice_direction='bright-friendly-female', voice_rate='natural-brisk', target_age='20-40', style_revision='category-v7',caption_design='common-pop-outline-v4',thumbnail_required=True)
PRESETS['food'].update(still_motion='static',storyboard_reference='docs/references/food-storyboard-approved-v1.png')
