from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "Docs" / "season_01"
PDF_PATH = OUT_DIR / "chapter_01.pdf"
LEGACY_PREVIEW_PATH = OUT_DIR / "chapter_01.png"

WIDTH = 1600
HEIGHT = 800
MARGIN = 52
MAX_PAGES = 10
TOTAL_PAGES = 8
LECTURE_FONT_SCALE = 0.92

FONT_DIR = Path("C:/Windows/Fonts")
FONT_REGULAR = FONT_DIR / "malgun.ttf"
FONT_BOLD = FONT_DIR / "malgunbd.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    scaled_size = max(8, round(size * LECTURE_FONT_SCALE))
    return ImageFont.truetype(str(path), scaled_size)


def rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: str | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_width(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font_obj)
    return box[2] - box[0]


def line_height(font_obj: ImageFont.FreeTypeFont, line_gap: int) -> int:
    box = font_obj.getbbox("가Ay")
    return box[3] - box[1] + line_gap


def split_long_token(draw: ImageDraw.ImageDraw, token: str, font_obj: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for char in token:
        candidate = current + char
        if current and text_width(draw, candidate, font_obj) > max_width:
            pieces.append(current)
            current = char
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue

        current = ""
        for token in paragraph.split(" "):
            if text_width(draw, token, font_obj) > max_width:
                if current:
                    lines.append(current)
                    current = ""
                lines.extend(split_long_token(draw, token, font_obj, max_width))
                continue

            candidate = token if not current else f"{current} {token}"
            if text_width(draw, candidate, font_obj) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = token
        if current:
            lines.append(current)
    return lines


def fit_font_for_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    size: int,
    max_width: int,
    bold: bool = False,
    min_size: int = 16,
) -> ImageFont.FreeTypeFont:
    current = size
    while current > min_size:
        font_obj = font(current, bold)
        if text_width(draw, text, font_obj) <= max_width:
            return font_obj
        current -= 1
    return font(min_size, bold)


def draw_fitted_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    size: int,
    fill: str,
    max_width: int,
    bold: bool = False,
    min_size: int = 16,
) -> None:
    font_obj = fit_font_for_width(draw, text, size, max_width, bold, min_size)
    draw.text(xy, text, font=font_obj, fill=fill)


def fit_wrapped_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    size: int,
    max_width: int,
    max_height: int,
    bold: bool = False,
    min_size: int = 15,
    line_gap: int = 8,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    current = size
    while current > min_size:
        font_obj = font(current, bold)
        lines = wrap_text(draw, text, font_obj, max_width)
        height = len(lines) * line_height(font_obj, line_gap)
        if height <= max_height:
            return font_obj, lines, line_height(font_obj, line_gap)
        current -= 1

    font_obj = font(min_size, bold)
    lines = wrap_text(draw, text, font_obj, max_width)
    return font_obj, lines, line_height(font_obj, line_gap)


def draw_wrapped_in_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    size: int,
    fill: str,
    bold: bool = False,
    line_gap: int = 8,
    min_size: int = 15,
    valign: str = "top",
) -> None:
    x1, y1, x2, y2 = box
    max_width = max(1, x2 - x1)
    max_height = max(1, y2 - y1)
    font_obj, lines, step = fit_wrapped_font(draw, text, size, max_width, max_height, bold, min_size, line_gap)

    available_lines = max(1, max_height // step)
    lines = lines[:available_lines]
    used_height = len(lines) * step
    y = y1 + max(0, (max_height - used_height) // 2) if valign == "middle" else y1

    for line in lines:
        draw.text((x1, y), line, font=font_obj, fill=fill)
        y += step


def draw_star(draw: ImageDraw.ImageDraw, cx: int, cy: int, r1: int, r2: int, fill: str, outline: str) -> None:
    points = []
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        radius = r1 if i % 2 == 0 else r2
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    draw.polygon(points, fill=fill, outline=outline)


def draw_coin(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int) -> None:
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill="#ffd35a", outline="#9a6500", width=5)
    draw.text((cx - 13, cy - 28), "$", font=font(43, True), fill="#805000")


def draw_mascot(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0) -> None:
    head = int(82 * scale)
    body_w = int(96 * scale)
    body_h = int(100 * scale)
    eye = int(13 * scale)
    width = max(3, int(7 * scale))

    draw.ellipse((cx - head, cy - head, cx + head, cy + head), fill="#68b8ff", outline="#1d4d91", width=width)
    draw.rectangle(
        (cx - body_w // 2, cy + int(62 * scale), cx + body_w // 2, cy + int(62 * scale) + body_h),
        fill="#2dd4bf",
        outline="#0f766e",
        width=width,
    )
    draw.ellipse((cx - int(42 * scale), cy - int(24 * scale), cx - int(42 * scale) + eye * 2, cy - int(24 * scale) + eye * 2), fill="white")
    draw.ellipse((cx + int(22 * scale), cy - int(24 * scale), cx + int(22 * scale) + eye * 2, cy - int(24 * scale) + eye * 2), fill="white")
    draw.arc(
        (cx - int(42 * scale), cy + int(8 * scale), cx + int(42 * scale), cy + int(68 * scale)),
        20,
        160,
        fill="white",
        width=max(3, int(5 * scale)),
    )


def draw_background(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill="#fff8e8")
    for x in range(-80, WIDTH + 80, 150):
        draw.ellipse((x, -52, x + 194, 104), fill="#e7f7ff")
    draw.rectangle((0, HEIGHT - 94, WIDTH, HEIGHT), fill="#e9f8ec")
    for x in range(-40, WIDTH + 80, 180):
        draw_star(draw, x + 42, HEIGHT - 68, 17, 8, "#ffe79a", "#f2c94c")


def draw_footer(draw: ImageDraw.ImageDraw, page: int, total: int) -> None:
    draw.text((MARGIN, HEIGHT - 44), "Guma Python Lab", font=font(20, True), fill="#2f4d64")
    draw.text((WIDTH - MARGIN - 112, HEIGHT - 44), f"{page} / {total}", font=font(20, True), fill="#2f4d64")


def draw_title(draw: ImageDraw.ImageDraw, chapter: str, title: str, subtitle: str) -> None:
    rounded(draw, (MARGIN, 46, WIDTH - MARGIN, 154), 32, "#193654")
    draw_fitted_text(draw, (MARGIN + 34, 72), chapter, 34, "#ffd35a", 140, True, 24)
    draw_fitted_text(draw, (MARGIN + 194, 70), title, 43, "#ffffff", 550, True, 28)
    draw_wrapped_in_box(draw, (MARGIN + 780, 76, WIDTH - MARGIN - 34, 132), subtitle, 24, "#cfeaff", min_size=17, valign="middle")


def draw_code_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], code: str, caption: str | None = None) -> None:
    rounded(draw, box, 26, "#142033")
    x1, y1, x2, _ = box
    if caption:
        draw_fitted_text(draw, (x1 + 36, y1 + 28), caption, 29, "#ffffff", x2 - x1 - 72, True, 18)
        code_y = y1 + 92
    else:
        code_y = y1 + 42
    rounded(draw, (x1 + 36, code_y, x2 - 36, code_y + 92), 18, "#0f172a", "#516174", 3)
    draw_fitted_text(draw, (x1 + 62, code_y + 28), code, 35, "#fbbf24", x2 - x1 - 124, True, 18)


def draw_game_preview(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    rounded(draw, box, 26, "#e8f4ff", "#8ec5f5", 4)
    draw.rectangle((x1, y1, x2, y1 + 58), fill="#18324a")
    draw_fitted_text(draw, (x1 + 30, y1 + 16), "보물 점수 게임", 25, "#ffffff", x2 - x1 - 60, True, 18)
    draw_coin(draw, x1 + 112, y1 + 150, 34)
    draw_star(draw, x2 - 116, y1 + 142, 39, 18, "#9b7cff", "#5a3fd8")
    draw_mascot(draw, (x1 + x2) // 2, y1 + 162, 0.48)
    draw_fitted_text(draw, (x1 + 28, y2 - 46), "보물 찾으러 출발!", 24, "#6b4a00", x2 - x1 - 56, True, 17)


def page_1() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#fff8e8")
    draw = ImageDraw.Draw(image)
    draw_background(draw)

    rounded(draw, (MARGIN, 54, 600, HEIGHT - 102), 42, "#193654")
    draw_fitted_text(draw, (MARGIN + 42, 96), "챕터 1", 50, "#ffd35a", 420, True, 30)
    draw_wrapped_in_box(draw, (MARGIN + 42, 178, MARGIN + 470, 320), "게임 화면에 인사하기", 58, "#ffffff", True, line_gap=12, min_size=34)
    draw_wrapped_in_box(draw, (MARGIN + 42, 372, MARGIN + 462, 480), "게임을 처음 켰을 때 나오는 말을 내 말로 바꿔요.", 31, "#cfeaff", line_gap=10)
    draw_mascot(draw, 390, 570, 0.72)

    rounded(draw, (650, 92, WIDTH - MARGIN, 312), 34, "#ffffff", "#f5c84c", 5)
    draw_star(draw, 710, 158, 31, 14, "#ffd35a", "#ad7600")
    draw_fitted_text(draw, (760, 128), "오늘의 목표", 38, "#193654", 600, True)
    draw_wrapped_in_box(
        draw,
        (760, 196, WIDTH - MARGIN - 40, 286),
        "오른쪽 파이썬 화면에서 한 줄을 바꾸고, 왼쪽 아래 게임 화면에서 바로 확인해요.",
        29,
        "#26384f",
    )

    rounded(draw, (650, 358, WIDTH - MARGIN, 642), 34, "#f1f8ff", "#b7d9ff", 5)
    draw_fitted_text(draw, (700, 404), "오늘 사용할 화면", 35, "#193654", 600, True)
    draw_fitted_text(draw, (716, 486), "1. 강의자료: 지금 보는 안내", 27, "#26384f", 720)
    draw_fitted_text(draw, (716, 544), "2. 파이썬 화면: 문장 바꾸기", 27, "#26384f", 720)
    draw_fitted_text(draw, (716, 602), "3. 게임화면: Play 결과 확인", 27, "#26384f", 720)

    draw_footer(draw, 1, TOTAL_PAGES)
    return image


def page_2() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#fff8e8")
    draw = ImageDraw.Draw(image)
    draw_background(draw)
    draw_title(draw, "챕터 1", "찾아야 할 코드", "오른쪽의 문장을 바꿔요")

    draw_code_box(draw, (MARGIN, 210, WIDTH - MARGIN, 420), 'start_message = "모험 시작!"', "오른쪽 파이썬 화면에서 이 줄을 찾아요")

    rounded(draw, (MARGIN, 468, 752, 660), 30, "#ffffff", "#f5c84c", 4)
    draw_fitted_text(draw, (MARGIN + 38, 510), "바꿀 곳", 32, "#193654", 560, True)
    draw_fitted_text(draw, (MARGIN + 38, 575), '"모험 시작!"', 34, "#be185d", 560, True)

    rounded(draw, (812, 468, WIDTH - MARGIN, 660), 30, "#ffffff", "#b7d9ff", 4)
    draw_fitted_text(draw, (850, 510), "기억하기", 32, "#193654", 560, True)
    draw_wrapped_in_box(draw, (850, 572, WIDTH - MARGIN - 40, 642), "따옴표 안에 있는 글자는 파이썬이 글자로 기억하는 값이에요.", 27, "#26384f")

    draw_footer(draw, 2, TOTAL_PAGES)
    return image


def page_3() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#fff8e8")
    draw = ImageDraw.Draw(image)
    draw_background(draw)
    draw_title(draw, "챕터 1", "자료형이 뭐야?", "파이썬은 값의 종류를 구분해요")

    rounded(draw, (MARGIN, 214, 760, 650), 34, "#ffffff", "#b7d9ff", 5)
    draw_fitted_text(draw, (MARGIN + 42, 260), "자료형", 40, "#193654", 560, True)
    draw_wrapped_in_box(
        draw,
        (MARGIN + 42, 338, 710, 488),
        "자료형은 파이썬이 값을 어떤 종류로 기억하는지 알려주는 이름이에요.",
        31,
        "#26384f",
        line_gap=10,
    )
    draw_wrapped_in_box(draw, (MARGIN + 42, 520, 710, 610), "글자, 숫자, 참/거짓처럼 값마다 종류가 달라요.", 27, "#40566f")

    rounded(draw, (840, 214, WIDTH - MARGIN, 650), 34, "#fff0f6", "#ff9ec7", 5)
    draw_fitted_text(draw, (882, 260), "오늘 만나는 자료형", 37, "#9d174d", 560, True)
    draw_code_box(draw, (882, 340, WIDTH - MARGIN - 40, 515), '"모험 시작!"', "문자열 str")
    draw_wrapped_in_box(draw, (882, 560, WIDTH - MARGIN - 42, 625), "따옴표 안의 말은 문자열이에요.", 27, "#be185d", True)

    draw_footer(draw, 3, TOTAL_PAGES)
    return image


def page_4() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#fff8e8")
    draw = ImageDraw.Draw(image)
    draw_background(draw)
    draw_title(draw, "챕터 1", "문자열과 숫자", "따옴표가 있으면 글자로 기억해요")

    rounded(draw, (MARGIN, 214, 760, 650), 34, "#142033")
    draw_fitted_text(draw, (MARGIN + 42, 260), "문자열 str", 38, "#ffffff", 560, True)
    rounded(draw, (MARGIN + 42, 344, 720, 444), 20, "#0f172a", "#516174", 3)
    draw_fitted_text(draw, (MARGIN + 72, 372), 'hero_name = "번개용사"', 31, "#fbbf24", 610, True, 18)
    draw_wrapped_in_box(draw, (MARGIN + 42, 500, 720, 610), "따옴표 안에 들어간 값은 글자로 기억해요.", 27, "#cfeaff")

    rounded(draw, (840, 214, WIDTH - MARGIN, 650), 34, "#ffffff", "#f5c84c", 5)
    draw_fitted_text(draw, (882, 260), "숫자 int", 38, "#193654", 560, True)
    rounded(draw, (882, 344, WIDTH - MARGIN - 42, 444), 20, "#fff8e8", "#f5c84c", 3)
    draw_fitted_text(draw, (912, 372), "start_score = 10", 31, "#9a6500", 560, True, 18)
    draw_wrapped_in_box(draw, (882, 500, WIDTH - MARGIN - 42, 610), "따옴표가 없는 수는 계산할 수 있는 숫자로 기억해요.", 27, "#26384f")

    draw_footer(draw, 4, TOTAL_PAGES)
    return image


def page_5() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#fff8e8")
    draw = ImageDraw.Draw(image)
    draw_background(draw)
    draw_title(draw, "챕터 1", "문장을 바꿔 보기", "내가 원하는 말로 업그레이드")

    draw_code_box(draw, (MARGIN, 214, 760, 448), 'start_message = "모험 시작!"', "바꾸기 전")
    draw_fitted_text(draw, (790, 314), "->", 60, "#193654", 70, True)
    draw_code_box(draw, (880, 214, WIDTH - MARGIN, 448), 'start_message = "보물 찾으러 출발!"', "바꾼 뒤")

    rounded(draw, (MARGIN, 500, WIDTH - MARGIN, 660), 30, "#fff0f6", "#ff9ec7", 5)
    draw_fitted_text(draw, (MARGIN + 40, 540), "주의!", 33, "#9d174d", 110, True)
    draw_wrapped_in_box(
        draw,
        (MARGIN + 160, 540, WIDTH - MARGIN - 50, 630),
        "따옴표는 지우지 말아요. 따옴표 안의 말만 바꾸면 됩니다.",
        29,
        "#5f2742",
    )

    draw_footer(draw, 5, TOTAL_PAGES)
    return image


def page_6() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#fff8e8")
    draw = ImageDraw.Draw(image)
    draw_background(draw)
    draw_title(draw, "챕터 1", "Play 해보기", "바꾼 코드가 게임에 바로 들어가요")

    rounded(draw, (MARGIN, 214, 640, 660), 34, "#ffffff", "#f5c84c", 5)
    draw_star(draw, 112, 282, 31, 14, "#ffd35a", "#ad7600")
    draw_fitted_text(draw, (164, 254), "순서", 36, "#193654", 380, True)
    steps = [
        "1. 오른쪽 코드를 바꿔요.",
        "2. 저장 또는 Play를 눌러요.",
        "3. 게임 첫 메시지를 봐요.",
        "4. 다시 바꾸고 또 Play!",
    ]
    y = 350
    for step in steps:
        draw_fitted_text(draw, (112, y), step, 28, "#26384f", 470)
        y += 62

    draw_game_preview(draw, (720, 234, WIDTH - MARGIN, 630))

    draw_footer(draw, 6, TOTAL_PAGES)
    return image


def page_7() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#fff8e8")
    draw = ImageDraw.Draw(image)
    draw_background(draw)
    draw_title(draw, "챕터 1", "미션과 퀴즈", "정답은 다음 페이지에서 확인해요")

    rounded(draw, (MARGIN, 210, 760, 660), 34, "#ffffff", "#b7d9ff", 5)
    draw_fitted_text(draw, (MARGIN + 42, 260), "미션", 38, "#193654", 560, True)
    missions = ['1. "모험 시작!"', '2. "보물 찾으러 출발!"', '3. "나는 오늘 용사다!"']
    y = 344
    for mission in missions:
        draw_fitted_text(draw, (MARGIN + 60, y), mission, 30, "#26384f", 610)
        y += 72
    draw_wrapped_in_box(draw, (MARGIN + 60, 580, 700, 632), "원하는 문장을 하나 골라 게임 시작 메시지로 바꿔 보세요.", 24, "#40566f")

    rounded(draw, (840, 210, WIDTH - MARGIN, 660), 34, "#fff0f6", "#ff9ec7", 5)
    draw_fitted_text(draw, (882, 260), "작은 퀴즈", 38, "#9d174d", 560, True)
    draw_wrapped_in_box(draw, (882, 332, WIDTH - MARGIN - 42, 426), "Q. 파이썬에서 글자를 기억하는 자료형 이름은 무엇일까요?", 27, "#5f2742", True)
    answers = ["1. 문자열 str", "2. 숫자 int", "3. 방향키 key"]
    y = 456
    for answer in answers:
        draw_fitted_text(draw, (902, y), answer, 25, "#5f2742", 520)
        y += 52
    draw_wrapped_in_box(draw, (902, 604, WIDTH - MARGIN - 52, 640), "힌트: 3페이지의 자료형 설명을 떠올려요.", 20, "#9d174d")

    draw_footer(draw, 7, TOTAL_PAGES)
    return image


def page_8() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#fff8e8")
    draw = ImageDraw.Draw(image)
    draw_background(draw)
    draw_title(draw, "챕터 1", "정답과 해설", "내가 고른 답과 비교해요")

    rounded(draw, (MARGIN, 214, 716, 650), 34, "#ffffff", "#f5c84c", 5)
    draw_star(draw, 118, 284, 31, 14, "#ffd35a", "#ad7600")
    draw_fitted_text(draw, (170, 256), "정답", 40, "#193654", 420, True)
    draw_wrapped_in_box(draw, (MARGIN + 58, 356, 662, 472), "1. 문자열 str", 50, "#be185d", True, line_gap=10, min_size=30, valign="middle")
    draw_wrapped_in_box(draw, (MARGIN + 58, 540, 662, 612), "글자를 기억하는 자료형은 문자열이고, 파이썬 이름은 str이에요.", 25, "#26384f")

    rounded(draw, (776, 214, WIDTH - MARGIN, 650), 34, "#f1f8ff", "#b7d9ff", 5)
    draw_fitted_text(draw, (820, 256), "왜 그럴까?", 38, "#193654", 620, True)
    draw_wrapped_in_box(
        draw,
        (820, 338, WIDTH - MARGIN - 42, 520),
        '자료형은 값의 종류를 말해요. "모험 시작!"처럼 따옴표 안에 있는 글자는 문자열이고, 파이썬 이름은 str이에요.',
        27,
        "#26384f",
        line_gap=10,
    )
    draw_wrapped_in_box(
        draw,
        (820, 552, WIDTH - MARGIN - 42, 620),
        "10처럼 따옴표가 없는 수는 숫자 int로 기억해요.",
        25,
        "#40566f",
    )

    draw_footer(draw, 8, TOTAL_PAGES)
    return image


def generate() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_page in OUT_DIR.glob("chapter_01_p*.png"):
        old_page.unlink()

    pages = [page_1(), page_2(), page_3(), page_4(), page_5(), page_6(), page_7(), page_8()]
    if len(pages) > MAX_PAGES:
        raise RuntimeError(f"챕터 PDF는 최대 {MAX_PAGES}페이지까지만 허용합니다.")

    for index, page in enumerate(pages, start=1):
        page.save(OUT_DIR / f"chapter_01_p{index:02d}.png")

    pages[0].save(LEGACY_PREVIEW_PATH)
    pages[0].save(PDF_PATH, "PDF", resolution=144.0, save_all=True, append_images=pages[1:])
    print(PDF_PATH)
    for index in range(1, len(pages) + 1):
        print(OUT_DIR / f"chapter_01_p{index:02d}.png")


if __name__ == "__main__":
    generate()
