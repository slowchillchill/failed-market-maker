# Phase 6.5 Train-Boundary Leaderboard

Verdict: `FAIL_CONTROL_AMPLIFICATION`

control candidate ranks first by train-boundary replay PnL

Ranking uses replay metrics only. It excludes BC/RL loss, bundle existence, and smoke pass.

| Rank | Candidate | Windows | Total PnL | Mean PnL | Sharpe | Max DD | Trades | Rejects | Cancels | Active Quote | Control Delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `phase67_C0_control_anchor` | 263 | 45844.681500 | 174.314378 | 16.435665 | 229.077900 | 3510921 | 0 | 12437353 | 0.807031 | 0.000000 |
| 2 | `phase67_P1_signed_reward_filter` | 263 | 6867.812000 | 26.113354 | 10.975787 | 86.040100 | 178028 | 0 | 463411 | 0.030938 | -38976.869500 |

## Review Gate

{
  "paper_trade_approval": false,
  "phase66_independent_offline_test": {
    "not_started_reason": "FAIL_CONTROL_AMPLIFICATION leaves no approved final candidate for Phase 6.6",
    "required_window": "20260514..20260518",
    "started": false
  },
  "reason": "control candidate ranks first by train-boundary replay PnL",
  "verdict": "FAIL_CONTROL_AMPLIFICATION"
}

## Decision Surface

{
  "action_surface_identical": false,
  "alpha_pairwise_max_abs_diff_max": null,
  "alpha_pairwise_mean_abs_diff_max": null,
  "alpha_pairwise_mean_abs_diff_min": null,
  "available": true,
  "candidate_count": 0,
  "common_policy_rows": 0,
  "differing_decoded_rows": 0,
  "disabled_reason_counts_identical": true,
  "enabled_slot_counts_identical": true,
  "identical_decoded_row_ratio": null,
  "legal_quote_margin_mean_max": null,
  "legal_quote_margin_mean_min": null,
  "legal_quote_margin_min": null,
  "per_slot_difference_counts": []
}
