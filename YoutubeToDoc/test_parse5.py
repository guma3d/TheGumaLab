from bs4 import BeautifulSoup
try:
    with open('/app/output/kmXaVIANa-c/kmXaVIANa-c.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    blocks = soup.find_all("div", class_="content-block")
    all_text = ""
    for index, block in enumerate(blocks):
        if index == 0:
            continue
        cap = block.find("div", class_="caption")
        if cap:
            all_text += cap.get_text(separator=" ", strip=True) + " "
    print("Parsed chars:", len(all_text))
    print("First 100 chars:", all_text[:100])
except Exception as e:
    print("Error:", e)
