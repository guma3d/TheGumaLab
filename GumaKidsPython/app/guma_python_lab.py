from __future__ import annotations

import importlib.util
import re
import traceback
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from types import ModuleType
from typing import Callable

from PIL import Image, ImageTk


BASE_DIR = Path(__file__).resolve().parents[1]
SEASON_ID = "season_01"
GAME_DIR = BASE_DIR / "games" / "season_01_treasure_score"
BASE_CODE_PATH = GAME_DIR / "upgrade_zone.py"
SAVE_ROOT = BASE_DIR / "user_saves" / SEASON_ID
LECTURE_ROOT = BASE_DIR / "Docs" / SEASON_ID

FONT_FAMILY = "Malgun Gothic"
CODE_FONT = ("Consolas", 11)
GAME_BASE_WIDTH = 520
GAME_BASE_HEIGHT = 330

APP_BG = "#070b12"
PANEL_BG = "#0b1120"
BAR_BG = "#0f172a"
CONTROL_BG = "#1e293b"
CONTROL_ACTIVE = "#334155"
TEXT_MAIN = "#e5e7eb"
TEXT_MUTED = "#94a3b8"
BORDER_DARK = "#1f2937"
CODE_BG = "#050816"


@dataclass(frozen=True)
class Chapter:
    number: int
    title: str
    concept: str
    upgrade: str
    mission: str
    quiz: str


@dataclass
class GameConfig:
    start_message: str
    hero_message: str
    hero_name: str
    title: str
    status_text: str
    score: int
    hp: int
    speed: int
    treasure_point: int
    trap_damage: int
    bonus_multiplier: int
    treasure_func: Callable[[int], int]
    trap_func: Callable[[int], int]
    bonus_func: Callable[[int], int]


@dataclass
class GameItem:
    kind: str
    x: int
    y: int
    done: bool = False


CHAPTERS = [
    Chapter(1, "게임 화면아 안녕", "print()", "게임 시작 문장 바꾸기", "시작 문장을 내 말로 바꿔 보자.", "print()는 어디에 글자를 보여줄까?"),
    Chapter(2, "캐릭터가 말해요", "문자열", "주인공 대사 바꾸기", "주인공에게 멋진 대사를 만들어 주자.", "따옴표 안에 들어 있는 것은 무엇일까?"),
    Chapter(3, "이름을 바꿔요", "문자열 값", "주인공 이름 바꾸기", "주인공 이름을 3개 만들어 보고 하나를 골라 보자.", "글자와 숫자는 어떻게 다를까?"),
    Chapter(4, "숫자가 보여요", "숫자", "시작 점수 바꾸기", "시작 점수를 0, 10, 100으로 바꿔 보자.", "숫자에는 따옴표가 필요할까?"),
    Chapter(5, "점수판 만들기", "변수", "점수 변수 만들기", "보물 게임의 시작 점수를 정해 보자.", "변수는 무엇을 담는 이름일까?"),
    Chapter(6, "체력 만들기", "숫자 변수", "주인공 체력 바꾸기", "체력을 50, 100, 999로 바꿔 보자.", "hp에 들어 있는 값은 무엇일까?"),
    Chapter(7, "속도 만들기", "변수 값 변경", "캐릭터 속도 바꾸기", "느린 캐릭터와 빠른 캐릭터를 만들어 보자.", "값이 바뀌면 게임은 어떻게 바뀔까?"),
    Chapter(8, "글자 합체", "문자열 연결", "이름과 문장 합치기", "내 이름이 들어간 등장 문장을 만들어 보자.", "+는 글자에서 어떤 일을 할까?"),
    Chapter(9, "멋진 상태창", "f-string", "이름과 점수를 문장에 넣기", "게임 상태창 문장을 바꿔 보자.", "{} 안에는 무엇을 넣을까?"),
    Chapter(10, "더하기 마법", "+", "보물 점수 더하기", "보물을 먹으면 50점 오르게 만들어 보자.", "점수는 어떻게 계산될까?"),
    Chapter(11, "빼기 마법", "-", "함정 데미지 만들기", "함정 데미지를 약하게 또는 강하게 만들어 보자.", "체력은 어떻게 줄어들까?"),
    Chapter(12, "보너스 점수", "*", "보너스 배율 만들기", "보너스 점수를 2배, 3배로 바꿔 보자.", "곱하기는 점수를 어떻게 바꿀까?"),
]


def chapter_save_path(chapter: Chapter) -> Path:
    return SAVE_ROOT / f"chapter_{chapter.number:02d}" / "upgrade_zone.py"


def read_base_code() -> str:
    return BASE_CODE_PATH.read_text(encoding="utf-8")


def lecture_path(chapter: Chapter) -> Path:
    return LECTURE_ROOT / f"chapter_{chapter.number:02d}.md"


def lecture_pdf_path(chapter: Chapter) -> Path:
    return LECTURE_ROOT / f"chapter_{chapter.number:02d}.pdf"


def lecture_preview_path(chapter: Chapter) -> Path:
    return LECTURE_ROOT / f"chapter_{chapter.number:02d}.png"


def lecture_preview_paths(chapter: Chapter) -> list[Path]:
    page_paths = sorted(LECTURE_ROOT.glob(f"chapter_{chapter.number:02d}_p*.png"))
    if page_paths:
        return page_paths

    legacy_path = lecture_preview_path(chapter)
    if legacy_path.exists():
        return [legacy_path]
    return []


def default_lesson(chapter: Chapter) -> str:
    return (
        f"# 챕터 {chapter.number}. {chapter.title}\n\n"
        f"## 오늘 배울 것\n"
        f"- {chapter.concept}\n\n"
        f"## 오늘의 업그레이드\n"
        f"- {chapter.upgrade}\n\n"
        f"## 미션\n"
        f"{chapter.mission}\n\n"
        f"## 해보기\n"
        f"1. 오른쪽 파이썬 화면에서 [챕터 {chapter.number}] 부분을 찾아요.\n"
        f"2. 값을 바꾸고 저장해요.\n"
        f"3. Play를 눌러 왼쪽 아래 게임 화면에서 확인해요.\n\n"
        f"## 퀴즈\n"
        f"{chapter.quiz}\n"
    )


def load_lesson(chapter: Chapter) -> str:
    path = lecture_path(chapter)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return default_lesson(chapter)


def load_student_code(chapter: Chapter) -> str:
    save_path = chapter_save_path(chapter)
    if save_path.exists():
        return save_path.read_text(encoding="utf-8")
    return read_base_code()


def save_student_code(chapter: Chapter, code: str) -> Path:
    save_path = chapter_save_path(chapter)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(code, encoding="utf-8")
    return save_path


def import_code_from_file(path: Path) -> ModuleType:
    module_name = f"guma_student_{SEASON_ID}_{path.parent.name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("파이썬 파일을 불러올 수 없습니다.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _as_text(module: ModuleType, name: str, default: str) -> str:
    return str(getattr(module, name, default))


def _as_int(module: ModuleType, name: str, default: int, low: int, high: int) -> int:
    value = getattr(module, name, default)
    try:
        number = int(value)
    except Exception:
        number = default
    return max(low, min(high, number))


def _as_func(module: ModuleType, name: str, fallback: Callable[[int], int]) -> Callable[[int], int]:
    value = getattr(module, name, fallback)
    if callable(value):
        return value
    return fallback


def load_config(module: ModuleType) -> GameConfig:
    treasure_point = _as_int(module, "treasure_point", 10, -1000, 1000)
    trap_damage = _as_int(module, "trap_damage", 20, -1000, 1000)
    bonus_multiplier = _as_int(module, "bonus_multiplier", 2, -20, 20)
    score_default = _as_int(module, "start_score", 10, -999, 9999)

    return GameConfig(
        start_message=_as_text(module, "start_message", "모험 시작!"),
        hero_message=_as_text(module, "hero_message", "보물을 찾자!"),
        hero_name=_as_text(module, "hero_name", "번개용사"),
        title=_as_text(module, "title", "번개용사 등장!"),
        status_text=_as_text(module, "status_text", "번개용사 점수: 10"),
        score=_as_int(module, "score", score_default, -999, 9999),
        hp=_as_int(module, "hp", 100, 1, 9999),
        speed=_as_int(module, "speed", 5, 1, 30),
        treasure_point=treasure_point,
        trap_damage=trap_damage,
        bonus_multiplier=bonus_multiplier,
        treasure_func=_as_func(module, "upgrade_score_when_get_treasure", lambda score: score + treasure_point),
        trap_func=_as_func(module, "upgrade_hp_when_hit_trap", lambda hp: hp - trap_damage),
        bonus_func=_as_func(module, "upgrade_score_when_get_bonus", lambda score: score * bonus_multiplier),
    )


def safe_call(func: Callable[[int], int], value: int, fallback: int) -> int:
    try:
        result = int(func(value))
    except Exception:
        result = fallback
    return max(-9999, min(9999, result))


class LessonView:
    def __init__(self, parent: tk.Widget) -> None:
        self.frame = tk.Frame(parent, bg=PANEL_BG)
        self.top_bar = tk.Frame(self.frame, bg=BAR_BG)
        self.top_bar.pack(fill="x")

        self.chapter_var = tk.StringVar(value="챕터 1")
        self.chapter_menu = tk.OptionMenu(self.top_bar, self.chapter_var, "챕터 1")
        self.chapter_menu.configure(
            font=(FONT_FAMILY, 9, "bold"),
            bg=CONTROL_BG,
            fg=TEXT_MAIN,
            activebackground=CONTROL_ACTIVE,
            activeforeground=TEXT_MAIN,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=8,
            pady=2,
        )
        self.chapter_menu.pack(side="left", padx=(8, 4), pady=4)
        self.chapter_menu["menu"].configure(
            bg=CONTROL_BG,
            fg=TEXT_MAIN,
            activebackground=CONTROL_ACTIVE,
            activeforeground=TEXT_MAIN,
            relief="flat",
            borderwidth=0,
        )

        self.prev_button = tk.Button(
            self.top_bar,
            text="이전",
            command=self.prev_page,
            font=(FONT_FAMILY, 9, "bold"),
            bg=CONTROL_BG,
            fg=TEXT_MAIN,
            activebackground=CONTROL_ACTIVE,
            activeforeground=TEXT_MAIN,
            disabledforeground="#64748b",
            relief="flat",
            padx=8,
            pady=2,
        )
        self.prev_button.pack(side="left", padx=(4, 4), pady=4)

        self.page_label = tk.Label(
            self.top_bar,
            text="",
            font=(FONT_FAMILY, 9, "bold"),
            bg=BAR_BG,
            fg=TEXT_MUTED,
        )
        self.page_label.pack(side="left", padx=6)

        self.next_button = tk.Button(
            self.top_bar,
            text="다음",
            command=self.next_page,
            font=(FONT_FAMILY, 9, "bold"),
            bg=CONTROL_BG,
            fg=TEXT_MAIN,
            activebackground=CONTROL_ACTIVE,
            activeforeground=TEXT_MAIN,
            disabledforeground="#64748b",
            relief="flat",
            padx=8,
            pady=2,
        )
        self.next_button.pack(side="left", padx=(4, 8), pady=4)

        self.preview_canvas = tk.Canvas(self.frame, bg=PANEL_BG, highlightthickness=0)
        self.preview_canvas.bind("<Configure>", lambda _event: self._redraw_preview())
        self.preview_image: Image.Image | None = None
        self.preview_photo: ImageTk.PhotoImage | None = None
        self.preview_paths: list[Path] = []
        self.preview_index = 0

        self.text = ScrolledText(
            self.frame,
            wrap="word",
            font=(FONT_FAMILY, 11),
            bg=BAR_BG,
            fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            selectbackground=CONTROL_ACTIVE,
            padx=16,
            pady=14,
            relief="flat",
            height=13,
        )
        self.text.pack(fill="both", expand=True)
        self.text.configure(state="disabled")

    def set_chapter_selector(self, chapters: list[Chapter], on_select: Callable[[Chapter], None]) -> None:
        menu = self.chapter_menu["menu"]
        menu.delete(0, "end")
        for chapter in chapters:
            label = f"챕터 {chapter.number}"
            menu.add_command(label=label, command=lambda selected=chapter: on_select(selected))

    def set_selected_chapter(self, chapter: Chapter) -> None:
        self.chapter_var.set(f"챕터 {chapter.number}")

    def show(self, chapter: Chapter) -> None:
        preview_paths = lecture_preview_paths(chapter)
        if preview_paths:
            self._show_previews(preview_paths)
            return

        lesson = load_lesson(chapter)
        self.preview_paths = []
        self.preview_index = 0
        self.preview_image = None
        self.page_label.configure(text="- / -")
        self.prev_button.configure(state="disabled")
        self.next_button.configure(state="disabled")
        self.preview_canvas.pack_forget()
        self.text.pack(fill="both", expand=True)
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", lesson)
        self.text.configure(state="disabled")

    def _show_previews(self, preview_paths: list[Path]) -> None:
        self.text.pack_forget()
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_paths = preview_paths
        self.preview_index = 0
        self._load_current_preview()

    def _load_current_preview(self) -> None:
        if not self.preview_paths:
            return
        self.preview_image = Image.open(self.preview_paths[self.preview_index]).convert("RGB")
        self._update_page_bar()
        self._redraw_preview()

    def prev_page(self) -> None:
        if self.preview_index <= 0:
            return
        self.preview_index -= 1
        self._load_current_preview()

    def next_page(self) -> None:
        if self.preview_index >= len(self.preview_paths) - 1:
            return
        self.preview_index += 1
        self._load_current_preview()

    def _update_page_bar(self) -> None:
        total = len(self.preview_paths)
        current = self.preview_index + 1 if total else 0
        self.page_label.configure(text=f"{current} / {total}")
        self.prev_button.configure(state="normal" if self.preview_index > 0 else "disabled")
        self.next_button.configure(state="normal" if self.preview_index < total - 1 else "disabled")

    def _redraw_preview(self) -> None:
        if self.preview_image is None:
            return
        canvas_width = max(1, self.preview_canvas.winfo_width())
        canvas_height = max(1, self.preview_canvas.winfo_height())
        max_width = max(1, canvas_width - 24)
        max_height = max(1, canvas_height - 24)
        image_width, image_height = self.preview_image.size
        scale = min(max_width / image_width, max_height / image_height)
        display_size = (max(1, int(image_width * scale)), max(1, int(image_height * scale)))
        display_image = self.preview_image.resize(display_size, Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(display_image)

        self.preview_canvas.delete("all")
        self.preview_canvas.create_rectangle(0, 0, canvas_width, canvas_height, fill=PANEL_BG, outline="")
        x = canvas_width // 2
        y = canvas_height // 2
        self.preview_canvas.create_rectangle(
            x - display_size[0] // 2 - 4,
            y - display_size[1] // 2 - 4,
            x + display_size[0] // 2 + 4,
            y + display_size[1] // 2 + 4,
            fill=BAR_BG,
            outline=BORDER_DARK,
        )
        self.preview_canvas.create_image(x, y, image=self.preview_photo)


class CodeView:
    def __init__(self, parent: tk.Widget, on_save: Callable[[], None], on_play: Callable[[], None], on_reset: Callable[[], None]) -> None:
        self.frame = tk.Frame(parent, bg=BAR_BG)

        toolbar = tk.Frame(self.frame, bg=BAR_BG)
        toolbar.pack(fill="x")

        self.status = tk.Label(
            toolbar,
            text="챕터를 선택하세요.",
            bg=BAR_BG,
            fg=TEXT_MUTED,
            font=(FONT_FAMILY, 9),
            anchor="w",
            padx=10,
            pady=4,
        )
        self.status.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=4)

        for text, command, color in [
            ("저장", on_save, "#2563eb"),
            ("Play", on_play, "#16a34a"),
            ("원래대로", on_reset, "#6b7280"),
        ]:
            button = tk.Button(
                toolbar,
                text=text,
                command=command,
                bg=color,
                fg="white",
                activebackground=CONTROL_ACTIVE,
                activeforeground="white",
                font=(FONT_FAMILY, 9, "bold"),
                relief="flat",
                padx=10,
                pady=4,
            )
            button.pack(side="right", padx=(0, 6), pady=4)

        self.editor = ScrolledText(
            self.frame,
            wrap="none",
            font=CODE_FONT,
            bg=CODE_BG,
            fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            selectbackground=CONTROL_ACTIVE,
            padx=14,
            pady=12,
            relief="flat",
            undo=True,
        )
        self.editor.pack(fill="both", expand=True)
        self._configure_tags()
        self.editor.bind("<KeyRelease>", lambda _event: self.highlight_python())

    def _configure_tags(self) -> None:
        self.editor.tag_configure("focus", background="#172033")
        self.editor.tag_configure("comment", foreground="#86efac")
        self.editor.tag_configure("string", foreground="#fbbf24")
        self.editor.tag_configure("number", foreground="#c4b5fd")
        self.editor.tag_configure("keyword", foreground="#93c5fd")
        self.editor.tag_configure("chapter_marker", foreground="#67e8f9", font=("Consolas", 11, "bold"))

    def get_code(self) -> str:
        return self.editor.get("1.0", "end-1c")

    def set_code(self, code: str, chapter: Chapter) -> None:
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", code)
        self.highlight_python()
        self.highlight_chapter(chapter.number)

    def set_status(self, text: str, ok: bool = True) -> None:
        color = "#10251d" if ok else "#2a1016"
        fg = "#86efac" if ok else "#fca5a5"
        self.status.configure(text=text, bg=color, fg=fg)

    def highlight_chapter(self, chapter_number: int) -> None:
        self.editor.tag_remove("focus", "1.0", "end")
        start = self.editor.search(f"[챕터 {chapter_number}]", "1.0", stopindex="end")
        if not start:
            return
        next_match = self.editor.search("[챕터 ", f"{start}+1c", stopindex="end")
        end = next_match if next_match else "end"
        self.editor.tag_add("focus", f"{start} linestart", end)
        self.editor.see(start)

    def highlight_python(self) -> None:
        code = self.get_code()
        for tag in ["comment", "string", "number", "keyword", "chapter_marker"]:
            self.editor.tag_remove(tag, "1.0", "end")

        for match in re.finditer(r"#.*", code):
            self._tag_match("comment", match)
        for match in re.finditer(r"(['\"])(?:\\.|(?!\1).)*\1", code):
            self._tag_match("string", match)
        for match in re.finditer(r"\b\d+\b", code):
            self._tag_match("number", match)
        for match in re.finditer(r"\b(def|return|if|else|elif|for|while|in|import|from|try|except|with|as)\b", code):
            self._tag_match("keyword", match)
        for match in re.finditer(r"\[챕터 \d+\]", code):
            self._tag_match("chapter_marker", match)

    def _tag_match(self, tag: str, match: re.Match[str]) -> None:
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        self.editor.tag_add(tag, start, end)


class GameView:
    def __init__(self, parent: tk.Widget) -> None:
        self.frame = tk.Frame(parent, bg=PANEL_BG)

        self.canvas = tk.Canvas(self.frame, width=GAME_BASE_WIDTH, height=GAME_BASE_HEIGHT, bg="#e8f4ff", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", lambda _event: self.focus_game())

        self.config = self.default_config()
        self.keys: set[str] = set()
        self.after_id: str | None = None
        self.reset()
        self.start_loop()

    def default_config(self) -> GameConfig:
        module = import_code_from_file(BASE_CODE_PATH)
        return load_config(module)

    def focus_game(self) -> None:
        self.canvas.focus_set()

    def apply_config(self, config: GameConfig) -> None:
        self.config = config
        self.reset()
        self.focus_game()

    def reset(self) -> None:
        self.hero_x = 60
        self.hero_y = 155
        self.score = self.config.score
        self.hp = self.config.hp
        self.max_hp = max(1, self.config.hp)
        self.message = self.config.start_message
        self.keys.clear()
        self.win = False
        self.game_over = False
        self.items = [
            GameItem("treasure", 150, 92),
            GameItem("treasure", 292, 206),
            GameItem("bonus", 438, 110),
            GameItem("trap", 220, 152),
            GameItem("trap", 385, 224),
        ]
        self.draw()

    def show_error(self, error: str) -> None:
        self.keys.clear()
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, 900, 900, fill="#fff1f2", outline="")
        self.canvas.create_text(28, 36, text="코드를 다시 확인해요", anchor="w", fill="#be123c", font=(FONT_FAMILY, 17, "bold"))
        self.canvas.create_text(
            28,
            74,
            text="오른쪽 파이썬 화면에 문제가 있어 게임을 시작하지 못했어요.",
            anchor="w",
            fill="#7f1d1d",
            font=(FONT_FAMILY, 11),
        )
        short_error = "\n".join(error.strip().splitlines()[-5:])
        self.canvas.create_text(28, 122, text=short_error, anchor="nw", fill="#111827", font=("Consolas", 9))

    def start_loop(self) -> None:
        if self.after_id is not None:
            self.canvas.after_cancel(self.after_id)
        self.loop()

    def loop(self) -> None:
        self.update()
        self.draw()
        self.after_id = self.canvas.after(33, self.loop)

    def on_key_press(self, event: tk.Event) -> None:
        key = event.keysym
        self.keys.add(key)
        if key == "space":
            self.try_collect()
        elif key.lower() == "r":
            self.reset()

    def on_key_release(self, event: tk.Event) -> None:
        self.keys.discard(event.keysym)

    def update(self) -> None:
        if self.win or self.game_over:
            return
        dx = 0
        dy = 0
        if "Left" in self.keys:
            dx -= self.config.speed
        if "Right" in self.keys:
            dx += self.config.speed
        if "Up" in self.keys:
            dy -= self.config.speed
        if "Down" in self.keys:
            dy += self.config.speed

        self.hero_x = max(28, min(GAME_BASE_WIDTH - 28, self.hero_x + dx))
        self.hero_y = max(76, min(GAME_BASE_HEIGHT - 70, self.hero_y + dy))

        for item in self.items:
            if item.kind == "trap" and not item.done and self.near(item, 34):
                old_hp = self.hp
                self.hp = safe_call(self.config.trap_func, self.hp, self.hp - self.config.trap_damage)
                item.done = True
                self.message = f"함정! 체력 {old_hp} -> {self.hp}"
                if self.hp <= 0:
                    self.hp = 0
                    self.game_over = True
                    self.message = "체력이 0이 되었어. R 키로 다시 도전!"

        if all(item.done for item in self.items):
            self.win = True
            self.message = f"성공! 최종 점수 {self.score}점"

    def try_collect(self) -> None:
        if self.win or self.game_over:
            return
        for item in self.items:
            if item.done or item.kind == "trap":
                continue
            if self.near(item, 48):
                old_score = self.score
                if item.kind == "bonus":
                    self.score = safe_call(self.config.bonus_func, self.score, self.score * self.config.bonus_multiplier)
                    self.message = f"보너스! 점수 {old_score} -> {self.score}"
                else:
                    self.score = safe_call(self.config.treasure_func, self.score, self.score + self.config.treasure_point)
                    self.message = f"보물! 점수 {old_score} -> {self.score}"
                item.done = True
                return
        self.message = self.config.hero_message

    def near(self, item: GameItem, distance: int) -> bool:
        return abs(self.hero_x - item.x) <= distance and abs(self.hero_y - item.y) <= distance

    def draw(self) -> None:
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        sx = width / GAME_BASE_WIDTH
        sy = height / GAME_BASE_HEIGHT

        def x(value: int | float) -> float:
            return value * sx

        def y(value: int | float) -> float:
            return value * sy

        def font(size: int, weight: str | None = None) -> tuple[str, int] | tuple[str, int, str]:
            scaled = max(7, int(size * min(sx, sy)))
            if weight:
                return (FONT_FAMILY, scaled, weight)
            return (FONT_FAMILY, scaled)

        c = self.canvas
        c.delete("all")

        c.create_rectangle(0, 0, width, y(64), fill="#18324a", outline="")
        c.create_rectangle(0, y(64), width, y(GAME_BASE_HEIGHT - 56), fill="#e8f4ff", outline="")
        c.create_rectangle(0, y(GAME_BASE_HEIGHT - 56), width, height, fill="#fff7d8", outline="")
        c.create_text(width // 2, y(20), text=self.config.title, fill="white", font=font(16, "bold"))
        c.create_text(width // 2, y(45), text=self.config.status_text, fill="#cdefff", font=font(10))
        c.create_text(x(18), y(24), text=f"점수 {self.score}", anchor="w", fill="#ffe36e", font=font(11, "bold"))
        c.create_text(x(400), y(24), text=f"체력 {self.hp}", anchor="w", fill="white", font=font(11, "bold"))

        for grid_x in range(0, GAME_BASE_WIDTH + 56, 56):
            c.create_line(x(grid_x), y(64), x(grid_x + 80), y(GAME_BASE_HEIGHT - 56), fill="#d6e9f8")

        for item in self.items:
            if item.done:
                continue
            if item.kind == "treasure":
                c.create_oval(x(item.x - 15), y(item.y - 15), x(item.x + 15), y(item.y + 15), fill="#ffd34e", outline="#a36500", width=max(1, int(2 * min(sx, sy))))
                c.create_text(x(item.x), y(item.y), text="$", fill="#6b4300", font=font(13, "bold"))
            elif item.kind == "bonus":
                c.create_polygon(
                    x(item.x),
                    y(item.y - 24),
                    x(item.x + 8),
                    y(item.y - 6),
                    x(item.x + 26),
                    y(item.y - 6),
                    x(item.x + 11),
                    y(item.y + 6),
                    x(item.x + 17),
                    y(item.y + 23),
                    x(item.x),
                    y(item.y + 13),
                    x(item.x - 17),
                    y(item.y + 23),
                    x(item.x - 11),
                    y(item.y + 6),
                    x(item.x - 26),
                    y(item.y - 6),
                    x(item.x - 8),
                    y(item.y - 6),
                    fill="#9b7cff",
                    outline="#5a3fd8",
                    width=max(1, int(2 * min(sx, sy))),
                )
            else:
                c.create_polygon(x(item.x - 20), y(item.y + 18), x(item.x), y(item.y - 20), x(item.x + 20), y(item.y + 18), fill="#ff7b54", outline="#74321d", width=max(1, int(2 * min(sx, sy))))
                c.create_text(x(item.x), y(item.y + 7), text="!", fill="white", font=font(13, "bold"))

        c.create_oval(x(self.hero_x - 18), y(self.hero_y - 24), x(self.hero_x + 18), y(self.hero_y + 12), fill="#4f9cff", outline="#1d4d91", width=max(1, int(2 * min(sx, sy))))
        c.create_rectangle(x(self.hero_x - 15), y(self.hero_y + 12), x(self.hero_x + 15), y(self.hero_y + 33), fill="#2dd4bf", outline="#0f766e", width=max(1, int(2 * min(sx, sy))))
        c.create_text(x(self.hero_x), y(self.hero_y + 50), text=self.config.hero_name, fill="#14324a", font=font(9, "bold"))

        c.create_text(x(18), y(GAME_BASE_HEIGHT - 36), text=self.message, anchor="w", fill="#3a2a08", font=font(11, "bold"))
        c.create_text(x(18), y(GAME_BASE_HEIGHT - 14), text="방향키 이동 / 스페이스 줍기 / R 다시", anchor="w", fill="#6b5a1f", font=font(9))

        if self.win or self.game_over:
            fill = "#ecfdf5" if self.win else "#fff1f2"
            outline = "#10b981" if self.win else "#fb7185"
            text = "성공!" if self.win else "다시 도전!"
            color = "#047857" if self.win else "#be123c"
            c.create_rectangle(x(150), y(120), x(370), y(210), fill=fill, outline=outline, width=max(1, int(3 * min(sx, sy))))
            c.create_text(x(260), y(155), text=text, fill=color, font=font(21, "bold"))
            c.create_text(x(260), y(187), text="R 키를 눌러요", fill="#374151", font=font(10, "bold"))


class GumaPythonLab:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Guma Python Lab - Prototype")
        self.root.geometry("1320x820")
        self.root.minsize(1080, 680)
        self.root.configure(bg=APP_BG)

        self.current_chapter = CHAPTERS[0]

        self.root.grid_columnconfigure(0, weight=1, uniform="main")
        self.root.grid_columnconfigure(1, weight=1, uniform="main")
        self.root.grid_rowconfigure(0, weight=1)

        left = tk.Frame(self.root, bg=APP_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=1, uniform="left")
        left.grid_rowconfigure(1, weight=1, uniform="left")

        right = tk.Frame(self.root, bg=BAR_BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)

        self.lesson = LessonView(left)
        self.lesson.frame.grid(row=0, column=0, sticky="nsew", pady=(0, 4))

        self.game = GameView(left)
        self.game.frame.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        self.code = CodeView(right, self.save_code, self.play_game, self.reset_code)
        self.code.frame.pack(fill="both", expand=True)

        self.lesson.set_chapter_selector(CHAPTERS, self.select_chapter)
        self.select_chapter(CHAPTERS[0])

    def select_chapter(self, chapter: Chapter) -> None:
        self.current_chapter = chapter
        self.lesson.set_selected_chapter(chapter)
        self.lesson.show(chapter)
        self.code.set_code(load_student_code(chapter), chapter)
        self.code.set_status(f"챕터 {chapter.number} 준비 완료. 코드를 바꾸고 Play를 눌러요.")
        self.play_game(silent=True)

    def save_code(self) -> Path:
        code = self.code.get_code()
        save_path = save_student_code(self.current_chapter, code)
        self.code.set_status(f"저장 완료: {save_path.relative_to(BASE_DIR)}")
        return save_path

    def play_game(self, silent: bool = False) -> None:
        try:
            save_path = self.save_code()
            module = import_code_from_file(save_path)
            config = load_config(module)
            self.game.apply_config(config)
        except Exception:
            error = traceback.format_exc()
            self.game.show_error(error)
            self.code.set_status("코드에 문제가 있어요. 빨간 메시지를 확인해요.", ok=False)
            if not silent:
                messagebox.showerror("코드 확인", "오른쪽 파이썬 코드에 문제가 있어요.\n게임 화면의 메시지를 확인해 주세요.")
            return

        if not silent:
            self.code.set_status("Play 완료. 왼쪽 아래 게임 화면에서 바로 확인해요.")

    def reset_code(self) -> None:
        if not messagebox.askyesno("원래대로", "현재 챕터 코드를 원래 준비된 코드로 되돌릴까요?"):
            return
        code = read_base_code()
        self.code.set_code(code, self.current_chapter)
        save_student_code(self.current_chapter, code)
        self.code.set_status("원래 코드로 되돌렸어요.")
        self.play_game(silent=True)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    GumaPythonLab().run()


if __name__ == "__main__":
    main()
