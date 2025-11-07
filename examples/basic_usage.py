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
    Wind,
    RulesetConfig,
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
    if result.drawn_tile is not None:
        print(f"玩家 {current_player} 摸到: {result.drawn_tile}")

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

    # 創建一個和牌型手牌（平和 + 門清自摸）
    # 手牌：1m2m3m 4p5p6p 7s8s9s 2m3m4m 5p（和牌牌5p）
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
            # 默認使用標準競技規則（RulesetConfig.standard()）
            game_state = GameState(num_players=4)
            game_state.set_round(Wind.EAST, 1)  # 東一局
            game_state.set_dealer(0)  # 玩家 0 為莊家

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
                print(f"  - {yaku.name_cn} ({yaku.name}): {yaku.han} 翻")

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
            print(f"  基本點: {score_result.base_points}")
            print(f"  總點數: {score_result.total_points}")
            print(f"  是否役滿: {score_result.is_yakuman}")
            print(f"  是否自摸: {score_result.is_tsumo}")
            if score_result.is_tsumo:
                print(f"  莊家支付: {score_result.dealer_payment}")
                print(f"  閒家支付: {score_result.non_dealer_payment}")

    print()


def example_tenpai():
    """示例：聽牌判定"""
    print("=== 聽牌判定示例 ===")

    # 創建一個聽牌型手牌（聽 1p 和 4p）
    # 手牌結構：123m 456m 789m 123p 4p
    # - 如果摸到 1p：組成 123m 456m 789m 234p 11p（對子）
    # - 如果摸到 4p：組成 123m 456m 789m 123p 44p（對子）
    tiles = parse_tiles("1m2m3m4m5m6m7m8m9m1p2p3p4p")
    hand = Hand(tiles)
    print(f"手牌: {format_tiles(hand.tiles)}")
    print("手牌結構: 123m 456m 789m 123p 4p")

    # 檢查是否聽牌
    if hand.is_tenpai():
        waiting_tiles = hand.get_waiting_tiles()
        print(f"聽牌！等待的牌: {format_tiles(waiting_tiles)}")
        print(f"說明: 摸到以上任意一張牌即可和牌")
    else:
        print("未聽牌")

    print()


def example_meld_operations():
    """示例：鳴牌操作"""
    print("=== 鳴牌操作示例 ===")

    # 創建手牌（包含兩張相同的牌，可以碰）
    # 手牌：1m1m 4p5p6p 7s8s9s 1z2z3z（手牌有兩張1m，可以碰外面的1m）
    tiles = parse_tiles("1m1m4p5p6p7s8s9s1z2z3z")
    hand = Hand(tiles)
    print(f"初始手牌: {format_tiles(hand.tiles)}")

    # 檢查是否可以碰（需要手牌中有兩張相同的牌，然後從外面碰一張）
    tile_to_pon = Tile(Suit.MANZU, 1)
    if hand.can_pon(tile_to_pon):
        meld = hand.pon(tile_to_pon)
        print(f"碰 {tile_to_pon}: {meld}")
        print(f"碰後手牌: {format_tiles(hand.tiles)}")
        print(f"副露: {[str(m) for m in hand.melds]}")
        print(f"是否門清: {hand.is_concealed}")

    # 創建新手牌用於吃示例
    # 手牌：1m2m3m 4p6p7p 8p9p 1s2s3s 4s（可以吃外面的5p，組成4p5p6p）
    tiles2 = parse_tiles("1m2m3m4p6p7p8p9p1s2s3s4s")
    hand2 = Hand(tiles2)
    print(f"\n新手牌: {format_tiles(hand2.tiles)}")

    # 檢查是否可以吃（需要上家的牌）
    tile_to_chi = Tile(Suit.PINZU, 5)  # 可以吃 4p5p6p
    if hand2.can_chi(tile_to_chi, from_player=0):  # 0 表示上家
        sequences = hand2.can_chi(tile_to_chi, from_player=0)
        if sequences:
            meld = hand2.chi(tile_to_chi, sequences[0])
            print(f"吃 {tile_to_chi}: {meld}")
            print(f"吃後手牌: {format_tiles(hand2.tiles)}")
            print(f"副露: {[str(m) for m in hand2.melds]}")
            print(f"是否門清: {hand2.is_concealed}")

    print()


def example_ruleset_configuration():
    """示例：規則配置"""
    print("=== 規則配置示例 ===")

    # 1. 使用默認標準競技規則
    print("1. 默認標準競技規則：")
    game_state_standard = GameState(num_players=4)
    print(f"   - 人和: {game_state_standard.ruleset.renhou_policy} (2翻)")
    print(f"   - 平和需要兩面聽: {game_state_standard.ruleset.pinfu_require_ryanmen}")
    print(f"   - 全帶么九（門清）: {game_state_standard.ruleset.chanta_closed_han}翻")
    print(f"   - 全帶么九（副露）: {game_state_standard.ruleset.chanta_open_han}翻")
    print(
        f"   - 四暗刻單騎: {'雙倍役滿' if game_state_standard.ruleset.suuankou_tanki_is_double_yakuman else '單倍役滿'}"
    )
    print(f"   - 四歸一: {'啟用' if game_state_standard.ruleset.suukantsu_ii_enabled else '不啟用'}")

    # 2. 使用舊版規則
    print("\n2. 舊版規則：")
    legacy_ruleset = RulesetConfig.legacy()
    game_state_legacy = GameState(num_players=4, ruleset=legacy_ruleset)
    print(f"   - 人和: {game_state_legacy.ruleset.renhou_policy} (役滿)")
    print(f"   - 平和需要兩面聽: {game_state_legacy.ruleset.pinfu_require_ryanmen}")
    print(f"   - 全帶么九（門清）: {game_state_legacy.ruleset.chanta_closed_han}翻")
    print(f"   - 全帶么九（副露）: {game_state_legacy.ruleset.chanta_open_han}翻")
    print(
        f"   - 四暗刻單騎: {'雙倍役滿' if game_state_legacy.ruleset.suuankou_tanki_is_double_yakuman else '單倍役滿'}"
    )
    print(f"   - 四歸一: {'啟用' if game_state_legacy.ruleset.suukantsu_ii_enabled else '不啟用'}")

    # 3. 自定義規則配置
    print("\n3. 自定義規則配置：")
    custom_ruleset = RulesetConfig(
        renhou_policy="yakuman",  # 人和為役滿
        pinfu_require_ryanmen=False,  # 平和不檢查兩面聽
        chanta_enabled=True,
        chanta_closed_han=2,
        chanta_open_han=1,
        junchan_closed_han=3,
        junchan_open_han=2,
        suukantsu_ii_enabled=False,
        suuankou_tanki_is_double_yakuman=True,
        chuuren_pure_double=True,
    )
    game_state_custom = GameState(num_players=4, ruleset=custom_ruleset)
    print(f"   - 人和: {game_state_custom.ruleset.renhou_policy}")
    print(f"   - 平和需要兩面聽: {game_state_custom.ruleset.pinfu_require_ryanmen}")

    # 4. 演示規則配置對役種判定的影響
    print("\n4. 規則配置對役種判定的影響：")
    tiles = parse_tiles("1m2m3m4p5p6p7s8s9s2m3m4m5p")
    hand = Hand(tiles)
    winning_tile = Tile(Suit.PINZU, 5)
    combinations = hand.get_winning_combinations(winning_tile)

    if combinations:
        winning_combination = list(combinations[0])
        yaku_checker = YakuChecker()

        # 使用標準規則（人和為2翻）
        game_state_standard.set_round(Wind.EAST, 1)
        game_state_standard.set_dealer(0)
        results_standard = yaku_checker.check_all(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=winning_combination,
            game_state=game_state_standard,
            is_tsumo=False,
            is_first_turn=True,
            player_position=1,  # 閒家
        )
        renhou_standard = [r for r in results_standard if r.name == "人和"]
        if renhou_standard:
            print(f"   標準規則 - 人和: {renhou_standard[0].han}翻 (非役滿)")

        # 使用舊版規則（人和為役滿）
        game_state_legacy.set_round(Wind.EAST, 1)
        game_state_legacy.set_dealer(0)
        results_legacy = yaku_checker.check_all(
            hand=hand,
            winning_tile=winning_tile,
            winning_combination=winning_combination,
            game_state=game_state_legacy,
            is_tsumo=False,
            is_first_turn=True,
            player_position=1,  # 閒家
        )
        renhou_legacy = [r for r in results_legacy if r.name == "人和"]
        if renhou_legacy:
            print(f"   舊版規則 - 人和: {renhou_legacy[0].han}翻 (役滿)")

    print()


if __name__ == "__main__":
    print("PyRiichi 基本使用示例\n")

    example_tile_operations()
    example_hand_operations()
    example_game_flow()
    example_winning_hand_and_scoring()
    example_tenpai()
    example_meld_operations()
    example_ruleset_configuration()

    print("示例完成！")
