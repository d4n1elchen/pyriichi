"""
規則配置系統 - RulesetConfig

管理日本麻將的規則變體配置，支持標準競技規則和自定義規則。
"""

from dataclasses import dataclass
from enum import Enum


class RenhouPolicy(str, Enum):
    """人和規則設定"""

    YAKUMAN = "yakuman"
    TWO_HAN = "2han"
    OFF = "off"


@dataclass
class RulesetConfig:
    """
    規則配置類

    用於配置日本麻將的不同規則變體，支持標準競技規則。
    """

    # 人和規則
    renhou_policy: RenhouPolicy = RenhouPolicy.TWO_HAN
    """
    人和規則：
    - RenhouPolicy.YAKUMAN: 役滿（13翻）
    - RenhouPolicy.TWO_HAN: 2翻（標準競技規則）
    - RenhouPolicy.OFF: 不啟用
    """

    # 平和規則
    pinfu_require_ryanmen: bool = True
    """
    平和是否需要兩面聽：
    - True: 必須是兩面聽（標準競技規則）
    - False: 不檢查聽牌類型
    """

    # 一發規則
    ippatsu_interrupt_on_meld_or_kan: bool = True
    """
    一發是否在副露/槓時中斷：
    - True: 副露或槓會中斷一發（標準競技規則）
    - False: 不檢查中斷條件
    """

    # 全帶系規則
    chanta_enabled: bool = True
    """
    是否啟用全帶么九（Chanta）：
    - True: 啟用（標準競技規則）
    - False: 不啟用
    """

    chanta_open_han: int = 1
    """全帶么九（副露）：1翻（標準競技規則）"""

    chanta_closed_han: int = 2
    """全帶么九（門清）：2翻（標準競技規則）"""

    junchan_open_han: int = 2
    """純全帶么九（副露）：2翻（標準競技規則）"""

    junchan_closed_han: int = 3
    """純全帶么九（門清）：3翻（標準競技規則）"""

    # 四歸一規則
    # 四暗刻單騎規則
    suuankou_tanki_double: bool = True
    """
    四暗刻單騎是否為雙倍役滿：
    - True: 雙倍役滿（26翻，標準競技規則）
    - False: 單倍役滿（13翻）
    """

    # 純正九蓮寶燈規則
    chuuren_pure_double: bool = True
    """
    純正九蓮寶燈是否為雙倍役滿：
    - True: 雙倍役滿（26翻，標準競技規則）
    - False: 單倍役滿（13翻）
    """

    # 切上滿貫規則
    kiriage_mangan: bool = False
    """
    切上滿貫規則：
    - True: 30符4翻 或 60符3翻 計為滿貫（可選規則）
    - False: 按正常基本點計算（標準競技規則）
    """

    # 擊飛規則
    tobi_enabled: bool = True
    """
    擊飛規則：
    - True: 當玩家點數 < 0 時遊戲結束
    - False: 遊戲繼續直到局數結束
    """

    # 遊戲結束規則
    west_round_extension: bool = True
    """
    西入規則（延長戰）：
    - True: 若南4局結束時無人達到目標分數（return_score），進入西場
    - False: 南4局結束即遊戲結束
    """

    return_score: int = 30000
    """
    返點/目標分數：
    - 遊戲結束時，若第一名分數未達此分數，且啟用西入，則遊戲延長
    - 西場中若有人達到此分數（且為第一名？通常是只要有人超過即可，或局結束時判斷），遊戲結束
    """

    agari_yame: bool = True
    """
    安可（上がり止め）：
    - True: 莊家在最後一局（南4或西4）和牌且為第一名時，遊戲結束
    - False: 莊家連莊，遊戲繼續
    """

    # 違規處理規則
    chombo_penalty_enabled: bool = True
    """
    錯和/錯立直罰則：
    - True: 發生違規時支付滿貫罰符並結束該局
    - False: 忽略違規或僅拒絕動作
    """

    # 頭跳/雙響/三響規則
    head_bump_only: bool = True
    """
    頭跳規則（只允許下家榮和）：
    - True: 多人可榮和時，只有放銃者下家（逆時針最近者）可以榮和
    - False: 允許多人榮和（需配合 allow_double_ron 或 allow_triple_ron）
    """

    allow_double_ron: bool = False
    """
    雙響規則：
    - True: 允許兩家同時榮和
    - False: 禁止雙響（可能觸發頭跳或流局）
    注意：需要 head_bump_only = False
    """

    allow_triple_ron: bool = False
    """
    三響規則：
    - True: 允許三家同時榮和
    - False: 三家可榮和時導致流局（三家和了）
    注意：需要 head_bump_only = False 且 allow_double_ron = True
    """

    @classmethod
    def standard(cls) -> "RulesetConfig":
        """
        創建標準競技規則配置

        Returns:
            標準競技規則配置
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
