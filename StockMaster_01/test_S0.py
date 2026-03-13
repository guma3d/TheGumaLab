import os
from google import genai
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

res = client.models.generate_content(
    model='gemini-3.1-flash-lite-preview',
    contents='If the user says "0118S0", what Korean stock ticker are they referring to? Are they talking about SOL 미국넥스트테크TOP10액티브? What is the official 6-digit code for SOL 미국넥스트테크TOP10액티브?'
)
print(res.text)
