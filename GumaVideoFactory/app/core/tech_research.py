"""Evidence gate for newly selected technology products; historical records stay readable."""


def validate_tech_evidence(item):
    data = item.model_dump() if hasattr(item, 'model_dump') else item
    if data.get('category') != 'tech':
        return
    evidence = data.get('tech_evidence') or {}
    videos = evidence.get('videos') or []
    if not videos:
        raise ValueError('테크 선정 1순위: 기술을 설명하는 기존 영상의 실제 확보·재생 검수 근거가 필요합니다.')
    for video in videos:
        if video.get('source_type') not in ('manufacturer_official', 'third_party'):
            raise ValueError('테크 영상의 제조사 공식/제3자 출처를 구분하세요.')
        if video['source_type'] == 'third_party' and video.get('creator_country') != 'CN':
            raise ValueError('제3자 테크 영상은 중국 제작 자료만 허용합니다. 게시 사이트 국가로 대체하지 마세요.')
        for field in ('source_url', 'publisher_evidence', 'local_path', 'sha256',
                      'technical_content', 'used_range', 'playback_review', 'reuse_permission_evidence'):
            if not str(video.get(field) or '').strip():
                raise ValueError(f'테크 확보 영상 근거 누락: {field}')
    if not evidence.get('official_search_evidence'):
        raise ValueError('제조사 공식 기술 영상 우선 조사 근거가 필요합니다.')
    if not any(v['source_type'] == 'manufacturer_official' for v in videos) and not evidence.get('official_unavailable_reason'):
        raise ValueError('중국 제3자 영상 선택에는 적합한 공식 영상 미확보 사유가 필요합니다.')
