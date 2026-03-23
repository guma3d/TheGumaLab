import re
import os

# 스크립트 파일이 위치한 경로를 기준으로 절대 경로 생성 (터미널 위치 상관없이 무조건 100% 동작)
script_dir = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(script_dir, '..', 'templates', 'index.html')

if not os.path.exists(filepath):
    print(f"오류: {filepath} 파일을 찾을 수 없습니다.")
    exit(1)

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 정규표현식을 사용해 ?v=숫자 패턴을 찾아 숫자를 1씩 증가시킵니다.
def replacer(match):
    prefix = match.group(1)
    version = int(match.group(2))
    new_version = version + 1
    print(f"Updated: v{version} -> v{new_version}")
    return f"{prefix}{new_version}"

new_content = re.sub(r'(\?v=)(\d+)', replacer, content)

if new_content != content:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("캐시 무효화 버전 펌핑 완료! 브라우저를 새로고침 하세요.")
else:
    print("?v= 패턴을 찾을 수 없습니다.")
