# 4-model 72h Top2 audit

- run_id: `run-four-profile-72h-mpv2-restart-20260527T161918Z`
- remote_run: `[PRIVATE_HOME]/m6-paper/runs/run-four-profile-72h-mpv2-restart-20260527T161918Z`
- local_run: `paper-trade-history/run-four-profile-72h-mpv2-restart-20260527T161918Z/remote_run`
- ranking metric: `final adjusted_total_pnl_usdc`
- integrity: remote pre/post diff `0`, remote/local SHA diff `0`, tracked files `18`
- service state: pre `inactive`, post `inactive`
- run manifest: start `2026-05-27T16:26:44.625000Z`, end `2026-05-30T16:25:18.093000Z`, total_decisions `2312862`, unsettled_at_shutdown `4`

## Ranking

| rank | profile | adjusted_total_pnl_usdc | nav_last | submitted orders | filled orders |
|---:|---|---:|---:|---:|---:|
| 1 | `mpv2_r1_a3_seq120_seed2` | 1114.9697 | 1214.9697 | 880719 | 146840 |
| 2 | `m5_baseline` | 20.1954 | 93.9943 | 14628 | 909 |
| 3 | `m3_b2` | -100.6707 | 50.0947 | 6843 | 374 |
| 4 | `m3_b1` | -127.7975 | 107.7580 | 1182 | 237 |

## Top2 ledger audit

| profile | decisions | nav start -> last | adjusted PnL | submitted | filled | fees | realized PnL | rebate accrual / payout / pending | closed PnL / resets / writeoffs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `mpv2_r1_a3_seq120_seed2` | 1016043 | 100.0000 -> 1214.9697 | 1114.9697 | 880719 | 146840 | 388.7013 | 1131.9808 | 1385.0015 / 1121.1119 / 263.8896 | 0 / 0 / 16 |
| `m5_baseline` | 830444 | 100.0000 -> 93.9943 | 20.1954 | 14628 | 909 | 6.5578 | 14.1654 | 14.2578 / 12.2361 / 2.0217 | 26.2011 / 4 / 16 |

## Fill haircut sensitivity

These are local sensitivity replays over recorded lifecycle events. Queue-ahead is a proxy, not exchange queue evidence.

### mpv2_r1_a3_seq120_seed2
- trades: `2799845`, final marks: `1666`, risk writeoffs: `16`, ratio break-even: `<0.1000`

| fill_ratio | nav_delta | final_nav | fill_events |
|---:|---:|---:|---:|
| 1.0000 | 1121.8831 | 1221.8831 | 169377 |
| 0.5000 | 560.5391 | 660.5391 | 169377 |
| 0.2500 | 280.0537 | 380.0537 | 169377 |
| 0.1000 | 112.0444 | 212.0444 | 169377 |

| queue_ahead_shares | nav_delta | final_nav | fill_events | blocked_sell_shares |
|---:|---:|---:|---:|---:|
| 0.0000 | 1121.8831 | 1221.8831 | 169377 | 0.0000 |
| 1.0000 | 809.6968 | 909.6968 | 150620 | 5486.0127 |
| 2.5000 | 425.4222 | 525.4222 | 126116 | 7981.3400 |
| 5.0000 | 0.0000 | 100.0000 | 0 | 0.0000 |
| 10.0000 | 0.0000 | 100.0000 | 0 | 0.0000 |

### m5_baseline
- trades: `45307`, final marks: `615`, risk writeoffs: `16`, ratio break-even: `<0.1000`

| fill_ratio | nav_delta | final_nav | fill_events |
|---:|---:|---:|---:|
| 1.0000 | 17.2794 | 117.2794 | 1099 |
| 0.5000 | 8.6352 | 108.6352 | 1099 |
| 0.2500 | 4.3163 | 104.3163 | 1099 |
| 0.1000 | 1.7256 | 101.7256 | 1099 |

| queue_ahead_shares | nav_delta | final_nav | fill_events | blocked_sell_shares |
|---:|---:|---:|---:|---:|
| 0.0000 | 17.2794 | 117.2794 | 1099 | 0.0000 |
| 1.0000 | 15.7835 | 115.7835 | 967 | 0.0000 |
| 2.5000 | 10.8775 | 110.8775 | 828 | 0.0000 |
| 5.0000 | 0.9649 | 100.9649 | 661 | 0.0000 |
| 10.0000 | -10.0003 | 89.9997 | 354 | 0.0000 |

## MakerPolicyV2 debug sidecar

- debug rows: `1016043`, mpv2 decision rows: `1016043`, row count matches: `True`
- first row aligns with decisions: `True`; last row aligns with decisions: `True`
- submitted_count sum: `880721`, cancel_count sum: `314579`
- policy_action_counts: `{'stale_features': 373287, 'quote': 348533, 'hold': 179951, 'cancel_replace': 72822, 'market_end_no_quote': 33971, 'cancel': 7360, 'warmup': 119}`
- non_null_field_counts: `{'block_reasons': 1016043, 'active_resting_count_before': 1016043, 'active_resting_count_after': 1016043, 'submitted_count': 1016043, 'cancel_count': 1016043, 'alpha': 608666, 'account_state': 608666, 'quote_probs': 608666, 'offset_classes': 608666, 'size_classes': 608666, 'risk_score': 608666}`

## Global health and caveats

- health event counts: `{'booting_observe_only': 1, 'cancel_stale_active_order': 2552, 'chainlink_settlement_pending': 781, 'clob_rate_limits_resolved': 1, 'feed_latency': 657649, 'gap': 48, 'gap_recovered': 48, 'market_p2b_set': 3412, 'market_resolved': 3381, 'market_resolved_meta': 3381, 'model_profiles_loaded': 1, 'order_lifecycle': 2864746, 'order_lifecycle_cancel_on_gap': 2132, 'order_lifecycle_cancel_on_risk_control': 390, 'order_lifecycle_cancel_on_shutdown': 36, 'order_rejected': 3, 'risk_control_await_segment_reset': 27, 'risk_control_cancel_attempt': 18, 'risk_control_late_liability_writeoff': 51, 'risk_control_order_blocked': 9, 'risk_control_rejoin_active': 26, 'risk_control_segment_reset': 26, 'risk_control_triggered': 27, 'shutdown_signal': 1, 'unexpected_unsettled_dropped': 51, 'unsettled_at_shutdown': 4, 'worker_spawned': 865}`
- global risk triggers: `{'stop_loss': 13, 'take_profit': 14}`
- Fill haircut is a local sensitivity analysis over recorded paper-runtime lifecycle events, not proof of real CLOB queue priority.
- No cutoff_iso was used; results cover the pulled artifact through its terminal events.
- Haircut nav_delta is a replay sensitivity measure and is not a replacement for adjusted_total_pnl_usdc ranking.
- Remote test data was not deleted in this run; deletion requires explicit user approval after reviewing remote_delete_candidates.md.
