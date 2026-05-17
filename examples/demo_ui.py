import curses
import os
import sys
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional

# Allow running this example directly from a source checkout.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.player import DefensivePlayer, PublicInfo, RandomPlayer, SimplePlayer
from pyriichi.rules import ActionResult, GameAction, GamePhase, RuleEngine
from pyriichi.rules_config import RenhouPolicy, RulesetConfig
from pyriichi.tiles import Suit, Tile


TEXT = {
    "en": {
        "title": "PyRiichi TUI",
        "language": "Language",
        "difficulty": "AI Difficulty",
        "rules": "Rule Configuration",
        "start": "Start Game",
        "quit": "Quit",
        "back": "Back",
        "easy": "Easy - random AI",
        "normal": "Normal - simple AI",
        "hard": "Hard - defensive AI",
        "help_menu": "Up/Down: move  Enter: select  q: quit",
        "help_game": "Arrows: move  Enter: select  q: quit",
        "select_action": "Select action",
        "select_tile": "Select tile",
        "select_sequence": "Select chi sequence",
        "round": "Round",
        "table": "Table",
        "dealer": "Dealer",
        "honba": "Honba",
        "kyoutaku": "Deposit",
        "wall": "Wall",
        "dora": "Dora indicators",
        "scores": "Scores",
        "hand": "Hand",
        "melds": "Melds",
        "discards": "Discards",
        "last": "Log",
        "winner": "Winner",
        "win_type": "Win",
        "deal_in": "Deal-in",
        "ryuukyoku": "Ryuukyoku",
        "round_result": "Round Result",
        "total_han": "Total Han",
        "payment": "Payment",
        "dora_bonus": "Dora/bonus",
        "all_pay": "all pay",
        "dealer_pays": "dealer pays",
        "others_pay": "others pay",
        "pays": "pays",
        "yakuman": "yakuman",
        "chombo": "Chombo",
        "next_round": "Press Enter for next round, or q to quit.",
        "game_over": "Game ended. Press any key.",
        "invalid": "Invalid action",
        "none": "None",
        "yes": "on",
        "no": "off",
    },
    "ja": {
        "title": "PyRiichi TUI",
        "language": "言語",
        "difficulty": "AI 難易度",
        "rules": "ルール設定",
        "start": "対局開始",
        "quit": "終了",
        "back": "戻る",
        "easy": "易しい - ランダムAI",
        "normal": "普通 - シンプルAI",
        "hard": "難しい - 守備AI",
        "help_menu": "上下: 移動  Enter: 決定  q: 終了",
        "help_game": "左右/上下: 移動  Enter: 決定  q: 終了",
        "select_action": "行動を選択",
        "select_tile": "牌を選択",
        "select_sequence": "チーの順子を選択",
        "round": "局",
        "table": "卓",
        "dealer": "親",
        "honba": "本場",
        "kyoutaku": "供託",
        "wall": "山",
        "dora": "ドラ表示牌",
        "scores": "点数",
        "hand": "手牌",
        "melds": "副露",
        "discards": "河",
        "last": "ログ",
        "winner": "和了",
        "win_type": "和了",
        "deal_in": "放銃",
        "ryuukyoku": "流局",
        "round_result": "局結果",
        "total_han": "合計翻",
        "payment": "支払い",
        "dora_bonus": "ドラ等",
        "all_pay": "全員支払い",
        "dealer_pays": "親支払い",
        "others_pay": "子支払い",
        "pays": "支払い",
        "yakuman": "役満",
        "chombo": "チョンボ",
        "next_round": "Enterで次局、qで終了。",
        "game_over": "対局終了。何かキーを押してください。",
        "invalid": "不正な操作",
        "none": "なし",
        "yes": "有効",
        "no": "無効",
    },
    "zh": {
        "title": "PyRiichi TUI",
        "language": "語言",
        "difficulty": "AI 難度",
        "rules": "規則設定",
        "start": "開始遊戲",
        "quit": "離開",
        "back": "返回",
        "easy": "簡單 - 隨機AI",
        "normal": "普通 - 簡單AI",
        "hard": "困難 - 防守AI",
        "help_menu": "上下: 移動  Enter: 選擇  q: 離開",
        "help_game": "方向鍵: 移動  Enter: 選擇  q: 離開",
        "select_action": "選擇動作",
        "select_tile": "選擇牌",
        "select_sequence": "選擇吃牌順子",
        "round": "局",
        "table": "牌桌",
        "dealer": "莊家",
        "honba": "本場",
        "kyoutaku": "供託",
        "wall": "牌山",
        "dora": "寶牌指示牌",
        "scores": "點數",
        "hand": "手牌",
        "melds": "副露",
        "discards": "河",
        "last": "紀錄",
        "winner": "和牌",
        "win_type": "和牌",
        "deal_in": "放銃",
        "ryuukyoku": "流局",
        "round_result": "本局結果",
        "total_han": "總翻",
        "payment": "支付",
        "dora_bonus": "寶牌等",
        "all_pay": "全員支付",
        "dealer_pays": "莊家支付",
        "others_pay": "閒家支付",
        "pays": "支付",
        "yakuman": "役滿",
        "chombo": "錯和",
        "next_round": "按 Enter 進入下一局，或 q 離開。",
        "game_over": "遊戲結束。按任意鍵。",
        "invalid": "無效動作",
        "none": "無",
        "yes": "開",
        "no": "關",
    },
}


DIFFICULTIES = {
    "easy": RandomPlayer,
    "normal": SimplePlayer,
    "hard": DefensivePlayer,
}

KANJI_NUMERALS = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
}

KANJI_SUITS = {
    Suit.MANZU: "萬",
    Suit.PINZU: "筒",
    Suit.SOUZU: "索",
}

KANJI_HONORS = {
    1: "東",
    2: "南",
    3: "西",
    4: "北",
    5: "白",
    6: "発",
    7: "中",
}

BACK_TILE = "伏"

COLOR_MANZU = 1
COLOR_PINZU = 2
COLOR_SOUZU = 3
COLOR_HONORS = 4
COLOR_BORDER = 6
COLOR_DIM = 7
COLOR_ALERT = 8
COLOR_ACTION_CHI = 9
COLOR_ACTION_PON = 10
COLOR_ACTION_KAN = 11
COLOR_ACTION_WIN = 12
COLOR_ACTION_RIICHI = 13
COLOR_ACTION_PASS = 14
ACTION_POPUP_MS = 1600


@dataclass
class Settings:
    language: str = "en"
    difficulty: str = "normal"
    ruleset: RulesetConfig = None

    def __post_init__(self):
        if self.ruleset is None:
            self.ruleset = RulesetConfig.standard()


@dataclass
class ActionOption:
    action: GameAction
    tile: Optional[Tile] = None
    sequence: Optional[List[Tile]] = None
    meld_tiles: Optional[List[Tile]] = None
    called_tile: Optional[Tile] = None
    called_from: Optional[int] = None


class Tui:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.settings = Settings()
        self.engine: Optional[RuleEngine] = None
        self.players = []
        self.status = ""
        self.running = True
        self.has_colors = False
        self.active_actions: List[GameAction] = []
        self.selected_action_index: Optional[int] = None
        self.active_sequences: List[List[Tile]] = []
        self.selected_sequence_index: Optional[int] = None
        self.active_options: List[ActionOption] = []
        self.selected_option_index: Optional[int] = None
        self.selected_tile_index: Optional[int] = None
        self.selection_tiles: Optional[List[Tile]] = None
        self.last_round_result: Optional[ActionResult] = None
        self.last_winners: List[int] = []

    def t(self, key: str) -> str:
        return TEXT[self.settings.language][key]

    def tile_text(self, tile: Optional[Tile]) -> str:
        if tile is None:
            return self.t("none")
        return self.tile_glyph(tile)

    def tile_glyph(self, tile: Optional[Tile], hidden: bool = False) -> str:
        if hidden or tile is None:
            return BACK_TILE
        if tile.suit == Suit.HONORS:
            return KANJI_HONORS[tile.rank]
        return f"{KANJI_NUMERALS[tile.rank]}{KANJI_SUITS[tile.suit]}"

    def tile_label(
        self, tile: Optional[Tile], hidden: bool = False, mark_dora: bool = True
    ) -> str:
        glyph = self.tile_glyph(tile, hidden)
        if hidden:
            return f"[{glyph}]"
        if tile and tile.is_red_dora:
            return f"[[紅{glyph}]]"
        if (
            mark_dora
            and tile
            and self.engine
            and self.engine.is_revealed_dora_tile(tile)
        ):
            return f"[[{glyph}]]"
        return f"[{glyph}]"

    def action_text(self, action: GameAction) -> str:
        return getattr(action, self.settings.language)

    def set_status(self, message: str) -> None:
        self.status = message

    def safe_addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        height, width = self.stdscr.getmaxyx()
        if y < 0 or y >= height or x >= width:
            return
        text = self.truncate_display(text, max(0, width - x - 1))
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    @staticmethod
    def char_width(char: str) -> int:
        if unicodedata.combining(char):
            return 0
        return 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1

    @classmethod
    def display_width(cls, text: str) -> int:
        return sum(cls.char_width(char) for char in text)

    @classmethod
    def truncate_display(cls, text: str, max_width: int) -> str:
        if max_width <= 0:
            return ""

        width = 0
        chars = []
        for char in text:
            char_width = cls.char_width(char)
            if width + char_width > max_width:
                break
            chars.append(char)
            width += char_width
        return "".join(chars)

    def add_centered(
        self, y: int, x: int, width: int, text: str, attr: int = 0
    ) -> None:
        text_width = self.display_width(text)
        offset = max(0, (width - text_width) // 2)
        self.safe_addstr(y, x + offset, text, attr)

    def run(self) -> None:
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.stdscr.keypad(True)
        self.setup_colors()
        self.main_menu()

    def setup_colors(self) -> None:
        self.has_colors = curses.has_colors()
        if not self.has_colors:
            return
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(COLOR_MANZU, curses.COLOR_RED, -1)
        curses.init_pair(COLOR_PINZU, curses.COLOR_CYAN, -1)
        curses.init_pair(COLOR_SOUZU, curses.COLOR_GREEN, -1)
        curses.init_pair(COLOR_HONORS, curses.COLOR_YELLOW, -1)
        curses.init_pair(COLOR_BORDER, curses.COLOR_GREEN, -1)
        curses.init_pair(COLOR_DIM, curses.COLOR_BLUE, -1)
        curses.init_pair(COLOR_ALERT, curses.COLOR_MAGENTA, -1)
        curses.init_pair(COLOR_ACTION_CHI, curses.COLOR_CYAN, -1)
        curses.init_pair(COLOR_ACTION_PON, curses.COLOR_YELLOW, -1)
        curses.init_pair(COLOR_ACTION_KAN, curses.COLOR_MAGENTA, -1)
        curses.init_pair(COLOR_ACTION_WIN, curses.COLOR_RED, -1)
        curses.init_pair(COLOR_ACTION_RIICHI, curses.COLOR_GREEN, -1)
        curses.init_pair(COLOR_ACTION_PASS, curses.COLOR_BLUE, -1)

    def color(self, color_pair: int, extra: int = 0) -> int:
        if not self.has_colors:
            return extra
        return curses.color_pair(color_pair) | extra

    def tile_attr(
        self, tile: Optional[Tile], hidden: bool = False, *, bold: bool = True
    ) -> int:
        extra = curses.A_BOLD if bold else 0
        if hidden or tile is None:
            return self.color(COLOR_DIM, extra)
        if tile.suit == Suit.MANZU:
            return self.color(COLOR_MANZU, extra)
        if tile.suit == Suit.PINZU:
            return self.color(COLOR_PINZU, extra)
        if tile.suit == Suit.SOUZU:
            return self.color(COLOR_SOUZU, extra)
        return self.color(COLOR_HONORS, extra)

    def main_menu(self) -> None:
        while self.running:
            options = [
                (self.t("start"), self.play_game),
                (self.t("language"), self.configure_language),
                (self.t("difficulty"), self.configure_difficulty),
                (self.t("rules"), self.configure_rules),
                (self.t("quit"), self.stop),
            ]
            choice = self.choose(self.t("title"), [label for label, _ in options])
            if choice is None:
                self.stop()
                return
            options[choice][1]()

    def stop(self) -> None:
        self.running = False

    def choose(
        self, title: str, options: List[str], selected: int = 0
    ) -> Optional[int]:
        if not options:
            return None
        index = max(0, min(selected, len(options) - 1))
        while True:
            overlay = (
                self.engine is not None and self.engine.get_phase() == GamePhase.PLAYING
            )
            if overlay:
                self.render()
                height, width = self.stdscr.getmaxyx()
                box_width = min(46, max(30, width - 8))
                box_height = min(len(options) + 5, max(8, height - 4))
                y = max(2, (height - box_height) // 2)
                x = max(2, (width - box_width) // 2)
                self.draw_box(y, x, box_height, box_width, title)
                help_y = y + 1
                option_y = y + 3
                option_x = x + 3
            else:
                self.stdscr.erase()
                self.safe_addstr(0, 2, title, curses.A_BOLD)
                help_y = 2
                option_y = 4
                option_x = 4

            self.safe_addstr(help_y, option_x, self.t("help_menu"), curses.A_DIM)
            for i, option in enumerate(options):
                prefix = "> " if i == index else "  "
                attr = curses.A_REVERSE if i == index else 0
                self.safe_addstr(option_y + i, option_x, f"{prefix}{option}", attr)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (ord("q"), 27):
                if overlay:
                    self.stop()
                return None
            if key in (curses.KEY_UP, ord("k")):
                index = (index - 1) % len(options)
            elif key in (curses.KEY_DOWN, ord("j")):
                index = (index + 1) % len(options)
            elif key in (curses.KEY_ENTER, 10, 13):
                return index

    def configure_language(self) -> None:
        languages = [("en", "English"), ("ja", "日本語"), ("zh", "繁體中文")]
        current = next(
            i for i, (code, _) in enumerate(languages) if code == self.settings.language
        )
        choice = self.choose(
            self.t("language"), [label for _, label in languages], current
        )
        if choice is not None:
            self.settings.language = languages[choice][0]

    def configure_difficulty(self) -> None:
        keys = ["easy", "normal", "hard"]
        current = keys.index(self.settings.difficulty)
        labels = [self.t(key) for key in keys]
        choice = self.choose(self.t("difficulty"), labels, current)
        if choice is not None:
            self.settings.difficulty = keys[choice]

    def configure_rules(self) -> None:
        while True:
            ruleset = self.settings.ruleset
            ron_mode = self.ron_mode_label(ruleset)
            options = [
                f"Renhou: {ruleset.renhou_policy.value}",
                f"Open Tanyao: {self.on_off(ruleset.open_tanyao_enabled)}",
                f"Pinfu ryanmen: {self.on_off(ruleset.pinfu_require_ryanmen)}",
                f"Ippatsu interruption: {self.on_off(ruleset.ippatsu_interrupt_on_meld_or_kan)}",
                f"Abortive draw dealer continuation: {self.on_off(ruleset.abortive_draw_dealer_continues)}",
                f"Kiriage Mangan: {self.on_off(ruleset.kiriage_mangan)}",
                f"Tobi: {self.on_off(ruleset.tobi_enabled)}",
                f"West round extension: {self.on_off(ruleset.west_round_extension)}",
                f"Agari Yame: {self.on_off(ruleset.agari_yame)}",
                f"Chombo penalty: {self.on_off(ruleset.chombo_penalty_enabled)}",
                f"Multiple ron: {ron_mode}",
                f"Double yakuman variants: {self.on_off(self.double_yakuman_enabled(ruleset))}",
                f"Return score: {ruleset.return_score}",
                self.t("back"),
            ]
            choice = self.choose(self.t("rules"), options)
            if choice is None or choice == len(options) - 1:
                return
            if choice == 0:
                values = list(RenhouPolicy)
                ruleset.renhou_policy = values[
                    (values.index(ruleset.renhou_policy) + 1) % len(values)
                ]
            elif choice == 1:
                ruleset.open_tanyao_enabled = not ruleset.open_tanyao_enabled
            elif choice == 2:
                ruleset.pinfu_require_ryanmen = not ruleset.pinfu_require_ryanmen
            elif choice == 3:
                ruleset.ippatsu_interrupt_on_meld_or_kan = (
                    not ruleset.ippatsu_interrupt_on_meld_or_kan
                )
            elif choice == 4:
                ruleset.abortive_draw_dealer_continues = (
                    not ruleset.abortive_draw_dealer_continues
                )
            elif choice == 5:
                ruleset.kiriage_mangan = not ruleset.kiriage_mangan
            elif choice == 6:
                ruleset.tobi_enabled = not ruleset.tobi_enabled
            elif choice == 7:
                ruleset.west_round_extension = not ruleset.west_round_extension
            elif choice == 8:
                ruleset.agari_yame = not ruleset.agari_yame
            elif choice == 9:
                ruleset.chombo_penalty_enabled = not ruleset.chombo_penalty_enabled
            elif choice == 10:
                self.cycle_ron_mode(ruleset)
            elif choice == 11:
                enabled = not self.double_yakuman_enabled(ruleset)
                ruleset.suuankou_tanki_double = enabled
                ruleset.kokushi_musou_juusanmen_double = enabled
                ruleset.pure_chuuren_poutou_double = enabled
            elif choice == 12:
                ruleset.return_score = 25000 if ruleset.return_score == 30000 else 30000

    def on_off(self, value: bool) -> str:
        return self.t("yes") if value else self.t("no")

    @staticmethod
    def double_yakuman_enabled(ruleset: RulesetConfig) -> bool:
        return (
            ruleset.suuankou_tanki_double
            and ruleset.kokushi_musou_juusanmen_double
            and ruleset.pure_chuuren_poutou_double
        )

    @staticmethod
    def ron_mode_label(ruleset: RulesetConfig) -> str:
        if ruleset.head_bump_only:
            return "head_bump"
        if ruleset.allow_triple_ron:
            return "triple_ron"
        if ruleset.allow_double_ron:
            return "double_ron"
        return "single_ron"

    @staticmethod
    def cycle_ron_mode(ruleset: RulesetConfig) -> None:
        modes = ["head_bump", "double_ron", "triple_ron"]
        current = Tui.ron_mode_label(ruleset)
        next_mode = (
            modes[(modes.index(current) + 1) % len(modes)]
            if current in modes
            else modes[0]
        )
        ruleset.head_bump_only = next_mode == "head_bump"
        ruleset.allow_double_ron = next_mode in {"double_ron", "triple_ron"}
        ruleset.allow_triple_ron = next_mode == "triple_ron"

    def play_game(self) -> None:
        self.engine = RuleEngine(num_players=4)
        self.engine.start_game()
        self.engine.game_state._ruleset = self.settings.ruleset
        ai_cls = DIFFICULTIES[self.settings.difficulty]
        self.players = [None] + [ai_cls(f"CPU {i}") for i in range(1, 4)]
        self.status = ""
        self.active_actions = []
        self.selected_action_index = None
        self.active_sequences = []
        self.selected_sequence_index = None
        self.active_options = []
        self.selected_option_index = None
        self.selected_tile_index = None
        self.last_round_result = None
        self.last_winners = []
        self.start_next_round()

        while self.running and self.engine.get_phase() != GamePhase.ENDED:
            if self.engine.get_phase() in {GamePhase.WINNING, GamePhase.RYUUKYOKU}:
                if not self.end_round_prompt():
                    return
                continue

            if self.engine.get_phase() != GamePhase.PLAYING:
                break

            if not self.engine.waiting_for_actions:
                ryuukyoku = self.engine.handle_ryuukyoku()
                if ryuukyoku.ryuukyoku:
                    self.last_round_result = ActionResult(ryuukyoku=ryuukyoku)
                    self.set_status(self.ryuukyoku_text(ryuukyoku.ryuukyoku_type))
                    continue
                break

            player = next(iter(self.engine.waiting_for_actions))
            if player == 0:
                result = self.human_turn(player)
            else:
                result = self.ai_turn(player)

            if result is not None:
                self.process_result(result)

        if not self.running:
            return

        self.render()
        self.safe_addstr(1, 2, self.t("game_over"), curses.A_BOLD)
        self.stdscr.getch()

    def start_next_round(self) -> None:
        assert self.engine is not None
        self.last_round_result = None
        self.last_winners = []
        self.engine.start_round()
        self.engine.deal()
        state = self.engine.game_state
        self.set_status(
            f"{getattr(state.round_wind, self.settings.language)} {state.round_number} - "
            f"{self.t('dealer')} P{state.dealer}"
        )

    def end_round_prompt(self) -> bool:
        assert self.engine is not None
        self.render()
        self.draw_round_summary()
        self.stdscr.refresh()
        while True:
            key = self.stdscr.getch()
            if key == ord("q"):
                self.stop()
                return False
            if key in (curses.KEY_ENTER, 10, 13):
                if self.engine.get_phase() == GamePhase.WINNING:
                    winners = list(getattr(self, "last_winners", []))
                    self.engine.end_round(winners)
                if self.engine.get_phase() != GamePhase.ENDED:
                    self.start_next_round()
                return True

    def human_turn(self, player: int) -> Optional[ActionResult]:
        assert self.engine is not None
        actions = self.engine.get_available_actions(player)
        if actions == [GameAction.DISCARD]:
            tile = self.choose_tile_from_hand(player, GameAction.DISCARD, actions)
            if tile is None:
                return None
            return self.execute_human_action(player, GameAction.DISCARD, tile)

        return self.choose_turn_option(player, actions)

    def execute_human_action(
        self,
        player: int,
        action: GameAction,
        tile: Optional[Tile] = None,
        **kwargs,
    ) -> Optional[ActionResult]:
        assert self.engine is not None
        try:
            result = self.engine.execute_action(player, action, tile, **kwargs)
            self.set_status(f"P{player}: {self.action_text(action)}")
            if result.riichi:
                self.show_action_popup(player, GameAction.DECLARE_RIICHI, tile)
            return result
        except ValueError as exc:
            self.set_status(f"{self.t('invalid')}: {exc}")
            return None

    def choose_turn_option(
        self, player: int, actions: List[GameAction]
    ) -> Optional[ActionResult]:
        assert self.engine is not None
        hand = self.engine.get_hand(player)
        discard_tiles = []
        if GameAction.DISCARD in actions:
            discard_tiles = self.sorted_tiles_for_display(
                hand.tiles, hand.last_drawn_tile
            )

        self.active_actions = actions
        self.active_options = self.build_action_options(player, actions)
        self.selection_tiles = discard_tiles or None
        tile_index = self.default_tile_selection_index(
            discard_tiles, hand.last_drawn_tile
        )
        selected_index = 0
        if not self.active_options and discard_tiles:
            selected_index = tile_index
        total_options = len(self.active_options) + len(discard_tiles)
        if total_options == 0:
            self.clear_selection()
            return None

        self.set_status(self.t("select_action"))

        def sync_selection() -> None:
            if selected_index < len(self.active_options):
                self.selected_option_index = selected_index
                self.selected_tile_index = None
            else:
                self.selected_option_index = None
                self.selected_tile_index = selected_index - len(self.active_options)

        sync_selection()
        while True:
            self.render()
            key = self.stdscr.getch()
            if key in (ord("q"), 27):
                self.stop()
                self.clear_selection()
                return None
            if key in (curses.KEY_LEFT, ord("h")):
                selected_index = (selected_index - 1) % total_options
                sync_selection()
            elif key in (curses.KEY_RIGHT, ord("l")):
                selected_index = (selected_index + 1) % total_options
                sync_selection()
            elif key in (curses.KEY_UP, ord("k")):
                if discard_tiles and selected_index >= len(self.active_options):
                    selected_index = 0
                    sync_selection()
            elif key in (curses.KEY_DOWN, ord("j")):
                if discard_tiles and selected_index < len(self.active_options):
                    selected_index = len(self.active_options) + tile_index
                    sync_selection()
            elif ord("1") <= key <= ord("9") and discard_tiles:
                index = key - ord("1")
                if index < len(discard_tiles):
                    tile = discard_tiles[index]
                    self.clear_selection()
                    return self.execute_human_action(player, GameAction.DISCARD, tile)
            elif key in (curses.KEY_ENTER, 10, 13):
                if selected_index < len(self.active_options):
                    option = self.active_options[selected_index]
                    self.clear_selection()
                    return self.execute_action_option(player, option, actions)

                tile = discard_tiles[selected_index - len(self.active_options)]
                self.clear_selection()
                return self.execute_human_action(player, GameAction.DISCARD, tile)

    def execute_action_option(
        self, player: int, option: ActionOption, actions: List[GameAction]
    ) -> Optional[ActionResult]:
        kwargs = {}
        if option.sequence is not None:
            kwargs["sequence"] = option.sequence
        if option.action == GameAction.DECLARE_RIICHI:
            tile = self.choose_tile_from_hand(player, option.action, actions)
            if tile is None:
                return None
            return self.execute_human_action(player, option.action, tile)
        return self.execute_human_action(player, option.action, option.tile, **kwargs)

    def build_action_options(
        self, player: int, actions: List[GameAction]
    ) -> List[ActionOption]:
        assert self.engine is not None
        options = []
        last_discard = self.engine.get_last_discard()
        last_discard_player = self.engine.get_last_discard_player()
        hand = self.engine.get_hand(player)

        for action in actions:
            if action == GameAction.DISCARD:
                continue
            if action == GameAction.CHI and last_discard is not None:
                for sequence in self.engine.get_available_chi_sequences(player):
                    meld_tiles = sorted(sequence + [last_discard])
                    options.append(
                        ActionOption(
                            action=action,
                            tile=last_discard,
                            sequence=sequence,
                            meld_tiles=meld_tiles,
                            called_tile=last_discard,
                            called_from=last_discard_player,
                        )
                    )
            elif action == GameAction.PON and last_discard is not None:
                hand_tiles = [tile for tile in hand.tiles if tile == last_discard][:2]
                options.append(
                    ActionOption(
                        action=action,
                        tile=last_discard,
                        meld_tiles=sorted(hand_tiles + [last_discard]),
                        called_tile=last_discard,
                        called_from=last_discard_player,
                    )
                )
            elif action in {GameAction.KAN, GameAction.DECLARE_ANKAN}:
                options.extend(self.build_kan_options(player, action))
            else:
                options.append(ActionOption(action=action, tile=last_discard))
        return options

    def build_kan_options(
        self, player: int, action: GameAction
    ) -> List[ActionOption]:
        assert self.engine is not None
        hand = self.engine.get_hand(player)
        last_discard = self.engine.get_last_discard()
        options = []

        if action == GameAction.KAN:
            if player != self.engine.get_current_player() and last_discard is not None:
                candidates = hand.can_kan(last_discard)
            else:
                candidates = [
                    meld
                    for meld in hand.can_kan(None)
                    if meld.type == MeldType.OPEN_KAN and meld.called_tile is not None
                ]
        else:
            candidates = [
                meld for meld in hand.can_kan(None) if meld.type == MeldType.CLOSED_KAN
            ]

        for meld in candidates:
            tile = meld.called_tile or (meld.tiles[0] if meld.tiles else None)
            options.append(
                ActionOption(
                    action=action,
                    tile=tile,
                    meld_tiles=meld.tiles,
                    called_tile=meld.called_tile,
                    called_from=self.engine.get_last_discard_player()
                    if action == GameAction.KAN
                    and player != self.engine.get_current_player()
                    else None,
                )
            )
        return options

    def choose_action(self, actions: List[GameAction]) -> Optional[GameAction]:
        self.active_actions = actions
        self.selected_action_index = 0
        self.set_status(self.t("select_action"))

        while True:
            self.render()
            key = self.stdscr.getch()
            if key in (ord("q"), 27):
                self.stop()
                self.clear_selection()
                return None
            if key in (curses.KEY_LEFT, curses.KEY_UP, ord("h"), ord("k")):
                self.selected_action_index = max(
                    0, (self.selected_action_index or 0) - 1
                )
            elif key in (curses.KEY_RIGHT, curses.KEY_DOWN, ord("l"), ord("j")):
                self.selected_action_index = min(
                    len(actions) - 1, (self.selected_action_index or 0) + 1
                )
            elif key in (curses.KEY_ENTER, 10, 13):
                action = actions[self.selected_action_index or 0]
                self.clear_selection()
                return action

    @staticmethod
    def sorted_tiles_for_display(
        tiles: List[Tile], incoming_tile: Optional[Tile] = None
    ) -> List[Tile]:
        display_tiles = list(tiles)
        pinned_tile = None
        if incoming_tile is not None:
            for index, tile in enumerate(display_tiles):
                if tile is incoming_tile:
                    pinned_tile = display_tiles.pop(index)
                    break
            if pinned_tile is None:
                for index, tile in enumerate(display_tiles):
                    if (
                        tile.suit == incoming_tile.suit
                        and tile.rank == incoming_tile.rank
                        and tile.is_red_dora == incoming_tile.is_red_dora
                    ):
                        pinned_tile = display_tiles.pop(index)
                        break

        display_tiles.sort()
        if pinned_tile is not None:
            display_tiles.append(pinned_tile)
        return display_tiles

    @classmethod
    def sorted_hand_tiles(cls, hand: Hand) -> List[Tile]:
        return cls.sorted_tiles_for_display(hand.tiles, hand.last_drawn_tile)

    def clear_selection(self) -> None:
        self.active_actions = []
        self.selected_action_index = None
        self.active_sequences = []
        self.selected_sequence_index = None
        self.active_options = []
        self.selected_option_index = None
        self.selected_tile_index = None
        self.selection_tiles = None

    def choose_tile_from_hand(
        self,
        player: int,
        action: GameAction,
        actions: Optional[List[GameAction]] = None,
    ) -> Optional[Tile]:
        assert self.engine is not None
        hand = self.engine.get_hand(player)
        candidates = (
            hand.tenpai_discards if action == GameAction.DECLARE_RIICHI else hand.tiles
        )
        if not candidates:
            candidates = hand.tiles
        candidates = self.sorted_tiles_for_display(candidates, hand.last_drawn_tile)
        self.active_actions = actions or [action]
        self.selection_tiles = candidates
        candidate_index = self.default_tile_selection_index(
            candidates, hand.last_drawn_tile
        )
        self.selected_tile_index = candidate_index
        self.set_status(self.t("select_tile"))

        while True:
            self.render()
            key = self.stdscr.getch()
            if key in (ord("q"), 27):
                self.stop()
                self.clear_selection()
                return None
            if key in (curses.KEY_LEFT, ord("h")):
                candidate_index = (candidate_index - 1) % len(candidates)
                self.selected_tile_index = candidate_index
            elif key in (curses.KEY_RIGHT, ord("l")):
                candidate_index = (candidate_index + 1) % len(candidates)
                self.selected_tile_index = candidate_index
            elif ord("1") <= key <= ord("9"):
                index = key - ord("1")
                if index < len(candidates):
                    candidate_index = index
                    self.selected_tile_index = candidate_index
                    tile = candidates[index]
                    self.clear_selection()
                    return tile
            elif key in (curses.KEY_ENTER, 10, 13):
                tile = candidates[candidate_index]
                self.clear_selection()
                return tile

    def choose_kan_tile(self, player: int, action: GameAction) -> Optional[Tile]:
        assert self.engine is not None
        if (
            action == GameAction.KAN
            and player != self.engine.get_current_player()
            and self.engine.get_last_discard() is not None
        ):
            return self.engine.get_last_discard()

        candidates = self.engine.get_hand(player).can_kan(None)
        if action == GameAction.KAN:
            candidates = [
                meld
                for meld in candidates
                if meld.type == MeldType.OPEN_KAN and meld.called_tile is not None
            ]
        elif action == GameAction.DECLARE_ANKAN:
            candidates = [
                meld for meld in candidates if meld.type == MeldType.CLOSED_KAN
            ]
        if not candidates:
            return None
        labels = [self.tiles_text(meld.tiles) for meld in candidates]
        choice = self.choose(self.t("select_tile"), labels)
        if choice is None:
            return None
        return candidates[choice].called_tile or candidates[choice].tiles[0]

    def choose_chi_sequence(self, player: int) -> Optional[List[Tile]]:
        assert self.engine is not None
        sequences = self.engine.get_available_chi_sequences(player)
        if not sequences:
            return None
        self.active_sequences = sequences
        self.selected_sequence_index = 0
        self.set_status(self.t("select_sequence"))

        while True:
            self.render()
            key = self.stdscr.getch()
            if key in (ord("q"), 27):
                self.stop()
                self.clear_selection()
                return None
            if key in (curses.KEY_LEFT, curses.KEY_UP, ord("h"), ord("k")):
                self.selected_sequence_index = max(
                    0, (self.selected_sequence_index or 0) - 1
                )
            elif key in (curses.KEY_RIGHT, curses.KEY_DOWN, ord("l"), ord("j")):
                self.selected_sequence_index = min(
                    len(sequences) - 1, (self.selected_sequence_index or 0) + 1
                )
            elif key in (curses.KEY_ENTER, 10, 13):
                sequence = sequences[self.selected_sequence_index or 0]
                self.clear_selection()
                return sequence

    def ai_turn(self, player: int) -> Optional[ActionResult]:
        assert self.engine is not None
        actions = self.engine.get_available_actions(player)
        ai = self.players[player]
        public_info = self.build_public_info()
        action, tile = ai.decide_action(
            self.engine.game_state,
            player,
            self.engine.get_hand(player),
            actions,
            public_info,
        )
        try:
            result = self.engine.execute_action(player, action, tile)
        except ValueError:
            if GameAction.PASS in actions:
                action, tile = GameAction.PASS, None
                result = self.engine.execute_action(player, action, tile)
            elif GameAction.DISCARD in actions:
                action = GameAction.DISCARD
                tile = self.engine.get_hand(player).tiles[0]
                result = self.engine.execute_action(player, action, tile)
            else:
                raise
        self.set_status(f"P{player}: {self.action_text(action)}")
        if result.riichi:
            self.show_action_popup(player, GameAction.DECLARE_RIICHI, tile)
        return result

    def build_public_info(self) -> PublicInfo:
        assert self.engine is not None
        return PublicInfo(
            turn_number=sum(len(self.engine.get_discards(i)) for i in range(4)),
            dora_indicators=self.engine.get_revealed_dora_indicators(),
            discards={i: self.engine.get_discards(i) for i in range(4)},
            melds={i: self.engine.get_hand(i).melds for i in range(4)},
            riichi_players=[i for i in range(4) if self.engine.get_hand(i).is_riichi],
            scores=self.engine.game_state.scores,
        )

    def process_result(self, result: ActionResult) -> None:
        assert self.engine is not None
        self.show_result_action_popup(result)
        if result.chombo:
            self.set_status(f"{self.t('chombo')}: P{result.chombo_player}")
        if result.rinshan_win:
            result.winners = [result.rinshan_win.player]
            result.win_results[result.rinshan_win.player] = result.rinshan_win
        if result.winners:
            self.last_round_result = result
            self.last_winners = result.winners
            self.set_status(
                f"{self.t('winner')}: {', '.join(f'P{p}' for p in result.winners)}"
            )
        if result.ryuukyoku:
            if (
                result.ryuukyoku.ryuukyoku_type
                and result.ryuukyoku.ryuukyoku_type.value == "exhaustive_draw"
            ):
                result.ryuukyoku = self.engine.handle_ryuukyoku()
            self.last_round_result = result
            self.set_status(self.ryuukyoku_text(result.ryuukyoku.ryuukyoku_type))
        elif self.engine.get_phase() == GamePhase.PLAYING:
            ryuukyoku_type = self.engine.check_ryuukyoku()
            if ryuukyoku_type:
                ryuukyoku = self.engine.handle_ryuukyoku()
                self.last_round_result = ActionResult(ryuukyoku=ryuukyoku)
                self.set_status(self.ryuukyoku_text(ryuukyoku.ryuukyoku_type))

    def ryuukyoku_text(self, ryuukyoku_type) -> str:
        if ryuukyoku_type is None:
            return self.t("ryuukyoku")
        return (
            f"{self.t('ryuukyoku')}: {getattr(ryuukyoku_type, self.settings.language)}"
        )

    def round_summary_lines(self) -> List[str]:
        assert self.engine is not None
        result = self.last_round_result
        if result is None:
            return [self.status or self.t("round_result")]
        if result.ryuukyoku:
            return [self.t("ryuukyoku")]

        lines = []
        for winner in result.winners:
            win_result = result.win_results.get(winner)
            if win_result is None:
                continue
            lines.append(f"{self.t('winner')}: P{winner}")
            lines.append(self.win_source_summary_text(win_result))
            lines.append(
                f"{self.t('hand')}: {self.tiles_text(self.win_hand_tiles(winner, win_result))}"
            )
            melds = self.engine.get_hand(winner).melds
            if melds:
                lines.append(
                    f"{self.t('melds')}: {self.melds_text(melds, owner=winner)}"
                )
            for yaku_result in win_result.yaku:
                lines.append(f"  {self.yaku_summary_text(yaku_result)}")
            listed_han = sum(yaku_result.han for yaku_result in win_result.yaku)
            bonus_han = max(0, win_result.han - listed_han)
            if bonus_han:
                lines.append(f"  {self.t('dora_bonus')}: {bonus_han} han")
            lines.append(
                f"{self.t('total_han')}: {win_result.han} han / {win_result.fu} fu"
            )
            lines.append(
                f"{self.t('payment')}: {self.payment_summary_text(win_result)}"
            )
            lines.append("")
        return lines[:-1] if lines and lines[-1] == "" else lines

    def win_hand_tiles(self, winner: int, win_result) -> List[Tile]:
        assert self.engine is not None
        hand = self.engine.get_hand(winner)
        tiles = list(hand.tiles)
        score_result = getattr(win_result, "score_result", None)
        is_tsumo = bool(getattr(score_result, "is_tsumo", False))
        winning_tile = (
            hand.last_drawn_tile if is_tsumo else self.engine.get_last_discard()
        )
        if winning_tile is not None and all(tile is not winning_tile for tile in tiles):
            tiles.append(winning_tile)
        return self.sorted_tiles_for_display(tiles, winning_tile)

    @staticmethod
    def default_tile_selection_index(
        tiles: List[Tile], incoming_tile: Optional[Tile]
    ) -> int:
        index = Tui.incoming_tile_index(tiles, incoming_tile)
        return 0 if index is None else index

    @staticmethod
    def incoming_tile_index(
        tiles: List[Tile], incoming_tile: Optional[Tile]
    ) -> Optional[int]:
        if not tiles or incoming_tile is None:
            return None
        for index, tile in enumerate(tiles):
            if tile is incoming_tile:
                return index
        for index, tile in enumerate(tiles):
            if tile == incoming_tile:
                return index
        return None

    def yaku_summary_text(self, yaku_result) -> str:
        name = getattr(yaku_result.yaku, self.settings.language)
        suffix = self.t("yakuman") if yaku_result.is_yakuman else "han"
        return f"{name}: {yaku_result.han} {suffix}"

    def win_source_summary_text(self, win_result) -> str:
        score = win_result.score_result
        if score.is_tsumo:
            return f"{self.t('win_type')}: {self.action_text(GameAction.TSUMO)}"
        return (
            f"{self.t('win_type')}: {self.action_text(GameAction.RON)} "
            f"({self.t('deal_in')}: P{score.payment_from})"
        )

    def payment_summary_text(self, win_result) -> str:
        score = win_result.score_result
        if score.is_tsumo:
            if score.payment_to == self.engine.game_state.dealer:
                text = f"{self.t('all_pay')} {score.non_dealer_payment}"
            else:
                text = (
                    f"{self.t('dealer_pays')} {score.dealer_payment}; "
                    f"{self.t('others_pay')} {score.non_dealer_payment}"
                )
        else:
            payment = score.total_points - score.riichi_sticks_bonus
            text = f"P{score.payment_from} {self.t('pays')} {payment}"

        if score.riichi_sticks_bonus:
            text = f"{text}; deposit +{score.riichi_sticks_bonus}"
        if score.pao_player is not None and score.pao_payment:
            text = f"{text}; pao P{score.pao_player} {score.pao_payment}"
        return text

    def draw_round_summary(self) -> None:
        height, width = self.stdscr.getmaxyx()
        lines = self.round_summary_lines()
        content_width = max([self.display_width(line) for line in lines] + [0])
        box_width = min(width - 4, max(42, content_width + 4))
        box_height = min(height - 4, max(6, len(lines) + 4))
        if box_width < 10 or box_height < 5:
            return
        y = max(1, (height - box_height) // 2)
        x = max(2, (width - box_width) // 2)
        self.draw_box(y, x, box_height, box_width, self.t("round_result"))
        max_lines = max(0, box_height - 4)
        for index, line in enumerate(lines[:max_lines]):
            self.safe_addstr(y + 1 + index, x + 2, line)
        self.safe_addstr(y + box_height - 2, x + 2, self.t("next_round"), curses.A_BOLD)

    def show_result_action_popup(self, result: ActionResult) -> None:
        assert self.engine is not None
        if result.called_action:
            self.show_action_popup(
                self.engine.get_current_player(),
                result.called_action,
                result.called_tile,
            )
        elif result.kan:
            self.show_action_popup(self.engine.get_current_player(), GameAction.KAN)
        elif result.closed_kan:
            self.show_action_popup(
                self.engine.get_current_player(), GameAction.DECLARE_ANKAN
            )
        elif result.winners:
            for winner in result.winners:
                win_result = result.win_results.get(winner)
                score = getattr(win_result, "score_result", None)
                action = (
                    GameAction.TSUMO
                    if score is not None and score.is_tsumo
                    else GameAction.RON
                )
                self.show_action_popup(winner, action)

    def show_action_popup(
        self, player: int, action: GameAction, tile: Optional[Tile] = None
    ) -> None:
        assert self.engine is not None
        self.render()
        height, width = self.stdscr.getmaxyx()
        title = self.action_text(action)
        state = self.engine.game_state
        wind = getattr(state.seat_winds[player], self.settings.language)
        line = f"P{player} {wind}"
        lines = [line]
        if tile is not None:
            lines.append(self.tile_label(tile))
        content_width = max(self.display_width(line) for line in lines)
        box_width = min(width - 4, max(40, content_width + 16))
        box_height = min(height - 4, max(11, len(lines) + 6))
        y = max(1, (height - box_height) // 2)
        x = max(2, (width - box_width) // 2)
        self.draw_box(y, x, box_height, box_width, title)
        first_line_y = y + max(2, (box_height - len(lines)) // 2)
        for index, popup_line in enumerate(lines):
            self.add_centered(
                first_line_y + index, x + 1, box_width - 2, popup_line, curses.A_BOLD
            )
        self.stdscr.refresh()
        curses.napms(ACTION_POPUP_MS)

    def draw_box(
        self, y: int, x: int, height: int, width: int, title: str = ""
    ) -> None:
        if height < 2 or width < 2:
            return
        attr = self.color(COLOR_BORDER)
        horizontal = "─" * max(0, width - 2)
        self.safe_addstr(y, x, f"┌{horizontal}┐", attr)
        fill = " " * max(0, width - 2)
        for row in range(1, height - 1):
            self.safe_addstr(y + row, x, "│", attr)
            self.safe_addstr(y + row, x + 1, fill)
            self.safe_addstr(y + row, x + width - 1, "│", attr)
        self.safe_addstr(y + height - 1, x, f"└{horizontal}┘", attr)
        if title:
            self.safe_addstr(y, x + 2, f" {title} ", attr | curses.A_BOLD)

    def draw_tile_row(
        self,
        y: int,
        x: int,
        tiles: List[Tile],
        max_width: int,
        *,
        hidden: bool = False,
        indexed: bool = False,
        selected_index: Optional[int] = None,
        gap_before_index: Optional[int] = None,
    ) -> None:
        cursor = x
        visible_tiles = tiles
        for index, tile in enumerate(visible_tiles):
            if (
                gap_before_index is not None
                and index == gap_before_index
                and cursor > x
            ):
                cursor += 1
            label = self.tile_label(tile, hidden)
            if indexed:
                label = f"{index + 1:02d}{label}"
            label_width = self.display_width(label)
            if cursor + label_width > x + max_width:
                remaining = len(visible_tiles) - index
                if remaining > 0:
                    self.safe_addstr(y, cursor, f"+{remaining}")
                return
            attr = self.tile_attr(tile, hidden)
            if selected_index == index:
                attr |= curses.A_REVERSE
            self.safe_addstr(y, cursor, label, attr)
            cursor += label_width + 1

    def draw_river_tile_row(
        self,
        y: int,
        x: int,
        tiles: List[Tile],
        max_width: int,
        *,
        first_index: int,
        riichi_index: Optional[int],
    ) -> None:
        cursor = x
        for offset, tile in enumerate(tiles):
            label = self.tile_label(tile)
            label_width = self.display_width(label)
            if cursor + label_width > x + max_width:
                return
            attr = self.tile_attr(tile)
            if riichi_index is not None and first_index + offset == riichi_index:
                attr |= curses.A_REVERSE | curses.A_UNDERLINE
            self.safe_addstr(y, cursor, label, attr)
            cursor += label_width + 1

    def action_attr(self, action: GameAction, selected: bool = False) -> int:
        color_pair = {
            GameAction.CHI: COLOR_ACTION_CHI,
            GameAction.PON: COLOR_ACTION_PON,
            GameAction.KAN: COLOR_ACTION_KAN,
            GameAction.DECLARE_ANKAN: COLOR_ACTION_KAN,
            GameAction.RON: COLOR_ACTION_WIN,
            GameAction.TSUMO: COLOR_ACTION_WIN,
            GameAction.DECLARE_RIICHI: COLOR_ACTION_RIICHI,
            GameAction.PASS: COLOR_ACTION_PASS,
        }.get(action, COLOR_ALERT)
        extra = curses.A_BOLD
        if selected:
            extra |= curses.A_REVERSE
        return self.color(color_pair, extra)

    def action_option_width(self, option: ActionOption) -> int:
        if option.meld_tiles:
            label = self.action_text(option.action)
            return (
                self.display_width(label)
                + 1
                + sum(
                    self.display_width(self.tile_label(tile))
                    for tile in option.meld_tiles
                )
            )
        return self.display_width(f"[{self.action_text(option.action)}]")

    def draw_action_option(
        self, y: int, x: int, option: ActionOption, selected: bool
    ) -> int:
        if not option.meld_tiles:
            label = f"[{self.action_text(option.action)}]"
            self.safe_addstr(y, x, label, self.action_attr(option.action, selected))
            return self.display_width(label)

        cursor = x
        action_label = self.action_text(option.action)
        self.safe_addstr(
            y, cursor, action_label, self.action_attr(option.action, selected)
        )
        cursor += self.display_width(action_label)
        space_attr = self.action_attr(option.action, selected) if selected else 0
        self.safe_addstr(y, cursor, " ", space_attr)
        cursor += 1
        for tile in option.meld_tiles:
            label = self.tile_label(tile)
            attr = self.tile_attr(tile, bold=False)
            if selected:
                attr |= curses.A_REVERSE
            self.safe_addstr(y, cursor, label, attr)
            cursor += self.display_width(label)
        return cursor - x

    def draw_action_row(self, y: int, x: int, width: int) -> None:
        if not self.active_options:
            if not self.active_actions or self.selected_action_index is None:
                return
            self.active_options = [
                ActionOption(action=action) for action in self.active_actions
            ]
            self.selected_option_index = self.selected_action_index

        self.safe_addstr(y, x, f"{self.t('select_action')}:")
        cursor = x + self.display_width(self.t("select_action")) + 2
        max_x = x + width
        for index, option in enumerate(self.active_options):
            label_width = self.action_option_width(option)
            if cursor + label_width > max_x:
                remaining = len(self.active_options) - index
                if remaining > 0:
                    self.safe_addstr(y, cursor, f"+{remaining}")
                return
            selected = (
                self.selected_option_index is not None
                and index == self.selected_option_index
            )
            self.draw_action_option(y, cursor, option, selected)
            cursor += label_width + 1

    def draw_sequence_row(self, y: int, x: int, width: int) -> None:
        if not self.active_sequences or self.selected_sequence_index is None:
            return

        self.safe_addstr(y, x, f"{self.t('select_sequence')}:")
        cursor = x + self.display_width(self.t("select_sequence")) + 2
        max_x = x + width
        for index, sequence in enumerate(self.active_sequences):
            label = f"[{self.tiles_text(sequence)}]"
            label_width = self.display_width(label)
            if cursor + label_width > max_x:
                remaining = len(self.active_sequences) - index
                if remaining > 0:
                    self.safe_addstr(y, cursor, f"+{remaining}")
                return
            attr = curses.A_REVERSE if index == self.selected_sequence_index else 0
            self.safe_addstr(y, cursor, label, attr)
            cursor += label_width + 1

    def draw_discard_grid(
        self, y: int, x: int, tiles: List[Tile], width: int, rows: int
    ) -> None:
        per_row = 6
        for row in range(rows):
            start = row * per_row
            if start >= len(tiles):
                return
            row_tiles = tiles[start : start + per_row]
            row_width = self.tile_row_width(row_tiles)
            row_offset = max(0, (width - row_width) // 2)
            row_x = x + row_offset
            self.draw_tile_row(y + row, row_x, row_tiles, width - row_offset)

    def tile_row_width(self, tiles: List[Tile]) -> int:
        if not tiles:
            return 0
        labels_width = sum(self.display_width(self.tile_label(tile)) for tile in tiles)
        return labels_width + len(tiles) - 1

    def draw_discard_river_row(
        self,
        y: int,
        x: int,
        tiles: List[Tile],
        width: int,
        rows: int = 3,
        *,
        riichi_index: Optional[int] = None,
    ) -> None:
        visible_tiles = tiles[-18:]
        first_index = max(0, len(tiles) - len(visible_tiles))
        per_row = 6
        for row in range(rows):
            start = row * per_row
            if start >= len(visible_tiles):
                return
            row_tiles = visible_tiles[start : start + per_row]
            row_width = self.tile_row_width(row_tiles)
            row_offset = max(0, (width - row_width) // 2)
            row_x = x + row_offset
            self.draw_river_tile_row(
                y + row,
                row_x,
                row_tiles,
                width - row_offset,
                first_index=first_index + start,
                riichi_index=riichi_index,
            )

    def draw_player_panel(
        self,
        player: int,
        y: int,
        x: int,
        height: int,
        width: int,
        *,
        hidden: bool,
    ) -> None:
        assert self.engine is not None
        state = self.engine.game_state
        hand = self.engine.get_hand(player)
        wind = state.seat_winds[player]
        dealer = "D" if state.dealer == player else " "
        riichi = "R" if hand.is_riichi else " "
        title = f"P{player} {getattr(wind, self.settings.language)} [{dealer}{riichi}]"
        self.draw_box(y, x, height, width, title)
        if hidden:
            self.draw_tile_row(y + 1, x + 2, hand.tiles, width - 4, hidden=True)
        else:
            display_tiles = self.selection_tiles or self.sorted_hand_tiles(hand)
            gap_before_index = self.incoming_tile_index(
                display_tiles, hand.last_drawn_tile
            )
            self.draw_tile_row(
                y + 1,
                x + 2,
                display_tiles,
                width - 4,
                indexed=True,
                selected_index=self.selected_tile_index if player == 0 else None,
                gap_before_index=gap_before_index,
            )
        self.safe_addstr(y + 2, x + 2, f"{self.t('melds')}:")
        self.draw_melds(y + 2, x + 10, hand.melds, width - 12, owner=player)
        if player == 0:
            self.draw_action_row(y + 3, x + 2, width - 4)

    def player_score_text(self, player: int, *, compact: bool = False) -> str:
        assert self.engine is not None
        state = self.engine.game_state
        wind = getattr(state.seat_winds[player], self.settings.language)
        dealer = "*" if state.dealer == player else " "
        if compact:
            wind = wind[:1]
            return f"{dealer}{wind} P{player} {state.scores[player]}"
        return f"{dealer}P{player} {wind} {state.scores[player]}"

    def draw_center_table(self, y: int, x: int, height: int, width: int) -> None:
        assert self.engine is not None
        state = self.engine.game_state
        self.draw_box(y, x, height, width)
        title = (
            f"{getattr(state.round_wind, self.settings.language)} {state.round_number}"
        )
        counters = f"{self.t('honba')} {state.honba}   {self.t('kyoutaku')} {state.riichi_sticks}"
        wall = f"{self.t('wall')} {self.engine.get_wall_remaining()}"
        dealer = f"{self.t('dealer')} P{state.dealer}"
        self.add_centered(
            y + 1, x + 1, width - 2, self.player_score_text(2, compact=True)
        )
        self.safe_addstr(y + 3, x + 2, self.player_score_text(3, compact=True))
        p1 = self.player_score_text(1, compact=True)
        self.safe_addstr(
            y + 3,
            x + max(2, width - self.display_width(p1) - 2),
            p1,
        )
        self.add_centered(y + 4, x + 1, width - 2, title, curses.A_BOLD)
        self.add_centered(y + 5, x + 1, width - 2, counters)
        self.add_centered(y + 6, x + 1, width - 2, wall)
        self.add_centered(y + 7, x + 1, width - 2, dealer)
        self.add_centered(
            y + height - 2,
            x + 1,
            width - 2,
            self.player_score_text(0, compact=True),
        )

    def draw_table_discards(
        self, center_y: int, center_x: int, table_x: int, table_width: int
    ) -> None:
        assert self.engine is not None
        center_height = 9
        center_width = 30
        side_gap = 6
        table_inner_x = table_x + 2
        table_inner_right = table_x + table_width - 2
        side_available = min(
            center_x - side_gap - table_inner_x,
            table_inner_right - (center_x + center_width + side_gap),
        )
        side_width = max(18, min(42, side_available))
        left_x = center_x - side_gap - side_width
        right_x = center_x + center_width + side_gap
        top_width = min(72, table_width - 4)
        top_x = center_x + (center_width - top_width) // 2
        dora = self.tiles_text(
            self.engine.get_revealed_dora_indicators(), mark_dora=False
        )

        self.add_centered(
            center_y - 6,
            top_x,
            top_width,
            f"P2 {self.t('discards')}",
            curses.A_DIM,
        )
        hand2 = self.engine.get_hand(2)
        self.draw_discard_river_row(
            center_y - 5,
            top_x,
            hand2.discards,
            top_width,
            riichi_index=hand2.riichi_discard_index,
        )
        self.add_centered(center_y - 1, top_x, top_width, f"{self.t('dora')}: {dora}")

        self.add_centered(
            center_y,
            left_x,
            side_width,
            f"P3 {self.t('discards')}",
            curses.A_DIM,
        )
        hand3 = self.engine.get_hand(3)
        self.draw_discard_river_row(
            center_y + 1,
            left_x,
            hand3.discards,
            side_width,
            riichi_index=hand3.riichi_discard_index,
        )
        self.add_centered(
            center_y,
            right_x,
            side_width,
            f"P1 {self.t('discards')}",
            curses.A_DIM,
        )
        hand1 = self.engine.get_hand(1)
        self.draw_discard_river_row(
            center_y + 1,
            right_x,
            hand1.discards,
            side_width,
            riichi_index=hand1.riichi_discard_index,
        )

        self.add_centered(
            center_y + center_height + 1,
            top_x,
            top_width,
            f"P0 {self.t('discards')}",
            curses.A_DIM,
        )
        hand0 = self.engine.get_hand(0)
        self.draw_discard_river_row(
            center_y + center_height + 2,
            top_x,
            hand0.discards,
            top_width,
            riichi_index=hand0.riichi_discard_index,
        )

    def draw_status_panel(self, y: int, x: int, width: int) -> None:
        dora = self.tiles_text(
            self.engine.get_revealed_dora_indicators(), mark_dora=False
        )
        lines = [
            f"{self.t('dora')}: {dora}",
            f"{self.t('difficulty')}: {self.settings.difficulty}",
            f"{self.t('language')}: {self.settings.language}",
        ]
        for index, line in enumerate(lines):
            self.safe_addstr(y + index, x, line[:width], curses.A_DIM)

    def render(self) -> None:
        assert self.engine is not None
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        if height < 44 or width < 170:
            self.render_compact()
            self.stdscr.refresh()
            return

        state = self.engine.game_state
        title = f" {self.t('title')} "
        self.safe_addstr(0, 2, title, self.color(COLOR_BORDER, curses.A_BOLD))
        self.safe_addstr(1, 2, self.t("help_game"), curses.A_DIM)
        scores = "  ".join(f"P{i}: {score}" for i, score in enumerate(state.scores))
        self.safe_addstr(1, max(2, width - len(scores) - 3), scores)

        margin_x = 2
        side_width = 31
        side_gap = 2
        bottom_panel_height = 7
        table_y = 8
        bottom_y = height - bottom_panel_height - 1
        table_height = bottom_y - table_y - 1
        left_panel_x = margin_x
        right_panel_x = width - side_width - margin_x
        table_x = left_panel_x + side_width + side_gap
        table_width = right_panel_x - table_x - side_gap
        top_panel_y = table_y - 5
        center_width = 30
        center_height = 9
        center_x = (width - center_width) // 2
        center_y = table_y + max(5, (table_height - center_height) // 2)

        self.draw_player_panel(
            2, top_panel_y, table_x, 4, table_width, hidden=True
        )

        self.draw_player_panel(
            3,
            table_y,
            left_panel_x,
            table_height,
            side_width,
            hidden=True,
        )
        self.draw_player_panel(
            1,
            table_y,
            right_panel_x,
            table_height,
            side_width,
            hidden=True,
        )

        self.draw_box(table_y, table_x, table_height, table_width, self.t("table"))
        self.draw_table_discards(center_y, center_x, table_x, table_width)
        self.draw_center_table(center_y, center_x, center_height, center_width)
        self.draw_status_panel(3, 3, 32)

        if self.status:
            self.safe_addstr(
                bottom_y - 1,
                table_x,
                self.status[:table_width],
                curses.A_BOLD,
            )
        self.draw_player_panel(0, bottom_y, table_x, 7, table_width, hidden=False)
        self.stdscr.refresh()

    def render_compact(self) -> None:
        assert self.engine is not None
        state = self.engine.game_state
        dora = self.tiles_text(
            self.engine.get_revealed_dora_indicators(), mark_dora=False
        )
        wall = self.engine.get_wall_remaining()
        header = (
            f"{self.t('round')}: {getattr(state.round_wind, self.settings.language)} {state.round_number}  "
            f"{self.t('dealer')}: P{state.dealer}  "
            f"{self.t('honba')}: {state.honba}  "
            f"{self.t('kyoutaku')}: {state.riichi_sticks}  "
            f"{self.t('wall')}: {wall}  "
            f"{self.t('dora')}: {dora}"
        )
        self.safe_addstr(0, 2, header, curses.A_BOLD)
        self.safe_addstr(1, 2, self.t("help_game"), curses.A_DIM)
        if self.status:
            self.safe_addstr(2, 2, self.status, curses.A_BOLD)

        scores = "  ".join(f"P{i}: {score}" for i, score in enumerate(state.scores))
        self.safe_addstr(3, 2, f"{self.t('scores')}: {scores}")

        for player in range(1, 4):
            y = 5 + (player - 1) * 4
            hand = self.engine.get_hand(player)
            self.safe_addstr(
                y,
                2,
                f"P{player} {'(dealer)' if state.dealer == player else ''}: "
                f"{len(hand.tiles)} tiles",
                curses.A_BOLD,
            )
            self.safe_addstr(
                y + 1,
                4,
                f"{self.t('melds')}: {self.melds_text(hand.melds, owner=player)}",
            )
            self.safe_addstr(
                y + 2,
                4,
                f"{self.t('discards')}: {self.tiles_text(hand.discards[-18:])}",
            )

        hand = self.engine.get_hand(0)
        base_y = 18
        self.safe_addstr(base_y, 2, f"P0 {self.t('hand')}:", curses.A_BOLD)
        display_tiles = self.selection_tiles or self.sorted_hand_tiles(hand)
        self.draw_tile_row(
            base_y + 1,
            4,
            display_tiles,
            74,
            indexed=True,
            selected_index=self.selected_tile_index,
        )
        self.draw_action_row(base_y + 2, 4, 74)
        self.safe_addstr(base_y + 3, 4, f"{self.t('melds')}:")
        self.draw_melds(base_y + 3, 12, hand.melds, 66, owner=0)
        self.safe_addstr(
            base_y + 4,
            4,
            f"{self.t('discards')}: {self.tiles_text(hand.discards[-24:])}",
        )

    def tiles_text(self, tiles: List[Tile], *, mark_dora: bool = True) -> str:
        if not tiles:
            return self.t("none")
        return " ".join(self.tile_label(tile, mark_dora=mark_dora) for tile in tiles)

    def arrange_called_tile(
        self,
        tiles: List[Tile],
        called_tile: Optional[Tile],
        called_from: Optional[int],
        owner: int,
    ) -> List[Tile]:
        if called_tile is None or called_from is None:
            return tiles

        remaining = []
        removed_called_tile = None
        for tile in tiles:
            if removed_called_tile is None and tile is called_tile:
                removed_called_tile = tile
            else:
                remaining.append(tile)
        if removed_called_tile is None:
            remaining = []
            for tile in tiles:
                if removed_called_tile is None and tile == called_tile:
                    removed_called_tile = tile
                else:
                    remaining.append(tile)

        display_called_tile = removed_called_tile or called_tile
        insert_at = self.called_tile_slot(len(tiles), called_from, owner)
        if insert_at is not None:
            insert_at = min(insert_at, len(remaining))
            return remaining[:insert_at] + [display_called_tile] + remaining[insert_at:]
        return tiles

    @staticmethod
    def called_tile_slot(
        tile_count: int, called_from: Optional[int], owner: int
    ) -> Optional[int]:
        if called_from is None or tile_count <= 0:
            return None
        source_direction = (called_from - owner) % 4
        if source_direction == 3:
            return 0
        if source_direction == 2:
            return tile_count // 2
        if source_direction == 1:
            return tile_count - 1
        return None

    def meld_display_tiles(self, meld: Meld, owner: int = 0) -> List[Tile]:
        return self.arrange_called_tile(
            meld.tiles,
            meld.called_tile,
            getattr(meld, "called_from", None),
            owner,
        )

    def draw_melds(
        self, y: int, x: int, melds: List[Meld], width: int, *, owner: int
    ) -> None:
        if not melds:
            self.safe_addstr(y, x, self.t("none"))
            return

        cursor = x
        max_x = x + width
        for meld_index, meld in enumerate(melds):
            if meld_index:
                separator = " / "
                if cursor + self.display_width(separator) > max_x:
                    return
                self.safe_addstr(y, cursor, separator, curses.A_DIM)
                cursor += self.display_width(separator)

            display_tiles = self.meld_display_tiles(meld, owner)
            called_index = self.called_tile_slot(
                len(display_tiles), getattr(meld, "called_from", None), owner
            )
            for tile_index, tile in enumerate(display_tiles):
                label = self.tile_label(tile)
                label_width = self.display_width(label)
                if cursor + label_width > max_x:
                    return
                is_called_tile = tile_index == called_index
                attr = self.tile_attr(tile, bold=is_called_tile)
                if is_called_tile:
                    attr |= curses.A_UNDERLINE
                self.safe_addstr(y, cursor, label, attr)
                cursor += label_width

    def meld_text(self, meld: Meld, owner: int = 0) -> str:
        return "".join(
            self.tile_label(tile) for tile in self.meld_display_tiles(meld, owner)
        )

    def melds_text(self, melds: List[Meld], owner: int = 0) -> str:
        if not melds:
            return self.t("none")
        return " / ".join(self.meld_text(meld, owner) for meld in melds)


def main() -> None:
    curses.wrapper(lambda stdscr: Tui(stdscr).run())


if __name__ == "__main__":
    main()
