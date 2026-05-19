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
class DungeonConfig:
    default_name: str
    default_weapon: str
    hp: int
    level: int
    required_level: int
    has_key: bool
    has_gem: bool
    red_key: bool
    blue_key: bool
    secret_password: str
    power_bonus: int
    treasure_score: int
    make_enter_message: Callable[[str], str]
    make_weapon_message: Callable[[str], str]
    make_damage: Callable[[int], int]
    can_open_key_door: Callable[[], bool]
    is_password_correct: Callable[[str], bool]
    password_result_message: Callable[[str], str]
    weapon_result: Callable[[str], str]
    hp_warning: Callable[[int], str]
    can_enter_boss_room: Callable[[int], bool]
    can_open_double_lock: Callable[[], bool]
    can_open_color_door: Callable[[], bool]
    treasure_box_result: Callable[[], tuple[str, int]]


def _load_upgrade_zone() -> ModuleType:
    return importlib.import_module("upgrade_zone")


def _text(module: ModuleType, name: str, default: str) -> str:
    return str(getattr(module, name, default))


def _int(module: ModuleType, name: str, default: int, low: int = -9999, high: int = 9999) -> int:
    try:
        value = int(getattr(module, name, default))
    except Exception:
        value = default
    return max(low, min(high, value))


def _bool(module: ModuleType, name: str, default: bool) -> bool:
    return bool(getattr(module, name, default))


def _func(module: ModuleType, name: str, fallback: Callable[..., Any]) -> Callable[..., Any]:
    value = getattr(module, name, fallback)
    if callable(value):
        return value
    return fallback


def _safe_text_call(func: Callable[..., Any], *args: Any, fallback: str) -> str:
    try:
        return str(func(*args))
    except Exception:
        return fallback


def _safe_bool_call(func: Callable[..., Any], *args: Any, fallback: bool = False) -> bool:
    try:
        return bool(func(*args))
    except Exception:
        return fallback


def _safe_int_call(func: Callable[..., Any], *args: Any, fallback: int = 0) -> int:
    try:
        return int(func(*args))
    except Exception:
        return fallback


def load_config() -> DungeonConfig:
    module = _load_upgrade_zone()
    secret_password = _text(module, "secret_password", "1234")
    power_bonus = _int(module, "power_bonus", 2)
    treasure_score = _int(module, "treasure_score", 100)

    return DungeonConfig(
        default_name=_text(module, "default_name", "용감한 모험가"),
        default_weapon=_text(module, "default_weapon", "검"),
        hp=_int(module, "hp", 100, 1, 9999),
        level=_int(module, "level", 5, 1, 999),
        required_level=_int(module, "required_level", 5, 1, 999),
        has_key=_bool(module, "has_key", True),
        has_gem=_bool(module, "has_gem", False),
        red_key=_bool(module, "red_key", False),
        blue_key=_bool(module, "blue_key", True),
        secret_password=secret_password,
        power_bonus=power_bonus,
        treasure_score=treasure_score,
        make_enter_message=_func(module, "make_enter_message", lambda name: name + " 던전에 입장!"),
        make_weapon_message=_func(module, "make_weapon_message", lambda weapon: weapon + " 장착 완료!"),
        make_damage=_func(module, "make_damage", lambda power: power + power_bonus),
        can_open_key_door=_func(module, "can_open_key_door", lambda: True),
        is_password_correct=_func(module, "is_password_correct", lambda password: password == secret_password),
        password_result_message=_func(module, "password_result_message", lambda password: "비밀번호 성공!" if password == secret_password else "문이 잠겼어!"),
        weapon_result=_func(module, "weapon_result", lambda weapon: weapon + " 선택!"),
        hp_warning=_func(module, "hp_warning", lambda hp: "위험!" if hp < 30 else "아직 괜찮아!"),
        can_enter_boss_room=_func(module, "can_enter_boss_room", lambda level: level >= 5),
        can_open_double_lock=_func(module, "can_open_double_lock", lambda: False),
        can_open_color_door=_func(module, "can_open_color_door", lambda: True),
        treasure_box_result=_func(module, "treasure_box_result", lambda: ("반짝 보석 획득!", treasure_score)),
    )


class DungeonChoiceGame:
    def __init__(self, root: tk.Tk, config: DungeonConfig) -> None:
        self.root = root
        self.config = config
        self.score = 0
        self.player_name = config.default_name
        self.weapon = config.default_weapon
        self.power = 5
        self.message = "던전 업그레이드를 시작하자!"
        self.logs: list[str] = ["버튼을 눌러 던전 규칙을 테스트해 보세요."]

        root.title("시즌 2 - 던전 선택 게임")
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#101827", highlightthickness=0)
        self.canvas.pack()

        self.name_entry = tk.Entry(root, font=(FONT, 12), width=16)
        self.name_entry.insert(0, config.default_name)
        self.weapon_entry = tk.Entry(root, font=(FONT, 12), width=12)
        self.weapon_entry.insert(0, config.default_weapon)
        self.power_entry = tk.Entry(root, font=(FONT, 12), width=8)
        self.power_entry.insert(0, "5")
        self.password_entry = tk.Entry(root, font=(FONT, 12), width=10)
        self.password_entry.insert(0, config.secret_password)

        self._create_controls()
        self.draw()

    def _create_controls(self) -> None:
        c = self.canvas
        c.create_window(120, 540, window=self.name_entry)
        c.create_window(298, 540, window=self.weapon_entry)
        c.create_window(438, 540, window=self.power_entry)
        c.create_window(575, 540, window=self.password_entry)

        buttons = [
            ("입장", self.enter_dungeon),
            ("공격력", self.test_power),
            ("열쇠문", self.key_door),
            ("비밀번호", self.password_door),
            ("무기선택", self.weapon_choice),
            ("체력경고", self.hp_check),
            ("레벨문", self.level_door),
            ("이중잠금", self.double_lock),
            ("색열쇠", self.color_door),
            ("보물상자", self.treasure_box),
            ("다시", self.reset),
        ]
        x = 88
        y = 592
        for label, command in buttons:
            button = tk.Button(self.root, text=label, font=(FONT, 10, "bold"), command=command, width=8)
            c.create_window(x, y, window=button)
            x += 78

    def add_log(self, text: str) -> None:
        self.message = text
        self.logs.append(text)
        self.logs = self.logs[-7:]
        self.draw()

    def enter_dungeon(self) -> None:
        self.player_name = self.name_entry.get().strip() or self.config.default_name
        text = _safe_text_call(self.config.make_enter_message, self.player_name, fallback=f"{self.player_name} 던전에 입장!")
        self.add_log(text)

    def weapon_choice(self) -> None:
        self.weapon = self.weapon_entry.get().strip() or self.config.default_weapon
        equip = _safe_text_call(self.config.make_weapon_message, self.weapon, fallback=f"{self.weapon} 장착 완료!")
        result = _safe_text_call(self.config.weapon_result, self.weapon, fallback=f"{self.weapon} 선택!")
        self.add_log(equip + " " + result)

    def test_power(self) -> None:
        try:
            self.power = int(self.power_entry.get())
        except ValueError:
            self.add_log("공격력에는 숫자를 넣어야 해!")
            return
        damage = _safe_int_call(self.config.make_damage, self.power, fallback=self.power + self.config.power_bonus)
        self.add_log(f"공격력 {self.power} -> 데미지 {damage}")

    def key_door(self) -> None:
        if _safe_bool_call(self.config.can_open_key_door):
            self.add_log("철컥! 열쇠문이 열렸어.")
        else:
            self.add_log("열쇠가 없어서 문이 닫혀 있어.")

    def password_door(self) -> None:
        password = self.password_entry.get()
        text = _safe_text_call(self.config.password_result_message, password, fallback="비밀번호를 다시 확인해 봐!")
        if _safe_bool_call(self.config.is_password_correct, password):
            text += " 숨겨진 길 발견!"
        self.add_log(text)

    def hp_check(self) -> None:
        text = _safe_text_call(self.config.hp_warning, self.config.hp, fallback="체력 확인!")
        self.add_log(f"현재 체력 {self.config.hp}. {text}")

    def level_door(self) -> None:
        if _safe_bool_call(self.config.can_enter_boss_room, self.config.level):
            self.add_log(f"레벨 {self.config.level}! 보스방 입장 가능.")
        else:
            self.add_log(f"레벨 {self.config.level}. 보스방은 레벨 {self.config.required_level}부터야.")

    def double_lock(self) -> None:
        if _safe_bool_call(self.config.can_open_double_lock):
            self.add_log("열쇠와 보석이 모두 있어! 이중잠금 해제.")
        else:
            self.add_log("이중잠금은 열쇠와 보석이 모두 필요해.")

    def color_door(self) -> None:
        if _safe_bool_call(self.config.can_open_color_door):
            self.add_log("색 열쇠 문이 열렸어!")
        else:
            self.add_log("빨간 열쇠나 파란 열쇠가 필요해.")

    def treasure_box(self) -> None:
        try:
            text, points = self.config.treasure_box_result()
            points = int(points)
        except Exception:
            text, points = "상자 규칙에 문제가 있어.", 0
        self.score += points
        self.add_log(f"{text} 점수 +{points}")

    def reset(self) -> None:
        self.score = 0
        self.logs = ["던전을 다시 시작했어."]
        self.message = "던전 업그레이드를 시작하자!"
        self.draw()

    def draw(self) -> None:
        c = self.canvas
        c.delete("scene")
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#101827", outline="", tags="scene")
        c.create_rectangle(0, 0, WIDTH, 92, fill="#25143d", outline="", tags="scene")
        c.create_text(WIDTH // 2, 30, text="던전 선택 게임", fill="#f8fafc", font=(FONT, 24, "bold"), tags="scene")
        c.create_text(WIDTH // 2, 64, text=self.message, fill="#facc15", font=(FONT, 14, "bold"), tags="scene")

        self._draw_dungeon(c)
        self._draw_status(c)
        self._draw_log(c)
        self._draw_input_labels(c)

    def _draw_dungeon(self, c: tk.Canvas) -> None:
        c.create_rectangle(50, 125, 570, 470, fill="#273449", outline="#64748b", width=4, tags="scene")
        c.create_polygon(50, 125, 310, 55, 570, 125, fill="#3b2f5c", outline="#64748b", width=4, tags="scene")
        c.create_rectangle(245, 255, 375, 470, fill="#5b3a24", outline="#d6a55d", width=5, tags="scene")
        c.create_oval(345, 365, 358, 378, fill="#facc15", outline="", tags="scene")
        c.create_text(310, 195, text="비밀의 문", fill="#e2e8f0", font=(FONT, 18, "bold"), tags="scene")

        colors = [("#f59e0b", 115, 390), ("#22c55e", 165, 360), ("#3b82f6", 455, 375), ("#ef4444", 505, 350)]
        for color, x, y in colors:
            c.create_oval(x - 16, y - 16, x + 16, y + 16, fill=color, outline="#f8fafc", width=2, tags="scene")

    def _draw_status(self, c: tk.Canvas) -> None:
        x0 = 620
        c.create_rectangle(x0, 125, 910, 322, fill="#f8fafc", outline="#cbd5e1", width=3, tags="scene")
        lines = [
            f"플레이어: {self.player_name}",
            f"무기: {self.weapon}",
            f"점수: {self.score}",
            f"체력: {self.config.hp}",
            f"레벨: {self.config.level}",
            f"열쇠: {self.config.has_key}",
            f"보석: {self.config.has_gem}",
            f"빨간/파란 열쇠: {self.config.red_key}/{self.config.blue_key}",
        ]
        c.create_text(x0 + 18, 148, text="상태창", anchor="w", fill="#0f172a", font=(FONT, 15, "bold"), tags="scene")
        y = 184
        for line in lines:
            c.create_text(x0 + 18, y, text=line, anchor="w", fill="#1e293b", font=(FONT, 11), tags="scene")
            y += 20

    def _draw_log(self, c: tk.Canvas) -> None:
        c.create_rectangle(620, 342, 910, 470, fill="#fff7ed", outline="#fed7aa", width=3, tags="scene")
        c.create_text(638, 363, text="던전 기록", anchor="w", fill="#9a3412", font=(FONT, 13, "bold"), tags="scene")
        y = 390
        for line in self.logs[-4:]:
            c.create_text(638, y, text=line[:32], anchor="w", fill="#431407", font=(FONT, 10), tags="scene")
            y += 22

    def _draw_input_labels(self, c: tk.Canvas) -> None:
        labels = [("이름", 120), ("무기", 298), ("공격력", 438), ("비밀번호", 575)]
        for text, x in labels:
            c.create_text(x, 512, text=text, fill="#f8fafc", font=(FONT, 11, "bold"), tags="scene")


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
    DungeonChoiceGame(root, config)
    root.mainloop()


def check_game_files() -> None:
    config = load_config()
    game_dir = Path(__file__).resolve().parent
    print("시즌 2 던전 선택 게임 확인 완료")
    print(f"폴더: {game_dir}")
    print(f"기본 이름: {config.default_name}")
    print(f"기본 무기: {config.default_weapon}")
    print(f"비밀번호: {config.secret_password}")
    print(f"체력/레벨: {config.hp}/{config.level}")
    print(f"열쇠/보석: {config.has_key}/{config.has_gem}")
    print(f"빨간/파란 열쇠: {config.red_key}/{config.blue_key}")
