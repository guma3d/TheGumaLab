from bs4 import BeautifulSoup

try:
    with open('/app/output/zsdmj-bF5kM/zsdmj-bF5kM.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    for div in soup.find_all('div'):
        c = div.get('class')
        if c and 'p_text' in c:
            print("Found p_text:", div.text[:50])
            break
        if c and 'caption-container' in c:
            print("Found caption-container children classes:", [ch.get('class') for ch in div.find_all('div') if ch.get('class')])
            break
except Exception as e:
    print(e)
