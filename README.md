# PyRiichi - Python 日本麻將引擎

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一個功能完整的 Python 日本麻將（Riichi Mahjong）遊戲引擎，提供完整的規則實現、役種判定、得分計算和遊戲流程管理。

## 功能特色

- 🎴 **完整的牌組系統** - 支援標準 136 張麻將牌，包含紅寶牌和寶牌計算
- 🎯 **和牌判定** - 精確的和牌判定算法，支援標準型和特殊型
- 🏆 **役種系統** - 實現所有標準役種（立直、斷么九、平和等）和役滿
- 💰 **得分計算** - 準確的符數、翻數和點數計算，符合日本麻將規則
- 🎮 **遊戲引擎** - 完整的遊戲流程控制，支援吃、碰、槓、立直等操作
- 📊 **狀態管理** - 局數、風、本場、供託等遊戲狀態管理
- 🔧 **易於整合** - 清晰的 API 設計，易於整合到其他應用程式

## 安裝

```bash
pip install pyriichi
```

或從源碼安裝：

```bash
git clone https://github.com/yourusername/pyriichi.git
cd pyriichi
pip install -e .
```

## 快速開始

### 基本使用

```python
from pyriichi import RuleEngine, GameAction, parse_tiles

# 創建遊戲引擎
engine = RuleEngine(num_players=4)

# 開始新遊戲
engine.start_game()
engine.start_round()

# 發牌
hands = engine.deal()
print(f"發牌完成，當前階段: {engine.get_phase()}")

# 獲取當前玩家手牌
current_player = engine.get_current_player()
hand = engine.get_hand(current_player)
print(f"玩家 {current_player} 的手牌: {hand.tiles}")
```

### 牌的表示和操作

```python
from pyriichi import Tile, Suit, TileSet, parse_tiles, format_tiles

# 創建單張牌
tile = Tile(Suit.MANZU, 1)  # 一萬
print(tile)  # 輸出: 1m

# 從字符串解析牌
tiles = parse_tiles("1m2m3m4p5p6p7s8s9s")
print(format_tiles(tiles))  # 輸出: 1m2m3m4p5p6p7s8s9s

# 創建和洗牌
tile_set = TileSet()
tile_set.shuffle()
hands = tile_set.deal()  # 發牌給 4 個玩家
```

### 遊戲流程控制

```python
from pyriichi import RuleEngine, GameAction

engine = RuleEngine()
engine.start_game()
engine.start_round()
engine.deal()

# 摸牌
current_player = engine.get_current_player()
result = engine.execute_action(current_player, GameAction.DRAW)
if "drawn_tile" in result:
    print(f"摸到: {result['drawn_tile']}")

# 打牌
hand = engine.get_hand(current_player)
if hand.tiles:
    discard_tile = hand.tiles[0]
    engine.execute_action(current_player, GameAction.DISCARD, tile=discard_tile)

# 檢查和牌
winning_result = engine.check_win(current_player, winning_tile)
if winning_result:
    print(f"和牌！翻數: {winning_result['han']}, 符數: {winning_result['fu']}")
    print(f"得分: {winning_result['points']}")
```

### 手牌操作

```python
from pyriichi import Hand, parse_tiles

# 創建手牌
tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z2z3z4z")
hand = Hand(tiles)

# 摸牌
from pyriichi import Tile, Suit
new_tile = Tile(Suit.MANZU, 5)
hand.add_tile(new_tile)

# 打牌
hand.discard(new_tile)

# 檢查聽牌
if hand.is_tenpai():
    waiting_tiles = hand.get_waiting_tiles()
    print(f"聽牌: {waiting_tiles}")

# 檢查和牌
winning_tile = Tile(Suit.MANZU, 1)
if hand.is_winning_hand(winning_tile):
    combinations = hand.get_winning_combinations(winning_tile)
    print(f"和牌組合數量: {len(combinations)}")
    if combinations:
        # 注意：get_winning_combinations 返回 List[Tuple]，需要轉換為 List
        winning_combination = list(combinations[0])
        print("第一個和牌組合:", winning_combination)
```

### 鳴牌操作

```python
from pyriichi import Hand, Tile, Suit

hand = Hand([...])  # 手牌

# 檢查是否可以碰
tile = Tile(Suit.PINZU, 5)
if hand.can_pon(tile):
    meld = hand.pon(tile)
    print(f"碰: {meld}")

# 檢查是否可以吃（只能吃上家的牌）
if hand.can_chi(tile, from_player=0):  # 0 表示上家
    sequences = hand.can_chi(tile, from_player=0)
    if sequences:
        meld = hand.chi(tile, sequences[0])
        print(f"吃: {meld}")
```

### 役種判定

```python
from pyriichi import YakuChecker, Hand, GameState, parse_tiles
from pyriichi.tiles import Tile, Suit

yaku_checker = YakuChecker()
# 創建一個和牌型手牌
tiles = parse_tiles("1m2m3m4p5p6p7s8s9s2m3m4m5p")
hand = Hand(tiles)
winning_tile = Tile(Suit.PINZU, 5)

# 獲取和牌組合（注意：需要轉換為 List）
winning_combinations = hand.get_winning_combinations(winning_tile)
if winning_combinations:
    winning_combination = list(winning_combinations[0])  # 轉換為 List
    
    game_state = GameState(num_players=4)
    
    # 檢查所有役種
    yaku_results = yaku_checker.check_all(
        hand=hand,
        winning_tile=winning_tile,
        winning_combination=winning_combination,
        game_state=game_state,
        is_tsumo=True,
        player_position=0,
    )
    
    for result in yaku_results:
        print(f"{result.name}: {result.han} 翻")

# 檢查特定役種
riichi_result = yaku_checker.check_riichi(hand, game_state)
if riichi_result:
    print(f"立直: {riichi_result.han} 翻")
```

### 得分計算

```python
from pyriichi import ScoreCalculator, YakuChecker, Hand, GameState, parse_tiles
from pyriichi.tiles import Tile, Suit

score_calculator = ScoreCalculator()
yaku_checker = YakuChecker()

# 創建一個和牌型手牌
tiles = parse_tiles("1m2m3m4p5p6p7s8s9s2m3m4m5p")
hand = Hand(tiles)
winning_tile = Tile(Suit.PINZU, 5)

# 獲取和牌組合（注意：需要轉換為 List）
winning_combinations = hand.get_winning_combinations(winning_tile)
if winning_combinations:
    winning_combination = list(winning_combinations[0])  # 轉換為 List
    
    game_state = GameState(num_players=4)
    
    # 先檢查役種
    yaku_results = yaku_checker.check_all(
        hand=hand,
        winning_tile=winning_tile,
        winning_combination=winning_combination,
        game_state=game_state,
        is_tsumo=True,
        player_position=0,
    )
    
    dora_count = 0  # 寶牌數量
    is_tsumo = True  # 是否自摸
    
    # 計算得分
    score_result = score_calculator.calculate(
        hand=hand,
        winning_tile=winning_tile,
        winning_combination=winning_combination,
        yaku_results=yaku_results,
        dora_count=dora_count,
        game_state=game_state,
        is_tsumo=is_tsumo,
        player_position=0,
    )
    
    print(f"翻數: {score_result.han}")
    print(f"符數: {score_result.fu}")
    print(f"總點數: {score_result.total_points}")
    print(f"是否役滿: {score_result.is_yakuman}")
```

### 遊戲狀態管理

```python
from pyriichi import GameState, Wind

# 創建遊戲狀態
game_state = GameState(num_players=4)

# 設置局數
game_state.set_round(Wind.EAST, 1)  # 東一局
game_state.set_dealer(0)  # 玩家 0 為莊家

# 查詢狀態
print(f"當前局: {game_state.round_wind} {game_state.round_number}")
print(f"莊家: 玩家 {game_state.dealer}")
print(f"本場數: {game_state.honba}")
print(f"供託棒: {game_state.riichi_sticks}")

# 更新點數
game_state.update_score(0, 1000)  # 玩家 0 獲得 1000 點
print(f"玩家點數: {game_state.scores}")

# 進入下一局
game_state.next_round()
```

### 完整遊戲示例

```python
from pyriichi import RuleEngine, GameAction, GamePhase

# 初始化遊戲
engine = RuleEngine(num_players=4)
engine.start_game()
engine.start_round()
engine.deal()

# 遊戲主循環
max_turns = 100  # 防止無限循環
turn_count = 0

while engine.get_phase() == GamePhase.PLAYING and turn_count < max_turns:
    turn_count += 1
    current_player = engine.get_current_player()

    # 摸牌
    result = engine.execute_action(current_player, GameAction.DRAW)
    if "draw" in result:
        # 流局
        print("流局")
        break

    hand = engine.get_hand(current_player)
    drawn_tile = result.get("drawn_tile")

    # 檢查和牌（自摸）
    if drawn_tile:
        win_result = engine.check_win(current_player, drawn_tile)
        if win_result:
            print(f"玩家 {current_player} 自摸！")
            print(f"翻數: {win_result['han']}, 符數: {win_result['fu']}")
            print(f"得分: {win_result['points']}")
            break

    # 檢查是否可以立直
    if engine.can_act(current_player, GameAction.RICHI):
        # 這裡可以加入玩家的立直決策邏輯
        # 例如：if hand.is_tenpai() and player_decision():
        pass

    # 打牌（簡單策略：打第一張）
    if hand.tiles:
        discard_tile = hand.tiles[0]
        engine.execute_action(current_player, GameAction.DISCARD, tile=discard_tile)
        print(f"玩家 {current_player} 打出: {discard_tile}")

print("遊戲結束")
```

## 核心 API

### 主要類別

- **`RuleEngine`** - 遊戲規則引擎，管理整個遊戲流程
- **`Hand`** - 手牌管理器，處理手牌操作和判定
- **`TileSet`** - 牌組管理器，處理發牌和洗牌
- **`GameState`** - 遊戲狀態管理器，管理局數、點數等
- **`YakuChecker`** - 役種判定器，檢查所有役種
- **`ScoreCalculator`** - 得分計算器，計算符數、翻數和點數

### 主要枚舉

- **`GameAction`** - 遊戲動作類型（摸牌、打牌、吃、碰等）
- **`GamePhase`** - 遊戲階段（初始化、發牌、遊戲中、結束等）
- **`Suit`** - 花色（萬、筒、條、字）
- **`Wind`** - 風（東、南、西、北）
- **`MeldType`** - 副露類型（吃、碰、槓、暗槓）

### 便利函數

- **`parse_tiles(tile_string)`** - 從字符串解析牌
- **`format_tiles(tiles)`** - 將牌列表格式化為字符串
- **`is_winning_hand(tiles, winning_tile)`** - 快速檢查是否和牌

## 完整功能列表

### 已實現功能

- ✅ 牌組系統（標準 136 張牌）
- ✅ 手牌基本操作（摸牌、打牌）
- ✅ 遊戲流程控制（發牌、回合管理）
- ✅ 遊戲狀態管理（局數、風、點數）
- ✅ 和牌判定算法（支援標準型和特殊型）
- ✅ 聽牌判定
- ✅ 吃、碰、槓操作
- ✅ 役種判定系統（包含所有標準役種和役滿）
- ✅ 得分計算系統（符數、翻數、點數計算）
- ✅ 流局處理（九種九牌等）
- ✅ 基礎 API 架構

### 注意事項

- `get_winning_combinations()` 返回 `List[Tuple]`，在使用時需要轉換為 `List`：
  ```python
  combinations = hand.get_winning_combinations(winning_tile)
  if combinations:
      winning_combination = list(combinations[0])  # 轉換為 List
  ```

## 文檔

- [API 設計文檔](API_DESIGN.md) - 完整的 API 接口定義
- [API 快速參考](API_SUMMARY.md) - API 快速參考指南
- [需求規格](REQUIREMENTS.md) - 詳細的功能需求
- [開發計劃](DEVELOPMENT_PLAN.md) - 開發計劃和時間表

## 範例程式

更多完整範例請查看 `examples/` 目錄：

- `basic_usage.py` - 基本使用示例

## 系統需求

- Python 3.8 或更高版本
- 無其他外部依賴（核心功能）

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 授權

[待定]

## 相關資源

- [日本麻將規則](https://zh.wikipedia.org/wiki/日本麻雀)
- [役種列表](https://zh.wikipedia.org/wiki/日本麻雀#役)

---

**注意**：本專案正在積極開發中，部分功能可能尚未完全實現。詳情請參考開發計劃文檔。
