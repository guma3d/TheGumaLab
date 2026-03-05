"""
Confluence Wiki 페이지 작성 스크립트

이 스크립트는 Confluence REST API를 사용하여 페이지를 생성하거나 업데이트합니다.
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import os
import re
from typing import Optional
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import markdown

# .env 파일 로드
load_dotenv()


class ConfluenceWiki:
    def __init__(self, base_url: str, username: str, api_token: str):
        """
        Confluence API 클라이언트 초기화
        
        Args:
            base_url: Confluence 베이스 URL (예: https://your-domain.atlassian.net/wiki)
            username: Confluence 사용자 이메일
            api_token: Confluence API 토큰
        """
        self.base_url = base_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, api_token)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_space_info(self, space_key: str):
        """스페이스 정보 조회"""
        url = f"{self.base_url}/rest/api/content"
        params = {
            'spaceKey': space_key,
            'limit': 1
        }
        
        response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_page_by_title(self, space_key: str, title: str) -> Optional[dict]:
        """제목으로 페이지 검색"""
        url = f"{self.base_url}/rest/api/content"
        params = {
            'spaceKey': space_key,
            'title': title,
            'expand': 'version,body.storage'
        }
        
        response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
        response.raise_for_status()
        
        results = response.json().get('results', [])
        return results[0] if results else None
    
    def create_page(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> dict:
        """새 페이지 생성"""
        url = f"{self.base_url}/rest/api/content"
        
        data = {
            'type': 'page',
            'title': title,
            'space': {'key': space_key},
            'body': {
                'storage': {
                    'value': content,
                    'representation': 'storage'
                }
            }
        }
        
        if parent_id:
            data['ancestors'] = [{'id': parent_id}]
        
        response = requests.post(
            url, 
            headers=self.headers, 
            auth=self.auth, 
            data=json.dumps(data)
        )
        response.raise_for_status()
        
        return response.json()
    
    def update_page(self, page_id: str, title: str, content: str, current_version: int) -> dict:
        """기존 페이지 업데이트"""
        url = f"{self.base_url}/rest/api/content/{page_id}"
        
        data = {
            'version': {'number': current_version + 1},
            'title': title,
            'type': 'page',
            'body': {
                'storage': {
                    'value': content,
                    'representation': 'storage'
                }
            }
        }
        
        response = requests.put(
            url,
            headers=self.headers,
            auth=self.auth,
            data=json.dumps(data)
        )
        response.raise_for_status()
        
        return response.json()
    
    def create_or_update_page(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> dict:
        """페이지 생성 또는 업데이트 (존재하면 업데이트, 없으면 생성)"""
        existing_page = self.get_page_by_title(space_key, title)
        
        if existing_page:
            print(f"기존 페이지 발견: {title} (ID: {existing_page['id']})")
            print("페이지 업데이트 중...")
            result = self.update_page(
                existing_page['id'],
                title,
                content,
                existing_page['version']['number']
            )
            print(f"✅ 페이지 업데이트 완료: {self.base_url}/pages/{result['id']}")
        else:
            print(f"새 페이지 생성 중: {title}")
            result = self.create_page(space_key, title, content, parent_id)
            print(f"✅ 페이지 생성 완료: {self.base_url}/pages/{result['id']}")
        
        return result
    
    def upload_attachment(self, page_id: str, file_path: str) -> dict:
        """페이지에 첨부파일 업로드"""
        url = f"{self.base_url}/rest/api/content/{page_id}/child/attachment"
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            headers = {'X-Atlassian-Token': 'no-check'}
            
            response = requests.post(
                url,
                headers=headers,
                auth=self.auth,
                files=files
            )
            response.raise_for_status()
            
        return response.json()


def get_youtube_title(youtube_url: str) -> Optional[str]:
    """
    YouTube oEmbed API를 사용하여 영상 제목 가져오기
    
    Args:
        youtube_url: YouTube 영상 URL
        
    Returns:
        영상 제목 또는 None
    """
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={youtube_url}&format=json"
        response = requests.get(oembed_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('title')
    except Exception as e:
        print(f"⚠️  YouTube 제목 가져오기 실패: {e}")
        return None


def extract_markdown_from_html(html_file_path: str) -> tuple[str, str]:
    """
    HTML 파일에서 마크다운 컨텐츠 추출
    
    Args:
        html_file_path: HTML 파일 경로
        
    Returns:
        (제목, 마크다운 컨텐츠) 튜플
    """
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 제목 추출 (title 태그에서 기본값)
    title_tag = soup.find('title')
    title = title_tag.text if title_tag else "Untitled"
    title = title.replace(" - 요약", "").strip()
    
    # YouTube 정보 추출
    youtube_url = None
    youtube_thumbnail = None
    video_id = None
    
    # YouTube URL 추출 (source-url 클래스에서)
    source_url = soup.find('p', class_='source-url')
    if source_url:
        link = source_url.find('a')
        if link:
            youtube_url = link.get('href')
            # URL에서 video ID 추출
            if 'watch?v=' in youtube_url:
                video_id = youtube_url.split('watch?v=')[1].split('&')[0]
            
            # YouTube에서 실제 영상 제목 가져오기
            youtube_title = get_youtube_title(youtube_url)
            if youtube_title:
                title = youtube_title
                print(f"   YouTube 제목: {title}")
    
    # 썸네일 이미지 추출
    content_block = soup.find('div', class_='content-block')
    if content_block:
        img_tag = content_block.find('img')
        if img_tag:
            youtube_thumbnail = img_tag.get('src')
    
    # markdown-body 클래스를 가진 div에서 마크다운 텍스트 추출
    markdown_div = soup.find('div', class_='markdown-body')
    
    if markdown_div:
        # div 내부의 텍스트 추출 (마크다운 형식으로 유지)
        markdown_text = markdown_div.get_text()
        
        # YouTube 정보를 컨텐츠 상단에 추가 (Confluence Storage Format)
        header_content = ""
        if youtube_thumbnail:
            # 썸네일 이미지를 화면 전체 폭으로 표시
            header_content += f'<p><ac:image ac:width="100%"><ri:url ri:value="{youtube_thumbnail}" /></ac:image></p>\n'
        if youtube_url:
            # YouTube 링크 하나만 추가
            header_content += f'<p><strong>원본 영상:</strong> <a href="{youtube_url}">{youtube_url}</a></p>\n'
        
        header_content += '<hr />\n'
        
        # 마크다운 텍스트 앞에 헤더 컨텐츠 추가
        full_content = header_content + markdown_text
        return title, full_content
    else:
        raise ValueError("HTML 파일에서 markdown-body를 찾을 수 없습니다.")


def markdown_to_confluence(markdown_text: str) -> str:
    """
    마크다운을 Confluence Storage Format으로 변환
    
    Args:
        markdown_text: 마크다운 텍스트
        
    Returns:
        Confluence Storage Format HTML
    """
    # 마크다운 테이블을 직접 Confluence 테이블로 변환
    def convert_markdown_table(match):
        lines = match.group(0).strip().split('\n')
        if len(lines) < 2:
            return match.group(0)
        
        # 첫 번째 줄: 헤더
        header_cells = [cell.strip() for cell in lines[0].split('|')[1:-1]]
        
        # 두 번째 줄: 구분자 (정렬 정보 추출)
        separator_cells = [cell.strip() for cell in lines[1].split('|')[1:-1]]
        alignments = []
        for sep in separator_cells:
            if sep.startswith(':') and sep.endswith(':'):
                alignments.append('center')
            elif sep.endswith(':'):
                alignments.append('right')
            elif sep.startswith(':'):
                alignments.append('left')
            else:
                alignments.append('')
        
        # 테이블 생성
        table_html = '<table><tbody>'
        
        # 헤더 행
        table_html += '<tr>'
        for i, cell in enumerate(header_cells):
            align_style = f' style="text-align: {alignments[i]};"' if i < len(alignments) and alignments[i] else ''
            table_html += f'<th{align_style}>{cell}</th>'
        table_html += '</tr>'
        
        # 데이터 행들
        for line in lines[2:]:
            if not line.strip():
                continue
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            table_html += '<tr>'
            for i, cell in enumerate(cells):
                align_style = f' style="text-align: {alignments[i]};"' if i < len(alignments) and alignments[i] else ''
                table_html += f'<td{align_style}>{cell}</td>'
            table_html += '</tr>'
        
        table_html += '</tbody></table>'
        return table_html
    
    # 마크다운 테이블 패턴 찾아서 변환
    table_pattern = r'(?:^|\n)((?:\|.+\|[\r\n]+)+)'
    markdown_text = re.sub(table_pattern, convert_markdown_table, markdown_text, flags=re.MULTILINE)
    
    # Python markdown 라이브러리로 HTML 변환
    html = markdown.markdown(
        markdown_text,
        extensions=['fenced_code']  # nl2br 제거 (리스트 파싱 방해)
    )
    
    # BeautifulSoup으로 HTML 파싱 - 코드 블록 변환용
    soup = BeautifulSoup(html, 'html.parser')
    
    # BeautifulSoup 결과를 문자열로 변환
    html = str(soup)
    
    # Confluence Storage Format으로 추가 변환
    # 코드 블록을 Confluence 매크로로 변환
    html = re.sub(
        r'<pre><code class="language-(\w+)">(.*?)</code></pre>',
        lambda m: f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">{m.group(1)}</ac:parameter><ac:plain-text-body><![CDATA[{m.group(2)}]]></ac:plain-text-body></ac:structured-macro>',
        html,
        flags=re.DOTALL
    )
    
    # 일반 코드 블록
    html = re.sub(
        r'<pre><code>(.*?)</code></pre>',
        r'<ac:structured-macro ac:name="code"><ac:plain-text-body><![CDATA[\1]]></ac:plain-text-body></ac:structured-macro>',
        html,
        flags=re.DOTALL
    )
    
    return html


def create_sample_content() -> str:
    """샘플 Confluence 페이지 컨텐츠 (Storage Format)"""
    return """
<h1>이미지 품질 분석 결과</h1>
<p>이 페이지는 자동으로 생성된 이미지 품질 분석 보고서입니다.</p>

<h2>분석 개요</h2>
<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p>전체 이미지 중 고품질 이미지를 자동으로 선별했습니다.</p>
  </ac:rich-text-body>
</ac:structured-macro>

<h2>선택 기준</h2>
<ul>
  <li>Sharpness (선명도) &gt; 90</li>
  <li>Saliency Score (주목도) &gt; 90</li>
  <li>Histogram Spread (히스토그램 분포) &lt; 70</li>
  <li>Edge Density (엣지 밀도) &gt; 50</li>
</ul>

<h2>결과 이미지</h2>
<p>선택된 고품질 이미지들은 아래 링크에서 확인할 수 있습니다.</p>
"""


# 사용 예제
if __name__ == "__main__":
    # .env 파일에서 설정 읽기
    CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "https://krafton.atlassian.net/wiki")
    CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
    CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
    SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY", "~kwonsh")
    PARENT_PAGE_ID = os.getenv("CONFLUENCE_PARENT_PAGE_ID", "283148678")
    
    # HTML 파일 경로 (명령줄 인자 또는 기본값)
    import sys
    if len(sys.argv) > 1:
        HTML_FILE = sys.argv[1]
    else:
        HTML_FILE = "./Streaming_Improvements_for_Den/Streaming_Improvements_for_Den-summary.html"
    
    # 필수 환경 변수 체크
    if not all([CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN]):
        print("❌ 에러: .env 파일에 필수 환경 변수가 설정되지 않았습니다.")
        print("필요한 환경 변수:")
        print("  - CONFLUENCE_USERNAME")
        print("  - CONFLUENCE_API_TOKEN")
        print("\n선택적 환경 변수 (기본값 사용 가능):")
        print("  - CONFLUENCE_URL (기본값: https://krafton.atlassian.net/wiki)")
        print("  - CONFLUENCE_SPACE_KEY (기본값: ~kwonsh)")
        print("  - CONFLUENCE_PARENT_PAGE_ID (기본값: 283148678)")
        exit(1)
    
    print(f"📝 Confluence 연결 정보:")
    print(f"   URL: {CONFLUENCE_URL}")
    print(f"   사용자: {CONFLUENCE_USERNAME}")
    print(f"   스페이스: {SPACE_KEY}")
    print(f"   상위 페이지 ID: {PARENT_PAGE_ID}")
    print(f"   HTML 파일: {HTML_FILE}\n")
    
    # Confluence 클라이언트 생성
    wiki = ConfluenceWiki(CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)
    
    # HTML 파일에서 마크다운 추출
    try:
        print("📄 HTML 파일에서 마크다운 추출 중...")
        page_title, markdown_content = extract_markdown_from_html(HTML_FILE)
        print(f"   제목: {page_title}")
        print(f"   컨텐츠 길이: {len(markdown_content)} 문자\n")
        
        print("🔄 마크다운을 Confluence 형식으로 변환 중...")
        confluence_content = markdown_to_confluence(markdown_content)
        
        print(f"📤 페이지 업로드 중: '{page_title}'")
        result = wiki.create_or_update_page(
            space_key=SPACE_KEY,
            title=page_title,
            content=confluence_content,
            parent_id=PARENT_PAGE_ID
        )
        
        print(f"\n✅ 성공!")
        print(f"페이지 URL: {CONFLUENCE_URL}/pages/viewpage.action?pageId={result['id']}")
        
    except FileNotFoundError:
        print(f"❌ 에러: HTML 파일을 찾을 수 없습니다: {HTML_FILE}")
    except ValueError as e:
        print(f"❌ 에러: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 에러: {e}")
        print(f"응답: {e.response.text if e.response else 'No response'}")
    except Exception as e:
        print(f"❌ 에러: {e}")
