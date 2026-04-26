"""
Ruleset Configuration System - RulesetConfig

Manages Riichi Mahjong rule variations configuration, supporting standard competitive rules and custom rules.
"""

from dataclasses import dataclass
from enum import Enum


class RenhouPolicy(str, Enum):
    """Renhou rule setting."""

    YAKUMAN = "yakuman"
    TWO_HAN = "2han"
    OFF = "off"


@dataclass
class RulesetConfig:
    """
    Ruleset configuration class.

    Used to configure different rule variations of Riichi Mahjong, supporting standard competitive rules.

    Attributes:
        renhou_policy (RenhouPolicy): Renhou rule.
            - YAKUMAN: Yakuman (13 Han).
            - TWO_HAN: 2 Han (Standard competitive rule).
            - OFF: Disabled.
        pinfu_require_ryanmen (bool): Whether Pinfu requires Ryanmen (Two-sided) wait.
            - True: Must be Ryanmen wait (Standard competitive rule).
            - False: Do not check wait type.
        ippatsu_interrupt_on_meld_or_kan (bool): Whether Ippatsu is interrupted by Meld/Kan.
            - True: Meld or Kan interrupts Ippatsu (Standard competitive rule).
            - False: Do not check interruption condition.
        chanta_enabled (bool): Whether Chanta is enabled.
            - True: Enabled (Standard competitive rule).
            - False: Disabled.
        chanta_open_han (int): Chanta (Open) Han. Default is 1.
        chanta_closed_han (int): Chanta (Closed) Han. Default is 2.
        junchan_open_han (int): Junchan (Open) Han. Default is 2.
        junchan_closed_han (int): Junchan (Closed) Han. Default is 3.
        suuankou_tanki_double (bool): Whether Suuankou Tanki is Double Yakuman.
            - True: Double Yakuman (26 Han, Standard competitive rule).
            - False: Single Yakuman (13 Han).
        chuuren_pure_double (bool): Whether Junsei Chuuren Poutou is Double Yakuman.
            - True: Double Yakuman (26 Han, Standard competitive rule).
            - False: Single Yakuman (13 Han).
        kiriage_mangan (bool): Kiriage Mangan rule.
            - True: 30 Fu 4 Han or 60 Fu 3 Han counts as Mangan (Optional rule).
            - False: Calculate based on normal basic points (Standard competitive rule).
        tobi_enabled (bool): Tobi (Bankruptcy) rule.
            - True: Game ends when player points < 0.
            - False: Game continues until round ends.
        west_round_extension (bool): West Round Extension rule (Enchousen).
            - True: If no one reaches target score (return_score) at end of South 4, enter West round.
            - False: Game ends at end of South 4.
        return_score (int): Return score / Target score.
            - When game ends, if 1st place score is below this score, and West Round Extension is enabled, game extends.
        agari_yame (bool): Agari Yame.
            - True: If Dealer wins in the last round (South 4 or West 4) and is 1st place, game ends.
            - False: Dealer repeats (Renchan), game continues.
        chombo_penalty_enabled (bool): Chombo penalty rule.
            - True: Pay Mangan penalty and end the round when violation occurs.
            - False: Ignore violation or just reject action.
        head_bump_only (bool): Head Bump rule (Only Shimocha wins).
            - True: When multiple players can Ron, only the discarder's Shimocha (closest counter-clockwise) wins.
            - False: Allow multiple Ron (Requires allow_double_ron or allow_triple_ron).
        allow_double_ron (bool): Double Ron rule.
            - True: Allow two players to Ron simultaneously.
            - False: Prohibit Double Ron (May trigger Head Bump or Ryuukyoku).
            Note: Requires head_bump_only = False.
        allow_triple_ron (bool): Triple Ron rule.
            - True: Allow three players to Ron simultaneously.
            - False: Three players Ron leads to Ryuukyoku (Sancha Ron).
            Note: Requires head_bump_only = False and allow_double_ron = True.
    """

    # Renhou Rule
    renhou_policy: RenhouPolicy = RenhouPolicy.TWO_HAN

    # Pinfu Rule
    pinfu_require_ryanmen: bool = True

    # Ippatsu Rule
    ippatsu_interrupt_on_meld_or_kan: bool = True

    # Chanta Rules
    chanta_enabled: bool = True

    chanta_open_han: int = 1
    chanta_closed_han: int = 2
    junchan_open_han: int = 2
    junchan_closed_han: int = 3

    # Suuankou Tanki Rule
    suuankou_tanki_double: bool = True

    # Chuuren Poutou Rule
    chuuren_pure_double: bool = True

    # Kiriage Mangan Rule
    kiriage_mangan: bool = False

    # Tobi Rule
    tobi_enabled: bool = True

    # Game End Rules
    west_round_extension: bool = True

    return_score: int = 30000

    agari_yame: bool = True

    # Violation Penalty Rule
    chombo_penalty_enabled: bool = True

    # Head Bump / Double Ron / Triple Ron Rules
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
            chanta_enabled=True,
            chanta_open_han=1,
            chanta_closed_han=2,
            junchan_open_han=2,
            junchan_closed_han=3,
            suuankou_tanki_double=True,
            chuuren_pure_double=True,
            kiriage_mangan=False,
            tobi_enabled=True,
            west_round_extension=True,
            return_score=30000,
            agari_yame=True,
            chombo_penalty_enabled=True,
        )
