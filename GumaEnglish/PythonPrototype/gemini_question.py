"""Generate varied eliciting questions for a given pattern.

Each call should return a fresh English question designed to make a
7-9 year old child naturally produce a sentence in the target pattern.
The function avoids repeating any of the previous questions passed in.
"""
import json

from google.genai import types

from gemini_client import get_client, get_model_name

SYSTEM_INSTRUCTION = """You are Guma, a friendly robot talking to a 7-9 year old Korean child who is learning English.

Your single job: ask ONE short English question that naturally makes the child respond using the target PATTERN.

Rules:
- One question only. No explanation, no preface, no translation.
- 8 words or fewer.
- Warm, playful tone. Use simple vocabulary a 7-year-old knows.
- The question must pull the child toward the target PATTERN — NOT toward other patterns.
- Do NOT repeat any of the PREVIOUS_QUESTIONS. Vary the situation, wording, and angle.
- Do NOT say the pattern yourself. The child should say it.
- Output ONLY the question text. No quotes, no JSON, no markdown.
"""


def generate_question(
    pattern_english: str,
    example_sentences: list[str],
    context_hint: str | None = None,
    previous_questions: list[str] | None = None,
) -> str:
    """Return a fresh eliciting question for the given pattern."""
    previous = previous_questions or []
    context_line = (
        f"SITUATION: {context_hint}"
        if context_hint
        else "SITUATION: pick any fun everyday situation a kid would enjoy"
    )

    user_prompt = f"""{context_line}

TARGET PATTERN: {pattern_english}

EXAMPLES OF SENTENCES THE CHILD SHOULD PRODUCE:
{chr(10).join(f'- {s}' for s in example_sentences)}

PREVIOUS_QUESTIONS (do not repeat these, even loosely):
{json.dumps(previous, ensure_ascii=False) if previous else '(none)'}

Now output ONE new English question that will elicit the target pattern.
"""

    response = get_client().models.generate_content(
        model=get_model_name(),
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=1.0,
        ),
    )
    return response.text.strip().strip('"').strip("'")


if __name__ == "__main__":
    pattern = "Can I have a ___?"
    examples = [
        "Can I have a cookie?",
        "Can I have some water?",
        "Can I have a pencil?",
    ]
    history: list[str] = []
    for i in range(5):
        q = generate_question(
            pattern_english=pattern,
            example_sentences=examples,
            context_hint=None,
            previous_questions=history,
        )
        print(f"[{i + 1}] {q}")
        history.append(q)
