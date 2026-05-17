"""Translated exception types for pyriichi."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    "pair_requires_two_tiles": {
        "en": "A pair must have 2 tiles",
        "ja": "対子は2枚でなければなりません",
        "zh": "對子必須是 2 張牌",
    },
    "triplet_requires_three_tiles": {
        "en": "A triplet must have 3 tiles",
        "ja": "刻子は3枚でなければなりません",
        "zh": "刻子必須是 3 張牌",
    },
    "sequence_requires_three_tiles": {
        "en": "A sequence must have 3 tiles",
        "ja": "順子は3枚でなければなりません",
        "zh": "順子必須是 3 張牌",
    },
    "kan_requires_four_tiles": {
        "en": "A kan must have 4 tiles",
        "ja": "槓子は4枚でなければなりません",
        "zh": "槓子必須是 4 張牌",
    },
    "honors_cannot_form_sequence": {
        "en": "Honor tiles cannot form a sequence",
        "ja": "字牌は順子にできません",
        "zh": "字牌不能組成順子",
    },
    "sequence_start_out_of_range": {
        "en": "Sequence starting rank must be between 1 and 7",
        "ja": "順子の開始番号は1から7の間でなければなりません",
        "zh": "順子起始點數必須介於 1 到 7 之間",
    },
    "unsupported_combination_type": {
        "en": "Unsupported combination type: {combo_type}",
        "ja": "未対応の組合せ種類: {combo_type}",
        "zh": "不支援的組合類型：{combo_type}",
    },
    "chi_requires_three_tiles": {
        "en": "Chi must have 3 tiles",
        "ja": "チーは3枚でなければなりません",
        "zh": "吃必須是 3 張牌",
    },
    "pon_requires_three_tiles": {
        "en": "Pon must have 3 tiles",
        "ja": "ポンは3枚でなければなりません",
        "zh": "碰必須是 3 張牌",
    },
    "meld_kan_requires_four_tiles": {
        "en": "Kan must have 4 tiles",
        "ja": "カンは4枚でなければなりません",
        "zh": "槓必須是 4 張牌",
    },
    "no_discard_to_remove": {
        "en": "There is no discard to remove",
        "ja": "取り除ける捨て牌がありません",
        "zh": "沒有可移除的捨牌",
    },
    "last_discard_mismatch": {
        "en": "The last discard does not match the specified tile",
        "ja": "最後の捨て牌が指定牌と一致しません",
        "zh": "最後一張捨牌與指定牌不符",
    },
    "cannot_chi_tile": {
        "en": "Cannot chi this tile",
        "ja": "この牌はチーできません",
        "zh": "不能吃這張牌",
    },
    "cannot_pon_tile": {
        "en": "Cannot pon this tile",
        "ja": "この牌はポンできません",
        "zh": "不能碰這張牌",
    },
    "cannot_kan_tile": {
        "en": "Cannot kan this tile",
        "ja": "この牌はカンできません",
        "zh": "不能槓這張牌",
    },
    "no_tile_for_added_kan": {
        "en": "No tile is available for added kan",
        "ja": "加槓に使える牌がありません",
        "zh": "沒有可用的牌升級為加槓",
    },
    "invalid_wind": {
        "en": "Invalid wind: {wind}",
        "ja": "無効な風: {wind}",
        "zh": "無效的風牌：{wind}",
    },
    "dealer_position_out_of_range": {
        "en": "Dealer position must be between 0 and {max_player}",
        "ja": "親の位置は0から{max_player}の間でなければなりません",
        "zh": "莊家位置必須在 0-{max_player} 之間",
    },
    "player_position_out_of_range": {
        "en": "Player position must be between 0 and {max_player}",
        "ja": "プレイヤー位置は0から{max_player}の間でなければなりません",
        "zh": "玩家位置必須在 0-{max_player} 之間",
    },
    "honor_rank_out_of_range": {
        "en": "Honor tile rank must be between 1 and 7; got {rank}",
        "ja": "字牌の番号は1から7の間でなければなりません。値: {rank}",
        "zh": "字牌序號必須在 1-7 之間，得到 {rank}",
    },
    "number_rank_out_of_range": {
        "en": "Number tile rank must be between 1 and 9; got {rank}",
        "ja": "数牌の番号は1から9の間でなければなりません。値: {rank}",
        "zh": "數牌序號必須在 1-9 之間，得到 {rank}",
    },
    "unsupported_locale": {
        "en": "Unsupported locale: {locale}",
        "ja": "未対応のロケール: {locale}",
        "zh": "不支援的語系：{locale}",
    },
    "invalid_suit": {
        "en": "Invalid suit: {suit}",
        "ja": "無効な色: {suit}",
        "zh": "無效的花色：{suit}",
    },
    "dora_indicators_insufficient": {
        "en": "Not enough dora indicators: need {count}, only {actual} available",
        "ja": "ドラ表示牌が不足しています。必要: {count}、現在: {actual}",
        "zh": "寶牌指示牌不足，需要 {count} 張，只有 {actual} 張",
    },
    "ura_dora_indicators_insufficient": {
        "en": "Not enough ura dora indicators: need {count}, only {actual} available",
        "ja": "裏ドラ表示牌が不足しています。必要: {count}、現在: {actual}",
        "zh": "裏寶牌指示牌不足，需要 {count} 張，只有 {actual} 張",
    },
    "deal_only_in_dealing_phase": {
        "en": "Tiles can only be dealt during the dealing phase",
        "ja": "配牌は配牌フェーズでのみ実行できます",
        "zh": "只能在發牌階段發牌",
    },
    "tile_set_not_initialized": {
        "en": "Tile wall is not initialized",
        "ja": "牌山が初期化されていません",
        "zh": "牌山未初始化",
    },
    "action_not_allowed": {
        "en": "Player {player} cannot execute action {action}",
        "ja": "プレイヤー {player} は操作 {action} を実行できません",
        "zh": "玩家 {player} 不能執行操作 {action}",
    },
    "action_not_implemented": {
        "en": "Action {action} is not implemented",
        "ja": "操作 {action} は未実装です",
        "zh": "操作 {action} 尚未實作",
    },
    "player_not_waiting_for_action": {
        "en": "Player {player} is not waiting for an action",
        "ja": "プレイヤー {player} は現在操作待ちではありません",
        "zh": "玩家 {player} 目前不需要執行操作",
    },
    "action_not_expected": {
        "en": "Player {player} cannot execute action {action}; expected: {allowed_actions}",
        "ja": "プレイヤー {player} は操作 {action} を実行できません。可能操作: {allowed_actions}",
        "zh": "玩家 {player} 不能執行操作 {action}，可用操作：{allowed_actions}",
    },
    "cannot_ron_without_discard": {
        "en": "Cannot ron without a discard",
        "ja": "捨て牌がないためロンできません",
        "zh": "沒有捨牌，無法榮和",
    },
    "no_discard": {
        "en": "No discard",
        "ja": "捨て牌がありません",
        "zh": "沒有捨牌",
    },
    "hand_limit_reached": {
        "en": "Hand already has {limit} tiles and cannot draw more",
        "ja": "手牌はすでに{limit}枚あり、これ以上ツモれません",
        "zh": "手牌已達 {limit} 張，不能再摸牌",
    },
    "discard_requires_tile": {
        "en": "Discard action requires a tile",
        "ja": "打牌操作には牌の指定が必要です",
        "zh": "打牌操作必須指定牌",
    },
    "riichi_must_discard_drawn_tile": {
        "en": "After riichi, only the drawn tile can be discarded",
        "ja": "立直後はツモった牌のみ打牌できます",
        "zh": "立直後只能打出剛摸到的牌",
    },
    "no_pon_discard": {
        "en": "There is no discard to pon",
        "ja": "ポンできる捨て牌がありません",
        "zh": "沒有可碰的捨牌",
    },
    "cannot_pon_own_discard": {
        "en": "Cannot pon your own discard",
        "ja": "自分の捨て牌はポンできません",
        "zh": "不能碰自己打出的牌",
    },
    "hand_cannot_pon_tile": {
        "en": "Hand cannot pon this tile",
        "ja": "手牌ではこの牌をポンできません",
        "zh": "手牌無法碰這張牌",
    },
    "no_chi_discard": {
        "en": "There is no discard to chi",
        "ja": "チーできる捨て牌がありません",
        "zh": "沒有可吃的捨牌",
    },
    "can_only_chi_from_kamicha": {
        "en": "Can only chi from kamicha",
        "ja": "チーは上家の牌に対してのみ可能です",
        "zh": "只能吃上家的牌",
    },
    "hand_cannot_chi_tile": {
        "en": "Hand cannot chi this tile",
        "ja": "手牌ではこの牌をチーできません",
        "zh": "手牌無法吃這張牌",
    },
    "invalid_chi_sequence": {
        "en": "Provided chi sequence is invalid",
        "ja": "指定された順子は無効です",
        "zh": "提供的順子無效",
    },
    "riichi_requires_discard": {
        "en": "Riichi must discard a tile at the same time",
        "ja": "リーチは同時に打牌する必要があります",
        "zh": "立直必須同時打出一張牌",
    },
    "riichi_not_enough_wall_tiles": {
        "en": "Not enough remaining wall tiles to declare riichi",
        "ja": "リーチには牌山の残り枚数が不足しています",
        "zh": "立直時牌山剩餘張數不足",
    },
    "tile_not_in_hand": {
        "en": "Tile is not in hand",
        "ja": "手牌にこの牌がありません",
        "zh": "手牌中沒有這張牌",
    },
    "riichi_discard_must_keep_tenpai": {
        "en": "Riichi discard must leave the hand in tenpai",
        "ja": "リーチ打牌後は聴牌していなければなりません",
        "zh": "立直打牌後必須聽牌",
    },
    "open_kan_requires_called_tile": {
        "en": "Open kan must specify the called tile",
        "ja": "明槓には鳴いた牌の指定が必要です",
        "zh": "明槓必須指定被槓的牌",
    },
    "hand_cannot_closed_kan": {
        "en": "Hand cannot declare closed kan",
        "ja": "手牌では暗槓できません",
        "zh": "手牌無法暗槓",
    },
    "cannot_closed_kan_tile": {
        "en": "Cannot declare closed kan with specified tile: {tile}",
        "ja": "指定された牌では暗槓できません: {tile}",
        "zh": "無法暗槓指定的牌：{tile}",
    },
    "cannot_determine_tsumo_tile": {
        "en": "Cannot determine the tsumo tile",
        "ja": "ツモ牌を特定できません",
        "zh": "無法確定自摸的牌",
    },
    "cannot_tsumo_with_tile": {
        "en": "Player {player} cannot tsumo with {tile}",
        "ja": "プレイヤー {player} は {tile} でツモ和了できません",
        "zh": "玩家 {player} 無法用 {tile} 自摸和牌",
    },
    "no_ron_discard": {
        "en": "There is no discard to ron",
        "ja": "ロンできる捨て牌がありません",
        "zh": "沒有可榮和的捨牌",
    },
    "cannot_ron": {
        "en": "Player {player} cannot ron because of ruleset limits or furiten",
        "ja": "プレイヤー {player} は設定制限または振聴のためロンできません",
        "zh": "玩家 {player} 因規則設定限制或振聽而不能榮和",
    },
    "kyuushu_kyuuhai_not_met": {
        "en": "Nine terminals abort conditions are not met",
        "ja": "九種九牌の流局条件を満たしていません",
        "zh": "不滿足九種九牌流局條件",
    },
}


@dataclass
class PyRiichiError(ValueError):
    """Base exception carrying translated error messages."""

    code: str
    params: Mapping[str, Any] = field(default_factory=dict)
    default_locale: str = "zh"

    def __post_init__(self) -> None:
        ValueError.__init__(self, self.message(self.default_locale))

    def message(self, locale: str = "zh") -> str:
        translations = ERROR_MESSAGES.get(self.code)
        if translations is None:
            return self.code
        template = translations.get(locale) or translations["en"]
        return template.format(**self.params)

    @property
    def zh(self) -> str:
        return self.message("zh")

    @property
    def ja(self) -> str:
        return self.message("ja")

    @property
    def en(self) -> str:
        return self.message("en")

    def __str__(self) -> str:
        return self.message(self.default_locale)


class HandError(PyRiichiError):
    """Hand and meld validation error."""


class TileError(PyRiichiError):
    """Tile and wall validation error."""


class GameStateError(PyRiichiError):
    """Game state validation error."""


class RuleError(PyRiichiError):
    """Rule engine validation error."""
