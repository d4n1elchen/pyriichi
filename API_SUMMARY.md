# PyRiichi API 接口摘要

本文檔提供 PyRiichi API 的快速參考。

## 核心類別

### 1. 牌組系統

#### `Tile`
單張麻將牌
- `suit`: 花色 (Suit)
- `rank`: 數字 (1-9)
- `is_red`: 是否紅寶牌
- `is_honor`: 是否字牌
- `is_terminal`: 是否老頭牌
- `is_simple`: 是否中張牌

#### `TileSet`
牌組管理器
- `shuffle()`: 洗牌
- `deal(num_players=4)`: 發牌
- `draw()`: 摸牌
- `get_dora_indicators(count)`: 獲取寶牌指示牌
- `get_dora(indicator)`: 獲取寶牌

### 2. 手牌管理

#### `Hand`
手牌管理器
- `add_tile(tile)`: 摸牌
- `discard(tile)`: 打牌
- `can_chi(tile, from_player)`: 檢查是否可以吃
- `chi(tile, sequence)`: 執行吃
- `can_pon(tile)`: 檢查是否可以碰
- `pon(tile)`: 執行碰
- `can_kan(tile)`: 檢查是否可以槓
- `kan(tile, kan_tiles)`: 執行槓
- `is_tenpai()`: 是否聽牌
- `is_winning_hand(winning_tile)`: 是否和牌
- `get_winning_combinations(winning_tile, is_tsumo=False)`: 獲取和牌組合

#### `Meld`
副露（明刻、明順、明槓、暗槓）
- `meld_type`: 副露類型
- `tiles`: 牌列表
- `called_tile`: 被鳴的牌

### 3. 遊戲狀態

#### `GameState`
遊戲狀態管理器
- `round_wind`: 當前局風
- `round_number`: 當前局數
- `dealer`: 莊家位置
- `honba`: 本場數
- `riichi_sticks`: 供託棒數
- `scores`: 玩家點數列表
- `set_round(wind, number)`: 設置局數
- `next_round()`: 下一局
- `update_score(player, points)`: 更新點數

### 4. 規則引擎

#### `RuleEngine`
遊戲規則引擎
- `start_game()`: 開始新遊戲
- `start_round()`: 開始新一局
- `deal()`: 發牌
- `get_current_player()`: 獲取當前玩家
- `get_phase()`: 獲取遊戲階段
- `get_available_actions(player)`: 取得玩家可執行的動作列表
- `execute_action(player, action, tile)`: 執行動作
- `check_win(player, winning_tile)`: 檢查和牌
- `check_draw()`: 檢查流局
- `get_hand(player)`: 獲取玩家手牌
- `get_game_state()`: 獲取遊戲狀態
- `waiting_for_actions`: (屬性) 獲取當前等待回應的玩家及其可用動作

#### `ActionResult`
動作執行結果
- `success`: 動作是否成功
- `phase`: 當前遊戲階段
- `drawn_tile`: 摸到的牌 (如果是摸牌動作)
- `discarded`: 是否執行了打牌
- `winners`: 和牌玩家列表
- `win_results`: 和牌結果詳情
- `ryuukyoku`: 是否流局
- `waiting_for`: 等待回應的玩家及其動作 (Dict[int, List[GameAction]])

#### `GameAction` (枚舉)
遊戲動作類型
- `DRAW`: 摸牌 (通常自動執行，除非特殊情況)
- `DISCARD`: 打牌
- `CHI`: 吃
- `PON`: 碰
- `KAN`: 槓
- `ANKAN`: 暗槓
- `RICHI`: 立直
- `WIN`: 和牌
- `TSUMO`: 自摸
- `RON`: 榮和
- `PASS`: 過 (用於放棄鳴牌或榮和機會)

#### `GamePhase` (枚舉)
遊戲階段
- `INIT`: 初始化
- `DEALING`: 發牌
- `PLAYING`: 遊戲中
- `WINNING`: 和牌
- `DRAW`: 流局
- `ENDED`: 結束

### 5. 役種判定

#### `YakuChecker`
役種判定器
- `check_all(hand, winning_tile, winning_combination, game_state, is_tsumo=False, is_ippatsu=False, is_first_turn=False, is_last_tile=False, player_position=0, is_rinshan=False)`: 檢查所有役種
- `check_riichi(hand, game_state, is_ippatsu=False)`: 檢查立直與一發
- `check_tanyao(hand, winning_combination)`: 檢查斷么九
- `check_pinfu(hand, winning_combination)`: 檢查平和
- 其他役種檢查方法...

#### `YakuResult`
役種判定結果
- `name`: 役種名稱（日文）
- `name_en`: 役種名稱（英文）
- `name_cn`: 役種名稱（中文）
- `han`: 翻數
- `is_yakuman`: 是否役滿

### 6. 得分計算

#### `ScoreCalculator`
得分計算器
- `calculate(hand, winning_tile, winning_combination, yaku_results, dora_count, game_state, is_tsumo, player_position=0)`: 計算得分
- `calculate_fu(hand, winning_tile, winning_combination, yaku_results, game_state, is_tsumo, player_position=0)`: 計算符數
- `calculate_han(yaku_results, dora_count)`: 計算翻數

#### `ScoreResult`
得分計算結果
- `han`: 翻數
- `fu`: 符數
- `base_points`: 基本點
- `total_points`: 總點數
- `payment_from`: 支付者位置
- `payment_to`: 獲得者位置
- `is_yakuman`: 是否役滿
- `yakuman_count`: 役滿倍數
- `is_tsumo`: 是否自摸
- `dealer_payment`: 莊家支付（自摸時）
- `non_dealer_payment`: 閒家支付（自摸時）
- `honba_bonus`: 本場獎勵
- `riichi_sticks_bonus`: 供託分配

### 7. AI 玩家系統

#### `BasePlayer`
玩家基類 (Abstract Base Class)
- `decide_action(game_state, player_index, hand, available_actions, public_info)`: 決定下一步動作

#### `RandomPlayer`
隨機行動 AI
- 策略：隨機選擇合法動作，優先和牌

#### `SimplePlayer`
簡單啟發式 AI
- 策略：優先和牌 > 優先立直 > 切字牌/老頭牌

#### `DefensivePlayer`
防守型 AI
- 策略：有人立直時優先切現物（安全牌），否則同 `SimplePlayer`

#### `PublicInfo`
公開遊戲資訊
- `discards`: 各家捨牌
- `melds`: 各家副露
- `riichi_players`: 立直玩家列表

## 便利函數

### `parse_tiles(tile_string)`
從字符串解析牌
```python
tiles = parse_tiles("1m2m3m4p5p6p")
```

### `format_tiles(tiles)`
將牌列表格式化為字符串
```python
s = format_tiles([Tile(Suit.MANZU, 1), Tile(Suit.PINZU, 5)])
```

### `is_winning_hand(tiles, winning_tile)`
快速檢查是否和牌
```python
if is_winning_hand(tiles, winning_tile):
    print("和牌！")
```

## 使用示例

```python
from pyriichi.rules import RuleEngine, GameAction, GamePhase
from pyriichi.player import RandomPlayer

# 初始化遊戲與玩家
engine = RuleEngine(num_players=4)
players = [RandomPlayer(f"Player {i}") for i in range(4)]

engine.start_game()
engine.start_round()
engine.deal()

# 遊戲主循環
while engine.get_phase() == GamePhase.PLAYING:
    current_player_idx = engine.get_current_player()
    player = players[current_player_idx]

    # 獲取可用動作
    actions = engine.get_available_actions(current_player_idx)
    if not actions: break

    # AI 決定動作
    action, tile = player.decide_action(
        engine.game_state,
        current_player_idx,
        engine.get_hand(current_player_idx),
        actions
    )

    # 執行動作
    engine.execute_action(current_player_idx, action, tile)
```

## 詳細文檔

完整 API 文檔請參考 `API_DESIGN.md`。
