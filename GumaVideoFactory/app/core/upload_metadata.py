"""Product-first metadata with a single, exact affiliate disclosure footer."""
import re

DISCLOSURE = '이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.'


def title(text):
    return re.sub(r'^(?:\s*\[광고\]\s*)+', '', text).strip()


def description_hashtags(text, supplied=''):
    """Keep author tags and add relevant defaults: ad plus at least five tags."""
    if not isinstance(supplied, str):
        supplied = ' '.join(supplied or [])
    tags = ['광고']
    tags.extend(re.findall(r'#(\w+)', supplied))
    for terms, related in (
        (('고구마빵',), ('고구마빵', '간식', '디저트')),
        (('딸기쏙우유',), ('딸기쏙우유', '찹쌀떡', '간식', '디저트')),
        (('찰떡아이스',), ('찰떡아이스', '아이스크림', '간식')),
        (('흑임자',), ('흑임자',)),
        (('피자설기',), ('피자설기', '떡', '간식', '디저트')),
        (('보풀제거기',), ('보풀제거기', '가전', '의류관리')),
        (('니트',), ('니트',)),
        (('가습기',), ('가습기', '가전', '생활용품')),
        (('가을',), ('가을',)),
    ):
        if any(term in text for term in terms):
            tags.extend(related)
    tags = list(dict.fromkeys(tags))
    for tag in ('쇼츠', '쇼핑쇼츠', '상품소개', '제품정보', '쇼핑정보'):
        if len(tags) >= 6:
            break
        if tag not in tags:
            tags.append(tag)
    return ' '.join('#' + tag for tag in tags)


def description(bullets, product_url, music_review, hashtags='', *, context=''):
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
    body += '\n\n' + description_hashtags(context + '\n' + '\n'.join(lines), hashtags)
    return bgm.credit(body, music_review).rstrip() + '\n\n' + DISCLOSURE
