# Three-Profile Paper Trade Final Conclusion

## Run Status
- Intended run: 72h three-profile paper trade
- Actual status: stopped by user request; service status `inactive`
- Start UTC: `2026-05-17T02:21:56Z`
- Stop UTC: `2026-05-17T08:35:17Z`
- Duration hours: `6.2224`
- Manifest total decisions: `265242`
- Unsettled at shutdown: `3`
- Remote run dir: `[PRIVATE_HOME]/m6-paper/logs/run-p22-three-profile-72h-20260517T022156Z`
- Local run dir: `paper-trade-history/run-p22-three-profile-72h-20260517T022156Z/remote_run`

## Artifact Integrity
- Remote and local sha256sum lists match.
- Local checksums: `paper-trade-history/run-p22-three-profile-72h-20260517T022156Z/reports/local_sha256sum.txt`
- Remote checksums: `paper-trade-history/run-p22-three-profile-72h-20260517T022156Z/reports/remote_sha256sum.txt`
- Diff file: `paper-trade-history/run-p22-three-profile-72h-20260517T022156Z/reports/sha256sum.diff` (empty means match)

## Health Summary
- Health events: `{'booting_observe_only': 1, 'market_p2b_set': 228, 'market_resolved': 222, 'market_resolved_meta': 222, 'model_profiles_loaded': 1, 'order_lifecycle': 1170, 'shutdown_signal': 1, 'unsettled_at_shutdown': 3, 'worker_spawned': 76}`
- Metadata rows: `76`, valid rule rows: `76`, invalid rule rows: `0`

## Model Ranking By NAV Delta
| rank | profile | nav_last | nav_delta_total | decisions | submitted | filled | cancelled | open | realized_pnl | fee | trade_events |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `m3_b1` | `200.0507` | `+100.0507` | `88414` | `71` | `61` | `29` | `0` | `+100.0508` | `6.1093` | `321` |
| 2 | `m3_b2` | `0.9412` | `-99.0588` | `88414` | `127` | `98` | `87` | `0` | `-99.0588` | `1.8565` | `621` |
| 3 | `m5_baseline` | `0.4470` | `-99.5530` | `88414` | `88` | `71` | `56` | `0` | `-99.5529` | `0.2968` | `450` |

## Conclusion
- Best model in this stopped run: `m3_b1` with NAV delta `+100.0507`.
- `m5_baseline` and `m3_b2` both ended near zero NAV and should be treated as failed in this run, not competitive candidates.
- `m3_b1` is the only profile that preserved and grew capital through the observed window.
- Because the run was manually stopped after about 6.22h rather than completing 72h, this is an early-stop conclusion, not a full 72h conclusion.

## Key Local Files
- Standard markdown report: `paper-trade-history/run-p22-three-profile-72h-20260517T022156Z/reports/report-20260517T083623Z.md`
- Standard JSON report: `paper-trade-history/run-p22-three-profile-72h-20260517T022156Z/reports/report-20260517T083623Z.json`
- Final conclusion markdown: `paper-trade-history/run-p22-three-profile-72h-20260517T022156Z/reports/final_conclusion.md`
- Final conclusion JSON: `paper-trade-history/run-p22-three-profile-72h-20260517T022156Z/reports/final_conclusion.json`
- Per-model trades: `paper-trade-history/run-p22-three-profile-72h-20260517T022156Z/remote_run/models/<profile_id>/trades.jsonl`
