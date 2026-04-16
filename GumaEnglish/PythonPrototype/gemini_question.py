"""Generate an eliciting question that targets ONE specific memorized sentence.

Each round aims to pull the child toward one exact target sentence (e.g.
"Can I have a cookie?") — not just "any sentence that fits the pattern".
The question funnels the child toward the target's key word via the
situation, without saying the key word itself.
"""
import json

from gemini_client import generate_content

SYSTEM_INSTRUCTION = """You are Guma, a friendly robot talking to a 7-9 year old Korean child who is learning English.

Your single job: ask ONE short English question whose most natural answer is the TARGET_SENTENCE.

Rules:
- One question only. No explanation, no preface, no translation.
- 8 words or fewer.
- Warm, playful tone. Use simple vocabulary a 7-year-old knows.
- The question must funnel the child toward the TARGET_SENTENCE specifically — so they will naturally want to say that exact key word (cookie / water / pencil / etc.).
- Do NOT say the key word itself in the question (don't leak the answer).
- Do NOT say the pattern skeleton itself. The child should produce it.
- Do NOT repeat any of the PREVIOUS_QUESTIONS. Vary wording and angle even when re-eliciting the same target.
- Output ONLY the question text. No quotes, no JSON, no markdown.
"""


def generate_question(
    pattern_english: str,
    target_sentence: str,
    context_hint: str | None = None,
    previous_questions: list[str] | None = None,
) -> str:
    """Return a fresh question whose natural answer is target_sentence."""
    previous = previous_questions or []
    context_line = (
        f"SITUATION: {context_hint}"
        if context_hint
        else "SITUATION: pick any fun everyday situation a kid would enjoy"
    )

    user_prompt = f"""{context_line}

PATTERN SKELETON (for reference): {pattern_english}
TARGET_SENTENCE (the exact answer you want the child to say): {target_sentence}

PREVIOUS_QUESTIONS (do not repeat these, even loosely):
{json.dumps(previous, ensure_ascii=False) if previous else '(none)'}

Now output ONE short question that will naturally make the child answer with the TARGET_SENTENCE.
"""

    text = generate_content(
        user_prompt,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=1.0,
    )
    return text.strip().strip('"').strip("'")


if __name__ == "__main__":
    pattern = "Can I have a ___?"
    sentences = [
        ("Can I have a cookie?", "snack shop"),
        ("Can I have some water?", "playground"),
        ("Can I have a pencil?", "library"),
    ]
    history: list[str] = []
    for i, (target, ctx) in enumerate(sentences, start=1):
        q = generate_question(
            pattern_english=pattern,
            target_sentence=target,
            context_hint=ctx,
            previous_questions=history,
        )
        print(f"[{i}] target={target!r} ctx={ctx!r}")
        print(f"    Q: {q}")
        history.append(q)
