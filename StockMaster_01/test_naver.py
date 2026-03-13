import urllib.request
import urllib.parse
import json

query = urllib.parse.quote("SOL 미국넥스트테크")
url = f"https://ac.finance.naver.com/ac?q={query}&q_enc=euc-kr&st=111&r_format=json&r_enc=euc-kr&r_lt=111&r_unicode=0&r_escape=1"
try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = response.read()
    j = json.loads(data)
    for i in j['items'][0]:
        print(i[0], i[1])
except Exception as e:
    print(e)
