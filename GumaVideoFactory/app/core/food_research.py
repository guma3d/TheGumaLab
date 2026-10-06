"""Food discovery queries and evidence checks; this does not execute web searches."""
from datetime import date, timedelta


def search_plan(today=None):
    today = today or date.today()
    since = (today - timedelta(days=7)).isoformat()
    return {
        'preferred_days': 7, 'maximum_days': 30,
        'queries': [
            {'route': 'broadcast', 'query': f'방송 소개 음식 화제 레시피 after:{since}'},
            {'route': 'overseas', 'query': f'viral food trend recipe news after:{since}'},
            {'route': 'overseas', 'query': f'海外 話題 グルメ 人気 after:{since}'},
            {'route': 'retail', 'query': f'음식 디저트 신제품 품절 재입고 after:{since}'},
            {'route': 'recipe', 'query': f'유행 음식 레시피 재료 after:{since}'},
        ],
        'follow_up': [
            '방송사 공식 회차·방영일, 해외 현지 원문·국가·사건일을 확인한다.',
            '품절은 판매처·옵션·확인시각별로 확인한다. 한 판매처 품절을 품절 대란으로 확대하지 않는다.',
            '완제품 또는 검증된 레시피의 핵심 재료로 연결한다. 유사 제품을 방송 속 동일 제품이나 동일 맛으로 주장하지 않는다.',
            '쿠팡 정확한 옵션·공식 판매처·로켓배송·발급 파트너스 링크를 확인한 뒤 추천한다.',
        ],
    }


def validate_food_trend(trend, today):
    """Validate recorded evidence, not the truth of a webpage; Codex verifies originals."""
    if trend is None:
        raise ValueError('푸드 신규 추천은 food_trend 조사 근거가 필요합니다.')
    age = (today - trend.event_date).days
    if not 0 <= age <= 30:
        raise ValueError('푸드 화제 발생일은 최근 30일 이내여야 합니다.')
    if not any(source.published_date and 0 <= (today - date.fromisoformat(source.published_date)).days <= 30 for source in trend.evidence):
        raise ValueError('최근 날짜가 확인된 푸드 원문 출처가 필요합니다.')
    if trend.route == 'broadcast' and not trend.program.strip():
        raise ValueError('방송 경로는 프로그램·회차를 기록해야 합니다.')
    if trend.route == 'recipe' and trend.connection != 'recipe_ingredient':
        raise ValueError('레시피 경로는 조리 재료 연결 근거가 필요합니다.')
    if trend.stock_claim and not trend.stock_evidence:
        raise ValueError('품절 주장은 판매처·옵션·시각과 별도 재고 근거가 필요합니다.')
