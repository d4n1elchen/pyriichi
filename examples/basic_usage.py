"""
PyRiichi 基本使用示例

展示如何使用 PyRiichi API 進行基本的遊戲操作。
"""

from pyriichi import (
    TileSet,
    Hand,
    RuleEngine,
    GameAction,
    parse_tiles,
    format_tiles,
    YakuChecker,
    ScoreCalculator,
    GameState,
)
from pyriichi.tiles import Tile, Suit


def example_tile_operations():
    """示例：牌的操作"""
    print("=== 牌的操作示例 ===")

    # 創建牌組
    tile_set = TileSet()
    print(f"標準牌組共 {len(tile_set._tiles)} 張牌")

    # 洗牌和發牌
    tile_set.shuffle()
    hands = tile_set.deal()
    print(f"發牌後，玩家 0（莊家）有 {len(hands[0])} 張牌")
    print(f"發牌後，玩家 1-3 各有 {len(hands[1])} 張牌")

    # 使用字符串創建牌
    tiles = parse_tiles("1m2m3m4p5p6p7s8s9s")
    print(f"\n解析牌字符串: {format_tiles(tiles)}")

    print()


def example_hand_operations():
    """示例：手牌操作"""
    print("=== 手牌操作示例 ===")

    # 創建手牌
    tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z2z3z4z")
    hand = Hand(tiles)
    print(f"初始手牌: {format_tiles(hand.tiles)}")

    # 摸牌
    new_tile = Tile(Suit.MANZU, 5)
    hand.add_tile(new_tile)
    print(f"摸到 {new_tile} 後: {format_tiles(hand.tiles)}")

    # 打牌
    hand.discard(new_tile)
    print(f"打出 {new_tile} 後: {format_tiles(hand.tiles)}")

    # 檢查是否門清
    print(f"是否門清: {hand.is_concealed}")

    print()


def example_game_flow():
    """示例：遊戲流程"""
    print("=== 遊戲流程示例 ===")

    # 創建遊戲引擎
    engine = RuleEngine(num_players=4)

    # 開始遊戲
    engine.start_game()
    engine.start_round()

    # 發牌
    hands = engine.deal()
    print(f"發牌完成，當前階段: {engine.get_phase()}")
    print(f"當前玩家: {engine.get_current_player()}")

    # 摸牌
    current_player = engine.get_current_player()
    result = engine.execute_action(current_player, GameAction.DRAW)
    if "drawn_tile" in result:
        print(f"玩家 {current_player} 摸到: {result['drawn_tile']}")

    # 獲取手牌
    hand = engine.get_hand(current_player)
    print(f"玩家 {current_player} 的手牌: {format_tiles(hand.tiles)}")

    # 打牌
    if hand.tiles:
        discard_tile = hand.tiles[0]
        engine.execute_action(current_player, GameAction.DISCARD, tile=discard_tile)
        print(f"玩家 {current_player} 打出: {discard_tile}")

    print(f"下一回合玩家: {engine.get_current_player()}")

    print()


def example_winning_hand_and_scoring():
    """示例：和牌判定、役種檢查和得分計算"""
    print("=== 和牌判定與得分計算示例 ===")

    # 創建一個和牌型手牌（斷么九）
    # 123m 456p 789s 234m 55p（和牌牌5p）
    tiles = parse_tiles("1m2m3m4p5p6p7s8s9s2m3m4m5p")
    hand = Hand(tiles)
    winning_tile = Tile(Suit.PINZU, 5)

    # 1. 檢查是否和牌
    is_winning = hand.is_winning_hand(winning_tile)
    print(f"是否和牌: {is_winning}")

    if is_winning:
        # 2. 獲取和牌組合
        winning_combinations = hand.get_winning_combinations(winning_tile)
        print(f"和牌組合數量: {len(winning_combinations)}")

        if winning_combinations:
            # 注意：get_winning_combinations 返回 List[Tuple]，需要轉換為 List
            winning_combination = list(winning_combinations[0])

            # 3. 檢查役種
            game_state = GameState(num_players=4)
            yaku_checker = YakuChecker()
            yaku_results = yaku_checker.check_all(
                hand=hand,
                winning_tile=winning_tile,
                winning_combination=winning_combination,
                game_state=game_state,
                is_tsumo=True,
                player_position=0,
            )

            print(f"\n役種檢查結果:")
            for yaku in yaku_results:
                print(f"  - {yaku.name}: {yaku.han} 翻")

            # 4. 計算得分
            score_calculator = ScoreCalculator()
            score_result = score_calculator.calculate(
                hand=hand,
                winning_tile=winning_tile,
                winning_combination=winning_combination,
                yaku_results=yaku_results,
                dora_count=0,  # 無寶牌
                game_state=game_state,
                is_tsumo=True,
                player_position=0,
            )

            print(f"\n得分計算結果:")
            print(f"  翻數: {score_result.han}")
            print(f"  符數: {score_result.fu}")
            print(f"  總點數: {score_result.total_points}")
            print(f"  是否役滿: {score_result.is_yakuman}")
            print(f"  是否自摸: {score_result.is_tsumo}")

    print()


if __name__ == "__main__":
    print("PyRiichi 基本使用示例\n")

    example_tile_operations()
    example_hand_operations()
    example_game_flow()
    example_winning_hand_and_scoring()

    print("示例完成！")
