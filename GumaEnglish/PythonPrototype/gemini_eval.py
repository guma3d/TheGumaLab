"""Evaluate a child's response and generate a brief acknowledgment.

Given the target pattern, the question the AI just asked, and the
child's spoken response, decide whether the child used the target
pattern correctly, and produce a short in-character reply to close
the round (no further conversation).
"""
import json
import re

from google.genai import types

from gemini_client import get_client, get_model_name

SYSTEM_INSTRUCTION = """You are Guma, a friendly robot talking to a 7-9 year old Korean child learning English.

Your job: judge whether the child's response uses the TARGET_PATTERN correctly, and generate a ONE-line reply that closes the round.

Rules:
- The reply must be in English, 10 words or fewer, warm and encouraging.
- If the child used the pattern correctly: react to the content naturally (as if their sentence were real). Use a playful emoji.
- If the child did NOT use the pattern (wrong grammar, wrong pattern, or off-topic): gently model the correct form once, still short and positive. Do NOT scold. Do NOT say "wrong".
- Never continue the conversation. Never ask another question.
- Pattern usage is "correct" if the child's sentence fits the pattern skeleton (allowing for the blank to be filled with reasonable content). Minor spelling errors do not count as wrong.

Output STRICT JSON (no markdown, no code fences):
{"used_pattern": true|false, "reply": "..."}
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def evaluate_and_reply(
    pattern_english: str,
    question_asked: str,
    learner_response: str,
) -> dict:
    """Return {'used_pattern': bool, 'reply': str}."""
    user_prompt = f"""TARGET_PATTERN: {pattern_english}
QUESTION_ASKED: {question_asked}
CHILD_RESPONSE: {learner_response}

Output the JSON now.
"""
    response = get_client().models.generate_content(
        model=get_model_name(),
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
        ),
    )
    return _extract_json(response.text)


if __name__ == "__main__":
    pattern = "Can I have a ___?"
    samples = [
        ("Guma is hungry! What do you want?", "Can I have a cookie?"),
        ("We're at the store! What do you want?", "I want cookie"),
        ("Library time! What do you want?", "Can I have a book?"),
        ("Snack time!", "apple"),
    ]
    for q, a in samples:
        result = evaluate_and_reply(pattern, q, a)
        ok = "[OK]" if result.get("used_pattern") else "[XX]"
        print(f"{ok} Q: {q}")
        print(f"     A: {a}")
        print(f"     -> {result.get('reply')}")
        print()
