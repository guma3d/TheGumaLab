import os

def generate_xmp_sidecar(filepath, payload):
    """
    Qdrant에 저장되는 텍스트 메타데이터(Payload)를 원본 사진 파일 옆에
    XMP(XML) 형태의 사이드카 파일로 영구 보존(백업)합니다.
    """
    base_name, _ = os.path.splitext(filepath)
    xmp_path = base_name + ".xmp"
    
    tags = []
    # Qdrant Payload의 주요 검색어들을 추출
    if payload.get("people"):
        for p in payload["people"]:
            tags.append(p)
    if payload.get("location") and payload["location"] != "Unknown Location":
        tags.append(payload["location"])
    if payload.get("season") and payload["season"] != "Unknown":
        tags.append(payload["season"])
    if payload.get("time_of_day") and payload["time_of_day"] != "Unknown":
        tags.append(payload["time_of_day"])
    if payload.get("objects"):
        for o in payload["objects"]:
            tags.append(o)
            
    # 중복 및 빈 문자열 제거
    tags = list(set([str(t).strip() for t in tags if str(t).strip()]))
    
    # XML/XMP 기본 템플릿 (Adobe Standard)
    xmp_tpl = f"""<?xpacket begin='' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
        xmlns:xmp="http://ns.adobe.com/xap/1.0/">
      <dc:subject>
        <rdf:Bag>
"""
    # [1] 태그(Keywords) 삽입
    for t in tags:
        t_clean = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xmp_tpl += f"          <rdf:li>{t_clean}</rdf:li>\n"
        
    xmp_tpl += """        </rdf:Bag>
      </dc:subject>
"""
    
    # [2] 캡션(Description) 삽입
    caption = payload.get("caption", "")
    if caption:
        c_clean = str(caption).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xmp_tpl += f"""      <dc:description>
        <rdf:Alt>
          <rdf:li xml:lang="x-default">{c_clean}</rdf:li>
        </rdf:Alt>
      </dc:description>
"""
    
    xmp_tpl += """    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end='w'?>"""

    try:
        with open(xmp_path, "w", encoding="utf-8") as f:
            f.write(xmp_tpl)
        print(f"      💾 [XMP 사이드카] 생성 완료: {os.path.basename(xmp_path)}")
    except Exception as e:
        print(f"      ⚠️ [XMP 사이드카] 생성/수정 권한 오류: {e}")
