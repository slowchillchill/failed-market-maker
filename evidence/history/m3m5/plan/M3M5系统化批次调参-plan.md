# Polymarket 5min BTC UP/DOWN — M3 与 M5 系统化批次调参方案

## 0. Context

项目 M0~M5 全链路已在 v6expanded（5 套 data-v1~v5 / 163 windows / 6248 markets / ~7.5M frames）上工程跑通，但训练参数与方法层面没做系统调参：v6 实际跑了 batch=128 / lr=1e-4 / MSE / 无 EMA / 无固定种子，既未应用第二/三轮已验证的 R04+T08 配方（seq=100 + Huber + label_smoothing=0.05 + warmup=2），也未实施第四轮预训练方案（多种子 + EMA + Feature Noise + Focal Loss + Snapshot Ensemble）。

v6 评估结果（K2-C signal route）：m3_v6_collection -123 / m5_v6_bc -251 / agent route -2289 / IQL -10。**单次方差 ≈ 0.17 > 信号 ≈ 0.12**——这次反向结果在统计上和"运气差"无法区分，必须靠多种子 + 多配置 + 多指标的候选清单机制才能稳定区分真实信号和噪声。

### 用户已确认的策略决策

| 决策项 | 选择 |
|--------|------|
| M3 调参规模 | 全面型（含 batch / seq / loss / EMA / focal / noise / seed / snapshot 维度）|
| M5 调参深度 | 含训练方法调整（class_weights / focal / EMA / BC→IQL warm-start）；不重设计 reward / 采集 protocol |
| 候选清单排名 | Multi-metric 加权（仅 val 与 rolling-val，test 不进排序）|
| 数据 / 训练路径 | 不变（v6expanded split + 5 套 data + 现有 features parquet）|

### 核心方法论原则

- **Test 不进调参**：所有 ranking、selection、gating 都基于 train→val→rolling-val 三层；test 仅在 Stage 1C / Stage 3.5 做一次性 confirmation，不参与重新排序。test PnL 进 ranking 等价于把 test 变成调参集，是 ML 泄漏。
- **执行头污染必须隔离**：collection ONNX 的 `size_head/limit_level_head` 是随机初始化（`train.py` 构造模型时新建）；BC 在任何 freeze 下都不训练它们——`train_oracle_bc.py:430` loss 仅对 policy_logits 做 CE，且 `policy_logits` 仅来自 `backbone_out`（`model.py:567`），与 fusion_proj/state_branch/size/limit/order/risk head 无梯度路径；IQL 训练 policy/size/order/limit + state_branch + fusion_proj（`iql.py:175,271-277`），但本计划主榜仍用 fixed exec 与 BC apples-to-apples。Rust 侧 `baseline_strategies.rs:200-208` 的 `force_order_type=limit` 不连带固定 limit_price_level，所以**所有排名命令必须显式 `--fixed-size medium --fixed-limit-level join-best`**——Stage 0 加 `--fixed-limit-level` Rust flag。
- **BC signal route 不评估 BC 训练效果**：j1 BC 的 signal_head 与 M3 collection 完全相同，size/limit 都是随机；signal route 又跳过 policy_head；所以 j1 BC signal route ≡ M3 collection signal route + 随机 head 噪声。BC 主排名走 agent+fixed exec；signal route 仅在 j3（BC 唯一让 backbone 通过 policy_head→backbone_out 反向链得到梯度的 freeze）作辅助参考。
- **两个 leaderboard 严格分开**：(a) Backbone 榜——M3 collection + 仅 j3 BC，评估口径 K2-C signal+`--fixed-size medium --fixed-limit-level join-best --force-order-type limit --signal-threshold 0.58 --override-risk-score 1.0`；(b) Full-policy 诊断榜——BC agent+fixed exec + IQL agent+fixed exec。两榜 schema 不同，不直接合并。
- **Stage gate 拦截无效投入**：每个阶段进入下一阶段前必须满足判据；test confirmation 失败时所有候选仅 shadow，不进 paper trading。
- **不预设结论**：M5 是否有用、IQL 是否能避免塌缩、focal loss 是否提升 PnL，全部由实验回答。
- **批次内同口径对比**：同一批训练用同一 split + 同一评估协议，唯一变化是配置维度。
- **跨 backbone BC 排名按 per-M3 子分组归一化再合榜**：避免 transition 质量差异 conflate BC 配置差异。

---

## 1. Multi-metric 排名公式

所有 ranking 仅用 train + val + rolling-val（val 切 5 段），test 不参与排序。

### Backbone 榜（M3 collection ONNX + 仅 j3 BC ONNX）

K2-C signal route + 双固定执行头（`--fixed-size medium --fixed-limit-level join-best --force-order-type limit --signal-threshold 0.58 --override-risk-score 1.0`）：

| 指标 | 权重 | 来源 |
|------|-----:|------|
| K2-C signal+fixed **val total_pnl** | 0.25 | `aggregate.json` |
| K2-C signal+fixed **val rolling segment median PnL**（val 24 windows 切 5 段）| 0.20 | per-window JSON 后处理 |
| K2-C signal+fixed **val rolling segment worst PnL** | 0.15 | 同上 |
| **M3 离线 val_top_decile_mean_ev_up**（backbone-only 信号能力）| 0.25 | `train_history.json` best epoch 的 val |
| **val_top10_ev_up 末 5 epoch 标准差**（训练稳定性，越低越好）| 0.15 | `train_history.json` 末 5 epoch |

### Full-policy 诊断榜（BC + IQL agent route）

| 候选类型 | 主评估命令 | ranking 用 metric | 备注 |
|---------|-----------|------------------|------|
| BC（任意 freeze）| `--strategy agent --force-order-type limit --fixed-size medium --fixed-limit-level join-best --override-risk-score 1.0` | `k2c_agent_fixed_val_*` | size/order/limit 都随机，必须固定才纯净测 BC policy 方向能力 |
| IQL（apples-to-apples 主榜）| 同上 fixed exec | `k2c_agent_fixed_val_*` | 与 BC 同口径，只测 policy_head 方向能力 |
| IQL native（仅记录，不入主榜）| `--strategy agent --override-risk-score 1.0` | `k2c_agent_native_val_pnl` 仅 info | IQL 训过执行头；如 native 显著 > fixed → paper 时考虑切到 native |

主榜 ranking 公式（统一 BC + IQL）：

| 指标 | 权重 | 来源 |
|------|-----:|------|
| **k2c_agent_fixed_val_total_pnl** | 0.30 | `aggregate.json` |
| **k2c_agent_fixed_val_mean_sharpe** | 0.20 | 同上 |
| **k2c_agent_fixed_val_winrate** | 0.15 | 同上 |
| **k2c_agent_fixed_val_rolling_median_pnl** | 0.20 | per-window 后处理 |
| **k2c_agent_fixed_val_rolling_worst_pnl** | 0.15 | 同上 |

### 归一化与排名

- 同一榜内 min-max 归一化（PnL/Sharpe/winrate 越高越好；val_top10_5ep_std 越低越好）
- 跨 backbone 的 BC 候选先在该 backbone 的 per-M3 子分组内归一化，再合到 full-policy 榜
- M3 inference ensemble 候选（M3-B-ens 多种子集成 + M3-B8-ens snapshot 集成）只看 Python 端 offline `val_top_decile_mean_ev_up`，**不进 backbone 榜**（Rust evaluate 仅吃单 ONNX，详见 §3.7）

### 输出

- 两榜各自 `top-3 综合候选` + 两榜各自 `top-1 per-metric`
- 全部记录写入 `poly-arb-ai/training/candidates_ledger.json`，schema 按 leaderboard 拆字段
- **关键约束**：所有进 paper trading 的候选必须额外通过 Pre-Paper-Trading Gate 的 test confirmation（详见 §4.4 / §6.4 / §7.2）；ranking top-3 仅决定**进入 confirmation 的资格**，不等于自动进 paper；未通过 confirmation 的候选仅进 shadow 诊断

---

## 2. 阶段路线（含 5 个 hard gates）

```
Stage 0 ─→ 基础设施 + Holdout 诊断 + 新 Rust flag
   │       （~7-9h 本地 dev + 0.5h GPU）
   ▼
Stage 1A ─→ M3 pilot：batch/seq/loss 小网格选 central config
   │       （5-7 runs，~10-15h GPU）
   │
   │   🚦 Pre-1B Gate：top val K2-C signal+fixed PnL > 0
   │   或 val_top10_ev_up > +0.10。否则停止，写诊断 doc
   ▼
Stage 1B ─→ M3 method sweep：在 central config 上做 EMA / focal / noise / seed
   │       （8-10 runs，~10-15h GPU；如 central=128 则 ~25-30h）
   ▼
Stage 1C ─→ Backbone 榜出榜 + top-3 一次 test confirmation
   │       （~1-2h GPU；test 不重排序）
   │
   │   🚦 Pre-Stage 2 Gate：top-1 backbone val PnL > 0 且 rolling worst > -100
   │   不过 → 跳过 M5；进入下一 gate
   │
   │   🚦 Pre-Paper-Trading Gate (Backbone)：top-1 by val 的 test PnL > 0 且
   │   test rolling worst > -100。不过 → 全部候选仅 shadow only，
   │   不进 paper trading；触发 split / regime 复盘独立 plan
   ▼
Stage 2 ─→ M5 BC 诊断：仅 top-1~top-2 M3，7-8 BC configs each
   │       （~25-33h GPU；仅 j1 默认，agent+fixed 主，j3 才补 signal+fixed）
   │
   │   🚦 Pre-Stage 3 Gate：top-1 BC agent val PnL > Hold baseline (-8.09)
   │   不过 → 不做 IQL
   ▼
Stage 3 ─→ M5 IQL 诊断：3 runs total（仅 top-1 M3）
   │       （~3-5h GPU；agent+fixed 主，native agent 仅 info）
   ▼
Stage 3.5 ─→ Full-policy top-1 test confirmation
   │       （~1-2h GPU；仅当 Stage 2/3 至少有候选 val PnL > Hold baseline）
   │
   │   🚦 Pre-Paper-Trading Gate (Full-policy)：top-1 by val 的 test PnL > 0 且
   │   test rolling worst > -100。不过 → full_policy 全部仅 shadow
   ▼
Stage 4 ─→ 双榜出榜 + 候选清单写入 dev-docs
          （~1h 脚本 + ~3h 文档 = ~4h）
          paper trading 候选 = 通过 Backbone Pre-Paper Gate 的 top-1/top-2（主+备 1）
                              + 通过 Full-policy Pre-Paper Gate 的 top-1（备 2）；
                              其余 → shadow 诊断
```

**总成本估算**（与 §12 per-stage 加和完全一致；rolling eval 改为 per-window 后处理后零额外 GPU）：

- GPU **pessimistic-A（所有 gate 全过 + central batch ≥ 512）**：~66-77h
- GPU **pessimistic-B（central batch=128，1B 训练翻倍）**：~81-97h
- GPU **mid（Pre-Stage 2 Gate 不过，跳过 M5/M5+IQL）**：~22-32h
- GPU **optimistic（Pre-1B Gate 不过，立即停）**：~14-19h
- 本地 dev + 文档：~12-15h
- 日历周期：约 1-4 个连续日历天（GPU 不并行）

---

## 3. Stage 0 — 基础设施 + Holdout 诊断 + 新 Rust flag

**目标**：在批量调参开跑前，把"可重复性、可对比、可累积、执行头可固定"的工程基础打好。

### 3.1 train.py 新增 5 个 flag（约 100 行 Python）

| flag | 含义 | 默认 | 影响位置 |
|------|------|------|---------|
| `--seed INT` | 固定 random/numpy/torch 种子 + cudnn deterministic | None（不固定）| train.py:223 main 入口 |
| `--ema-decay FLOAT` | EMA 权重衰减系数；启用时 best_model.pt 存 EMA 权重 | 0.0（禁用）| 新增 ModelEMA 类（30 行）+ train.py:103 step 后 update + train.py:134/387/413 swap 权重 |
| `--feature-noise FLOAT` | 训练时 obs += randn × σ（仅 train，eval 不加）| 0.0（禁用）| train.py:86-92，obs.to(device) 之后、autocast 之前 |
| `--focal-gamma FLOAT` | Cls 头用 focal CE（γ > 0 启用）| 0.0（退化为 CE）| loss.py:54 替换 cross_entropy 为新 focal_loss 实现 |
| `--snapshot-epochs LIST` | 在指定 epoch 末额外存 ckpt；缺失 epoch 跳过 + WARN | []（禁用）| train.py:382-410 best 保存逻辑旁加 snapshot 保存；K2-C eval 仅用 best ckpt（snapshot ensemble 仅 Python offline 对照）|

所有新 flag 默认值都让训练行为与 v6 完全一致（M3-A0 anchor 必须能复现 v6 旧 test_metrics 在统计噪声内）。

### 3.2 EMA 与 `torch.compile` 兼容

`torch.compile()` 把模型 wrap 成 `OptimizedModule`。EMA 实现要点：

1. `ModelEMA.__init__` 接收的 `model` 先 unwrap：`base = model._orig_mod if hasattr(model, "_orig_mod") else model`
2. EMA shadow 参数从 `base.parameters()` 拷贝；`update(model)` / `apply_to(model)` 都先 unwrap
3. Smoke 验证：`--compile --ema-decay 0.999` 跑 1 epoch 不报错且 val 指标合理
4. Fallback：实现复杂度过高时，启用 EMA 自动强制 `--compile=False` + 提示

### 3.3 train_oracle_bc.py 新增 4 个 flag（约 60 行 Python）

| flag | 含义 | 默认 | 影响位置 |
|------|------|------|---------|
| `--seed INT` | 同上 | None | main 入口 |
| `--ema-decay FLOAT` | BC 训练 EMA（共享 ModelEMA 类）| 0.0 | 新增 EMA 引用 |
| `--class-balance MODE` | `none` / `inv_freq` / `inv_freq_0.75` 三选；公式 `w_i = (max_freq / freq_i) ** alpha` | `none` | train_oracle_bc.py:140-150 class_weights 算法分支 |
| `--focal-gamma FLOAT` | BC cls focal | 0.0 | train_oracle_bc.py:390 替换 F.cross_entropy |

`oracle_mode {A,B,C}` 与 `freeze_scope {j1,j2,j3}` 是已有 flag。本 plan 实际矩阵仅用 oracle B/C 与 freeze j1（默认）+ j3（可选 BC-7）；smoke 阶段单独验证 oracle A 兼容性，留作未来扩展。

### 3.4 train_iql.py 新增 1 个 flag + 复用既有 flag

| flag | 含义 | 默认 | 影响位置 |
|------|------|------|---------|
| `--seed INT` | 同上 | None | main 入口 |
| `--init-agent-checkpoint PATH`（已存在）| 从 BC / 旧 agent checkpoint warm-start。本计划用法：传 BC best_model.pt，仅加载 policy_head + state_branch + fusion_proj 子集（即 IQL 训练的 head 集合），跳过 mismatch keys（如 BC 没训过 risk_head 但 ckpt 含其权重）| None | `train_iql.py:80,162` 既有逻辑；docstring 补"BC warm-start 用法"说明 |

### 3.5 Rust agent 新增 `--fixed-limit-level` flag

**问题背景**：`baseline_strategies.rs:200-208` 只有 `force_order_type=Market` 才会自动 `limit_price_level=JoinBest`；当 `force_order_type=Limit`（K2-C 必用），limit_price_level 仍读 ONNX 的 `limit_level_head` 输出——而该 head 在 M3 collection 与 BC（任何 freeze 下）ONNX 中都是随机初始化。这导致 K2-C signal route 的 PnL 含随机执行头噪声，cross-candidate 排名不可信。

**修法**（约 30 行 Rust）：

| 文件 | 改动 |
|------|------|
| `rust/agent/src/baseline_strategies.rs:60` | `BaselineConfig` 加 `pub fixed_limit_level: Option<LimitPriceLevelAction>` 字段 |
| `rust/agent/src/baseline_strategies.rs:206-208` | 在 `if let Some(sz) = self.fixed_size` 后追加 `if let Some(ll) = self.fixed_limit_level { actions.limit_price_level = ll; }` |
| `rust/agent/src/main.rs:125,195` | `EvaluateArgs` / `CollectArgs` 加 `#[arg(long)] fixed_limit_level: Option<String>` |
| `rust/agent/src/main.rs:243` | 加 `parse_limit_level()` 函数；枚举字符串：`join-best` / `improve1` / `improve2` / `passive1` / `passive2`（与 `model_output.rs:103-110` `LimitPriceLevelAction` 5 类完全对应）|
| `rust/agent/src/main.rs:266` | `cfg.fixed_limit_level = parse_limit_level(args.fixed_limit_level.as_ref())?;` |

**Backbone 榜评估必用**：`--fixed-size medium --fixed-limit-level join-best`。

### 3.6 `validate_transitions.py` 加 `--ignore-reward-range` flag（约 10 行 Python）

`validate_transitions.py:282-285` 在 G2 fail 时强制 `gates_ok=False` 并退出 1。但 reward_minimal（reward_clip=0）下结算 tick 的 ±10-20 USDC 会让 `reward p99-p01` 远超 G2 限制 2.0，G2 必然 FAIL。修法：

```python
parser.add_argument("--ignore-reward-range", action="store_true",
                    help="Skip G2 (reward p99-p01) check. Required for reward_minimal mode.")

# L274 G2 块改为：
if args.ignore_reward_range:
    print(f"  [G2] reward p99-p01 = {reward_range:.4f} (SKIP — --ignore-reward-range)")
elif not g2_pass:
    gates_ok = False
```

Stage 2 §5.1 默认带 `--ignore-reward-range`，G1/G3 仍是 hard gate。

### 3.7 候选 ledger 工具（约 100 行 Python）

新建 `poly-arb-ai/training/candidate_ledger.py`：

- `register_run(run_id, stage, leaderboard, config, paths)`：写入 entry，**leaderboard ∈ {backbone, full_policy}**，决定 score schema
- `attach_metrics(run_id, metrics_dict)`
- `compute_score(run_id, leaderboard, weights, scope='batch'|'global')`
- `rank_top(leaderboard, k, scope='batch'|'global')`
- 持久化：`poly-arb-ai/training/candidates_ledger.json`

新建包装脚本：

- `scripts/run_one_m3.sh`：train.py + export ONNX + K2-C signal+fixed eval（val + rolling-val）+ ledger register（leaderboard=backbone）
- `scripts/run_one_bc.sh`：train_oracle_bc + export ONNX + agent+fixed route eval + ledger register（leaderboard=full_policy）
- `scripts/run_one_iql.sh`：train_iql + export ONNX（含可失败补导）+ agent+fixed route eval + ledger register（leaderboard=full_policy）
- `scripts/eval_rolling_segments.py`：**不重跑 evaluate**——`AggregatedReport`（`evaluation.rs:188-215`）无 per-window 字段；per-window 数据在 `<dataset>__<window>.json`（`main.rs:831`）。脚本接收 `--eval-dir`，glob 该目录下所有 `*__*.json` 读 PerformanceMetrics，按 window_id（前缀是 epoch 秒）排序切 N 段（默认 5），输出 `rolling_segments.json: {segments: [...], median_pnl, worst_pnl}`。**rolling 评估的 GPU 成本 = 0**（仅 Python 后处理）。
- `scripts/ensemble_inference.py`（限 Python 端）：N 个 ONNX → 平均 logits/ev_pred → 计算 offline `top_decile_mean_ev_up` / AUC。**K2-C 等价 PnL 不实现**——Rust evaluate 仅接受单 ONNX；扩展多 ONNX 评估在数百行新代码量级，本计划不做。M3 inference ensemble 候选（M3-B-ens / M3-B8-ens）只跑 Python 端 offline 指标，不进 backbone 榜；如集成 offline 指标显著好于 single-best 可触发独立立项。

### 3.8 Smoke 验收

| 检查项 | 命令 | 通过条件 |
|--------|------|---------|
| 5+4+1 个 Python flag 注册（IQL 仅新增 `--seed`）| 三个 `--help` 各 grep 一次 | 全部出现 |
| 1 个 Rust flag 注册 | `cargo run -p agent -- evaluate --help \| grep fixed-limit-level` | 出现 |
| 默认行为不变（M3-A0 anchor 1 epoch smoke）| 必须传全部 5 套 parquet——`split_by_canonical` 强制 train/val/test 都非空（`dataloader.py:524-526`），单 dv 会 crash | val_top10_ev / loss / auc 在历史方差内 |
| EMA + compile 共存 | 1 epoch smoke | 不 crash 且 val 指标合理 |
| Focal γ=2 数值稳定 | 1 epoch smoke | cls_loss 不 NaN |
| BC oracle A 兼容性（当前 BC 矩阵不含 A，仅未来扩展验证）| `train_oracle_bc.py --epochs 1 --oracle-mode A` | 1 epoch 不 crash 即记录通过；不通过仅在 dev-docs 标记，本 plan 矩阵不受影响 |
| Rust `--fixed-limit-level` 生效 | **不依赖 trades.json**（TradeLog 只存 `order_type / limit_price`，无 `limit_price_level` 字段，见 `replay.rs:187-204`）。改用 Rust 单元测试：在 `baseline_strategies.rs:320+` 现有 `tests` mod 加 `fn fixed_limit_level_overrides()`：构造 `BaselineConfig{ fixed_limit_level: Some(JoinBest), ... }` + 任意 ONNX 输出 → 调 `decide_actions()` → assert 输出 `limit_price_level == JoinBest`。`cargo test --release -p agent fixed_limit_level_overrides` 通过 | unit test PASS |
| `validate_transitions.py --ignore-reward-range` 生效 | 用 v6 现有 `tick_stream/data-v1_reward_minimal.parquet` 跑：`python3 validate_transitions.py --paths ... --ignore-reward-range` | exit 0；G1/G3 PASS；G2 显示 SKIP |
| ledger CRUD（含 leaderboard 字段）| smoke 脚本 | register（含 leaderboard）→ attach → 两 schema rank 都成功 |
| `eval_rolling_segments.py` 后处理 | 用 v6 现有 `eval/v6/m3_v6_collection_signal__val/aggregate.json` 同目录跑后处理 | 输出 `rolling_segments.json` 含 5 段 + median_pnl + worst_pnl |

### 3.9 Holdout 诊断（拆两步：先 evaluate 写 per-window，再 rolling 后处理）

复用现有 `agent_model_76_collection_v6.onnx`，把 v6 val 切 5 段算 PnL，作为 Backbone 榜 "rolling segment median/worst" 的 baseline 锚点。

```bash
# 步骤 1：跑 evaluate 写 per-window PerformanceMetrics（~25min GPU）
cargo run --release --manifest-path poly-arb-ai/rust/Cargo.toml -p agent -- evaluate \
  --model-path poly-arb-ai/training/onnx/agent_model_76_collection_v6.onnx \
  --split-info poly-arb-ai/training/split/split_info.v6expanded.json --split val \
  --strategy signal --signal-threshold 0.58 --force-order-type limit \
  --fixed-size medium --fixed-limit-level join-best --override-risk-score 1.0 \
  --output poly-arb-ai/training/eval/v6_baseline_val \
  --seq-len 240 --starting-cash 100.0

# 步骤 2：纯 Python 后处理，零 GPU（~10s）
PYTHONPATH=poly-arb-ai python3 poly-arb-ai/scripts/eval_rolling_segments.py \
  --eval-dir poly-arb-ai/training/eval/v6_baseline_val \
  --segment-size 5 \
  --output poly-arb-ai/training/eval/v6_holdout_val_segments.json
```

### 3.10 seq_len 切换后的 sample 数 sanity

dataloader.py 用 seq_len 控制冷启动排除。Stage 0 dev 末尾跑一次 sanity log：

```bash
PYTHONPATH=poly-arb-ai python3 poly-arb-ai/scripts/dataloader_sample_count_sanity.py \
  --parquet-paths model/feature-engine/out/features_250ms_data-v{1..5}.parquet \
  --split-info poly-arb-ai/training/split/split_info.v6expanded.json \
  --seq-lens 100 120 180 240
```

期望：每个 seq_len 都打印 train/val/test 三 split 的 valid 行数。

---

## 4. Stage 1 — M3 系统调参（拆 1A pilot / 1B sweep / 1C confirmation）

### 4.1 关键设计：batch 作为 primary 搜索维度

前三轮历史超参数搜索默认 batch=2048（Round 1 E05/E10、Round 2 R04、Round 3 T08 全部 batch=2048），m3_run3 production baseline 也是 batch=2048+lr=4e-4 / 92% GPU util。前三轮没有任何一轮把 batch 当成搜索维度；v6 把 batch 降到 128 + lr=1e-4 没有解释依据。

**理论假设**：v6expanded 数据 ~5x 于 m3_run3，每 epoch step 数从 ~500 涨到 ~2637（更多 step）。小 batch 对分布漂移更鲁棒的真实理由是 **SGD 噪声尺度与 batch 大小成反比**——小 batch 给每步更新引入更大随机扰动，类似隐式正则；这在分布漂移场景（v6 train→test regime shift 已确诊）下可能比大 batch 更好。但这是假设，必须由 batch sweep 实证。

**lr-batch 缩放规则**（plan 默认值；smoke 阶段任一组合发散可调整）：

| batch | 推荐 lr | 备注 |
|------:|--------:|:-----|
| 128 | 1e-4 | v6 lr |
| 256 | 1.5e-4 | sqrt-ish |
| 512 | 2e-4 | sqrt-ish |
| 1024 | 3e-4 | sqrt-ish |
| 2048 | 4e-4 | T08 / m3_run3 默认 |

### 4.2 Stage 1A — M3 pilot（5-7 runs，~10-15h GPU）

**目标**：在 batch / seq / loss 三个 primary 维度上做小网格 pilot，按 val + rolling-val 选出 "central config" 供 Stage 1B 的方法 sweep 使用。

固定基础（pilot 阶段都用，**A0 anchor 例外**）：
- `--epochs 30 --patience 5 --d-model 128 --n-transformer-layers 2 --nhead 4 --dropout 0.1`
- `--lambda-cls 1.0 --lambda-ev 0.5 --weight-decay 1e-4 --warmup-epochs 2 --label-smoothing 0.05`
- `--device cuda --num-workers 8 --amp --compile --seed 42`

**A0 anchor 例外**：A0 = "v6 同口径" 指**操作语义对齐 v6 实际运行**（v6 没用 warmup / label_smoothing / compile），所以 A0 不带 `--warmup-epochs --label-smoothing --compile` 三 flag。其他 A1+ 全部带固定基础。

| ID | seq | batch | lr | loss | 备注 |
|:---|----:|------:|---:|:-----|:-----|
| **M3-A0**（anchor）| 240 | 128 | 1e-4 | mse | v6 操作语义同口径（不带 warmup/smooth/compile），不进 ledger；epoch 1 sanity 即可 kill（compromise C） |
| ~~**M3-A1**~~ | ~~100~~ | ~~128~~ | ~~1e-4~~ | ~~huber~~ | **skip**（用户决策 B+C：v6expanded 5.4M 数据下 batch=128 GPU util ~18% 严重 underutilized，且 A0 epoch 1 已部分 sanity）|
| **M3-A2** | 100 | 256 | 1.5e-4 | huber | batch sweep / 256（实证 val_top10 第 2 / val PnL +222 / fat tail -57）|
| **M3-A3** | 100 | 512 | 2e-4 | huber | batch sweep / 512（val PnL +279 / fat tail -75）|
| **M3-A4** | 100 | 1024 | 3e-4 | huber | batch sweep / 1024（val PnL +112 / fat tail -28）|
| **M3-A5** | 100 | 2048 | 4e-4 | huber | batch sweep / 2048（m3_run3 同口径；实证 val PnL -13 outlier）|
| **M3-A6** | 100 | 4096 | 5.6e-4 | huber | batch sweep / 4096（**Stage 1A winner**：val PnL +280 / fat tail -8 / score 0.692）|
| **M3-A7** | 100 | 8192 | 8e-4 | huber | batch sweep / 8192（val PnL +64 / fat tail -65）|
| **M3-A8** | 100 | 3072 | 4.9e-4 | huber | 细粒度 sweep / 3072（B+C 扩展；val PnL +89 / fat tail -42）|
| **M3-A9** | 100 | 5120 | 6.3e-4 | huber | 细粒度 sweep / 5120（B+C 扩展；val PnL +108 / fat tail -148 ⚠️）|
| **M3-A10** | 100 | 6144 | 6.9e-4 | huber | 细粒度 sweep / 6144（B+C 扩展；val_top10 第 1 +0.263 但 val PnL 仅 +39 — signal-PnL 解耦）|

**lr 缩放规则**（实证使用的 sqrt-ish）：lr ∝ √(batch / 256) × 1.5e-4，例如 batch=4096 → lr ≈ √16 × 1.5e-4 = 6e-4（实际取 5.6e-4）。

**实际执行顺序**（chain）：A0 → A5 → A6 → A7 → A4 → A3 → A2 → intercept_v2 切换 → A8 → A9 → A10。原 plan "A1 优先" 被 user 决策 B+C 替换为 "skip A1 + 加细粒度 batch sweep"。

**evaluate 工程实测**：单 run K2-C signal+fixed val eval ~33 min（24 windows × ~85s/window）是 Stage 1A 的真瓶颈，远超 train（batch=4096+ 的 train ~12-20 min）。

**评估**：每个 run 训完 → export collection ONNX → K2-C signal+fixed val eval（rolling 5 seg 通过 per-window JSON 后处理派生）→ M3 离线 val_top10_ev_up → 写 ledger（leaderboard=backbone）。**不跑 test split**。

**Pre-1B Gate**：top-1 by Backbone 榜 score 必须满足任一：
- val K2-C signal+fixed PnL > 0
- val_top10_ev_up > +0.10（v6 best epoch 是 +0.123）

任一通过 → 进 Stage 1B；否则停止，写 dev-docs 记录"v6expanded 数据下 T08 配方 + batch sweep 也无法转正"。

**central config 选择规则**：取 Pre-1B Gate 通过候选中 score 最高的，记为 `(seq*, batch*, lr*)`。

**GPU 时长**（实测；A1 skip 后 9 个有效 datapoint）：

| 子任务 | 单次时长 | 数量 | 小计 |
|--------|---------:|-----:|-----:|
| M3-A0 anchor（epoch 1 sanity 即 kill）| ~25 min | 1 | ~25 min |
| M3-A2 train（batch=256）| ~150 min | 1 | ~2.5h |
| M3-A3 train（batch=512）| ~80 min | 1 | ~1.3h |
| M3-A4 train（batch=1024）| ~50 min | 1 | ~0.8h |
| M3-A5 train（batch=2048）| ~25 min | 1 | ~0.4h |
| M3-A6 train（batch=4096）| ~20 min | 1 | ~0.3h |
| M3-A7 train（batch=8192）| ~12 min | 1 | ~0.2h |
| M3-A8 train（batch=3072）| ~17 min | 1 | ~0.3h |
| M3-A9 train（batch=5120）| ~14 min | 1 | ~0.2h |
| M3-A10 train（batch=6144）| ~16 min | 1 | ~0.3h |
| ONNX export | ~1 min | 9 | ~9 min |
| K2-C signal+fixed val eval | ~33 min | 9 | ~5.0h |
| **小计**（实测）| | | **~11-12h** |

注：原 plan §4.2 估的 "10-15h" 偏乐观（按 5-7 runs 估），实际跑 9 runs 约 11-12h，与原估算上限近似。K2-C eval 33 min/run 是 sequential bottleneck，远超 train 时长。

**安全网**：
- M3-A0 anchor 优先跑：epoch 1 sanity（val_top10_ev / loss / auc 在 v6 E01 量级 ±2 σ 内）即可 kill；若不在 → 暂停后续，先排查新 flag 实现 bug
- M3-A2..M3-A10 任何一个在 ep 1-2 NaN 或 val_loss > 5 → 该 batch 大概率 lr 不匹配；按"batch 减半 → lr 减半"重试一次，仍发散就标 fail 并跳过
- 原计划 M3-A1（batch=128）已 skip（理由见 grid 表）；下次类似计划若 GPU util 数据可用，应在 plan 阶段就剔除明显 underutilize 的 batch 档

### 4.3 Stage 1B — M3 method sweep at central config（8-10 runs，~10-15h GPU；central=128 时 ~25-30h）

**目标**：在 1A 选出的 `(seq*, batch*, lr*)` 上做方差控制 + 方法 tuning。

| ID | 与 central 的差异 | 备注 |
|:---|:------------------|:-----|
| **M3-B0**（central）| `--seed 42 --ema-decay 0`（与 1A 中胜出 run 一致；不重训，复用 ckpt）| central anchor，进 ledger |
| **M3-B1** | `+--ema-decay 0.999` | EMA 保守 |
| **M3-B2** | `+--ema-decay 0.99` | EMA 激进 |
| **M3-B3** | `+--ema-decay 0.999 --seed 123` | 第 2 种子（与 B1 同 EMA）|
| **M3-B4** | `+--ema-decay 0.999 --seed 7` | 第 3 种子 |
| **M3-B5** | `+--ema-decay 0.999 --focal-gamma 2.0` | Focal CE |
| **M3-B6** | `+--ema-decay 0.999 --label-smoothing 0.10` | 激进 label smooth |
| **M3-B7** | `+--ema-decay 0.999 --feature-noise 0.05` | Feature noise |
| **M3-B8** | `+--ema-decay 0.999 --snapshot-epochs 3,5,7` | Snapshot 保存：训练时多保存 ckpt；K2-C eval 仅用 best ckpt（与其他 run 一样进 backbone 榜，单 ONNX）；snapshot 的 ensemble 效应仅 Python offline 对照 |
| **M3-B-ens**（仅 Python offline，**不进 backbone 榜**）| 平均 M3-B1 + M3-B3 + M3-B4 三种子 logits | offline `val_top10_ev_up` 与 single-best 对比 |
| **M3-B8-ens**（仅 Python offline，**不进 backbone 榜**）| 平均 M3-B8 的 snapshot ckpts (ep 3,5,7) | 同上性质；与 M3-B8 single-best 对比 |

**评估**：同 1A，每个 run K2-C signal+fixed val eval（rolling 5 seg 通过 per-window JSON 后处理派生，零额外 GPU 成本）+ M3 离线指标。

**GPU 时长**：

- 8-9 个 train × ~30-50min（central batch ≥ 512 假设）= ~5-8h
- ONNX export + val K2-C eval ≈ 30-40min × 9 = ~5-6h
- **小计**：~10-15h
- 若 1A 选出 central batch=128，1B 训练时长上升到 8 × 2.5h ≈ 20h，总 ~25-30h

### 4.4 Stage 1C — Backbone 榜出榜 + top-3 一次 test confirmation（~1-2h GPU）

合并 1A + 1B 的所有 ledger entry（leaderboard=backbone），按 §1 加权打分排名。

**Duplicate 去重原则（unique top-3）**：当两个 run 的 ledger metrics 是 4 位小数级 identical（典型情况：B8 = B1 + snapshot-epochs side output flag，snapshot save 不影响 train loss / EMA / weight update，best_ckpt 完全相同），**只占 unique top-3 中一个 slot**（保留 score tie 中 run_id 字典序最早的，或显式人工选定）。Snapshot Ensemble 的真实收益评估**仅** 通过 `ensemble_inference.py` offline 平均 ckpts logits，结果只入 dev-docs 不进 backbone 榜（plan §1 / §3.7 约束）。

**人工 override 条款（manual top-3 substitution）**：默认 Stage 1C top-3 = 按 ledger score 排序的 unique top-3。但允许**人工 override**用相邻 score 候选替换默认 top-3 entry，**前提条件**：
- override 必须**在 Stage 1C test split 评估前**做出（不能 test 后回头改）
- override 必须在 dev changelog 写明 reasoning（为什么换 vs 默认按 score）
- override 候选 **score 差距 ≤ 5%**（避免选 score 差距过大的备选）
- override 候选**仍需通过 Pre-Paper-Trading Gate** 才能进 paper

**为什么允许 override**：score 公式是 5-metric weighted，不一定完美 capture "可解释性 / 简洁性 / mechanism robustness" 等定性因素。例如 baseline run（无 modifier）通过 test confirmation 比 modifier run 通过，对 paper trading 决策 confidence 更高。

**Top-3 一次性 test 评估**：

```bash
for tag in $top3_run_ids; do
  cargo run --release --manifest-path poly-arb-ai/rust/Cargo.toml -p agent -- evaluate \
    --model-path <onnx_$tag> \
    --split-info poly-arb-ai/training/split/split_info.v6expanded.json \
    --split test \
    --strategy signal --signal-threshold 0.58 --force-order-type limit \
    --fixed-size medium --fixed-limit-level join-best --override-risk-score 1.0 \
    --output poly-arb-ai/training/eval/v7_final/$tag__test \
    --seq-len <对应 seq_len> --starting-cash 100.0
done
```

**重要约束**：test 结果只用于最终接受/拒绝，**不能用来重新排序选 top-1**（不切换到 top-2，那是 test 泄漏），但**也不能在 test 失败时强行进 paper trading**——那就把 paper trading 当成 test 拒绝时的兜底，等于绕过 confirmation。

**Pre-Stage 2 Gate**：
- Backbone 榜 top-1 val K2-C signal+fixed PnL **显著好于 v6 baseline**（v6 m3_collection val 当时约 -313）
- 显著标准：val PnL > 0 且 rolling worst segment > -100
- 通过 → 启动 Stage 2；不过 → 跳过 M5（无论 test confirmation 结果）

**Pre-Paper-Trading Gate (Backbone)（无论 Pre-Stage 2 是否通过都执行）**：
- top-1 by val 的 **test K2-C signal+fixed PnL > 0** 且 **test rolling worst segment > -100**
- **通过** → top-1 进 paper trading 主候选；备选用 backbone 榜 top-2（如其 test 也通过该 gate）
- **不通过** → 本轮无 offline-confirmed backbone 候选，所有 backbone 候选仅进 shadow 诊断；同时触发 split / regime 复盘独立 plan（v6 test 段是否有结构性问题：BTC 4-20~4-24 行情、流动性、Polymarket 出清 anomaly 等）

**注**：full_policy 候选（BC / IQL）的对应 Pre-Paper-Trading Gate 在 Stage 3.5 单独执行，详见 §6.4 / §7.1。

**为什么 test 失败 ≠ 切换 top-2**：如果允许 "test 失败时挑 test PnL 最高的 candidate"，等价于把 test 当 ranking criterion，是经典泄漏；正确动作是承认本轮选型未通过，调查根因。

**为什么 test 失败 ≠ paper trading**：paper trading 等同于"小金额验证"或"软实盘"，已超过纯 offline；如果 test 都没通过就上 paper，相当于把 paper 当 test 用，会让真金白银承担本应在 offline 阶段拒绝的方法论风险。

---

## 5. Stage 2 — M5 BC 诊断（top 2 backbone B1 + B2，7-8 BC each；~25-33h GPU）

**目标**：诊断 BC 在新 backbone 上是否仍然让 PnL 变差（v6 上 BC -251 vs collection -123）。这是诊断而非主路径——backbone 候选已经独立可用。

**Stage 2 backbone scope（top-2 by val score + A6 人工追加）**：
- top-1: **m3_run_v7_M3-B1** (A6 + EMA 0.999, val PnL +424, test PnL +92)
- top-2: **m3_run_v7_M3-B2** (A6 + EMA 0.99, val PnL +416, test PnL +138)
- 追加: **m3_run_v7_M3-A6** (baseline no EMA, val PnL +280, test PnL +86) — Stage 1C 人工 override 候选，Pre-Paper-Trading Gate PASS

**A6 追加 reasoning**（plan §4.4 人工 override 条款类比扩展）：
- A6 是 Stage 1C top-3 confirmation 之一（B5 → A6 override），test PASS → paper trading 备份候选
- A6 是 baseline (no EMA)，与 B1/B2 (EMA 系) backbone 训出的 transition tick_stream 数据分布显著不同 → BC × A6 不能从 BC × B1/B2 推断
- 多 backbone full-policy 候选给 paper trading 备选 2 路线更多选项
- 成本 ~9-10h GPU 增量，对于全 Stage 2 ~25-33h 的占比 ~30%，可接受

下面命令模板以 `M3_ID` 变量代入；实际跑时分别替换为 `m3_run_v7_M3-B1` / `m3_run_v7_M3-B2` / `m3_run_v7_M3-A6`。所有 backbone seq_len = 100。

### 5.1 前置：对每个 top M3 重新采集 transition

reward.rs 不动 / 采集 protocol（reward_minimal + mix-as + seed=20260408）不动，但**每个 backbone 必须用对应 collection ONNX 重新跑 collect-transitions**——这是技术必要，不属于"reward 设计变化"。

```bash
# M3_ID ∈ { m3_run_v7_M3-B1, m3_run_v7_M3-B2 }
for M3_ID in m3_run_v7_M3-B1 m3_run_v7_M3-B2 m3_run_v7_M3-A6; do
  for dv in data-v1 data-v2 data-v3 data-v4 data-v5; do
    cargo run --release --manifest-path poly-arb-ai/rust/Cargo.toml -p agent -- \
      collect-transitions \
        --model-path poly-arb-ai/training/onnx/${M3_ID}_collection.onnx \
        --dataset-version $dv \
        --output tick_stream_v7_${M3_ID}/${dv}_reward_minimal.parquet \
        --seq-len 100 --starting-cash 100.0 \
        --alpha-loss 1.0 --lambda-turn 0 --lambda-dd 0 --lambda-idle 0 --reward-clip 0 \
        --collection-policy mix-as --sampling-temperature 1.0 --epsilon-random 0.05 \
        --seed 20260408 --threads 16
  done

  # G1/G3 hard gate（必须带 --ignore-reward-range，否则 G2 误杀）
  PYTHONPATH=poly-arb-ai python3 poly-arb-ai/training/validate_transitions.py \
    --paths tick_stream_v7_${M3_ID}/*_reward_minimal.parquet \
    --ignore-reward-range
  # G1（NAV<0 < 0.01%）和 G3（action entropy > 1.2）必须 PASS
  # exit code: G1 或 G3 fail 时 exit 1（hard fail）
done
```

时长：每个 M3 ≈ 2.5-3h；top 1-2 M3 = ~5-6h。两个 backbone 共享 seq_len=100，但 collection ONNX 不同 → tick_stream 不同 → BC 训练数据不同。**BC 候选先在同一 M3 内排名，再做总榜**。

### 5.2 BC 配置矩阵（per top M3，7-8 configs）

固定基础：`--epochs 20 --device cuda --num-workers 8 --early-stop-patience 3`

**评估口径分工**：
- agent route + 固定执行头是 BC 的主评估口径（policy_head 是 BC 唯一被监督训过的方向决策头）
- signal route 仅在 freeze=j3 时跑（j3 让 backbone 通过 policy_head 反向链接得到梯度 → backbone_out 变化 → signal_head 读到不同输入 → signal route 间接反映 backbone-modifying 效应；命令仍需 `--fixed-size medium --fixed-limit-level join-best`，因为 BC 在 j3 下也不训练执行头）
- j1 BC 不跑 signal route——技术上等价于 M3 collection signal route + 随机 head 噪声

**BC batch 也是搜索维度**：v6 BC 用 batch=2048（默认），同样未探过 batch；本轮 batch ∈ {512, 1024, 2048}，按 sqrt-ish lr 缩放（batch=512 时 lr_policy=5e-4；batch=1024 时 lr_policy=7e-4；batch=2048 时 lr_policy=1e-3）。

| ID | oracle | freeze | batch | lr_policy | class_balance | focal | ema | seed | 评估口径 | 备注 |
|:---|:------:|:------:|------:|----------:|:--------------|------:|----:|-----:|:---------|:-----|
| **BC-0** | B | j1 | 2048 | 1e-3 | none | 0 | 0 | 42 | agent+fixed | anchor（v6 同口径）|
| **BC-1** | B | j1 | **512** | **5e-4** | none | 0 | 0 | 42 | agent+fixed | batch sweep / 512 |
| **BC-2** | B | j1 | **1024** | **7e-4** | none | 0 | 0 | 42 | agent+fixed | batch sweep / 1024 |
| **BC-3** | **C-0.7** | j1 | 2048 | 1e-3 | none | 0 | 0 | 42 | agent+fixed | 不同 oracle（quantile 0.7）；**v7expanded 上 filter 实证 no-op**：compute_oracle_c_threshold() 用 np.quantile(margins, 0.7) 算出来的 threshold 让所有 episode 通过（BC-0/BC-3 train sample count 都是 5542314 → 0 episode dropped），导致训练数据与 oracle B 完全相同（best_model.pt 4 位小数 identical）。本轮 BC oracle 维度实际未测。Fix path: (a) 修 compute_oracle_c_threshold margin 分布处理 (b) 显式传 --oracle-c-threshold X 跳过 quantile 计算 (c) 留作"已知未测"。详见 dev changelog "BC oracle dimension untested" 段。|
| **BC-4** | B | j1 | 2048 | 1e-3 | **inv_freq_0.75** | 0 | 0 | 42 | agent+fixed | + class balance |
| **BC-5** | B | j1 | 2048 | 1e-3 | inv_freq_0.75 | **2.0** | **0.999** | 42 | agent+fixed | 综合 method stack（class balance + focal + EMA）|
| **BC-6** | B | j1 | 2048 | 1e-3 | none | 0 | 0 | **7** | agent+fixed | seed 变种（BC 内方差检查）|
| **BC-7**（可选）| B | **j3** | 2048 | 5e-4 | inv_freq_0.75 | 0 | 0.999 | 42 | agent+fixed + signal+fixed | 全网络可训（高 overfit 风险）；仅当 BC-0..BC-6 中有 ≥ 1 个 agent val PnL > Hold baseline -8.09 时才跑 |
| **BC-CP1** | B | j1 | **512** | 5e-4 | **inv_freq_0.75** | 0 | 0 | 42 | agent+fixed | **cross-product 追加（仅 B1 backbone）**：BC-1 (small batch) + BC-4 (class_balance)，测试 batch effect + modifier effect 是否 additive |
| **BC-CP2** | B | j1 | **512** | 5e-4 | **inv_freq_0.75** | **2.0** | **0.999** | 42 | agent+fixed | cross-product：BC-1 + BC-5 method stack |
| **BC-CP3** | B | j1 | **512** | 5e-4 | none | 0 | 0 | **7** | agent+fixed | cross-product：BC-1 + BC-6 (seed=7) |

**为什么去掉 freeze=j2**：`model.py:567` 显示 `policy_logits = self.policy_head(backbone_out)`，与 fusion_proj/state_branch 没有梯度路径；`train_oracle_bc.py:430` BC loss 仅对 policy_logits 做 CE。所以 j2 解冻的 fusion_proj/state_branch 不会受到任何梯度更新，j2 ≡ j1，浪费 slot。j3 是 BC 唯一让 backbone 真正变化的选项（通过 policy_head→backbone_out→transformer→encoders 的反向链）。

**配置数 per M3**：核心 7 个（BC-0~BC-6），可选 1 个（BC-7）。**top 1-2 M3 总数 = 7-16 BC runs**。

### 5.3 评估流程

每个 BC 训练完后：

1. 显式导出 trained ONNX（`export_onnx.py --mode trained`）
2. **agent route + 固定执行头 eval**：
   ```
   --strategy agent --force-order-type limit \
   --fixed-size medium --fixed-limit-level join-best \
   --override-risk-score 1.0
   ```
   跑 val（不跑 train、test，test 留 Stage 3.5 后期 confirmation）→ 后处理 rolling 5 seg（读 per-window JSON）→ 写 full_policy 榜
3. **仅 freeze=j3（BC-7）**：再跑 signal+fixed eval（与 backbone 榜同口径，仅 `--strategy signal` 不同）→ 写 backbone 榜（per-M3 内归一化，再跨 M3 合榜）

### 5.4 Stage 2 决策与 Pre-Stage 3 Gate

- 全 BC 候选在 full_policy 榜按 score 排名
- top-3 BC 进候选清单
- **Pre-Stage 3 Gate**：top-1 BC agent val PnL > Hold baseline (-8.09) → 启动 Stage 3 IQL；否则跳过（IQL 在 v6 已显示完全塌缩，BC 都不达 Hold 时 IQL 几乎肯定也不行）

- **Mid-B1 early abort**：BC-0/1/2/3 × B1 跑完后，若 max(agent val PnL) < -50（远低于 Hold baseline），直接跳过 BC-4..7 × B1 + 全部 BC × B2 + 直接进 Pre-Stage 3 Gate fail 决议（节省 ~20h GPU on hopeless config space）

### 5.5 GPU 时长估计

| 子任务 | 单次时长 | 数量（max；× 3 M3 = B1, B2, A6）| 小计 |
|--------|---------:|-----:|-----:|
| transition 重采集（5 dv 串行）| ~2.5-3h/M3 | 3 | ~7.5-9h |
| validate_transitions G1/G3（带 `--ignore-reward-range`）| ~10min/M3 | 3 | ~30min |
| BC 训练 batch=2048（BC-0,3,4,5,6,7）| ~0.7-1.2h | 6 × 3 = 18 | ~13-22h |
| BC 训练 batch=512（BC-1）| ~1.5-2h | 1 × 3 = 3 | ~4.5-6h |
| BC 训练 batch=1024（BC-2）| ~1-1.5h | 1 × 3 = 3 | ~3-4.5h |
| trained ONNX 导出 | ~1min | 8 × 3 = 24 | ~25min |
| K2-C agent+fixed eval val | ~30-40min | 8 × 3 = 24 | ~9-12h |
| K2-C signal+fixed eval（仅 j3 BC，1-3 候选）| ~30-40min | 3 | ~1.5-2h |
| **Stage 2 总计** | | | **~38-50h**（含 A6 追加 +~9-10h）|

---

## 6. Stage 3 — M5 IQL 诊断（3 runs total；~3-5h GPU；独立 leaderboard）

**目标**：用极小代价测 IQL 在新 backbone + 几个高潜超参变体下能否不塌缩。失败也是有价值的"系统化否决"。IQL 进 full_policy 诊断榜的 IQL 子分类。

### 6.1 IQL 配置（3 runs total，仅在 top-1 backbone = m3_run_v7_M3-B1 上跑）

固定基础：`--epochs 50 --batch-size 2048 --lr-policy 1e-4 --lr-q 3e-4 --lr-v 3e-4 --device cuda --num-workers 8 --checkpoint-metric probe_gap`，复用 top-1 backbone (B1) 的 transition tick_stream `tick_stream_v7_m3_run_v7_M3-B1/`。

| ID | gamma | tau | beta | `--init-agent-checkpoint` | seed | 备注 |
|:---|------:|----:|-----:|:--------------------------|-----:|:-----|
| **IQL-0** | 0.9995 | 0.7 | 3.0 | none | 42 | anchor（v6 同口径）|
| **IQL-1** | **0.99** | 0.7 | **1.0** | **`checkpoints/<top-1 BC under M3-B1>/best_model.pt`**（待 Stage 2 排名后决定）| 42 | 短 horizon + AWR 锐化 + warm-start from BC（综合方法 stack）|
| **IQL-2** | 0.9995 | **0.5** | 3.0 | none | 42 | 不那么 pessimistic 的对照 |

**为什么只 3 runs**：v6 已确诊 IQL 在当前 reward 设计下结构性塌缩，多组超参验证过无效；本轮只测"新 backbone + warm-start 是否能救"+ "γ/τ 各放松 1 个"两个最有希望的方向，如果 3 个都塌缩就实证确认 IQL 这条路在 v6 数据上不可救（至少在不动 reward 的前提下）。

### 6.2 评估

每个 IQL 训练完后：

1. 看 `probe_gap` 末 5 epoch（>-0.5 = 未塌缩；<-0.9 = 塌缩，标 ledger `iql_collapsed=true`）
2. 导出 trained ONNX（含可失败补导）
3. **agent route + 固定执行头 eval val**（apples-to-apples 主榜口径，与 BC 同；IQL 实际训练 policy_head + size_head + order_type_head + limit_level_head + state_branch + fusion_proj，本榜统一用 fixed exec 是为了与 BC 直接可比的方向决策能力打分）：
   ```
   --strategy agent --force-order-type limit \
   --fixed-size medium --fixed-limit-level join-best \
   --override-risk-score 1.0
   ```
   后处理 rolling 5 seg → 写 full_policy 榜（IQL 子分类）
4. **额外记录 IQL native agent route**（不固定 size/order/limit，仅 `--strategy agent --override-risk-score 1.0`）：
   - 写到 ledger 的 `k2c_agent_native_val_pnl` 等 info-only 字段
   - 不进 ranking 计算
   - 用途：如果 IQL native 显著好于 fixed exec → 说明 IQL 训过的执行头确实加分，paper trading 时考虑切到 native；否则 fixed exec 当主候选

### 6.3 Stage 3 决策

- 取 top-3 IQL（多 M3 合榜）进候选清单
- 若 12 个 IQL 全部塌缩（probe_gap < -0.9）→ 实证确认"v6 数据规模 + 现 reward 设计下 IQL 不可救"，paper trading 候选完全跳过 IQL 路线

**2026-05-07 execution checkpoint（Stage 3 actual）**：
- IQL-0: fixed val +117.8847, native val +0.5295, last `probe_gap=-0.8775 / hold=0.9385`, `iql_collapsed=true`
- IQL-1 (BC-CP1 warm-start): fixed val +71.8358, native val -52.0237, last `probe_gap=-0.7895 / hold=0.8920`, `iql_collapsed=false`
- IQL-2 (`tau=0.5`): fixed val +127.0769, native val -51.6534, last `probe_gap=-0.9070 / hold=0.9530`, `iql_collapsed=true`
- Finding: warm-start can reduce Hold collapse, but current IQL path still does not produce a paper-ready candidate; native execution heads are consistently worse than fixed exec.
- Stage 3 canonical rerank keeps full_policy top-1 at `m5_bc_v7_m3_run_v7_M3-B2_BC-6`; collapsed-top1 guard did not block because top-1 is BC.

### 6.4 Stage 3.5 — Full-policy top-1 test confirmation（~1-2h GPU）

**目标**：补齐 full_policy 候选进 paper trading 的 test confirmation 环节。Stage 2 / Stage 3 默认仅跑 val（与 backbone 1A/1B 同口径），test 留到这里一次性确认。

**前提**：Stage 2 已完成且 Pre-Stage 3 Gate 通过（top-1 BC agent val PnL > Hold baseline -8.09）；如 gate 不过则跳过 Stage 3.5，full_policy 全部 shadow only。

**操作**：取 full_policy 榜 top-1 候选（按 §1 multi-metric score；可能是 BC 也可能是 IQL）：

```bash
# Use --group-by-config-key m3_id for canonical per-M3 subgroup ranking
# (per plan §1 line 68); --include-excluded omitted by default skips BC-3
# oracle C dups (commit 9f32272).
TOP1=$(python3 poly-arb-ai/training/candidate_ledger.py rank \
  --leaderboard full_policy --group-by-config-key m3_id \
  --top 1 --field run_id)
# show --field 支持 dotted path；ledger entry 结构：paths.onnx / config.seq_len
TOP1_ONNX=$(python3 poly-arb-ai/training/candidate_ledger.py show --run-id $TOP1 --field paths.onnx)
TOP1_SEQ=$(python3 poly-arb-ai/training/candidate_ledger.py show --run-id $TOP1 --field config.seq_len)

cargo run --release --manifest-path poly-arb-ai/rust/Cargo.toml -p agent -- evaluate \
  --model-path $TOP1_ONNX \
  --split-info poly-arb-ai/training/split/split_info.v6expanded.json \
  --split test \
  --strategy agent --force-order-type limit \
  --fixed-size medium --fixed-limit-level join-best --override-risk-score 1.0 \
  --output poly-arb-ai/training/eval/v7_final/${TOP1}__test \
  --seq-len $TOP1_SEQ --starting-cash 100.0

PYTHONPATH=poly-arb-ai python3 poly-arb-ai/scripts/eval_rolling_segments.py \
  --eval-dir poly-arb-ai/training/eval/v7_final/${TOP1}__test \
  --segment-size 5 \
  --output poly-arb-ai/training/eval/v7_final/${TOP1}__test_segments.json
```

**Pre-Paper-Trading Gate (Full-policy)**（与 backbone Pre-Paper Gate 同结构）：
- top-1 by val 的 **test K2-C agent+fixed PnL > 0** 且 **test rolling worst > -100**
- **通过** → full_policy top-1 进 paper trading 备选 2
- **不通过** → full_policy 全部候选仅 shadow only；backbone 候选不受此 gate 影响

**2026-05-07 execution checkpoint（Stage 3.5 actual）**：
- test target: canonical full_policy top-1 `m5_bc_v7_m3_run_v7_M3-B2_BC-6`
- test result: total PnL -11.0374, mean Sharpe 0.3115, win/loss windows 13/12
- rolling: median -0.3249, worst -31.7451, best +41.2805
- gate: **FAIL** because total PnL ≤ 0, despite rolling worst > -100
- decision: full_policy candidates remain shadow/diagnostic only; no fallback test is run under this plan because Stage 3.5 is top-1-only and test must not participate in candidate switching.

**为什么只跑 top-1 不跑 top-3**：full_policy 主要是诊断分支（v6 已显示 BC -251 / IQL -10 都极弱），test 资源应优先 backbone；如 top-1 通不过 gate，top-2/3 大概率也通不过；如确实想验证 top-2/3，可手动补跑（plan 之外的 ad-hoc）。

### 6.5 GPU 时长估计（含 Stage 3.5）

| 子任务 | 单次时长 | 数量 | 小计 |
|--------|---------:|-----:|-----:|
| IQL 训练（塌缩则提前停）| ~30-60min | 3 | ~1.5-3h |
| trained ONNX 导出（含可选补导）| ~2min | 3 | ~10min |
| K2-C agent+fixed eval val | ~30-40min | 3 | ~1.5-2h |
| Stage 3.5 test eval（top-1 only）| ~30-40min | 1 | ~0.5-1h |
| **Stage 3 + 3.5 总计** | | | **~4-7h** |

---

## 7. Stage 4 — 候选选拔与发布（双榜）

### 7.1 操作（本地文档收口）

Stage 4 只收口 M3M5 offline 结论：双榜出榜、gate 判定、产物索引、训练发现和 known limitations。**不进入 M6，不部署，不发单，不补跑实验**。

```bash
mkdir -p logs

PYTHONPATH=poly-arb-ai python3 poly-arb-ai/training/candidate_ledger.py \
  --ledger poly-arb-ai/training/candidates_ledger.json \
  rank --leaderboard backbone --top 10 \
  > logs/candidate_ranking_v7_backbone_top10.md

PYTHONPATH=poly-arb-ai python3 poly-arb-ai/training/candidate_ledger.py \
  --ledger poly-arb-ai/training/candidates_ledger.json \
  rank --leaderboard full_policy --group-by-config-key m3_id --top 10 \
  > logs/candidate_ranking_v7_fullpolicy_grouped_top10.md
```

`candidate_ledger.py rank` 当前没有 `--output` 参数；ranking 输出用 shell redirect。`logs/` 是 ignored scratch path，最终提交文档必须内嵌关键榜单和候选状态，不能只引用 ignored logs。

Full-policy 出榜必须使用 `--group-by-config-key m3_id`。Flat rank 会把 `IQL-0` 排到 top-1，但 Stage 3 canonical rerank / Stage 3.5 test target 均使用 per-`m3_id` grouped normalization，因此 Stage 4 收口必须沿用 grouped canonical 口径。

### 7.2 M3M5 offline-confirmed 候选清单

每个候选必须有自己的 test confirmation；不允许"主候选 test 失败 → 用备选 1 顶上"。Test 只用于接受/拒绝，不参与重新排序。

| 候选位 | 来源 | Gate 条件 | 实际选拔 |
|--------|------|----------|----|
| 主候选 | Backbone unique top-1 by val | 自身 test PnL > 0 且 test rolling worst > -100 | `m3_run_v7_M3-B1`（val +424.3953 / test +92.2782 / rolling worst -40.4436，PASS） |
| 备选 1 | Backbone unique top-2 by val | 自身 test PnL > 0 且 test rolling worst > -100 | `m3_run_v7_M3-B2`（val +415.7186 / test +137.8349 / rolling worst +5.3328，PASS） |
| reference | Backbone no-EMA baseline | 自身 test PnL > 0 且 test rolling worst > -100 | `m3_run_v7_M3-A6`（val +280.1133 / test +85.5283 / rolling worst -30.7744，PASS） |
| shadow/diagnostic | Full-policy grouped top-1 + 全部 BC/IQL | Stage 3.5 Full-policy Gate | `m5_bc_v7_m3_run_v7_M3-B2_BC-6` test -11.0374 → FAIL；full-policy 全部 shadow only |

`m3_run_v7_M3-B8` 是 B1 duplicate/no-op，不占 unique candidate slot。B2 test PnL 高于 B1，但不用于改写主候选排序。

### 7.3 dev-docs 同步

Stage 4 必须更新：

- `poly-arb-ai/model-train-docs/dev/M3M5系统化批次调参方案.md`：内嵌最终双榜 top 表、gate 结果、候选状态、产物索引、训练发现、known limitations。
- `poly-arb-ai/dev-docs/M3M5调参实验记录v7.md`：流程结束后的最终汇总报告，覆盖阶段目标、实验矩阵、最终双榜、候选冻结、失败路线、产物索引。
- `poly-arb-ai/dev-docs/依赖环境说明.md`：覆盖过期 Stage 1B/GPU 状态，记录 M3M5 Stage 4 收口状态、产物已同步本地、full_policy FAIL。

Stage 4 known limitations：
- BC-7 signal route eval 未跑：ledger 仅有 agent route metrics；作为 coverage limitation 记录，不阻塞收口。
- BC-3 explicit `--oracle-c-threshold` mini-sweep 未跑：oracle C quantile route 已确认 no-op duplicate；作为 oracle 维度未测记录，不补跑。

---

## 8. 显式不做的工作

| 项 | 决定 | 原因 |
|----|------|------|
| 改 model.py 架构 | 不做 | 三轮实验已穷尽架构维度（d_model/layers/nhead/dropout）；本次目标是"调参"|
| 改 dataloader.py（除新 flag 间接读 args.feature_noise）| 不做 | 跨市场回看 + 冷启动过滤 stable |
| 改 split 切分（split_info.v6expanded.json）| 不做 | 用户明确"在当前数据集和当前训练路径基础上"调参 |
| 改 reward.rs 设计 / 修改 collect-transitions 的 reward / latency / fee 参数 | 不做 | 用户选择"含训练方法调整"但不含"奖励/采集 protocol 重设计"|
| 每个 top backbone 重采集 transition | **要做** | 这是 BC 训练的技术必要（每个 collection ONNX 不同 → tick_stream 不同），不属于"采集 protocol 变化"。Stage 2 §5.1 强制 + validate G1/G3 gate |
| 重新计算 features parquet | 不做 | M2 features 不变 |
| 增加 v6 之外的新数据 | 不做 | 用 v6expanded 现有 5 套 |
| Walk-forward CV | 暂不做 | 等 Stage 4 双榜结果，仅当主榜 top-1 paper trading 真实表现差 + Stage 1C test confirmation 也差时再考虑 |
| Rust evaluate 多 ONNX 平均（让 ensemble 候选进 K2-C 主榜）| 暂不做 | M3 ensemble 仅 Python offline 指标；如集成显著好可触发独立立项 |

---

## 9. Critical Files

> 本地 dev 路径：`source://training/poly-arb-ai/...`（model-train 分支 worktree）
> GPU 服务器执行路径：`source://v2/poly-arb-ai/...`
> 修改 / 新增的代码必须 push 到 remote 后再 `git pull` 到 GPU 服务器执行

### 新增文件

| 路径 | 行数（估）| 阶段 |
|------|----------:|------|
| `poly-arb-ai/training/candidate_ledger.py`（含双 leaderboard schema）| ~120 | Stage 0 |
| `poly-arb-ai/scripts/eval_rolling_segments.py` | ~90 | Stage 0 |
| `poly-arb-ai/scripts/dataloader_sample_count_sanity.py` | ~50 | Stage 0 |
| `poly-arb-ai/scripts/run_one_m3.sh` | ~30 | Stage 0 |
| `poly-arb-ai/scripts/run_one_bc.sh` | ~30 | Stage 0 |
| `poly-arb-ai/scripts/run_one_iql.sh` | ~30 | Stage 0 |
| `poly-arb-ai/scripts/ensemble_inference.py`（仅 Python offline）| ~80 | Stage 0 |
| `poly-arb-ai/dev-docs/M3M5调参实验记录v7.md` | （流程结束后写）| Stage 4 |

### 修改文件

| 路径 | 改动 | 阶段 |
|------|------|------|
| `poly-arb-ai/training/train.py` | +5 flag + ModelEMA 类（~100 行；含 EMA-compile 兼容）| Stage 0 |
| `poly-arb-ai/training/loss.py` | +`focal_loss` 函数（~15 行）| Stage 0 |
| `poly-arb-ai/training/train_oracle_bc.py` | +4 flag + class_balance 分支（~60 行）| Stage 0 |
| `poly-arb-ai/training/train_iql.py` | +`--seed`（~10 行）+ `--init-agent-checkpoint` 既有 flag 的 docstring 补充 | Stage 0 |
| `poly-arb-ai/training/validate_transitions.py` | +`--ignore-reward-range` flag（~10 行）| Stage 0 |
| `poly-arb-ai/rust/agent/src/baseline_strategies.rs` | +`fixed_limit_level` 字段 + override 逻辑 + unit test（~20 行）| Stage 0 |
| `poly-arb-ai/rust/agent/src/main.rs` | +`--fixed-limit-level` CLI flag + parse 函数 + 注入 BaselineConfig（~20 行）| Stage 0 |
| `poly-arb-ai/dev-docs/依赖环境说明.md` | 流程结束后追加 | Stage 4 |

### 不动的文件

- `poly-arb-ai/training/model.py`、`dataloader.py`、`gen_m6_v1v4_split.py`
- `poly-arb-ai/rust/agent/src/{reward.rs,strategy.rs}`、`feature-engine`、`replay-engine`（除 baseline_strategies.rs / main.rs 已列）
- `poly-arb-ai/data-pipeline/`
- features parquet、split_info.v6expanded.json

---

## 10. Verification（端到端）

### Stage 0 验收

```bash
# Python flag 注册（M3 5 个 / BC 4 个 / IQL 1 个新增 + 复用 init-agent-checkpoint / validate 1 个）
python3 poly-arb-ai/training/train.py --help | grep -E "seed|ema-decay|feature-noise|focal-gamma|snapshot-epochs"
python3 poly-arb-ai/training/train_oracle_bc.py --help | grep -E "seed|ema-decay|class-balance|focal-gamma"
python3 poly-arb-ai/training/train_iql.py --help | grep -E "seed|init-agent-checkpoint"
python3 poly-arb-ai/training/validate_transitions.py --help | grep "ignore-reward-range"
cargo run --manifest-path poly-arb-ai/rust/Cargo.toml -p agent -- evaluate --help | grep "fixed-limit-level"

# 默认行为不变（M3-A0 anchor 1 epoch smoke；必须传全部 5 套 parquet）
PYTHONPATH=poly-arb-ai python3 poly-arb-ai/training/train.py \
  --parquet-paths \
    model/feature-engine/out/features_250ms_data-v1.parquet \
    model/feature-engine/out/features_250ms_data-v2.parquet \
    model/feature-engine/out/features_250ms_data-v3.parquet \
    model/feature-engine/out/features_250ms_data-v4.parquet \
    model/feature-engine/out/features_250ms_data-v5.parquet \
  --split-info poly-arb-ai/training/split/split_info.v6expanded.json \
  --output-dir /tmp/m3_smoke --epochs 1 --batch-size 128 --seq-len 240 \
  --device cuda --amp --num-workers 4

# Rust fixed-limit-level 生效（Rust unit test）
cargo test --release --manifest-path poly-arb-ai/rust/Cargo.toml -p agent fixed_limit_level_overrides

# EMA + compile + Focal γ=2 三 flag 合并 1-epoch smoke（plan §3.8 强制；§11 风险行兜底）
PYTHONPATH=poly-arb-ai python3 poly-arb-ai/training/train.py \
  --parquet-paths model/feature-engine/out/features_250ms_data-v1.parquet \
  --split-info poly-arb-ai/training/split/split_info.v6expanded.json \
  --output-dir /tmp/m3_smoke_ema_focal --epochs 1 --batch-size 4096 --seq-len 100 \
  --lr 5.6e-4 --warmup-epochs 2 --label-smoothing 0.05 --device cuda --amp --num-workers 4 \
  --compile --ema-decay 0.999 --focal-gamma 2.0 --seed 42
# 通过条件：1 epoch 不 crash + cls_loss 不 NaN + EMA 权重已更新（best_model.pt mtime > start time）

# BC oracle A 兼容性 1-epoch smoke（当前 BC 矩阵不含 A，仅未来扩展验证；不通过仅 dev-docs 标记）
PYTHONPATH=poly-arb-ai python3 poly-arb-ai/training/train_oracle_bc.py \
  --tick-stream-paths poly-arb-ai/rust/agent/out/tick_stream/data-v1_reward_minimal.parquet \
  --label-paths poly-arb-ai/data-pipeline/out/data-v1/labels.parquet \
  --split-info poly-arb-ai/training/split/split_info.v6expanded.json \
  --m3-checkpoint <existing M3 best_model.pt> --m3-stats <existing M3 feature_stats.npz> \
  --seq-len 100 --output-dir /tmp/bc_smoke_oracle_a --oracle-mode A \
  --epochs 1 --batch-size 2048 --device cuda --amp --num-workers 4
# 通过条件：1 epoch 不 crash 即记录通过

# rolling segment 后处理 smoke
PYTHONPATH=poly-arb-ai python3 poly-arb-ai/scripts/eval_rolling_segments.py \
  --eval-dir poly-arb-ai/training/eval/v6/m3_v6_collection_signal__val \
  --segment-size 5 \
  --output /tmp/v6_baseline_segments.json
python3 -c "
import json
r = json.load(open('/tmp/v6_baseline_segments.json'))
assert 'segments' in r and len(r['segments']) == 5
assert 'median_pnl' in r and 'worst_pnl' in r
print(f'rolling segments OK: median={r[\"median_pnl\"]:.2f} worst={r[\"worst_pnl\"]:.2f}')
"

# ledger 双 schema CRUD
python3 poly-arb-ai/training/candidate_ledger.py register --run-id smoke_bb --stage M3 --leaderboard backbone --config '{}'
python3 poly-arb-ai/training/candidate_ledger.py register --run-id smoke_fp --stage BC --leaderboard full_policy --config '{}'
python3 poly-arb-ai/training/candidate_ledger.py rank --leaderboard backbone --top 1
python3 poly-arb-ai/training/candidate_ledger.py rank --leaderboard full_policy --top 1
```

### 各 Stage 单 run 验收

每个 run 完成后：`python3 candidate_ledger.py show --run-id <run_id>` 期望 config + 指标 + score 完整。

### 整体 ledger 完整性验收

```bash
python3 -c "
import json
l = json.load(open('poly-arb-ai/training/candidates_ledger.json'))
backbone_count = sum(1 for r in l['runs'] if r['leaderboard'] == 'backbone')
fullpolicy_count = sum(1 for r in l['runs'] if r['leaderboard'] == 'full_policy')
print(f'backbone: {backbone_count}, full_policy: {fullpolicy_count}')
# 期望：backbone ≥ 14（5-7 1A + 9 1B；M3-A0 anchor 不进 ledger），full_policy ≥ 10（7-16 BC + 3 IQL）
"
```

---

## 11. 风险与回滚

| 风险 | 触发 | 早发现信号 | 回滚 |
|------|------|----------|------|
| 5 个 M3 新 flag 默认行为破坏 | 任何用 default 跑的旧脚本 | smoke 1 epoch：loss 不在 v6 ep1 合理范围；M3-A0 epoch 1：val_top10_ev / loss / auc 不在 v6 E01 量级 ±2 σ（**A0 epoch 1 sanity 即可 kill，不要求 30 epoch**）| smoke 回归 + bisect |
| EMA + torch.compile 兼容 bug | EMA 类直接 wrap compiled module | M3-B1~B4 train_loss NaN 或 EMA 权重不更新 | 启用 EMA 时强制 `--compile=False` |
| Focal loss 数值不稳 | γ=2 在 logit 极值时 grad 爆 | M3-B5 cls_loss 在 ep1 已 NaN | logit clip（`logits.clamp(-30, 30)`）或回退 γ=0 |
| Snapshot ckpt 与 patience 冲突 | early stop 在某 snapshot epoch 之前 | warnings 含 missing snapshot | 跳过缺失 snapshot + WARN，仅用已存在的 |
| BC class_balance 实现 bug | weights tensor shape 不匹配 | BC-4/5/6 ep1 报错 | 回退 `--class-balance none` |
| Oracle A 与 6-class policy_head 不兼容 | Stage 0 dev smoke 时报错 | smoke stack trace | dev-docs 标记不可用；本 plan 矩阵不受影响 |
| IQL warm-start 加载错维度 | BC ckpt 与 IQL state_dict 部分 key 不匹配 | IQL-1 加载报 KeyError | 既有 `--init-agent-checkpoint` 加载逻辑须支持 partial load + 跳过 mismatch；fallback `none` |
| Rust `--fixed-limit-level` patch 出 bug | 编译错或 override 逻辑未生效 | Stage 0 Rust unit test 失败 | 回退 PR；Stage 1 ranking 暂用 `--fixed-size medium` only |
| 5090 32G 装不下 batch=2048 | M3-A5 / BC anchor | OOM | 该 run 降 batch=1024 + lr 减半 |
| 小 batch + lr 不匹配发散 | M3-A2（256, 1.5e-4）| ep 1-2 NaN | 按 batch 减半→lr 减半重试，仍发散标 fail |
| 大 batch 过快 overfit | M3-A5（2048）| best_ep ≤ 2 | 加 patience 8 或减 lr 重试一次 |
| transition 重采集 OOM | rayon 默认 thread 数过高 | OOM kill | 降 `--threads 8` |
| autodl GPU 中断（v6 已踩过）| 实例 reboot | 后台进程被 kill | 所有 run `tee log`；M3 单 run 重跑代价 ≤ 3h；BC ≤ 1.2h；IQL ≤ 1h；evaluate 自带 cache |
| validate_transitions G2 误杀 | Stage 2 §5.1 漏带 `--ignore-reward-range` | exit 1 中断 Stage 2 | 命令必带 `--ignore-reward-range`；smoke 阶段验证 patch 生效 |
| BC agent route 未训练执行头污染 | BC agent eval 漏带 fixed-size + fixed-limit-level | full_policy 榜 score 反映随机执行头噪声而非 BC policy | §5.3 BC eval 命令必带 `--strategy agent --force-order-type limit --fixed-size medium --fixed-limit-level join-best --override-risk-score 1.0`；IQL 同 |
| ledger 写入异常 | 训练成功但 metrics attach 失败 | rank 时该 run 缺 metric | 重跑只 evaluate 不 train；`attach-metrics --force` |
| test confirmation 失败 | top-1 by val 在 test PnL < 0 或 worst seg ≤ -100 | confirmation 报告显示 | 既不切换 top-2（避免 test 泄漏）也不进 paper trading（避免用 paper 当 test 兜底）；所有候选仅 shadow；触发独立 split / regime 复盘 plan |
| Pre-1B Gate 不通过 | M3 batch sweep 全部 val PnL ≤ 0 且 val_top10_ev ≤ +0.10 | Stage 1A 出榜后 | 停止 Stage 1B-3，写 dev-docs，要求"v6 split 设计是否有问题"独立诊断 |
| Pre-Stage 2 Gate 不通过 | top-1 backbone val PnL ≤ 0 或 rolling worst ≤ -100 | Stage 1C 后 | 跳过 Stage 2/3/3.5；backbone 仍走 Pre-Paper Gate；paper trading 仅 backbone 候选（如其 Pre-Paper Gate 通过）|
| Pre-Stage 3 Gate 不通过 | top-1 BC agent val PnL ≤ -8.09 | Stage 2 后 | 跳过 Stage 3 IQL **和 Stage 3.5**；full_policy 全部仅 shadow（与 §6.4 前提一致）；paper trading 仅 backbone 候选 |
| Stage 3.5 Pre-Paper Gate 不通过 | full_policy top-1 test PnL ≤ 0 或 worst ≤ -100 | Stage 3.5 后 | full_policy 全部仅 shadow；不影响 backbone 候选 |

所有 train.py / train_oracle_bc.py / train_iql.py / Rust agent / validate_transitions.py 的新 flag 默认 = 旧行为，任何阶段都可以一行 flag 回滚到 v6 同口径。

---

## 12. 执行顺序（含 wall-clock）

```
[本地] Stage 0 dev (~7-9h)
  ├─ train.py +5 flag + ModelEMA + EMA-compile 兼容（~3h）
  ├─ loss.py + focal_loss（~30min）
  ├─ train_oracle_bc.py +4 flag + class_balance（~1.5h）
  ├─ train_iql.py +1 flag + warm-start docstring（~30min）
  ├─ validate_transitions.py +1 flag（~15min）
  ├─ Rust baseline_strategies + main.rs +fixed-limit-level（~1.5h）
  ├─ candidate_ledger（双 schema）+ 4 wrapper script + ensemble + rolling（~2-3h）
  └─ Smoke 验收（~1h）

[本地→GPU] git push + GPU pull（~5min）

[GPU] Stage 0 GPU (~30min)
  └─ holdout val 5 段诊断 + sample-count sanity

[GPU] Stage 1A (~11-12h 实测；A1 skip 后 9 datapoint)
  ├─ M3-A0 anchor epoch 1 sanity（~25 min，compromise C 提前 kill，不进 ledger）
  ├─ M3-A1 (batch=128) **skip**（user 决策 B+C：GPU util 18% underutilized）
  ├─ M3-A2..A7 (batch sweep) + M3-A8/A9/A10 (B+C 细粒度扩展) (~5h 总训练 + ~5h val K2-C eval)
  └─ 🚦 Pre-1B Gate 检查 → 通过则继续；不通过停

[GPU] Stage 1B (~10-15h；central batch ≥ 512 时 ~10h；batch=128 时 ~25-30h)
  ├─ M3-B0..B8 共 9 个 train（central config 上方法 sweep；M3-B8 K2-C 仅 best ckpt）
  ├─ K2-C signal+fixed eval val（rolling 5 seg 零成本后处理）
  ├─ M3-B-ens / M3-B8-ens Python offline 指标（不进 backbone 榜）
  └─ ledger rank Backbone 榜出榜

[GPU] Stage 1C (~1-2h)
  ├─ Backbone 榜 top-3 一次 test K2-C signal+fixed eval（confirmation only）
  ├─ 🚦 Pre-Stage 2 Gate 检查 → 通过则继续；不通过跳过 M5
  └─ 🚦 Pre-Paper-Trading Gate (Backbone) 检查 → top-1 by val 的 test 必须 PnL>0 + worst seg>-100；不通过 → no-go (shadow only)

[GPU] Stage 2 (~25-33h；如 Pre-Stage 2 Gate 不过则 0h)
  ├─ top 1-2 M3 各采集 5 dv tick_stream + validate_transitions --ignore-reward-range（~5-6h + 20min）
  ├─ 7-16 BC 训练 + agent+fixed route eval val
  ├─ j3 BC（仅 BC-7 可选）补 signal+fixed eval（~1-1.5h）
  ├─ ledger rank Full-policy 榜（BC 部分）
  └─ 🚦 Pre-Stage 3 Gate 检查 → 通过则继续

[GPU] Stage 3 (~3-5h；如 Pre-Stage 3 Gate 不过则 0h)
  └─ 3 IQL 训练（仅 top-1 M3）+ agent+fixed route eval + 写 Full-policy 榜 IQL 子分类

[GPU] Stage 3.5 (~1-2h；仅当 Pre-Stage 3 Gate 通过 OR Stage 2 BC 已有 val > Hold 候选)
  ├─ Full-policy 榜 top-1 单独 test K2-C agent+fixed eval
  ├─ rolling segment 后处理
  └─ 🚦 Pre-Paper-Trading Gate (Full-policy) 检查 → 通过则 full_policy top-1 进备选 2；不通过 → 全部 shadow

[本地] Stage 4 (~4h)
  ├─ ledger rank 双榜输出到 ignored logs/，并把关键榜单内嵌进提交文档（~30min）
  ├─ 写 dev-docs/M3M5调参实验记录v7.md（~2-3h）
  ├─ 更新 model-train-docs/dev changelog + 依赖环境说明.md（~1h）
  └─ M3M5 offline 候选清单：Backbone unique B1/B2；A6 reference；Full-policy 全 shadow/diagnostic
```

**总计**（与 §2 总成本估算完全一致）：

- **GPU pessimistic-A（所有 gate 全过 + central batch ≥ 512）**：~66-77h
- **GPU pessimistic-B（central batch=128，1B 训练翻倍）**：~81-97h
- **GPU mid（Pre-Stage 2 Gate 不过）**：~22-32h
- **GPU optimistic（Pre-1B Gate 不过）**：~14-19h
- **本地 dev + 文档**：~12-15h
- **日历周期**：约 1-4 个连续日历天（optimistic 1 天 / pessimistic-B 4 天）

---

## 13. 与 v6expanded baseline 的对比

| 维度 | v6expanded | 本计划 |
|------|-----------|--------|
| 训练入口 flag 数 | 17 | 17 + 5（M3）+ 4（BC）+ 1（IQL 新增 seed）+ 1（validate `--ignore-reward-range`）+ 1（Rust `--fixed-limit-level`）= 29 |
| M3 训练运行 | 1（batch=128 单点）| 14-16（5-7 pilot + 9 sweep + 1 anchor）；实际 1A 跑 9 batch 档：batch ∈ {256,512,1024,2048,3072,4096,5120,6144,8192}（A1=128 skip，user 决策 B+C）|
| M5 BC 训练运行 | 1（batch=2048 单点）| 7-16（仅 top 1-2 M3，7-8 each）；batch ∈ {512,1024,2048} 3 档 |
| M5 IQL 训练运行 | 1（batch=2048 单点）| 3（仅 top-1 M3）；γ/τ/β/warm-start 多变体 |
| ledger 候选数 | 5 主动比较 | ~24-29（backbone ≥ 14 + full_policy 10-13）|
| 排名机制 | 主观判断 | Multi-metric 加权 + ledger 持久化 + 双 leaderboard（backbone + full_policy）|
| Test 在 ranking 中权重 | n/a | **0%**（Stage 1C / Stage 3.5 各一次性 confirmation，不进排序）|
| 执行头处理（backbone）| 接受随机 | Rust `--fixed-limit-level` + backbone 榜评估必须 `--fixed-size medium --fixed-limit-level join-best --force-order-type limit` |
| 执行头处理（full-policy）| 接受随机 | agent route 也固定执行头（BC loss 仅 policy_logits CE，size/order/limit/risk 头无监督；IQL 训过这些头但主榜 fixed exec 与 BC apples-to-apples，native 仅 info）|
| BC signal route ranking | 主指标 | freeze=j1 不跑 signal（无意义）；仅 j3（BC-7 可选）跑 signal+fixed 辅助 |
| IQL ranking | 与 BC/M3 混 | 同 full_policy 榜的 IQL 子分类，与 BC agent 同 fixed exec 口径 |
| Stage gates | 无 | 5 个 hard gates（Pre-1B、Pre-Stage 2、Pre-Stage 3、Backbone Pre-Paper、Full-policy Pre-Paper）|
| test 失败处理 | n/a | no-go：仅 shadow 诊断 + 触发 split/regime 复盘 |
| validate_transitions | 默认 G2 hard fail | `--ignore-reward-range` flag，G2 SKIP / G1+G3 hard gate |
| Full-policy test confirmation | n/a | Stage 3.5 单独 step：top-1 跑 test agent+fixed eval；通过 Pre-Paper Gate 才进备选 2 |
| GPU 总时长 | ~24h | ~14-97h（4 档：optimistic 14-19h / mid 22-32h / pess-A 66-77h / pess-B 81-97h）|
