"""Content-based staging for approved-model tech previews."""
import re


def validate_tech_visuals(scenes):
    for index, scene in enumerate(scenes):
        mode = scene.get('visual_mode')
        if mode not in ('approved_model', 'mechanism_concept'):
            raise ValueError(f'{index+1}번 컷의 외형/원리 연출 유형을 지정해주세요.')
        if index in (0, len(scenes)-1) and mode != 'approved_model':
            raise ValueError('도입·마지막 컷은 승인된 제품 외형을 사용해주세요.')
        spoken = scene.get('narration_ko', '') + ' ' + ' '.join(scene.get('covered_features', []))
        # A named thermal mechanism must be visibly explained, not merely tagged
        # in metadata while a phone beauty shot is rendered.
        if re.search(r'베이퍼\s*챔버|증기\s*챔버|vapo[u]?r\s*chamber', spoken, re.I):
            if mode != 'mechanism_concept':
                raise ValueError(f'{index+1}번 컷: 베이퍼 챔버 설명에는 원리 개념도가 필요합니다.')
            prompt = scene.get('visual_prompt', '')
            if not re.search(r'vapo[u]?r\s*chamber', prompt, re.I) or not re.search(r'condens|응축', prompt, re.I):
                raise ValueError(f'{index+1}번 컷: 베이퍼 챔버와 응축 과정을 장면에 명시해주세요.')
        if not scene.get('visual_subject', '').strip():
            raise ValueError(f'{index+1}번 컷의 시각적 설명 대상을 지정해주세요.')
