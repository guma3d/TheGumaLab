from __future__ import annotations

import io
import time
import textwrap
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from pypdf import PdfReader


# Project root. The generator lives in /tools, while outputs and assets live one level up.
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reptile_reports"
IMG_DIR = OUT_DIR / "images"
PAGE_DIR = OUT_DIR / "pages"

W, H = 1920, 1080
PDF_RESOLUTION = 144.0


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path(r"C:\Windows\Fonts\malgunbd.ttf" if bold else r"C:\Windows\Fonts\malgun.ttf"),
        Path(r"C:\Windows\Fonts\NotoSansKR-Bold.ttf" if bold else r"C:\Windows\Fonts\NotoSansKR-Regular.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


FONTS = {
    "title": font(112, True),
    "subtitle": font(48, False),
    "h1": font(72, True),
    "h2": font(48, True),
    "body": font(38, False),
    "body_bold": font(38, True),
    "small": font(26, False),
    "tiny": font(20, False),
    "quiz": font(96, True),
    "answer": font(72, True),
}


def ensure_dirs() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    IMG_DIR.mkdir(exist_ok=True)
    PAGE_DIR.mkdir(exist_ok=True)


def download_image(name: str, url: str) -> Path:
    path = IMG_DIR / f"{name}.jpg"
    if path.exists() and path.stat().st_size > 10_000:
        return path

    last_error: Exception | None = None
    for attempt in range(4):
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Codex educational PDF generator; contact guma3d@gmail.com"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()
            break
        except Exception as exc:
            last_error = exc
            time.sleep(4 + attempt * 4)
    else:
        raise RuntimeError(f"Failed to download image for {name}: {last_error}") from last_error

    image = Image.open(io.BytesIO(data)).convert("RGB")
    image.save(path, quality=95)
    return path


def fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def rounded_image(image: Image.Image, radius: int = 36) -> Image.Image:
    image = image.convert("RGBA")
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, image.size[0], image.size[1]), radius=radius, fill=255)
    image.putalpha(mask)
    return image


def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int] | tuple[int, int, int, int],
    radius: int = 28,
    outline: tuple[int, int, int] | None = None,
    width: int = 3,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[2] - bbox[0]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    paragraphs = text.split("\n")
    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if text_width(draw, trial, fnt) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                if text_width(draw, word, fnt) <= max_width:
                    current = word
                else:
                    chunks = textwrap.wrap(word, width=16)
                    lines.extend(chunks[:-1])
                    current = chunks[-1]
        if current:
            lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    fnt: ImageFont.ImageFont,
    max_width: int,
    fill: tuple[int, int, int] = (32, 39, 49),
    line_gap: int = 14,
    bullet: bool = False,
) -> int:
    x, y = xy
    if bullet:
        bullet_indent = 34
        lines = wrap_text(draw, text, fnt, max_width - bullet_indent)
        draw.text((x, y), "•", font=fnt, fill=fill)
        for i, line in enumerate(lines):
            draw.text((x + bullet_indent, y), line, font=fnt, fill=fill)
            y += fnt.size + line_gap
        return y

    for line in wrap_text(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def draw_footer(draw: ImageDraw.ImageDraw, text: str, page_num: int, accent: tuple[int, int, int]) -> None:
    draw.line((120, 1012, 1800, 1012), fill=(218, 224, 232), width=2)
    draw.text((120, 1028), text, font=FONTS["tiny"], fill=(91, 99, 112))
    draw_rounded_rect(draw, (1710, 1022, 1800, 1062), fill=accent, radius=18)
    draw.text((1738, 1029), f"{page_num}/4", font=FONTS["tiny"], fill=(255, 255, 255))


def page_cover(item: dict, image_path: Path) -> Image.Image:
    page = fit_image(image_path, (W, H)).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H):
        alpha = int(175 * max(0, (y - 470) / 610))
        od.line((0, y, W, y), fill=(0, 0, 0, alpha))
    od.rectangle((0, 0, W, 140), fill=(*item["accent"], 118))
    page = Image.alpha_composite(page, overlay).convert("RGB")
    draw = ImageDraw.Draw(page)

    draw.text((118, 686), item["name"], font=FONTS["title"], fill=(255, 255, 255))
    draw.text((125, 810), item["tagline"], font=FONTS["subtitle"], fill=(240, 248, 255))
    draw_rounded_rect(draw, (120, 90, 420, 148), fill=item["accent"], radius=28)
    draw.text((150, 102), "파충류 탐구", font=FONTS["small"], fill=(255, 255, 255))
    draw_footer(draw, "사진: Wikimedia Commons", 1, item["accent"])
    return page


def page_basic(item: dict, image_path: Path) -> Image.Image:
    page = Image.new("RGB", (W, H), item["bg"])
    draw = ImageDraw.Draw(page)
    draw.rectangle((0, 0, 1920, 150), fill=item["accent"])
    draw.text((120, 43), "기본 설명", font=FONTS["h1"], fill=(255, 255, 255))
    draw.text((1390, 62), item["name"], font=FONTS["h2"], fill=(255, 255, 255))

    img = fit_image(image_path, (610, 670))
    page.paste(rounded_image(img, 36), (120, 235), rounded_image(img, 36))

    x, y = 790, 225
    for label, value in item["basic"]:
        draw_rounded_rect(draw, (x, y, x + 165, y + 58), fill=item["accent"], radius=24)
        draw.text((x + 24, y + 10), label, font=FONTS["small"], fill=(255, 255, 255))
        y = draw_wrapped(
            draw,
            value,
            (x + 190, y + 5),
            FONTS["body"],
            840,
            fill=(31, 41, 55),
            line_gap=10,
        ) + 16

    draw_footer(draw, "기본 정보: 나무위키/나무모에 및 공개 생물 자료를 초등 발표용으로 정리", 2, item["accent"])
    return page


def page_quiz(item: dict) -> Image.Image:
    page = Image.new("RGB", (W, H), item["quiz_bg"])
    draw = ImageDraw.Draw(page)
    draw.rectangle((0, 0, W, 120), fill=item["accent"])
    draw.text((120, 31), "퀴즈", font=FONTS["h1"], fill=(255, 255, 255))

    draw.text((120, 190), "생각해 보기", font=FONTS["quiz"], fill=item["accent"])
    draw_wrapped(draw, item["quiz_question"], (125, 328), FONTS["h2"], 1520, fill=(31, 41, 55), line_gap=18)

    y = 565
    for idx, choice in enumerate(item["choices"], start=1):
        draw_rounded_rect(
            draw,
            (140, y, 1780, y + 96),
            fill=(255, 255, 255),
            radius=30,
            outline=item["accent"],
            width=4,
        )
        draw_rounded_rect(draw, (170, y + 20, 230, y + 76), fill=item["accent"], radius=22)
        draw.text((190, y + 26), str(idx), font=FONTS["small"], fill=(255, 255, 255))
        draw.text((270, y + 26), choice, font=FONTS["body"], fill=(31, 41, 55))
        y += 125

    draw_footer(draw, "다음 페이지에서 정답을 확인해요.", 3, item["accent"])
    return page


def page_answer(item: dict, image_path: Path) -> Image.Image:
    page = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(page)
    draw.rectangle((0, 0, W, 132), fill=item["accent"])
    draw.text((120, 34), "정답과 특이한 점", font=FONTS["h1"], fill=(255, 255, 255))

    img = fit_image(image_path, (470, 470))
    page.paste(rounded_image(img, 40), (1220, 220), rounded_image(img, 40))

    draw_rounded_rect(draw, (120, 210, 1120, 360), fill=item["answer_fill"], radius=40)
    draw.text((170, 248), "정답", font=FONTS["h2"], fill=item["accent"])
    draw_wrapped(draw, item["answer"], (330, 238), FONTS["answer"], 720, fill=(18, 24, 38), line_gap=10)

    y = 430
    for point in item["details"]:
        y = draw_wrapped(draw, point, (150, y), FONTS["body"], 1000, fill=(31, 41, 55), line_gap=13, bullet=True) + 8

    draw.text((1225, 735), "발표 팁", font=FONTS["h2"], fill=item["accent"])
    draw_wrapped(draw, item["present_tip"], (1225, 800), FONTS["body"], 540, fill=(31, 41, 55), line_gap=13)
    draw_footer(draw, item["sources"], 4, item["accent"])
    return page


def save_pdf(item: dict, pages: list[Image.Image]) -> Path:
    pdf_path = OUT_DIR / f"{item['slug']}_보고서_가로형.pdf"
    rgb_pages = [page.convert("RGB") for page in pages]
    rgb_pages[0].save(
        pdf_path,
        "PDF",
        resolution=PDF_RESOLUTION,
        save_all=True,
        append_images=rgb_pages[1:],
    )
    return pdf_path


def save_contact_sheet(all_pages: list[tuple[str, int, Image.Image]]) -> Path:
    thumb_w, thumb_h = 480, 270
    gap = 28
    label_h = 46
    rows = (len(all_pages) + 3) // 4
    sheet_w = gap + 4 * (thumb_w + gap)
    sheet_h = gap + rows * (thumb_h + label_h + gap)
    sheet = Image.new("RGB", (sheet_w, sheet_h), (248, 250, 252))
    draw = ImageDraw.Draw(sheet)

    for idx, (name, page_num, image) in enumerate(all_pages):
        row, col = divmod(idx, 4)
        x = gap + col * (thumb_w + gap)
        y = gap + row * (thumb_h + label_h + gap)
        thumb = image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, y))
        draw.text((x, y + thumb_h + 10), f"{name} {page_num}/4", font=FONTS["tiny"], fill=(31, 41, 55))

    path = OUT_DIR / "QA_contact_sheet.jpg"
    sheet.save(path, quality=92)
    return path


ITEMS = [
    {
        "slug": "바다이구아나",
        "name": "바다이구아나",
        "tagline": "바다에서 먹이를 찾는 특별한 도마뱀",
        "accent": (0, 118, 137),
        "bg": (235, 250, 252),
        "quiz_bg": (231, 247, 250),
        "answer_fill": (222, 246, 249),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/4/4e/Marine_Iguana_%2850142080922%29.jpg",
        "basic": [
            ("사는 곳", "에콰도르 갈라파고스 제도"),
            ("지역", "바닷가 바위와 얕은 바다"),
            ("먹이", "바닷속 해조류"),
            ("특징", "헤엄쳐서 먹이를 찾는 아주 드문 도마뱀"),
        ],
        "quiz_question": "바다이구아나는 바닷속 해조류를 먹어요. 몸속에 들어온 소금은 어떻게 없앨까요?",
        "choices": ["물을 아주 많이 마셔요.", "코로 소금을 재채기하듯 내보내요.", "꼬리를 흔들어 소금을 떨어뜨려요."],
        "answer": "코로 소금을 뿜어내요.",
        "details": [
            "바다이구아나는 해조류를 먹으면서 소금도 함께 먹게 돼요.",
            "코 근처의 특별한 기관이 소금을 걸러내고, 재채기처럼 밖으로 내보내요.",
            "코 주변이 하얗게 보일 때가 있는데, 말라붙은 소금 때문이에요.",
        ],
        "present_tip": "“소금을 재채기하는 도마뱀”이라고 소개하면 기억하기 쉬워요.",
        "sources": "자료: National Geographic, Galapagos Conservation Trust, Wikimedia Commons",
    },
    {
        "slug": "가비알",
        "name": "가비알",
        "tagline": "길고 가느다란 주둥이를 가진 악어 친척",
        "accent": (47, 112, 79),
        "bg": (240, 249, 244),
        "quiz_bg": (237, 248, 242),
        "answer_fill": (226, 244, 234),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/1/1d/Gavialis_gangeticus.jpg",
        "basic": [
            ("사는 곳", "현재는 주로 인도와 네팔"),
            ("지역", "큰 강, 깊은 민물, 모래톱"),
            ("먹이", "물고기와 작은 물속 동물"),
            ("특징", "긴 주둥이와 가는 이빨을 가진 위급 멸종위기종"),
        ],
        "quiz_question": "가비알의 길고 가느다란 주둥이는 무엇을 잡기 좋게 발달했을까요?",
        "choices": ["큰 사슴", "물고기", "나뭇잎"],
        "answer": "물고기를 잡기 좋아요.",
        "details": [
            "가비알의 주둥이는 물속에서 빠르게 움직이며 물고기를 낚아채기 좋게 생겼어요.",
            "날카롭고 가는 이빨이 많아서 미끄러운 물고기를 붙잡는 데 유리해요.",
            "수컷은 주둥이 끝에 ‘가라’라는 둥근 혹이 생겨요. 소리를 내거나 짝을 찾을 때 도움을 준다고 알려져 있어요.",
        ],
        "present_tip": "주둥이를 보고 “물고기 사냥용 집게”라고 비유하면 친구들이 이해하기 쉬워요.",
        "sources": "자료: 나무위키/나무모에, National Geographic, Smithsonian, Wikimedia Commons",
    },
    {
        "slug": "도마뱀붙이",
        "name": "도마뱀붙이",
        "tagline": "벽과 천장을 걸어 다니는 작은 파충류",
        "accent": (184, 112, 31),
        "bg": (255, 247, 235),
        "quiz_bg": (255, 244, 224),
        "answer_fill": (255, 237, 213),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/b/b3/Tokay_Gecko_%28Gekko_gecko%29.jpg",
        "basic": [
            ("사는 곳", "따뜻한 지역에 널리 살고, 한국에도 일부 서식"),
            ("지역", "숲, 바위, 집 주변의 벽과 천장"),
            ("먹이", "곤충과 거미"),
            ("특징", "주로 밤에 활동하고 발바닥 구조가 특별함"),
        ],
        "quiz_question": "도마뱀붙이는 접착제나 빨판 없이도 벽과 천장에 붙어요. 비밀은 무엇일까요?",
        "choices": ["발바닥의 아주 작은 털 구조", "몸에서 나오는 끈끈한 액체", "꼬리 끝의 갈고리"],
        "answer": "발바닥의 작은 털이에요.",
        "details": [
            "도마뱀붙이의 발바닥에는 눈에 잘 보이지 않는 작은 털 같은 구조가 많아요.",
            "이 구조가 벽 표면과 아주 가깝게 닿아 붙는 힘을 만들어 내요.",
            "발가락 각도를 바꾸면 쉽게 떼어낼 수 있어서 빠르게 걸을 수 있어요.",
        ],
        "present_tip": "빨판도 풀도 아닌 ‘발바닥 기술’이라고 말하면 핵심이 잘 전달돼요.",
        "sources": "자료: 나무위키/나무모에, Britannica, NIST, Wikimedia Commons",
    },
    {
        "slug": "뿔도마뱀",
        "name": "뿔도마뱀",
        "tagline": "작은 공룡처럼 생긴 방어의 달인",
        "accent": (157, 70, 43),
        "bg": (255, 244, 237),
        "quiz_bg": (255, 239, 231),
        "answer_fill": (255, 228, 216),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/3/30/Desert_Horned_Lizard.jpg",
        "basic": [
            ("사는 곳", "주로 미국과 멕시코"),
            ("지역", "사막, 반사막, 건조한 초원과 모래땅"),
            ("먹이", "개미와 작은 곤충"),
            ("특징", "납작한 몸, 짧은 꼬리, 머리의 뿔"),
        ],
        "quiz_question": "뿔도마뱀은 위협을 받으면 몸을 부풀리기도 해요. 그래도 위험하면 무엇을 할까요?",
        "choices": ["눈 주변에서 피를 뿜어요.", "날개를 펴고 날아가요.", "물속으로 오래 숨어요."],
        "answer": "눈 주변에서 피를 뿜어요.",
        "details": [
            "일부 뿔도마뱀은 아주 위험할 때 눈 모서리 쪽에서 피를 뿜는 방어 행동을 해요.",
            "이 행동은 적을 놀라게 해서 도망갈 시간을 벌기 위한 마지막 방법이에요.",
            "항상 쓰는 기술은 아니고, 위급한 상황에서 드물게 사용하는 방어법이에요.",
        ],
        "present_tip": "“눈에서 피를 뿜는 도마뱀”이라고 시작하면 발표를 듣는 사람이 바로 집중해요.",
        "sources": "자료: Britannica, National Park Service, Arizona-Sonora Desert Museum, Wikimedia Commons",
    },
    {
        "slug": "바실리스크도마뱀",
        "name": "바실리스크도마뱀",
        "tagline": "물 위를 달리는 ‘예수도마뱀’",
        "accent": (16, 128, 94),
        "bg": (236, 253, 245),
        "quiz_bg": (232, 250, 242),
        "answer_fill": (209, 250, 229),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Plumedbasiliskcele4_edit.jpg/1280px-Plumedbasiliskcele4_edit.jpg",
        "basic": [
            ("사는 곳", "멕시코 남부, 중앙아메리카, 남아메리카 북부"),
            ("지역", "강과 개울 가까운 열대우림"),
            ("먹이", "곤충, 작은 동물, 과일"),
            ("특징", "위험할 때 뒷다리로 물 위를 짧게 달릴 수 있음"),
        ],
        "quiz_question": "바실리스크도마뱀은 위험할 때 물 위를 달릴 수 있어요. 어떻게 가능한 걸까요?",
        "choices": ["빠른 뒷다리와 넓게 펴지는 발가락 덕분이에요.", "몸에서 공기주머니가 부풀어 떠올라요.", "물속에 보이지 않는 길을 만들어 둬요."],
        "answer": "빠른 발과 발가락 덕분이에요.",
        "details": [
            "바실리스크도마뱀은 뒷다리를 매우 빠르게 움직여 물을 강하게 밀어요.",
            "긴 발가락과 가장자리의 작은 막이 순간적으로 발 면적을 넓혀 줘요.",
            "그래도 오래 달리지는 못해서, 속도가 줄면 물속으로 뛰어들어 헤엄치거나 잠수해요.",
        ],
        "present_tip": "“사람은 못 하지만 이 도마뱀은 물 위를 달려요”라고 시작하면 좋아요.",
        "sources": "자료: Smithsonian National Zoo, National Geographic, Wikimedia Commons",
    },
    {
        "slug": "아르마딜로도마뱀",
        "name": "아르마딜로도마뱀",
        "tagline": "꼬리를 물고 둥글게 마는 방패 도마뱀",
        "accent": (117, 83, 42),
        "bg": (250, 246, 237),
        "quiz_bg": (249, 240, 222),
        "answer_fill": (245, 230, 205),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Armadillo_girdle-tailed_lizard.jpg/1280px-Armadillo_girdle-tailed_lizard.jpg",
        "basic": [
            ("사는 곳", "남아프리카 공화국 서쪽 해안 근처"),
            ("지역", "건조한 바위 지대와 사막성 지역"),
            ("먹이", "흰개미와 작은 곤충"),
            ("특징", "단단한 비늘과 가시가 많고, 무리 지어 살기도 함"),
        ],
        "quiz_question": "아르마딜로도마뱀은 적이 다가오면 몸을 어떻게 지킬까요?",
        "choices": ["자기 꼬리를 물고 둥글게 말아요.", "몸 색을 투명하게 바꿔요.", "큰 소리로 노래를 불러요."],
        "answer": "둥글게 말아요.",
        "details": [
            "위험하면 자기 꼬리를 입으로 물고 몸을 동그랗게 말아요.",
            "부드러운 배를 안쪽으로 숨기고, 가시가 많은 등과 꼬리를 바깥쪽으로 내세워요.",
            "이 모습이 아르마딜로가 몸을 마는 행동과 비슷해서 이름도 아르마딜로도마뱀이에요.",
        ],
        "present_tip": "손으로 동그라미를 만들며 설명하면 방어 자세가 바로 이해돼요.",
        "sources": "자료: Britannica, Animal Diversity Web, Wikimedia Commons",
    },
    {
        "slug": "마타마타거북",
        "name": "마타마타거북",
        "tagline": "낙엽처럼 숨어 사냥하는 이상한 거북",
        "accent": (99, 102, 58),
        "bg": (248, 250, 232),
        "quiz_bg": (245, 248, 224),
        "answer_fill": (235, 240, 201),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Matamata_turtle_2048x1536.jpg/1280px-Matamata_turtle_2048x1536.jpg",
        "basic": [
            ("사는 곳", "남아메리카 아마존과 오리노코 유역"),
            ("지역", "얕고 느리게 흐르는 민물, 진흙 바닥"),
            ("먹이", "물고기와 작은 물속 동물"),
            ("특징", "머리와 목이 낙엽처럼 울퉁불퉁해서 위장에 좋음"),
        ],
        "quiz_question": "마타마타거북은 빠르게 쫓아가지 않고도 물고기를 잡아요. 어떤 방법을 쓸까요?",
        "choices": ["입을 크게 벌려 물과 먹이를 빨아들여요.", "등껍질에서 그물을 꺼내요.", "물고기에게 소리를 내어 오라고 해요."],
        "answer": "빨아들이듯 잡아요.",
        "details": [
            "마타마타거북은 낙엽처럼 가만히 숨어서 먹이가 가까이 오길 기다려요.",
            "물고기가 가까워지면 입을 크게 벌려 물과 먹이를 함께 빨아들여요.",
            "이런 사냥 방법을 흡입 섭식이라고 해요.",
        ],
        "present_tip": "입으로 ‘훅!’ 하고 빨아들이는 동작을 보여주면 재미있어요.",
        "sources": "자료: World Wildlife Fund, Britannica, Wikimedia Commons",
    },
    {
        "slug": "돼지코거북",
        "name": "돼지코거북",
        "tagline": "돼지코와 바다거북 같은 발을 가진 민물거북",
        "accent": (199, 84, 128),
        "bg": (253, 242, 248),
        "quiz_bg": (252, 235, 244),
        "answer_fill": (251, 218, 235),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Pig-nosed_Turtle_Pengo.jpg/1280px-Pig-nosed_Turtle_Pengo.jpg",
        "basic": [
            ("사는 곳", "호주 북부와 뉴기니 남부"),
            ("지역", "강, 석호, 늪, 민물과 기수 지역"),
            ("먹이", "과일, 수생식물, 새우, 조개, 곤충"),
            ("특징", "돼지처럼 생긴 코와 지느러미 같은 앞발"),
        ],
        "quiz_question": "돼지코거북은 민물거북인데도 바다거북처럼 보이는 부분이 있어요. 무엇일까요?",
        "choices": ["지느러미처럼 생긴 발", "새처럼 나는 날개", "몸에서 빛나는 등껍질"],
        "answer": "지느러미 같은 발이에요.",
        "details": [
            "돼지코거북은 민물에 살지만 앞발이 바다거북의 지느러미처럼 생겼어요.",
            "돼지코처럼 생긴 코는 물 위로 살짝 내밀고 숨쉬기 좋아요.",
            "그래서 물속 생활에 아주 잘 맞게 생긴 독특한 거북이에요.",
        ],
        "present_tip": "코는 돼지, 발은 바다거북이라고 비교하면 기억하기 쉬워요.",
        "sources": "자료: Smithsonian National Zoo, National Aquarium, Wikimedia Commons",
    },
    {
        "slug": "가시악마도마뱀",
        "name": "가시악마도마뱀",
        "tagline": "온몸의 홈으로 물을 입까지 보내는 사막 도마뱀",
        "accent": (181, 83, 15),
        "bg": (255, 247, 237),
        "quiz_bg": (255, 241, 222),
        "answer_fill": (254, 226, 190),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Thornydevil.jpg/1280px-Thornydevil.jpg",
        "basic": [
            ("사는 곳", "오스트레일리아 중부와 서부의 건조 지역"),
            ("지역", "사막, 모래 평원, 건조한 관목지"),
            ("먹이", "주로 개미"),
            ("특징", "온몸이 가시처럼 보이고 피부 사이의 홈이 물길 역할을 함"),
        ],
        "quiz_question": "가시악마도마뱀은 사막에서 물을 마시기 어려워요. 몸에 묻은 물을 어떻게 입까지 보낼까요?",
        "choices": ["피부 홈을 따라 물을 입으로 이동시켜요.", "등의 가시를 빨대처럼 꽂아요.", "꼬리 끝에서 물을 만들어 내요."],
        "answer": "피부 홈을 따라 이동해요.",
        "details": [
            "가시악마도마뱀의 비늘 사이에는 아주 좁은 홈들이 있어요.",
            "이 홈들이 젖은 모래나 이슬의 물을 입 쪽으로 천천히 보내 줘요.",
            "그래서 물을 직접 핥지 않아도 몸 표면의 물을 이용할 수 있어요.",
        ],
        "present_tip": "작은 물길이 몸 전체에 있다고 말하면 아이들이 바로 상상해요.",
        "sources": "자료: Parks Australia, National Geographic, Wikimedia Commons",
    },
    {
        "slug": "팬케이크거북",
        "name": "팬케이크거북",
        "tagline": "납작한 등껍질로 바위틈에 숨는 거북",
        "accent": (101, 84, 50),
        "bg": (250, 248, 240),
        "quiz_bg": (247, 242, 229),
        "answer_fill": (239, 230, 209),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/PancakeTortoise_MalacochersusTornieri57.jpg/1280px-PancakeTortoise_MalacochersusTornieri57.jpg",
        "basic": [
            ("사는 곳", "케냐 남부와 탄자니아 북부·동부"),
            ("지역", "건조한 사바나, 관목지, 바위가 많은 언덕"),
            ("먹이", "마른 풀, 잎, 열매, 다육식물"),
            ("특징", "등껍질이 얇고 납작하며 다른 거북보다 유연함"),
        ],
        "quiz_question": "팬케이크거북은 위험하면 등껍질 안에만 숨지 않아요. 어디로 도망갈까요?",
        "choices": ["좁은 바위틈", "깊은 바닷속", "나무 꼭대기"],
        "answer": "바위틈으로 숨어요.",
        "details": [
            "팬케이크거북의 껍질은 일반 거북보다 납작하고 유연해요.",
            "위험하면 빠르게 바위틈으로 들어가 몸을 단단히 끼워 넣어요.",
            "그래서 높은 돔 모양 껍질보다 얇고 가벼운 껍질이 이 거북에게는 큰 장점이에요.",
        ],
        "present_tip": "납작한 팬케이크 모양이라 바위 사이에 쏙 들어간다고 말하면 쉬워요.",
        "sources": "자료: San Diego Zoo, Oakland Zoo, Wikimedia Commons",
    },
    {
        "slug": "뱀목거북",
        "name": "뱀목거북",
        "tagline": "목이 길어 뱀처럼 보이는 민물거북",
        "accent": (55, 101, 115),
        "bg": (240, 249, 251),
        "quiz_bg": (231, 246, 249),
        "answer_fill": (211, 237, 243),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Snake-necked_Turtle_%28Chelodina_Longicollis%29_%282863782655%29.jpg/1280px-Snake-necked_Turtle_%28Chelodina_Longicollis%29_%282863782655%29.jpg",
        "basic": [
            ("사는 곳", "오스트레일리아 동부와 남동부"),
            ("지역", "늪, 호수, 느린 물길, 민물 습지"),
            ("먹이", "작은 물고기, 올챙이, 곤충, 물속 동물"),
            ("특징", "목이 길고, 머리를 등껍질 안으로 옆으로 접어 넣음"),
        ],
        "quiz_question": "뱀목거북은 목이 아주 길어요. 머리를 숨길 때는 어떻게 넣을까요?",
        "choices": ["목을 옆으로 접어 등껍질 안에 넣어요.", "목을 완전히 빼서 따로 숨겨요.", "목을 등 위로 세워 나뭇가지처럼 보여요."],
        "answer": "옆으로 접어 넣어요.",
        "details": [
            "뱀목거북은 숨을 때 목을 뒤로 곧게 당기지 않고 옆으로 접어요.",
            "긴 목은 먹이를 향해 빠르게 뻗을 수 있어서 사냥에 도움이 돼요.",
            "위협을 받으면 냄새나는 액체를 내보내기도 해서 ‘스팅커’라고 불리기도 해요.",
        ],
        "present_tip": "목을 옆으로 접는 동작을 팔로 흉내 내면 발표가 살아나요.",
        "sources": "자료: Australian Museum, NSW National Parks, Wikimedia Commons",
    },
    {
        "slug": "뉴멕시코채찍꼬리도마뱀",
        "name": "뉴멕시코채찍꼬리도마뱀",
        "tagline": "암컷만으로도 이어지는 신기한 도마뱀",
        "accent": (79, 70, 229),
        "bg": (245, 243, 255),
        "quiz_bg": (239, 237, 255),
        "answer_fill": (224, 222, 255),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/New_Mexico_Whiptail%2C_Rio_Grande_Blvd_NW%2C_Los_Ranchos_de_Albuquerque%2C_NM%2C_US_imported_from_iNaturalist_photo_205773706.jpg/1280px-New_Mexico_Whiptail%2C_Rio_Grande_Blvd_NW%2C_Los_Ranchos_de_Albuquerque%2C_NM%2C_US_imported_from_iNaturalist_photo_205773706.jpg",
        "basic": [
            ("사는 곳", "미국 뉴멕시코·애리조나와 멕시코 북부"),
            ("지역", "건조한 초원, 관목지, 모래땅"),
            ("먹이", "작은 곤충과 절지동물"),
            ("특징", "암컷만 있는 종으로 알려져 있고, 처녀생식으로 번식함"),
        ],
        "quiz_question": "뉴멕시코채찍꼬리도마뱀은 수컷이 없어도 새끼를 이어갈 수 있어요. 어떻게 가능할까요?",
        "choices": ["암컷의 알이 수정 없이 자라요.", "다른 동물이 알을 대신 낳아 줘요.", "꼬리가 떨어져 새끼가 돼요."],
        "answer": "수정 없이 알이 자라요.",
        "details": [
            "이 도마뱀은 암컷만 있는 종으로 유명해요.",
            "알이 수컷의 정자 없이도 발달하는데, 이것을 처녀생식이라고 해요.",
            "그래서 ‘암컷만으로 이어지는 도마뱀’이라는 점이 매우 특이해요.",
        ],
        "present_tip": "어려운 말은 한 번만 말하고, ‘수컷 없이 알이 자란다’고 쉽게 풀어 말해요.",
        "sources": "자료: Animal Diversity Web, Nature, Wikimedia Commons",
    },
    {
        "slug": "인도별거북",
        "name": "인도별거북",
        "tagline": "등껍질에 별무늬가 반짝이는 거북",
        "accent": (188, 141, 31),
        "bg": (255, 251, 235),
        "quiz_bg": (255, 247, 214),
        "answer_fill": (254, 240, 172),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Geochelone_elegans_%28Indian_star_tortoise%29_%2815536373660%29.jpg/1280px-Geochelone_elegans_%28Indian_star_tortoise%29_%2815536373660%29.jpg",
        "basic": [
            ("사는 곳", "인도, 파키스탄, 스리랑카"),
            ("지역", "건조한 풀밭, 관목지, 반건조 숲"),
            ("먹이", "풀, 잎, 꽃, 과일"),
            ("특징", "등껍질의 노란 선이 별 모양 무늬를 만듦"),
        ],
        "quiz_question": "인도별거북의 등껍질 무늬는 왜 ‘별’처럼 보일까요?",
        "choices": ["노란 선들이 중심에서 바깥으로 퍼져요.", "밤이 되면 등껍질이 실제로 빛나요.", "별 모양 조개를 붙이고 다녀요."],
        "answer": "노란 선이 퍼져 보여요.",
        "details": [
            "등껍질의 각 판에는 밝은 노란 선들이 중심에서 바깥쪽으로 퍼져 있어요.",
            "이 선들이 별이나 불꽃처럼 보여서 인도별거북이라는 이름이 붙었어요.",
            "예쁜 무늬 때문에 불법 거래의 위험도 있어서 보호가 필요한 동물이에요.",
        ],
        "present_tip": "사진을 가리키며 별무늬를 하나씩 찾아보게 하면 참여도가 좋아요.",
        "sources": "자료: Utica Zoo, IUCN-linked references, Wikimedia Commons",
    },
    {
        "slug": "바다뱀",
        "name": "바다뱀",
        "tagline": "노처럼 납작한 꼬리로 헤엄치는 독사",
        "accent": (37, 99, 235),
        "bg": (239, 246, 255),
        "quiz_bg": (231, 241, 255),
        "answer_fill": (219, 234, 254),
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/Sea_snake.jpg/1280px-Sea_snake.jpg",
        "basic": [
            ("사는 곳", "인도양과 서태평양의 따뜻한 바다"),
            ("지역", "산호초, 맹그로브, 얕은 바다, 해안 주변"),
            ("먹이", "물고기, 장어류, 물고기 알"),
            ("특징", "독이 있고, 바다 생활에 맞게 꼬리가 납작함"),
        ],
        "quiz_question": "바다뱀은 바닷속에서 헤엄치기 좋게 꼬리가 어떻게 변했을까요?",
        "choices": ["노처럼 납작해졌어요.", "공처럼 둥글어졌어요.", "깃털처럼 갈라졌어요."],
        "answer": "노처럼 납작해졌어요.",
        "details": [
            "바다뱀의 꼬리는 좌우로 납작해서 물을 밀기 좋아요.",
            "몸도 바다 생활에 맞게 변했고, 콧구멍에는 물이 들어가지 않도록 닫히는 구조가 있어요.",
            "독을 가진 뱀이지만 보통 먼저 공격하려 하지 않으니, 야생에서는 절대 만지지 않는 것이 중요해요.",
        ],
        "present_tip": "꼬리를 배의 노와 비교하면 왜 잘 헤엄치는지 쉽게 설명돼요.",
        "sources": "자료: Britannica, Britannica Kids, Wikimedia Commons",
    },
]


def main() -> None:
    ensure_dirs()
    all_pages: list[tuple[str, int, Image.Image]] = []
    pdf_paths: list[Path] = []

    for item in ITEMS:
        image_path = download_image(item["slug"], item["image_url"])
        pages = [
            page_cover(item, image_path),
            page_basic(item, image_path),
            page_quiz(item),
            page_answer(item, image_path),
        ]

        for index, page in enumerate(pages, start=1):
            png_path = PAGE_DIR / f"{item['slug']}_{index}.png"
            page.save(png_path, quality=95)
            all_pages.append((item["slug"], index, page))

        pdf_paths.append(save_pdf(item, pages))

    contact_sheet = save_contact_sheet(all_pages)

    for pdf_path in pdf_paths:
        reader = PdfReader(str(pdf_path))
        page_sizes = []
        for page in reader.pages:
            box = page.mediabox
            page_sizes.append((float(box.width), float(box.height)))
        print(f"{pdf_path.name}: {len(reader.pages)} pages, sizes={page_sizes}")
    print(f"QA contact sheet: {contact_sheet}")


if __name__ == "__main__":
    main()
