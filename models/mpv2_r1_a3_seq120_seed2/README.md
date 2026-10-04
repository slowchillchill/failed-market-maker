# mpv2_r1_a3_seq120_seed2

[English / 中文](../../README.md) · [Structured model record / 结构化记录](../../catalog/mpv2_r1_a3_seq120_seed2.json)

**Architecture / 架构:** Alpha R1 A3 seed2 + MakerPolicy R1 A3 seed2.

R1 A3 seed2的Alpha和Policy组合；Alpha分类与EV拼接为4维Policy输入。

**Parameters / 参数量:** See component cards / 见组件模型卡. Counts exclude non-trainable normalization/position buffers; ONNX-only counts derive from the preserved architecture and configuration. / 不含归一化及位置缓冲，ONNX-only参数量按原架构和配置计算。

**Weight version and gaps / 权重版本与缺口:** Deployment copy, not a 25th trained model. Paper and live results belong to this combination. / 部署组合不算第25个训练候选；paper/live成绩仅归属该组合。

**Feature order / 特征顺序:** [contract](../../models/mpv2_r1_a3_seq120_seed2/feature_spec.json). Normalization is inside the forward graph; use raw ordered features, do not normalize twice. See the colocated NPZ and graph buffers. / 前向内部执行归一化，应输入按顺序排列的原始特征，不要重复归一化，参见同目录NPZ和图缓冲。

**Runtime use / 实际输出使用:** Alpha output is concatenated and passed to policy; runtime executes interpreted quote targets. / Alpha输出拼接后输入Policy，运行时解释报价目标。

**Training parameters, data and split / 训练参数、数据及切分**

Raw market observations come from Polymarket, Binance and Chainlink. Data files are not redistributed. Published split/config manifests describe the historical train/validation/test boundaries; a retained manifest does not make the raw dataset downloadable. M3 checkpoints have data paths and historical split rules, but their referenced exact split manifests were not found locally: N/A. / 原始数据来自Polymarket、Binance、Chainlink，本包不分发数据集。M3权重保留数据路径和历史切分规则，但旧路径引用的精确切分清单未找到，为N/A。

```json
{
  "alpha_order": [
    "signal_logits[0]",
    "signal_logits[1]",
    "signal_ev[0]",
    "signal_ev[1]"
  ],
  "account_state": [
    "cash",
    "nav_before",
    "shares_up",
    "shares_down",
    "active_resting_count"
  ],
  "cash_nav_unit": "USDC, not raw token units",
  "features": [
    1,
    120,
    160
  ]
}
```

**Training / offline / paper / live results / 分层成绩**

```json
{
  "paper": "See run-specific paper table / 见逐次模拟盘表",
  "live": "See local-ledger table; platform final PnL unavailable / 见本地账本表，平台最终收益不可用"
}
```

[All run-specific results, offline comparisons and failure criteria / 全部逐次结果、离线对照与失败判据](../../RESULTS.md) · [中文完整结果](../../RESULTS.zh-CN.md). Maker Phase 6.5/6.6: `FAIL_NO_MAKER_EDGE`; Phase 6.7: `FAIL_CONTROL_AMPLIFICATION`. Offline replay PnL is never substituted for test loss. / 离线回放收益不能代替测试损失。

**Evidence and files / 证据与文件**

- [feature_spec.json](feature_spec.json)
- [normalization.npz](https://huggingface.co/slowchillchill/failed-market-maker/resolve/main/models/mpv2_r1_a3_seq120_seed2/normalization.npz)

[Unified file/source/license manifest / 统一来源许可证清单](../../manifest.json). Original code/weights: Apache-2.0. Curated card/reports: CC-BY-4.0. Synthetic-forward success proves executability only, not learned profitability. / 原创代码权重Apache-2.0，整理模型卡及报告CC-BY-4.0，构造输入只证明可运行。
