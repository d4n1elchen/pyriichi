"""
規則配置系統 - RulesetConfig

管理日本麻將的規則變體配置，支持標準競技規則和自定義規則。
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class RulesetConfig:
    """
    規則配置類

    用於配置日本麻將的不同規則變體，支持標準競技規則。
    """

    # 人和規則
    renhou_policy: Literal["yakuman", "2han", "off"] = "2han"
    """
    人和規則：
    - "yakuman": 役滿（13翻）
    - "2han": 2翻（標準競技規則）
    - "off": 不啟用
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
    suukantsu_ii_enabled: bool = False
    """
    是否啟用四歸一：
    - True: 啟用（非標準規則）
    - False: 不啟用（標準競技規則）
    """

    # 四暗刻單騎規則
    suuankou_tanki_is_double_yakuman: bool = True
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

    @classmethod
    def standard(cls) -> "RulesetConfig":
        """
        創建標準競技規則配置

        Returns:
            標準競技規則配置
        """
        return cls(
            renhou_policy="2han",
            pinfu_require_ryanmen=True,
            ippatsu_interrupt_on_meld_or_kan=True,
            chanta_enabled=True,
            chanta_open_han=1,
            chanta_closed_han=2,
            junchan_open_han=2,
            junchan_closed_han=3,
            suukantsu_ii_enabled=False,
            suuankou_tanki_is_double_yakuman=True,
            chuuren_pure_double=True,
        )

    @classmethod
    def legacy(cls) -> "RulesetConfig":
        """
        創建舊版規則配置（保持向後兼容）

        Returns:
            舊版規則配置
        """
        return cls(
            renhou_policy="yakuman",
            pinfu_require_ryanmen=False,
            ippatsu_interrupt_on_meld_or_kan=False,
            chanta_enabled=False,
            chanta_open_han=2,  # 舊版混全帶么九
            chanta_closed_han=2,
            junchan_open_han=3,  # 舊版純全帶么九
            junchan_closed_han=3,
            suukantsu_ii_enabled=True,
            suuankou_tanki_is_double_yakuman=False,
            chuuren_pure_double=True,
        )
