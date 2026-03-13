import os
from google import genai
import json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

query = "sol 미국넥스트테크top10 액티브"

prompt = f"""
Find the 6-digit Korean stock ticker code for "{query}".
Respond with only the 6 digits.
"""
try:
    res = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview',
        contents=prompt
    )
    print(res.text)
except Exception as e:
    print(e)
