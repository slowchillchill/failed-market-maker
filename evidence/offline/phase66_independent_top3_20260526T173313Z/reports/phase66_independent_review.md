# Phase 6.6 Independent Offline Replay Review

Verdict: `FAIL_NO_MAKER_EDGE`

decision-surface audit found identical decoded actions across the reviewed candidates

Ranking uses independent replay metrics only. It excludes BC/RL loss, bundle existence, and smoke pass.

| Rank | Candidate | Windows | Total PnL | Mean PnL | Sharpe | Max DD | Trades | Rejects | Cancels | Active Quote | Control Delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed2` | 30 | 5336.603800 | 177.886793 | 12.147838 | 0.000000 | 299619 | 0 | 1350046 | 0.761452 | 4.268200 |
| 2 | `primary_R3_A6_seq120_bs2048_ep30_lev0p5_sr0p05_sm0p1_seed2` | 30 | 5334.889200 | 177.829640 | 12.151941 | 0.000000 | 299531 | 0 | 1350027 | 0.761419 | 2.553600 |
| 3 | `primary_R6_C2_control_seq180_bs4096_ep30_lev0p25_sr0p1_sm0p0_seed2` | 30 | 5332.335600 | 177.744520 | 12.120207 | 0.000000 | 299614 | 0 | 1350060 | 0.761438 | 0.000000 |

## Review Gate

{
  "paper_trade_approval": false,
  "phase66_independent_offline_test": {
    "required_window": "20260514..20260518",
    "started": true
  },
  "reason": "decision-surface audit found identical decoded actions across the reviewed candidates",
  "verdict": "FAIL_NO_MAKER_EDGE"
}

## Decision Surface

{
  "action_surface_identical": true,
  "alpha_pairwise_max_abs_diff_max": 5.192193031311035,
  "alpha_pairwise_mean_abs_diff_max": 0.9150745868682861,
  "alpha_pairwise_mean_abs_diff_min": 0.270534873008728,
  "available": true,
  "candidate_count": 7,
  "common_policy_rows": 50000,
  "differing_decoded_rows": 0,
  "disabled_reason_counts_identical": true,
  "enabled_slot_counts_identical": true,
  "identical_decoded_row_ratio": 1.0,
  "legal_quote_margin_mean_max": 0.4500000000000002,
  "legal_quote_margin_mean_min": 0.449999991714942,
  "legal_quote_margin_min": 0.44979704618453975,
  "per_slot_difference_counts": [
    0,
    0,
    0,
    0
  ]
}
