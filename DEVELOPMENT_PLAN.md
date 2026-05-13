# PyRiichi Development Plan

## Development Timeline

### Phase 1: Project Foundation (✅ Completed)

#### 1.1 Project Initialization
- [x] Create the project directory structure.
- [x] Create `requirements.txt`.
- [x] Create `pyproject.toml`.
- [x] Configure the development environment.
- [x] Initialize the Git repository.

#### 1.2 Core Module - Tile System
- [x] Implement tile enums and tile representation (`Tile`).
  - [x] Manzu, pinzu, souzu, and honor tiles.
  - [x] Tile representation and comparison.
  - [x] Tile serialization.
  - [x] Red Dora support through the `is_red_dora` flag.
  - [x] Standard string notation, such as `r5m`, matching common Japanese mahjong community conventions.
- [x] Implement the tile set class (`TileSet`).
  - [x] Shuffle algorithm.
  - [x] Deal logic.
  - [x] Draw logic.
  - [x] Wall management.
  - [x] Dora indicator system.

**Deliverables**:
- [x] `tiles.py` - complete tile system.
- [x] Unit tests, integrated into the related test files.

---

### Phase 2: Hand Management System (✅ Completed)

#### 2.1 Hand Representation
- [x] Implement the hand class (`Hand`).
  - [x] Hand storage for 13 or 14 tiles.
  - [x] Meld management, including open triplets and open sequences through the `Meld` class.
  - [x] Concealed triplet and closed kan management inside the hand.
- [x] Hand operations.
  - [x] Discard (`discard`).
  - [x] Chi (`chi`).
  - [x] Pon (`pon`).
  - [x] Kan (`kan`, basic implementation).
  - [x] Tsumo/draw (`add_tile`).

#### 2.2 Hand Analysis
- [x] Hand sorting through `Tile` comparison.
- [x] Hand statistics through `_get_tile_counts`.
- [x] Tenpai detection (`is_tenpai`, `get_machi_tiles`).
- [x] Winning-hand detection (`is_winning_hand`, `get_winning_combinations`).

**Deliverables**:
- [x] `hand.py` - hand management system.
- [x] `test_hand.py` - unit tests, 9 test cases.

---

### Phase 3: Winning-Hand Detection System (✅ Completed)

#### 3.1 Basic Winning-Hand Detection
- [x] Standard winning-hand shape detection.
  - [x] Four sets plus one pair.
  - [x] Recursive algorithm implementation (`_find_melds`).
- [x] Special winning-hand shape detection.
  - [x] Chiitoitsu (`_is_chiitoitsu`).
  - [x] Kokushi Musou (`_is_kokushi_musou`).
  - [ ] Thirteen Unconnected Tiles, optional draw detection.

#### 3.2 Tenpai Detection
- [x] Tenpai detection algorithm (`is_tenpai`).
- [x] Machi tile list (`get_machi_tiles`).
- [x] Winning-combination list (`get_winning_combinations`).

#### 3.3 Set Decomposition
- [x] Sequence detection (`_remove_sequence`).
- [x] Triplet detection (`_remove_triplet`).
- [x] Pair detection (`_remove_pair`).
- [x] Kan detection, integrated into triplet detection.

**Deliverables**:
- [x] Integrated into `hand.py` - winning-hand detection system.
- [x] `test_hand.py` - unit tests, including winning-hand detection tests.

---

### Phase 4: Yaku Detection System (✅ Completed, 45+ Yaku)

#### 4.1 Foundation
- [x] Yaku result base design (`YakuResult` dataclass).
- [x] Yaku detection interface (`YakuChecker.check_all`).
- [x] Multilingual support: Japanese, English, and Traditional Chinese.

#### 4.2 Basic Yaku Implementation, 1 Han
- [x] Riichi.
- [x] Ippatsu.
- [x] Menzen Tsumo.
- [x] Tanyao.
- [x] Pinfu - improved by checking whether the pair is yakuhai.
- [x] Iipeikou.
- [x] Yakuhai - completed, including seat_wind detection.

#### 4.3 Special Yaku Implementation, 2-3 Han
- [x] Sanshoku Doujun.
- [x] Sanshoku Doukou.
- [x] Ittsu.
- [x] Toitoi.
- [x] Sanankou.
- [x] Sankantsu.
- [x] Shousangen.
- [x] Honroutou.
- [x] Chiitoitsu.

#### 4.4 Advanced Yaku Implementation, Mangan and Above
- [x] Chinitsu - 6 han.
- [x] Honitsu - 3 han.
- [x] Junchan - 3 han.
- [x] Chanta - 2 han.
- [x] Ryanpeikou - 3 han.

#### 4.5 Yakuman Implementation
- [x] Tenhou, Chihou, and Renhou - completed through game-state tracking.
- [x] Daisangen, Shousuushi, and Daisuushi.
- [x] Suuankou and Suuankou Tanki - Suuankou implemented.
- [x] Suukantsu.
- [x] Chuuren Poutou and Pure Chuuren Poutou.
- [x] Kokushi Musou and Kokushi Musou Juusanmen - completed, including thirteen-sided detection.
- [x] Ryuuiisou, Chinroutou, and Tsuuiisou.

#### 4.6 Combined Yaku Handling
- [x] Multiple-yaku stacking logic (`check_all`).
- [x] Han calculation by summing the `han` field.
- [x] Yaku conflict detection - full implementation, including all conflict rules.

**Currently Implemented Conflict Handling**:
- ✅ Chiitoitsu cannot combine with other yaku, except Riichi.
- ✅ Kokushi Musou cannot combine with other yaku, except Riichi.
- ✅ Yakuman do not combine with non-yakuman yaku, except Riichi.
- ✅ Pinfu and Yakuhai conflict detection is implemented.
- ✅ Tanyao and terminal/honor-containing yaku conflict detection is implemented.
- ✅ Toitoi and sequence-requiring yaku conflict detection is implemented.
- ✅ Iipeikou and Ryanpeikou mutual exclusion is implemented.
- ✅ Chinitsu and Honitsu mutual exclusion is implemented.
- ✅ Junchan and Chanta mutual exclusion is implemented.
- ✅ Pinfu and Toitoi conflict detection is implemented.
- ✅ Pinfu remains combinable with Iipeikou and Ryanpeikou when the hand otherwise qualifies.

**Implemented Conflict Tests**:
- [x] Pinfu and Yakuhai conflict detection.
- [x] Tanyao and terminal/honor-containing yaku conflict detection.
- [x] Toitoi and sequence-yaku conflict detection.
- [x] Iipeikou and Ryanpeikou mutual exclusion.
- [x] Chinitsu and Honitsu mutual exclusion.
- [x] Junchan and Chanta mutual exclusion.

**Deliverables**:
- [x] `yaku.py` - yaku detection system.
- [x] `test_yaku.py` - unit tests covering 45+ yaku, yaku filtering, and ruleset variants.

**Completed Yaku List, 45+ Total**:
- Basic yaku, 6: Riichi, Tanyao, Pinfu, Iipeikou, Ippatsu, Menzen Tsumo.
- Special yaku, 9: Toitoi, Sanshoku Doujun, Sanshoku Doukou, Ittsu, Sanankou, Sankantsu, Shousangen, Honroutou, Chiitoitsu.
- Advanced yaku, 5: Chinitsu, 6 han; Honitsu, 3 han; Junchan, 3 han; Chanta, 2 han; Ryanpeikou, 3 han.
- Yakuhai, 11: Haku, Hatsu, Chun, round_wind_east, round_wind_south, round_wind_west, round_wind_north, seat_wind_east, seat_wind_south, seat_wind_west, seat_wind_north.
- Yakuman, 13+: Daisangen, Suuankou, Kokushi Musou, Kokushi Musou Juusanmen, Shousuushi, Daisuushi, Chinroutou, Tsuuiisou, Suukantsu, Ryuuiisou, Chuuren Poutou, Tenhou, Chihou, Renhou.
- Special win yaku, 3: Haitei, Houtei, Rinshan.

---

### Phase 5: Scoring System (✅ Completed)

#### 5.1 Fu Calculation
- [x] Base fu calculation, 20 fu.
- [x] Winning-method fu calculation: closed ron +10, closed tsumo +2, open tsumo +2.
- [x] Set fu calculation for triplets and kans.
- [x] Pair fu calculation for yakuhai pairs, +2.
- [x] Wait fu calculation, including ryanmen, penchan, kanchan, tanki, and shabo detection.
- [x] Fu rounding logic, rounded up to 10.
- [x] Pinfu special handling, fixed 20/22 fu.

#### 5.2 Han Calculation
- [x] Base han from the yaku system.
- [x] Dora calculation, integrated in the rule engine.
  - [x] Visible dora.
  - [x] Ura Dora after riichi.
  - [x] Red Dora.
- [x] Han stacking.

#### 5.3 Point Calculation
- [x] Base point calculation: fu x 2^(han+2).
- [x] Mangan-and-above handling: Mangan, Haneman, Baiman, Sanbaiman, Yakuman.
- [x] Payment method calculation - completed.
  - [x] Tsumo payments: dealer 2x, non-dealer 1x.
  - [x] Ron payment: discarder pays the full amount.
- [x] Honba and kyoutaku handling - completed, honba +300 points and kyoutaku distribution.

#### 5.4 Special Scores
- [x] Nagashi Mangan detection, in the rule engine.
- [x] Yakuman score calculation.
- [x] Double yakuman and triple yakuman calculation.

**Deliverables**:
- [x] `scoring.py` - scoring system.
- [x] `test_scoring.py` - unit tests covering fu, han, limit hands, payments, pao, and yakuman multipliers.

---

### Phase 6: Game Rule Engine (✅ Completed, Core Features Implemented)

#### 6.1 Basic Game Flow
- [x] Game initialization (`start_game`).
- [x] Deal flow (`deal`).
- [x] Turn management: draw and discard.
- [x] Call handling for chi, pon, open kan, closed kan, call priority, and post-call discard flow.
- [x] Win flow (`check_win`).
- [x] Ryuukyoku flow (`check_ryuukyoku`, `handle_ryuukyoku`).

#### 6.2 Game State Management
- [x] Round management for east, south, west, and north - implemented in `GameState`.
- [x] round_wind and seat_wind management - implemented in `GameState`.
- [x] Honba management - implemented in `GameState`.
- [x] Kyoutaku management - implemented in `GameState`.
- [x] Player score management - implemented in `GameState`.
- [x] Round transition and end handling (`end_round`).

#### 6.3 Ryuukyoku Handling
- [x] Suufon Renda - completed through discard-history tracking.
- [x] Kyuushu Kyuuhai detection (`check_kyuushu_kyuuhai`) - completed, including first-turn detection.
- [x] Suucha Riichi, all players in riichi leading to abortive draw.
- [x] Suukan Sanra - completed through kan-count tracking.
- [x] Sancha Ron - completed.
- [x] Nagashi Mangan detection (`check_nagashi_mangan`).

#### 6.4 Special Rules
- [x] Riichi rules (`get_available_actions`, `execute_action`).
- [x] Ippatsu rules - completed through turn-count tracking after riichi.
- [x] Chankan rules - completed by checking whether other players can win when an open kan is declared.
- [x] Rinshan - completed by checking wins after the kan draw.
- [x] Haitei - completed for tsumo on the last wall tile.
- [x] Houtei - completed for ron on the last discard.

#### 6.5 Dora System
- [x] Visible dora calculation and display.
- [x] Ura Dora calculation after riichi.
- [x] Red Dora recognition.
- [x] Dora han counting (`_count_dora`).

**Deliverables**:
- [x] `rules.py` - rule engine covered by focused tests.
- [x] `game_state.py` - game-state management covered by focused tests.
- [x] `test_rule_*.py` - expanded rule-engine unit tests.

---

### Phase 7: Testing and Optimization (✅ Completed for Current Scope)

#### 7.1 Test Improvements
- [x] Unit test foundation expanded.
  - [x] `test_hand.py`, multiple tests.
  - [x] `test_yaku.py`, multiple tests.
  - [x] `test_scoring.py`, multiple tests.
  - [x] `test_rule_*.py`, multiple tests.
  - [x] `test_game_state.py`, multiple tests.
  - [x] `test_tiles.py`, multiple tests.
  - [x] `test_utils.py`, multiple tests.
  - [x] `test_integration.py`, integration tests.
- [x] Unit test coverage workflow exists through pytest-cov.
- [x] `rules.py` coverage improvement work completed.
- [x] Integration tests - completed; `test_integration.py` includes full game flow, special rules, ryuukyoku scenarios, and related tests.
- [x] Edge-case tests - completed for winning hands, tenpai, ryuukyoku, special rules, and related cases.
- [ ] Dedicated performance benchmark script - optional, pending.

#### 7.2 Code Optimization
- [x] Code structure optimization through modular design.
- [x] Type warning fixes for all `winning_combination` type mismatches.
- [x] String format standardization: Red Dora uses the standard `r5m` format, matching Japanese mahjong community conventions.
- [x] Performance optimization - completed.
  - [x] Winning-hand detection algorithm optimized by using backtracking to reduce dictionary copies and object allocation.
  - [x] Tile-count cache added to reduce repeated calculations, improving performance by about 10%.
  - [x] Tenpai detection optimized to check only relevant tiles and avoid unnecessary attempts.
  - [x] Machi tile listing optimized through smarter candidate selection.
- [x] Code style checks passed through the linter.

#### 7.3 Documentation Improvements
- [x] API quick reference: `API_SUMMARY.md`.
- [x] Usage examples: `examples/basic_usage.py`, `README.md`.
- [x] Development documentation: `DEVELOPMENT_PLAN.md`, `REQUIREMENTS.md`, and `rules/`.
- [x] String notation explanation: detailed explanation in `README.md`.
- [x] Red Dora format standardization: uses the Japanese mahjong community standard `r5m` format.
- [ ] Detailed API reference documentation - pending, optional.

**Deliverables**:
- [x] Unit and integration test suite.
- [x] Clear code structure.
- [x] Current documentation: README, API summary, development plan, glossary, project requirements, and rule requirements.

---

## Development Priority

### High Priority, Core Features
1. Tile system.
2. Hand management.
3. Winning-hand detection.
4. Basic yaku, at least 10.
5. Score calculation.
6. Basic game flow.

### Medium Priority, Important Features
1. Complete yaku system.
2. Ryuukyoku handling.
3. Game state management.
4. Special rules.

### Low Priority, Enhancements
1. Performance optimization.
2. Additional convenience features.
3. Statistics and analysis features.

---

## Development Methodology

### Test-Driven Development (TDD)

This project follows a strict test-driven development approach, using the red-green-refactor cycle.

#### TDD Development Cycle

1. **Red phase**: write a failing test.
   - Write test cases before implementing any feature.
   - Tests should clearly describe the expected behavior.
   - Run the test and confirm it fails because the feature is not implemented yet.
   - Ensure the test fails for the correct reason, not because the test itself is wrong.

2. **Green phase**: implement the minimum viable code.
   - Write just enough code to make the test pass.
   - Avoid over-designing; focus on passing the test.
   - Run the test and confirm it passes.
   - All existing tests must continue to pass.

3. **Refactor phase**: improve code quality.
   - Improve code structure under the protection of passing tests.
   - Remove duplicated code.
   - Improve readability and maintainability.
   - Rerun tests after each refactor to ensure behavior is unchanged.

#### TDD Best Practices

1. **Test-first principle**
   - Never write production code without a failing test.
   - Every new feature and bug fix should start with a test.
   - Tests are a design tool that helps shape APIs and interfaces.

2. **Small steps**
   - Implement one small feature at a time.
   - Run tests frequently after each change.
   - Keep each iteration short, around 5-10 minutes.

3. **Test isolation**
   - Each test should run independently.
   - Tests should not depend on each other.
   - Use appropriate setup and teardown mechanisms.

4. **Test readability**
   - Use descriptive test names, such as `test_function_scenario_expected_result`.
   - Follow the AAA pattern: arrange, act, assert.
   - Each test should verify one concept.

#### Test Strategy

1. **Unit tests**, highest priority.
   - Test behavior of individual functions or classes.
   - Use mocks to isolate dependencies.
   - Coverage target: >= 90%.
   - Location: `tests/test_*.py`.

2. **Integration tests**, high priority.
   - Test collaboration between modules.
   - Verify end-to-end flows.
   - Cover core business scenarios.
   - Location: `tests/test_integration.py`.

3. **Boundary tests**, high priority.
   - Test boundary conditions and extreme cases.
   - Include empty input, maximum values, minimum values, and similar cases.
   - Include at least 2-3 boundary tests for each feature.

4. **Error-handling tests**, medium priority.
   - Test exceptional cases and error handling.
   - Use `pytest.raises` to verify exceptions.
   - Ensure error messages are clear and useful.

5. **Performance benchmarks**, low priority.
   - Critical algorithms need performance tests.
   - Establish baselines to prevent regressions.
   - A dedicated benchmark script is optional and not currently part of the source tree.

#### Test Coverage Requirements

- **Overall target**: >= 85%.
- **Core module targets**: >= 90%.
  - `tiles.py`: >= 90%.
  - `hand.py`: >= 90%.
  - `yaku.py`: >= 85%.
  - `scoring.py`: >= 90%.
  - `rules.py`: >= 85%.
  - `game_state.py`: >= 95%.
- **Minimum requirement**: all new code >= 80%.

#### Test Tools

- **Test framework**: pytest.
- **Coverage tool**: pytest-cov.
- **Run commands**:
  ```bash
  # Run all tests
  .venv/bin/python -m pytest

  # Run a specific test file
  .venv/bin/python -m pytest tests/test_yaku.py

  # Run tests and show coverage
  .venv/bin/python -m pytest --cov=pyriichi --cov-report=html

  # Run tests with detailed output
  .venv/bin/python -m pytest -v
  ```

#### Development Workflow Example

For new feature development, such as adding a new yaku:

1. **Create the test case**
   ```python
   def test_check_new_yaku():
       # Arrange: prepare test data
       tiles = parse_tiles("1m 2m 3m 4p 5p 6p 7s 8s 9s 1z 1z 2z 2z")
       hand = Hand(tiles)

       # Act: run the test subject
       results = YakuChecker.check_all(hand, ...)

       # Assert: verify the result
       assert any(r.yaku == Yaku.NEW_YAKU for r in results)
   ```

2. **Run the test and confirm it fails**
   ```bash
   .venv/bin/python -m pytest tests/test_yaku.py::test_check_new_yaku
   # A failure should be visible.
   ```

3. **Implement the feature**
   - Add the new check function in `yaku.py`.
   - Add the new yaku to the `Yaku` enum.

4. **Run the test and confirm it passes**
   ```bash
   .venv/bin/python -m pytest tests/test_yaku.py::test_check_new_yaku
   # The test should pass.
   ```

5. **Run all tests**
   ```bash
   .venv/bin/python -m pytest
   # Ensure existing behavior is not broken.
   ```

6. **Check coverage**
   ```bash
   .venv/bin/python -m pytest --cov=pyriichi
   # Ensure coverage satisfies the target.
   ```

7. **Refactor**
   - Improve code structure.
   - Remove duplication.
   - Rerun tests to ensure they pass.

### Iterative Development
- Test after each phase is completed.
- Discover and fix problems promptly.
- Keep the codebase runnable.
- Use short iteration cycles, with one small feature completed in 1-2 days.
- Each commit should include both tests and implementation.

### Code Review
- Review code after each module is completed.
- Ensure code quality and consistency.
- Review focus:
  - Whether there is sufficient test coverage.
  - Whether tests are meaningful and truly verify behavior.
  - Whether code follows PEP 8.
  - Whether error handling is appropriate.
  - Whether API design is clear and easy to use.

---

## Risk Management

### Technical Risks
- **Winning-hand detection algorithm has high complexity**
  - Mitigation: reference existing implementations and use recursive algorithms.
- **Yaku detection may miss edge cases**
  - Mitigation: build a complete test-case library.
- **Score calculation rules are complex**
  - Mitigation: implement in phases and verify gradually.

### Schedule Risks
- **Development time may exceed expectations**
  - Mitigation: prioritize core features and defer non-core features.

---

## Success Criteria

1. ✅ Correctly detect all standard winning-hand shapes: standard shape, Chiitoitsu, and Kokushi Musou.
2. ✅ Correctly detect at least 20 yaku; current count is 45+, far beyond the target.
3. ✅ Correctly calculate score: fu, han, and points.
4. ✅ Complete one full round flow; the basic flow is implemented, including special rules.
5. ✅ Unit test coverage target is > 80%; regenerate coverage after the full suite is restored.
6. ✅ Code follows PEP 8; linter checks pass.
7. ✅ Complete usage documentation: README, API summary, glossary, development plan, and related docs.

## Recent Updates, 2025-11-21

### Bug Fixes
- ✅ **Fix Chiitoitsu fu calculation error**:
  - Fixed a logic error in the `calculate_fu` method in `scoring.py`.
  - Fixed test data setup in `test_calculate_fu_chiitoitsu` in `test_scoring.py`.
  - Ensured yaku enum values are correctly recognized inside `YakuResult` objects.

### Performance Optimization
- ✅ **Winning-hand detection algorithm optimization**:
  - Used a backtracking algorithm to reduce dictionary copies and avoid creating new objects on every recursion.
  - Modified the count dictionary in place and restored it during backtracking, greatly reducing memory allocation.
  - Average standard winning-hand detection time is < 0.06 ms.
- ✅ **Tile-count cache**:
  - Added `_tile_counts_cache` to the hand class.
  - Automatically clears the cache when the hand changes.
  - Improves performance by about 10% on cache hits.
- ✅ **Tenpai detection optimization**:
  - Smart candidate selection checks only tiles related to the hand: same, adjacent, or sequence-related tiles.
  - Reduces checks from 34 tile types to an average of 10-20 candidate tile types.
  - Average standard tenpai detection time is about 1.3 ms.
- ⏳ **Performance testing tool**:
  - A dedicated benchmark script is optional and pending.
  - Current performance claims should be refreshed before publishing release documentation.

### Test Improvements
- ✅ **Integration tests completed**: added `test_integration.py`, including full game flow, special rules, ryuukyoku scenarios, and related tests.
  - Complete win flow tests for tsumo and ron.
  - Complete game flow test including calls.
  - Special rule flow tests for riichi and kan.
  - Ryuukyoku scenario tests for Kyuushu Kyuuhai.
  - Multi-module integration tests for hand, yaku, and score calculation.
  - Realistic scenario tests for multi-round game flow.
  - Error-handling tests.
- ✅ **Test count increased**: the current suite collects 364 tests.
- ✅ **Coverage workflow maintained**: coverage can be regenerated with pytest-cov when needed.

### Documentation Improvements, 2025-11-21
- ✅ **Terminology standardization**:
  - Standardized Japanese mahjong terminology in `REQUIREMENTS.md`, `rules/`, and the code.
  - Adopted the most common spellings used in Japanese mahjong games: katakana for actions and kanji for yaku names.
  - Updated translations in `yaku.py` and `rules.py`.
- ✅ **Rule requirements improvements**:
  - Added missing standard rules: Double Riichi, Furiten, and Pao.
  - Added same-discard rules, Head Bump, and kan dora timing notes.
  - Added scoring rules: Noten Bappu and Kiriage Mangan.
  - Added game-end conditions: Tobi, West round extension, and Agari Yame.
  - Added Chombo handling.
  - Corrected the Chiitoitsu combination-rule description.

### Code Quality Improvements
- ✅ **Type warning fixes**: fixed all `winning_combination` type mismatch issues.
  - Converted tuples returned by `get_winning_combinations()` to lists.
  - Updated all test files: `test_integration.py`, `test_yaku.py`, and `test_scoring.py`.
  - Fixed 72 type warnings in total.

### Format Standardization
- ✅ **Red Dora format standardization**: adopted the Japanese mahjong community standard format.
  - Changed from `[5p]` format to standard `r5p` format with an `r` prefix.
  - Matches the widely used Japanese mahjong community standard.
  - Unified input and output formats, supporting round-trip conversion.
  - Updated all related code and tests.

### Documentation Improvements
- ✅ **README update**:
  - Added a detailed string-notation section.
  - Updated all example code to use the standard format.
  - Added type-conversion notes and cautions.
  - Updated the feature list and marked all implemented features.
- ✅ **Example code update**:
  - Added complete examples for winning-hand detection, yaku checking, and score calculation.
  - Demonstrated correct type-conversion usage.

## Current Progress Summary

### ✅ Completed Core Features
- Tile system (`Tile`, `TileSet`) - fully implemented.
- Hand management (`Hand`) - fully implemented, including winning-hand detection and tenpai detection.
- Call operations: chi, pon, kan - fully implemented.
- Yaku detection system, 45+ yaku - basic yaku, advanced yaku, and yakuman implemented, including special yakuman such as Tenhou, Chihou, and Renhou.
- Scoring system: fu, han, and points - fully implemented.
- Rule engine: game flow, ryuukyoku, dora, and special rules - core features implemented, including Ippatsu, Haitei, Houtei, Suufon Renda, Suukan Sanra, and related rules.
- Game state management: rounds, winds, and points - fully implemented.
- Project initialization: `pyproject.toml` and Git repository - fully implemented.

### 🟡 Rule Feature Summary

#### Yaku System, High Priority
- [x] **Double Riichi**: declare riichi on the first uninterrupted turn, 2 han - added to the `Yaku` enum and `YakuChecker`.
  - First-turn tracking and no-call detection implemented.
  - Complete test cases added.

#### Yaku System, Medium Priority
- [x] Sanshoku Doukou, 2 han - completed.
- [x] Shousangen, 2 han - completed.
- [x] Honroutou, 2 han - completed.
- [x] Junchan, 3 han - completed.
- [x] Chanta, 2 han - completed.
- [x] Ryanpeikou, 3 han - completed.
- [x] Sankantsu, 2 han - completed.
- [x] Ippatsu, 1 han - completed through turn-count tracking after riichi.
- [x] Menzen Tsumo, 1 han - completed.
- [x] Most yakuman, 14 yakuman - completed, including Tenhou, Chihou, and Renhou.
- [x] Tenhou, Chihou, and Renhou, requiring game-state tracking - completed.
- [x] Kokushi Musou Juusanmen, requiring more precise detection - completed.
- [x] Seat Wind detection, requiring improved player-position logic - completed.
- [x] Haitei and Houtei - completed.

#### Special Rules, High Priority
- [x] **Furiten rules**: Genbutsu, Temp Furiten, and Riichi Furiten are implemented in `RuleEngine`.
- [x] **Pao rule**: responsibility payment for Daisangen and Daisuushi is implemented.
- [x] Kan dora timing rule - implemented: closed kan reveals immediately; open kan and added kan reveal after the discard.
- [x] **Same-discard rule, Head Bump**: handling for multiple ron.
  - `rules/game-flow.md` documents this as "only the winner closest to the discarder in turn order wins."
  - Optional rules: Double Ron and Triple Ron allow multiple winners.
  - Multiple-win handling is implemented in `RuleEngine`.

#### Yaku Combination Rules, Medium Priority
- [x] Basic conflict detection for Chiitoitsu, Kokushi Musou, and Yakuman - completed.
- [x] Pinfu and Yakuhai conflict detection - completed.
- [x] Tanyao and terminal/honor-containing yaku conflict detection - completed.
- [x] Toitoi and sequence-yaku conflict detection - completed.
- [x] Iipeikou and Ryanpeikou mutual exclusion - completed.
- [x] Chinitsu and Honitsu mutual exclusion - completed.
- [x] Junchan and Chanta mutual exclusion - completed.
- [x] Complete yaku combination-rule tests - completed, including Pinfu with Iipeikou/Ryanpeikou as valid combinations.

#### Special Rules, Medium Priority
- [x] Ippatsu rule, requiring turn-count tracking after riichi - completed.
- [x] Chankan rule, requiring winning-hand detection during open kan - completed.
- [x] Rinshan, requiring handling of the draw after kan - completed, including yaku detection.
- [x] Haitei, requiring detection of the last wall tile - completed.
- [x] Houtei, requiring detection of the last discard - completed.

#### Ryuukyoku Handling, Medium Priority
- [x] Suufon Renda, requiring tracking of the first four discards - completed.
- [x] Suukan Sanra, requiring tracking the kan count - completed.
- [x] Sancha Ron, requiring handling of multiple winners - completed.
- [x] First-turn Kyuushu Kyuuhai detection, requiring first-turn tracking - completed.
- [x] Nagashi Mangan detection, requiring every discard to be yaochuu and none of those discards to be called - completed.

#### Scoring Improvements, Medium Priority
- [x] Detailed wait fu calculation, requiring machi type detection: Ryanmen, Penchan, Kanchan, Tanki, Shabo - completed.
- [x] Detailed payment calculation: tsumo with dealer 2x and non-dealer 1x; ron paid fully by the discarder - completed.
- [x] Honba and kyoutaku handling: honba +300 points and kyoutaku distribution - completed.
- [x] **Noten Bappu**: point transfer at ryuukyoku.
  - Total 3000 points are distributed between tenpai and noten players.
  - Point transfer logic is implemented in ryuukyoku handling.
- [x] **Kiriage Mangan**: 30 fu 4 han or 60 fu 3 han count as mangan when enabled by ruleset configuration.

#### Game-End Conditions, Medium Priority
- [x] **Tobi**: game ends when a player's score is below 0.
  - Detection logic is implemented in `RuleEngine`.
- [x] **West round extension**: when nobody reaches the target score after South 4, extend to the west round.
  - `GameState` supports west round extension.
- [x] **Agari Yame**: last-round dealer may choose to end the game after winning while in first place.
  - This logic is implemented in game-end detection.

#### Chombo Handling, Low Priority
- [x] **False win**: declaring a win while not tenpai, declaring ron while furiten, and similar cases.
  - Violation detection is implemented.
- [x] **Invalid riichi**: declaring riichi while not tenpai, discovered at ryuukyoku.
  - Invalid declarations produce explicit chombo results when enabled.
- [x] **Penalty**: pay mangan-level points or forbid winning.

#### Project Configuration, Low Priority
- [x] `pyproject.toml`, for packaging and release - completed.
- [x] Git repository initialization - completed.
- [ ] CI/CD configuration, optional - pending.

### 📊 Test Statistics
- Current collected test cases: 364.
- The full test suite passed in the latest documented run.
- Test files include `test_hand`, `test_yaku`, `test_scoring`, `test_rule_*`, `test_game_state`, `test_tiles`, `test_utils`, `test_integration`, and `test_player`.
- Core modules: 8, including `tiles`, `hand`, `game_state`, `yaku`, `scoring`, `rules`, `utils`, `__init__`.
- Coverage can be regenerated with pytest-cov when needed.

### 🔍 Checklist, No Missing Items
- ✅ Tile system: fully implemented, including dora system.
- ✅ Hand management: fully implemented, including winning-hand detection, tenpai detection, and calls: chi, pon, kan, closed kan.
- ✅ Winning-hand detection: fully implemented for standard shape, Chiitoitsu, and Kokushi Musou.
- ✅ Yaku detection: 45+ yaku implemented, covering basic yaku, special yaku, advanced yaku, and yakuman, including Tenhou, Chihou, Renhou, and Kokushi Musou Juusanmen.
- ✅ Score calculation: fu, han, and point calculation fully implemented.
- ✅ Rule engine: basic game flow, ryuukyoku, dora system, and special rules implemented, including Ippatsu, Haitei, Houtei, Suufon Renda, Suukan Sanra, Chankan, Rinshan, and Sancha Ron.
- ✅ Game state: round, wind, and score management fully implemented.
- ✅ Utility functions: `parse_tiles`, `format_tiles`, and `is_winning_hand` implemented.
  - ✅ Supports standard string format, such as `1m`, `2p`, `3s`, `1z`.
  - ✅ Supports standard Red Dora format: `r5m`, `r5p`, `r5s`.
  - ✅ Input and output formats are unified and support round-trip conversion.
- ✅ Test suite: 364 collected tests, including unit and integration tests, covering core features, special rules, and conflict detection.
- ✅ Documentation: README, API summary, glossary, development plan, project requirements, and rule requirements are maintained.
  - ✅ README includes a complete string-notation explanation.
  - ✅ Example code shows complete flows for winning-hand detection, yaku checking, and score calculation.
  - ✅ All examples use correct type conversion, such as `list(combinations[0])`.
  - ✅ `rules/` records standard Japanese riichi mahjong rules.
  - ✅ Japanese terms are standardized, using katakana for actions and kanji for yaku names.

### Current Rule Audit

Current rule implementation status is tracked in `rules/implementation-audit.md`. That audit keeps met items in the summary and lists unresolved findings separately.

---

## Future Extensions

1. Online play.
2. Graphical interface.
3. Stronger AI.
4. Statistics and analysis features.
5. Custom rule support.
6. Multilingual support.
