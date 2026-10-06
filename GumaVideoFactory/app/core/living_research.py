"""Living discovery plan and evidence gates; original pages require human/agent inspection."""
from datetime import date, timedelta


def search_plan(today=None):
    today = today or date.today()
    since = (today - timedelta(days=7)).isoformat()
    return {
        'routes': ['commerce', 'news'],
        'queries': [
            {'route': 'commerce', 'query': '쿠팡 생활용품 정리 청소 구매 상품평'},
            {'route': 'news', 'query': f'생활용품 화제 신제품 판매 증가 after:{since}'},
        ],
        'review_preference': {'count': 500, 'rating_out_of_5': 4.3, 'hard_cutoff': False},
        'news_preferred_days': 7, 'news_maximum_days': 30,
        'recommendation_gate': {
            'applies_to': ['research_recommendations'],
            'required_order': ['verify_exact_product_media_acquisition', 'review_quality_and_required_action', 'recommend'],
            'download_required': False,
            'acquisition_verification_required': True,
            'production_readiness_validator': 'app.core.recommendation_readiness.validate_readiness',
            'unverified_items': 'internal_research_only',
        },
        'follow_up': [
            '정확한 옵션의 가격·판매처·로켓배송·파트너스 링크를 확인한다.',
            '판매량/구매자 수는 표시 문구·기간·범위·확인 시각을 보존한다. 리뷰 수로 판매량을 추정하지 않는다.',
            '리뷰 500개·평점 4.3 이상은 탐색 우선값이며 카테고리별 비교와 최근/낮은 평점 후기 내용도 확인한다.',
            '뉴스는 원문 게시일과 사건일을 구분하고 재배포 보도자료를 독립 근거로 중복 집계하지 않는다.',
            '리뷰가 적은 신제품도 최근 뉴스 근거로 검토하되 판매 검증 부족을 표시한다.',
            '동일 제품 자료의 실제 확보 경로와 근거를 검증해야 추천한다. 사전 일괄 다운로드는 필수가 아니지만 검색 결과·재생 가능·썸네일만으로 확보 가능이라 판단하지 않는다.',
            '출처·동일 제품 판단·확보 방법/검증 근거·해상도·육안 화질을 기록한다. 짧은 변 720px 이상, 1080p 우선. 작동 시연이 필요한 제품은 선명한 실제 작동 영상과 구간까지 검수한다.',
            '확보 경로 미검증·저화질·필수 작동 장면 미확인 제품은 추천에서 제외한다. 사용 허가와 확보 여부는 구분하고 제작 등록 때 기존 readiness 원본 확보·검수도 적용한다.',
        ],
    }


def validate_living_evidence(evidence, today):
    if evidence is None:
        raise ValueError('생활 신규 추천은 living_evidence 판매·리뷰 또는 뉴스 근거가 필요합니다.')
    usable = [m for m in evidence.media if m.acquisition_verified
              and len(m.acquisition_method.strip()) >= 5
              and len(m.acquisition_evidence.strip()) >= 10
              and m.visually_reviewed and min(m.width, m.height) >= 720]
    if not usable:
        raise ValueError('생활 추천은 동일 제품의 고화질 자료 확보 경로와 검증 근거가 필요합니다. 존재·재생 확인만으로 추천할 수 없습니다.')
    if evidence.requires_real_action and not any(
            m.kind == 'video' and m.real_action_reviewed and m.action_segment.strip() for m in usable):
        raise ValueError('실사용 시연 제품은 확보 가능한 고화질 실제 작동 영상과 검수 구간이 필요합니다.')
    if not 0 <= (today - evidence.checked_at.date()).days <= 1:
        raise ValueError('생활 지표는 최근 24시간 내 확인한 구매 정보와 함께 재확인해야 합니다.')
    if evidence.route == 'commerce':
        if evidence.review_count is None and not evidence.sales_statement.strip():
            raise ValueError('상품평 수 또는 실제 표시된 구매 지표가 필요합니다.')
        if evidence.sales_statement and (not evidence.sales_period.strip() or not evidence.sales_scope.strip()):
            raise ValueError('구매 지표의 기간과 집계 범위가 필요합니다.')
        if evidence.review_count is not None and not evidence.review_scope.strip():
            raise ValueError('리뷰의 상품/옵션 합산 범위를 기록해야 합니다.')
    else:
        if evidence.event_date is None or not 0 <= (today - evidence.event_date).days <= 30:
            raise ValueError('생활 뉴스 사건일은 최근 30일 이내여야 합니다.')
        if not any(s.published_date and 0 <= (today - date.fromisoformat(s.published_date)).days <= 30 for s in evidence.sources):
            raise ValueError('최근 게시일이 확인된 뉴스 원문이 필요합니다.')
