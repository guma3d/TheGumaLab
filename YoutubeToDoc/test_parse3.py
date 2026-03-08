from bs4 import BeautifulSoup

try:
    with open('/app/output/zsdmj-bF5kM/zsdmj-bF5kM.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    blocks = soup.find_all('div', class_='content-block')
    print("Number of content blocks:", len(blocks))
    if len(blocks) > 0:
        c1 = [ch.get('class') for ch in blocks[0].find_all('div')]
        print("Block 0 div classes:", c1)
    if len(blocks) > 1:
        c2 = [ch.get('class') for ch in blocks[1].find_all('div')]
        print("Block 1 div classes:", c2)
except Exception as e:
    print(e)
