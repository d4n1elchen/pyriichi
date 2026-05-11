# Ruleset Variants

This file maps documented optional behavior to `RulesetConfig` fields. Defaults are the values returned by `RulesetConfig.standard()`.

| Rule Area | Config Field | Standard Default | Supported Alternatives |
|-----------|--------------|------------------|------------------------|
| Renhou value | `renhou_policy` | `RenhouPolicy.TWO_HAN` | `RenhouPolicy.YAKUMAN`, `RenhouPolicy.OFF` |
| Pinfu wait requirement | `pinfu_require_ryanmen` | `True` | `False` disables the ryanmen requirement. |
| Ippatsu interruption | `ippatsu_interrupt_on_meld_or_kan` | `True` | `False` keeps Ippatsu after chi, pon, kan, or closed kan. |
| Open Tanyao | `open_tanyao_enabled` | `True` | `False` requires Tanyao to be closed. |
| Abortive-draw dealer continuation | `abortive_draw_dealer_continues` | `True` | `False` rotates the dealer after abortive draws. |
| Chanta availability | `chanta_enabled` | `True` | `False` disables Chanta. |
| Chanta han | `chanta_open_han`, `chanta_closed_han` | `1`, `2` | Custom open and closed han values. |
| Junchan han | `junchan_open_han`, `junchan_closed_han` | `2`, `3` | Custom open and closed han values. |
| Suuankou Tanki value | `suuankou_tanki_double` | `True` | `False` scores it as single yakuman. |
| Kokushi Musou Juusanmen value | `kokushi_musou_juusanmen_double` | `True` | `False` scores it as single yakuman. |
| Pure Chuuren Poutou value | `pure_chuuren_poutou_double` | `True` | `False` scores it as single yakuman. |
| Kiriage Mangan | `kiriage_mangan` | `False` | `True` treats 30 fu 4 han and 60 fu 3 han as mangan. |
| Tobi | `tobi_enabled` | `True` | `False` disables bankruptcy game end. |
| West round extension | `west_round_extension` | `True` | `False` ends after South 4 regardless of return score. |
| Return score | `return_score` | `30000` | Custom target score for game end. |
| Agari Yame | `agari_yame` | `True` | `False` forces renchan when the last-round dealer wins. |
| Chombo penalty | `chombo_penalty_enabled` | `True` | `False` rejects invalid actions without applying chombo settlement. |
| Riichi live-wall minimum | `riichi_min_remaining_tiles` | `4` | Custom live-wall minimum for riichi declaration. |
| Head Bump | `head_bump_only` | `True` | `False` allows multiple ron if enabled by the following fields. |
| Double Ron | `allow_double_ron` | `False` | `True` allows two simultaneous ron wins when Head Bump is disabled. |
| Triple Ron | `allow_triple_ron` | `False` | `True` allows three simultaneous ron wins when Head Bump and Double Ron allow it. |
