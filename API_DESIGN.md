# PyRiichi API 設計文檔

本文檔定義了 PyRiichi 日本麻將引擎的所有公開 API 接口。

## 1. 牌組系統 API

### 1.1 Tile（牌）

```python
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field

class Suit(Enum):
    """花色"""
    MANZU = "m"      # 萬子
    PINZU = "p"      # 筒子
    SOZU = "s"       # 條子
    JIHAI = "z"      # 字牌

class Tile:
    """單張麻將牌"""

    def __init__(self, suit: Suit, rank: int, is_red: bool = False):
        """
        初始化一張牌

        Args:
            suit: 花色
            rank: 數字（1-9 對數牌，1-7 對字牌）
            is_red: 是否為紅寶牌（默認 False）
        """
        pass

    @property
    def suit(self) -> Suit:
        """獲取花色"""
        pass

    @property
    def rank(self) -> int:
        """獲取數字"""
        pass

    @property
    def is_red(self) -> bool:
        """是否為紅寶牌"""
        pass

    @property
    def is_honor(self) -> bool:
        """是否為字牌"""
        pass

    @property
    def is_terminal(self) -> bool:
        """是否為老頭牌（1 或 9）"""
        pass

    @property
    def is_simple(self) -> bool:
        """是否為中張牌（2-8）"""
        pass

    def __eq__(self, other) -> bool:
        """比較兩張牌是否相同"""
        pass

    def __hash__(self) -> int:
        """哈希值，用於集合和字典"""
        pass

    def __str__(self) -> str:
        """字符串表示（例如：1m, 5p, 東）"""
        pass

    def __repr__(self) -> str:
        """對象表示"""
        pass

# 便利函數
def create_tile(suit: str, rank: int, is_red: bool = False) -> Tile:
    """
    創建一張牌（便捷函數）

    Args:
        suit: 花色字符串 ("m", "p", "s", "z")
        rank: 數字
        is_red: 是否為紅寶牌

    Returns:
        Tile 對象
    """
    pass
```

### 1.2 TileSet（牌組）

```python
from typing import List, Optional

class TileSet:
    """牌組管理器"""

    def __init__(self, tiles: Optional[List[Tile]] = None):
        """
        初始化牌組

        Args:
            tiles: 初始牌列表（如果為 None，則創建標準 136 張牌）
        """
        pass

    def shuffle(self) -> None:
        """洗牌"""
        pass

    def deal(self, num_players: int = 4) -> List[List[Tile]]:
        """
        發牌

        Args:
            num_players: 玩家數量（默認 4）

        Returns:
            每個玩家的手牌列表（13 張），莊家為 14 張
        """
        pass

    def draw(self) -> Optional[Tile]:
        """
        從牌山頂端摸一張牌

        Returns:
            摸到的牌，如果牌山為空則返回 None
        """
        pass

    def draw_wall_tile(self) -> Optional[Tile]:
        """
        從王牌區摸一張牌（用於槓後摸牌）

        Returns:
            摸到的牌，如果王牌區為空則返回 None
        """
        pass

    @property
    def remaining(self) -> int:
        """剩餘牌數"""
        pass

    @property
    def wall_remaining(self) -> int:
        """王牌區剩餘牌數"""
        pass

    def is_exhausted(self) -> bool:
        """檢查牌山是否耗盡"""
        pass

    def get_dora_indicator(self, index: int = 0) -> Optional[Tile]:
        """
        獲取寶牌指示牌

        Args:
            index: 指示牌索引（0 為表寶牌，1+ 為裡寶牌）

        Returns:
            指示牌，如果不存在則返回 None
        """
        pass

    def get_dora(self, indicator: Tile) -> Tile:
        """
        根據指示牌獲取寶牌

        Args:
            indicator: 指示牌

        Returns:
            對應的寶牌
        """
        pass
```

## 2. 手牌管理 API

### 2.1 Meld（副露）

```python
from enum import Enum
from typing import List

class MeldType(Enum):
    """副露類型"""
    CHI = "chi"      # 吃
    PON = "pon"     # 碰
    KAN = "kan"     # 明槓
    ANKAN = "ankan" # 暗槓

class Meld:
    """副露（明刻、明順、明槓、暗槓）"""

    def __init__(self, meld_type: MeldType, tiles: List[Tile], called_tile: Optional[Tile] = None):
        """
        初始化副露

        Args:
            meld_type: 副露類型
            tiles: 副露的牌列表
            called_tile: 被鳴的牌（吃/碰時需要）
        """
        pass

    @property
    def meld_type(self) -> MeldType:
        """獲取副露類型"""
        pass

    @property
    def tiles(self) -> List[Tile]:
        """獲取副露的牌列表"""
        pass

    @property
    def called_tile(self) -> Optional[Tile]:
        """獲取被鳴的牌"""
        pass

    def is_concealed(self) -> bool:
        """是否為暗槓"""
        pass

    def is_open(self) -> bool:
        """是否為明副露"""
        pass
```

### 2.2 Hand（手牌）

```python
from typing import List, Optional, Tuple

class Hand:
    """手牌管理器"""

    def __init__(self, tiles: List[Tile]):
        """
        初始化手牌

        Args:
            tiles: 初始手牌列表（13 或 14 張）
        """
        pass

    def add_tile(self, tile: Tile) -> None:
        """添加一張牌（摸牌）"""
        pass

    def discard(self, tile: Tile) -> bool:
        """
        打出一張牌

        Args:
            tile: 要打出的牌

        Returns:
            是否成功打出
        """
        pass

    def can_chi(self, tile: Tile, from_player: int) -> List[List[Tile]]:
        """
        檢查是否可以吃

        Args:
            tile: 被吃的牌
            from_player: 出牌玩家位置（0=上家，1=對家，2=下家）

        Returns:
            可以組成的順子列表（每個順子包含 3 張牌）
        """
        pass

    def chi(self, tile: Tile, sequence: List[Tile]) -> Meld:
        """
        執行吃操作

        Args:
            tile: 被吃的牌
            sequence: 手牌中的兩張牌（與被吃的牌組成順子）

        Returns:
            創建的 Meld 對象
        """
        pass

    def can_pon(self, tile: Tile) -> bool:
        """
        檢查是否可以碰

        Args:
            tile: 被碰的牌

        Returns:
            是否可以碰
        """
        pass

    def pon(self, tile: Tile) -> Meld:
        """
        執行碰操作

        Args:
            tile: 被碰的牌

        Returns:
            創建的 Meld 對象
        """
        pass

    def can_kan(self, tile: Optional[Tile] = None) -> List[Meld]:
        """
        檢查是否可以槓

        Args:
            tile: 被槓的牌（明槓時需要，暗槓時為 None）

        Returns:
            可以槓的組合列表
        """
        pass

    def kan(self, tile: Optional[Tile], kan_tiles: List[Tile]) -> Meld:
        """
        執行槓操作

        Args:
            tile: 被槓的牌（明槓時需要，暗槓時為 None）
            kan_tiles: 手牌中的三張/四張牌

        Returns:
            創建的 Meld 對象
        """
        pass

    @property
    def tiles(self) -> List[Tile]:
        """獲取當前手牌"""
        pass

    @property
    def melds(self) -> List[Meld]:
        """獲取所有副露"""
        pass

    @property
    def is_concealed(self) -> bool:
        """是否門清（無副露）"""
        pass

    @property
    def is_riichi(self) -> bool:
        """是否立直"""
        pass

    def set_riichi(self, is_riichi: bool = True) -> None:
        """設置立直狀態"""
        pass

    def is_tenpai(self) -> bool:
        """是否聽牌"""
        pass

    def get_waiting_tiles(self) -> List[Tile]:
        """
        獲取聽牌列表

        Returns:
            所有可以和的牌列表
        """
        pass

    def is_winning_hand(self, winning_tile: Tile) -> bool:
        """
        檢查是否可以和牌

        Args:
            winning_tile: 和牌牌

        Returns:
            是否可以和牌
        """
        pass

    def get_winning_combinations(self, winning_tile: Tile) -> List[Tuple]:
        """
        獲取和牌組合（用於役種判定）

        Args:
            winning_tile: 和牌牌

        Returns:
            所有可能的和牌組合（每種組合包含 4 組面子和 1 對子）
            注意：返回的是 List[Tuple]，使用時需要轉換為 List：
            winning_combination = list(combinations[0])
        """
        pass
```

## 3. 役種判定 API

### 3.1 Yaku（役種）

```python
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class YakuResult:
    """役種判定結果"""
    name: str           # 役種名稱（日文）
    name_en: str        # 役種名稱（英文）
    name_cn: str        # 役種名稱（中文）
    han: int           # 翻數
    is_yakuman: bool   # 是否為役滿

class YakuChecker:
    """役種判定器"""

    def check_all(self, hand: Hand, winning_tile: Tile,
                  winning_combination: List,
                  game_state: 'GameState',
                  is_tsumo: bool = False,
                  turns_after_riichi: int = -1,
                  is_first_turn: bool = False,
                  is_last_tile: bool = False,
                  player_position: int = 0,
                  is_rinshan: bool = False) -> List[YakuResult]:
        """
        檢查所有符合的役種

        Args:
            hand: 手牌
            winning_tile: 和牌牌
            winning_combination: 和牌組合（標準型）或 None（特殊型如七對子）
            game_state: 遊戲狀態
            is_tsumo: 是否自摸
            turns_after_riichi: 立直後經過的回合數（-1 表示未立直）
            is_first_turn: 是否為第一巡
            is_last_tile: 是否為最後一張牌（海底撈月/河底撈魚）
            player_position: 玩家位置（用於判定自風）
            is_rinshan: 是否為嶺上開花

        Returns:
            所有符合的役種列表
        """
        pass

    def check_riichi(self, hand: Hand, game_state: 'GameState') -> Optional[YakuResult]:
        """檢查立直"""
        pass

    def check_ippatsu(self, hand: Hand, game_state: 'GameState') -> Optional[YakuResult]:
        """檢查一發"""
        pass

    def check_menzen_tsumo(self, hand: Hand, game_state: 'GameState') -> Optional[YakuResult]:
        """檢查門清自摸"""
        pass

    def check_tanyao(self, hand: Hand, winning_combination: Tuple) -> Optional[YakuResult]:
        """檢查斷么九"""
        pass

    def check_pinfu(self, hand: Hand, winning_combination: Tuple) -> Optional[YakuResult]:
        """檢查平和"""
        pass

    # ... 其他役種檢查方法
```

## 4. 得分計算 API

### 4.1 ScoreCalculator（得分計算器）

```python
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class ScoreResult:
    """得分計算結果"""
    han: int              # 翻數
    fu: int               # 符數
    base_points: int      # 基本點
    total_points: int     # 總點數（自摸時為每人支付）
    payment_from: int     # 支付者位置（榮和時）
    payment_to: int       # 獲得者位置
    is_yakuman: bool      # 是否役滿
    yakuman_count: int    # 役滿倍數
    is_tsumo: bool        # 是否自摸
    dealer_payment: int   # 莊家支付（自摸時）
    non_dealer_payment: int  # 閒家支付（自摸時）
    honba_bonus: int      # 本場獎勵
    riichi_sticks_bonus: int  # 供託分配

class ScoreCalculator:
    """得分計算器"""

    def calculate(self, hand: Hand, winning_tile: Tile,
                  winning_combination: List,
                  yaku_results: List[YakuResult],
                  dora_count: int,
                  game_state: 'GameState',
                  is_tsumo: bool,
                  player_position: int = 0) -> ScoreResult:
        """
        計算得分

        Args:
            hand: 手牌
            winning_tile: 和牌牌
            winning_combination: 和牌組合
            yaku_results: 役種列表
            dora_count: 寶牌數量
            game_state: 遊戲狀態
            is_tsumo: 是否自摸
            player_position: 玩家位置（用於計算自風對子符數）

        Returns:
            得分計算結果
        """
        pass

    def calculate_fu(self, hand: Hand, winning_tile: Tile,
                     winning_combination: List,
                     yaku_results: List[YakuResult],
                     game_state: 'GameState',
                     is_tsumo: bool,
                     player_position: int = 0) -> int:
        """
        計算符數

        Args:
            hand: 手牌
            winning_tile: 和牌牌
            winning_combination: 和牌組合
            yaku_results: 役種列表（用於判斷是否為平和）
            game_state: 遊戲狀態
            is_tsumo: 是否自摸
            player_position: 玩家位置（用於計算自風對子符數）

        Returns:
            符數
        """
        pass

    def calculate_han(self, yaku_results: List[YakuResult],
                     dora_count: int) -> int:
        """
        計算翻數

        Args:
            yaku_results: 役種列表
            dora_count: 寶牌數量

        Returns:
            翻數
        """
        pass
```

## 5. 遊戲狀態 API

### 5.1 Wind（風）

```python
from enum import Enum

class Wind(Enum):
    """風"""
    EAST = "e"   # 東
    SOUTH = "s"  # 南
    WEST = "w"   # 西
    NORTH = "n"  # 北
```

### 5.2 GameState（遊戲狀態）

```python
from typing import List, Optional

class GameState:
    """遊戲狀態管理器"""

    def __init__(self, initial_scores: Optional[List[int]] = None):
        """
        初始化遊戲狀態

        Args:
            initial_scores: 初始點數列表（默認每人 25000）
        """
        pass

    @property
    def round_wind(self) -> Wind:
        """當前局風"""
        pass

    @property
    def round_number(self) -> int:
        """當前局數（1-4）"""
        pass

    @property
    def player_winds(self) -> List[Wind]:
        """每個玩家的自風"""
        pass

    @property
    def dealer(self) -> int:
        """當前莊家位置（0-3）"""
        pass

    @property
    def honba(self) -> int:
        """本場數"""
        pass

    @property
    def riichi_sticks(self) -> int:
        """供託棒數"""
        pass

    @property
    def scores(self) -> List[int]:
        """每個玩家的點數"""
        pass

    def set_round(self, round_wind: Wind, round_number: int) -> None:
        """設置局數"""
        pass

    def set_dealer(self, dealer: int) -> None:
        """設置莊家"""
        pass

    def add_honba(self, count: int = 1) -> None:
        """增加本場數"""
        pass

    def reset_honba(self) -> None:
        """重置本場數"""
        pass

    def add_riichi_stick(self) -> None:
        """增加供託棒"""
        pass

    def clear_riichi_sticks(self) -> None:
        """清除供託棒"""
        pass

    def update_score(self, player: int, points: int) -> None:
        """更新玩家點數"""
        pass

    def transfer_points(self, from_player: int, to_player: int, points: int) -> None:
        """轉移點數"""
        pass

    def next_round(self) -> bool:
        """
        進入下一局

        Returns:
            是否還有下一局（遊戲是否結束）
        """
        pass
```

## 6. 規則引擎 API

### 6.1 RuleEngine（規則引擎）

```python
from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from pyriichi.yaku import YakuResult
from pyriichi.scoring import ScoreResult
from pyriichi.tiles import Tile

class GameAction(Enum):
    """遊戲動作"""
    DRAW = "draw"           # 摸牌
    DISCARD = "discard"     # 打牌
    CHI = "chi"            # 吃
    PON = "pon"            # 碰
    KAN = "kan"            # 槓
    ANKAN = "ankan"        # 暗槓
    RICHI = "riichi"       # 立直
    WIN = "win"            # 和牌
    TSUMO = "tsumo"        # 自摸
    RON = "ron"            # 榮和
    PASS = "pass"          # 過

class GamePhase(Enum):
    """遊戲階段"""
    INIT = "init"          # 初始化
    DEALING = "dealing"    # 發牌
    PLAYING = "playing"    # 遊戲中
    WINNING = "winning"    # 和牌
    DRAW = "draw"          # 流局
    ENDED = "ended"        # 結束

@dataclass
class ActionResult:
    """動作執行結果"""
    drawn_tile: Optional[Tile] = None
    is_last_tile: Optional[bool] = None
    draw: Optional[bool] = None
    draw_type: Optional[DrawType] = None
    discarded: Optional[bool] = None
    riichi: Optional[bool] = None
    chankan: Optional[bool] = None
    winners: List[int] = field(default_factory=list)
    rinshan_tile: Optional[Tile] = None
    kan: Optional[bool] = None
    ankan: Optional[bool] = None
    rinshan_win: Optional["WinResult"] = None

@dataclass
class WinResult:
    """和牌結果"""
    win: bool
    player: int
    yaku: List[YakuResult]
    han: int
    fu: int
    points: int
    score_result: ScoreResult
    chankan: Optional[bool] = None
    rinshan: Optional[bool] = None

@dataclass
class DrawResult:
    """流局結果"""
    draw: bool
    draw_type: Optional[str] = None
    flow_mangan_players: List[int] = field(default_factory=list)
    kyuushu_kyuuhai: Optional[bool] = None
    kyuushu_kyuuhai_player: Optional[int] = None

class RuleEngine:
    """規則引擎"""

    def __init__(self, num_players: int = 4):
        """
        初始化規則引擎

        Args:
            num_players: 玩家數量（默認 4）
        """
        pass

    def start_game(self) -> None:
        """開始新遊戲"""
        pass

    def start_round(self) -> None:
        """開始新一局"""
        pass

    def deal(self) -> Dict[int, List[Tile]]:
        """
        發牌

        Returns:
            每個玩家的手牌字典 {player_id: [tiles]}
        """
        pass

    def get_current_player(self) -> int:
        """獲取當前行動玩家"""
        pass

    def get_phase(self) -> GamePhase:
        """獲取當前遊戲階段"""
        pass

    def can_act(self, player: int, action: GameAction,
                tile: Optional[Tile] = None, **kwargs) -> bool:
        """
        檢查玩家是否可以執行某個動作

        Args:
            player: 玩家位置
            action: 動作類型
            tile: 相關的牌
            **kwargs: 其他參數

        Returns:
            是否可以執行
        """
        pass

    def execute_action(self, player: int, action: GameAction,
                      tile: Optional[Tile] = None, **kwargs) -> ActionResult:
        """
        執行動作

        Args:
            player: 玩家位置
            action: 動作類型
            tile: 相關的牌
            **kwargs: 其他參數（如吃時的順子）

        Returns:
            動作執行結果
        """
        pass

    def check_win(self, player: int, winning_tile: Tile, is_chankan: bool = False, is_rinshan: bool = False) -> Optional[WinResult]:
        """
        檢查是否可以和牌

        Args:
            player: 玩家位置
            winning_tile: 和牌牌

        Returns:
            和牌結果（包含役種、得分等），如果不能和則返回 None
        """
        pass

    def check_draw(self) -> Optional[str]:
        """
        檢查是否流局

        Returns:
            流局類型（如 "kyuushu_kyuuhai", "suufon_renta" 等），否則返回 None
        """
        pass

    def get_hand(self, player: int) -> Hand:
        """獲取玩家的手牌"""
        pass

    def get_game_state(self) -> GameState:
        """獲取遊戲狀態"""
        pass

    def get_discards(self, player: int) -> List[Tile]:
        """獲取玩家的舍牌"""
        pass
```

## 7. 便利函數和工具

### 7.1 工具函數

```python
def parse_tiles(tile_string: str) -> List[Tile]:
    """
    從字符串解析牌（例如："1m2m3m4p5p6p"）

    Args:
        tile_string: 牌字符串

    Returns:
        牌列表
    """
    pass

def format_tiles(tiles: List[Tile]) -> str:
    """
    將牌列表格式化為字符串

    Args:
        tiles: 牌列表

    Returns:
        格式化後的字符串
    """
    pass

def is_winning_hand(tiles: List[Tile], winning_tile: Tile) -> bool:
    """
    快速檢查是否和牌（便利函數）

    Args:
        tiles: 手牌列表（13 張）
        winning_tile: 和牌牌

    Returns:
        是否和牌
    """
    pass
```

## 8. 使用示例

```python
from pyriichi import TileSet, Hand, RuleEngine, GameState, YakuChecker, ScoreCalculator

# 創建遊戲
engine = RuleEngine(num_players=4)
engine.start_game()
engine.start_round()

# 發牌
hands = engine.deal()

# 獲取玩家手牌
player_hand = engine.get_hand(0)

# 摸牌
tile = engine.execute_action(0, GameAction.DRAW)

# 打牌
engine.execute_action(0, GameAction.DISCARD, tile=player_hand.tiles[0])

# 檢查和牌
winning_result = engine.check_win(0, winning_tile)
if winning_result:
    print(f"和牌！翻數: {winning_result.han}, 符數: {winning_result.fu}")
    print(f"得分: {winning_result.points}")
```
