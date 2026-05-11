"""
Ruleset Configuration System - RulesetConfig

Manages riichi Mahjong rule variations configuration, supporting standard competitive rules and custom rules.
"""

from dataclasses import dataclass
from enum import Enum


class RenhouPolicy(str, Enum):
    """renhou rule setting."""

    YAKUMAN = "yakuman"
    TWO_HAN = "two_han"
    OFF = "off"


@dataclass
class RulesetConfig:
    """
    Ruleset configuration class.

    Used to configure different rule variations of riichi Mahjong, supporting standard competitive rules.

    Attributes:
        renhou_policy (RenhouPolicy): renhou rule.
            - YAKUMAN: yakuman (13 han).
            - TWO_HAN: 2 han (Standard competitive rule).
            - OFF: Disabled.
        pinfu_require_ryanmen (bool): Whether pinfu requires ryanmen (Two-Sided Wait) machi.
            - True: Must be ryanmen (Two-Sided Wait) machi (Standard competitive rule).
            - False: Do not check machi.
        ippatsu_interrupt_on_meld_or_kan (bool): Whether ippatsu is interrupted by Meld/kan.
            - True: Meld or kan interrupts ippatsu (Standard competitive rule).
            - False: Do not check interruption condition.
        open_tanyao_enabled (bool): Whether Open Tanyao is enabled.
            - True: Open hands may score Tanyao.
            - False: Tanyao requires a closed hand.
        abortive_draw_dealer_continues (bool): Whether abortive draws keep the current dealer.
            - True: Abortive draws keep the dealer and increment honba.
            - False: Abortive draws rotate the dealer and increment honba.
        chanta_enabled (bool): Whether chanta is enabled.
            - True: Enabled (Standard competitive rule).
            - False: Disabled.
        chanta_open_han (int): chanta (Open) han. Default is 1.
        chanta_closed_han (int): chanta (Closed) han. Default is 2.
        junchan_open_han (int): junchan (Open) han. Default is 2.
        junchan_closed_han (int): junchan (Closed) han. Default is 3.
        suuankou_tanki_double (bool): Whether suuankou tanki is Double yakuman.
            - True: Double yakuman (26 han, Standard competitive rule).
            - False: Single yakuman (13 han).
        kokushi_musou_juusanmen_double (bool): Whether kokushi_musou_juusanmen is Double yakuman.
            - True: Double yakuman (26 han, Standard competitive rule).
            - False: Single yakuman (13 han).
        pure_chuuren_poutou_double (bool): Whether pure_chuuren_poutou is Double yakuman.
            - True: Double yakuman (26 han, Standard competitive rule).
            - False: Single yakuman (13 han).
        kiriage_mangan (bool): kiriage_mangan rule.
            - True: 30 fu 4 han or 60 fu 3 han counts as mangan (Optional rule).
            - False: Calculate based on normal basic points (Standard competitive rule).
        tobi_enabled (bool): tobi (Bankruptcy) rule.
            - True: Game ends when player points < 0.
            - False: Game continues until round ends.
        west_round_extension (bool): west_round_extension rule (Enchousen).
            - True: If no one reaches return_score at end of south 4, enter west round.
            - False: Game ends at end of South 4.
        return_score (int): Return score threshold.
            - When game ends, if 1st place score is below this score, and west_round_extension is enabled, game extends.
        agari_yame (bool): Agari Yame.
            - True: If dealer wins in the last round (south 4 or west 4) and is 1st place, game ends.
            - False: dealer repeats (renchan), game continues.
        chombo_penalty_enabled (bool): Chombo penalty rule.
            - True: Pay mangan penalty and end the round when violation occurs.
            - False: Ignore violation or just reject action.
        riichi_min_remaining_tiles (int): Minimum live wall tiles required to declare riichi.
        head_bump_only (bool): head_bump rule (only shimocha wins).
            - True: When multiple players can ron, only the discarder's shimocha (closest counter-clockwise) wins.
            - False: Allow multiple ron (Requires allow_double_ron or allow_triple_ron).
        allow_double_ron (bool): double_ron rule.
            - True: Allow two players to ron simultaneously.
            - False: Prohibit double_ron (may trigger head_bump or ryuukyoku).
            Note: Requires head_bump_only = False.
        allow_triple_ron (bool): triple_ron rule.
            - True: Allow three players to ron simultaneously.
            - False: Three players ron leads to ryuukyoku (sancha_ron).
            Note: Requires head_bump_only = False and allow_double_ron = True.
    """

    # renhou rule
    renhou_policy: RenhouPolicy = RenhouPolicy.TWO_HAN

    # pinfu Rule
    pinfu_require_ryanmen: bool = True

    # ippatsu Rule
    ippatsu_interrupt_on_meld_or_kan: bool = True

    # Open Tanyao rule
    open_tanyao_enabled: bool = True

    # Abortive Draw rule
    abortive_draw_dealer_continues: bool = True

    # chanta Rules
    chanta_enabled: bool = True

    chanta_open_han: int = 1
    chanta_closed_han: int = 2
    junchan_open_han: int = 2
    junchan_closed_han: int = 3

    # suuankou tanki Rule
    suuankou_tanki_double: bool = True

    # kokushi_musou_juusanmen rule
    kokushi_musou_juusanmen_double: bool = True

    # chuuren_poutou rule
    pure_chuuren_poutou_double: bool = True

    # kiriage_mangan rule
    kiriage_mangan: bool = False

    # tobi Rule
    tobi_enabled: bool = True

    # Game End Rules
    west_round_extension: bool = True

    return_score: int = 30000

    agari_yame: bool = True

    # Violation Penalty Rule
    chombo_penalty_enabled: bool = True

    riichi_min_remaining_tiles: int = 4

    # head_bump / double_ron / triple_ron rules
    head_bump_only: bool = True

    allow_double_ron: bool = False

    allow_triple_ron: bool = False

    @classmethod
    def standard(cls) -> "RulesetConfig":
        """
        Create standard competitive ruleset configuration.

        Returns:
            RulesetConfig: Standard competitive ruleset configuration.
        """
        return cls(
            renhou_policy=RenhouPolicy.TWO_HAN,
            pinfu_require_ryanmen=True,
            ippatsu_interrupt_on_meld_or_kan=True,
            open_tanyao_enabled=True,
            abortive_draw_dealer_continues=True,
            chanta_enabled=True,
            chanta_open_han=1,
            chanta_closed_han=2,
            junchan_open_han=2,
            junchan_closed_han=3,
            suuankou_tanki_double=True,
            kokushi_musou_juusanmen_double=True,
            pure_chuuren_poutou_double=True,
            kiriage_mangan=False,
            tobi_enabled=True,
            west_round_extension=True,
            return_score=30000,
            agari_yame=True,
            chombo_penalty_enabled=True,
            riichi_min_remaining_tiles=4,
        )
