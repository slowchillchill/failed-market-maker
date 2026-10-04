# mpv2 maker fill haircut analysis

## Input

- model_dir: `source://paper/paper-trade-history/run-four-profile-72h-mpv2-restart-20260527T161918Z/remote_run/models/mpv2_r1_a3_seq120_seed2`
- trades: `2799845` rows, `2026-05-27T16:30:30.600000Z` -> `2026-05-30T16:25:18.001000Z`
- starting_cash: `100.0000`
- cutoff_iso: `None`
- ratio break-even estimate: `<0.1000`

## 方案 1: fill_ratio proportional haircut

| scenario | final_nav | nav_delta | buy_cost | sell_realized | settlement | writeoff | open_mark | blocked_sell | markets +/- |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0000 | 1221.8831 | 1121.8831 | 159358.3117 | 1217.0277 | -85.0408 | -9.5236 | 6.9132 | 0.0000 | 637/197 |
| 0.5000 | 660.5391 | 560.5391 | 79679.5590 | 608.1275 | -42.5361 | -4.7623 | 3.4566 | 0.0000 | 637/197 |
| 0.2500 | 380.0537 | 280.0537 | 39839.9970 | 303.8508 | -21.2713 | -2.3809 | 1.7283 | 0.0000 | 637/197 |
| 0.1000 | 212.0444 | 112.0444 | 15935.9754 | 121.5616 | -8.5064 | -0.9527 | 0.6913 | 0.0000 | 637/197 |

## 方案 2: queue_ahead_shares order-level haircut

| scenario | final_nav | nav_delta | buy_cost | sell_realized | settlement | writeoff | open_mark | blocked_sell | markets +/- |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.0000 | 1221.8831 | 1121.8831 | 159358.3117 | 1217.0277 | -85.0408 | -9.5236 | 6.9132 | 0.0000 | 637/197 |
| 1.0000 | 909.6968 | 809.6968 | 121013.3067 | 870.0963 | -55.3987 | -4.8715 | 6.9132 | 5486.0127 | 625/209 |
| 2.5000 | 525.4222 | 425.4222 | 70526.4620 | 458.7616 | -31.5946 | -2.8750 | 7.9344 | 7981.3400 | 589/245 |
| 5.0000 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0/0 |
| 10.0000 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0/0 |

## Notes

- This is a local sensitivity analysis over recorded paper-runtime lifecycle events.
- The queue haircut is a proxy for queue priority, not proof of real CLOB queue position.
- Missing final marks are treated as zero mark and reported via `open_unmarked_cost_basis` in JSON.
