from __future__ import annotations

import importlib
import traceback
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox
from types import ModuleType
from typing import Callable


WIDTH = 900
HEIGHT = 560
HUD_HEIGHT = 88
FOOTER_HEIGHT = 92
PLAY_TOP = HUD_HEIGHT
PLAY_BOTTOM = HEIGHT - FOOTER_HEIGHT

FONT_FAMILY = "Malgun Gothic"


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
class Item:
    kind: str
    x: int
    y: int
    collected: bool = False
    triggered: bool = False


def _load_upgrade_zone() -> ModuleType:
    return importlib.import_module("upgrade_zone")


def _as_text(module: ModuleType, name: str, default: str) -> str:
    value = getattr(module, name, default)
    return str(value)


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


def _safe_call(func: Callable[[int], int], value: int, fallback: int) -> int:
    try:
        result = int(func(value))
    except Exception:
        return fallback
    return max(-9999, min(9999, result))


def load_config() -> GameConfig:
    module = _load_upgrade_zone()

    treasure_point = _as_int(module, "treasure_point", 10, -1000, 1000)
    trap_damage = _as_int(module, "trap_damage", 20, -1000, 1000)
    bonus_multiplier = _as_int(module, "bonus_multiplier", 2, -20, 20)

    return GameConfig(
        start_message=_as_text(module, "start_message", "모험 시작!"),
        hero_message=_as_text(module, "hero_message", "보물을 찾자!"),
        hero_name=_as_text(module, "hero_name", "번개용사"),
        title=_as_text(module, "title", "번개용사 등장!"),
        status_text=_as_text(module, "status_text", "번개용사 점수: 10"),
        score=_as_int(module, "score", _as_int(module, "start_score", 10, -999, 9999), -999, 9999),
        hp=_as_int(module, "hp", 100, 1, 9999),
        speed=_as_int(module, "speed", 5, 1, 30),
        treasure_point=treasure_point,
        trap_damage=trap_damage,
        bonus_multiplier=bonus_multiplier,
        treasure_func=_as_func(module, "upgrade_score_when_get_treasure", lambda score: score + treasure_point),
        trap_func=_as_func(module, "upgrade_hp_when_hit_trap", lambda hp: hp - trap_damage),
        bonus_func=_as_func(module, "upgrade_score_when_get_bonus", lambda score: score * bonus_multiplier),
    )


class TreasureScoreGame:
    def __init__(self, root: tk.Tk, config: GameConfig) -> None:
        self.root = root
        self.config = config
        self.root.title("시즌 1 - 보물 점수 게임")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#f8fbff", highlightthickness=0)
        self.canvas.pack()

        self.keys: set[str] = set()
        self.hero_x = 80
        self.hero_y = 270
        self.hero_size = 34
        self.score = config.score
        self.hp = config.hp
        self.max_hp = max(1, config.hp)
        self.message = config.start_message
        self.game_over = False
        self.win = False
        self.tick = 0

        self.items = [
            Item("treasure", 230, 155),
            Item("treasure", 480, 335),
            Item("treasure", 700, 190),
            Item("bonus", 765, 360),
            Item("trap", 345, 255),
            Item("trap", 610, 290),
        ]

        root.bind("<KeyPress>", self.on_key_press)
        root.bind("<KeyRelease>", self.on_key_release)

        print(config.start_message)
        self.loop()

    def on_key_press(self, event: tk.Event) -> None:
        key = event.keysym
        self.keys.add(key)
        if key == "space":
            self.try_collect()
        elif key.lower() == "r":
            self.reset()

    def on_key_release(self, event: tk.Event) -> None:
        self.keys.discard(event.keysym)

    def reset(self) -> None:
        self.hero_x = 80
        self.hero_y = 270
        self.score = self.config.score
        self.hp = self.config.hp
        self.max_hp = max(1, self.config.hp)
        self.message = self.config.start_message
        self.game_over = False
        self.win = False
        for item in self.items:
            item.collected = False
            item.triggered = False

    def loop(self) -> None:
        self.update()
        self.draw()
        self.root.after(33, self.loop)

    def update(self) -> None:
        self.tick += 1
        if self.game_over or self.win:
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

        self.hero_x = max(25, min(WIDTH - 25, self.hero_x + dx))
        self.hero_y = max(PLAY_TOP + 25, min(PLAY_BOTTOM - 25, self.hero_y + dy))

        for item in self.items:
            if item.kind == "trap" and not item.triggered and self._near(item, 36):
                old_hp = self.hp
                self.hp = _safe_call(self.config.trap_func, self.hp, self.hp - self.config.trap_damage)
                item.triggered = True
                self.message = f"앗, 함정! 체력 {old_hp} -> {self.hp}"
                if self.hp <= 0:
                    self.hp = 0
                    self.game_over = True
                    self.message = "체력이 0이 되었어. R 키로 다시 도전!"

        if all(item.collected or item.kind == "trap" for item in self.items) and not self.win:
            self.win = True
            self.message = f"성공! {self.config.hero_name}의 최종 점수는 {self.score}점!"

    def try_collect(self) -> None:
        if self.game_over or self.win:
            return

        for item in self.items:
            if item.collected or item.kind == "trap":
                continue
            if self._near(item, 48):
                old_score = self.score
                if item.kind == "bonus":
                    self.score = _safe_call(self.config.bonus_func, self.score, self.score * self.config.bonus_multiplier)
                    self.message = f"반짝 보너스! 점수 {old_score} -> {self.score}"
                else:
                    self.score = _safe_call(self.config.treasure_func, self.score, self.score + self.config.treasure_point)
                    self.message = f"보물 획득! 점수 {old_score} -> {self.score}"
                item.collected = True
                return

        self.message = self.config.hero_message

    def _near(self, item: Item, distance: int) -> bool:
        return abs(self.hero_x - item.x) <= distance and abs(self.hero_y - item.y) <= distance

    def draw(self) -> None:
        c = self.canvas
        c.delete("all")
        self._draw_background(c)
        self._draw_items(c)
        self._draw_hero(c)
        self._draw_hud(c)
        self._draw_footer(c)

    def _draw_background(self, c: tk.Canvas) -> None:
        c.create_rectangle(0, 0, WIDTH, HUD_HEIGHT, fill="#18324a", outline="")
        c.create_rectangle(0, PLAY_TOP, WIDTH, PLAY_BOTTOM, fill="#e8f4ff", outline="")
        c.create_rectangle(0, PLAY_BOTTOM, WIDTH, HEIGHT, fill="#fff7d8", outline="")

        for x in range(40, WIDTH, 80):
            c.create_oval(x, 132, x + 14, 146, fill="#c5e5d4", outline="")
        for x in range(0, WIDTH, 60):
            c.create_line(x, PLAY_TOP, x + 80, PLAY_BOTTOM, fill="#d6e9f8", width=1)

        c.create_text(
            WIDTH // 2,
            32,
            text=self.config.title,
            fill="white",
            font=(FONT_FAMILY, 22, "bold"),
        )
        c.create_text(
            WIDTH // 2,
            64,
            text=self.config.status_text,
            fill="#cdefff",
            font=(FONT_FAMILY, 12),
        )

    def _draw_hud(self, c: tk.Canvas) -> None:
        c.create_text(26, 22, text=f"이름: {self.config.hero_name}", anchor="w", fill="white", font=(FONT_FAMILY, 13, "bold"))
        c.create_text(26, 52, text=f"점수: {self.score}", anchor="w", fill="#ffe36e", font=(FONT_FAMILY, 15, "bold"))

        hp_width = 180
        hp_ratio = max(0, min(1, self.hp / self.max_hp))
        c.create_text(690, 22, text=f"체력: {self.hp}", anchor="w", fill="white", font=(FONT_FAMILY, 13, "bold"))
        c.create_rectangle(690, 45, 690 + hp_width, 64, fill="#5d7185", outline="")
        c.create_rectangle(690, 45, 690 + int(hp_width * hp_ratio), 64, fill="#ff6b6b", outline="")
        c.create_rectangle(690, 45, 690 + hp_width, 64, outline="#d7e7f5", width=2)

    def _draw_items(self, c: tk.Canvas) -> None:
        for item in self.items:
            if item.collected:
                continue
            if item.kind == "treasure":
                self._draw_coin(c, item.x, item.y)
            elif item.kind == "bonus":
                self._draw_star(c, item.x, item.y)
            elif item.kind == "trap":
                self._draw_trap(c, item.x, item.y, item.triggered)

    def _draw_coin(self, c: tk.Canvas, x: int, y: int) -> None:
        c.create_oval(x - 18, y - 18, x + 18, y + 18, fill="#ffd34e", outline="#b67800", width=3)
        c.create_text(x, y, text="$", fill="#7a4b00", font=(FONT_FAMILY, 18, "bold"))

    def _draw_star(self, c: tk.Canvas, x: int, y: int) -> None:
        points = [
            x, y - 28,
            x + 8, y - 8,
            x + 29, y - 8,
            x + 12, y + 5,
            x + 18, y + 26,
            x, y + 13,
            x - 18, y + 26,
            x - 12, y + 5,
            x - 29, y - 8,
            x - 8, y - 8,
        ]
        c.create_polygon(points, fill="#9b7cff", outline="#5a3fd8", width=3)

    def _draw_trap(self, c: tk.Canvas, x: int, y: int, triggered: bool) -> None:
        color = "#a3a3a3" if triggered else "#ff7b54"
        c.create_polygon(x - 24, y + 20, x, y - 24, x + 24, y + 20, fill=color, outline="#74321d", width=3)
        c.create_text(x, y + 8, text="!", fill="white", font=(FONT_FAMILY, 18, "bold"))

    def _draw_hero(self, c: tk.Canvas) -> None:
        x = self.hero_x
        y = self.hero_y
        bounce = 3 if (self.tick // 10) % 2 == 0 else 0
        c.create_oval(x - 20, y + 23, x + 20, y + 31, fill="#8fb3c7", outline="")
        c.create_oval(x - 19, y - 24 - bounce, x + 19, y + 14 - bounce, fill="#4f9cff", outline="#1d4d91", width=3)
        c.create_oval(x - 8, y - 12 - bounce, x - 3, y - 7 - bounce, fill="white", outline="")
        c.create_oval(x + 5, y - 12 - bounce, x + 10, y - 7 - bounce, fill="white", outline="")
        c.create_arc(x - 8, y - 5 - bounce, x + 10, y + 8 - bounce, start=200, extent=140, style=tk.ARC, outline="white", width=2)
        c.create_rectangle(x - 16, y + 14 - bounce, x + 16, y + 38 - bounce, fill="#2dd4bf", outline="#0f766e", width=3)
        c.create_text(x, y + 56, text=self.config.hero_name, fill="#14324a", font=(FONT_FAMILY, 11, "bold"))

    def _draw_footer(self, c: tk.Canvas) -> None:
        c.create_text(28, PLAY_BOTTOM + 24, text=self.message, anchor="w", fill="#3a2a08", font=(FONT_FAMILY, 15, "bold"))
        c.create_text(
            28,
            PLAY_BOTTOM + 58,
            text="방향키: 이동   스페이스: 보물 줍기/대사 보기   R: 다시 시작",
            anchor="w",
            fill="#6b5a1f",
            font=(FONT_FAMILY, 11),
        )
        if self.game_over:
            c.create_rectangle(270, 205, 630, 315, fill="#fff1f2", outline="#fb7185", width=4)
            c.create_text(450, 246, text="게임 오버", fill="#be123c", font=(FONT_FAMILY, 28, "bold"))
            c.create_text(450, 286, text="R 키로 다시 도전!", fill="#7f1d1d", font=(FONT_FAMILY, 14, "bold"))
        elif self.win:
            c.create_rectangle(245, 198, 655, 320, fill="#ecfdf5", outline="#10b981", width=4)
            c.create_text(450, 240, text="보물 모으기 성공!", fill="#047857", font=(FONT_FAMILY, 25, "bold"))
            c.create_text(450, 284, text=f"최종 점수: {self.score}", fill="#065f46", font=(FONT_FAMILY, 16, "bold"))


def run_game() -> None:
    try:
        config = load_config()
    except Exception:
        error = traceback.format_exc()
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("upgrade_zone.py 확인", "업그레이드 존 코드에 문제가 있어요.\n\n터미널의 오류 내용을 확인해 주세요.")
        print(error)
        return

    root = tk.Tk()
    TreasureScoreGame(root, config)
    root.mainloop()


def check_game_files() -> None:
    config = load_config()
    game_dir = Path(__file__).resolve().parent
    print("시즌 1 보물 점수 게임 확인 완료")
    print(f"폴더: {game_dir}")
    print(f"주인공: {config.hero_name}")
    print(f"시작 점수: {config.score}")
    print(f"체력: {config.hp}")
    print(f"속도: {config.speed}")
    print(f"보물 점수: {config.treasure_point}")
    print(f"함정 데미지: {config.trap_damage}")
    print(f"보너스 배율: {config.bonus_multiplier}")
