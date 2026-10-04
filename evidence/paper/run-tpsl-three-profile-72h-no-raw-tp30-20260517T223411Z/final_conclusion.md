# Final Conclusion

- run_id: `run-tpsl-three-profile-72h-no-raw-tp30-20260517T223411Z`
- remote_run_dir: `[PRIVATE_HOME]/m6-paper/logs/run-tpsl-three-profile-72h-no-raw-tp30-20260517T223411Z`
- local_archive: `paper-trade-history/run-tpsl-three-profile-72h-no-raw-tp30-20260517T223411Z/remote_run`
- stopped_at_utc: `2026-05-19T13:52:29Z`
- duration_hours: `39.30`
- service_status_after_stop: `inactive`
- archive_hash_check: `passed`
- full_72h_completed: `False`

## Summary
- Run was stopped intentionally before the 72h target to make way for the V2 merge and restart.
- Artifact archive was pulled from a stopped run snapshot and passed sha256 verification.
- All three profiles were in await_segment_safe_to_reset after a stop_loss trigger at shutdown time.
- Adjusted total PnL includes closed TP/SL segments plus current segment PnL; current segment PnL is zero because each profile was closed/cooling down at stop time.
- m3_b2 led this stopped sample by adjusted total PnL, but this is not a completed 72h performance result.

## Risk Control
- total events: `{'risk_control_await_segment_reset': 17, 'risk_control_late_liability_writeoff': 6, 'risk_control_order_blocked': 7, 'risk_control_rejoin_active': 14, 'risk_control_segment_close': 17, 'risk_control_segment_reset': 14, 'risk_control_triggered': 17}`
- triggers total: `{'stop_loss': 7, 'take_profit': 10}`
- triggers by profile: `{'m3_b1': {'stop_loss': 3, 'take_profit': 2}, 'm3_b2': {'take_profit': 6, 'stop_loss': 2}, 'm5_baseline': {'take_profit': 2, 'stop_loss': 2}}`

## Profile Comparison
| profile | NAV delta | closed PnL | adjusted total PnL | resets | writeoffs | final risk state | last trigger | orders/fills |
|---|---:|---:|---:|---:|---:|---|---|---:|
| m5_baseline | `-49.5660` | `-47.7168` | `-47.7168` | `3` | `2` | `await_segment_safe_to_reset` | `stop_loss` | `521/471` |
| m3_b1 | `-49.9688` | `-55.7933` | `-55.7933` | `4` | `2` | `await_segment_safe_to_reset` | `stop_loss` | `221/196` |
| m3_b2 | `-49.7604` | `+78.4222` | `+78.4222` | `7` | `2` | `await_segment_safe_to_reset` | `stop_loss` | `348/289` |

## Artifacts
- report markdown: `paper-trade-history/run-tpsl-three-profile-72h-no-raw-tp30-20260517T223411Z/final-reports/report-20260519T135915Z.md`
- report json: `paper-trade-history/run-tpsl-three-profile-72h-no-raw-tp30-20260517T223411Z/final-reports/report-20260519T135915Z.json`
- sha256 check: `paper-trade-history/run-tpsl-three-profile-72h-no-raw-tp30-20260517T223411Z/sha256sum.check.txt`
