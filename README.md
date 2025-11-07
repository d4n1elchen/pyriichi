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
- ⚙️ **規則配置** - 支援標準競技規則和自定義規則配置
- 🔧 **易於整合** - 清晰的 API 設計，易於整合到其他應用程式

## 專案資訊

- **專案狀態**：Development Status :: 3 - Alpha
- **支援關鍵字**：mahjong、riichi、japanese、game、engine
- **首頁**：<https://github.com/d4n1elchen/pyriichi>
- **文件**：<https://github.com/d4n1elchen/pyriichi#readme>
- **問題回報**：<https://github.com/d4n1elchen/pyriichi/issues>
- **原始碼**：<https://github.com/d4n1elchen/pyriichi>

## 安裝

```bash
pip install pyriichi
```

或從源碼安裝：

```bash
git clone https://github.com/d4n1elchen/pyriichi.git
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

#### 字串表示法

PyRiichi 使用簡潔的字串格式來表示麻將牌，方便輸入和顯示：

**基本格式**：`數字 + 花色字母`

- **萬子（MANZU）**：使用 `m` 表示
  - `1m` = 一萬, `2m` = 二萬, ..., `9m` = 九萬

- **筒子（PINZU）**：使用 `p` 表示
  - `1p` = 一筒, `2p` = 二筒, ..., `9p` = 九筒

- **條子（SOZU）**：使用 `s` 表示
  - `1s` = 一條, `2s` = 二條, ..., `9s` = 九條

- **字牌（JIHAI）**：使用 `z` 表示
  - `1z` = 東, `2z` = 南, `3z` = 西, `4z` = 北
  - `5z` = 白, `6z` = 發, `7z` = 中

**紅寶牌表示**：使用 `r` 前綴（標準格式）
- `r5p` = 紅五筒（紅寶牌）
- `r5s` = 紅五條（紅寶牌）
- `r5m` = 紅五萬（紅寶牌）

**注意**：這是日本麻將社區廣泛使用的標準格式，輸入和輸出格式統一為 `r5p`。

**示例**：
```python
from pyriichi import Tile, Suit, TileSet, parse_tiles, format_tiles

# 創建單張牌
tile = Tile(Suit.MANZU, 1)  # 一萬
print(tile)  # 輸出: 1m

# 從字符串解析牌
tiles = parse_tiles("1m2m3m4p5p6p7s8s9s")
print(format_tiles(tiles))  # 輸出: 1m2m3m4p5p6p7s8s9s

# 解析包含紅寶牌的牌（標準格式：r5p）
red_tiles = parse_tiles("r5p6p7p")  # 紅五筒、六筒、七筒
print(format_tiles(red_tiles))  # 輸出: r5p6p7p（格式一致）

# 解析字牌
honor_tiles = parse_tiles("1z2z3z5z6z7z")  # 東南西北白發中
print(format_tiles(honor_tiles))  # 輸出: 1z2z3z5z6z7z

# 創建和洗牌
tile_set = TileSet()
tile_set.shuffle()
hands = tile_set.deal()  # 發牌給 4 個玩家
```

**注意事項**：
- 字串中可以包含空格或其他字符，`parse_tiles()` 會自動跳過無效字符
- 多張牌可以連續寫在一起，例如：`"1m2m3m"` 表示三張萬子
- 使用 `format_tiles()` 可以將牌列表轉換回字串格式
- **紅寶牌格式**：使用標準格式 `r5p`（r 前綴），輸入和輸出格式一致，支持往返轉換

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
if result.drawn_tile is not None:
    print(f"摸到: {result.drawn_tile}")

# 打牌
hand = engine.get_hand(current_player)
if hand.tiles:
    discard_tile = hand.tiles[0]
    engine.execute_action(current_player, GameAction.DISCARD, tile=discard_tile)

# 檢查和牌
winning_result = engine.check_win(current_player, winning_tile)
if winning_result:
    print(f"和牌！翻數: {winning_result.han}, 符數: {winning_result.fu}")
    print(f"得分: {winning_result.points}")
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
        print(f"{result.name_cn} ({result.name}): {result.han} 翻")

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
    print(f"基本點: {score_result.base_points}")
    print(f"總點數: {score_result.total_points}")
    print(f"是否役滿: {score_result.is_yakuman}")
    print(f"是否自摸: {score_result.is_tsumo}")
```

### 遊戲狀態管理

```python
from pyriichi import GameState, Wind

# 創建遊戲狀態（默認使用標準競技規則）
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

### 規則配置

PyRiichi 支援標準競技規則和自定義規則配置：

```python
from pyriichi import GameState, RulesetConfig

# 1. 使用默認標準競技規則
game_state = GameState(num_players=4)
# game_state.ruleset 已經是 RulesetConfig.standard()

# 2. 使用舊版規則（保持向後兼容）
legacy_ruleset = RulesetConfig.legacy()
game_state_legacy = GameState(num_players=4, ruleset=legacy_ruleset)

# 3. 自定義規則配置
custom_ruleset = RulesetConfig(
    renhou_policy="yakuman",  # 人和為役滿
    pinfu_require_ryanmen=False,  # 平和不檢查兩面聽
    chanta_enabled=True,
    chanta_closed_han=2,  # 全帶么九（門清）2翻
    chanta_open_han=1,  # 全帶么九（副露）1翻
    junchan_closed_han=3,  # 純全帶么九（門清）3翻
    junchan_open_han=2,  # 純全帶么九（副露）2翻
    suukantsu_ii_enabled=False,  # 不啟用四歸一
    suuankou_tanki_is_double_yakuman=True,  # 四暗刻單騎為雙倍役滿
    chuuren_pure_double=True,  # 純正九蓮寶燈為雙倍役滿
)
game_state_custom = GameState(num_players=4, ruleset=custom_ruleset)

# 規則配置會影響役種判定
print(f"人和規則: {game_state.ruleset.renhou_policy}")  # 標準: "2han"
print(f"平和需要兩面聽: {game_state.ruleset.pinfu_require_ryanmen}")  # 標準: True
```

**標準競技規則特點**：
- 人和為 2 翻（非役滿）
- 平和必須是兩面聽
- 全帶么九：門清 2 翻，副露 1 翻
- 純全帶么九：門清 3 翻，副露 2 翻
- 四暗刻單騎為雙倍役滿（26 翻）
- 四歸一不啟用

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
    if result.draw:
        # 流局
        print("流局")
        break

    hand = engine.get_hand(current_player)
    drawn_tile = result.drawn_tile

    # 檢查和牌（自摸）
    if drawn_tile:
        win_result = engine.check_win(current_player, drawn_tile)
        if win_result:
            print(f"玩家 {current_player} 自摸！")
            print(f"翻數: {win_result.han}, 符數: {win_result.fu}")
            print(f"得分: {win_result.points}")
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
- **`RulesetConfig`** - 規則配置類，支援標準競技規則和自定義規則

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
- ✅ 規則配置系統（支援標準競技規則和自定義規則）
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

- Python 3.8 至 3.12（官方支援版本）
- 核心功能無其他外部依賴

## 開發與測試

- 建議於虛擬環境中安裝專案依賴
- 安裝完整開發工具：`pip install ".[dev]"`
  - 內容包含：pytest>=7.0.0、pytest-cov>=4.0.0、black>=23.0.0、flake8>=6.0.0、mypy>=1.0.0
- 僅安裝測試工具：`pip install ".[test]"`
  - 內容包含：pytest>=7.0.0、pytest-cov>=4.0.0

## 貢獻

歡迎透過 Issue 與 Pull Request 參與開發，並於 `dev`/`test` 額外依賴協助維護測試品質。

## 授權

本專案採用 MIT 授權條款，詳見 `LICENSE`。

## 相關資源

- [日本麻將規則](https://zh.wikipedia.org/wiki/日本麻雀)
- [役種列表](https://zh.wikipedia.org/wiki/日本麻雀#役)

---

**注意**：本專案正在積極開發中，部分功能可能尚未完全實現。詳情請參考開發計劃文檔。
