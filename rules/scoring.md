# Scoring Rules

## Fu Calculation

- Base fu: 20 fu for the win itself.
- Fully concealed ron: +10 fu.
- Tsumo: +2 fu, except Pinfu tsumo.
- Open ron: +0 fu.
- Pinfu tsumo is a special 20-fu hand.
- Chiitoitsu is fixed at 25 fu.

## Set Fu

- Sequences: 0 fu.
- Open simple triplet: 2 fu.
- Concealed simple triplet: 4 fu.
- Open terminal/honor triplet: 4 fu.
- Concealed terminal/honor triplet: 8 fu.
- Open simple kan: 8 fu.
- Closed simple kan: 16 fu.
- Open terminal/honor kan: 16 fu.
- Closed terminal/honor kan: 32 fu.

## Pair Fu

- Non-value pair: 0 fu.
- Dragon pair: 2 fu.
- round_wind pair: 2 fu.
- seat_wind pair: 2 fu.
- Double wind pair behavior is ruleset-dependent: some rules award 2 fu, while others award 4 fu when round_wind and seat_wind are the same.

## Wait Fu

- Tanki: +2 fu.
- Penchan: +2 fu.
- Kanchan: +2 fu.
- Shabo: +0 fu.
- Ryanmen: +0 fu.

## Rounding

- Fu rounds up to the next 10, except fixed 25-fu Chiitoitsu.
- Final payments round up to the nearest 100 points.

## Han Calculation

- Base han comes from yaku.
- Dora: +1 han per visible dora.
- Ura Dora: +1 han per tile after riichi.
- Red Dora: +1 han per red tile.
- Dora do not create yaku by themselves.

## Limits

- Base points = fu x 2^(han + 2).
- Mangan: 2000 base points, at 5+ han or 4 han 40+ fu.
- Kiriage Mangan: 30 fu 4 han and 60 fu 3 han count as mangan when enabled.
- Haneman: 3000 base points, 6-7 han.
- Baiman: 4000 base points, 8-10 han.
- Sanbaiman: 6000 base points, 11-12 han.
- Yakuman: 8000 base points.
- Double yakuman: 16000 base points.
- Triple yakuman: 24000 base points.

## Payments

- Ron: the discarder pays the full rounded amount.
- Non-dealer tsumo: dealer pays 2x base and each other non-dealer pays 1x base, rounded separately.
- Dealer tsumo: each non-dealer pays 2x base, rounded separately.
- Honba adds 300 points to ron payment.
- Honba adds 100 points per paying player on tsumo.
- Kyoutaku goes to the winner and is not paid by the discarder.

## Ryuukyoku Payments

- Noten Bappu transfers a total of 3000 points between tenpai and noten players.
- One tenpai player: +3000, each noten player -1000.
- Two tenpai players: each tenpai player +1500, each noten player -1500.
- Three tenpai players: each tenpai player +1000, one noten player -3000.
- Zero or four tenpai players: no transfer.

## Special Scores

- Nagashi Mangan is scored as mangan.
- Pao applies responsibility payment for Daisangen and Daisuushi when the ruleset supports it.
- Pao tsumo: the responsible player pays all.
- Pao ron by responsible player: the responsible player pays all.
- Pao ron by another player: the responsible player and discarder split the payment.
