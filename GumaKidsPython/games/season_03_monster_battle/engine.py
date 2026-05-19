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
class BattleConfig:
    monster_hp: int
    player_power: int
    combo_count: int
    countdown_start: int
    escape_word: str
    trap_tile: str
    bag: list[str]
    reward_item: str
    discard_item: str
    monster: dict[str, Any]
    battle_until_defeat: Callable[[int], list[str]]
    count_attack_turns: Callable[[int], int]
    combo_attack: Callable[[], list[str]]
    boss_countdown: Callable[[], list[str]]
    dungeon_commands: Callable[[list[str]], list[str]]
    collect_path_rewards: Callable[[list[str]], list[str]]
    first_item: Callable[[], str]
    add_reward_item: Callable[[list[str]], list[str]]
    remove_old_item: Callable[[list[str]], list[str]]
    describe_bag: Callable[[list[str]], list[str]]


def _load_upgrade_zone() -> ModuleType:
    return importlib.import_module("upgrade_zone")


def _int(module: ModuleType, name: str, default: int, low: int = 1, high: int = 9999) -> int:
    try:
        value = int(getattr(module, name, default))
    except Exception:
        value = default
    return max(low, min(high, value))


def _text(module: ModuleType, name: str, default: str) -> str:
    return str(getattr(module, name, default))


def _list(module: ModuleType, name: str, default: list[str]) -> list[str]:
    value = getattr(module, name, default)
    if isinstance(value, list):
        return [str(item) for item in value]
    return list(default)


def _dict(module: ModuleType, name: str, default: dict[str, Any]) -> dict[str, Any]:
    value = getattr(module, name, default)
    if isinstance(value, dict):
        merged = dict(default)
        merged.update(value)
        return merged
    return dict(default)


def _func(module: ModuleType, name: str, fallback: Callable[..., Any]) -> Callable[..., Any]:
    value = getattr(module, name, fallback)
    if callable(value):
        return value
    return fallback


def _safe_logs(func: Callable[..., Any], *args: Any, fallback: list[str]) -> list[str]:
    try:
        result = func(*args)
        if isinstance(result, list):
            return [str(item) for item in result]
        return [str(result)]
    except Exception:
        return fallback


def _safe_int(func: Callable[..., Any], *args: Any, fallback: int) -> int:
    try:
        return int(func(*args))
    except Exception:
        return fallback


def load_config() -> BattleConfig:
    module = _load_upgrade_zone()
    default_monster = {"name": "슬라임", "hp": 30, "power": 5}
    player_power = _int(module, "player_power", 5)

    return BattleConfig(
        monster_hp=_int(module, "monster_hp", 30),
        player_power=player_power,
        combo_count=_int(module, "combo_count", 5),
        countdown_start=_int(module, "countdown_start", 3),
        escape_word=_text(module, "escape_word", "도망"),
        trap_tile=_text(module, "trap_tile", "함정"),
        bag=_list(module, "bag", ["물약", "검", "열쇠"]),
        reward_item=_text(module, "reward_item", "황금열쇠"),
        discard_item=_text(module, "discard_item", "낡은검"),
        monster=_dict(module, "monster", default_monster),
        battle_until_defeat=_func(module, "battle_until_defeat", lambda hp: ["공격!", "몬스터를 쓰러뜨렸어!"]),
        count_attack_turns=_func(module, "count_attack_turns", lambda hp: max(1, hp // max(1, player_power))),
        combo_attack=_func(module, "combo_attack", lambda: ["연속 공격!"]),
        boss_countdown=_func(module, "boss_countdown", lambda: ["3", "2", "1", "보스 등장!"]),
        dungeon_commands=_func(module, "dungeon_commands", lambda commands: commands),
        collect_path_rewards=_func(module, "collect_path_rewards", lambda path: [tile + " 보상" for tile in path if tile != "함정"]),
        first_item=_func(module, "first_item", lambda: "물약"),
        add_reward_item=_func(module, "add_reward_item", lambda bag: bag + ["황금열쇠"]),
        remove_old_item=_func(module, "remove_old_item", lambda bag: bag),
        describe_bag=_func(module, "describe_bag", lambda bag: ["가방 안에 " + item + " 있어!" for item in bag]),
    )


class MonsterBattleGame:
    def __init__(self, root: tk.Tk, config: BattleConfig) -> None:
        self.root = root
        self.config = config
        self.root.title("시즌 3 - 몬스터 배틀 게임")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#f8fafc", highlightthickness=0)
        self.canvas.pack()

        self.player_hp = 100
        self.monster_name = str(config.monster.get("name", "슬라임"))
        self.monster_hp = int(config.monster.get("hp", config.monster_hp))
        self.monster_max_hp = max(1, self.monster_hp)
        self.monster_power = int(config.monster.get("power", 5))
        self.bag = list(config.bag)
        self.turn = 1
        self.logs = ["몬스터 배틀 시작! 버튼으로 업그레이드를 테스트해 보세요."]
        self.message = "반복문과 가방을 써서 전투를 업그레이드하자!"

        self._create_buttons()
        self.draw()

    def _create_buttons(self) -> None:
        buttons = [
            ("공격", self.attack_once),
            ("계속공격", self.auto_battle),
            ("턴세기", self.count_turns),
            ("연속공격", self.combo),
            ("카운트다운", self.countdown),
            ("탈출명령", self.escape_test),
            ("함정길", self.trap_path),
            ("첫아이템", self.show_first_item),
            ("보상줍기", self.add_reward),
            ("아이템버리기", self.remove_item),
            ("가방보기", self.show_bag),
            ("다시", self.reset),
        ]
        x = 58
        y = 598
        for label, command in buttons:
            button = tk.Button(self.root, text=label, font=(FONT, 10, "bold"), command=command, width=8)
            self.canvas.create_window(x, y, window=button)
            x += 76

    def add_logs(self, logs: list[str]) -> None:
        for log in logs:
            self.logs.append(str(log))
        self.logs = self.logs[-9:]
        if logs:
            self.message = str(logs[-1])
        self.draw()

    def attack_once(self) -> None:
        old = self.monster_hp
        self.monster_hp = max(0, self.monster_hp - self.config.player_power)
        self.turn += 1
        logs = [f"공격! {self.monster_name} 체력 {old} -> {self.monster_hp}"]
        if self.monster_hp <= 0:
            logs.append("몬스터를 쓰러뜨렸어!")
        self.add_logs(logs)

    def auto_battle(self) -> None:
        logs = _safe_logs(self.config.battle_until_defeat, self.config.monster_hp, fallback=["계속 공격 실패"])
        self.monster_hp = 0
        self.add_logs(logs[-6:])

    def count_turns(self) -> None:
        turns = _safe_int(self.config.count_attack_turns, self.config.monster_hp, fallback=1)
        self.add_logs([f"몬스터를 쓰러뜨리려면 {turns}번 공격해야 해!"])

    def combo(self) -> None:
        logs = _safe_logs(self.config.combo_attack, fallback=["연속 공격!"])
        damage = self.config.player_power * max(1, len(logs))
        old = self.monster_hp
        self.monster_hp = max(0, self.monster_hp - damage)
        self.add_logs(logs + [f"총 데미지 {damage}! 체력 {old} -> {self.monster_hp}"])

    def countdown(self) -> None:
        logs = _safe_logs(self.config.boss_countdown, fallback=["3", "2", "1", "보스 등장!"])
        self.add_logs(logs)

    def escape_test(self) -> None:
        commands = ["공격", "방어", self.config.escape_word, "보물줍기"]
        logs = _safe_logs(self.config.dungeon_commands, commands, fallback=["탈출 테스트 실패"])
        self.add_logs(logs)

    def trap_path(self) -> None:
        path = ["동전", self.config.trap_tile, "보석", "열쇠"]
        rewards = _safe_logs(self.config.collect_path_rewards, path, fallback=["길 보상 실패"])
        self.add_logs(rewards)

    def show_first_item(self) -> None:
        try:
            item = str(self.config.first_item())
        except Exception:
            item = self.bag[0] if self.bag else "없음"
        self.add_logs([f"첫 번째 아이템은 {item}!"])

    def add_reward(self) -> None:
        self.bag = _safe_logs(self.config.add_reward_item, self.bag, fallback=self.bag + [self.config.reward_item])
        self.add_logs([f"{self.config.reward_item} 획득!", "가방: " + ", ".join(self.bag)])

    def remove_item(self) -> None:
        self.bag = _safe_logs(self.config.remove_old_item, self.bag, fallback=list(self.bag))
        self.add_logs([f"{self.config.discard_item} 버리기 시도", "가방: " + ", ".join(self.bag)])

    def show_bag(self) -> None:
        logs = _safe_logs(self.config.describe_bag, self.bag, fallback=["가방 확인 실패"])
        self.add_logs(logs)

    def reset(self) -> None:
        self.player_hp = 100
        self.monster_hp = int(self.config.monster.get("hp", self.config.monster_hp))
        self.monster_max_hp = max(1, self.monster_hp)
        self.bag = list(self.config.bag)
        self.turn = 1
        self.logs = ["전투를 다시 시작했어."]
        self.message = "반복문과 가방을 써서 전투를 업그레이드하자!"
        self.draw()

    def draw(self) -> None:
        c = self.canvas
        c.delete("scene")
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#f8fafc", outline="", tags="scene")
        c.create_rectangle(0, 0, WIDTH, 92, fill="#172554", outline="", tags="scene")
        c.create_text(WIDTH // 2, 30, text="몬스터 배틀 게임", fill="white", font=(FONT, 24, "bold"), tags="scene")
        c.create_text(WIDTH // 2, 64, text=self.message, fill="#bfdbfe", font=(FONT, 13, "bold"), tags="scene")
        self._draw_arena(c)
        self._draw_status(c)
        self._draw_logs(c)
        self._draw_bag(c)

    def _draw_arena(self, c: tk.Canvas) -> None:
        c.create_rectangle(36, 118, 610, 420, fill="#dbeafe", outline="#60a5fa", width=4, tags="scene")
        c.create_oval(105, 315, 245, 348, fill="#93c5fd", outline="", tags="scene")
        c.create_oval(120, 215, 220, 325, fill="#22c55e", outline="#15803d", width=4, tags="scene")
        c.create_text(170, 205, text="플레이어", fill="#14532d", font=(FONT, 13, "bold"), tags="scene")
        c.create_line(150, 325, 135, 365, fill="#15803d", width=5, tags="scene")
        c.create_line(190, 325, 210, 365, fill="#15803d", width=5, tags="scene")

        c.create_oval(382, 300, 552, 348, fill="#c4b5fd", outline="", tags="scene")
        c.create_oval(400, 185, 535, 330, fill="#a855f7", outline="#6b21a8", width=5, tags="scene")
        c.create_oval(430, 230, 448, 248, fill="white", outline="", tags="scene")
        c.create_oval(486, 230, 504, 248, fill="white", outline="", tags="scene")
        c.create_arc(442, 260, 494, 300, start=200, extent=140, style=tk.ARC, outline="white", width=3, tags="scene")
        c.create_text(468, 172, text=self.monster_name, fill="#581c87", font=(FONT, 14, "bold"), tags="scene")

    def _draw_status(self, c: tk.Canvas) -> None:
        c.create_rectangle(36, 438, 610, 552, fill="#eff6ff", outline="#bfdbfe", width=3, tags="scene")
        c.create_text(58, 462, text=f"턴: {self.turn}", anchor="w", fill="#1e3a8a", font=(FONT, 12, "bold"), tags="scene")
        c.create_text(58, 492, text=f"플레이어 공격력: {self.config.player_power}", anchor="w", fill="#1e3a8a", font=(FONT, 12), tags="scene")
        c.create_text(58, 522, text=f"몬스터 카드: {self.monster_name} / HP {self.config.monster.get('hp')} / 공격력 {self.monster_power}", anchor="w", fill="#1e3a8a", font=(FONT, 12), tags="scene")

        ratio = max(0, min(1, self.monster_hp / self.monster_max_hp))
        c.create_text(345, 462, text=f"몬스터 HP: {self.monster_hp}", anchor="w", fill="#7e22ce", font=(FONT, 12, "bold"), tags="scene")
        c.create_rectangle(345, 484, 560, 506, fill="#ddd6fe", outline="", tags="scene")
        c.create_rectangle(345, 484, 345 + int(215 * ratio), 506, fill="#a855f7", outline="", tags="scene")
        c.create_rectangle(345, 484, 560, 506, outline="#6b21a8", width=2, tags="scene")

    def _draw_logs(self, c: tk.Canvas) -> None:
        c.create_rectangle(640, 118, 918, 360, fill="#fff7ed", outline="#fdba74", width=4, tags="scene")
        c.create_text(660, 145, text="전투 로그", anchor="w", fill="#9a3412", font=(FONT, 14, "bold"), tags="scene")
        y = 176
        for log in self.logs[-7:]:
            c.create_text(660, y, text=log[:30], anchor="w", fill="#431407", font=(FONT, 10), tags="scene")
            y += 25

    def _draw_bag(self, c: tk.Canvas) -> None:
        c.create_rectangle(640, 382, 918, 552, fill="#ecfdf5", outline="#86efac", width=4, tags="scene")
        c.create_text(660, 410, text="아이템 가방", anchor="w", fill="#166534", font=(FONT, 14, "bold"), tags="scene")
        y = 442
        for item in self.bag[:5]:
            c.create_rectangle(662, y - 13, 888, y + 13, fill="#dcfce7", outline="#bbf7d0", tags="scene")
            c.create_text(674, y, text=item, anchor="w", fill="#14532d", font=(FONT, 11, "bold"), tags="scene")
            y += 28


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
    MonsterBattleGame(root, config)
    root.mainloop()


def check_game_files() -> None:
    config = load_config()
    game_dir = Path(__file__).resolve().parent
    print("시즌 3 몬스터 배틀 게임 확인 완료")
    print(f"폴더: {game_dir}")
    print(f"몬스터: {config.monster}")
    print(f"플레이어 공격력: {config.player_power}")
    print(f"연속 공격 횟수: {config.combo_count}")
    print(f"가방: {config.bag}")
    print(f"보상 아이템: {config.reward_item}")
