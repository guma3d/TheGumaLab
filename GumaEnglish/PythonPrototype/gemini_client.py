"""Shared Gemini client setup for GumaEnglish (google-genai SDK).

Provides a fallback chain: tries the preferred model first, falls through
to stable models on ServerError / rate-limit / unavailable errors. This
mirrors GumaStockReport's strategy — the preview model has the best
quality but occasionally returns 503 UNAVAILABLE.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_KEY = os.environ.get("GEMINI_API_KEY")
PRIMARY_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")

# Primary first, then stable fallbacks.
MODEL_CHAIN = [
    PRIMARY_MODEL,
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]
# De-duplicate while preserving order.
MODEL_CHAIN = list(dict.fromkeys(MODEL_CHAIN))

if not API_KEY:
    raise RuntimeError(
        f"GEMINI_API_KEY not found. Expected in {ROOT / '.env'}"
    )

client = genai.Client(api_key=API_KEY)


def generate_content(
    contents,
    *,
    system_instruction: str | None = None,
    temperature: float = 1.0,
) -> str:
    """Call Gemini with fallback chain. Return response.text."""
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
    )
    last_exc: Exception | None = None
    for model_name in MODEL_CHAIN:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            return response.text
        except errors.ServerError as e:
            print(f"[gemini] {model_name} ServerError: {e} — trying next")
            last_exc = e
        except errors.ClientError as e:
            # 429 rate limit → try next; other client errors propagate.
            if getattr(e, "code", None) == 429:
                print(f"[gemini] {model_name} rate-limited — trying next")
                last_exc = e
            else:
                raise
    raise RuntimeError(f"All Gemini models failed: {last_exc}")
