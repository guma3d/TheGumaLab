from __future__ import annotations

import importlib
import traceback
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox
from types import ModuleType
from typing import Any, Callable


WIDTH = 960
HEIGHT = 640
FONT = "Malgun Gothic"


@dataclass
class AdventureConfig:
    dice_min: int
    dice_max: int
    treasure_items: list[str]
    boss_wait_seconds: float
    score_file: str
    win_score: int
    hero_name: str
    final_goal: str
    jump: Callable[[], str]
    say_hello: Callable[[], str]
    attack: Callable[[int], int]
    add_score: Callable[[int, int], int]
    random_damage: Callable[[], int]
    random_treasure: Callable[[], str]
    boss_entrance: Callable[[], str]
    save_score: Callable[[int], str]
    load_score: Callable[[], int]
    safe_number: Callable[[str], int | None]
    check_win: Callable[[int], str]


def _load_upgrade_zone() -> ModuleType:
    return importlib.import_module("upgrade_zone")


def _int(module: ModuleType, name: str, default: int, low: int = -9999, high: int = 9999) -> int:
    try:
        value = int(getattr(module, name, default))
    except Exception:
        value = default
    return max(low, min(high, value))


def _float(module: ModuleType, name: str, default: float, low: float = 0.0, high: float = 5.0) -> float:
    try:
        value = float(getattr(module, name, default))
    except Exception:
        value = default
    return max(low, min(high, value))


def _text(module: ModuleType, name: str, default: str) -> str:
    return str(getattr(module, name, default))


def _list(module: ModuleType, name: str, default: list[str]) -> list[str]:
    value = getattr(module, name, default)
    if isinstance(value, list) and value:
        return [str(item) for item in value]
    return list(default)


def _func(module: ModuleType, name: str, fallback: Callable[..., Any]) -> Callable[..., Any]:
    value = getattr(module, name, fallback)
    if callable(value):
        return value
    return fallback


def _safe_text(func: Callable[..., Any], *args: Any, fallback: str) -> str:
    try:
        return str(func(*args))
    except Exception:
        return fallback


def _safe_int(func: Callable[..., Any], *args: Any, fallback: int) -> int:
    try:
        return int(func(*args))
    except Exception:
        return fallback


def load_config() -> AdventureConfig:
    module = _load_upgrade_zone()
    dice_min = _int(module, "dice_min", 1)
    dice_max = _int(module, "dice_max", 6)
    if dice_max < dice_min:
        dice_min, dice_max = dice_max, dice_min

    return AdventureConfig(
        dice_min=dice_min,
        dice_max=dice_max,
        treasure_items=_list(module, "treasure_items", ["동전", "보석", "황금열쇠"]),
        boss_wait_seconds=_float(module, "boss_wait_seconds", 1),
        score_file=_text(module, "score_file", "high_score.txt"),
        win_score=_int(module, "win_score", 100, 1, 99999),
        hero_name=_text(module, "hero_name", "보물 사냥꾼"),
        final_goal=_text(module, "final_goal", "전설의 황금열쇠를 찾아라!"),
        jump=_func(module, "jump", lambda: "점프!"),
        say_hello=_func(module, "say_hello", lambda: "안녕!"),
        attack=_func(module, "attack", lambda power: power * 2),
        add_score=_func(module, "add_score", lambda score, gained: score + gained),
        random_damage=_func(module, "random_damage", lambda: dice_min),
        random_treasure=_func(module, "random_treasure", lambda: "동전"),
        boss_entrance=_func(module, "boss_entrance", lambda: "보스 등장!"),
        save_score=_func(module, "save_score", lambda score: "점수 저장 완료!"),
        load_score=_func(module, "load_score", lambda: 0),
        safe_number=_func(module, "safe_number", lambda text: int(text) if str(text).isdigit() else None),
        check_win=_func(module, "check_win", lambda score: "승리!" if score >= 100 else "아직 더 모아야 해!"),
    )


class MiniAdventureGame:
    def __init__(self, root: tk.Tk, config: AdventureConfig) -> None:
        self.root = root
        self.config = config
        self.root.title("시즌 4 - 미니 어드벤처 게임")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#f7fee7", highlightthickness=0)
        self.canvas.pack()

        self.x = 90
        self.y = 330
        self.score = 0
        self.high_score = 0
        self.power = 5
        self.boss_hp = 40
        self.jump_timer = 0
        self.message = config.final_goal
        self.logs = ["미니 어드벤처 시작!"]
        self.chests = [
            {"x": 290, "y": 230, "open": False},
            {"x": 520, "y": 370, "open": False},
            {"x": 765, "y": 250, "open": False},
        ]

        root.bind("<KeyPress>", self.on_key)
        self.number_entry = tk.Entry(root, font=(FONT, 12), width=10)
        self.number_entry.insert(0, "7")
        self._create_buttons()
        self.draw()

    def _create_buttons(self) -> None:
        buttons = [
            ("인사", self.say_hello),
            ("점프", self.jump),
            ("공격", self.attack_boss),
            ("상자", self.open_chest),
            ("보스등장", self.boss_intro),
            ("저장", self.save),
            ("불러오기", self.load),
            ("숫자검사", self.safe_number_test),
            ("다시", self.reset),
        ]
        x = 68
        y = 598
        for label, command in buttons:
            button = tk.Button(self.root, text=label, font=(FONT, 10, "bold"), command=command, width=8)
            self.canvas.create_window(x, y, window=button)
            x += 82
        self.canvas.create_window(842, 598, window=self.number_entry)

    def on_key(self, event: tk.Event) -> None:
        key = event.keysym
        if key == "Left":
            self.x = max(40, self.x - 18)
        elif key == "Right":
            self.x = min(WIDTH - 40, self.x + 18)
        elif key == "Up":
            self.y = max(125, self.y - 18)
        elif key == "Down":
            self.y = min(510, self.y + 18)
        elif key == "space":
            self.jump()
        elif key.lower() == "a":
            self.attack_boss()
        elif key.lower() == "e":
            self.open_chest()
        elif key.lower() == "r":
            self.reset()
        self.draw()

    def add_log(self, text: str) -> None:
        self.message = text
        self.logs.append(text)
        self.logs = self.logs[-7:]
        self.high_score = max(self.high_score, self.score)
        self.draw()

    def say_hello(self) -> None:
        self.add_log(_safe_text(self.config.say_hello, fallback="안녕!"))

    def jump(self) -> None:
        self.jump_timer = 10
        self.add_log(_safe_text(self.config.jump, fallback="점프!"))

    def attack_boss(self) -> None:
        damage = _safe_int(self.config.attack, self.power, fallback=self.power * 2)
        dice = _safe_int(self.config.random_damage, fallback=self.config.dice_min)
        total = max(0, damage + dice)
        old_hp = self.boss_hp
        self.boss_hp = max(0, self.boss_hp - total)
        self.score = _safe_int(self.config.add_score, self.score, total, fallback=self.score + total)
        text = f"공격 {total}! 보스 HP {old_hp} -> {self.boss_hp}"
        if self.boss_hp <= 0:
            text += " 보스 클리어!"
        self.add_log(text)

    def open_chest(self) -> None:
        for chest in self.chests:
            if chest["open"]:
                continue
            if abs(self.x - chest["x"]) < 60 and abs(self.y - chest["y"]) < 60:
                chest["open"] = True
                item = _safe_text(self.config.random_treasure, fallback="동전")
                gained = 50 if "황금" in item else 30 if "보석" in item else 10
                old = self.score
                self.score = _safe_int(self.config.add_score, self.score, gained, fallback=self.score + gained)
                result = _safe_text(self.config.check_win, self.score, fallback="")
                self.add_log(f"{item} 획득! 점수 {old} -> {self.score}. {result}")
                return
        self.add_log("상자 가까이에서 E 또는 상자 버튼을 눌러봐!")

    def boss_intro(self) -> None:
        text = _safe_text(self.config.boss_entrance, fallback="보스 등장!")
        self.add_log(text)

    def save(self) -> None:
        text = _safe_text(self.config.save_score, self.score, fallback="점수 저장 완료!")
        self.add_log(text)

    def load(self) -> None:
        score = _safe_int(self.config.load_score, fallback=0)
        self.high_score = max(self.high_score, score)
        self.add_log(f"저장된 점수: {score}")

    def safe_number_test(self) -> None:
        text = self.number_entry.get()
        try:
            value = self.config.safe_number(text)
        except Exception:
            value = None
        if value is None:
            self.add_log("숫자가 아니야. 다시 넣어보자!")
        else:
            self.power = int(value)
            self.add_log(f"공격력 숫자 확인! power = {self.power}")

    def reset(self) -> None:
        self.x = 90
        self.y = 330
        self.score = 0
        self.power = 5
        self.boss_hp = 40
        self.jump_timer = 0
        for chest in self.chests:
            chest["open"] = False
        self.logs = ["모험을 다시 시작했어."]
        self.message = self.config.final_goal
        self.draw()

    def draw(self) -> None:
        if self.jump_timer > 0:
            self.jump_timer -= 1

        c = self.canvas
        c.delete("scene")
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#f7fee7", outline="", tags="scene")
        c.create_rectangle(0, 0, WIDTH, 92, fill="#14532d", outline="", tags="scene")
        c.create_text(WIDTH // 2, 30, text="미니 어드벤처 게임", fill="white", font=(FONT, 24, "bold"), tags="scene")
        c.create_text(WIDTH // 2, 64, text=self.message, fill="#dcfce7", font=(FONT, 13, "bold"), tags="scene")

        self._draw_map(c)
        self._draw_player(c)
        self._draw_hud(c)
        self._draw_logs(c)
        self._draw_hint(c)
        if self.jump_timer > 0:
            self.root.after(40, self.draw)

    def _draw_map(self, c: tk.Canvas) -> None:
        c.create_rectangle(34, 118, 625, 535, fill="#bbf7d0", outline="#22c55e", width=4, tags="scene")
        for x in range(70, 610, 86):
            c.create_oval(x, 465, x + 32, 498, fill="#86efac", outline="", tags="scene")
        c.create_rectangle(690, 170, 875, 330, fill="#fee2e2", outline="#ef4444", width=4, tags="scene")
        c.create_text(782, 160, text="보스 구역", fill="#991b1b", font=(FONT, 14, "bold"), tags="scene")
        c.create_oval(727, 210, 835, 318, fill="#ef4444", outline="#991b1b", width=5, tags="scene")
        c.create_text(781, 264, text=f"HP {self.boss_hp}", fill="white", font=(FONT, 16, "bold"), tags="scene")

        for chest in self.chests:
            x = int(chest["x"])
            y = int(chest["y"])
            if chest["open"]:
                c.create_rectangle(x - 25, y - 10, x + 25, y + 22, fill="#a3a3a3", outline="#525252", width=3, tags="scene")
                c.create_text(x, y + 6, text="열림", fill="white", font=(FONT, 10, "bold"), tags="scene")
            else:
                c.create_rectangle(x - 26, y - 18, x + 26, y + 22, fill="#b45309", outline="#78350f", width=3, tags="scene")
                c.create_rectangle(x - 18, y - 28, x + 18, y - 12, fill="#f59e0b", outline="#78350f", width=3, tags="scene")
                c.create_text(x, y + 3, text="?", fill="#fef3c7", font=(FONT, 18, "bold"), tags="scene")

    def _draw_player(self, c: tk.Canvas) -> None:
        jump_offset = 22 if self.jump_timer > 0 else 0
        x = self.x
        y = self.y - jump_offset
        c.create_oval(x - 20, y + 24, x + 20, y + 32, fill="#65a30d", outline="", tags="scene")
        c.create_oval(x - 21, y - 26, x + 21, y + 16, fill="#38bdf8", outline="#0369a1", width=4, tags="scene")
        c.create_rectangle(x - 18, y + 15, x + 18, y + 42, fill="#facc15", outline="#a16207", width=3, tags="scene")
        c.create_text(x, y + 61, text=self.config.hero_name, fill="#365314", font=(FONT, 10, "bold"), tags="scene")

    def _draw_hud(self, c: tk.Canvas) -> None:
        c.create_rectangle(650, 360, 918, 454, fill="#fefce8", outline="#fde047", width=4, tags="scene")
        lines = [
            f"점수: {self.score}",
            f"최고 점수: {self.high_score}",
            f"공격력: {self.power}",
            f"승리 점수: {self.config.win_score}",
        ]
        y = 383
        for line in lines:
            c.create_text(670, y, text=line, anchor="w", fill="#713f12", font=(FONT, 12, "bold"), tags="scene")
            y += 20

    def _draw_logs(self, c: tk.Canvas) -> None:
        c.create_rectangle(650, 468, 918, 555, fill="#eff6ff", outline="#93c5fd", width=4, tags="scene")
        c.create_text(670, 491, text="모험 기록", anchor="w", fill="#1d4ed8", font=(FONT, 13, "bold"), tags="scene")
        y = 516
        for log in self.logs[-2:]:
            c.create_text(670, y, text=log[:28], anchor="w", fill="#1e3a8a", font=(FONT, 10), tags="scene")
            y += 22

    def _draw_hint(self, c: tk.Canvas) -> None:
        c.create_text(36, 564, text="방향키: 이동   Space: 점프   A: 공격   E: 상자 열기   R: 다시 시작", anchor="w", fill="#365314", font=(FONT, 11, "bold"), tags="scene")
        c.create_text(842, 568, text="숫자검사 입력", fill="#365314", font=(FONT, 10, "bold"), tags="scene")


def run_game() -> None:
    try:
        config = load_config()
    except Exception:
        print(traceback.format_exc())
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("upgrade_zone.py 확인", "업그레이드 존 코드에 문제가 있어요.")
        return

    root = tk.Tk()
    MiniAdventureGame(root, config)
    root.mainloop()


def check_game_files() -> None:
    config = load_config()
    game_dir = Path(__file__).resolve().parent
    print("시즌 4 미니 어드벤처 게임 확인 완료")
    print(f"폴더: {game_dir}")
    print(f"주인공: {config.hero_name}")
    print(f"목표: {config.final_goal}")
    print(f"랜덤 데미지: {config.dice_min}~{config.dice_max}")
    print(f"보물 목록: {config.treasure_items}")
    print(f"승리 점수: {config.win_score}")
    print(f"점수 파일: {config.score_file}")
