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
            'applies_to': ['chat', 'web'],
            'required_order': ['acquire_exact_product_media', 'inspect_quality', 'recommend'],
            'readiness_validator': 'app.core.recommendation_readiness.validate_readiness',
            'unacquired_items': 'internal_research_only',
        },
        'follow_up': [
            '정확한 옵션의 가격·판매처·로켓배송·파트너스 링크를 확인한다.',
            '판매량/구매자 수는 표시 문구·기간·범위·확인 시각을 보존한다. 리뷰 수로 판매량을 추정하지 않는다.',
            '리뷰 500개·평점 4.3 이상은 탐색 우선값이며 카테고리별 비교와 최근/낮은 평점 후기 내용도 확인한다.',
            '뉴스는 원문 게시일과 사건일을 구분하고 재배포 보도자료를 독립 근거로 중복 집계하지 않는다.',
            '리뷰가 적은 신제품도 최근 뉴스 근거로 검토하되 판매 검증 부족을 표시한다.',
            '생활 문제·계절성·디자인·기존 소재 중복을 평가하고, 동일 제품 이미지 또는 영상을 실제로 확보한다.',
            '추천 전에 원본 파일·출처·동일 제품 판단·사용 가능 근거를 기록하고 해상도와 육안 화질을 검수한다. 영상은 실제 작동 구간도 재생 검수한다.',
            '자료 미확보 제품은 내부 조사 대상으로만 유지한다. 대화 추천과 웹 등록 모두 readiness 검증 후 확보 자료 링크 또는 미리보기를 제시한다.',
        ],
    }


def validate_living_evidence(evidence, today):
    if evidence is None:
        raise ValueError('생활 신규 추천은 living_evidence 판매·리뷰 또는 뉴스 근거가 필요합니다.')
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
