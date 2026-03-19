import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("/app/.env" if os.path.exists("/app/.env") else ".env")

with open("data/available_tags.json", "r", encoding="utf-8") as f:
    existing_locations = json.load(f)["locations"]

prompt = (
    f"사용자 검색어: '삼척에서 찍은 사진 보여줘'\n"
    "당신은 스마트 갤러리의 이미지 검색 쿼리 작성 도우미입니다. "
    "사용자가 한글로 자연어 검색을 하더라도, 반드시 우리가 서버에 '보유하고 있는 태그'를 파악하고 번역(대조)하여 JSON을 구성해야 합니다.\n"
    "다음 규칙에 따라 응답을 반드시 유효한 JSON 형식으로만 작성하세요.\n"
    f"1) 사용자 검색어 중 등록된 가족 이름([])과 매칭되는 사람이 있다면 'people' 문자열 배열에 저장.\n"
    "2) 사용자 검색어 중 장소/위치/국가명(예: 하와이, 제주도, 미국 등)이 포함되어 있다면, 의미를 스스로 번역/유추하여 다음 <보유 장소 목록> 중 가장 일치하는 텍스트 원본 그대로를 'location'에 문자열로 저장하세요.\n"
    f"   <보유 장소 목록> : {existing_locations}\n"
    "   (핵심 규칙: '하와이'를 검색하면 'Hawaii'나 'Honolulu', '엘에이'를 검색하면 'Los Angeles California' 등 위 목록에 있는 정확한 철자로만 치환해야 합니다. 포함관계에 있는 장소도 매칭 대상입니다. 정합되는 게 없으면 빈 문자열을 넣으세요.)\n"
    "3) 명확한 형태가 있는 '물리적 사물' (예: 강아지, 안경, 자동차, 빨간 셔츠)만 '영어 소문자 영단어'로 번역하여 'objects' 문자열 배열에 저장하세요. (예: dog, blue shirt, glasses)\n"
    "   ⚠️ [경고]: '결혼식(wedding)', '생일파티', '행사', '축제' 등과 같은 추상적 이벤트나 관념적인 명사는 절대 'objects'에 넣지 마세요!\n"
    "4) 위 3가지를 제외한 모든 내용(결혼식, 배경, 분위기, 행동 특징, 날씨 등)은 '순수 영어(English)' 문장으로 상세히 번역하여 'scene' 문자열에 저장하세요. (오직 영어로만 작성, 예: a wedding ceremony, young girl wearing blue shirt opening refrigerator)\n"
    "예시: {\"people\": [\"송이\"], \"location\": \"Honolulu Hawaii\", \"objects\": [\"dog\", \"blue shirt\"], \"scene\": \"a young girl playing at a wedding ceremony\"}\n"
    "만약 파악된 값이 없다면 빈 배열이나 빈 문자열로 두세요."
)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("API KEY NOT FOUND")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    print("Gemini Response:\n", response.text)
