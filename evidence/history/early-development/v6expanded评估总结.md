# v6expanded 执行总结（2026-04-27 ~ 2026-04-28）

## TL;DR

| 维度 | 结果 |
|------|------|
| 数据规模 | 5 套 v1~v5 共 **6248 markets / 163 windows / ~7.5M frames** |
| M0~M2 流程 | ✅ 全部通过；feature coverage ≥ 0.95；G1/G3 hard gate 全 PASS |
| M3 监督预训练 | ✅ E10 早停；val_auc=**0.7517**（≈ K2-A1 历史 0.7542）；但 **test_top_decile_mean_ev_up=-0.027 (Phase 1 严格 acceptance FAIL)** |
| M5 BC 训练 | ✅ E07 早停；val_acc=0.6826 |
| M5 IQL 训练 | ⚠️ 塌缩到 hold（probe_gap=-0.97 / hold≥98% 持续 3 epoch），按 runbook 提前停 |
| **K2-C 复现（test PnL）** | ❌ **m5_v6_bc_signal/test = -251.49** vs 历史 **+66.10**（**反向且差距大**）|
| **结论** | M3/M5 backbone 在 train/val 表现良好，但 **test 期（2026-04-20~04-24）严重分布漂移**，K2-C 路线在大数据下未复现历史 +66 |

## 1. 数据规模与 split

```
data-v1: 2 windows,    492 exported markets
data-v2: 20 windows,   746 exported markets
data-v3: 35 windows,  1188 exported markets
data-v4: 58 windows,  2228 exported markets
data-v5: 49 windows*, 1594 exported markets   (*1 window 隔离 - 见执行偏离 §6.4)
─────────────────────────────────────────────
合计    164 windows, 6248 exported markets
M0 manifest_for_split → 163 valid windows (data-v5_quarantine 那 1 window 已剔除)
```

**Frozen split (sha256=cf2bfe7fa646)**：
- train: **114 windows** (data-v1~v4)，2026-03-23 06:40 → 2026-04-15 04:00（约 23 天）
- val: **24 windows** (data-v4 后期 + v5 前期)，2026-04-15 08:00 → 2026-04-20 00:00（约 5 天）
- test: **25 windows** (仅 data-v5 后期)，2026-04-20 04:00 → 2026-04-24 04:00（约 4 天）

**注**：split sanity check 通过（同 (dv, window_id) 单 split；同 ts 跨 split = hard fail），无 LEAK / TS_LEAK。

## 2. M3 监督预训练结果（m3_run_v6expanded）

- 训练数据：5 套 features_250ms_data-v*.parquet 共 **7,288,487 frames**（train=5.41M, val=1.05M, test=0.83M）
- 配置：epochs=30 (E10 早停 patience=5), batch=128, lr=1e-4, AMP+CUDA, num_workers=8 (+ulimit -n 65535)
- best epoch = E05（val_top10_ev=+0.1226 后 5 epoch 无改善）

| Epoch | train_loss | val_loss | val_auc | val_top10_ev |
|-------|-----------:|---------:|--------:|-------------:|
| E01 | 1.7282 | 4.0191 | 0.752 | +0.0963 |
| E05（best）| 0.1355 | 6.2140 | **0.770** | **+0.1226** |
| E10（停）| 0.0466 | 6.27?? | 0.78x | +0.06xx |

**test_metrics.json**：
- auc: **0.7517**（>=0.70 阈值 ✓；与 K2-A1 历史 0.7542 接近）
- brier: 0.3458
- **top_decile_mean_ev_up: -0.0272 ❌**（FAIL Phase 1 严格 acceptance）
- ev_up_sign_acc: 0.6003（> 0.52 阈值 ✓）

**预警**：top_decile_mean_ev_up 在 test 期为负（"看涨置信≥50% 的样本，实际 BTC 涨幅<0"）—— 已是分布漂移信号。当时未阻断流程继续推进。

## 3. M5 训练结果

### 3.1 Oracle-BC（hard required，K2-C 主候选 backbone）

- `m5_run_v6_bc/`：E07 early stop（patience=3）
- E07 train_acc=**0.9371**, val_acc=**0.6826**, val_loss=1.3605
- BC ONNX 已显式导出（2.16MB, max abs diff = 9.54e-05）

### 3.2 IQL（optional / diagnostic）

- `m5_run_v6_iql/`：3 epoch 后人工提前停（按 runbook M5 失败模式）
- E01-E03 probe_gap = -0.984 → -0.980 → -0.968；hold ratio ≥ 98%（**严重塌缩到 Hold**）
- IQL ONNX 仍导出（1.14e-04 max abs diff）以便 P8 agent route 跑诊断

## 4. P8 双路线评估（K2-C 主对照）

### 4.1 K2-C signal route（含 fixed-medium 副对照）

`--strategy signal --signal-threshold 0.58 --force-order-type limit --override-risk-score 1.0`

| 候选 | train PnL | val PnL | **test PnL** | win/lose (test) | mean_sharpe (test) |
|------|----------:|--------:|-------------:|-----------------|-------------------:|
| K2-C 历史 (v1+v2+v3 frozen) | +3282.03 | -95.16 | **+66.10** | 5/5 | n/a |
| **m3_v6_collection_signal**（baseline） | +11438.22 | -313.13 | **-123.49** | 9/16 | -0.35 |
| **m5_v6_bc_signal**（**主候选**）| +15635.10 | -20.78 | **-251.49** | 9/16 | -0.25 |
| **m5_v6_bc_signal_fixed_medium** | +15426.72 | +21.59 | **-209.81** | 7/18 | -0.56 |

### 4.2 M5 agent route（policy_head 直接出 trade，诊断用）

`--strategy agent --override-risk-score 1.0`

| 候选 | train PnL | val PnL | test PnL | trades (test) | flat% (test) |
|------|----------:|--------:|---------:|--------------:|-------------:|
| m5_v6_bc_agent | +7326.39 | -2299.29 | **-2288.78** | 14092 | 10.3% |
| m5_v6_iql_agent | +78.59 | -18.25 | -9.94 | 131 | **98.3%** |

## 5. 关键诊断（test 期失败原因分析）

### 5.1 现象

- **train 健康**：m5_v6_bc_signal train **win/lose=114/0 全胜 + sharpe 11.95**（极强）
- **val 健康（甚至改善）**：v6 val=-21 vs 历史 -95（改善 4.5x）；fixed_medium val=+22（翻正）
- **test 集体失败**：所有 5 候选 test PnL 全为负（最好 m3_collection -123，最差 bc_agent -2289）

### 5.2 根因分解

| 信号 | 含义 |
|------|------|
| M3 离线 test_top_decile_mean_ev_up=**-0.027** | "看涨高置信"在 test 期反而平均跌 → train/test 趋势相反 |
| BC train acc=0.94 vs val acc=0.68 | BC 模型 train 过拟合 |
| BC agent route train +7326 vs test -2289 | BC 直接 trade 在 test 期方向反 |
| IQL 训练 hold=98%，policy_head 信息几乎为零 | IQL 在新数据上无法学到稳定 V-function（与历史 K2-C 用 BC 不用 IQL 的决策一致）|

**核心解释**：v6 test 时段（2026-04-20 ~ 04-24）的 BTC 行情与训练时段（2026-03-23 ~ 04-15）有显著差异（可能 trend 反向、波动率不同等）。M3 backbone 在 train/val 学到的"高 P_up = 看涨"信号在 test 期反向。

K2-C 历史 +66 是在 v3 的 test split (10 windows) 上得到的，那段时间的 BTC 模式刚好与 K2-C 训练分布一致；v6 把 test 切到更晚的 v5 后期，遇到了不同 regime。

### 5.3 与历史 K2-C 的关键差异

| 维度 | K2-C 历史 (v3 frozen) | v6expanded (本次) |
|------|---------------------|-------------------|
| Frozen split sha256 | 7a770e8... | cf2bfe7fa646 |
| train/val/test windows | 39/8/10 | 114/24/25 |
| backbone | m3_run3 (旧 v1+v2+v3) | m3_run_v6expanded (v1~v5) |
| BC checkpoint | j1_b_from_m3 (旧) | m5_run_v6_bc (v1~v5) |
| test 时间窗 | v3 内某段 (具体日期未追溯) | 2026-04-20 ~ 04-24 |

## 6. 执行偏离 runbook 的清单（共 7 处）

| # | runbook 写法 | 实际执行（偏离原因）|
|---|-------------|-------------------|
| 1 | P0 默认跳过 | 必须执行：GPU 落后本地 5 commit + GitHub 直连超时 → autodl 学术加速 + PAT 临时 git fetch + ff-merge |
| 2 | P3 用 prebuilt rust binary | rustup toolchain 损坏 + prebuilt (Apr 16) 与最新源码 ABI 不兼容 → rustup update stable + cargo build (1m51s) |
| 3 | P4 train.py num_workers=8 | DataLoader 触发 fd limit (1024) 崩溃 → ulimit -n 65535（runbook 未提，已实测必加）|
| 4 | P1 假设 5 个 tar.gz 完整 | data-v5_2026-04-25_parquet-data.tar.gz 源端损坏 → 改用 data-v5-2nd.zip raw + migrate_raw_dataset_to_parquet.py（耗时 50min）|
| 5 | P1 验收所有 window 完整 | v5 第 49 个 window `1777017600-1777032000` 缺 btcusdt-orderbook + chainlink → 隔离到 data-v5_quarantine_*；v5 实际跑 48 windows |
| 6 | P2 五 dv 串行 | 改为 5 dv 并行（cli.py 单线程，每进程 1 vCPU，5 进程并行不抢 25 quota）→ 总耗时从估 14h 降到 4h35m |
| 7 | P8 默认串行（cmd_evaluate 不暴露 --threads）| 改为 5 进程并行（每 model_tag 一进程，3 split 串行）→ 估 16h 降到 ~6h；中途 autodl 重启 1 次但 evaluate 内置 resume cache 续跑 18min 完成 4 个 test |

**操作失误**（不算 runbook 偏离）：
- 误读 cgroup `memory.current = anon + page cache`，错杀 IQL agent eval 后又重启（用户提示后修正）
- 中途 SSH 断流 5min（autodl 实例 reboot），全部后台进程被 kill；P8 通过 evaluate 内置 cache 完美续跑

## 7. 后续动作建议

1. **不应把 v6expanded checkpoint 直接进 paper trading / 实盘**——test PnL 反向是明确警告
2. **诊断 BTC 行情分布漂移**：
   - 抓取 4-15 ~ 4-24 的 BTC daily return / volatility / regime 切换
   - 如果是已知的某次行情转折（如重大事件），考虑用更长 window / 更多 v5 后续数据补 train
3. **回测 K2-C 历史路线在 v6 split 上的表现**（如果 j1_b_from_m3/agent_model_m5.onnx 还在）→ 看是不是 v6 backbone 本身的问题，还是 split 选段问题
4. **试 fixed-medium signal route 提前 paper trading**（test=-209 但比主候选好 ~17%；副对照在 train/val 上信号更稳）
5. **M6 准备前的策略复盘**：runbook P9 的"M5 BC test PnL < 0 → 触发 M6 准备前的策略复盘"已生效，本次必须做

## 8. 产物清单（供 aliyunpan 备份）

```
poly-arb-ai/data-pipeline/out/data-v{1..5}/  # M0 产物（manifest/labels/validation/tables/summary.json）
model/feature-engine/out/features_250ms_data-v{1..5}.parquet  # M2 特征
poly-arb-ai/training/checkpoints/m3_run_v6expanded/{best_model.pt, feature_stats.npz, test_metrics.json, train_history.json}
poly-arb-ai/training/onnx/agent_model_76_collection_v6.onnx  # M3 collection ONNX
tick_stream/data-v{1..5}_reward_minimal.parquet  # P6 transition
poly-arb-ai/training/checkpoints/m5_run_v6_bc/{best_model.pt, feature_stats_76.npz, agent_model_m5.onnx}
poly-arb-ai/training/checkpoints/m5_run_v6_iql/{best_model.pt, feature_stats_76.npz, agent_model_m5.onnx}
poly-arb-ai/training/eval/v6/  # P8 全部 15 个 aggregate.json + per-window JSON
poly-arb-ai/training/split/split_info.v6expanded.json
logs/p2_m0_*, logs/p3_*, logs/p4_*, logs/p6_*, logs/p7_*, logs/p8_*
poly-arb-ai/data-pipeline/out_pre_v6_20260427_143002/  # 旧 v3 baseline 备份
```

## 9. 关键时间戳

| 阶段 | 启动 | 完成 | 耗时 |
|------|------|------|------|
| P1 数据落位 | 2026-04-27 14:24 | 14:50（不含 v5 raw migrate）+ 19:32 → 20:23 (v5 raw migrate) | ~22 min + 50 min |
| P2 M0 5 套并行 | 21:20:22 | 04-28 01:55:58 | 4h35m |
| P3 M2 5 套串行 | 04-28 01:56:30 | 02:30:21 | 14m |
| P4 M3 训练 | 02:55:18 | 07:06:24 | 4h11m |
| P5 ONNX 导出 | 07:07 | 07:07 | <1 min |
| P6 collect-transitions + validate | 07:07:59 | 09:53:33 | 2h45m |
| P7 BC 训练 + ONNX | 09:54:15 | 10:55 | ~1h |
| P7 IQL 训练（提前停）| 10:55:48 | 11:28（kill）| 33m |
| P8 评估（含 autodl 重启 1 次）| 11:52:42 | 19:57:26 | ~8h05m |
| **总耗时** | | | **~24h**（自然时间，含 autodl 重启）|
