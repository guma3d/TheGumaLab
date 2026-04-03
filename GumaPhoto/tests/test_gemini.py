import os
from google import genai

key = ""
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if "GOOGLE_API_KEY=" in line:
                key = line.split("GOOGLE_API_KEY=")[1].strip()

if not key:
    print("NO KEY")
    exit()

client = genai.Client(api_key=key)

prompt = """You are a Photo Search Query Parser.
Current Year: 2026
Known People in DB: [성욱, 송이]

User Query: "하와이 성욱"

Parse the query into EXACTLY this JSON structure:
{
  "years": [], // list of integers, e.g., 2025. convert "작년" to 2025. If none, []
  "people": [], // list of names exactly matching the Known People list. Fix misspellings if obvious. If none, []
  "locations": [ // If any specific place, landmark, city, or province is mentioned (e.g. "하와이", "전라도", "오사카", "집근처"), convert it into GPS coordinates (WGS84).
    {
      "lat": 35.6329,
      "lon": 139.8804,
      "radius": 50000,    // City/Province/Country: 50000. Specific landmark/district: 2000.
      "matched_word": "오사카", // The exact substring of the location from the user's query
      "official_name": "오사카부" // The official administrative name (e.g. "대구" -> "대구광역시", "제주" -> "제주특별자치도"). Important for DB metadata matching.
    }
  ], // If none, []
  "visual": "EMPTY" // Translate all remaining visual/abstract concepts to a concise English phrase. DO NOT include the extracted years, people, or locations. e.g. "수영하는" -> "swimming". If no visual meaning remains, output "EMPTY".
}
Output ONLY valid JSON without markup.
"""

print(client.models.generate_content(model='gemini-3.1-flash-lite-preview', contents=prompt).text)
