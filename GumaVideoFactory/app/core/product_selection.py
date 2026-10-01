"""Only select product variants backed by an explicit dimension reference."""
import re


def selection_policy(product_name):
    name=product_name.strip().casefold()
    if re.fullmatch(r'(?:apple\s+)?iphone\s*18\s*pro(?:\s*max)?',name):
        return dict(product_name=product_name,expected_height_m=.1634 if name.endswith('max') else .150,
            tolerance_m=.002,source_url='https://www.apple.com/iphone-18-pro/specs/')
    return None


def choose_phone(groups,policy):
    """Never choose the first/largest mesh or discard individual phone parts."""
    if not policy:raise ValueError('여러 제품이 포함된 모델입니다. 정확한 기종을 선택할 근거가 필요합니다.')
    candidates=[]
    for g in groups:
        depth,width,height=sorted(g['size_m'])
        if (g['mesh_count']>=10 and .3<width/height<.65 and depth/width<.3
                and abs(height-policy['expected_height_m'])<=policy['tolerance_m']):
            candidates.append(g)
    if len(candidates)!=1:
        raise ValueError('제품 치수와 일치하는 단일 모델을 확정하지 못했습니다. 임의로 부품을 제거하지 않습니다.')
    return candidates[0]
