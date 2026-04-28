# PyRiichi Detailed Requirements Specification

## 1. System Overview

PyRiichi is a complete Japanese riichi mahjong game engine. It implements standard riichi mahjong rules, including full yaku detection and score calculation.

## 2. Functional Requirements

### 2.1 Tile System

#### 2.1.1 Tile Type Definitions
- **Manzu tiles**: 1-9 manzu, four copies each, 36 tiles total.
- **Pinzu tiles**: 1-9 pinzu, four copies each, 36 tiles total.
- **Souzu tiles**: 1-9 souzu, four copies each, 36 tiles total.
- **Honor tiles**:
  - Wind tiles: east, south, west, north, four copies each, 16 tiles total.
  - Dragon tiles: haku, hatsu, chun, four copies each, 12 tiles total.
- **Total**: 136 tiles.

#### 2.1.2 Tile Representation
- Use standardized tile IDs or enums.
- Support tile comparison and sorting.
- Support string representation for display and debugging.

#### 2.1.3 Tile Set Operations
- Shuffle.
- Deal tiles, 13 tiles per player and 14 tiles for the dealer.
- Draw tiles.
- Query the number of remaining tiles.

### 2.2 Hand Management

#### 2.2.1 Hand Representation
- 13-tile hands, or 14 tiles for the dealer.
- Discarded tiles.
- Melds: open triplets, open kans, and open sequences.
- Concealed triplets and closed kans.

#### 2.2.2 Hand Operations
- Discard.
- Chi: claim a sequence from kamicha.
- Pon: claim a triplet.
- Kan: claim or declare a kan.
- Tenpai detection.
- Winning-hand detection.

### 2.3 Game Rules

#### 2.3.1 Basic Flow
1. **Deal**: deal 13 tiles to each player and 14 tiles to the dealer.
2. **Draw**: draw one tile from the live wall.
3. **Discard**: choose and discard one tile.
4. **Call**: other players may chi, pon, or kan.
5. **Win**: declare a win when the winning conditions are met.
6. **Drawn round**: calculate points when the round ends in a draw.

Call and win response priority must follow standard riichi timing:

- Ron has priority over calls.
- Pon and kan have priority over chi.
- When multiple players may ron the same discard, resolve according to the active multi-win rule: Head Bump, Double Ron, or Triple Ron.

#### 2.3.2 Winning Conditions
- Standard shape: four sets plus one pair.
- Special shapes: Chiitoitsu, Kokushi Musou, and similar optional shapes.
- The hand must have at least one yaku.

#### 2.3.3 Tenpai Detection
- Determine whether the current hand is tenpai.
- Count waits.
- List all possible winning tiles.

#### 2.3.4 Ryuukyoku Handling
- **Nagashi Mangan**: special draw score under specific conditions.
- **Abortive draws**:
  - Suufon Renda.
  - Kyuushu Kyuuhai.
  - Suucha Riichi.
  - Suukan Sanra.
  - Sancha Ron, when Triple Ron is disabled by the ruleset.

#### 2.3.5 Special Rules
- **Furiten**:
  - **Genbutsu furiten**: a player cannot ron on a tile they previously discarded.
  - **Temp Furiten**: after a player passes on a winning tile, they cannot ron during the same turn cycle.
  - **Riichi furiten**: after declaring riichi, passing on a win creates permanent furiten, so the player can only win by tsumo.
- **Pao**:
  - When Daisangen or Daisuushi is confirmed, the player who provided the final called tile takes responsibility for payment.
- **Kan dora timing**:
  - Closed kan: reveal the kan dora indicator immediately.
  - Open kan, including daiminkan and added kan: reveal the kan dora indicator after the discard, or after Rinshan when applicable.
- **Same-discard rules**:
  - **Head Bump**: when multiple players ron the same discard, only the winner closest to the discarder in turn order wins. Optional rules may allow Double Ron or Triple Ron.

### 2.4 Yaku System

#### 2.4.1 Basic Yaku, 1 Han
- **Riichi**: declare riichi with a closed hand while tenpai, pay one Riichi Stick, and meet the ruleset's remaining-wall requirement.
- **Ippatsu**: win within one uninterrupted turn after declaring riichi.
- **Menzen Tsumo**: tsumo with a fully concealed hand.
- **Tanyao**: all tiles are simples, 2-8. Open Tanyao is controlled by ruleset configuration.
- **Pinfu**: sequence hand with a non-value pair and no fu from sets.
- **Iipeikou**: fully concealed hand with two identical sequences.
- **Yakuhai**: triplet of round_wind, seat_wind, or dragon tiles.
- **Haitei**: win by tsumo on the last live wall tile.
- **Houtei**: win by ron on the last discard.
- **Rinshan**: win by tsumo on the rinshan tile after a kan.
- **Chankan**: win by robbing another player's kan.

#### 2.4.2 Special Yaku, 2-3 Han
- **Double Riichi**: declare riichi on the first uninterrupted turn, 2 han.
- **Sanshoku Doujun**: same-number sequence in all three suits, 2 han closed and 1 han open.
- **Sanshoku Doukou**: same-number triplet in all three suits.
- **Ittsu**: 1-3, 4-6, and 7-9 sequences in one suit, 2 han closed and 1 han open.
- **Toitoi**: all sets are triplets or kans.
- **Sanankou**: three concealed triplets.
- **Sankantsu**: three kans.
- **Shousangen**: two dragon triplets and one dragon pair.
- **Honroutou**: all tiles are terminals and honors, normally paired with Toitoi or Chiitoitsu.
- **Chiitoitsu**: seven pairs.
- **Renhou**: non-dealer wins by first-turn ron. Its value is ruleset-dependent, commonly treated as a yakuman, mangan, or regular yaku depending on the ruleset.

#### 2.4.3 High-Value Yaku, Mangan and Above
- **Chinitsu**: all tiles from one suit, 6 han closed and 5 han open.
- **Honitsu**: one suit plus honors, 3 han closed and 2 han open.
- **Junchan**: every set contains a terminal and there are no honors, 3 han closed and 2 han open.
- **Chanta**: every set contains a terminal or honor, 2 han closed and 1 han open.
- **Ryanpeikou**: two Iipeikou patterns, 3 han.

#### 2.4.4 Yakuman
- **Tenhou**: dealer wins from the initial hand.
- **Chihou**: non-dealer wins by first-turn tsumo.
- **Daisangen**: triplets or kans of all three dragons.
- **Shousuushi**: three wind triplets or kans plus a wind pair.
- **Daisuushi**: four wind triplets or kans.
- **Suuankou**: four concealed triplets.
- **Suuankou Tanki**: Suuankou with a single wait.
- **Suukantsu**: four kans.
- **Chuuren Poutou**: special Chinitsu pattern.
- **Pure Chuuren Poutou**: true nine-sided Chuuren Poutou pattern.
- **Kokushi Musou**: one of each terminal and honor plus one duplicate.
- **Kokushi Musou Juusanmen**: thirteen-sided Kokushi Musou wait.
- **Ryuuiisou**: all green tiles.
- **Chinroutou**: all terminals.
- **Tsuuiisou**: all honors.

Optional local yakuman and legacy variants may be configured separately, but they are not part of the standard modern yaku list.

#### 2.4.5 Yaku Detection Requirements
- Support combined yaku detection.
- Correctly add han values.
- Handle closed and open hand states.
- Handle special cases, such as Suuankou Tanki.

#### 2.4.6 Yaku Combination Rules

**Yaku combinations that cannot combine**:

1. **Chiitoitsu**
   - Cannot combine with standard-shape yaku such as Pinfu, Iipeikou, or Toitoi.
   - Can combine with composition yaku such as Tanyao, Honitsu, or Chinitsu.
   - Reason: Chiitoitsu is a special winning shape and is structurally incompatible with the standard four-sets-plus-one-pair shape.

2. **Pinfu**
   - Cannot combine with Yakuhai for round_wind, seat_wind, or dragon pair value.
   - Reason: Pinfu requires a non-value pair.
   - Cannot combine with Toitoi because Pinfu requires sequences and Toitoi requires triplets.
   - Can combine with Iipeikou or Ryanpeikou when the hand also satisfies Pinfu requirements.

3. **Tanyao**
   - Cannot combine with yaku that require terminals or honors:
     - Ittsu: includes 1 and 9 sequences.
     - Junchan: every set contains a terminal.
     - Chanta: every set contains a terminal or honor.
     - Honroutou: all tiles are terminals and honors.
     - Chinroutou: all tiles are terminals.
   - Reason: Tanyao requires all tiles to be simples, 2-8.

4. **Toitoi**
   - Cannot combine with Pinfu because Pinfu requires sequences and Toitoi requires triplets.
   - Cannot combine with Iipeikou or Ryanpeikou because those require sequences.
   - Cannot combine with Sanshoku Doujun because it requires sequences.
   - Cannot combine with Ittsu because it requires sequences.
   - Cannot combine with Ryanpeikou because it requires two identical sequence pairs.

5. **Iipeikou and Ryanpeikou**
   - Mutually exclusive: Ryanpeikou contains two Iipeikou patterns, so both should not be awarded together.
   - Cannot combine with Toitoi because Iipeikou/Ryanpeikou require sequences and Toitoi requires triplets.
   - Can combine with Pinfu when the hand also satisfies Pinfu requirements.

6. **Chinitsu and Honitsu**
   - Mutually exclusive: Chinitsu requires one pure suit; Honitsu requires one suit plus honors.
   - Cannot combine with Sanshoku Doujun or Sanshoku Doukou because those require multiple suits.

7. **Junchan and Chanta**
   - Mutually exclusive: Junchan has no honors, while Chanta may contain honors.
   - Cannot combine with Tanyao because Junchan and Chanta require terminals or honors, while Tanyao excludes them.

8. **Yakuman**
   - Yakuman do not score together with non-yakuman yaku.
   - Multiple yakuman may combine, such as Suuankou plus Tsuuiisou.

**Yaku combinations that can combine**:

1. **Riichi**
   - Can combine with most non-yakuman yaku, including Chiitoitsu.
   - Reason: Riichi is a declaration action and does not change hand structure.

2. **Ippatsu**
   - Can combine with Riichi, which is required first.
   - Can combine with other yaku.

3. **Menzen Tsumo**
   - Can combine with all yaku that allow a fully concealed hand.
   - Cannot combine with ron because it only applies to tsumo wins.

4. **Yakuhai**
   - Yakuhai may combine with each other, such as round_wind plus seat_wind plus dragon tiles.
   - Can combine with other yaku except Pinfu.

5. **Sanankou**
   - Can combine with Toitoi if the hand has four triplets plus one pair.

6. **Sanshoku Doukou**
   - Can combine with Toitoi.
   - Can combine with Sanankou.

7. **Shousangen**
   - Can combine with Toitoi, Sanankou, and similar yaku.

**Special cases**:

- **Kokushi Musou**: does not combine with standard-shape yaku because it is a special winning shape. Kokushi Musou Juusanmen may be treated as double yakuman depending on the ruleset.
- **Chiitoitsu**: can combine with compatible composition yaku such as Tanyao, Honitsu, Chinitsu, Honroutou, Riichi, Menzen Tsumo, and dora.
- **Chuuren Poutou**: can combine with Chinitsu because Chuuren Poutou is a special Chinitsu shape.

### 2.5 Scoring System

#### 2.5.1 Fu Calculation
- **Base fu**: 20 fu for the win itself.
- **Winning-method fu**:
  - Fully concealed ron: +10 fu.
  - Fully concealed tsumo: +2 fu.
  - Open ron: +0 fu.
  - Open tsumo: +2 fu.
  - Pinfu tsumo is a special 20-fu hand and does not receive tsumo fu.
- **Set fu**:
  - Simple sequence: 0 fu.
  - Terminal/honor sequence: 0 fu.
  - Open simple triplet: 2 fu.
  - Concealed simple triplet: 4 fu.
  - Open terminal/honor triplet: 4 fu.
  - Concealed terminal/honor triplet: 8 fu.
  - Open simple kan: 8 fu.
  - Closed simple kan: 16 fu.
  - Open terminal/honor kan: 16 fu.
  - Closed terminal/honor kan: 32 fu.
- **Pair fu**:
  - Non-value pair: 0 fu.
  - Yakuhai pair: 2 fu.
  - Double wind pair behavior is ruleset-dependent: some rules award 2 fu, while others award 4 fu when round_wind and seat_wind are the same.
- **Wait fu**:
  - Tanki: +2 fu.
  - Penchan: +2 fu.
  - Kanchan: +2 fu.
  - Shabo: +0 fu.
  - Ryanmen: +0 fu.
- **Fu rounding**: round up to the next 10, such as 32 fu to 40 fu.

#### 2.5.2 Han Calculation
- Base han comes from the yaku system.
- Dora:
  - Visible dora: +1 han per tile.
  - Ura Dora after riichi: +1 han per tile.
  - Red Dora: +1 han per tile.
- Han stacking: add all han values.

#### 2.5.3 Point Calculation
- **Base point calculation**:
  - Base points = fu x 2^(han+2).
  - Mangan: 2000 base points, at 5+ han or 4 han 40+ fu.
  - Haneman: 3000 base points, 6-7 han.
  - Baiman: 4000 base points, 8-10 han.
  - Sanbaiman: 6000 base points, 11-12 han.
  - Yakuman: 8000 base points, 13+ han or yakuman.
  - Double yakuman: 16000 base points.
- **Payment method**:
  - Tsumo: dealer pays 2x and non-dealers pay 1x.
  - Ron: the discarder pays the full amount.
  - Dealer bonus payment: when the dealer wins by tsumo, non-dealers pay 2x.
  - Final payments are rounded up to the nearest 100 points.
- **Honba and kyoutaku**:
  - Honba: +300 points per repeat or draw counter.
  - Kyoutaku: the winner receives the 1000-point riichi deposits.
- **Noten Bappu**:
  - At ryuukyoku, tenpai players receive points from noten players.
  - Total transfer is 3000 points: one tenpai player receives +3000 and three noten players pay -1000 each; two tenpai players receive +1500 each and two noten players pay -1500 each; three tenpai players receive +1000 each and one noten player pays -3000.
- **Kiriage Mangan**:
  - 30 fu 4 han and 60 fu 3 han are scored directly as mangan when the optional rule is enabled.

#### 2.5.4 Special Scores
- **Nagashi Mangan**: scored as mangan.
- **Yakuman**: 8000 base points.
- **Double Yakuman**: 16000 base points.
- **Triple Yakuman**: 24000 base points.

### 2.6 Game State Management

#### 2.6.1 Round Management
- **East round**: East 1, East 2, East 3, East 4.
- **South round**: South 1, South 2, South 3, South 4.
- **Round Wind**: wind of the current round.
- **Seat Wind**: each player's seat wind: east, south, west, or north.

#### 2.6.2 Player State
- Score: initial 25000 points.
- Riichi state.
- Fully concealed state.
- Open meld state.

#### 2.6.3 Game State
- Current turn player.
- Honba count.
- Kyoutaku count.
- Remaining live wall tiles.
- Ryuukyoku state.

#### 2.6.4 Game-End Conditions
- **Normal end**: complete the scheduled rounds, such as ending after South 4.
- **Tobi**: any player's score drops below 0, or at/below 0 under optional rules.
- **Abortive draw**: Kyuushu Kyuuhai and similar abortive draws cause a dealer repeat.
- **West round extension**: if nobody reaches the target score, usually 30000, after South 4, extend into the west round.
- **Agari Yame**: when the last-round dealer wins while in first place, they may choose to end the game.

Renchan and counter handling must follow the active ruleset:

- Dealer win causes renchan and increments honba.
- Exhaustive Draw causes renchan when the dealer is tenpai; otherwise the dealer rotates.
- Abortive draw dealer-continuation behavior is ruleset-dependent.
- Kyoutaku carries forward until the next winning hand.

### 2.7 Chombo Handling
- **False win**: declaring a win while not tenpai, declaring ron while furiten, and similar violations.
- **Invalid riichi**: declaring riichi while not tenpai, discovered at ryuukyoku.
- **Penalty**: usually pay mangan-level points, 4000 all as dealer or 2000/4000 as non-dealer, or only forbid winning.

### 2.7 AI Players, Optional Feature

#### 2.7.1 Basic AI
- Simple discard strategy.
- Basic tenpai detection.
- Basic winning-hand detection.

#### 2.7.2 Advanced AI
- Tile-efficiency calculation.
- Defensive strategy.
- Offensive strategy.
- Riichi decision.
- Call decision.

## 3. Non-Functional Requirements

### 3.1 Performance Requirements
- Hand detection response time < 100 ms.
- Yaku detection response time < 500 ms.
- Support continuous multi-round games.

### 3.2 Maintainability
- Clear code structure.
- Complete documentation.
- Unit test coverage > 80%.

### 3.3 Extensibility
- Modular design.
- Easy to add new yaku.
- Easy to modify rules.

### 3.4 Testability
- All core features have corresponding tests.
- Test cases cover edge cases.

## 4. Technical Implementation Details

### 4.1 Data Structures
- Use enums or constants to represent tile types.
- Use lists or sets to manage hands.
- Use dictionaries or structures to manage game state.

### 4.2 Algorithms
- Winning-hand detection: use recursion or state machines.
- Yaku detection: use rule matching.
- Tenpai detection: enumerate possible hand transformations.

### 4.3 Error Handling
- Input validation.
- Exception handling.
- Clear error messages.

## 5. Testing Requirements

### 5.1 Unit Tests
- Tile set operation tests.
- Hand operation tests.
- Yaku detection tests.
- Score calculation tests.

### 5.2 Integration Tests
- Complete game flow tests.
- Special-case tests, such as ryuukyoku and yakuman.

### 5.3 Boundary Tests
- Extreme case handling.
- Invalid input handling.
