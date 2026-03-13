import os
from google import genai
import json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("NO KEY")
    exit()

client = genai.Client(api_key=GEMINI_API_KEY)

query = "0118S0"

prompt = f"""
사용자가 입력한 주식 검색어 또는 주식 코드: '{query}'
이 검색어/코드에 해당하는 주식 시장의 Ticker 심볼(Yahoo Finance 기준)과 영문 공식 회사 이름을 찾아주세요. (주식 코드가 입력되면 반드시 해당 코드를 가진 종목을 최우선으로 찾아주세요)
관련된 종목이 있다면 가장 연관성이 높은 순서대로 1개에서 최대 3개까지 찾아주세요.
(한국 주식인 경우 KOSPI는 '.KS', 코스닥은 '.KQ'를 Ticker에 붙여주세요. 숫자 코드가 들어온 경우 무조건 한국 주식입니다. 예: 005930 -> 005930.KS)
추가로 이 종목이 소속된 국가/시장을 'market' 필드에 '한국(KOR)' 또는 '미국(USA)' 등으로 명시해주세요.
ETF 등도 검색될 수 있습니다.
반드시 아래와 같은 JSON 배열 형식으로만 응답해야 합니다. 다른 텍스트는 절대로 포함하지 마세요:
[
  {{"ticker": "TSLA", "name": "Tesla, Inc.", "market": "USA"}},
  {{"ticker": "005930.KS", "name": "Samsung Electronics", "market": "KOR"}}
]
"""
try:
    res = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview',
        contents=prompt
    )
    print(res.text)
except Exception as e:
    print(e)
