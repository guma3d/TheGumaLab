"""Evidence gate for newly selected technology products; historical records stay readable."""


def validate_tech_visual_plan(category, board):
    """Gate new production only; metadata supplements, never replaces visual review."""
    if category != 'tech':
        return
    data = board.model_dump() if hasattr(board, 'model_dump') else board
    if data.get('needs_3d') or data.get('veo_transition'):
        raise ValueError('테크는 imagegen 고정 카메라 방식만 사용합니다. 3D·영상 생성 전환은 금지합니다.')
    for scene in data.get('scenes', []):
        visual = scene.get('tech_visual') or {}
        if scene.get('mode', scene.get('visual_mode')) not in ('explanatory_image', 'illustration_clip'):
            raise ValueError('테크 비주얼은 imagegen 이미지 또는 해당 이미지의 일반 편집 합성만 사용합니다.')
        if visual.get('generator') != 'imagegen' or visual.get('camera') != 'fixed':
            raise ValueError('테크는 imagegen·fixed 카메라 이력이 필요합니다.')
        for field in ('reference_evidence', 'base_image', 'edit_lineage', 'consistency_review'):
            if not str(visual.get(field) or '').strip():
                raise ValueError(f'테크 고정 카메라 검수 근거 누락: {field}')


def validate_tech_evidence(item):
    data = item.model_dump() if hasattr(item, 'model_dump') else item
    if data.get('category') != 'tech':
        return
    evidence = data.get('tech_evidence') or {}
    purchase = data.get('purchase_link') or {}
    if not purchase.get('affiliate_url') or not purchase.get('affiliate_evidence'):
        raise ValueError('테크 선정 필수 조건: 동일 제품·옵션의 실제 발급 파트너스 링크와 근거가 필요합니다.')
    fit = evidence.get('market_fit') or {}
    if fit.get('basis') not in ('popularity', 'season', 'trend', 'current_event') or any(
        not str(fit.get(key) or '').strip() for key in ('reason', 'source_url', 'checked_at')
    ):
        raise ValueError('테크는 인기 또는 현재 계절·트렌드·화제성의 확인 근거가 필요합니다.')
    videos = evidence.get('videos') or []
    images = evidence.get('images') or []
    if not (videos or images):
        raise ValueError('테크 제작 등록에는 기술 설명 기존 영상 또는 이미지의 실제 확보·검수 근거가 필요합니다.')
    for video in videos + images:
        if video.get('source_type') not in ('manufacturer_official', 'third_party'):
            raise ValueError('테크 영상의 제조사 공식/제3자 출처를 구분하세요.')
        if video['source_type'] == 'third_party' and video.get('creator_country') != 'CN':
            raise ValueError('제3자 테크 영상은 중국 제작 자료만 허용합니다. 게시 사이트 국가로 대체하지 마세요.')
        for field in ('source_url', 'publisher_evidence', 'local_path', 'sha256',
                      'technical_content', 'reuse_permission_evidence'):
            if not str(video.get(field) or '').strip():
                raise ValueError(f'테크 확보 영상 근거 누락: {field}')
        required = ('used_range', 'playback_review') if video in videos else ('visual_review',)
        if any(not str(video.get(field) or '').strip() for field in required):
            raise ValueError('테크 자료의 실제 구간 재생 또는 이미지 시각 검수 근거가 필요합니다.')
    if not evidence.get('official_search_evidence'):
        raise ValueError('제조사 공식 기술 영상 우선 조사 근거가 필요합니다.')
    if not any(v['source_type'] == 'manufacturer_official' for v in videos + images) and not evidence.get('official_unavailable_reason'):
        raise ValueError('중국 제3자 영상 선택에는 적합한 공식 영상 미확보 사유가 필요합니다.')
