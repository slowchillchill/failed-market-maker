# Polymarket BTC UP/DOWN 5MIN AI Trading Agent — PRD

> 核心原则：**先把系统做对，再把模型做强。**

---

## 1. 目标

训练一个完整交易 agent，在 Polymarket BTC UP/DOWN 5MIN 市场上，每个时间步做出：交易方向、仓位大小、下单方式（market/limit）、限价档位、持有/减仓/平仓/反手 的完整决策。

约束条件：

- 结算按 Chainlink BTC/USD（`>=` 判 Up，非对称结构）
- 手续费按 2026-03-30 新版 `crypto_fees`
- 成交按 Polymarket 真实盘口逐档模拟
- 训练和推理必须注入真实网络延迟
- 风控必须有系统硬约束，不能完全依赖模型

---

## 2. 数据源

| 数据源                                                                          | 角色                                                              | 延迟                   |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ---------------------- |
| Polymarket btc-updown-5m orderbook                                              | 主交易场所：盘口、成交模拟、执行价格                              | 20ms                                        |
| Chainlink BTC/USD                                                               | **唯一结算标签** + 低频参考特征                                   | 20ms（统一使用 Polymarket 转发，约 1Hz）   |
| Binance BTCUSDT aggtrades                                                       | 高频价格、成交方向                                                | 105ms                                       |
| Binance BTCUSDT orderbook                                                       | 深度结构、流动性                                                  | 105ms                                       |
| BLB 技术指标(通过binance btcusdt orderbook与aggtrades 构建，由模拟系统实时计算) | bps / levelCount / barrierUsdt（判断价格能否回归 P2B 的关键特征） | binance延迟 + 计算耗时                      |

### Chainlink 双重角色

- **标签口径**：仅使用 market 结束后的结算结果
- **特征口径**：仅使用决策时刻前因果可见的更新值 + staleness
- **统一实现**：使用 `Polymarket` 转发的 `Chainlink BTC/USD`，按 `20ms` 可见延迟建模，原始更新频率约 `1Hz`

两者严格分离，进入模型前统一抽象为 `Chainlink reference signal`。

### BLB 指标说明

- **bps**：`(current_price - P2B) / P2B × 10000`，价格趋势强度
- **levelCount**：midpoint 到 P2B 的盘口档位数（有符号），阻力深度
- **barrierUsdt**：上述档位的美元总量（有符号），流动性壁垒

注意：BLB 的 P2B 基于 Binance 价格，结算 P2B 来自 Chainlink，存在微小差异，但作为预测特征合理。

---

## 3. 市场规则

- 二元结果市场（Up/Down），CLOB 订单簿撮合
- 最小价格跳动 `0.01`，最小下单量 `5`
- 结算：`resolution_price >= price_to_beat` → Up 赢，否则 Down 赢

### 手续费（2026-03-30 新版）

```
fee = C × 0.072 × p² × (1 - p)
```

- 买单以份额收取，卖单以 USDC 收取
- Maker fee = 0，Maker rebate = taker fee × 20%（第一版即纳入）
- 精度：四舍五入到小数点后 4 位，最小 0.0001 USDC
- 峰值有效费率 1.80%（p=0.50 附近），100 份 @p=0.50 fee = $0.90

---

## 4. 部署架构与延迟

- **核心服务器**：AWS 爱尔兰（Polymarket 20ms 往返）
- **中继服务器**：AWS 东京 → VPC Peering → 爱尔兰（Binance 105ms）
- **Chainlink 链路**：统一使用 `Polymarket` 转发到核心服务器，按 `20ms` 可见延迟建模，原始更新频率约 `1Hz`

### 执行时间线

```
t_decision → (+20ms) → t_exchange_arrival → (+20ms) → t_local_ack
```

- 撮合用 `t_exchange_arrival` 时刻的订单簿
- 本地状态在 `t_local_ack` 才更新

### 冷启动

每次会话的第一个 5 分钟 market 作为冷启动周期，不允许交易。

---

## 5. 模型架构

**多分支 TCN + 小型因果 Transformer 混合骨干**

### 编码层（4 个分支）

| 分支        | 编码器 | 主要特征                                             | Phase 1 |
| ----------- | ------ | ---------------------------------------------------- | ------- |
| Polymarket  | TCN    | Up/Down 深度、点差、盘口失衡、成交方向               | ✅ |
| Binance     | TCN    | 深度、market_drift（相对 market 开盘价的累计漂移）、成交方向失衡、波动、bps、levelCount、barrierUsdt | ✅ |
| Chainlink   | MLP    | 可见值、与P2B偏离、短时变化、staleness               | ✅ |
| Agent State | MLP    | 持仓、浮盈亏、净值、剩余时间                         | Phase 2（Phase 1 的 feature-engine 以 order_size=0 运行，agent state 全为常数，不入训练特征） |

### 融合层

小型因果 Transformer：2-4 层，dim 64-128，heads 2-4，序列 60-240 步

### 输出头

```
state_embedding → SignalHead    （辅助监督/诊断，不直接驱动交易）
               → PolicyHead    （hold/open_up/open_down/reduce/close/flip）
               → SizeHead      （small/medium/large 目标仓位档位）
               → OrderTypeHead （market/limit）
               → LimitPriceLevelHead（join_best/improve_1~2tick/passive_1~2tick）
               → RiskHead      （软风险约束）
```

### 执行流水线

```
PolicyHead + SizeHead → candidate_target_position
    → RiskHead 施加软约束
    → HardRiskGuard 施加硬约束 → final_target_position
    → OrderTypeHead + LimitPriceLevelHead → 具体订单
```

限价单若在下一决策步前未完全成交，先撤后重评估。

---

## 6. 风控

### 模型软决策（PolicyHead）

动态输出 hold / reduce / close / flip

### 系统硬保护（HardRiskGuard）

- 单市场最大仓位 / 最大亏损
- 日内最大回撤 / 连续亏损熔断
- 到期前禁止新开仓 / 强制平仓

**止盈止损可部分由模型学习，但永远不能没有系统级硬保护。**

---

## 7. 会计与奖励

### 唯一 NAV 口径

```
NAV_after_fee(t) = cash（含 fee/rebate）+ inventory_mark_to_market
terminal_settlement(T) = 按 Chainlink 结算后的最终账户价值
```

- slippage 体现在 fill price 中，不重复扣减
- fee/rebate 体现在 NAV_after_fee 中，不额外扣减

### 单步奖励

> 详细设计见 `dev-docs/奖励函数思路.md`。

```
# 不对称 ΔNAV（区分主动纠错 vs 被动承受亏损）
if ΔNAV(t) >= 0:         reward_nav = ΔNAV(t)
elif has_trade_this_tick: reward_nav = ΔNAV(t)           # 主动纠错（止损/减仓）：不放大
else:                     reward_nav = α_loss × ΔNAV(t)  # 被动承受（持仓缩水）：放大

reward_t = reward_nav - turnover_penalty - drawdown_penalty - idle_penalty
```

- 无 inventory penalty（双侧持仓是合法套利：`price_up + price_down < 1` 时持有到结算可盈利）
- idle_penalty：空仓且非冷启动时每 tick 收取固定惩罚（惩罚躺平不交易）
- drawdown_penalty：仅对增量回撤（创新低）收费，不对存量回撤重复收费

---

## 8. 训练路线

| 阶段                       | 目标              | 方法                                                                                      |
| -------------------------- | ----------------- | ----------------------------------------------------------------------------------------- |
| **Phase 1：监督预训练**    | 学会发现交易 edge | 训练三路市场编码器（Polymarket/Binance/Chainlink）+ SignalHead，监督目标：结算方向分类 `y_cls` + 标准化动作 EV 回归 `y_ev_up/down`；Agent State 分支因 feature-engine order_size=0 全为常数，Phase 1 不纳入 |
| **Phase 2：离线策略学习（已完成）**  | 诊断并收口离线策略路线 | 历史执行路径为 Oracle-guided BC → Hybrid BC+IQL → Execution/MarketEdge；最终冻结 `frozen signal head + signal_threshold=0.58 + force_order_type=limit + 默认 size` 为 M6 默认候选，完整可交易 final policy 尚未解锁 |
| **Phase 3：Paper Trading** | 实时验证          | 验证能否复现离线表现、延迟影响、事件密度稳定性                                            |

**Phase 2 修订说明（2026-04-09；历史执行路径，现已完成）**：
M5 执行期间发现纯 offline IQL 在本问题上结构性不适用，原因是 γ=0.9995 + 1200 tick 的 settlement 延迟（有效衰减 0.549）+ 采集里 Hold 动作占 58% 的三重叠加，使 AWR 权重退化为近似均匀、policy 必然塌缩到众数 Hold。Oracle 上限 +94%/笔、M3 方向精度 54.1% 两项独立诊断证实**数据本身有强信号**，但早期采集阶段把 `reward_clip` 默认设为 `±1.0`，将 ±20 USDC 的 settlement 信号斩断，是激发塌缩的"smoking gun"。当时实际执行路径为：(1) 先用 Oracle-guided 行为克隆诊断 PolicyHead 架构可学性；(2) 再用 `Hybrid BC→IQL` 验证是否能解锁完整可交易 policy；(3) 在 `K1_a/K1_b` 双失败后，转入 `Execution/MarketEdge` 收口。当前阶段结论以下方 2026-04-15 收口结果为准，不再把 `Hybrid BC→IQL` 视为 M6 的进行中主线。详见 `dev-docs/M5待解决问题.md` 与 `dev-docs/M5开发日志.md` 的 "Phase 11 迭代记录" 章节。

**Phase 2 阶段结论（2026-04-15）**：
- `J1_B_fromM3` 已命中强通过，说明当前 `backbone + policy head` 可以学出方向语义，结论记为 `H1`
- `K1_a/K1_b` 双失败，说明在当前 offline 数据与奖励口径下，`Hybrid BC→IQL` 仍未解锁可交易 policy
- `K2` 的 `Execution/MarketEdge` 分支已确认当前可部署候选：`frozen signal head + signal_threshold=0.58 + force_order_type=limit + 默认 size`
- held-out `test` 确认结果为 `total_pnl=+66.0951`（对照 `hold=-26.1318`），但 `val` 8 个窗口单独为 `-95.1558`，M6 需要重点盯住这类 regime shift
- 因此 M5 的实际交付不是“纯 RL 已收敛出最终 policy”，而是“已经确认 M6 默认候选应以 frozen signal head + 固定 execution config 为主”

Phase 1 验证指标：
- **主判据**：top_decile_mean_ev_up > 0（P_up 前 10% 的条件均值实际 y_ev_up 为正）、ev_up_sign_acc > 0.52（正确识别"应买/不应买"的比例）
- **理智检查**：AUC > 0.52、Brier < 0.25、ECE < 0.05、ev_rank_corr > 0.03
- y_ev 标签已含手续费（taker fee 峰值 1.80% @p=0.50），y_ev_up > 0 直接意味着扣费后正收益

数据计划：1 天验证流程 → 全量训练（历史已验证监督基线为 `data-v1+v2+v3`，`2.6M` 帧；当前工程数据线已扩展到 `V1~V4`）→ 后续按周滚动扩展；新增版本必须沿用当前目录、索引和切分规范，详见 `数据集规范.md`

---

## 9. 评估标准

扣费后净收益 · Sharpe · 最大回撤 · 胜率 · 换手率 · 平均持仓时长 · 单市场容量

所有验证使用严格时间前推，不随机打散。

---

## 10. 技术栈

- **训练**：Python（PyTorch），Phase 1 全量训练需云端 GPU（NVIDIA RTX 3080+ / A100）；实测 RTX 5090 + batch=2048 + AMP + torch.compile 约 61s/epoch（含 eval），30 epoch 约 30 分钟
- **推理**：Rust + ONNX（目标数毫秒级 CPU 推理）
- **Rust 模块**：replay-engine / feature-engine / onnx-inference / agent（含 arbiter、risk_guard、execution、evaluation、strategy）
- **训练数据**：历史已验证监督基线为 feature-engine 产出的 parquet（`data-v1+v2+v3` 共 `2,609,247` 帧，`FEATURE_COLS=65`）；当前工程数据线已扩展到 `V1~V4`，新增数据集版本接入时必须保持全局时间前推切分，并遵循 `数据集规范.md`

---

## 11. 数据管理

- **原始层**：canonical raw 保留 `ndjson/csv`，用于审计、回放、订单簿重建；同时允许在 `model/parquet-data/<dataset_version>/` 下维护与 raw 同构的 **typed parquet 原始镜像层**，供 `data-pipeline --raw-root`、`replay-engine`、`feature-engine` 直接消费
- **M0 索引/验证层**：`manifest.parquet + labels.parquet + validation.parquet + tables/*.parquet`
- **M2 特征层**：按 market 对齐后的特征帧 parquet；当前 canonical schema 为 `86` 列，`Phase 1` 监督训练正式输入为 `FEATURE_COLS=65`，`M5/M6` observation 输入为 `76` 维
- **RL 样本层**：`obs/action/reward/next_obs/done/market_id -> parquet`；如需离线诊断，当前默认输入应为 `tick_stream/*_reward_minimal.parquet`，不再把 clipped reward 视为默认口径
- **当前数据目录**：新数据集版本的 raw 目录统一使用 `model/data-v*/<window_id>/...`；若生成 mirror，则使用 `model/parquet-data/<dataset_version>/<window_id>/...`。旧文档中的 `model/data-v1/<date>/<window_id>/...` 示例已废弃
- **下游消费口径**：`manifest.parquet` 不单独提供完整标签；`p2b / resolution_price / label_up` 位于 `labels.parquet`，回放、特征和训练相关流程必须联合消费 `manifest + labels`
- **切分单元**：5 分钟 market，数据缺失 `>15s` 则丢弃。窗口目录路径中两个时间戳分别是**首个和最后一个 market 的开始时刻**（非结束时刻），market 计数公式为 `(last_start - first_start) / 300 + 1`
- **上下文窗口**可跨 market 拼接历史，但不能穿越未来
- **多数据集联合训练**必须先全局合并 parquet，再统一做严格时间前推切分；禁止“各 parquet 各自切分后再拼接”
- **时间粒度**：第一版聚合为 `250ms` 或 `500ms` 特征帧
- **回看窗口**：`30-60s`
- **当前 `data-v4` 状态**：`typed parquet 原始镜像层` 已完成 `verify_parquet_raw_coverage.py` 校验，结果为 `3016 -> 3016`、`missing/extra/row_mismatch = 0`；这证明镜像层文件覆盖与逐文件行数一致，但不等同于全链路全量等价
- **新增版本接入**：`data-v4` 及后续版本的目录结构、mirror 规则、校验流程、主键口径、M5 后注意事项统一见 `数据集规范.md`
