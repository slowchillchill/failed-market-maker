# Phase 6.5 Train-Boundary Leaderboard

Verdict: `FAIL_NO_MAKER_EDGE`

decision-surface audit found identical decoded actions across all candidates, so replay leaderboard cannot identify a maker edge

Ranking uses replay metrics only. It excludes BC/RL loss, bundle existence, and smoke pass.

| Rank | Candidate | Windows | Total PnL | Mean PnL | Sharpe | Max DD | Trades | Rejects | Cancels | Active Quote | Control Delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed2` | 263 | 46401.528900 | 176.431669 | 16.544189 | 243.143000 | 3523885 | 0 | 12473465 | 0.809686 | 5.827500 |
| 2 | `primary_R6_C2_control_seq180_bs4096_ep30_lev0p25_sr0p1_sm0p0_seed2` | 263 | 46395.701400 | 176.409511 | 16.520638 | 238.757500 | 3523791 | 0 | 12473487 | 0.809684 | 0.000000 |
| 3 | `primary_R3_A6_seq120_bs2048_ep30_lev0p5_sr0p05_sm0p1_seed2` | 263 | 46373.296900 | 176.324323 | 16.542135 | 239.522300 | 3523716 | 0 | 12473369 | 0.809679 | -22.404500 |
| 4 | `primary_R2_A1_seq120_bs2048_ep30_lev0p5_sr0p0_sm0p1_seed2` | 263 | 46367.904600 | 176.303820 | 16.507845 | 239.490300 | 3523817 | 0 | 12473514 | 0.809690 | -27.796800 |
| 5 | `primary_R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed2` | 263 | 46366.356700 | 176.297934 | 16.521180 | 249.875300 | 3523649 | 0 | 12473397 | 0.809684 | -29.344700 |
| 6 | `primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed3` | 263 | 46360.578100 | 176.275962 | 16.535270 | 245.017100 | 3523801 | 0 | 12473511 | 0.809687 | -35.123300 |
| 7 | `primary_R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed1` | 263 | 46356.429100 | 176.260187 | 16.532733 | 244.811000 | 3523609 | 0 | 12473445 | 0.809677 | -39.272300 |

## Review Gate

{
  "paper_trade_approval": false,
  "phase66_independent_offline_test": {
    "not_started_reason": "FAIL_NO_MAKER_EDGE leaves no approved final candidate for Phase 6.6",
    "required_window": "20260514..20260518",
    "started": false
  },
  "reason": "decision-surface audit found identical decoded actions across all candidates, so replay leaderboard cannot identify a maker edge",
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
