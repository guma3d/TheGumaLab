import os
from dotenv import load_dotenv
load_dotenv('/app/.env')
from google import genai

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

for model in ['gemini-2.5-flash-lite', 'gemini-2.0-flash-lite', 'gemini-flash-lite-latest', 'gemini-2.0-flash-lite-001', 'models/gemini-2.5-flash']:
    try:
        res = client.models.generate_content(
            model=model,
            contents='Hello'
        )
        print(f'Success {model}:', res.text)
    except Exception as e:
        print(f'Error {model}:', e)
