"""Shared Gemini client setup for GumaEnglish (google-genai SDK)."""
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")

if not API_KEY:
    raise RuntimeError(
        f"GEMINI_API_KEY not found. Expected in {ROOT / '.env'}"
    )

client = genai.Client(api_key=API_KEY)


def get_client() -> genai.Client:
    return client


def get_model_name() -> str:
    return MODEL_NAME
