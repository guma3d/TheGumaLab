import urllib.request
import xml.etree.ElementTree as ET

urls = {
    "정치": "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=ko&gl=KR&ceid=KR:ko",
    "경제": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
    "사회": "https://news.google.com/rss/headlines/section/topic/NATION?hl=ko&gl=KR&ceid=KR:ko",
    "IT": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko",
    "주식": "https://news.google.com/rss/search?q=%EC%A3%BC%EC%8B%9D+when:24h&hl=ko&gl=KR&ceid=KR:ko"
}

for cat, url in urls.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        items = root.findall('.//item')[:5]
        print(f"[{cat}]")
        for item in items:
            title = item.find('title').text
            print("  - " + title)
    except Exception as e:
        print(f"Error fetching {cat}: {e}")
