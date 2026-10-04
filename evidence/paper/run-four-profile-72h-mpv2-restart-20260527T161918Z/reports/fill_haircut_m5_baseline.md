# mpv2 maker fill haircut analysis

## Input

- model_dir: `source://paper/paper-trade-history/run-four-profile-72h-mpv2-restart-20260527T161918Z/remote_run/models/m5_baseline`
- trades: `45307` rows, `2026-05-27T16:31:32.847000Z` -> `2026-05-30T16:25:00.010000Z`
- starting_cash: `100.0000`
- cutoff_iso: `None`
- ratio break-even estimate: `<0.1000`

## 方案 1: fill_ratio proportional haircut

| scenario | final_nav | nav_delta | buy_cost | sell_realized | settlement | writeoff | open_mark | blocked_sell | markets +/- |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0000 | 117.2794 | 17.2794 | 2584.0839 | 325.5214 | -311.3565 | -0.4355 | 4.9500 | 0.0000 | 356/258 |
| 0.5000 | 108.6352 | 8.6352 | 1292.0465 | 162.7591 | -155.6811 | -0.2178 | 2.4750 | 0.0000 | 356/258 |
| 0.2500 | 104.3163 | 4.3163 | 646.0246 | 81.3786 | -77.8410 | -0.1089 | 1.2375 | 0.0000 | 356/258 |
| 0.1000 | 101.7256 | 1.7256 | 258.4107 | 32.5515 | -31.1373 | -0.0436 | 0.4950 | 0.0000 | 356/258 |

## 方案 2: queue_ahead_shares order-level haircut

| scenario | final_nav | nav_delta | buy_cost | sell_realized | settlement | writeoff | open_mark | blocked_sell | markets +/- |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.0000 | 117.2794 | 17.2794 | 2584.0839 | 325.5214 | -311.3565 | -0.4355 | 4.9500 | 0.0000 | 356/258 |
| 1.0000 | 115.7835 | 15.7835 | 2259.1591 | 297.4968 | -284.5533 | 0.0000 | 3.9600 | 0.0000 | 315/228 |
| 2.5000 | 110.8775 | 10.8775 | 1839.9921 | 256.9798 | -247.8773 | 0.0000 | 2.4750 | 0.0000 | 258/188 |
| 5.0000 | 100.9649 | 0.9649 | 1253.6669 | 191.4993 | -190.5345 | 0.0000 | 0.0000 | 0.0000 | 191/136 |
| 10.0000 | 89.9997 | -10.0003 | 494.5741 | 75.7715 | -85.7719 | 0.0000 | 0.0000 | 0.0000 | 112/83 |

## Notes

- This is a local sensitivity analysis over recorded paper-runtime lifecycle events.
- The queue haircut is a proxy for queue priority, not proof of real CLOB queue position.
- Missing final marks are treated as zero mark and reported via `open_unmarked_cost_basis` in JSON.
