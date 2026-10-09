"""Product-first metadata with a single, exact affiliate disclosure footer."""
import re

DISCLOSURE = '이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.'


def title(text):
    return re.sub(r'^(?:\s*\[광고\]\s*)+', '', text).strip()


def description(bullets, product_url, music_review, hashtags=''):
    from app.core import bgm
    if isinstance(bullets, str):
        bullets = re.split(r'\n+|(?<=[.!?])\s+', bullets)
    lines = []
    for item in bullets:
        item = item.strip().removeprefix('- ').strip()
        if not item or item == DISCLOSURE:
            continue
        # Omit production boilerplate, never manufacture a personal endorsement.
        if any(term in item for term in ('AI 연출', '합성 음성', '합성 여성 음성',
                '합성 내레이션', '직접 시식 후기', 'Zephyr')):
            continue
        lines.append('- ' + item)
    if not lines:
        raise ValueError('검증된 상품 설명을 작성해주세요.')
    body = '\n'.join(lines) + '\n\n상품 정보: ' + product_url
    if hashtags.strip():
        body += '\n\n' + hashtags.strip()
    return bgm.credit(body, music_review).rstrip() + '\n\n' + DISCLOSURE
