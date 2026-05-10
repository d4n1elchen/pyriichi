"""Winning and scoring tests for RuleEngine."""

from pyriichi.hand import Hand, Meld, MeldType
from pyriichi.rules import GameAction, GamePhase
from pyriichi.tiles import Suit, Tile
from pyriichi.utils import parse_tiles
from pyriichi.yaku import Yaku
from tests.helpers import (
    RuleEngineTestMixin,
    no_response_hand,
    set_non_matching_scoring_dora,
)


def _score_deltas(initial_scores, current_scores):
    return [current - initial for current, initial in zip(current_scores, initial_scores)]


class TestWinningAndScoring(RuleEngineTestMixin):
    def test_check_chankan(self):
        """Test chankan check"""
        self._init_game()
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)

        # Set Player 0 can chankan (machi 6p, tanyao)
        # hand: 234m 567m 234p 66p 78p (machi 6p/9p)
        test_tiles = parse_tiles("234567m2346678p")
        self.engine._hands[0] = Hand(test_tiles)

        # Check chankan
        kan_tile = Tile(Suit.PINZU, 6)

        # check_win needs pending_kan_tile to set payer
        # Assume Player 1 open_kan 6p
        self.engine._pending_kan_tile = (1, kan_tile)

        result = self.engine.check_win(0, kan_tile, is_chankan=True)
        assert result is not None
        assert result.win is True
        assert result.chankan is True
        assert {y.yaku for y in result.yaku} == {Yaku.CHANKAN, Yaku.TANYAO}
        assert result.score_result.payment_from == 1

    def test_false_tsumo_applies_chombo(self):
        """Test false tsumo applies chombo."""
        self._init_game()
        player = 1
        self.engine._game_state.set_dealer(0)
        self.engine._hands[player] = Hand(parse_tiles("124578m1245p78s1z"))
        tile = Tile(Suit.HONORS, 1)
        self.engine._hands[player].add_tile(tile)
        initial_scores = self.engine._game_state.scores.copy()

        result = self.engine._handle_tsumo(player, tile=tile)

        assert result.chombo is True
        assert result.chombo_player == player
        assert self.engine.get_phase() == GamePhase.RYUUKYOKU
        assert self.engine._game_state.scores[player] == initial_scores[player] - 8000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 4000

    def test_false_ron_applies_chombo(self):
        """Test false ron applies chombo."""
        self._init_game()
        player = 1
        self.engine._game_state.set_dealer(0)
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._hands[player] = Hand(parse_tiles("124578m1245p78s1z"))
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 0
        initial_scores = self.engine._game_state.scores.copy()

        result = self.engine._handle_ron(player)

        assert result.chombo is True
        assert result.chombo_player == player
        assert self.engine.get_phase() == GamePhase.RYUUKYOKU
        assert self.engine._game_state.scores[player] == initial_scores[player] - 8000
        assert self.engine._game_state.scores[0] == initial_scores[0] + 4000

    def test_check_win_rinshan(self):
        """Test rinshan win check"""
        self._init_game()
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)
        # Set a hand that can win on rinshan
        # Create a winning hand
        # hand: 123m 456m 789m 123p 4p (rinshan tile 4p)
        self.engine._hands[0] = Hand(parse_tiles("123456789m12344p"))
        self.engine._current_player = 0

        # Check rinshan win
        rinshan_tile = Tile(Suit.PINZU, 4)
        result = self.engine.check_win(0, rinshan_tile, is_rinshan=True)
        assert result is not None
        assert result.win is True
        assert result.rinshan is True
        assert {y.yaku for y in result.yaku} == {
            Yaku.MENZEN_TSUMO,
            Yaku.RINSHAN,
            Yaku.ITTSU,
        }
        assert result.score_result.is_tsumo is True

    def test_check_win_tsumo_sets_is_tsumo(self):
        """Test Tumo sets score_result.is_tsumo to True"""
        self._init_game()
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)
        player = self.engine.get_current_player()
        winning_tile = Tile(Suit.PINZU, 4)
        # Concealed hand: 123m 456m 789m 123p + 4p
        self.engine._hands[player] = Hand(parse_tiles("123456789m12344p"))
        # Simulate just drawn winning tile
        self.engine._last_drawn_tile = (player, winning_tile)
        result = self.engine.check_win(player, winning_tile)
        assert result is not None
        assert {y.yaku for y in result.yaku} == {Yaku.MENZEN_TSUMO, Yaku.ITTSU}
        assert result.score_result.is_tsumo is True
        assert result.score_result.payment_from == 0

    def test_check_win_ron_when_turn_passes(self):
        """Test ron after other player discards is not mistaken for tsumo"""
        self._init_game()
        discarder = 0
        winner = (discarder + 1) % self.engine.get_num_players()
        winning_tile = Tile(Suit.PINZU, 4)
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)
        self.engine._hands[winner] = Hand(parse_tiles("123456789m1234p"))
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = discarder
        # Simulate turn passed to next player (actually ron state)
        self.engine._current_player = winner
        self.engine._last_drawn_tile = None
        result = self.engine.check_win(winner, winning_tile)
        assert result is not None
        assert {y.yaku for y in result.yaku} == {Yaku.ITTSU}
        assert result.score_result.is_tsumo is False
        assert result.score_result.payment_from == discarder

    def test_check_win_no_combinations(self):
        """Test check_win with no winning combinations"""
        self._init_game()
        # Create a non-winning hand
        # 123m 456m 78m 123p 45p
        test_tiles = parse_tiles("12345678m12345p")
        test_hand = Hand(test_tiles)
        self.engine._hands[0] = test_hand

        # Check win (Should return None because no winning combinations)
        winning_tile = Tile(Suit.MANZU, 9)
        result = self.engine.check_win(0, winning_tile)
        assert result is None

    def test_check_win_no_yaku(self):
        """Test No yaku"""
        self._init_game()
        # 234m 567m 789m 2p 4p 22s
        tiles = parse_tiles("234567789m24p22s")

        hand = Hand(tiles)
        # Set hand to not concealed
        hand._melds.append(Meld(MeldType.PON_MELD, parse_tiles("1s1s1s")))
        # Set last discard to 3p, test ron
        winning_tile = Tile(Suit.PINZU, 3)
        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1

        self.engine._last_discarded_player = 1

        # Set hand to player 0
        self.engine._hands[0] = hand
        self.engine._current_player = 2

        # Check win (Not concealed and no other yaku, should return None)
        result = self.engine.check_win(0, winning_tile)
        assert result is None

    def test_count_dora_zero(self):
        """Test zero dora count"""
        self._init_game()
        set_non_matching_scoring_dora(self.engine)
        self.engine._hands[0] = Hand(parse_tiles("1111234567999m"))
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count == 0

    def test_count_dora_one(self):
        """Test dora count"""
        self._init_game()
        test_hand = Hand(parse_tiles("1111234567999m"))
        self.engine._hands[0] = test_hand
        self.engine._tile_set._dora_indicators = [Tile(Suit.MANZU, 9)]
        self.engine._tile_set._ura_dora_indicators = [Tile(Suit.PINZU, 9)]
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count == 5

        # Test ura_dora when riichi
        test_hand.set_riichi(True)
        self.engine._tile_set._ura_dora_indicators = [Tile(Suit.MANZU, 9)]
        dora_count = self.engine._count_dora(0, Tile(Suit.MANZU, 1))
        assert dora_count == 10

        # Test red_dora
        # hand: r5p
        red_dora_tiles = parse_tiles("r5p")

        test_hand = Hand(red_dora_tiles)
        self.engine._hands[0] = test_hand
        set_non_matching_scoring_dora(self.engine)
        dora_count = self.engine._count_dora(0, Tile(Suit.PINZU, 5))
        assert dora_count == 1

    def test_count_dora_uses_initial_and_kan_indicators(self):
        """Test dora count uses initial and kan indicators."""
        self._init_game()
        self.engine._hands[0] = Hand(parse_tiles("5m5p123456789s1z"))
        self.engine._tile_set._dora_indicators = [
            Tile(Suit.MANZU, 4),
            Tile(Suit.PINZU, 4),
        ]

        self.engine._kan_count = 0
        assert self.engine._count_dora(0) == 1

        self.engine._kan_count = 1
        assert self.engine._count_dora(0) == 2

    def test_count_ura_dora_uses_initial_indicator(self):
        """Test ura_dora count uses the initial indicator."""
        self._init_game()
        self.engine._hands[0] = Hand(parse_tiles("5m123456789s123p"))
        self.engine._hands[0].set_riichi(True)
        self.engine._tile_set._dora_indicators = [Tile(Suit.PINZU, 8)]
        self.engine._tile_set._ura_dora_indicators = [Tile(Suit.MANZU, 4)]

        assert self.engine._count_dora(0) == 1

    def test_pao_daisangen_tsumo(self):
        """Test pao: daisangen tsumo, pao player pays all"""
        self._init_game()

        # Player 0: daisangen tenpai (pon haku, hatsu)
        # hand: 11m 99m
        # Melds: haku haku haku, hatsu hatsu hatsu
        # Simulate meld state
        # Assume Player 1 discards haku, Player 0 pons
        # Assume Player 2 discards hatsu, Player 0 pons
        # Assume Player 3 discards chun, Player 0 pons (Triggers pao)

        # For testing, we need to manually set state because _handle_pon doesn't implement pao logic yet
        # But we are writing tests, so we assume it works, or we manually set _pao_daisangen

        # Set Player 0 hand
        # For tsumo, hand must contain winning tile (Total 14 tiles)
        # 3 Melds (9 tiles) + 5 tiles = 14 tiles
        # hand: 1m1m1m 9m9m (Winning tile 1m is already in hand for is_winning_hand check)
        self.engine._hands[0] = Hand(parse_tiles("11199m"))  # 111m 99m

        # Set Melds
        meld_haku = Meld(
            MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, 1
        )  # pon haku (from 1)
        meld_hatsu = Meld(
            MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, 2
        )  # pon hatsu (from 2)
        meld_chun = Meld(
            MeldType.PON_MELD, [Tile(Suit.HONORS, 7)] * 3, 3
        )  # pon chun (from 3) - Triggers pao

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # Set pao state (Player 3 is pao)
        # Note: This requires adding _pao_daisangen attribute in rules.py
        # Since attribute is not added yet, this will error, which is expected
        self.engine._pao_daisangen[0] = 3

        # Player 0 tsumo 1m (This tile is already in hand for is_winning_hand check)
        winning_tile = Tile(Suit.MANZU, 1)
        self.engine._current_player = 0
        self.engine._last_drawn_tile = (0, winning_tile)

        # Record initial scores
        initial_scores = self.engine._game_state.scores.copy()

        # Execute tsumo
        # We need to call check_win to ensure it is daisangen
        result = self.engine.check_win(0, winning_tile)
        assert result is not None, "check_win should return a result"
        assert result.win
        assert any(y.yaku == Yaku.DAISANGEN for y in result.yaku)

        # Apply score
        self.engine.apply_win_score(result)

        # Execute end_round
        self.engine.end_round([0])

        # Verify score changes
        # daisangen tsumo: 32000 (dealer 48000)
        # Here is dealer (Player 0 is dealer initially) -> 48000
        # pao player (Player 3) pays all 48000

        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[0] > 0
        assert score_deltas[3] == -score_deltas[0]
        assert score_deltas[1] == 0
        assert score_deltas[2] == 0

    def test_pao_daisangen_tracks_final_dragon_call(self):
        """Test pao_daisangen tracks final dragon call."""
        self._init_game()
        player = 0
        responsible_player = 3
        called_tile = Tile(Suit.HONORS, 7)
        hand = Hand(parse_tiles("77z123m456p789s1m"))
        hand._melds = [
            Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, called_tile=Tile(Suit.HONORS, 5)),
            Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, called_tile=Tile(Suit.HONORS, 6)),
        ]
        self.engine._hands[player] = hand
        self.engine._hands[responsible_player]._discards = [called_tile]
        self.engine._last_discarded_tile = called_tile
        self.engine._last_discarded_player = responsible_player

        self.engine._handle_pon(player)

        assert self.engine._pao_daisangen[player] == responsible_player

    def test_pao_daisuushi_tracks_final_wind_call(self):
        """Test pao_daisuushi tracks final wind call."""
        self._init_game()
        player = 0
        responsible_player = 2
        called_tile = Tile(Suit.HONORS, 4)
        hand = Hand(parse_tiles("44z123m456p789s1m"))
        hand._melds = [
            Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 1)] * 3, called_tile=Tile(Suit.HONORS, 1)),
            Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 2)] * 3, called_tile=Tile(Suit.HONORS, 2)),
            Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 3)] * 3, called_tile=Tile(Suit.HONORS, 3)),
        ]
        self.engine._hands[player] = hand
        self.engine._hands[responsible_player]._discards = [called_tile]
        self.engine._last_discarded_tile = called_tile
        self.engine._last_discarded_player = responsible_player

        self.engine._handle_pon(player)

        assert self.engine._pao_daisuushi[player] == responsible_player

    def test_pao_daisangen_ron_pao_player(self):
        """Test pao: daisangen ron pao player (normal payment)"""
        self._init_game()

        # Set Player 0 hand
        self.engine._hands[0] = Hand(parse_tiles("1199m"))

        # Set Melds
        meld_haku = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, 2)
        meld_chun = Meld(
            MeldType.PON_MELD, [Tile(Suit.HONORS, 7)] * 3, 3
        )  # pon chun (from 3) - Triggers pao

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # Set pao state (Player 3 is pao)
        self.engine._pao_daisangen[0] = 3

        # Player 3 discards chun (pao player deals in)
        # winning_tile = Tile(Suit.HONORS, 7) # Actually should discard 1m or 5z, because 5z is already ponned, so discard 1m
        # The hand is 11m 55z after ponning 567z.
        # tenpai should be 1m and 5z by shabo.
        # 13 tiles: 3*3=9 tiles melded, remains 4 tiles.
        # 11m 55z -> machi 1m, 5z (Shanpon)
        # Assume Player 3 discards 1m
        winning_tile = Tile(Suit.MANZU, 1)

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 3
        self.engine._current_player = 0

        initial_scores = self.engine._game_state.scores.copy()

        # Execute ron
        result = self.engine.check_win(0, winning_tile)
        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[0] > 0
        assert score_deltas[3] == -score_deltas[0]
        assert score_deltas[1] == 0
        assert score_deltas[2] == 0

    def test_pao_daisangen_ron_other(self):
        """Test pao: daisangen ron other (pao player and Deal-in player split)"""
        self._init_game()

        # Set Player 0 hand
        # 3 Melds (9 tiles) + 4 tiles = 13 tiles
        # hand: 1m1m 9m9m
        self.engine._hands[0] = Hand(parse_tiles("1199m"))

        # Set Melds
        meld_haku = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 5)] * 3, 1)
        meld_hatsu = Meld(MeldType.PON_MELD, [Tile(Suit.HONORS, 6)] * 3, 2)
        meld_chun = Meld(
            MeldType.PON_MELD, [Tile(Suit.HONORS, 7)] * 3, 3
        )  # pon chun (from 3) - Triggers pao

        self.engine._hands[0]._melds = [meld_haku, meld_hatsu, meld_chun]

        # Set pao state (Player 3 is pao)
        self.engine._pao_daisangen[0] = 3

        # Player 1 discards 1m (Non-pao player deals in)
        winning_tile = Tile(Suit.MANZU, 1)

        self.engine._last_discarded_tile = winning_tile
        self.engine._last_discarded_player = 1
        self.engine._current_player = 0

        initial_scores = self.engine._game_state.scores.copy()

        # Execute ron
        result = self.engine.check_win(0, winning_tile)
        self.engine.apply_win_score(result)
        self.engine.end_round([0])

        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[0] > 0
        assert score_deltas[1] == score_deltas[3]
        assert score_deltas[1] < 0
        assert score_deltas[0] == -(score_deltas[1] + score_deltas[3])
        assert score_deltas[2] == 0

    # ==================== head_bump / double_ron / triple_ron Tests ====================

    def test_head_bump_only_shimocha_wins(self):
        """Test head_bump: shimocha and kamicha can ron, only shimocha wins"""
        self._init_game()

        # Ensure head_bump mode (default)
        assert self.engine._game_state.ruleset.head_bump_only

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Player 1 (shimocha) and Player 3 (kamicha) can ron 1m
        # hand should have 13 tiles, becomes 14 after ron
        self.engine._hands[1] = Hand(parse_tiles("23456789m12344p"))  # 13 tiles
        self.engine._hands[3] = Hand(parse_tiles("23456789m12344p"))  # 13 tiles

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # In head_bump mode, when multiple players can ron, only shimocha (Player 1) wins
        assert len(winners) == 1
        assert winners[0] == 1  # Only Player 1 (shimocha)

    def test_head_bump_only_toimen_blocked(self):
        """Test head_bump: toimen can ron but blocked"""
        self._init_game()

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Only Player 2 (toimen) can ron
        self.engine._hands[2] = Hand(parse_tiles("23456789m12344p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # If only one player can ron, head_bump doesn't apply, player wins normally
        assert len(winners) == 1
        assert winners[0] == 2  # Only Player 2 can ron, returns normally

    def test_head_bump_only_kamicha_blocked(self):
        """Test head_bump: kamicha can ron but blocked"""
        self._init_game()

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Only Player 3 (kamicha) can ron
        self.engine._hands[3] = Hand(parse_tiles("23456789m12344p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # If only one player can ron, head_bump doesn't apply, player wins normally
        assert len(winners) == 1
        assert winners[0] == 3

    def test_double_ron_both_win(self):
        """Test double_ron: Two players win simultaneously"""
        self._init_game()

        # Enable double_ron mode
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 1m
        discard_tile = Tile(Suit.MANZU, 1)

        # Player 1 (shimocha) and Player 2 (toimen) can ron
        self.engine._hands[1] = Hand(parse_tiles("23456789m12344p"))
        self.engine._hands[2] = Hand(parse_tiles("23456789m12344p"))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Test check_multiple_ron
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # In double_ron mode, both players can win
        assert len(winners) == 2
        assert 1 in winners
        assert 2 in winners
        # Order should be counter-clockwise (shimocha first)
        assert winners[0] == 1
        assert winners[1] == 2

    def test_double_ron_score_calculation(self):
        """Test double_ron: Verify deal-in player pays both"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 4p
        discard_tile = Tile(Suit.PINZU, 4)

        # Set Player 1 and 2 hands (tanyao pinfu)
        # 234m 567m 234p 56p 88s (machi 4p/7p)
        # 30 fu 2 han = 2000 points (non-dealer)
        hand_tiles = parse_tiles("234567m23456p88s")
        self.engine._hands[1] = Hand(hand_tiles)
        self.engine._hands[2] = Hand(hand_tiles)

        self.engine._current_player = 0
        set_non_matching_scoring_dora(self.engine)

        # Disable renhou by simulating that it's not the first turn
        # This ensures we test standard yaku (tanyao + pinfu) scoring
        self.engine._is_first_turn_after_deal = False

        initial_scores = self.engine._game_state.scores.copy()

        # Player 0 discards 4p
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)

        # Execute double_ron
        self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        result = self.engine.execute_action(2, GameAction.RON, tile=discard_tile)

        # Verify results
        assert result.success
        assert len(result.winners) == 2

        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[1] > 0
        assert score_deltas[2] == score_deltas[1]
        assert score_deltas[0] == -(score_deltas[1] + score_deltas[2])

    def test_double_ron_uses_score_result_settlement(self):
        """Test double_ron uses score_result settlement."""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True
        self.engine._game_state._honba = 1
        self.engine._game_state.add_riichi_stick()

        discard_tile = Tile(Suit.PINZU, 4)
        hand_tiles = parse_tiles("234567m23456p88s")
        self.engine._hands[1] = Hand(hand_tiles)
        self.engine._hands[2] = Hand(hand_tiles)
        self.engine._current_player = 0
        self.engine._is_first_turn_after_deal = False
        set_non_matching_scoring_dora(self.engine)

        initial_scores = self.engine._game_state.scores.copy()
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)
        self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        result = self.engine.execute_action(2, GameAction.RON, tile=discard_tile)

        assert result.success
        assert sorted(result.winners) == [1, 2]
        assert self.engine._game_state.riichi_sticks == 0
        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[1] > score_deltas[2] > 0
        assert score_deltas[1] - score_deltas[2] == 1000
        assert sum(score_deltas) == 1000

    def test_double_ron_dealer_renchan(self):
        """Test double_ron: dealer win leads to renchan"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Set dealer to Player 0
        self.engine._game_state._dealer = 0
        self.engine._game_state._round_number = 1
        self.engine._game_state._honba = 0

        # Player 1 discards 5p
        discard_tile = Tile(Suit.PINZU, 5)

        # Player 0 (dealer) and Player 2 (non-dealer) ron
        hand_str = "233445678m2345p"
        self.engine._hands[0] = Hand(parse_tiles(hand_str))
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[3] = no_response_hand()

        # Player 1 discards 5p
        self.engine._current_player = 1
        self.engine._hands[1]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {1: self.engine._calculate_turn_actions(1)}
        self.engine.execute_action(1, GameAction.DISCARD, discard_tile)

        # Execute ron
        self.engine.execute_action(0, GameAction.RON, tile=discard_tile)
        result = self.engine.execute_action(2, GameAction.RON, tile=discard_tile)

        assert result.success
        assert sorted(result.winners) == [0, 2]

    def test_triple_ron_enabled_all_win(self):
        """Test triple_ron enabled: All three players win"""
        self._init_game()
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True
        self.engine._game_state.ruleset.allow_triple_ron = True
        self.engine._is_first_turn_after_deal = False

        # Player 0 discards 5p, Player 1, 2, 3 all ron with tanyao
        discard_tile = Tile(Suit.PINZU, 5)

        # 234m 345m 678m 234p 5p (machi 5p)
        hand_str = "233445678m2345p"
        self.engine._hands[1] = Hand(parse_tiles(hand_str))
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[3] = Hand(parse_tiles(hand_str))
        set_non_matching_scoring_dora(self.engine)

        initial_scores = self.engine._game_state.scores.copy()

        # Execute triple_ron
        # Player 0 discards 5p
        self.engine._current_player = 0
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)

        # Player 1 ron
        self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        # Player 2 ron
        self.engine.execute_action(2, GameAction.RON, tile=discard_tile)
        # Player 3 ron (triggers resolution)
        result = self.engine.execute_action(3, GameAction.RON, tile=discard_tile)

        assert result.success
        assert sorted(result.winners) == [1, 2, 3]
        score_deltas = _score_deltas(initial_scores, self.engine._game_state.scores)
        assert score_deltas[1] > 0
        assert score_deltas[2] == score_deltas[1]
        assert score_deltas[3] == score_deltas[1]
        assert score_deltas[0] == -sum(score_deltas[1:])

    def test_double_ron_with_furiten(self):
        """Test double_ron with furiten: One player furiten, only other player wins"""
        self._init_game()

        # Enable double_ron mode
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 5p
        discard_tile = Tile(Suit.PINZU, 5)

        # 234m 345m 678m 234p 5p (machi 5p) - tanyao
        hand_str = "233445678m2345p"

        # Player 1 can ron
        self.engine._hands[1] = Hand(parse_tiles(hand_str))

        # Player 2 can ron but is furiten
        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[2]._discards.append(
            discard_tile
        )  # Discarded 5p, genbutsu furiten

        # Player 0 discards 5p
        self.engine._current_player = 0
        self.engine._hands[0]._tiles.append(discard_tile)
        self.engine._waiting_for_actions = {0: self.engine._calculate_turn_actions(0)}
        self.engine.execute_action(0, GameAction.DISCARD, discard_tile)

        # Player 1 ron
        result1 = self.engine.execute_action(1, GameAction.RON, tile=discard_tile)
        assert result1.success
        assert result1.winners == [1]

    def test_double_ron_priority_order(self):
        """Test double_ron: Verify player order (shimocha first)"""
        self._init_game()

        # Enable double_ron mode
        self.engine._game_state.ruleset.head_bump_only = False
        self.engine._game_state.ruleset.allow_double_ron = True

        # Player 0 discards 5p, Player 2 and 3 can ron
        discard_tile = Tile(Suit.PINZU, 5)

        # 234m 345m 678m 234p 5p (machi 5p) - tanyao
        hand_str = "233445678m2345p"

        self.engine._hands[2] = Hand(parse_tiles(hand_str))
        self.engine._hands[3] = Hand(parse_tiles(hand_str))

        self.engine._last_discarded_tile = discard_tile
        self.engine._last_discarded_player = 0

        # Check check_multiple_ron return order
        winners = self.engine.check_multiple_ron(discard_tile, 0)

        # Player 0's shimocha is Player 1, then 2, 3
        # So return order should be [2, 3] (Counter-clockwise)
        assert winners == [2, 3]
