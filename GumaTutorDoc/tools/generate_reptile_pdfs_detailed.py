from __future__ import annotations

import io
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps
from pypdf import PdfReader

from generate_reptile_pdfs import (
    FONTS,
    H,
    IMG_DIR,
    ITEMS,
    OUT_DIR,
    ROOT,
    W,
    download_image,
    draw_rounded_rect,
    draw_wrapped,
    fit_image,
    rounded_image,
    save_pdf,
)


DETAIL_DIR = ROOT / "reptile_reports_detailed"
DETAIL_PAGE_DIR = DETAIL_DIR / "pages"
CURATED_DIR = ROOT / "assets" / "curated_overrides"
PDF_RESOLUTION = 144.0
TOTAL_PAGES = 7
WORLD_GEOJSON = OUT_DIR / "world_countries_110m.geojson"
NE_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"

IMAGE_OVERRIDES = {
    ("뿔도마뱀", "feature"): "horned_lizard_blood_crop.jpg",
    ("뿔도마뱀", "answer"): "horned_lizard_blood_crop.jpg",
    ("바실리스크도마뱀", "feature"): "basilisk_foot_toes_close_b.jpg",
    ("바실리스크도마뱀", "answer"): "basilisk_foot_toes_close_b.jpg",
    ("아르마딜로도마뱀", "feature"): "armadillo_curled_clear.jpg",
    ("아르마딜로도마뱀", "answer"): "armadillo_curled_clear.jpg",
    ("마타마타거북", "answer"): "matamata_suction_feeding_frame.jpg",
    ("가시악마도마뱀", "feature"): "thorny_devil_skin_channels.jpg",
    ("가시악마도마뱀", "answer"): "thorny_devil_skin_channels.jpg",
    ("팬케이크거북", "feature"): "pancake_tortoise_crevice.jpg",
    ("팬케이크거북", "answer"): "pancake_tortoise_crevice.jpg",
    ("바다뱀", "feature"): "sea_snake_paddle_tail_crop.jpg",
    ("바다뱀", "answer"): "sea_snake_paddle_tail_crop.jpg",
}

SOURCE_OVERRIDES = {
    ("마타마타거북", "answer"): "영상 프레임: Reddit r/turtles / 자료: World Wildlife Fund, Britannica",
    ("팬케이크거북", "feature"): "사진: Animal.photos",
    ("팬케이크거북", "answer"): "사진: Animal.photos / 자료: San Diego Zoo, Oakland Zoo",
}


def ensure_dirs() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    IMG_DIR.mkdir(exist_ok=True)
    CURATED_DIR.mkdir(exist_ok=True)
    DETAIL_DIR.mkdir(exist_ok=True)
    DETAIL_PAGE_DIR.mkdir(exist_ok=True)


def safe_key(text: str) -> str:
    bad = '<>:"/\\|?*'
    for ch in bad:
        text = text.replace(ch, "_")
    return text[:120]


def request_bytes(url: str, timeout: int = 60, accept: str = "*/*") -> bytes:
    last_error: Exception | None = None
    for attempt in range(5):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Codex educational PDF generator; contact guma3d@gmail.com",
                "Accept": accept,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except Exception as exc:
            last_error = exc
            time.sleep(3 + attempt * 4)
    raise RuntimeError(f"Could not fetch {url}: {last_error}") from last_error


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def resized_font(fnt, size: int):
    try:
        return fnt.font_variant(size=size)
    except Exception:
        return fnt


def wrap_cjk(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for ch in paragraph:
            trial = current + ch
            if not current or text_size(draw, trial, fnt)[0] <= max_width:
                current = trial
            else:
                lines.append(current.rstrip())
                current = ch.lstrip()
        if current:
            lines.append(current.rstrip())
        elif not paragraph:
            lines.append("")
    return lines


def fit_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    base_font,
    max_width: int,
    max_height: int,
    line_gap: int = 12,
    min_size: int = 24,
) -> tuple[object, list[str], int]:
    base_size = getattr(base_font, "size", 38)
    for size in range(base_size, min_size - 1, -2):
        fnt = resized_font(base_font, size)
        gap = max(6, min(line_gap, int(size * 0.35)))
        lines = wrap_cjk(draw, text, fnt, max_width)
        total_h = len(lines) * size + max(0, len(lines) - 1) * gap
        if total_h <= max_height:
            return fnt, lines, gap

    fnt = resized_font(base_font, min_size)
    gap = max(5, int(min_size * 0.25))
    lines = wrap_cjk(draw, text, fnt, max_width)
    max_lines = max(1, max_height // (min_size + gap))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1].rstrip(" .") + "..."
    return fnt, lines, gap


def draw_text_box(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    base_font,
    fill: tuple[int, int, int],
    line_gap: int = 12,
    min_size: int = 24,
    align: str = "left",
    valign: str = "top",
) -> int:
    x0, y0, x1, y1 = box
    fnt, lines, gap = fit_lines(draw, text, base_font, x1 - x0, y1 - y0, line_gap, min_size)
    total_h = len(lines) * getattr(fnt, "size", 30) + max(0, len(lines) - 1) * gap
    y = y0
    if valign == "middle":
        y = y0 + max(0, (y1 - y0 - total_h) // 2)
    elif valign == "bottom":
        y = y1 - total_h

    for line in lines:
        w, _ = text_size(draw, line, fnt)
        x = x0
        if align == "center":
            x = x0 + max(0, (x1 - x0 - w) // 2)
        elif align == "right":
            x = x1 - w
        draw.text((x, y), line, font=fnt, fill=fill)
        y += getattr(fnt, "size", 30) + gap
    return y


def draw_bullets_box(
    draw: ImageDraw.ImageDraw,
    points: list[str],
    box: tuple[int, int, int, int],
    base_font,
    fill: tuple[int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    text = "\n".join(f"• {point}" for point in points)
    draw_text_box(draw, text, box, base_font, fill, line_gap=10, min_size=25)


def image_hash(path: Path) -> tuple[int, ...] | None:
    try:
        image = Image.open(path).convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(image.getdata())
        bits = []
        for y in range(8):
            row = pixels[y * 9 : (y + 1) * 9]
            for x in range(8):
                bits.append(1 if row[x] > row[x + 1] else 0)
        return tuple(bits)
    except Exception:
        return None


def image_distance(a: tuple[int, ...] | None, b: tuple[int, ...] | None) -> int:
    if a is None or b is None:
        return 64
    return sum(x != y for x, y in zip(a, b))


def add_unique_image(selected: list[Path], path: Path, avoid: list[Path] | None = None, threshold: int = 8) -> bool:
    if not path.exists() or path.stat().st_size <= 10_000:
        return False
    pool = list(selected) + list(avoid or [])
    path_hash = image_hash(path)
    for other in pool:
        if path.resolve() == other.resolve():
            return False
        if image_distance(path_hash, image_hash(other)) <= threshold:
            return False
    selected.append(path)
    return True


def media_search_image(key: str, query: str) -> Path:
    path = IMG_DIR / f"detail_{safe_key(key)}.jpg"
    if path.exists() and path.stat().st_size > 10_000:
        return path

    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "12",
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "iiurlwidth": "1280",
    }
    api_url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    data = json.loads(request_bytes(api_url, timeout=45, accept="application/json").decode("utf-8"))
    pages = list(data.get("query", {}).get("pages", {}).values())
    pages.sort(key=lambda p: p.get("index", 999))

    for page in pages:
        title = page.get("title", "").lower()
        if any(skip in title for skip in ["map", ".svg", "logo", "icon", "range"]):
            continue
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        mime = info.get("mime", "")
        if mime not in {"image/jpeg", "image/png", "image/webp"}:
            continue
        url = info.get("thumburl") or info.get("url")
        if not url:
            continue
        try:
            image = Image.open(io.BytesIO(request_bytes(url, accept="image/avif,image/webp,image/apng,image/*,*/*;q=0.8"))).convert("RGB")
            image.save(path, quality=94)
            time.sleep(0.35)
            return path
        except Exception:
            continue

    # Fallback keeps generation unblocked; the report still gets a species photo.
    fallback_slug = key.split("_", 1)[0]
    fallback = IMG_DIR / f"{fallback_slug}.jpg"
    if fallback.exists():
        return fallback
    raise RuntimeError(f"No usable Commons image for query: {query}")


def query_variants(query: str) -> list[str]:
    replacements = [
        "Wikimedia Commons",
        "photograph",
        "photo",
        "close up",
        "macro",
        "habitat",
        "picture",
    ]
    cleaned = query
    for word in replacements:
        cleaned = cleaned.replace(word, " ")
    cleaned = " ".join(cleaned.split())

    variants: list[str] = []
    for candidate in [query, cleaned]:
        candidate = candidate.strip()
        if candidate and candidate not in variants:
            variants.append(candidate)

    words = cleaned.split()
    for count in (5, 4, 3, 2):
        if len(words) >= count:
            candidate = " ".join(words[:count])
            if candidate and candidate not in variants:
                variants.append(candidate)
    return variants


def media_search_candidates(key: str, query: str, max_count: int = 5) -> list[Path]:
    collected: list[Path] = []
    for variant_index, variant in enumerate(query_variants(query)):
        for candidate in media_search_candidates_once(f"{key}_{variant_index}", variant, max_count=max_count):
            add_unique_image(collected, candidate, threshold=8)
            if len(collected) >= max_count:
                return collected
    return collected


def media_search_candidates_once(key: str, query: str, max_count: int = 5) -> list[Path]:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "24",
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "iiurlwidth": "1280",
    }
    api_url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    try:
        data = json.loads(request_bytes(api_url, timeout=45, accept="application/json").decode("utf-8"))
    except Exception:
        return []

    pages = list(data.get("query", {}).get("pages", {}).values())
    pages.sort(key=lambda p: p.get("index", 999))
    candidates: list[Path] = []
    for rank, page in enumerate(pages):
        title = page.get("title", "").lower()
        if any(skip in title for skip in ["map", ".svg", "logo", "icon", "range", "distribution"]):
            continue
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        if info.get("mime", "") not in {"image/jpeg", "image/png", "image/webp"}:
            continue

        path = IMG_DIR / f"detail2_{safe_key(key)}_{rank}.jpg"
        if path.exists() and path.stat().st_size > 10_000:
            candidates.append(path)
            if len(candidates) >= max_count:
                break
            continue

        url = info.get("thumburl") or info.get("url")
        if not url:
            continue
        try:
            image = Image.open(
                io.BytesIO(request_bytes(url, accept="image/avif,image/webp,image/apng,image/*,*/*;q=0.8"))
            ).convert("RGB")
            image.save(path, quality=94)
            candidates.append(path)
            time.sleep(0.25)
            if len(candidates) >= max_count:
                break
        except Exception:
            continue
    return candidates


def collect_unique_images(slug: str, role: str, queries: list[str], count: int, avoid: list[Path] | None = None) -> list[Path]:
    selected: list[Path] = []
    avoid_paths = list(avoid or [])
    for query_index, query in enumerate(queries):
        for candidate in media_search_candidates(f"{slug}_{role}_{query_index}", query, max_count=6):
            add_unique_image(selected, candidate, avoid_paths)
            if len(selected) >= count:
                return selected

    for query_index, query in enumerate(queries):
        try:
            fallback = media_search_image(f"{slug}_{role}_legacy_{query_index}", query)
            add_unique_image(selected, fallback, avoid_paths)
            if len(selected) >= count:
                return selected
        except Exception:
            continue
    return selected


def complete_image_list(images: list[Path], count: int, fallbacks: list[Path], allow_repeat: bool = False) -> list[Path]:
    selected = list(images)
    for fallback in fallbacks:
        add_unique_image(selected, fallback)
        if len(selected) >= count:
            return selected
    while allow_repeat and selected and len(selected) < count:
        selected.append(selected[-1])
    return selected


def apply_image_override(slug: str, role: str, images: list[Path]) -> list[Path]:
    filename = IMAGE_OVERRIDES.get((slug, role))
    if not filename:
        return images
    path = CURATED_DIR / filename
    if path.exists():
        return [path]
    return images


def source_for(slug: str, role: str, default: str) -> str:
    return SOURCE_OVERRIDES.get((slug, role), default)


def draw_footer(draw: ImageDraw.ImageDraw, source: str, page_num: int, accent: tuple[int, int, int]) -> None:
    draw.line((120, 1012, 1800, 1012), fill=(218, 224, 232), width=2)
    draw.text((120, 1028), source, font=FONTS["tiny"], fill=(91, 99, 112))
    draw_rounded_rect(draw, (1704, 1022, 1800, 1062), fill=accent, radius=18)
    draw.text((1728, 1029), f"{page_num}/{TOTAL_PAGES}", font=FONTS["tiny"], fill=(255, 255, 255))


def draw_header(draw: ImageDraw.ImageDraw, item: dict, title: str) -> None:
    draw.rectangle((0, 0, W, 132), fill=item["accent"])
    draw.text((120, 34), title, font=FONTS["h1"], fill=(255, 255, 255))
    draw_text_box(
        draw,
        item["name"],
        (1110, 22, 1800, 116),
        FONTS["h2"],
        fill=(255, 255, 255),
        line_gap=6,
        min_size=28,
        align="right",
        valign="middle",
    )


def paste_shadowed(page: Image.Image, image: Image.Image, xy: tuple[int, int], radius: int = 34) -> None:
    x, y = xy
    shadow = Image.new("RGBA", (image.width + 28, image.height + 28), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((14, 14, image.width + 14, image.height + 14), radius=radius, fill=(0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    page.paste(shadow, (x - 14, y - 10), shadow)
    rounded = rounded_image(image, radius)
    page.paste(rounded, xy, rounded)


def fetch_world_geojson() -> dict | None:
    if not WORLD_GEOJSON.exists():
        try:
            WORLD_GEOJSON.write_bytes(request_bytes(NE_URL, timeout=60))
        except Exception:
            return None
    try:
        return json.loads(WORLD_GEOJSON.read_text(encoding="utf-8"))
    except Exception:
        return None


def project(lon: float, lat: float, box: tuple[int, int, int, int]) -> tuple[int, int]:
    x0, y0, x1, y1 = box
    x = x0 + (lon + 180.0) / 360.0 * (x1 - x0)
    y = y0 + (90.0 - lat) / 180.0 * (y1 - y0)
    return int(x), int(y)


def iter_rings(geometry: dict):
    if geometry.get("type") == "Polygon":
        for ring in geometry.get("coordinates", [])[:1]:
            yield ring
    elif geometry.get("type") == "MultiPolygon":
        for polygon in geometry.get("coordinates", []):
            if polygon:
                yield polygon[0]


def draw_world_map(item: dict, detail: dict) -> Image.Image:
    img = Image.new("RGB", (1280, 650), (229, 245, 250))
    draw = ImageDraw.Draw(img, "RGBA")
    box = (24, 28, 1256, 622)
    draw.rounded_rectangle((0, 0, 1279, 649), radius=36, fill=(229, 245, 250))
    draw.rectangle(box, fill=(213, 238, 246))

    for lon in range(-180, 181, 30):
        x, _ = project(lon, 0, box)
        draw.line((x, box[1], x, box[3]), fill=(170, 200, 210, 90), width=1)
    for lat in range(-60, 61, 30):
        _, y = project(0, lat, box)
        draw.line((box[0], y, box[2], y), fill=(170, 200, 210, 90), width=1)

    geo = fetch_world_geojson()
    if geo:
        for feature in geo.get("features", []):
            for ring in iter_rings(feature.get("geometry", {})):
                pts = [project(float(lon), float(lat), box) for lon, lat in ring]
                if len(pts) >= 3:
                    draw.polygon(pts, fill=(241, 244, 239, 255), outline=(178, 188, 183, 180))
    else:
        # Coarse fallback silhouettes.
        fallback_shapes = [
            [(-165, 65), (-55, 72), (-35, 12), (-80, 5), (-115, 20), (-150, 45)],
            [(-82, 12), (-35, 5), (-55, -55), (-78, -20)],
            [(-10, 70), (150, 65), (170, 10), (95, -8), (35, 5), (5, 35)],
            [(-20, 35), (45, 34), (50, -35), (15, -35), (-10, 5)],
            [(112, -10), (154, -12), (150, -43), (115, -37)],
        ]
        for shape in fallback_shapes:
            pts = [project(lon, lat, box) for lon, lat in shape]
            draw.polygon(pts, fill=(241, 244, 239, 255), outline=(178, 188, 183, 180))

    accent = item["accent"]
    for mark in detail["range_marks"]:
        if mark["type"] == "box":
            lon0, lat0, lon1, lat1 = mark["value"]
            x0, y0 = project(lon0, lat1, box)
            x1, y1 = project(lon1, lat0, box)
            draw.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=(*accent, 92), outline=(*accent, 230), width=4)
        elif mark["type"] == "point":
            lon, lat, radius = mark["value"]
            x, y = project(lon, lat, box)
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*accent, 170), outline=(255, 255, 255, 255), width=4)
        elif mark["type"] == "band":
            lon0, lat0, lon1, lat1 = mark["value"]
            x0, y0 = project(lon0, lat1, box)
            x1, y1 = project(lon1, lat0, box)
            draw.rectangle((x0, y0, x1, y1), fill=(*accent, 50), outline=(*accent, 150), width=3)

    draw.rounded_rectangle((38, 520, 585, 602), radius=28, fill=(255, 255, 255, 220))
    draw.text((62, 537), detail["map_label"], font=FONTS["small"], fill=(35, 45, 55))
    return img


def page_cover(item: dict, image_path: Path) -> Image.Image:
    page = fit_image(image_path, (W, H)).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H):
        alpha = int(185 * max(0, (y - 450) / 630))
        od.line((0, y, W, y), fill=(0, 0, 0, alpha))
    od.rectangle((0, 0, W, 150), fill=(*item["accent"], 118))
    page = Image.alpha_composite(page, overlay).convert("RGB")
    draw = ImageDraw.Draw(page)
    draw_rounded_rect(draw, (120, 90, 445, 150), fill=item["accent"], radius=28)
    draw.text((150, 103), "파충류 탐구", font=FONTS["small"], fill=(255, 255, 255))
    draw.text((118, 680), item["name"], font=FONTS["title"], fill=(255, 255, 255))
    draw.text((125, 810), item["tagline"], font=FONTS["subtitle"], fill=(240, 248, 255))
    draw_footer(draw, "사진: Wikimedia Commons", 1, item["accent"])
    return page


def page_place(item: dict, detail: dict, species_image: Path) -> Image.Image:
    page = Image.new("RGB", (W, H), item["bg"])
    draw = ImageDraw.Draw(page)
    draw_header(draw, item, "사는 곳")
    map_img = draw_world_map(item, detail).resize((1100, 650), Image.Resampling.LANCZOS)
    paste_shadowed(page, map_img, (90, 220), radius=36)
    draw_rounded_rect(draw, (1280, 220, 1810, 920), fill=(255, 255, 255), radius=42, outline=(230, 235, 242), width=3)
    draw_text_box(draw, "어디에 살까요?", (1330, 290, 1765, 360), FONTS["h2"], fill=item["accent"], min_size=34)
    draw_text_box(
        draw,
        detail["place_text"],
        (1330, 400, 1765, 820),
        FONTS["body"],
        fill=(31, 41, 55),
        line_gap=12,
        min_size=28,
    )
    draw_footer(draw, "세계지도: Natural Earth 기반", 2, item["accent"])
    return page


def page_photo_topic(item: dict, title: str, label: str, text: str, photo_paths: list[Path], page_num: int, source: str) -> Image.Image:
    page = Image.new("RGB", (W, H), item["bg"])
    draw = ImageDraw.Draw(page)
    draw_header(draw, item, title)

    if photo_paths:
        main = fit_image(photo_paths[0], (1060, 700))
        paste_shadowed(page, main, (100, 220), radius=38)

    draw_rounded_rect(draw, (1260, 220, 1810, 920), fill=(255, 255, 255), radius=42, outline=(230, 235, 242), width=3)
    draw_text_box(draw, label, (1310, 280, 1765, 390), FONTS["h1"], fill=item["accent"], line_gap=6, min_size=38)
    draw_text_box(
        draw,
        text,
        (1310, 420, 1765, 830),
        FONTS["body"],
        fill=(31, 41, 55),
        line_gap=14,
        min_size=28,
    )
    draw_footer(draw, source, page_num, item["accent"])
    return page


def page_quiz(item: dict) -> Image.Image:
    page = Image.new("RGB", (W, H), item["quiz_bg"])
    draw = ImageDraw.Draw(page)
    draw_header(draw, item, "퀴즈")
    draw.text((120, 210), "생각해 보기", font=FONTS["quiz"], fill=item["accent"])
    draw_text_box(
        draw,
        item["quiz_question"],
        (125, 345, 1780, 510),
        FONTS["h2"],
        fill=(31, 41, 55),
        line_gap=12,
        min_size=32,
    )
    y = 575
    for idx, choice in enumerate(item["choices"], start=1):
        draw_rounded_rect(draw, (140, y, 1780, y + 96), fill=(255, 255, 255), radius=30, outline=item["accent"], width=4)
        draw_rounded_rect(draw, (170, y + 20, 230, y + 76), fill=item["accent"], radius=22)
        draw.text((190, y + 26), str(idx), font=FONTS["small"], fill=(255, 255, 255))
        draw_text_box(
            draw,
            choice,
            (270, y + 14, 1735, y + 84),
            FONTS["body"],
            fill=(31, 41, 55),
            line_gap=6,
            min_size=26,
            valign="middle",
        )
        y += 125
    draw_footer(draw, "다음 페이지에서 정답을 확인해요.", 6, item["accent"])
    return page


def page_answer(item: dict, detail: dict, photo_paths: list[Path], source: str | None = None) -> Image.Image:
    page = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(page)
    draw_header(draw, item, "정답과 특이한 점")

    draw_rounded_rect(draw, (110, 210, 930, 370), fill=item["answer_fill"], radius=42)
    draw.text((160, 255), "정답", font=FONTS["h2"], fill=item["accent"])
    draw_text_box(
        draw,
        item["answer"],
        (330, 226, 870, 355),
        FONTS["answer"],
        fill=(17, 24, 39),
        line_gap=4,
        min_size=42,
        valign="middle",
    )

    draw_bullets_box(draw, item["details"], (145, 430, 930, 930), FONTS["body"], fill=(31, 41, 55))

    if photo_paths:
        img1 = fit_image(photo_paths[0], (760, 755))
        paste_shadowed(page, img1, (1040, 220), radius=38)
    draw_footer(draw, source or detail["answer_source"], 7, item["accent"])
    return page


DETAILS = {
    "바다이구아나": {
        "map_label": "갈라파고스 제도 주변",
        "range_marks": [{"type": "point", "value": (-90.5, -0.8, 34)}],
        "place_text": "에콰도르 서쪽 바다의 갈라파고스 제도에서만 자연적으로 살아요.",
        "habitat_label": "바위 해안과 얕은 바다",
        "habitat_text": "검은 용암 바위가 많은 해안에서 몸을 데우고, 얕은 바다로 들어가 먹이를 찾아요.",
        "habitat_queries": ["Galapagos rocky shoreline ocean photograph"],
        "food_label": "해조류",
        "food_text": "바위에 붙은 해조류를 긁어 먹어요. 그래서 바닷물의 소금도 함께 몸속에 들어와요.",
        "food_queries": ["green seaweed algae underwater Wikimedia Commons", "marine algae on rock close up"],
        "feature_label": "소금 재채기",
        "feature_text": "코 근처의 소금샘이 소금을 걸러내고, 재채기처럼 밖으로 내보내요.",
        "feature_queries": ["marine iguana salt nose close up"],
        "answer_queries": [
            "marine iguana underwater feeding algae Wikimedia Commons",
            "marine iguana swimming underwater Wikimedia Commons",
            "marine iguana salt nose close up",
            "Galapagos marine iguana close up",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: National Geographic, Galapagos Conservation Trust",
    },
    "가비알": {
        "map_label": "인도와 네팔의 큰 강",
        "range_marks": [{"type": "box", "value": (76, 21, 89, 31)}],
        "place_text": "예전에는 남아시아 강에 넓게 살았지만, 지금은 주로 인도와 네팔의 강에 남아 있어요.",
        "habitat_label": "깊은 민물 강",
        "habitat_text": "깊은 강 굽이와 모래톱 근처에서 쉬고, 물속에서 물고기를 찾아요.",
        "habitat_queries": ["Chambal River India gharial habitat photograph"],
        "food_label": "물고기",
        "food_text": "가늘고 긴 주둥이는 빠르게 움직이는 물고기를 낚아채기 좋게 발달했어요.",
        "food_queries": ["small fish underwater school Wikimedia Commons", "freshwater fish close up"],
        "feature_label": "긴 주둥이와 가라",
        "feature_text": "수컷은 주둥이 끝에 둥근 혹 같은 ‘가라’가 생겨요. 소리와 구애 행동에 관련이 있어요.",
        "feature_queries": ["gharial snout close up"],
        "answer_queries": [
            "gharial catching fish Wikimedia Commons",
            "gharial eating fish",
            "Gavialis gangeticus snout close up",
            "gharial teeth close up",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: 나무위키, National Geographic, Smithsonian",
    },
    "도마뱀붙이": {
        "map_label": "따뜻한 지역과 집 주변",
        "range_marks": [{"type": "band", "value": (-180, -35, 180, 35)}, {"type": "box", "value": (120, 30, 132, 38)}],
        "place_text": "도마뱀붙이류는 따뜻한 지역에 널리 살고, 한국 남부 지역에도 일부 종류가 살아요.",
        "habitat_label": "벽, 천장, 숲, 바위",
        "habitat_text": "밤에 활동하며 전등 주변 벽이나 천장에 붙어 곤충을 기다리는 모습을 볼 수 있어요.",
        "habitat_queries": ["gecko on wall night Wikimedia Commons"],
        "food_label": "곤충과 거미",
        "food_text": "작은 곤충, 거미, 바퀴벌레 같은 먹이를 잡아먹어 집 주변의 벌레를 줄이기도 해요.",
        "food_queries": ["cockroach macro photograph Wikimedia Commons", "small insect macro Wikimedia Commons"],
        "feature_label": "발바닥 구조",
        "feature_text": "발바닥에는 아주 작은 털 같은 구조가 많아 벽과 천장에도 붙을 수 있어요.",
        "feature_queries": ["gecko foot close up Wikimedia Commons"],
        "answer_queries": [
            "gecko foot close up Wikimedia Commons",
            "gecko toe pads macro",
            "gecko climbing glass",
            "gecko on window close up",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: 나무위키, Britannica, NIST",
    },
    "뿔도마뱀": {
        "map_label": "북아메리카 건조 지역",
        "range_marks": [{"type": "box", "value": (-124, 23, -94, 45)}],
        "place_text": "주로 미국 서부와 멕시코 북부의 건조한 지역에서 살아요.",
        "habitat_label": "사막과 반사막",
        "habitat_text": "모래땅, 자갈밭, 건조한 풀밭에서 몸 색으로 위장해요.",
        "habitat_queries": ["Sonoran Desert scrub photograph Wikimedia Commons"],
        "food_label": "개미와 작은 곤충",
        "food_text": "종에 따라 개미를 많이 먹고, 작은 곤충도 잡아먹어요.",
        "food_queries": ["harvester ants close up Wikimedia Commons", "ants close up macro"],
        "feature_label": "마지막 방어",
        "feature_text": "일부 종은 아주 위험할 때 눈 주변에서 피를 뿜어 포식자를 놀라게 해요.",
        "feature_queries": ["horned lizard close up eye Wikimedia Commons"],
        "answer_queries": [
            "horned lizard eye close up Wikimedia Commons",
            "horned lizard defensive posture",
            "Texas horned lizard close up",
            "horned lizard blood eye",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: Britannica, National Park Service",
    },
    "바실리스크도마뱀": {
        "map_label": "중앙아메리카 열대림",
        "range_marks": [{"type": "box", "value": (-100, -3, -72, 20)}],
        "place_text": "멕시코 남부부터 중앙아메리카, 남아메리카 북부의 물가 숲에서 살아요.",
        "habitat_label": "물가 열대우림",
        "habitat_text": "강과 개울 가까운 나무와 덤불에서 지내며, 위험하면 물 위로 도망가요.",
        "habitat_queries": ["Central America rainforest stream photograph Wikimedia Commons"],
        "food_label": "곤충과 작은 동물",
        "food_text": "곤충, 지렁이, 작은 동물, 과일 등을 먹는 잡식성 도마뱀이에요.",
        "food_queries": ["cricket insect macro Wikimedia Commons", "earthworm photograph Wikimedia Commons"],
        "feature_label": "물 위 달리기",
        "feature_text": "빠른 뒷다리와 넓게 펴지는 발가락이 물을 밀어 잠깐 물 위를 달리게 해요.",
        "feature_queries": ["basilisk lizard foot toes close up"],
        "answer_queries": [
            "basilisk lizard running on water",
            "Jesus Christ lizard running water",
            "Basiliscus plumifrons foot toes",
            "green basilisk lizard close up",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: Smithsonian National Zoo, National Geographic",
    },
    "아르마딜로도마뱀": {
        "map_label": "남아프리카 서쪽 바위 지대",
        "range_marks": [{"type": "box", "value": (16, -34, 21, -27)}],
        "place_text": "남아프리카 공화국 서쪽 해안 가까운 건조한 바위 지대에 살아요.",
        "habitat_label": "건조한 바위틈",
        "habitat_text": "바위틈에 숨어 쉬고, 작은 무리를 이루어 사는 경우도 있어요.",
        "habitat_queries": ["Namaqualand rocky desert South Africa Wikimedia Commons"],
        "food_label": "흰개미와 곤충",
        "food_text": "주로 흰개미 같은 작은 무척추동물을 먹고, 때로는 식물도 먹어요.",
        "food_queries": ["termites close up Wikimedia Commons", "termite mound close up"],
        "feature_label": "꼬리를 무는 방어",
        "feature_text": "자기 꼬리를 물고 동그랗게 말아 부드러운 배를 숨겨요.",
        "feature_queries": ["armadillo girdled lizard curled ball"],
        "answer_queries": [
            "armadillo girdled lizard curled ball",
            "armadillo girdled lizard tail mouth",
            "Ouroborus cataphractus close up",
            "armadillo lizard defense",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: Britannica, Animal Diversity Web",
    },
    "마타마타거북": {
        "map_label": "아마존과 오리노코 유역",
        "range_marks": [{"type": "box", "value": (-78, -16, -50, 9)}],
        "place_text": "남아메리카의 아마존강과 오리노코강 주변의 민물에서 살아요.",
        "habitat_label": "느린 민물과 진흙 바닥",
        "habitat_text": "얕고 느리게 흐르는 물, 진흙 바닥, 낙엽이 쌓인 곳에서 잘 숨어요.",
        "habitat_queries": ["Amazon river slow water forest Wikimedia Commons"],
        "food_label": "작은 물고기",
        "food_text": "주로 물고기를 먹고, 가만히 기다리다가 입으로 물과 함께 빨아들여요.",
        "food_queries": ["small freshwater fish underwater Wikimedia Commons", "fish in muddy river water"],
        "feature_label": "낙엽 위장",
        "feature_text": "울퉁불퉁한 머리와 목이 물속 낙엽처럼 보여 먹이가 잘 알아차리지 못해요.",
        "feature_queries": ["mata mata turtle head close up"],
        "answer_queries": [
            "mata mata turtle mouth open",
            "mata mata turtle head close up",
            "Chelus fimbriata close up",
            "mata mata turtle camouflage",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: World Wildlife Fund, Britannica",
    },
    "돼지코거북": {
        "map_label": "호주 북부와 뉴기니 남부",
        "range_marks": [{"type": "box", "value": (120, -20, 153, -4)}],
        "place_text": "호주 북부와 뉴기니 남부의 강과 늪, 석호에서 살아요.",
        "habitat_label": "강, 늪, 석호",
        "habitat_text": "민물에서 살지만 바다거북처럼 지느러미 모양 발로 헤엄쳐요.",
        "habitat_queries": ["tropical freshwater river lagoon Wikimedia Commons"],
        "food_label": "과일과 물속 먹이",
        "food_text": "과일, 수생식물, 새우, 조개, 곤충 등 여러 가지를 먹어요.",
        "food_queries": ["fig fruit close up Wikimedia Commons", "freshwater shrimp Wikimedia Commons"],
        "feature_label": "돼지코와 지느러미 발",
        "feature_text": "코는 돼지코처럼 생겼고, 발은 바다거북처럼 넓게 변했어요.",
        "feature_queries": ["pig nosed turtle nose close up"],
        "answer_queries": [
            "pig-nosed turtle flippers swimming",
            "pig nosed turtle close up",
            "Carettochelys insculpta swimming",
            "pig-nosed turtle flipper close up",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: Smithsonian National Zoo, National Aquarium",
    },
    "가시악마도마뱀": {
        "map_label": "오스트레일리아 사막",
        "range_marks": [{"type": "box", "value": (112, -34, 138, -17)}],
        "place_text": "오스트레일리아 중부와 서부의 건조한 사막과 모래 평원에 살아요.",
        "habitat_label": "사막과 모래 평원",
        "habitat_text": "뜨겁고 건조한 지역에서 작은 몸과 위장색으로 살아가요.",
        "habitat_queries": ["Australian red desert sand Wikimedia Commons"],
        "food_label": "개미",
        "food_text": "거의 개미를 주식으로 먹고, 개미 길 옆에서 혀로 빠르게 잡아먹어요.",
        "food_queries": ["Australian ants close up Wikimedia Commons", "ants trail close up"],
        "feature_label": "피부의 물길",
        "feature_text": "비늘 사이의 좁은 홈이 물을 입 쪽으로 이동시키는 작은 물길 역할을 해요.",
        "feature_queries": ["thorny devil close up skin scales"],
        "answer_queries": [
            "thorny devil water skin",
            "thorny devil close up",
            "Moloch horridus close up",
            "thorny devil scales macro",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: Parks Australia, National Geographic",
    },
    "팬케이크거북": {
        "map_label": "동아프리카 바위 언덕",
        "range_marks": [{"type": "box", "value": (33, -9, 41, 3)}],
        "place_text": "케냐 남부와 탄자니아 북부·동부의 건조한 바위 지역에 살아요.",
        "habitat_label": "바위틈과 사바나",
        "habitat_text": "바위틈이 많은 건조한 사바나와 관목지에서 몸을 숨겨요.",
        "habitat_queries": ["East Africa rocky outcrop savanna Wikimedia Commons"],
        "food_label": "풀과 식물",
        "food_text": "마른 풀, 잎, 떨어진 열매, 다육식물 등을 먹어요.",
        "food_queries": ["dry grass close up Wikimedia Commons", "succulent aloe plant Wikimedia Commons"],
        "feature_label": "납작하고 유연한 등껍질",
        "feature_text": "껍질이 납작해서 좁은 바위틈으로 빠르게 들어갈 수 있어요.",
        "feature_queries": ["pancake tortoise flat shell close up"],
        "answer_queries": [
            "pancake tortoise rock crevice",
            "pancake tortoise flat shell",
            "Malacochersus tornieri close up",
            "pancake tortoise hiding",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: San Diego Zoo, Oakland Zoo",
    },
    "뱀목거북": {
        "map_label": "오스트레일리아 동부 습지",
        "range_marks": [{"type": "box", "value": (136, -40, 154, -16)}],
        "place_text": "오스트레일리아 동부와 남동부의 민물 습지와 호수에 살아요.",
        "habitat_label": "늪, 호수, 느린 물길",
        "habitat_text": "민물에서 살다가 새 물웅덩이나 산란 장소를 찾아 육지로 이동하기도 해요.",
        "habitat_queries": ["Australian freshwater swamp lake Wikimedia Commons"],
        "food_label": "작은 물속 동물",
        "food_text": "작은 물고기, 올챙이, 곤충, 물속 무척추동물을 잡아먹어요.",
        "food_queries": ["tadpoles close up Wikimedia Commons", "small freshwater fish Wikimedia Commons"],
        "feature_label": "긴 목과 옆목 접기",
        "feature_text": "목이 길고, 머리를 뒤로 당기는 대신 옆으로 접어 등껍질 안에 넣어요.",
        "feature_queries": ["snake necked turtle long neck close up"],
        "answer_queries": [
            "snake necked turtle long neck",
            "eastern long necked turtle side neck",
            "Chelodina longicollis neck extended",
            "snake-necked turtle close up",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: Australian Museum, NSW National Parks",
    },
    "뉴멕시코채찍꼬리도마뱀": {
        "map_label": "미국 남서부와 멕시코 북부",
        "range_marks": [{"type": "box", "value": (-114, 26, -103, 37)}],
        "place_text": "미국 뉴멕시코·애리조나와 멕시코 북부의 건조한 지역에서 살아요.",
        "habitat_label": "건조한 초원과 관목지",
        "habitat_text": "모래땅, 풀이 듬성듬성 난 곳, 관목지에서 빠르게 움직이며 먹이를 찾아요.",
        "habitat_queries": ["New Mexico desert grassland Wikimedia Commons"],
        "food_label": "작은 곤충",
        "food_text": "작은 곤충, 딱정벌레, 절지동물을 찾아 빠르게 뛰어다녀요.",
        "food_queries": ["small beetle insect macro Wikimedia Commons", "grasshopper insect close up Wikimedia Commons"],
        "feature_label": "암컷만 있는 종",
        "feature_text": "수컷 없이 암컷의 알이 발달하는 처녀생식으로 이어지는 도마뱀이에요.",
        "feature_queries": ["New Mexico whiptail lizard close up"],
        "answer_queries": [
            "New Mexico whiptail lizard",
            "Aspidoscelis neomexicanus close up",
            "lizard eggs close up Wikimedia Commons",
            "whiptail lizard eggs",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: Animal Diversity Web, Nature",
    },
    "인도별거북": {
        "map_label": "인도, 파키스탄, 스리랑카",
        "range_marks": [{"type": "box", "value": (66, 5, 83, 29)}],
        "place_text": "인도, 파키스탄, 스리랑카의 건조한 풀밭과 관목지에 살아요.",
        "habitat_label": "건조한 풀밭과 관목지",
        "habitat_text": "반건조 숲과 가시덤불, 풀밭에서 식물을 먹으며 살아요.",
        "habitat_queries": ["India dry scrub forest grassland Wikimedia Commons"],
        "food_label": "풀, 잎, 꽃",
        "food_text": "풀과 잎, 꽃, 과일 같은 식물성 먹이를 주로 먹어요.",
        "food_queries": ["grass leaves flowers close up Wikimedia Commons", "hibiscus flower close up Wikimedia Commons"],
        "feature_label": "별 모양 등껍질",
        "feature_text": "등껍질의 노란 선이 중심에서 퍼져 나가 별처럼 보여요.",
        "feature_queries": ["Indian star tortoise shell close up"],
        "answer_queries": [
            "Indian star tortoise shell pattern",
            "Indian star tortoise close up",
            "Geochelone elegans shell close up",
            "star tortoise pattern",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: Utica Zoo, conservation references",
    },
    "바다뱀": {
        "map_label": "인도양과 서태평양",
        "range_marks": [{"type": "box", "value": (45, -30, 165, 32)}],
        "place_text": "대부분 인도양과 서태평양의 따뜻한 바다, 해안 가까운 곳에 살아요.",
        "habitat_label": "산호초와 얕은 바다",
        "habitat_text": "산호초, 맹그로브, 바닥이 모래나 진흙인 얕은 바다에서 먹이를 찾아요.",
        "habitat_queries": ["coral reef underwater Wikimedia Commons"],
        "food_label": "물고기와 장어류",
        "food_text": "물고기와 장어류를 잡아먹고, 일부 종류는 물고기 알을 먹기도 해요.",
        "food_queries": ["reef fish underwater Wikimedia Commons", "eel fish underwater Wikimedia Commons"],
        "feature_label": "노처럼 납작한 꼬리",
        "feature_text": "꼬리가 좌우로 납작해서 물을 밀며 헤엄치기 좋아요.",
        "feature_queries": ["sea snake paddle tail close up"],
        "answer_queries": [
            "sea snake swimming underwater",
            "sea snake paddle tail",
            "Laticauda colubrina underwater",
            "sea snake tail close up",
        ],
        "answer_source": "사진: Wikimedia Commons / 자료: Britannica, Britannica Kids",
    },
}


def build_detail_pdf(item: dict) -> Path:
    detail = DETAILS[item["slug"]]
    species_image = download_image(item["slug"], item["image_url"])
    habitat = collect_unique_images(item["slug"], "habitat", detail["habitat_queries"], 1, avoid=[species_image])
    habitat = complete_image_list(habitat, 1, [species_image])

    food = collect_unique_images(item["slug"], "food", detail["food_queries"], 1, avoid=habitat + [species_image])
    food = complete_image_list(food, 1, habitat + [species_image])

    feature = collect_unique_images(item["slug"], "feature", detail["feature_queries"], 1, avoid=habitat + food)
    feature = complete_image_list(feature, 1, [species_image] + habitat + food)
    feature = apply_image_override(item["slug"], "feature", feature)

    answer = collect_unique_images(
        item["slug"],
        "answer",
        detail["answer_queries"],
        1,
        avoid=habitat + food + feature + [species_image],
    )
    answer = complete_image_list(answer, 1, feature + food + habitat + [species_image])
    answer = apply_image_override(item["slug"], "answer", answer)
    feature_source = source_for(item["slug"], "feature", "사진: Wikimedia Commons")
    answer_source = source_for(item["slug"], "answer", detail["answer_source"])

    pages = [
        page_cover(item, species_image),
        page_place(item, detail, species_image),
        page_photo_topic(item, "서식 지역", detail["habitat_label"], detail["habitat_text"], habitat, 3, "사진: Wikimedia Commons"),
        page_photo_topic(item, "먹이", detail["food_label"], detail["food_text"], food, 4, "사진: Wikimedia Commons"),
        page_photo_topic(item, "특징", detail["feature_label"], detail["feature_text"], feature, 5, feature_source),
        page_quiz(item),
        page_answer(item, detail, answer, answer_source),
    ]

    for index, page in enumerate(pages, start=1):
        page.save(DETAIL_PAGE_DIR / f"{item['slug']}_{index}.png", quality=95)

    pdf_path = DETAIL_DIR / f"{item['slug']}_보고서_상세가로형.pdf"
    rgb_pages = [page.convert("RGB") for page in pages]
    rgb_pages[0].save(
        pdf_path,
        "PDF",
        resolution=PDF_RESOLUTION,
        save_all=True,
        append_images=rgb_pages[1:],
    )
    return pdf_path


def save_contact_sheet(pages: list[tuple[str, int, Image.Image]]) -> Path:
    thumb_w, thumb_h = 384, 216
    gap = 18
    label_h = 38
    cols = 7
    rows = math.ceil(len(pages) / cols)
    sheet = Image.new("RGB", (gap + cols * (thumb_w + gap), gap + rows * (thumb_h + label_h + gap)), (248, 250, 252))
    draw = ImageDraw.Draw(sheet)
    for idx, (name, page_num, image) in enumerate(pages):
        row, col = divmod(idx, cols)
        x = gap + col * (thumb_w + gap)
        y = gap + row * (thumb_h + label_h + gap)
        sheet.paste(image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y))
        draw.text((x, y + thumb_h + 8), f"{name} {page_num}/{TOTAL_PAGES}", font=FONTS["tiny"], fill=(31, 41, 55))
    path = DETAIL_DIR / "QA_contact_sheet_detailed.jpg"
    sheet.save(path, quality=92)
    return path


def main() -> None:
    ensure_dirs()
    pdfs: list[Path] = []
    all_pages: list[tuple[str, int, Image.Image]] = []
    for item in ITEMS:
        pdf_path = build_detail_pdf(item)
        pdfs.append(pdf_path)
        for idx in range(1, TOTAL_PAGES + 1):
            all_pages.append((item["slug"], idx, Image.open(DETAIL_PAGE_DIR / f"{item['slug']}_{idx}.png").convert("RGB")))

    contact = save_contact_sheet(all_pages)
    for pdf_path in pdfs:
        reader = PdfReader(str(pdf_path))
        sizes = [(float(p.mediabox.width), float(p.mediabox.height)) for p in reader.pages]
        print(f"{pdf_path.name}: {len(reader.pages)} pages, sizes={sizes}")
    print(f"QA contact sheet: {contact}")


if __name__ == "__main__":
    main()
