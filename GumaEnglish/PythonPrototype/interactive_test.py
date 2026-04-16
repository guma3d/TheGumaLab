"""Interactive CLI — play through one practice session in the terminal.

Each round: Guma asks a question, you type a response, Guma replies.
No continuing dialogue. Press Ctrl+C to exit.

Usage:
    python interactive_test.py
"""
from gemini_eval import evaluate_and_reply
from gemini_question import generate_question

# Stage 1 sample data — later this will be loaded from Curriculum/stages/stage_001.json
STAGE = {
    "pattern_english": "Can I have a ___?",
    "pattern_korean": "~를 가질 수 있나요?",
    "examples": [
        "Can I have a cookie?",
        "Can I have some water?",
        "Can I have a pencil?",
    ],
    "contexts": ["snack shop", "library", "playground"],
}


def run_round(round_num: int, history: list[str], target: str, context: str) -> None:
    print(f"\n===== Round {round_num} — target: {target!r} (ctx: {context}) =====")
    question = generate_question(
        pattern_english=STAGE["pattern_english"],
        target_sentence=target,
        context_hint=context,
        previous_questions=history,
    )
    history.append(question)
    print(f"Guma: {question}")
    response = input("You : ").strip()
    if not response:
        print("(empty — skipped)")
        return
    result = evaluate_and_reply(
        pattern_english=STAGE["pattern_english"],
        question_asked=question,
        learner_response=response,
    )
    mark = "OK" if result.get("used_pattern") else "MISS"
    print(f"Guma: {result.get('reply')}")
    print(f"      [pattern used: {mark}]")


def main() -> None:
    print("GumaEnglish — Practice Session (Stage 1)")
    print(f"Pattern: {STAGE['pattern_english']}  ({STAGE['pattern_korean']})")
    print("Target sentences:")
    for s in STAGE["examples"]:
        print(f"  - {s}")
    print("\n(Ctrl+C to exit)")

    history: list[str] = []
    try:
        for i, (target, ctx) in enumerate(
            zip(STAGE["examples"], STAGE["contexts"]), start=1
        ):
            run_round(i, history, target, ctx)
    except KeyboardInterrupt:
        print("\n\nBye!")


if __name__ == "__main__":
    main()
