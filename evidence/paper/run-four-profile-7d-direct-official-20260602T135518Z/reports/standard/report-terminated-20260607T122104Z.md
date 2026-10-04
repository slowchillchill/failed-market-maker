# Daily Paper Run Report - 2026-06-07T12:21:04Z

## Service

- run_dir: `paper-trade-history/run-four-profile-7d-direct-official-20260602T135518Z/remote_run`
- service_status: `terminated`
- git_commit: `bc80f6c`
- latency_mode: `logical_equal_decision`
- duration_hours: `118.36`
- disk: used `1272.89GiB` / total `1875.68GiB`, free `507.43GiB`, usage `67.9%`

## Decisions And Account

- rows: total `252439`, window_24h `0`
- decision_rate_hz: total `1.0072`, window `n/a`
- max_interval_ms: total `28800246`, window `None`
- NAV: start `100.0000`, last `50.5466`, total_delta `-49.4534`, window_delta `n/a`
- cash_last: `44.1776`
- gaps total: `gap_chainlink=51, gap_polymarket=5475, has_gap=5526`
- gaps window: `{}`

## Trade Activity

- events: total `12056`, window `0`
- order counts total: submitted `3759`, filled `256`, full_fill `220`, partial_fill `48`, cancelled `3539`
- order counts window: submitted `0`, filled `0`, full_fill `0`, partial_fill `0`, cancelled `0`
- kind counts total: `CancelRequested=3, Cancelled=3539, FilledFull=220, FilledPartial=66, RestingPlaced=3566, Submitted=3759, settlement=903`
- kind counts window: `{}`
- submitted sides total: `buy=2734, sell=1025`
- submitted sides window: `{}`
- open_order_count: `0`
- realized_pnl_usdc: total `-313.2695`, window `+0.0000`
- fee_usdc: total `55.4136`, window `0.0000`

## Health

- health events total: `binance_source_config=1, binance_source_health=18333, binance_source_order_blocked=23, booting_observe_only=1, cancel_stale_active_order=7138, chainlink_settlement_pending=429, clob_rate_limits_resolved=1, feed_latency=684190, gap=124, gap_recovered=120, market_p2b_set=3644, market_resolved=3616, market_resolved_meta=3616, model_profiles_loaded=1, no_worker_for_next_target=2, order_lifecycle=2998582, order_lifecycle_cancel_on_gap=6713, order_lifecycle_cancel_on_risk_control=451, order_rejected=2, recovery_observe_only=1, risk_control_await_segment_reset=28, risk_control_cancel_attempt=20, risk_control_late_liability_writeoff=30, risk_control_order_blocked=14, risk_control_rejoin_active=26, risk_control_segment_reset=28, risk_control_triggered=28, schedule_worker_error=151867, shutdown_signal=1, unexpected_unsettled_dropped=30, unsettled_at_shutdown=2, worker_spawned=915`
- health events window: `binance_source_health=4616, schedule_worker_error=86400, shutdown_signal=1, unsettled_at_shutdown=2`
- metadata: rows `915`, valid_rules `915`, invalid_rules `0`

## Risk Control

- events total: `risk_control_await_segment_reset=28, risk_control_cancel_attempt=20, risk_control_late_liability_writeoff=30, risk_control_order_blocked=14, risk_control_rejoin_active=26, risk_control_segment_close=28, risk_control_segment_reset=28, risk_control_triggered=28`
- events window: `{}`
- triggers total: `stop_loss=16, take_profit=12`
- triggers window: `{}`
- closed_segment_pnl_usdc: total `-298.0387`, window `+0.0000`
- segment_reset_count: `9`
- late_liability_writeoff_count: `8`
- current_segment_pnl_usdc: `+0.0000`
- adjusted_total_pnl_usdc: `-298.0387`

## Rebate

- amount total: `maker_rebate_accrual=1.17421, maker_rebate_carry=0.0`
- amount window: `{}`
- pending_usdc: `1.1742`

## Profile Comparison

| profile | nav_last | nav_delta_total | window_delta | decision_rows | orders | fills | open_orders | realized_pnl | adjusted_pnl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3_b1 | `50.5466` | `-49.4534` | `n/a` | `252439` | `3759` | `256` | `0` | `-313.2695` | `-298.0387` |
| m3_b2 | `50.0888` | `-49.9112` | `n/a` | `196813` | `5006` | `266` | `0` | `-283.0591` | `-224.9895` |
| m5_baseline | `97.0450` | `-2.9550` | `n/a` | `690250` | `14382` | `786` | `0` | `+67.9293` | `+84.7787` |
| mpv2_r1_a3_seq120_seed2 | `1891.3144` | `+1791.3144` | `n/a` | `1086034` | `923677` | `163836` | `0` | `+1809.2561` | `+1791.3144` |

