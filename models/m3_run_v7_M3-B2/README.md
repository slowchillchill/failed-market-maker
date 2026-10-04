# m3_run_v7_M3-B2

<!-- scorecard:start -->
| Metric / 指标 | Result / 成绩 |
| --- | --- |
| Best epoch / 最佳轮次 | 12 |
| Train loss / 训练损失 | 0.299922 |
| Val AUC / 验证 AUC | 0.735113 |
| Test AUC / 测试 AUC | 0.713882 |
| Test top-decile EV / 测试最高十分位 EV | -0.086622 |

**Paper / 模拟盘 — all five runs / 全部五轮（USDC）**

| UTC run / 运行 | Metric / 口径 | PnL |
| --- | --- | --- |
| [20260517T022156Z](../../evidence/paper/run-p22-three-profile-72h-20260517T022156Z/reports/report-20260517T083623Z.json) | nav_delta_total | -99.0588 |
| [20260517T223411Z](../../evidence/paper/run-tpsl-three-profile-72h-no-raw-tp30-20260517T223411Z/final-reports/report-20260519T135915Z.json) | adjusted_total_pnl_usdc | +78.4222 |
| [20260519T141035Z](../../evidence/paper/run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z/codex_reports/report-20260522T234126Z.json) | adjusted_total_pnl_usdc | +43.0920 |
| [20260527T161918Z](../../evidence/paper/run-four-profile-72h-mpv2-restart-20260527T161918Z/reports/report-20260530T162518Z.json) | adjusted_total_pnl_usdc | -100.6707 |
| [20260602T135518Z](../../evidence/paper/run-four-profile-7d-direct-official-20260602T135518Z/reports/standard/report-terminated-20260607T122104Z.json) | adjusted_total_pnl_usdc | -224.9895 |

Signal outputs plus external execution/risk rules; June 2 run stopped early. Live N/A — no corresponding evidence. / 使用 signal 输出和外部执行风控；6 月 2 日运行提前结束。实盘 N/A：无对应证据。

[All results and limitations / 全部成绩与限制](../../RESULTS.md) · [完整中文](../../RESULTS.zh-CN.md)

<!-- scorecard:end -->

[English / 中文](../../README.md) · [Structured model record / 结构化记录](../../catalog/m3_run_v7_M3-B2.json)

**Architecture / 架构:** Causal TCN market branches + Chainlink MLP + causal Transformer (128 hidden, 2 layers, 4 heads) + classification / EV heads.

市场特征由因果TCN分支和Chainlink逐时刻MLP编码，再由两层因果Transformer融合，输出分类logits和EV。

**Parameters / 参数量:** 419556. Counts exclude non-trainable normalization/position buffers; ONNX-only counts derive from the preserved architecture and configuration. / 不含归一化及位置缓冲，ONNX-only参数量按原架构和配置计算。

**Weight version and gaps / 权重版本与缺口:** Original checkpoint: 65 features. Collection exports: 76 features, with added state/fusion and execution heads. Added-head training scores are N/A (no corresponding training evidence). Train-tree and paper-tree exports are distinct. / 原始权重为65维；collection为76维，新增头无对应训练成绩，训练侧与paper侧分别保留。

**Feature order / 特征顺序:** [contract](../../contracts/feature_cols.json). Normalization is inside the forward graph; use raw ordered features, do not normalize twice. See the colocated NPZ and graph buffers. / 前向内部执行归一化，应输入按顺序排列的原始特征，不要重复归一化，参见同目录NPZ和图缓冲。

**Runtime use / 实际输出使用:** B1/B2/M5 BC paper uses signal outputs with external execution and risk rules; not evidence that every execution head influenced actions. / B1、B2、M5 BC 模拟盘使用 signal 输出和外部执行风控规则，不证明全部执行头有效参与。

**Training parameters, data and split / 训练参数、数据及切分**

Raw market observations come from Polymarket, Binance and Chainlink. Data files are not redistributed. Published split/config manifests describe the historical train/validation/test boundaries; a retained manifest does not make the raw dataset downloadable. M3 checkpoints have data paths and historical split rules, but their referenced exact split manifests were not found locally: N/A. / 原始数据来自Polymarket、Binance、Chainlink，本包不分发数据集。M3权重保留数据路径和历史切分规则，但旧路径引用的精确切分清单未找到，为N/A。

<details>
<summary>Exact retained record / 完整留存记录</summary>

```json
{
  "seq_len": 100,
  "batch_size": 4096,
  "lr": 0.00056,
  "epochs": 30,
  "lambda_cls": 1.0,
  "lambda_ev": 0.5,
  "d_model": 128,
  "n_transformer_layers": 2,
  "dropout": 0.1,
  "output_dir": "poly-arb-ai/training/checkpoints/m3_run_v7_M3-B2",
  "device": "cuda",
  "num_workers": 8,
  "amp": true,
  "compile": true,
  "patience": 5,
  "weight_decay": 0.0001,
  "label_smoothing": 0.05,
  "warmup_epochs": 2,
  "ev_loss_fn": "huber",
  "nhead": 4,
  "split_info": "poly-arb-ai/training/split/split_info.v6expanded.json",
  "seed": 42,
  "ema_decay": 0.99,
  "feature_noise": 0.0,
  "focal_gamma": 0.0,
  "snapshot_epochs": ""
}
```

</details>

**Training / offline / paper / live results / 分层成绩**

<details>
<summary>Exact retained record / 完整留存记录</summary>

```json
{
  "best_epoch": 12,
  "train_loss": 0.2999222529466905,
  "val_auc": 0.7351134852246457,
  "test": {
    "auc": 0.7138815588138743,
    "brier": 0.27409004629649314,
    "ece": 0.2452327631933416,
    "ev_up_mae": 1.6587376760534323,
    "ev_up_rmse": 2.755799891158789,
    "ev_rank_corr": 0.0035322517724225315,
    "ev_down_mae": 1.654643851520991,
    "ev_down_rmse": 2.7519640914936017,
    "ev_up_sign_acc": 0.6480479949479002,
    "top_decile_mean_ev_up": -0.08662242966845597,
    "ev_up_conditional_mean_by_threshold": {
      "0.50": -0.021090989169416475,
      "0.52": -0.021324504641008483,
      "0.55": -0.020719908331812583,
      "0.60": -0.020873620767270215,
      "0.65": -0.02009865174274774
    },
    "ev_up_opportunity_rate_by_threshold": {
      "0.50": 0.3478855356968454,
      "0.52": 0.34567418934381855,
      "0.55": 0.342263121277999,
      "0.60": 0.3363308289896173,
      "0.65": 0.32952075036262946
    },
    "edge_by_decile": [
      0.10240084838936454,
      -0.05530123368410529,
      -0.07264870216185908,
      -0.03287912117262209,
      -0.058962474591456863,
      -0.04229088739360767,
      -0.005879217836146618,
      0.006309815623740446,
      0.01904438840259867,
      -0.08645479142688046
    ],
    "loss": 1.7292454365421743
  },
  "paper": "See run-specific paper table / 见逐次模拟盘表",
  "live": "N/A — no standalone corresponding run evidence / 未找到单体对应实盘证据"
}
```

</details>

[All run-specific results, offline comparisons and failure criteria / 全部逐次结果、离线对照与失败判据](../../RESULTS.md) · [中文完整结果](../../RESULTS.zh-CN.md). Maker Phase 6.5/6.6: `FAIL_NO_MAKER_EDGE`; Phase 6.7: `FAIL_CONTROL_AMPLIFICATION`. Offline replay PnL is never substituted for test loss. / 离线回放收益不能代替测试损失。

**Evidence and files / 证据与文件**

- [best_model.pt](https://huggingface.co/slowchillchill/failed-market-maker/resolve/main/models/m3_run_v7_M3-B2/best_model.pt)
- [feature_stats.npz](https://huggingface.co/slowchillchill/failed-market-maker/resolve/main/models/m3_run_v7_M3-B2/feature_stats.npz)
- [run_metadata.json](run_metadata.json)
- [test_metrics.json](test_metrics.json)
- [train_history.json](train_history.json)

[Unified file/source/license manifest / 统一来源许可证清单](../../manifest.json). Original code/weights: Apache-2.0. Curated card/reports: CC-BY-4.0. Synthetic-forward success proves executability only, not learned profitability. / 原创代码权重Apache-2.0，整理模型卡及报告CC-BY-4.0，构造输入只证明可运行。

**Complete retained loss traces / 全部留存损失曲线**

Separate panels keep different objectives on their own scales; BC and RL epoch counters restart by stage. / 不同目标分别展示，BC与RL轮次在各阶段重新计数。

![Retained loss curves / 留存损失曲线](../../figures/m3_run_v7_M3-B2.svg)
