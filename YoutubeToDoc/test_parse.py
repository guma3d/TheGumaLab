from bs4 import BeautifulSoup

try:
    with open('/app/output/zsdmj-bF5kM/zsdmj-bF5kM.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    caps = soup.find_all('div', class_='caption')
    print(len(caps))
    for c in caps[:5]:
        print(c.get('class'))
except Exception as e:
    print(e)
