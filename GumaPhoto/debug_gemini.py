import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

prompt = """You are a Photo Search Query Parser.
Current Year: 2026
Known People in DB: []
Known Locations in DB: []

User Query: "강원도 사진"

Parse the query into EXACTLY this JSON structure:
{
  "years": [], // list of integers, e.g., 2025. convert "작년" to {current_year - 1}. If none, []
  "people": [], // list of names exactly matching the Known People list. Fix misspellings if obvious. If none, []
  "locations": [ // If any specific place, landmark, city, or province is mentioned (e.g. "하와이", "강원도", "오사카", "집근처"), convert it into GPS coordinates (WGS84).
    {
      "lat": 21.3069,
      "lon": -157.8583,
      "radius": 50000,    // IMPORTANT: Estimate radius in METERS accurately. Province/State: 100000 (100km), City: 30000 (30km), Landmark: 5000. DO NOT use excessively massive radiuses like 300km unless it is a huge country.
      "matched_word": "하와이", // The strict substring from the user query
      "official_name": "Hawaii", // Official administrative name
      "db_exact_locations": [] // (Optional) If you know exact DB tag names, add them here. Otherwise leave empty.
    }
  ], // If none, []
  "seasons": [], // Extract mentioned seasons exactly matching ["봄", "여름", "가을", "겨울"]. If none, []
  "time_of_days": [], // Extract mentioned times exactly matching ["아침", "낮", "오후", "저녁", "밤", "심야"]. If none, []
  "visual": "EMPTY" // Translate all visual/abstract concepts (including seasons/times) into concise English keywords. For "겨울", output "winter, snow, cold, frozen". For "밤", output "night, dark, streetlights". DO NOT include people/locations. If none, "EMPTY".
}
Output ONLY valid JSON without markup.
"""

print(model.generate_content(prompt).text)
