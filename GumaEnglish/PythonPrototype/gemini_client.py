"""Shared Gemini client setup for GumaEnglish prototype."""
import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")

if not API_KEY:
    raise RuntimeError(
        f"GEMINI_API_KEY not found. Expected in {ROOT / '.env'}"
    )

genai.configure(api_key=API_KEY)


def get_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(MODEL_NAME)
