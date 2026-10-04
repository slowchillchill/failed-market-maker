# First-place trade style analysis

Run: `run-four-profile-7d-direct-official-20260602T135518Z`

## Primary Ranking

Primary metric: `final adjusted_total_pnl_usdc` from the standard paper run report. Maker rebate ledger is shown separately and is not added to the primary ranking.

| rank | profile | adjusted_total_pnl_usdc | nav_last | orders | fills |
|---:|---|---:|---:|---:|---:|
| 1 | `mpv2_r1_a3_seq120_seed2` | 1791.3144 | 1891.3144 | 923677 | 163836 |
| 2 | `m5_baseline` | 84.7787 | 97.0450 | 14382 | 786 |
| 3 | `m3_b2` | -224.9895 | 50.0888 | 5006 | 266 |
| 4 | `m3_b1` | -298.0387 | 50.5466 | 3759 | 256 |

## First Place: `mpv2_r1_a3_seq120_seed2`

- adjusted_total_pnl_usdc: `1791.3144`
- nav_last: `1891.3144`
- event window: `2026-06-02T14:00:33.622000Z` -> `2026-06-05T18:09:19.239000Z`
- trade events: `2936992`
- orders: submitted `923677`, filled `163836`, cancelled `797482`, open `0`
- fill_order_rate: `17.7374%`; cancel_order_rate: `86.3378%`
- buy_cost_usdc: `182689.6897`; sell_proceeds_usdc: `181532.2677`; turnover_vs_100_start: `1826.90x`
- trade reconstructed closed_realized_pnl_usdc: `1790.7109`
- maker rebate side-ledger accrual: `2859.3160`; last pending: `330.2897`
- open inventory cost basis at shutdown: `12.4854` across `2` positions

## Trade Distribution

- kind_counts: `{"CancelRequested": 119824, "Cancelled": 797482, "FilledFull": 126240, "FilledPartial": 50994, "Rejected": 1, "RestingPlaced": 917869, "Submitted": 923677, "settlement": 905}`
- submitted_side: `{"buy": 753671, "sell": 170006}`
- submitted_outcome: `{"down": 461080, "up": 462597}`
- submitted_slot: `{"down_buy": 376959, "down_sell": 84121, "up_buy": 376712, "up_sell": 85885}`
- submitted_offset: `{"improve_1_tick": 75834, "join_best": 847843}`
- filled_side_events: `{"buy": 94625, "sell": 82609}`
- filled_outcome_events: `{"down": 90055, "up": 87179}`
- fill_shares_stats: `{"count": 177234, "max": 5.0, "p50": 5.0, "p90": 5.0, "p99": 5.0}`
- buy_price_stats: `{"count": 94625, "p10": 0.12, "p50": 0.51, "p90": 0.92}`
- sell_price_stats: `{"count": 82609, "p10": 0.14, "p50": 0.55, "p90": 0.94}`
- order_lifetime_ms: `{"count": 923722, "max": 737502, "p50": 279.0, "p90": 231458.9, "p99": 293466.0}`
- cancel_lifetime_ms: `{"count": 797482, "max": 737502, "p50": 448.0, "p90": 240798.0, "p99": 294458.0}`
- full_fill_lifetime_ms: `{"count": 126240, "max": 289, "p50": 124.0, "p90": 233.0, "p99": 279.0}`

## Policy Debug Style

- debug rows: `1086034`; actions: `{"cancel": 7216, "cancel_replace": 90755, "hold": 178019, "market_end_no_quote": 36260, "quote": 355621, "stale_features": 418044, "warmup": 119}`
- submitted_count_per_tick: `{"0": 639658, "1": 73893, "2": 275165, "3": 89794, "4": 7524}`
- cancel_count_per_tick: `{"0": 891016, "1": 74031, "2": 100838, "3": 19371, "4": 778}`
- offset_class_counts: `{"improve_1_tick": 210780, "join_best": 2315664}`
- size_class_counts: `{"min_order_size": 2526444}`
- risk_score: `{"avg": 0.1979160398497857, "count": 631611, "max": 0.6505687, "min": 0.040576965, "p50": 0.15904796, "p90": 0.26587123, "p99": 0.58459002}`
- quote_all_ones_ratio: `0.999927`
- top block reasons: `[["down_sell:insufficient_inventory", 505680], ["up_sell:insufficient_inventory", 501108], ["stale_features", 418044], ["market_end_no_quote", 36260], ["down_buy:crossing_price", 21621], ["up_buy:crossing_price", 21242], ["up_buy:inventory_or_cash_cap", 13077], ["down_buy:inventory_or_cash_cap", 11689], ["up_sell:crossing_price", 6572], ["down_sell:crossing_price", 5284], ["warmup", 119]]`

## Best And Worst Closed Markets

Best closed markets:
- `0xd76b0bf96ce088e22829b1fc4ba41dcef93f10df438026d0e4c6d675a26e0803` pnl=22.2079, orders=1341, fills=324, buy_cost=347.5968, settlement=18.1823
- `0x7929b5075780e8db4c57d83ac6ba49420eb3bcce0c089e001ddea0e66c417469` pnl=17.9916, orders=1259, fills=354, buy_cost=370.4215, settlement=6.6759
- `0xd0bc4eeea68d839bd0115977a2b587c2db2e0b5f7f9a788ec677dea1de28c668` pnl=16.8864, orders=761, fills=161, buy_cost=145.8538, settlement=0.0435
- `0xad8319b99fe3c8d24b89960026b1507aad67fe373724bd50627484bb53f3aec6` pnl=16.3158, orders=1421, fills=393, buy_cost=373.7435, settlement=-3.9863
- `0xa82d452f7e73aeef8be94b5710ec87f535910c13a14540f91e8a3770c8c5a69e` pnl=15.9343, orders=1271, fills=236, buy_cost=264.1581, settlement=8.2659

Worst closed markets:
- `0xd2f20213bb6c6e3a97b8f638dee3a80668c9458063b539211f68e2fb5124df10` pnl=-8.2078, orders=1252, fills=259, buy_cost=283.2294, settlement=-4.3887
- `0xb4ffd6e8905d37ac1040e951cf9d32106e7c8be347da00301bf0bf34912073c9` pnl=-7.8543, orders=1322, fills=276, buy_cost=300.8255, settlement=-0.5648
- `0xa034b1e48475192cdf4fc16bfefde919105aa387117becfbb9f15690a5f966c4` pnl=-7.7662, orders=1247, fills=252, buy_cost=257.9002, settlement=0.0926
- `0x82de0e5434db2555276eda3abd5b83a6cbdeb37bde820ffb8872c5a9ba64b349` pnl=-7.0460, orders=1241, fills=200, buy_cost=213.3862, settlement=-2.0384
- `0x6d23cdfd58c78d54f618cadcb36fb4d9cbcf573a7efefb3d327720166c918258` pnl=-6.7109, orders=1233, fills=272, buy_cost=232.4775, settlement=-2.4384

## Open Positions At Shutdown

- `0xa1bff5ffc0de13e6c6b9544cb0a75e50ce03cefd0d14a15c10cee8ef4400446e` down shares=11.6239, cost=2.3334
- `0xa1bff5ffc0de13e6c6b9544cb0a75e50ce03cefd0d14a15c10cee8ef4400446e` up shares=13.4001, cost=10.1520
