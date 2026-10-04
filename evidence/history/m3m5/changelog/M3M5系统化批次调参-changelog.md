# M3M5 系统化批次调参 — 执行变更日志

对应方案：[`plan/M3M5系统化批次调参方案.md`](../plan/M3M5系统化批次调参方案.md)

本文件记录方案的执行进展、关键决策、验证结果与偏离原方案的地方。CLAUDE.md §"方案文档与 changelog（强制）" 要求 plan 与 dev 一一对应；此文件随方案推进追加。

---

## Stage 0 — 基础设施 + Holdout 诊断

### 状态：代码全部完成；smoke 验证进行中

### 代码改动（11 项）

| # | 文件 | 状态 | 备注 |
|:---|:-----|:-----|:-----|
| 1 | `training/loss.py` | ✅ done | 新增 `focal_loss(γ, label_smoothing, weight, logit_clamp)`；`signal_loss` 增 `focal_gamma` 参数；γ=0 退化为 weighted CE |
| 2 | `training/train.py` | ✅ done | 新增 `ModelEMA`（unwrap `_orig_mod` 兼容 `torch.compile`）+ `_set_seed` + `_parse_snapshot_epochs`；5 flag `--seed --ema-decay --feature-noise --focal-gamma --snapshot-epochs`；val 评估走 swap→eval→restore；best ckpt 在 EMA 启用时存 shadow；snapshot 缺失 epoch 仅 WARN；新写 `run_metadata.json` sidecar 不破坏 `train_history.json` 的 list-shape |
| 3 | `training/train_oracle_bc.py` | ✅ done | 4 flag `--seed --ema-decay --class-balance{none,inv_freq,inv_freq_0.75} --focal-gamma`；`_resolve_class_weights` 解耦 `oracle_mode` 与 `class_balance`；`_bc_cls_loss` 路由 focal/CE；EMA 共享 `train.py` 的 `ModelEMA`；best ckpt 存 shadow |
| 4 | `training/train_iql.py` | ✅ done | 新增 `--seed`；既有 `--init-agent-checkpoint` 改 `strict=False`，输出 `missing_keys / unexpected_keys` 摘要；docstring 明确 BC partial warm-start 用法 |
| 5 | `training/validate_transitions.py` | ✅ done | 新增 `--ignore-reward-range`；G2 在 reward_minimal 模式下走 SKIP 分支；G1/G3 仍 hard fail；空 reward 边缘情况也走 SKIP |
| 6 | `rust/agent/src/baseline_strategies.rs` + `main.rs` | ✅ done | `BaselineConfig.fixed_limit_level` 字段 + override；`--fixed-limit-level` CLI flag 接受 `join-best/improve1/improve2/passive1/passive2`（hyphen 与 snake 兼容）；`aggregate.json.run_config` 写入；新增单元测试 `fixed_limit_level_overrides`（覆盖 default / override / 与 `force_order_type=Limit` 共存 三场景）|
| 7 | `training/candidate_ledger.py` | ✅ done | 双 leaderboard schema (backbone + full_policy) + 不同权重；`register / attach-metrics / show / rank` CLI；min-max 归一化（`val_top10_5ep_std` 走 LOWER_IS_BETTER 反转）；`show --field` 支持 dotted path |
| 8 | `scripts/eval_rolling_segments.py` | ✅ done | 读 per-window `<dataset>__<window>.json` PerformanceMetrics → 按 `window_id` 时间序切 N 段 → 输出 `median/worst/best/mean PnL`；零额外 GPU 成本 |
| 9 | `scripts/dataloader_sample_count_sanity.py` | ✅ done | 多 seq_len 下 split 有效样本数表格输出 |
| 10 | `scripts/run_one_m3.sh / run_one_bc.sh / run_one_iql.sh` | ✅ done | 一键 train + export ONNX + K2-C eval（M3 走 `--strategy signal --signal-threshold 0.58 --force-order-type limit --fixed-size medium --fixed-limit-level join-best --override-risk-score 1.0`；BC/IQL 走 agent+fixed exec 同口径）+ rolling 后处理 + ledger register/attach |
| 11 | `scripts/ensemble_inference.py` | ✅ done | 多 ONNX 平均 logits/ev → `compute_metrics` offline `top_decile_mean_ev_up` / AUC；ONNX 输出按名取（`signal_logits` / `signal_ev`）；first-batch logits std 非零 sanity check |

### Smoke 验证（GPU 服务器执行；plan §3.8 / §10）

| 检查项 | 状态 | 实测 |
|:-------|:-----|:-----|
| Python 5+4+1+1 个新 flag 注册（train / train_oracle_bc / train_iql / validate_transitions）| ✅ PASS | `--help \| grep` 全部命中 |
| Rust `--fixed-limit-level` CLI flag + 5 类枚举 parse | ✅ PASS | `cargo run -p agent -- evaluate --help` 命中 |
| Rust 单元测试 `fixed_limit_level_overrides` | ✅ PASS | `cargo test -p agent fixed_limit_level_overrides`：1 passed; 0 failed |
| ledger CRUD（双 leaderboard register / attach-metrics / rank / `--field run_id` 单字段输出）| ✅ PASS | smoke 脚本输出 backbone / full_policy 双榜各 1 候选，`--field run_id` 输出干净（shell-loop 友好）|
| `validate_transitions.py --ignore-reward-range` G2 SKIP + G1/G3 hard fail + exit 0 | ✅ PASS | v6 现有 `tick_stream/data-v1_reward_minimal.parquet` 实测：G1 PASS（NAV<0=0.0）/ G2 SKIP / G3 PASS（entropy=1.41）/ exit 0 |
| `eval_rolling_segments.py` 后处理（v6 baseline `m3_v6_collection_signal__val/`，24 windows → 5 段）| ✅ PASS | 5 段加和 -313.13 与 v6 已知 m3_collection signal val PnL 完全对齐（median=-48.04 / worst=-117.58）|
| **M3-A0 anchor 1-epoch smoke**（5 套 parquet, default flags = v6 同口径）| ✅ PASS | `ulimit -n 65535` + batch=128 / seq=240 / num-workers=4 / amp / no compile / no EMA / no seed。**结果**：train_loss 1.77 / val_loss 4.08（ep1，未过拟合）；test `auc=0.7740 / top_decile_mean_ev_up=+0.0520 / ev_up_sign_acc=0.6286 / brier=0.2323`。`run_metadata.json` 显示 `snapshot_epochs=[] / ema_decay=0.0 / seed=null / feature_noise=0 / focal_gamma=0`，等价 v6 baseline。`train_history.json` 保持 list-shape 向后兼容。`best_model.pt` 5.4MB 落盘。**default 行为未破坏**（5 个新 flag 全 0/None 时训练完全等价 v6 baseline）|

#### Smoke 详细对照

v6 baseline（30 epoch 早停 E10）参考：`auc=0.7517 / top_decile_mean_ev_up=-0.0272`（E10 已过拟合；E05 best 是 +0.123）。

本次 1 epoch smoke 的 +0.0520 与 v6 训练曲线 E01 量级吻合（v6 训练初期 top10_ev 在 0~0.1 区间），符合"刚学到方向信号还未过拟合"的预期。这只是 1-epoch smoke，目的是验证 default 行为不破坏 + 全产物落盘流程；不是 M3-A0 完整 30-epoch anchor 跑（那是 Stage 1A 的内容）。

`ulimit -n 65535` 是必须前置环境项；首次未带它跑挂在 val eval 第 231 batch（`Too many open files`）。已记入手册，所有 Stage 1+ 训练命令必须前置 `ulimit -n 65535`。

#### Smoke 已发现的环境必备项

- **`ulimit -n 65535` 是 train.py multi-worker DataLoader 跑 5 套 parquet val/test eval 的硬性前提**（v6expanded 执行总结也提到过；本次再次验证）
  - 不带 `ulimit` 时，val eval 走到 ~5% (231/4097 batches) 即 `RuntimeError: Too many open files`
  - 加 `ulimit -n 65535` 重跑后 train epoch 进入正常进度（30+ batch/s）
  - 已记入运行手册，所有 Stage 1+ 训练命令都必须前置 `ulimit -n 65535`

### 与 plan §3 的偏离 / 决策记录

| 点 | plan 写法 | 实施差异 | 理由 |
|:---|:---------|:--------|:-----|
| `train.py` `run_metadata.json` | plan §3.1 未提；plan §3.7 提 ledger 用 `train_history.json` | 实际新建 `run_metadata.json` 作为 sidecar | `train_history.json` 是 list-shape，下游 reader（如未来调用方）可能依赖；保持兼容；新元信息（snapshot warning / seed / EMA decay / focal_gamma 等 run-level）放 sidecar 文件 |
| `train_iql.py` flag 数 | plan §3.4 写"新增 1 个 flag + 复用既有 flag" | 严格只新增 `--seed`；`--init-agent-checkpoint` 复用 + docstring 补充 | 与 plan 一致；多打印一行 missing/unexpected keys 摘要便于排查 partial load |
| `train_iql.py` 的 EMA | plan §6 未提 IQL EMA | 不实施 | plan §6.1 IQL 矩阵未引入 EMA；本计划不动该文件的 EMA。如未来 IQL 需要 EMA，要再做一次小改造（_save_checkpoint 也要支持 shadow 路径）|
| `--fixed-limit-level` 接受字符串 | plan §3.5 写"枚举字符串：`join-best / improve1 / improve2 / passive1 / passive2`" | 同时支持 `joinbest` / `improve_1` / `improve-1` 等变体（snake/camel/hyphen 互通）| 用户脚本经常混用大小写/连字符；放宽 parse 不影响安全性 |
| `eval_rolling_segments.py` 排序 | plan §3.6 写"按 window_id（前缀是 epoch 秒）排序" | 实施同时按 `(epoch_seconds, dataset_version)` 双键排序 | 跨 dv 同 epoch_seconds 时给确定性顺序，避免不同环境下 `glob` 顺序漂移导致段切分非确定 |
| `ensemble_inference.py` 的 `--feature-stats` | plan §3.7 / §3.8 默认必传 | 实施改 optional + first-batch logits std 非零 sanity check | collection ONNX 的 InputNormalizer 已 baked-in，预归一化是 redundant；保留 flag 作 forward-compat 但默认不读 |

### Plan 文档修正（review 反馈采纳）

| 修正点 | 文件 | 内容 |
|:------|:-----|:-----|
| §6.4 Stage 3.5 `--field onnx_path` / `--field seq_len` 路径错（实际字段是 `paths.onnx` / `config.seq_len`）| `plan/M3M5系统化批次调参方案.md:556-557` | 改为 `--field paths.onnx` 与 `--field config.seq_len`，并加注 ledger entry 结构说明 |

### 其他小修（review P2 采纳）

- `run_one_iql.sh` collapse 检测：从"任何 epoch 命中 `probe_gap.*-0\.9`"改为"读取**最后一次** `probe_gap` 与 `hold_argmax_share` 数值"——避免训练中段瞬时 dip 误标 `iql_collapsed=true`
- `ensemble_inference.py` first-batch sanity：检测 logits std < 1e-3 时立即抛 `RuntimeError`（提早发现 ONNX 没带 normalizer 的回归 bug）
- `ensemble_inference.py` docstring：明确依赖 `export_onnx.py --mode collection` 输出名 `signal_logits / signal_ev`，未来重命名要同步 `_onnx_forward_signal_only`

---

## Stage 1A — M3 pilot batch sweep

### 状态：M3-A0 anchor 启动中

### 配置（与 plan §4.2 一致）

| ID | seq | batch | lr | loss | warmup | label_smooth | seed | EMA | focal | feat_noise | 备注 |
|:---|----:|------:|---:|:-----|-------:|-------------:|-----:|----:|------:|-----------:|:-----|
| **M3-A0**（anchor，**不进 ledger**）| 240 | 128 | 1e-4 | mse | 0 | 0.0 | 42 | 0 | 0 | 0 | 严格 v6 同口径 + seed；不带 `--compile`；compromise C：epoch 1 完成后 kill |
| M3-A1 | 100 | 128 | 1e-4 | huber | 2 | 0.05 | 42 | 0 | 0 | 0 | 最慢；chain 末位跑 |
| M3-A2 | 100 | 256 | 1.5e-4 | huber | 2 | 0.05 | 42 | 0 | 0 | 0 | sqrt-ish lr |
| M3-A3 | 100 | 512 | 2e-4 | huber | 2 | 0.05 | 42 | 0 | 0 | 0 | sqrt-ish lr |
| M3-A4 | 100 | 1024 | 3e-4 | huber | 2 | 0.05 | 42 | 0 | 0 | 0 | sqrt-ish lr |
| M3-A5 | 100 | 2048 | 4e-4 | huber | 2 | 0.05 | 42 | 0 | 0 | 0 | m3_run3 同口径；chain 头位 |
| **M3-A6**（用户决策扩展）| 100 | **4096** | **5.6e-4** | huber | 2 | 0.05 | 42 | 0 | 0 | 0 | sqrt-ish lr 外推；测大 batch sweet spot |
| **M3-A7**（用户决策扩展）| 100 | **8192** | **8e-4** | huber | 2 | 0.05 | 42 | 0 | 0 | 0 | sqrt-ish lr 外推；v6 数据 3.5x 于 v3 → sweet spot 可能上移 |

**Sweep 扩展决策（2026-05-01 17:30）**：原 plan §4.2 batch ∈ {128, 256, 512, 1024, 2048} 上限锚定 m3_run3 baseline。但 30+ 历史实验在 v3（~1.5M 帧）上做的；v6expanded（5.4M 帧，3.5x）上 step/epoch 同口径要求 batch ≈ 7000-8000。用户决策追加 M3-A6 (batch=4096) + M3-A7 (batch=8192)，sqrt-ish lr 缩放 (5.6e-4 / 8e-4)，物理 5090 32GB 完全 fit（VRAM 估 ~6-14GB）。边际成本 ~20min wall。

### 启动命令样板

`ulimit -n 65535` 是必须前置环境项。M3-A0 anchor 用直接 train.py（不进 ledger）；M3-A1..A5 用 `scripts/run_one_m3.sh`（一键 train + ONNX + K2-C signal+fixed eval + rolling 后处理 + ledger register）。

```bash
# M3-A0 anchor（不进 ledger；GPU server 上 nohup 后台跑）
ulimit -n 65535
PYTHONPATH=poly-arb-ai [PRIVATE_ROOT]/miniconda3/bin/python -u poly-arb-ai/training/train.py \
  --parquet-paths model/feature-engine/out/features_250ms_data-v{1..5}.parquet \
  --split-info poly-arb-ai/training/split/split_info.v6expanded.json \
  --output-dir poly-arb-ai/training/checkpoints/m3_run_v7_M3-A0 \
  --epochs 30 --patience 5 \
  --batch-size 128 --seq-len 240 --lr 1e-4 \
  --ev-loss-fn mse --warmup-epochs 0 --label-smoothing 0.0 \
  --d-model 128 --n-transformer-layers 2 --nhead 4 --dropout 0.1 \
  --lambda-cls 1.0 --lambda-ev 0.5 --weight-decay 1e-4 \
  --device cuda --num-workers 8 --amp \
  --seed 42

# M3-A1..A5 with run_one_m3.sh
export PARQUETS="model/feature-engine/out/features_250ms_data-v1.parquet ... v5.parquet"
export SPLIT_INFO=poly-arb-ai/training/split/split_info.v6expanded.json
./poly-arb-ai/scripts/run_one_m3.sh m3_run_v7_M3-A1 100 -- \
  --batch-size 128 --lr 1e-4 --ev-loss-fn huber --warmup-epochs 2 --label-smoothing 0.05 \
  --epochs 30 --patience 5 \
  --d-model 128 --n-transformer-layers 2 --nhead 4 --dropout 0.1 \
  --lambda-cls 1.0 --lambda-ev 0.5 --weight-decay 1e-4 \
  --seed 42
```

### 进度

- **2026-05-01 16:36 UTC+8**: M3-A0 anchor 启动（PID 7944, nohup, batch=128 + AMP, 不带 compile）
- **2026-05-01 17:00**: M3-A0 E01/30 完成；E01 metrics: `train_loss=1.7849 val_loss=3.5792 val_auc=0.782 val_brier=0.228 val_ev_sign_acc=0.632 val_top10_ev=+0.0918`（1445.3s wall = 24min/epoch；v6 实测同口径）；GPU util 18% / VRAM 1.4GB（M3 模型 + batch=128 严重 GPU 饥饿）
- **2026-05-01 17:01**: 按 compromise C，kill M3-A0（已验证 default 行为；epoch 1 quality 健康超过 v6 训练曲线 E01 量级）；保留 best_model.pt + epoch_summaries.txt；不再 30 epoch 跑
- **2026-05-01 17:13**: M3-A5 (batch=2048, lr=4e-4, huber+T08+compile) 启动；E10/30 时 GPU util 跃升至 **72% / VRAM 4.1GB**（batch=2048 + compile 让 epoch 时长降到 ~84s/epoch，比 anchor 24min **17x faster**）
- **2026-05-01 17:30**: 用户决策扩展 sweep 加 M3-A6 (batch=4096) + M3-A7 (batch=8192)；chain 脚本启动（PID 11755）等 M3-A5 完成后顺序跑 A6 → A7 → A4 → A3 → A2 → A1
- **2026-05-01 18:06**: M3-A5 (batch=2048) 入榜 — val_top10_ev=+0.1455 / **val K2-C PnL=-13.30** / rolling worst=-48.63（K2-C eval ~33min/run 是真正瓶颈，远高于初估）
- **2026-05-01 19:10**: M3-A6 (batch=4096) 入榜 — val_top10_ev=+0.1627 / **val K2-C PnL=+280.11 ⭐ 突破** / rolling median=+41.12 / rolling worst=-7.94（**通过 Pre-1B Gate 全部三条**：val PnL > 0 且 val_top10 > +0.10 且 rolling worst > -100；vs v6 baseline -313 提升 +593）
- **2026-05-01 19:40**: GPU 利用率验证 — batch=128 → 18% util / VRAM 1.4GB；batch=2048 + compile → 72% util / VRAM 4.1GB；batch=4096+ → 70-90% util。实证用户担忧的"v6 batch=128 严重 GPU 饥饿"问题；m3_run3 历史 batch=2048 在 v6 数据规模 (5.4M, 3.5x of v3) 下不再是 sweet spot
- **2026-05-01 20:12**: M3-A7 (batch=8192) 入榜 — val_top10_ev=**+0.1763**（最高） / val K2-C PnL=+64.02 / rolling worst=**-65.43 ⚠️**。**Trend 转折**：信号能力（val_top10_ev）单调上升，但端到端 PnL 倒 U 形（A6 +280 >> A7 +64）。原因：大 batch + 激进 lr → sharp minima → fat tail（A7 worst -65 vs A6 -8 = 8x 恶化）。**结论**：不需追加 batch ≥ 8192，sweet spot 在 [3072, 5120] 区间
- **2026-05-01 20:24**: 用户决策 B+C — kill A1 (节省 4-5h) + 加细粒度 sweep batch ∈ {3072, 5120, 6144} 精化 sweet spot；首次 watch_v1 启动后立即 regex bug（`run_one_m3.sh.*M3-A1` 模式过宽）误判触发，prematurely launch A8。Kill A8 + 重启 watch_v2 用 ledger-based trigger（监听 M3-A2 metrics attach）
- **2026-05-01 20:55**: 发现 watch_v1 (PID 29801) 我之前 pkill 没杀干净，仍在跑 A9 (batch=5120)。GPU 双 process contention（A4 eval + A9 eval）。Cleanup：杀 watch_v1 + watch_v2 + A9 leftover；重启 intercept_v2 (PID 38841) 单一协调点
- **2026-05-01 21:30**: M3-A4 (batch=1024) 入榜 — val_top10_ev=+0.1688 / val K2-C PnL=**+112.39** / rolling worst=-28.32。trend 复杂化：1024 → 2048 (drop) → 4096 (peak) → 8192 (drop) — 像 W 形而非简单倒 U；A5 (2048) 可能是 noise outlier
- **2026-05-01 23:08**: M3-A3 (batch=512) 入榜 — val_top10_ev=+0.1291 / **val K2-C PnL=+279.35 ⭐ 几乎并列 A6** / rolling median=**+73.81 ⭐** / rolling worst=**-74.89 ⚠️**。**Surprise double peak**：trend 不是单峰，是 double-peak（batch=512 + batch=4096 都是 local optima）。差别在 fat tail：A6 mean 高 + 稳；A3 mean 高 + 高方差。**Pre-1B Gate 多 candidate 通过**：A6 (主)、A4 (备 1) 都符合
- **2026-05-01 23:08**: 用户决策 ALL（不跳 A2）。A2 train ~165min（batch=256 慢），ETA Stage 1A 完成 ~04:32 next day

### Stage 1A 当前 Backbone 榜（截至 2026-05-01 23:09，5 datapoint）

| Rank | Run | Batch | LR | best_epoch | **val_top10_ev** | **val K2-C PnL** | rolling median | rolling worst | score |
|-----:|:----|------:|---:|----------:|----------------:|----------------:|---------------:|--------------:|------:|
| 1 | **M3-A6** | 4096 | 5.6e-4 | E15 | +0.1627 | **+280.11** | +41.12 | **-7.94** | 0.732 |
| 2 | M3-A4 | 1024 | 3e-4 | E6 | +0.1688 | +112.39 | +33.27 | -28.32 | 0.625 |
| 3 | M3-A7 | 8192 | 8e-4 | E14 | **+0.1763** | +64.02 | +25.06 | -65.43 | 0.500 |
| 4 | M3-A3 | 512 | 2e-4 | E6 | +0.1291 | +279.35 | **+73.81** | -74.89 | 0.449 |
| 5 | M3-A5 | 2048 | 4e-4 | E6 | +0.1455 | -13.30 | -6.08 | -48.63 | 0.295 |

### Stage 1A pending（chain + intercept_v2）

| Run | Batch | LR | 排队状态 | 预估完成 |
|:----|------:|---:|:---------|:--------|
### Stage 1A B+C ALL 收官（2026-05-02 05:09）— 8 datapoint 完整榜

| Rank | Run | Batch | lr | val_top10 | val PnL | rolling worst | std | score |
|:----:|:----|------:|----:|---------:|--------:|--------------:|----:|------:|
| 🥇 | **A6** | **4096** | 5.6e-4 | 0.163 | **+280** | **-8** ⭐ | 0.024 | **0.692** |
| 🥈 | **A10** | **6144** | 6.9e-4 | **+0.263** ⭐ | +39 | -20 | **0.013** ⭐ | 0.635 |
| 🥉 | A3 | 512 | 2e-4 | 0.129 | +279 | -75 | 0.027 | 0.619 |
| 4 | A2 | 256 | 1.5e-4 | 0.228 | +222 | -57 | 0.049 | 0.610 |
| 5 | A4 | 1024 | 3e-4 | 0.169 | +112 | -28 | 0.017 | 0.547 |
| 6 | A7 | 8192 | 8e-4 | 0.176 | +64 | -65 | 0.019 | 0.453 |
| 7 | A9 | 5120 | 6.3e-4 | 0.198 | +108 | **-148** ⚠️ | 0.027 | 0.448 |
| 8 | A8 | 3072 | 4.9e-4 | 0.172 | +89 | -42 | 0.017 | 0.415 |
| 9 | A5 | 2048 | 4e-4 | 0.146 | -13 | -49 | 0.013 | 0.301 |
| skip | ~~A1~~ | ~~128~~ | ~~1e-4~~ | - | - | - | - | - |

### 关键执行教训（已修方案均已 apply）

- **`pgrep -f "run_one_m3.sh.*M3-A1"` regex 过宽**：误匹配某 substring，导致 watch_v1 启动后立即 trigger A8。修法：用 ledger-based trigger（轮询 `candidates_ledger.json` 中 M3-A2 metrics attach）替代进程级 grep
- **GPU contention**：单 5090 同时跑两个 train.py + agent evaluate 会让 throughput 各自降到一半。设计 chain + intercept 时务必单线串行
- **K2-C eval ~33min/run 是 sequential bottleneck**（不是 train 时长）。这意味着 batch sweep 中 7 个 run 的 K2-C eval 总和 ~3.5h，不论 batch 大小如何
- **Stage 1A 实际 ETA 比 plan 估计更长**（最长 batch=128 单 run 5h+，最短 batch=8192 单 run 40min）。plan §4.5 的 "10-15h" 估计偏乐观，剔除 batch=128 + 加细粒度 sweep 后总长 ~11h（含 K2-C eval 约占一半时间）

### Pre-1B Gate 状态（已通过 — A6 anchor）

通过条件（plan §4.2）：top-1 by Backbone 榜 score 必须满足任一：(a) val K2-C signal+fixed PnL > 0；(b) val_top10_ev_up > +0.10。

- **A6 同时通过 Pre-1B Gate (a) + (b)**：val PnL +280, val_top10 +0.1627
- 同时 **A6 提前满足 Pre-Stage 2 Gate**（plan §4.4）成分：rolling worst -8 > -100, 5ep std 0.024 < 0.05
- A2/A3/A4/A10 也都通过 Pre-1B Gate（各 score ≥ 0.55）
- A5 (2048) 未通过 Pre-1B Gate (a)：val PnL -13；但通过 (b) val_top10 +0.146

注：rolling worst > -100 + 5ep std < 0.05 是 **Pre-Stage 2 Gate** 的成分（plan §4.4），不是 Pre-1B Gate 的成分。Pre-1B Gate 严格只看 (a) val PnL OR (b) val_top10 二选一。前一稿 dev 把它们一起写成 "all 4 hard gates" 是术语错。

### 双 sweet spot 结构（核心发现）

batch sweep 揭示两个**互不重叠**的 sweet spot：

1. **A6 (4096, lr=5.6e-4) = PnL-stability sweet spot**
   - PnL 第一（+280） + fat tail 最低（-8）
   - val_top10 仅排第 6（+0.163）但 K2-C 阈值切信号最准
   - **唯一同时高 PnL + 高稳定性的 unique winner**

2. **A10 (6144, lr=6.9e-4) = signal-stability sweet spot**
   - val_top10 第一（+0.263）+ 5ep std 最稳定（0.013）+ fat tail 第三（-20）
   - **K2-C PnL 仅 +39** —— 极端 signal-PnL 解耦
   - 模型在 top10% EV-up frames 上 ranking 极强，但 K2-C 阈值 0.58 切出的不一定是 top10%
   - 暗示 Stage 1B 可加 signal_threshold calibration 子实验（0.55 / 0.58 / 0.60）

### A10 解耦根因实证（fee 假说否定）

K2-C eval 不直接输出 fee，用 trade 活动代理（A6/A10 都 fixed-size medium，fee 与 trade count 强相关）：

| 指标 | A6 | A10 | A10/A6 比 |
|:-----|---:|----:|---------:|
| PnL | +280.11 | +39.05 | 0.139x |
| n_trades | 1974 | 1921 | **0.973x** |
| trades / market | 2.196 | 2.137 | **0.973x** |
| in-position ratio | 0.916 | 0.912 | **0.996x** |
| PnL / trade | +0.142 | +0.020 | **0.143x** |

**结论**：
- A10 的 trade 频率/在场比例与 A6 几乎相同 → **fee 总量 ≈ 相等**
- 因此 "fee+slippage 吃 PnL" 假设（method 改造无法修）**被实证否定**
- A10 PnL/trade 仅 A6 的 0.143x → A10 选错方向/时机的 trade 占比高
- 真实根因 = **noise overfit（train 末期）** 或 **signal head 在 K2-C 阈值附近 calibration 差**
- 两者都是 EMA / Label Smoothing / Focal Loss 可修方向 → Stage 1B 的 B' (A10 + EMA + LS) 子实验 ROI 实证支持

### Stage 1B central config（已决策）

- **首选 A6 (batch=4096, lr=5.6e-4, T08 baseline)** — PnL 是最终目标，A6 唯一 PnL + stability 双冠
- 备选 A10 (batch=6144, lr=6.9e-4) — signal 极强但 PnL 弱，可在 Stage 1B 加 1-2 个 A10 variant 测能否通过 EMA / method 改造把 signal 转化为 PnL

### 下一步

- ✅ Stage 1A 全部完成（8 datapoint 全榜 + Pre-1B Gate passed + dev 文档同步）
- ✅ Stage 1B 启动前置：EMA + compile + Focal γ=2 三 flag 合并 1-epoch smoke PASS（task b56jcsono / 2026-05-02 09:14-09:24 / val_top10=+0.0476 / cls_loss 不 NaN / EMA 权重已更新 / compile graph 无冲突）
- ⏭ Stage 1B-A 启动（central=A6 + 8 method configs B1-B8）
- ⏭ Stage 1B-B' 接续（A10 + EMA(0.999) + A10 + EMA(0.999) + LS(0.10) 共 2 configs）
- ⏭ Stage 1B-C 接续（A6/A10 × {0.55, 0.60} 共 4 个 K2-C threshold calibration eval；只入 dev-docs，不入 ledger）

### Stage 1B 启动 bug 与 chain relaunch（2026-05-02 09:37-10:09）

- **2026-05-02 09:37**: 首次启动 Stage 1B chain (PID 76839)，B1 立即 register_run 成功后 train.py 用 `--loss huber` flag 退出
- **bug 根因**: chain script 的 `A6_FLAGS` / `A10_FLAGS` 写了 `--loss huber`，但 `train.py` argparse 注册的 flag 是 `--ev-loss-fn {mse,huber}`（见 train.py CLI help 输出）。Stage 1A 的 chain 不带 loss flag（默认 mse）所以未暴露
- **影响**: chain set -e 触发立即退出；09:37 → 10:09 共 32 min wall clock wasted；ledger 留 1 个 NaN B1 entry + 1 个之前 stale 的 A1 NaN entry
- **修复**: `sed -i "s|--loss huber|--ev-loss-fn huber|g" scripts_stage1b_chain.sh`；清理 2 个 stale ledger entry；删除 `checkpoints/m3_run_v7_M3-B1` 残骸（实际未生成）；relaunch chain
- **2026-05-02 10:09:46**: chain relaunch 成功，B1 真正进入 train phase（PID 77762/77771/77778 三层进程齐全）
- **教训**: 包装脚本写新 flag 时**必须先 `python3 train.py --help | grep <flag-name>` 确认 argparse 注册名**，而不是凭记忆用历史 flag 别名。Stage 1A chain 因为不传 loss flag 走了默认 mse，掩盖了这个 flag 别名问题，到 1B 才暴露
- **ETA 修正**: Stage 1B + C ALL 收官从原 ~20:10 推后到 **~20:45 server**（+35 min wasted time）


### Stage 1B 中期数据（B1-B8 + B11 完成，B12 + B0-s123 + C 待跑）

实测时间线（chain 10:09:46 启动）。**当前 Backbone ledger interim ranking**（截至 2026-05-02 ~18:30 server，所有 9 个有数据点已 attached + 全榜 min-max 重归一化；source: `candidate_ledger.py rank --leaderboard backbone`）：

| Rank | Run | 配置 | best_ep | val_top10 | val PnL | rolling worst | rolling median | score |
|:----:|:----|:-----|--------:|----------:|--------:|--------------:|---------------:|------:|
| 1 | B1 | A6 + EMA 0.999 | 13 | +0.1665 | +424.40 | +16.37 | +103.54 | **0.8085** |
| 2 | B8 | A6 + EMA 0.999 + snapshot-epochs (B1 duplicate) | 13 | +0.1665 | +424.40 | +16.37 | +103.54 | **0.8085** |
| 3 | B2 | A6 + EMA 0.99 | 12 | +0.1734 | +415.72 | +19.11 | +74.17 | 0.7731 |
| 4 | B5 | A6 + EMA + Focal γ=2 | 11 | +0.1343 | +212.15 | +13.96 | +44.85 | 0.6064 |
| 5 | A6 | baseline (no EMA) | 15 | +0.1627 | +280.11 | -7.94 | +41.12 | 0.5961 |
| 6 | B7 | A6 + EMA + Feat Noise 0.05 | 1 | +0.0704 | +268.10 | +9.40 | +55.77 | 0.5670 |
| 7 | A10 | (Stage 1A) | 9 | +0.2632 | +39.05 | -19.81 | +9.90 | 0.5633 |
| 8 | B3 | A6 + EMA + seed=123 | 8 | +0.1901 | +181.45 | +4.24 | +17.27 | 0.5424 |
| 9 | A3 | (Stage 1A) | 6 | +0.1291 | +279.35 | -74.89 | +73.81 | 0.5364 |
| 10 | B11 | A10 + EMA 0.999 | 9 | +0.2085 | +154.46 | -46.76 | +32.39 | 0.5327 |
| 11 | B4 | A6 + EMA + seed=7 | 1 | +0.0775 | +305.20 | +3.91 | +62.57 | 0.5296 |
| 12 | A2 | (Stage 1A) | 9 | +0.2282 | +221.72 | -56.81 | +42.13 | 0.5153 |

**Stage 1B method sweep 完成 7/8 + B' 1/2 + B0-s123 0/1**。最终 Stage 1C top-3 必须用 canonical `candidate_ledger.py rank --leaderboard backbone` 在所有 chain (B12 + B0-s123) 跑完后重算 + **应用 duplicate 去重原则（见下）**。

### Stage 1C duplicate 去重原则（当前 plan 未明确，本次 changelog 显式增补）

plan §4.4 line 393 仅写 "合并 1A + 1B ledger entry + §1 加权打分 + top-3 test confirmation"，**没有 duplicate filter**。机械执行会让 B1 / B8 同时占 top-3 两个 slot（4 位小数 identical → score tie），浪费 1 个 unique test slot。

**本次 changelog 显式增补规则**：
- B8 single-best ckpt = B1 best_ckpt 的 4 位小数级 reproduce（snapshot-epochs flag 是 side output，不影响 train loss / EMA / weight update）
- **B8 不占 Stage 1C unique top-3 slot**；Stage 1C top-3 = B1 + B2 + 第三名（按 score 顺位）
- B8 的 Snapshot Ensemble 收益评估**仅** 通过 `ensemble_inference.py` 平均 ep 3/5/7 ckpts logits → offline val_top10_ev_up 对比 B1 single-best；**只入 dev-docs，不入 ledger，不进 paper**

**强 enforcement 来源**：约束来自 wrapper 命令（`run_one_m3.sh` 调 `agent evaluate` 单 ONNX + `export_onnx.py --mode collection`）+ plan §4.3 line 380 `B8 K2-C eval 仅用 single best ckpt`。**ledger 仅记录 single-best 结果，不主动 enforce**——前一稿 dev 写的 "ledger 自动 enforce plan §4.3" 措辞错。

### B11 (A10 + EMA 0.999) 实测：部分改善 PnL，fat tail 恶化

source: ledger row #10 + B11 segments JSON

| 维度 | A10 baseline | **B11 (A10+EMA)** | 变化 |
|:-----|-------------:|------------------:|:----:|
| val PnL | +39.05 | **+154.46** | **+295%** ⭐ |
| val_top10 | +0.2632 | +0.2085 | -21% |
| rolling worst | -19.81 | **-46.76** ⚠️ | **fat tail 恶化 -2.36x** |
| rolling median | +9.90 | +32.39 | +227% |
| score | 0.5633 (#7) | 0.5327 (**#10**) | -0.03 / 跌 3 位 |

**结论降级**：B11 不是"EMA 修 A10 解耦成功"。EMA 部分改善 A10 的 total PnL（+39 → +154，~4x），但 **fat tail 恶化（rolling worst -19 → -47）**，综合 score 反而下降，**rank 从 #7 降到 #10**——**未进入 Stage 1B top group**。

**对 Stage 1B 的 implication**：A10 base + EMA 没解 A10 解耦谜题。Mechanism 不是 "train 末期 noise overfit"（如果是，EMA 应同时改善 PnL + fat tail）。等 B12 (A10 + EMA + LS) 看是否更糟或反转。

### 数据更正记录

### 数据更正记录

| 日期 | 字段 | 旧值 | 新值 | Source | Impact |
|:-----|:-----|-----:|-----:|:-------|:-------|
| 2026-05-02 17:00 | B6 rolling_worst | +13.79 | **-11.85** | `eval/v7/m3_run_v7_M3-B6__val_segments.json` (mtime 15:44:19，5 segment totals = [0.05, 70.70, 29.97, -11.85, 61.69]，worst_pnl=min) + ledger `k2c_signal_fixed_val_rolling_worst` 字段 | 修正 fat tail 评估：B6 (LS 0.10) 不仅 PnL 退 -46% (vs B1)，**rolling worst 也从 EMA-only 的 +16 退到 -12**——LS 0.10 在 EMA 之上**双重退化** (PnL + fat tail)。修正前的 +13.79 是凭印象写未核 ledger，已修正流程：以后所有 changelog 数值必须从 canonical source（ledger / segments JSON）dump，禁止凭印象。 |
| 2026-05-02 17:00 | B6/B7 score "(待重排)" | 占位符 | **B6=0.5003, B7=0.5670** | `candidate_ledger.py rank --leaderboard backbone` 当前实际输出 | 全榜重归一化后所有 score 都微调（B1 0.804 → 0.8085, B2 0.769 → 0.7731 etc）；Stage 1B interim top-3 仍是 B1/B2/B5，但 B7 实际进 #5（高于 A10 排第 6） |
| 2026-05-02 18:30 | B8 n_trades = 1967 来源 | 标 "canonical ledger" | 实际 `eval/v7/m3_run_v7_M3-B8__val/aggregate.json` 字段 `n_trades_total` | ledger schema 仅 5 metric 字段 (k2c_signal_fixed_val_pnl/rolling_median/rolling_worst, val_top10_ev_up, val_top10_5ep_std)，**不含 n_trades**；trade-level 字段在 `aggregate.json` (n_trades_total / n_buy_total / n_sell_total / mean_trades_per_market 等) | 修正 source attribution：以后 changelog 引用 PnL/rolling_worst/val_top10/std 用 ledger，引用 n_trades / flat_ratio / n_markets / mean_sharpe 等用 aggregate.json |
| 2026-05-02 18:30 | "ledger 自动 enforce plan §4.3" | 不严谨措辞 | 改 "约束来自 wrapper 命令 + plan §4.3 line 380；ledger 仅记录 single-best" | wrapper `run_one_m3.sh` 内嵌 `agent evaluate` 单 ONNX + `export_onnx.py --mode collection` | ledger 是 record store 不是 enforcer；强约束的层是 pipeline command 设计 |

### B4 / B7 mode 实证特征（Z1 + Z2 诊断；机制结论降级为 observation）

B4 是首个被诊断的 short-holding run；B4 + B7 都落入 short-holding family（B4 in-pos=0.514 / B7 in-pos=0.361）。B4 全 24 windows 一致 short-holding：

- in-pos 范围 [0.33, 0.63]，histogram 0/4/17/3/0
- 24 windows 中 18 个正盈利 / 6 个亏损（与 B1 17/7 接近）
- PnL 范围 [-29, +56]（比 B1 [-26, +71] 还窄）
- max drawdown mean 18.4%（vs B1 21.9% / A6 22.8%）— dd 最低
- n_trades 83.7/window 略高（vs baseline 80-82）+ in-pos 51% → 平均持仓时间是 baseline 的 ~56%
- 24 windows cross-window robust（不是 lucky 偶然，但仍是 val 表现）

**机制结论降级（采纳审查）**：

- ❌ "frequent flip / prob ~0.58 阈值反复切换" — K2-C eval 输出无 trades.json / decision trace / probability histogram，仅 per-window aggregate；无法 verify trade-level flip pattern 或 prob 分布；只能说 "平均持仓时间显著短于 baseline"
- ❌ "alternative valid strategy" / "portfolio diversification" — val 24 windows robust ≠ test/paper 可用；要主张组合多样化需 (i) B1 vs B4/B7 per-window PnL 相关性分析 (ii) Stage 1C test confirmation 通过；当前为 hypothesis 不是 conclusion

### B7 mode 数据 + mechanism observation（不下结论）

B7 (A6 + EMA + Feature Noise 0.05) 实测：

- val PnL = +268.10
- val_top10 = +0.0704（best_ep=1，与 B4 接近）
- in-pos = 0.361（**比 B4 的 0.514 还低**）
- n_trades 1413（vs baseline 1970，少 -28%）

**B4 vs B7 共同点**：best_ep=1 + in-pos < 0.7 + val_top10 < 0.10
**B4 vs B7 差异**：B4 是 (seed=7, EMA), B7 是 (seed=42, EMA + Feature Noise) — 多变量混杂

**审查 #4 采纳**：仅能 observe "两个 best_ep=1 相关配置都落入 short-holding family"。**不能** 隔离 isolate "EMA + best_ep=1 系统性触发"为 mechanism — 至少需要：
- (seed=42, EMA, no FeatNoise, best_ep=1 自然出现) — 当前没有这个 cell
- 或 trades.json + decision trace 验证 within-run 行为

### EMA × seed 矩阵（部分填充）

|           | seed=42  | seed=123      | seed=7   |
|:----------|:--------:|:-------------:|:--------:|
| no EMA    | A6=+280 | B0-s123=PEND | (缺) |
| EMA 0.999 | B1=+424 | B3=+181 | B4=+305 (mode outlier) |

只能 robust disentangle：
- seed=42 下 EMA gain = +144（已知）
- seed=123 下 EMA gain = 181 - B0-s123（pending，区间预估 [-19, +131]）
- seed=7 下 EMA gain 不能算（B4 是 mode outlier，main effect ANOVA 假设破坏）

→ "EMA effect 跨 seed 是否 robust" 当前是 **hypothesis 不是 conclusion**。

### Stage 1B method sweep 阶段性结论（已采纳审查校正）

✅ **EMA 0.999 / 0.99（B1/B2）显著提升 PnL** （+50% vs A6 +280）
✅ **EMA effect plateau**（B1 / B2 差距仅 2%，多 decay 值都 work）
✅ **multi-seed K2-C PnL 高 spread**（B1+424 / B3+181 / B4+305，sample std $121.5）
❌ Focal γ=2（B5 +212）+ LS 0.10（B6 +151）在 EMA 之上**进一步退化** — 但 mechanism 不同：
  - LS 0.10 改 target → output prob 压缩 → fee 区间偏移（fee 公式机制：fee max 在 p=0.667 处 ~1.07%）
  - Focal γ=2 改 per-sample weight → confident 区学习被 deprioritize（不直接改 target / output prob）
🟡 Snapshot Ensemble (B8) + A10 base (B11/B12) **数据未到，不能外推 "modifier 全 lose"**

### 审查纠正记录（2026-05-02 多轮 audit）

| 错误 | 纠正 |
|:-----|:-----|
| "ensemble 进 paper trading" 违反 plan §1/§3.7 hard constraint（Rust evaluate 单 ONNX）| 撤回，B-ens 仅作 offline val_top10_ev_up 诊断 |
| "EMA E1 末几乎全初始化"错误 | E1 末 0.999^1321 ≈ 27% init / 73% trained（batch=4096 假设）|
| "ensemble PnL ≈ N-seed PnL 算术平均" Jensen 陷阱 | K2-C 阈值切 + fee 公式都是 p 的非线性，N-seed mean ≠ ensemble logits average 后 PnL |
| "fee p=0.75 = 0.91%" 算错 | 实际 1.01%；fee max 在 p=0.667 处 1.07% |
| "3-seed std $99" 用 population formula | 应用 sample std (n-1) = $121.5 |
| "EMA + 任何 modifier 都退化" 过度概括 | Snapshot/A10 数据未到，仅"已测 3 modifier 都退化" |
| 三机制统一归"calibration shift" | LS/Focal/FeatNoise mechanism 路径不同，未来加新 modifier 需 mechanism-specific 分析 |
| "加 B0-s7 完成 5/6 cell + EMA main effect 95% CI" | B4 是 mode outlier 非 seed outlier，main effect ANOVA 假设破坏，撤回；plan §7.2 paper trading 不依赖 fully-crossed disentangle |

### Stage 1B + B0-s123 + C calibration 完整 finale（2026-05-02 22:55:17 全部完成）

**实测时间线**：

| 时刻 | 事件 |
|:-----|:-----|
| 10:09:46 | Stage 1B chain start (B1) |
| 11:10-15:44 | B1/B2/B3/B4/B5/B6 chain 完成 |
| 16:28 | B7 done (PnL +268, in-pos 0.361 short-holding) |
| 17:28 | B8 done (4-decimal reproduce of B1) |
| 18:22 | B11 done (A10+EMA, PnL +154 fat tail -47) |
| 19:20:10 | B12 done → **chain ALL DONE** (10 configs B1-B8 + B11/B12) |
| 19:21:01 | watchdog 自动触发 M3-B0-s123 |
| 20:21:38 | M3-B0-s123 done (PnL +144.25) → watchdog 自然退出 |
| 20:35:08 | **GPU idle 14 min**（watchdog 漏接 C）→ 手动启动 calibration |
| 22:55:17 | C 4 calibration evals 全完 |

**Final Backbone Ledger top 6**（17 datapoint canonical ranking，2026-05-02 23:09 dump）：

| Rank | Run | score | val PnL | rolling worst | val_top10 | 5ep std |
|:----:|:----|------:|--------:|--------------:|----------:|--------:|
| 1 | B1 | **0.8085** | +424.40 | +16.37 | +0.1665 | 0.0247 |
| 2 | B8 | 0.8085 | +424.40 | +16.37 | +0.1665 | 0.0247 |
| 3 | B2 | 0.7731 | +415.72 | +19.11 | +0.1734 | 0.0223 |
| 4 | B5 | 0.6064 | +212.15 | +13.96 | +0.1343 | 0.0070 |
| 5 | A6 | 0.5961 | +280.11 | -7.94 | +0.1627 | 0.0236 |
| 6 | B7 | 0.5670 | +268.10 | +9.40 | +0.0704 | 0.0079 |

### EMA × seed disentangle 完整数据（B0-s123 attached 后）

| | seed=42 | seed=123 |
|:--|:------:|:------:|
| no EMA | A6: PnL +280 / val_top10 +0.163 | **B0-s123: PnL +144 / val_top10 +0.156** |
| EMA 0.999 | B1: PnL +424 / val_top10 +0.167 | B3: PnL +181 / val_top10 +0.190 |
| **EMA PnL gain** | **+144** (51%↑) | **+37** (26%↑) |

**核心结论**：EMA effect 真的 **seed-dependent on PnL dimension**。seed=42 EMA boost 是 seed=123 的 ~3.9x。"EMA + multi-seed 平均必然 +X 提升" plan §0 隐含假设**不严格成立**。但在两个 seed 下 EMA 都给正向 PnL gain（不是 +144 也不是 0），**真实 seed-averaged EMA gain 估计 ≈ +90/seed** 而非单 seed=42 观察的 +144。

### threshold calibration 完整结论（A10 解耦谜题答案）

source: `eval/v7/m3_run_v7_M3-{A6,A10}__val_thr{055,060}/aggregate.json` + ledger baseline 0.58

| Run | 0.55 | 0.58 (baseline) | 0.60 |
|:----|----:|---:|---:|
| **A6** | +248.84 | **+280.11** ⭐ sweet spot | +253.96 |
| **A10** | +30.07 | +39.05 | **-34.23** ⚠️ 反向 |

**A6 calibration**：0.58 是 K2-C 协议默认值的 **structural sweet spot**，跨 ±0.02 阈值 PnL 仅降 9-11%（robust），无法通过 threshold tuning 改善。

**A10 calibration**：跨阈值 PnL 都低（+30 / +39 / -34），threshold **不是** A10 解耦的主因。A10 × 0.60 PnL 跌为 -34 揭示 A10 在 prob > 0.60 高 confidence 区是 **反向 prediction**（confidence 高 + 方向错）。**A10 解耦真实 mechanism 在 model 端，不在 K2-C 协议**——任何 threshold 都不能救活 A10 K2-C PnL。A10 不是 paper trading candidate（按 plan §7.2）。

### B8 解读约束（Snapshot Ensemble；plan §4.3 line 380 强制）

plan §4.3 line 380 明确：
- B8 K2-C eval **仅用 single best ckpt**（与其他 run 一样进 backbone 榜，单 ONNX）
- snapshot 的 ensemble 效应**仅 Python offline 对照**

→ B8 进入 ledger 的 single-best K2-C PnL **不能解读为 "Snapshot Ensemble 帮助"**。B8 = B1 同 train flag + snapshot save 副产物，best_ep 由 patience 决定，B8 single-best K2-C PnL = B1 4-decimal identical（实测 PnL=424.3953 / rolling_worst=16.3697 / val_top10=0.1665 / score=0.8085 完全相同）—— 这是 **reproduce / no-op test** 性质。**真正的 snapshot ensemble 收益**只能通过 `ensemble_inference.py` 算 averaged val_top10_ev_up vs single-best 来评估，结果只入 dev-docs，不入 ledger 不进 paper。

### B' 剩余 6 configs 追加决策：不追加（数据自动 derive）

之前设计的追加触发条件（plan §4.3 B' 扩展子实验）：

| 触发条件 | 追加 method | 实际数据 |
|:---------|:------------|:--------|
| B' 任一显著改善 A10（PnL > +200）| 加 Feat Noise / Focal / Snapshot × 3 = ~4.5h GPU | ❌ B11 +154 (fat tail -47 恶化) / B12 +58 退化 |
| C 显示 A10 在 0.55 / 0.60 PnL > +180 | 加 Multi-seed × 3 = ~4.5h GPU | ❌ A10 × 0.55 +30 / × 0.60 -34 |
| B' 都没改善 + C 也都低 | **不追加，A10 转 backbone backup** | ✅ **当前数据满足** |

**决策**：**不追加** — 实证数据完整否决追加：
- A10 + EMA (B11): PnL +154 但 fat tail rolling worst 恶化 2.4x（-19 → -47）
- A10 + EMA + LS (B12): PnL 退回到 +58
- A10 × 任何 threshold: 都低或反向 (+30 / +39 / -34)
- → A10 解耦 mechanism 在 model 端，不是任何 K2-C 协议 modifier 能修

追加 Feature Noise / Focal / Snapshot / Multi-seed × A10 = 浪费 ~4.5h GPU 换"再次 confirm A10 不能救活"。**A10 转 backbone backup**（M5 BC agent route 阶段仍可作为非 K2-C 协议下的 backbone candidate 评估）。

### Stage 1C top-3 候选选定（含人工 override）

**默认 by score**: B1 (0.8085) + B2 (0.7731) + B5 (0.6064)（B8 按 duplicate 去重 skip）

**实际人工 override**: B1 + B2 + **A6** (0.5961) — 用 A6 替换 B5

**override reasoning**（plan §4.4 人工 override 条款要求 documented）：
- B5 vs A6 score 差距仅 1.7%（0.6064 vs 0.5961，well within 5% override 上限）
- A6 PnL +280 显著高于 B5 +212（PnL 维度更强 +32%）
- A6 val_top10 +0.163 高于 B5 +0.134（信号维度更强）
- B5 (Focal γ=2 modifier) 已实证在 v6 上 PnL 退化（B5 +212 < B1 +424），mechanism 是"hard examples 加权 → confident 区学习被 deprioritize"——即使 test 上通过 gate，也是 modifier 退化的弱版本，paper trading 价值低于 baseline A6
- A6 是**所有 B-family 的 base config**——A6 通过 test confirmation = baseline structure 在 test 上 robust，比 modifier 通过更有 mechanism robustness
- 用户决策：选可解释性 / 简洁性 / mechanism robustness 优先

**Stage 1C 最终 top-3**：B1 / B2 / A6

### Stage 1C 完整 finale + Pre-Paper-Trading Gate 决议（2026-05-03 00:40:35 完成）

**Stage 1C top-3 test split 完整数据**（3 candidates × test split K2-C signal+fixed eval，含 rolling segments 后处理）：

| Candidate | val PnL | **test PnL** | test sharpe | **test rolling worst** | val→test drop |
|:----------|--------:|-------------:|------------:|-----------------------:|:-------------:|
| **B1** (主候选 by val) | +424.40 | **+92.28** | 1.063 | **-40.44** | -78% |
| B2 (备选 1 by val rank) | +415.72 | **+137.83** ⭐ | **1.410** ⭐ | **+5.33** ⭐ | -67% |
| A6 (override of B5) | +280.11 | +85.53 | 1.069 | -30.77 | -69% |

**Pre-Paper-Trading Gate (Backbone) — top-1 by val (= B1) check**：
- ✅ B1 test PnL +92.28 > 0
- ✅ B1 test rolling worst -40.44 > -100
- → **B1 进 paper trading 主候选**

**Pre-Paper-Trading Gate — top-2 by val (= B2) check**：
- ✅ B2 test PnL +137.83 > 0
- ✅ B2 test rolling worst +5.33 > -100
- → **B2 进 paper trading 备选 1**（B2 测试上 outperform B1，但按 plan §4.4 严格 rule 不能因 test 重新排序——B1 仍是主候选）

**A6 override result**：A6 test PnL +85.53 也通过 gate，但作为 override 候选不进 paper（按 plan §7.2 主候选 = top-1 by val + 备选 1 = top-2 by val 严格规则），A6 留作"override 候选确认 robust"的诊断意义。

**Pre-Stage 2 Gate check**（plan §4.4）：
- Backbone top-1 (B1) val PnL +424 > 0 ✅
- Backbone top-1 (B1) val rolling worst +16.37 > -100 ✅
- → **Pre-Stage 2 Gate PASSED** — 可启动 Stage 2 (M5 BC)

**val→test gap 关键观察**：
- B1: -78% drop（val +424 → test +92）
- B2: -67% drop（val +416 → test +138）
- A6: -69% drop（val +280 → test +86）

**EMA benefit on test 实际**：
- val 维度：B1 +424 vs A6 +280 → EMA +51% benefit
- **test 维度**：B1 +92 vs A6 +86 → EMA **+7%** benefit（实际 K2-C edge）
- → val 上 +51% EMA benefit 大部分是 lucky high (val 数据集偏好 + seed=42 basin 偏好)，**真实 test edge 仅 +7%**
- 这强化"single-seed K2-C PnL 高方差"假设——paper trading 时**真实 PnL estimate 应取 test +85-138 区间**而非 val +280-424

**B2 在 test 上 outperform B1 的解读**：
- val 上 B1 (+424) > B2 (+416) by 2%（borderline，well within K2-C noise spread $121.5）
- test 上 B2 (+138) > B1 (+92) by 49%
- B2 (EMA 0.99 更激进) test rolling worst +5.33（**全 5 segments 正盈利**）vs B1 -40.44
- **B2 generalize 比 B1 略好**（不能 prove，paper trading 仍按 val 严格 ranking）
- 这是 plan §4.4 "test 不能重新排序" 严格规则的有意 trade-off：避免 test 泄漏 > 选 best test PnL

### 流程教训：watchdog 漏接 C calibration

**事件**：B0-s123 watchdog 设计只 trigger M3-B0-s123 一次就 exit，没有 chain 到 C calibration。chain ALL DONE 后 GPU idle 14 min（22:55:17 → 23:09 用户报告 GPU 0%），需手动启动 C。

**根因**：设计 multi-stage pipeline 时只 enumerate "current trigger"，没明确"trigger 完成后下一步"。我之前说"watchdog 接 C"实际没实现 chain logic。

**改进**：以后设计 multi-stage pipeline 必须画完整 dependency graph + 在每个 trigger 处显式列出"完成后下一步是 manual / auto / 串入 chain 哪个 script"。


---

## Stage 2 — 启动准备（2026-05-03）

### v7 Hold baseline spot-check（实测）

source: `eval/v7/v7_hold_baseline_val/aggregate.json` + `_segments.json`

| 字段 | 值 |
|:-----|:---:|
| val total PnL | **-8.09** |
| val rolling median | +0.85 |
| val rolling worst | -5.79 |
| 5 segment totals | [-5.79, -5.25, +1.12, +0.85, +0.99] |
| flat_ratio | 0.9768（settlement-only trades, n=43）|
| n_windows | 24 |

**对 plan 的影响**：plan §4.4 / §5.4 / §6.4 / §11 原 Pre-Stage 3 Gate 阈值 -26（v6 reference）→ 已实测更新为 **-8.09**（v7expanded 实测）。Living-doc 原则不留 v6/v7 对比注释，4 处全改 -26 → -8.09。

### Phase A1 commit (4357f99) per-M3 subgroup normalization

`fix(ledger): add --group-by-config-key for per-M3 BC ranking`

- file: `poly-arb-ai/training/candidate_ledger.py` (+76 / -25 lines)
- core change: `compute_scores()` 新增 `group_by_config_key` 参数；entries 按 `config[group_by_config_key]` 分组后**各组独立 min-max normalize**（不再全榜 flat normalize）
- CLI: 新增 `--group-by-config-key` flag；markdown table 加 `subgroup` 列；default behavior（无 flag）= flat normalize 完全不变

**E2E verify**（用 4 fake BC entries：B1 group {PnL +100, +200} + B2 group {PnL +10, +50}）：

| 模式 | top-1 | top-2 | top-3 | top-4 |
|:-----|:------|:------|:------|:------|
| Flat normalize（错误，conflate）| B1_1 (1.00, 200) | B1_0 (0.46, 100) | B2_1 (0.35, 50) | B2_0 (0.00, 10) |
| **--group-by-config-key m3_id** | B1_1 (1.00 in M3-B1) | **B2_1 (1.00 in M3-B2)** | B1_0 (0.00) | B2_0 (0.00) |

→ subgroup 模式让 winners 在各自子组内 surface（**plan §1 line 68 期望行为**）。这不是 silent flat normalize，是**真正的 per-M3 子分组归一化**。

### Phase A2 v6 reference 误带过来的修复

plan 原写"top-1 BC val PnL > Hold baseline (-26)"是 v6 reference 直接 carry over，没在 v7 数据上验证。Audit C4 建议 spot-check Hold baseline。实测后差距 ~$18，按数据驱动用 -8.09。

### Stage 2 chain 模式（已确认）

- **sequential B1 → B2**（实现简单，复用 Stage 1B chain 模式）
- **mid-B1 early abort**: BC-0/1/2/3 × B1 完成后 max(agent val PnL) < -50 → 直接跳到 Pre-Stage 3 Gate fail dump（节省 ~20h GPU on hopeless config）

### BC oracle dimension untested（Stage 2 mid-chain 实证发现）

source: BC-0 vs BC-3 best_model.pt md5 collision (`a6b7192e670791b521cb5abf6661306b` 完全相同) + ONNX md5 collision (`3435f004d34ee0813c08567c8bdb52e1`) + train log sample count identical (`train=5542314` vs `train=5542314`) + epoch 1 train_loss 1.5个4位小数完全相同

**Root cause（已确诊）**：
- `oracle_bc_dataset.py:237-238`: oracle C 与 oracle B 唯一差异是 drop margin < `oracle_c_threshold` 的 episode；保留下来的 sample target 完全一致
- `compute_oracle_c_threshold()` 用 `np.quantile(margins, 0.7)` 算 threshold (margins = `abs((resolution - p2b) / p2b)`)
- 在 v7expanded BTC UP/DOWN 二元期权数据上，BC-0/BC-3 sample count 完全 identical → **0 episode 被 drop** → filter 是 no-op
- 推断：v7expanded margin 分布让 quantile(0.7) 算出来的 threshold 比所有 market margin 都低（可能 binary outcome resolution=0/1 + p2b 范围让所有 |resolution - p2b|/p2b 都集中在 ≥ threshold 区间）

**Implication**：
- plan §5.2 BC oracle 维度（B vs C-0.7）**本轮实际未测**
- BC sweep 实际只测了 batch / class_balance / focal / ema / seed 5 个维度（4 个独立差异 + BC-3 等价 BC-0）
- BC-3 ledger entry 已 attach marker（`_excluded_from_ranking=true` + `_duplicate_of=BC-0` + `_duplicate_root_cause=...`），保审计 trail
- Phase 4 ranking 时 jq filter 排除 `_excluded_from_ranking=true` entries

**Stage 3 风险检查**（已 verify）：
- `train_iql.py` grep `oracle_mode|OracleBCDataset` 输出**空** → IQL 不用 oracle BC dataset
- → **Stage 3 IQL 不受此 bug 影响**，可正常启动（待 Pre-Stage 3 Gate 通过）

**修法待 Stage 3 启动前评估**：
- (a) 修 `compute_oracle_c_threshold()` 使其在 v7 数据上产生有效 filter
- (b) 直接传 `--oracle-c-threshold X` 显式 override 跳过 quantile 计算
- (c) 留作"已知未测"维度，未来若有 ad-hoc GPU 时间补 1-config mini-sweep（不破坏当前 Stage 2 ETA）

### Stage 2 backbone scope 扩展：追加 A6（user 决策 2026-05-03 ~09:00）

**变更**：Stage 2 backbone scope 从 plan 原 "top-2 by val score (B1 + B2)" 扩展为 **B1 + B2 + A6** 共 3 个 backbone × 8 BC configs each = 24 BC runs（plus conditional BC-7 触发）。

**A6 追加 reasoning**：
- A6 是 Stage 1C 的 **B5 → A6 人工 override** 候选 + Pre-Paper-Trading Gate PASS（test PnL +85.53 / rolling worst -30.77）
- A6 baseline (no EMA) 与 B1/B2 (EMA 系) backbone 训出的 transition 数据分布显著不同 → BC × A6 不能从 BC × B1/B2 推断
- 多 backbone full-policy 候选给 paper trading 备选 2 路线更多备份
- 当前 BC × B1 进展超 expectations（max +106 vs v6 baseline -251），Stage 2 是高 ROI 阶段，加 A6 边际价值高

**chain 改造方案**：
- 当前 chain (PID 129319) 跑完 B1 + B2 后**自然结束**，scripts/stage2_chain.sh 不动
- 写新 chain `scripts/stage2_chain_a6.sh`：collect-transitions A6 + validate G1/G3 + BC-0..7 × A6 + Phase 4 全榜 Gate dump（含 A6 entries）
- 通过 watchdog 监听 chain `m3_run_v7_M3-B2_BC-7`（或 chain "ALL DONE" marker）退出后自动启动 A6 chain
- 若 mid-B1 abort 触发（不太可能 - max=+106），watchdog 也检测到 abort marker 并 skip A6 (因 B1 已 fail，A6 大概率也 fail)

**ETA 影响**：
- 原 plan §5.5 估 ~25-33h（top-2 backbone）
- 加 A6 后估 ~38-50h（含 +~9-10h）
- 当前 chain 启动 02:33:44，B1 phase ~13-15h，B2 phase ~13-15h，A6 phase ~9-10h
- 全 Stage 2 完成 ETA：**~05:00 next day server**（B1 phase 已过半，B2 + A6 还需 ~22-26h）

**plan §5.1 / §5.5 同步更新**：collect-transitions for-loop 加 m3_run_v7_M3-A6；GPU 估算从 × 2 M3 改为 × 3 M3。

### Stage 2 Mid-chain audit 纠错（2026-05-03 ~12:30）

GPT 审查发现 5 项问题，全部独立验证成立 + 修复：

| # | 问题 | 验证 | 修复 |
|:--|:-----|:----:|:-----|
| P1a | 依赖环境说明.md line 1043 仍写 Pre-Stage 3 Gate -26 (v6 reference) | ✅ | 改 -8.09 (v7 实测) |
| P1b | plan §6.4 line 596（gate 不过 → 跳 Stage 3.5） vs §11 line 854（gate 不过 → Stage 3.5 仍执行）self-contradiction | ✅ | 修 §11 与 §6.4 一致：gate 不过跳 Stage 3 + 3.5，full_policy 全 shadow，paper 仅 backbone |
| P2a | run_one_bc.sh:96 不跑 signal eval；plan §5.2 line 502 + §5.3 设计 BC-7 (j3) 应同时跑 agent + signal route | ✅ | 用户决策 1：补跑但不打断（低优先级，留 BC × B2 完成后或最后 ad-hoc）|
| P2b | scripts/stage2_chain.sh:364 Phase 4 没过滤 BC-3 `_excluded_from_ranking`（与 stage2_chain_a6.sh:180 不一致）| ✅ | 加 jq-free Python filter（与 A6 chain 同步）|
| P2c | 报告按 PnL 排，不是 canonical full_policy score 排（Top-2 reorder: BC-1/BC-6/BC-4/BC-5/BC-7 vs 报告写 BC-1/BC-5/BC-4/BC-6）| ✅ | 修正：以后报告按 ledger canonical rank 输出（top-1 不变 = BC-1，但 BC-6 实际 #2 by score）|
| P3 | scripts_stage1c_test.sh:47 用 `jq` (远端 jq missing → summary 失败但 aggregate 文件齐全) | ✅ | Stage 1C 历史问题，aggregate 文件已 archived; scripts/stage2_chain*.sh 都 jq-free（Python helper），未来不会再触发 |

**用户 3 决策（2026-05-03 ~12:45）**：
1. **BC-7 signal eval**: 补跑但低优先级，不打断当前 chain（~33 min，留诊断/文档完整性，不参与 paper 主候选重排）
2. **BC-3 oracle C**: 现选 (c) 留作"本轮未测"；不修后重跑；Stage 3.5 之后用 (b) `--oracle-c-threshold X` 显式 override 做小规模补测
3. **Stage 4 paper trading**: 等 Stage 3.5 Gate 之后再启动；之前 backbone 仅 shadow 不入金/不发单

### Sharpe 字段口径澄清（user 13:00 纠正）

ledger / aggregate.json 字段 `mean_sharpe` **不是 portfolio sharpe**，是 **per-window sharpe 取平均**。一个常见误读，下文统一口径：

| 字段 | 计算方式 | 含义 |
|:-----|:---------|:-----|
| `mean_sharpe`（ledger reported）| `mean([sharpe_ratio_per_window for window in 24 windows])` | 每个 5-min episode 内部 NAV trajectory 的 sharpe 取平均；不反映跨 windows portfolio risk-adjusted return |
| cross-window portfolio sharpe (un-annualized) | `mean(per_window_pnl) / std(per_window_pnl)` | 把 24 windows 当时间序列算；反映 "如果一直投这个 strategy 的 risk-adjusted return" |
| annualized cross-window sharpe | un-annualized × √(N annual periods / N windows in val) | 标准 finance 年化 sharpe；24 windows ≈ 1 day → ×√252 |

**实例（BC-1 val_agent，total_pnl=+106.02 / 24 windows）**：
- mean_pnl_per_window = +4.42 / std(per_window) = 16.62
- per-window mean_sharpe = **0.878**（ledger）
- cross-window portfolio sharpe (un-annualized) = +4.42/16.62 = **0.266**
- annualized (假设 24 windows = 1 day) = 0.266 × √252 = **+4.22** ⭐

K2-C 协议把每个 window 当**独立 episode**（每个 5-min 都从 100 starting cash 开始），24 windows PnL 是 sum 不是 compound。`mean_sharpe` per-window 设计 choice 是评估"单个 5-min 执行质量"。

**对 paper trading 决策的 implication**：
- per-window mean_sharpe 0.6-0.9 不是 "weak strategy"，是 "短期 5-min 内的风险调整收益"
- 真正的 portfolio sharpe（年化）≈ 4-5（高质量 strategy 区间）
- 但需注意 fat tail：BC-1 worst window -30%（lose 1/3 capital in 5 min）；33% 概率 lose
- **strategy 本质 = "67% prob 赚 +4 ~ +37, 33% prob 亏 -4 ~ -30"**——这才是 paper trading 实操时的真实 PnL 分布

未来报告 default 用 cross-window portfolio sharpe + per-window mean_sharpe **两个数字都列**，避免单一指标误读。

### Stage 2 BC batch sweep audit + CP cross-product 追加（user 14:00 决策 D）

GPT 第 2 轮审查指出我之前对 user "Stage 2 没扫 batch>2048" 怀疑的回答有 4 处问题，全部独立 verify 成立：

| # | 我原回答的错误 | 修正 |
|:--|:--------------|:-----|
| 1 | "BC × B1 batch trend monotonic decrease（越大越差）" | **只看 vanilla 子维度（BC-0/1/2）忽略 modifier path**；batch=2048 + modifier (BC-4/5/6) 都做到了 +97-100，几乎追平 BC-1 batch=512 +106 |
| 2 | "Stage 1A double sweet spot (A6 batch=4096 PnL+280, A2 batch=256 val_top10+0.228)" | **跨 metric framing 错乱**：PnL 真双峰是 A3 batch=512 (+279) + A6 batch=4096 (+280)；val_top10 真峰是 A10 batch=6144 (+0.263) 不是 A2 |
| 3 | "假设 batch=256 BC PnL +130（基于 Stage 1A 趋势外推）" | **Stage 1A 反向证据**：A2 batch=256 PnL=+222 < A6 batch=4096 +280；外推仅靠 Stage 2 自己斜率（弱证据）|
| 4 | "真正 missed 的是 batch<512 (256/128)" | **真正 missed 的是 batch=512 × modifier cross-product**（plan §5.2 全部 modifier configs 都在 batch=2048）|

**user 决策 D（14:00）**：等 B1+B2+A6 chain 全完后，追加 3 个 BC × B1 cross-product config，验证 "batch effect + modifier effect 是否 additive" 假设：

- **BC-CP1** = BC-1 (batch=512) + BC-4 (class_balance) — 单 modifier 与小 batch
- **BC-CP2** = BC-1 + BC-5 (class+focal+EMA method stack) — 全方位 stack
- **BC-CP3** = BC-1 + BC-6 (seed=7) — 第二种子小 batch

**Cost**: ~3 × 1.5h (batch=512 train ~1h + eval 33min) = **~4.5h GPU on B1 backbone only**

**Hypothesis test**:
- batch effect (B1 vanilla): BC-0 +52 → BC-1 +106 = +54 gain
- modifier effect (B1 batch=2048): BC-0 +52 → BC-4/5/6 +97-100 = +45-48 gain
- 若 additive: CP ≈ +130-150（vs 当前 max +106）
- 若 sub-additive (饱和): CP ≈ +110-120
- 若反向 interaction: CP ≈ +90-100（与 BC-4/5/6 持平）

**实施**：
- `scripts/stage2_chain_cp.sh`：3 CP runs + final Phase 4 dump（含 CP entries）
- `scripts/stage2_cp_watchdog.sh`：监听 stage2_a6_watchdog (PID 164682) 退出 + 验证 A6 ALL DONE marker → 自动启动 CP chain
- 不影响 paper 主候选锁定（B1 backbone 已 main）
- ETA 推后 ~4-5h: ~05:00 next day → ~10:00 next day server

**反思（process）**：之前对 user 怀疑的回答暴露 4 类系统性错误（看片段、混 metric、外推反向 reference、看错 missing dim），下次类似分析必查 ledger 全表 + single-metric-internal sweet spot + verify reference 数据方向 + 优先看 cross-product matrix 空白格。

### Stage 2 ALL DONE finale（2026-05-04 06:57:35 — 全 27 BC runs 完成）

**实测时间线**（B1+B2 chain → A6 chain → CP chain，含 watchdog auto-trigger）：

| 节点 | 时刻 | 实际耗时 |
|:----|:-----|:--------|
| chain (B1+B2) start | 2026-05-03 02:33:44 | - |
| Stage 2 Phase 1 collect B1 + validate G1/G3 | ~04:24 | ~1.85h |
| Stage 2 Phase 2 BC × B1 (8 configs) | 04:24 → 11:39 | ~7.25h |
| Stage 2 Phase 1 collect B2 + validate | 11:39 → 13:16 | ~1.6h |
| Stage 2 Phase 2 BC × B2 (8 configs) | 13:16 → 20:04 | ~6.8h |
| chain (B1+B2) ALL DONE | 2026-05-03 20:04:46 | **17.5h** |
| A6 watchdog auto-trigger | 20:05:33 | 47s 内 |
| A6 collect (5 dv) + validate | 20:05 → 21:40 | ~1.6h |
| A6 BC × A6 (8 configs) | 21:40 → 04:26 | ~6.75h |
| A6 chain ALL DONE | 2026-05-04 04:26:18 | **+8.4h** |
| CP watchdog auto-trigger | 04:27:02 | 44s 内 |
| CP chain (3 configs) | 04:27 → 06:57 | ~2.5h |
| Final Phase 4 dump | 06:57:35 | - |
| **Stage 2 ALL DONE total** | | **~28.4h GPU wall** |

vs plan §5.5 估 ~38-50h（含 A6 追加），实际 ~28.4h（30% 快于估算上限）。

### Final canonical full_policy ranking（per-M3 subgroup）

source: `candidate_ledger.py rank --leaderboard full_policy --top 12 --group-by-config-key m3_id` + `_excluded_from_ranking=true` filter (Phase 4 dump 内嵌)

| Rank | Run | subgroup | score | val PnL | sharpe | rolling worst |
|:-:|:----|:---------|------:|--------:|-------:|--------------:|
| 🥇 | **BC-6 × B2** | M3-B2 | **0.9081** | +120.78 | 0.974 | -29.61 |
| 2 | **BC-CP1 × B1** | M3-B1 | 0.8416 | **+123.39** ⭐ | 0.929 | **-6.09** ⭐ |
| 3 | BC-1 × B2 | M3-B2 | 0.8291 | +122.17 | 0.980 | -38.53 |
| 4 | BC-7 × B2 | M3-B2 | 0.7921 | +108.48 | 0.871 | -11.23 |
| 5 | BC-1 × B1 | M3-B1 | 0.7108 | +106.02 | 0.878 | -10.37 |
| 6 | BC-6 × A6 | M3-A6 | 0.6865 | +66.87 | 0.661 | **-4.92** ⭐ |
| 7 | BC-6 × B1 | M3-B1 | 0.6473 | +97.80 | 0.836 | -13.39 |
| 8 | BC-0 × A6 | M3-A6 | 0.6130 | +59.68 | 0.671 | -8.73 |
| 9 | BC-7 × A6 | M3-A6 | 0.5750 | +78.18 | 0.730 | -32.65 |
| 10 | BC-4 × B1 | M3-B1 | 0.5700 | +98.02 | 0.812 | -15.86 |
| 11 | BC-CP2 × B1 | M3-B1 | 0.5293 | +94.18 | 0.782 | **-2.39** ⭐⭐ |
| 12 | BC-2 × A6 | M3-A6 | 0.5006 | +47.46 | 0.668 | -20.24 |
| 13 | BC-5 × B1 | M3-B1 | 0.4860 | +99.87 | 0.829 | -15.09 |

### 跨 backbone 模式分析

**B1 (EMA 0.999) backbone 模式**：
- vanilla baseline +52，small batch +106，modifier +97-100
- modifier path 全部 +97-100 plateau（class_balance / focal+EMA / seed=7 几乎同等）
- → batch 与 modifier 各自独立 gain ~+50

**B2 (EMA 0.99) backbone 模式**：
- vanilla baseline +83（比 B1 高 +59%），small batch +122（比 B1 高 +15%）
- **modifier 反作用**：BC-4 +90 (-8% vs B1), BC-5 +66 (-34% vs B1)
- → B2 transition 已"激进 modified"，加 modifier 双 modify → diminishing/negative

**A6 (no EMA baseline) backbone 模式**：
- vanilla baseline +60（mid，比 B1/B2 都高），small batch +46（**反转**，比 vanilla 低）
- modifier 全 hurt（class_balance +35, stack +47）
- **fat tail 全 ledger 最稳**：BC-6 × A6 worst -4.92 ⭐
- → A6 raw transition 噪声 → small batch + modifier 都 amplify noise → 仅 vanilla 稳定

### CP cross-product 假设完整结果

target hypothesis: BC-1 (small batch on B1) + modifier ≈ +130-150 (additive)

| Config | actual PnL | additive 比例 | 解读 |
|:-------|----------:|:-------------:|:-----|
| BC-CP1 (B1+512+CB) | **+123.39** ⭐ | 81% (123/152) | sub-additive but **真的 outperform single-axis** path |
| BC-CP2 (B1+512+CB+focal+EMA stack) | +94.18 | 62% (94/152) | **method stack saturates**，fat tail 反而最稳 -2.39 |
| BC-CP3 (B1+512+seed=7) | +75.07 | 49% (75/152) | seed=7 + small batch **negative interaction**（seed=7 单独 +98，与 small batch 组合反而退化）|

**核心 takeaway**：single modifier on small batch (BC-CP1) = sweet spot；加更多 modifier 或换 seed 都退化。

### Pre-Stage 3 Gate 决议（PASSED）

```
Hold gate threshold: -8.09
top-1 BC × val (canonical, per-M3 subgroup, excluded skipped): BC-6 × B2 +120.78
+120.78 >> -8.09 → ✅ PASS
→ Stage 3 IQL allowed to start (per plan §5.4)
```

### paper trading 备选 2 候选评估

按 Stage 3.5 will run test confirmation on full_policy top-1 by score = **BC-6 × B2**（+120.78 / -29.61），但**有 fat tail 风险**。

替代候选评估：

| 候选 | val PnL | val rolling worst | implied paper risk profile |
|:----|--------:|------------------:|:--------------------------|
| **BC-6 × B2** (canonical top-1) | +120.78 | -29.61 | High return, high drawdown risk |
| **BC-CP1 × B1** | +123.39 | **-6.09** ⭐ | **Best balance**: high PnL + low drawdown |
| BC-1 × B2 | +122.17 | -38.53 | Highest sharpe (0.98) but worst fat tail |
| BC-CP2 × B1 | +94.18 | **-2.39** ⭐⭐ | Best fat tail of all, mid PnL |
| BC-6 × A6 | +66.87 | -4.92 | Lowest PnL but very stable |

**Stage 3.5 仅跑 top-1 by score** (per plan §6.4) → BC-6 × B2 进 test confirmation。但 dev 应记录：**BC-CP1 在 PnL+fat tail 双维度上比 BC-6 × B2 都好**（+2.6 PnL & -23.5 better fat tail），属于 plan §4.4 类比的"人工 override 候选"——若 BC-6 × B2 test fail，BC-CP1 应是首选 fallback。

### Process improvements during Stage 2（已 commit）

| issue | fix | commit |
|:------|:----|:-------|
| chain script `--loss huber` typo | 改 `--ev-loss-fn huber` | (in 5e4e3cb) |
| `--threads 16` collect-transitions SIGABRT crash | threads=4 + parquet existence resume + SIGABRT 容忍 | 77c07b8 |
| watchdog 漏接 C calibration (Stage 1B 教训重现风险) | 设计完整 watchdog dependency graph: chain → A6 watchdog → A6 chain → CP watchdog → CP chain | (in 12de940 + 5e4e3cb) |
| candidate_ledger.py per-M3 子分组 normalization 缺失 | +`--group-by-config-key` flag | 4357f99 |
| BC-3 oracle C noop bug 跨 3 backbone universal | attach `_excluded_from_ranking=true` markers | (manual ledger updates) |
| 报告 sharpe 字段口径误读 | dev changelog 加三种 sharpe 计算方式说明 | cad22c0 |
| BC-1 × B2 等 cross-product gap 用户怀疑 | CP chain 追加 (BC-CP1/2/3) | 5e4e3cb |

### 当前 known issues + 流程教训

1. **🟡 BC-7 signal route eval 未跑**（plan §5.2 line 502 + §5.3 设计 j3 BC 应同时跑 agent + signal；实际 chain script 仅 agent route）
   - 影响：**plan §5.2 j3 backbone 榜数据缺失**；agent route 已 cover paper 主路径
   - 修法：留 ad-hoc 后跑 OR Stage 4 candidate ranking 时手动补
2. **🟡 BC-3 oracle C filter no-op 跨 3 backbone universal**
   - root cause: `compute_oracle_c_threshold()` quantile 0.7 在 v7 BTC binary outcome 数据上产 no-op threshold
   - 影响：BC oracle 维度本轮**未测**
   - 修法：Stage 3.5 后用 `--oracle-c-threshold X` 显式 override mini-sweep
3. **✅ candidate_ledger.py rank CLI default filter `_excluded_from_ranking`**（已修复）
   - 修复 commit 9f32272: `_entries_for_leaderboard()` 加 `include_excluded` 参数（default False）；CLI `rank` 新增 `--include-excluded` flag。**默认行为变化**: rank 输出不再含 BC-3 dup（与 chain script Phase 4 dump 一致）；通过 `--include-excluded` 仍可看（audit trail）
   - 已 smoke verify (commit 9f32272 message 内引用)：default 隐藏 3 个 BC-3 dup；`--include-excluded` 显示
4. **流程教训累积**：
   - 实证发现 → plan + dev 双同步（不能只 dev）
   - audit 建议必须 verify 实证 reference（reverse evidence 检查）
   - cross-product matrix 空白格优先 > 边界外推
   - chain script 设计前必须画完整 dependency graph
   - 数值必须从 canonical source dump（ledger / aggregate.json），禁止凭印象

### 下一步（Stage 3 IQL launch decision）

按 plan §6.1: 3 IQL configs on **top-1 backbone = m3_run_v7_M3-B1**（不是 BC top-1 的 backbone）：
- IQL-0: anchor (gamma 0.9995, tau 0.7, beta 3.0)
- IQL-1: short horizon + AWR 锐化 + warm-start from BC
- IQL-2: tau 0.5 (less pessimistic)

GPU 估 ~3-5h。Stage 3.5 test confirmation 用 full_policy top-1 by score (BC-6 × B2) → +1-2h GPU。

---

## Stage 2 — M5 BC 诊断（已完成 2026-05-04 06:57:35）

（执行时追加）

---

## Stage 3 + 3.5 — M5 IQL 诊断 + Full-policy test confirmation（已完成 2026-05-07 01:16:08）

### Stage 3 execution checkpoint — IQL completed + rerank（2026-05-07）

**执行状态**：
- tmux runner: `m3m5_stage3`
- remote runner log: `logs/stage3_resume2_runner.log`
- ledger backup: `poly-arb-ai/training/candidates_ledger.before_stage3.json`
- pre-Stage-3 rank snapshot: `logs/stage3_before_full_policy_top12.txt`
- IQL-0: ✅ train + fixed val + native val + rolling + ledger attach completed
- IQL-1: ✅ train + fixed val + native val + rolling + ledger attach completed
- IQL-2: ✅ train + fixed val + native val + rolling + ledger attach completed
- Stage 3 after-rank: ✅ `logs/stage3_after_full_policy_top5.txt`
- Stage 3.5: ✅ top-1 test confirmation completed on `m5_bc_v7_m3_run_v7_M3-B2_BC-6`
- local artifact sync: ✅ remote `candidates_ledger.json` / `logs/stage3*` / `training/eval/v7*` / 3× IQL checkpoints / 3× IQL ONNX copied back to `source://training` (2026-05-07)

**执行修复**：
- `scripts/run_one_iql.sh` 原 collapse detector 只匹配 `hold_argmax_share=...`，但 `train_iql.py` 实际日志字段为 `hold=...`。
- 在 `set -euo pipefail` 下，`grep` 无匹配会导致脚本在 rolling 后、ledger attach 前退出。
- 已修为兼容 `hold` / `hold_argmax_share`，并对空匹配加 `|| true`；IQL-0 已用已完成 eval 产物补 attach metrics，没有重跑训练。

**IQL completed metrics（full_policy main = agent + fixed exec val）**：

| run_id | fixed val PnL | fixed Sharpe | winrate | rolling median | rolling worst | native val PnL | last probe_gap | last hold | collapsed |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|
| `m5_iql_v7_m3_run_v7_M3-B1_IQL-0` | +117.8847 | 1.2664 | 66.67% | +17.4948 | +6.2875 | +0.5295 | -0.8775 | 0.9385 | true |
| `m5_iql_v7_m3_run_v7_M3-B1_IQL-1` | +71.8358 | 0.8993 | 58.33% | +13.8549 | -21.0937 | -52.0237 | -0.7895 | 0.8920 | false |
| `m5_iql_v7_m3_run_v7_M3-B1_IQL-2` | +127.0769 | 1.1033 | 54.17% | +23.9702 | -13.7224 | -51.6534 | -0.9070 | 0.9530 | true |

**IQL-1 key finding**：
- BC-CP1 warm-start + `gamma=0.99 / tau=0.7 / beta=1.0` 能把末轮 hold share 从早期 0.99+ 拉到 0.8920，按 hard rule 未标 collapsed。
- 但 fixed val PnL 只有 +71.8358，低于 Stage 2 强 BC 候选，也低于 IQL-0 的 fixed val +117.8847。
- native route 为 -52.0237，显著差于 fixed route；说明 IQL-1 训练出的执行头没有带来增益，paper 候选不应因 IQL 训过执行头而切 native。
- 结论：IQL-1 是“非 collapsed 的诊断成功”，不是“性能成功”。warm-start 缓解 Hold 塌缩，但当前 IQL 配置仍不足以挑战 BC 主候选。

**IQL-2 key finding**：
- `tau=0.5` 单独放松（无 warm-start）没有缓解 Hold 塌缩：末轮 `probe_gap=-0.9070 / hold=0.9530`，按 hard rule 标 `iql_collapsed=true`。
- fixed val PnL 达 +127.0769，rolling worst -13.72，单看 fixed-route 经济指标优于 IQL-1，也略高于 BC-6 × B2 的 +120.7812。
- 但 native route 仍为 -51.6534，和 IQL-1 native (-52.0237) 一样显著差于 fixed route，继续证明 IQL execution heads 不可靠。
- 结论：IQL-2 是“fixed-route val 指标好但训练形态 collapsed”的候选，不能作为 paper top candidate；只保留诊断价值。

**Stage 3 canonical rerank（after IQL-0/1/2）**：

source: `logs/stage3_after_full_policy_top5.txt`

| rank | run_id | subgroup | score | fixed val PnL | rolling worst |
|--:|:--|:--|--:|--:|--:|
| 1 | `m5_bc_v7_m3_run_v7_M3-B2_BC-6` | M3-B2 | 0.9081 | +120.7812 | -29.6094 |
| 2 | `m5_iql_v7_m3_run_v7_M3-B1_IQL-0` | M3-B1 | 0.8391 | +117.8847 | +6.2875 |
| 3 | `m5_bc_v7_m3_run_v7_M3-B2_BC-1` | M3-B2 | 0.8291 | +122.1655 | -38.5274 |
| 4 | `m5_bc_v7_m3_run_v7_M3-B2_BC-7` | M3-B2 | 0.7921 | +108.4809 | -11.2261 |
| 5 | `m5_bc_v7_m3_run_v7_M3-B1_BC-CP1` | M3-B1 | 0.6877 | +123.3941 | -6.0887 |

**Stage 3 decision**：
- canonical top-1 remains `BC-6 × B2`, not IQL.
- collapsed-top1 guard did not block Stage 3.5 because top-1 stage is `BC` (`logs/stage3_top1_decision.txt`).
- Stage 3.5 one-time test confirmation ran on `m5_bc_v7_m3_run_v7_M3-B2_BC-6`; test result must not be used to rerank candidates.

### Stage 3.5 result — Full-policy top-1 test confirmation（FAILED）

source:
- aggregate: `poly-arb-ai/training/eval/v7_final/m5_bc_v7_m3_run_v7_M3-B2_BC-6__test/aggregate.json`
- rolling: `poly-arb-ai/training/eval/v7_final/m5_bc_v7_m3_run_v7_M3-B2_BC-6__test_segments.json`
- gate: `logs/stage3_5_test_gate_decision.txt`

| run_id | test total PnL | mean Sharpe | win/loss windows | rolling median | rolling worst | gate |
|:--|--:|--:|:--|--:|--:|:--|
| `m5_bc_v7_m3_run_v7_M3-B2_BC-6` | -11.0374 | 0.3115 | 13 / 12 | -0.3249 | -31.7451 | FAIL |

**Gate interpretation**：
- Full-policy Pre-Paper Gate requires `test_total_pnl > 0 && test_rolling_worst_pnl > -100`.
- `rolling_worst=-31.7451` passes the tail-risk bound, but `test_total_pnl=-11.0374` fails positivity.
- Result: full_policy top-1 **does not enter paper trading**; full_policy candidates remain shadow/diagnostic only.
- No fallback test was run for BC-CP1 or other candidates because Stage 3.5 is top-1-only by plan §6.4; using test to choose a fallback would leak test into selection.

---

## Stage 4 — 候选选拔与发布（已完成 2026-05-07）

### Stage 4 scope

本段只收口 M3M5 offline 训练与评估结论：双榜出榜、gate 判定、产物索引、训练发现、known limitations。**不进入 M6，不部署，不发单，不补跑实验**；M6 由其他工作树处理。

### Local artifact status

远端 GPU Stage 3 / 3.5 产物已同步到本地 `source://training`。本地校验：

| artifact | local path | status |
|:--|:--|:--|
| ledger | `poly-arb-ai/training/candidates_ledger.json` | ✅ synced |
| Stage 3 logs | `logs/stage3*` | ✅ 8 files |
| eval outputs | `poly-arb-ai/training/eval/v7/`, `poly-arb-ai/training/eval/v7_final/` | ✅ synced |
| IQL checkpoints | `poly-arb-ai/training/checkpoints/m5_iql_v7_m3_run_v7_M3-B1_IQL-{0,1,2}/` | ✅ 3 dirs |
| IQL ONNX | `poly-arb-ai/training/onnx/m5_iql_v7_m3_run_v7_M3-B1_IQL-*_trained.onnx` | ✅ 3 files |

### Final Backbone leaderboard（raw top 10）

source: `candidate_ledger.py rank --leaderboard backbone --top 10`

| # | run_id | score | val PnL | rolling median | rolling worst | val_top10_ev_up | val_top10_5ep_std |
|---:|:--|--:|--:|--:|--:|--:|--:|
| 1 | `m3_run_v7_M3-B1` | 0.8085 | +424.3953 | +103.5391 | +16.3697 | 0.1665 | 0.0247 |
| 2 | `m3_run_v7_M3-B8` | 0.8085 | +424.3953 | +103.5391 | +16.3697 | 0.1665 | 0.0247 |
| 3 | `m3_run_v7_M3-B2` | 0.7731 | +415.7186 | +74.1651 | +19.1092 | 0.1734 | 0.0223 |
| 4 | `m3_run_v7_M3-B5` | 0.6064 | +212.1497 | +44.8495 | +13.9644 | 0.1343 | 0.0070 |
| 5 | `m3_run_v7_M3-A6` | 0.5961 | +280.1133 | +41.1218 | -7.9442 | 0.1627 | 0.0236 |
| 6 | `m3_run_v7_M3-B7` | 0.5670 | +268.1047 | +55.7711 | +9.3998 | 0.0704 | 0.0079 |
| 7 | `m3_run_v7_M3-A10` | 0.5633 | +39.0453 | +9.9012 | -19.8132 | 0.2632 | 0.0129 |
| 8 | `m3_run_v7_M3-B3` | 0.5424 | +181.4489 | +17.2705 | +4.2407 | 0.1901 | 0.0244 |
| 9 | `m3_run_v7_M3-A3` | 0.5364 | +279.3529 | +73.8079 | -74.8888 | 0.1291 | 0.0268 |
| 10 | `m3_run_v7_M3-B11` | 0.5327 | +154.4638 | +32.3944 | -46.7636 | 0.2085 | 0.0239 |

`m3_run_v7_M3-B8` 与 B1 指标完全相同，是 snapshot save side-output no-op，不占 unique candidate slot。Stage 4 unique 候选位按 B1 → B2 选取；A6 作为 no-EMA baseline/reference 记录。

### Backbone offline confirmation

source: `poly-arb-ai/training/eval/v7_final/*__test/{aggregate.json,*_segments.json}`

| status | run_id | val PnL | test PnL | test Sharpe | win/loss windows | test rolling median | test rolling worst | decision |
|:--|:--|--:|--:|--:|:--|--:|--:|:--|
| 主候选 | `m3_run_v7_M3-B1` | +424.3953 | +92.2782 | 1.0626 | 13 / 12 | +20.7197 | -40.4436 | PASS |
| 备选 1 | `m3_run_v7_M3-B2` | +415.7186 | +137.8349 | 1.4101 | 14 / 11 | +21.7386 | +5.3328 | PASS |
| reference | `m3_run_v7_M3-A6` | +280.1133 | +85.5283 | 1.0690 | 12 / 13 | +24.8739 | -30.7744 | PASS |

说明：
- Test 只做 confirmation，不参与重新排序。B2 test PnL 高于 B1，但不会因此替换 B1 主候选位。
- A6 通过 test gate，但它是 no-EMA baseline/reference，不占 B1/B2 unique candidate slot。

### Final Full-policy leaderboard（canonical grouped top 10）

source: `candidate_ledger.py rank --leaderboard full_policy --group-by-config-key m3_id --top 10`

| # | run_id | subgroup | score | fixed val PnL | Sharpe | winrate | rolling median | rolling worst |
|---:|:--|:--|--:|--:|--:|--:|--:|--:|
| 1 | `m5_bc_v7_m3_run_v7_M3-B2_BC-6` | M3-B2 | 0.9081 | +120.7812 | 0.9740 | 0.6667 | +36.5242 | -29.6094 |
| 2 | `m5_iql_v7_m3_run_v7_M3-B1_IQL-0` | M3-B1 | 0.8391 | +117.8847 | 1.2664 | 0.6667 | +17.4948 | +6.2875 |
| 3 | `m5_bc_v7_m3_run_v7_M3-B2_BC-1` | M3-B2 | 0.8291 | +122.1655 | 0.9800 | 0.6250 | +36.2177 | -38.5274 |
| 4 | `m5_bc_v7_m3_run_v7_M3-B2_BC-7` | M3-B2 | 0.7921 | +108.4809 | 0.8707 | 0.6667 | +29.0326 | -11.2261 |
| 5 | `m5_bc_v7_m3_run_v7_M3-B1_BC-CP1` | M3-B1 | 0.6877 | +123.3941 | 0.9293 | 0.6667 | +15.5683 | -6.0887 |
| 6 | `m5_bc_v7_m3_run_v7_M3-A6_BC-6` | M3-A6 | 0.6865 | +66.8669 | 0.6613 | 0.5833 | +15.4794 | -4.9189 |
| 7 | `m5_iql_v7_m3_run_v7_M3-B1_IQL-2` | M3-B1 | 0.6376 | +127.0769 | 1.1033 | 0.5417 | +23.9702 | -13.7224 |
| 8 | `m5_bc_v7_m3_run_v7_M3-A6_BC-0` | M3-A6 | 0.6130 | +59.6760 | 0.6710 | 0.6250 | +5.9484 | -8.7348 |
| 9 | `m5_bc_v7_m3_run_v7_M3-B1_BC-1` | M3-B1 | 0.5853 | +106.0163 | 0.8783 | 0.6667 | +15.7698 | -10.3671 |
| 10 | `m5_bc_v7_m3_run_v7_M3-A6_BC-7` | M3-A6 | 0.5750 | +78.1810 | 0.7296 | 0.6250 | -5.8336 | -32.6454 |

Stage 4 full-policy 必须使用 grouped canonical rank。Flat rank 会把 `IQL-0` 排到 top-1，但 Stage 3.5 的 canonical rerank 与 test target 均使用 `--group-by-config-key m3_id`，因此 flat rank 不作为收口依据。

### Full-policy Stage 3.5 confirmation

| run_id | test PnL | test Sharpe | win/loss windows | rolling median | rolling worst | gate |
|:--|--:|--:|:--|--:|--:|:--|
| `m5_bc_v7_m3_run_v7_M3-B2_BC-6` | -11.0374 | 0.3115 | 13 / 12 | -0.3249 | -31.7451 | FAIL |

Full-policy Gate 要求 `test_total_pnl > 0 && test_rolling_worst_pnl > -100`。BC-6 × B2 rolling worst 通过，但 total PnL 为负，因此 full_policy 全部候选仅 shadow/diagnostic only；不补 fallback test，不用 test 重排。

### Training findings and lessons

1. EMA 是本轮最稳定有效的 backbone 改动。B1/B2 相对 no-EMA A6 在 val PnL 与 rolling 稳定性上显著提升，且 test confirmation 均通过。
2. B8 证明 snapshot save flag 本身是 no-op。B8 与 B1 指标完全相同，不能解释为 snapshot ensemble 收益；ensemble 只能通过独立 offline logits averaging 诊断，不进入本轮候选。
3. Focal / Label smoothing 在本轮口径下没有形成候选级收益。Focal 在 EMA 基础上退化，LS 未改写 B1/B2 的主结论。
4. BC agent route 没能挑战 backbone signal route。full_policy val top-1 在 test 上 total PnL 为负，说明 Stage 2/3 的 agent-route 改进不足以进入候选。
5. IQL warm-start 能缓解 Hold collapse，但不是性能成功。IQL-1 non-collapsed 只证明 warm-start 有诊断价值；fixed val 和 native route 都不支持候选化。
6. IQL native execution heads 不可靠。IQL-1 / IQL-2 native val 均约 -52，显著差于 fixed route。
7. IQL-2 fixed-route val 指标好但 collapsed，不能作为候选。塌缩形态优先于单一 fixed-route PnL。
8. BC-3 oracle C quantile route 在 v7expanded 上 no-op，oracle 维度本轮未被有效测试。

### Known limitations closed with Stage 4

| issue | verification | Stage 4 decision |
|:--|:--|:--|
| BC-7 signal route eval 未跑 | ledger 仅有 `eval_val_agent` / `k2c_agent_fixed_*`，无 `k2c_signal_fixed_*` | 作为 coverage limitation 记录；不阻塞收口 |
| BC-3 explicit `--oracle-c-threshold` mini-sweep 未跑 | ledger 中 BC-3 为 duplicate + `_excluded_from_ranking=true`，无 override run | 作为 oracle 维度未测记录；不补跑 |
| Full-policy top-1 test FAIL | `logs/stage3_5_test_gate_decision.txt` | full_policy 全部 shadow/diagnostic only |

### Stage 4 final decision

M3M5 offline 收口完成。最终可交接给下游的事实是：
- Backbone unique top candidates: `m3_run_v7_M3-B1`、`m3_run_v7_M3-B2`。
- Reference baseline: `m3_run_v7_M3-A6`。
- Full-policy: no offline-confirmed candidate; all BC/IQL full-policy runs remain shadow/diagnostic.
