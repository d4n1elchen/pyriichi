import curses
import os
import sys
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional

# Allow running this example directly from a source checkout.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyriichi.hand import Hand, Meld
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
        "dealer": "Dealer",
        "honba": "Honba",
        "kyoutaku": "Deposit",
        "wall": "Wall",
        "dora": "Dora indicators",
        "scores": "Scores",
        "hand": "Your hand",
        "melds": "Melds",
        "discards": "Discards",
        "last": "Log",
        "winner": "Winner",
        "ryuukyoku": "Ryuukyoku",
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
        "ryuukyoku": "流局",
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
        "ryuukyoku": "流局",
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
COLOR_RED_DORA = 5
COLOR_BORDER = 6
COLOR_DIM = 7
COLOR_ALERT = 8


@dataclass
class Settings:
    language: str = "en"
    difficulty: str = "normal"
    ruleset: RulesetConfig = None

    def __post_init__(self):
        if self.ruleset is None:
            self.ruleset = RulesetConfig.standard()


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
        self.selected_tile_index: Optional[int] = None
        self.selection_tiles: Optional[List[Tile]] = None

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

    def tile_label(self, tile: Optional[Tile], hidden: bool = False) -> str:
        glyph = self.tile_glyph(tile, hidden)
        if hidden:
            return f"[{glyph}]"
        marker = "*" if tile and tile.is_red_dora else ""
        return f"[{glyph}{marker}]"

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
        curses.init_pair(COLOR_RED_DORA, curses.COLOR_RED, -1)
        curses.init_pair(COLOR_BORDER, curses.COLOR_GREEN, -1)
        curses.init_pair(COLOR_DIM, curses.COLOR_BLUE, -1)
        curses.init_pair(COLOR_ALERT, curses.COLOR_MAGENTA, -1)

    def color(self, color_pair: int, extra: int = 0) -> int:
        if not self.has_colors:
            return extra
        return curses.color_pair(color_pair) | extra

    def tile_attr(self, tile: Optional[Tile], hidden: bool = False) -> int:
        if hidden or tile is None:
            return self.color(COLOR_DIM, curses.A_BOLD)
        if tile.is_red_dora:
            return self.color(COLOR_RED_DORA, curses.A_BOLD)
        if tile.suit == Suit.MANZU:
            return self.color(COLOR_MANZU, curses.A_BOLD)
        if tile.suit == Suit.PINZU:
            return self.color(COLOR_PINZU, curses.A_BOLD)
        if tile.suit == Suit.SOUZU:
            return self.color(COLOR_SOUZU, curses.A_BOLD)
        return self.color(COLOR_HONORS, curses.A_BOLD)

    def main_menu(self) -> None:
        while self.running:
            options = [
                (self.t("language"), self.configure_language),
                (self.t("difficulty"), self.configure_difficulty),
                (self.t("rules"), self.configure_rules),
                (self.t("start"), self.play_game),
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
        self.selected_tile_index = None
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

        self.render()
        self.safe_addstr(1, 2, self.t("game_over"), curses.A_BOLD)
        self.stdscr.getch()

    def start_next_round(self) -> None:
        assert self.engine is not None
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
        self.safe_addstr(1, 2, self.t("next_round"), curses.A_BOLD)
        self.stdscr.refresh()
        while True:
            key = self.stdscr.getch()
            if key == ord("q"):
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

        action = self.choose_action(actions)
        if action is None:
            return None

        tile = None
        kwargs = {}
        if action in {GameAction.DISCARD, GameAction.DECLARE_RIICHI}:
            tile = self.choose_tile_from_hand(player, action, actions)
            if tile is None:
                return None
        elif action in {GameAction.KAN, GameAction.DECLARE_ANKAN}:
            tile = self.choose_kan_tile(player, action)
        elif action == GameAction.CHI:
            sequence = self.choose_chi_sequence(player)
            if sequence is None:
                return None
            kwargs["sequence"] = sequence

        return self.execute_human_action(player, action, tile, **kwargs)

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
            return result
        except ValueError as exc:
            self.set_status(f"{self.t('invalid')}: {exc}")
            return None

    def choose_action(self, actions: List[GameAction]) -> Optional[GameAction]:
        self.active_actions = actions
        self.set_status(self.t("select_action"))
        choice = self.choose(
            self.t("select_action"), [self.action_text(action) for action in actions]
        )
        self.clear_selection()
        if choice is None:
            return None
        return actions[choice]

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
        candidate_index = 0
        self.selected_tile_index = 0
        self.set_status(self.t("select_tile"))

        while True:
            self.render()
            key = self.stdscr.getch()
            if key in (ord("q"), 27):
                self.clear_selection()
                return None
            if key in (curses.KEY_LEFT, ord("h")):
                candidate_index = max(0, candidate_index - 1)
                self.selected_tile_index = candidate_index
            elif key in (curses.KEY_RIGHT, ord("l")):
                candidate_index = min(len(candidates) - 1, candidate_index + 1)
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
        if action == GameAction.KAN and self.engine.get_last_discard() is not None:
            return self.engine.get_last_discard()

        candidates = self.engine.get_hand(player).can_kan(None)
        if not candidates:
            return None
        labels = [self.tiles_text(meld.tiles) for meld in candidates]
        choice = self.choose(self.t("select_tile"), labels)
        if choice is None:
            return None
        return candidates[choice].tiles[0]

    def choose_chi_sequence(self, player: int) -> Optional[List[Tile]]:
        assert self.engine is not None
        sequences = self.engine.get_available_chi_sequences(player)
        if not sequences:
            return None
        labels = [self.tiles_text(sequence) for sequence in sequences]
        choice = self.choose(self.t("select_sequence"), labels)
        return sequences[choice] if choice is not None else None

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
        if result.chombo:
            self.set_status(f"{self.t('chombo')}: P{result.chombo_player}")
        if result.rinshan_win:
            result.winners = [result.rinshan_win.player]
            result.win_results[result.rinshan_win.player] = result.rinshan_win
        if result.winners:
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
            self.set_status(self.ryuukyoku_text(result.ryuukyoku.ryuukyoku_type))
        elif self.engine.get_phase() == GamePhase.PLAYING:
            ryuukyoku_type = self.engine.check_ryuukyoku()
            if ryuukyoku_type:
                ryuukyoku = self.engine.handle_ryuukyoku()
                self.set_status(self.ryuukyoku_text(ryuukyoku.ryuukyoku_type))

    def ryuukyoku_text(self, ryuukyoku_type) -> str:
        if ryuukyoku_type is None:
            return self.t("ryuukyoku")
        return (
            f"{self.t('ryuukyoku')}: {getattr(ryuukyoku_type, self.settings.language)}"
        )

    def draw_box(
        self, y: int, x: int, height: int, width: int, title: str = ""
    ) -> None:
        if height < 2 or width < 2:
            return
        attr = self.color(COLOR_BORDER)
        horizontal = "─" * max(0, width - 2)
        self.safe_addstr(y, x, f"┌{horizontal}┐", attr)
        for row in range(1, height - 1):
            self.safe_addstr(y + row, x, "│", attr)
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
    ) -> None:
        cursor = x
        visible_tiles = tiles
        for index, tile in enumerate(visible_tiles):
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

    def draw_discard_grid(
        self, y: int, x: int, tiles: List[Tile], width: int, rows: int
    ) -> None:
        per_row = max(1, width // 5)
        for row in range(rows):
            start = row * per_row
            if start >= len(tiles):
                return
            self.draw_tile_row(y + row, x, tiles[start : start + per_row], width)

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
            self.draw_tile_row(
                y + 1,
                x + 2,
                display_tiles,
                width - 4,
                indexed=True,
                selected_index=self.selected_tile_index if player == 0 else None,
            )
        self.safe_addstr(y + 2, x + 2, f"{self.t('melds')}:")
        self.safe_addstr(y + 2, x + 10, self.melds_text(hand.melds)[: width - 12])
        self.safe_addstr(y + 3, x + 2, f"{self.t('discards')}:")
        self.draw_discard_grid(y + 4, x + 2, hand.discards[-24:], width - 4, height - 5)

    def draw_center_table(self, y: int, x: int, height: int, width: int) -> None:
        assert self.engine is not None
        state = self.engine.game_state
        self.draw_box(y, x, height, width, "TABLE")
        dora = self.tiles_text(self.engine.get_revealed_dora_indicators())
        wall = self.engine.get_wall_remaining()
        lines = [
            f"{self.t('round')}: {getattr(state.round_wind, self.settings.language)} {state.round_number}",
            f"{self.t('dealer')}: P{state.dealer}",
            f"{self.t('honba')}: {state.honba}   {self.t('kyoutaku')}: {state.riichi_sticks}",
            f"{self.t('wall')}: {wall}",
            f"{self.t('dora')}: {dora}",
            f"{self.t('difficulty')}: {self.settings.difficulty}",
            f"{self.t('language')}: {self.settings.language}",
        ]
        for i, line in enumerate(lines[: height - 2]):
            self.safe_addstr(y + 1 + i, x + 2, line)

    def render(self) -> None:
        assert self.engine is not None
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        if height < 30 or width < 100:
            self.render_compact()
            self.stdscr.refresh()
            return

        state = self.engine.game_state
        title = f" {self.t('title')} "
        self.safe_addstr(0, 2, title, self.color(COLOR_BORDER, curses.A_BOLD))
        self.safe_addstr(1, 2, self.t("help_game"), curses.A_DIM)
        scores = "  ".join(f"P{i}: {score}" for i, score in enumerate(state.scores))
        self.safe_addstr(1, max(2, width - len(scores) - 3), scores)

        top_width = min(66, width - 36)
        top_x = (width - top_width) // 2
        self.draw_player_panel(2, 3, top_x, 7, top_width, hidden=True)

        side_height = max(13, height - 19)
        side_width = 29
        self.draw_player_panel(3, 11, 2, side_height, side_width, hidden=True)
        self.draw_player_panel(
            1, 11, width - side_width - 2, side_height, side_width, hidden=True
        )

        center_x = side_width + 4
        center_width = width - (side_width + 4) * 2
        self.draw_center_table(11, center_x, side_height, center_width)

        bottom_y = height - 8
        if self.status:
            self.safe_addstr(bottom_y - 1, 4, self.status, curses.A_BOLD)
        self.draw_player_panel(0, bottom_y, 2, 7, width - 4, hidden=False)
        self.stdscr.refresh()

    def render_compact(self) -> None:
        assert self.engine is not None
        state = self.engine.game_state
        dora = self.tiles_text(self.engine.get_revealed_dora_indicators())
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
                y + 1, 4, f"{self.t('melds')}: {self.melds_text(hand.melds)}"
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
        self.safe_addstr(
            base_y + 2, 4, f"{self.t('melds')}: {self.melds_text(hand.melds)}"
        )
        self.safe_addstr(
            base_y + 3,
            4,
            f"{self.t('discards')}: {self.tiles_text(hand.discards[-24:])}",
        )

    def tiles_text(self, tiles: List[Tile]) -> str:
        if not tiles:
            return self.t("none")
        return " ".join(self.tile_label(tile) for tile in tiles)

    def meld_text(self, meld: Meld) -> str:
        return self.tiles_text(meld.tiles)

    def melds_text(self, melds: List[Meld]) -> str:
        if not melds:
            return self.t("none")
        return " / ".join(self.meld_text(meld) for meld in melds)


def main() -> None:
    curses.wrapper(lambda stdscr: Tui(stdscr).run())


if __name__ == "__main__":
    main()
