"""
PyRiichi 基本使用示例

展示如何使用 PyRiichi API 進行基本的遊戲操作。
"""

from pyriichi import (
    TileSet, Hand, RuleEngine, GameAction,
    parse_tiles, format_tiles
)


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
    from pyriichi.tiles import Tile, Suit
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


if __name__ == "__main__":
    print("PyRiichi 基本使用示例\n")

    example_tile_operations()
    example_hand_operations()
    example_game_flow()

    print("示例完成！")
