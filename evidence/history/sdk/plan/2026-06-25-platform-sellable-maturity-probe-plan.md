# platform-sellable maturity probe 权威测试计划

> 状态：current active authoritative plan，2026-06-25 JST。
>
> 对应 active changelog：
> `poly-arb-ai/sdk-live-trade-docs/changelog/2026-06-25-platform-sellable-maturity-probe-plan.md`。
>
> 本文件 supersede 归档计划
> `poly-arb-ai/sdk-live-trade-docs/plan/2nd-moneyrun-bugs-fix.md`。
> 旧 plan/changelog 只作为历史真实资金 run、Phase 9/10 blocker 与 platform-sellable maturity 背景证据。
>
> 本文件记录需求目标、测试设计和当前执行 cursor。heartbeat + cumulative partial-fill + under-min cleanup、
> clean-accept artifact normalization、artifact-smoke + streaming persistence、BUY submit evidence/retry
> 以及 cleanup-audit-only 修复均已完成本地实现、review、commit/push、fresh build、binary-only deploy
> 和 production `--no-live-funds` gate。当前已部署运行的 0B 代码 commit 是
> `bb21d140cb373bd9b44f9c265e9314b4116da07f`；随后用户批准并已执行 one-sample artifact smoke
> `platform-sellable-maturity-artifact-smoke-20260626T132728Z` 和正式 30 有效样本真实资金 probe
> `platform-sellable-maturity-live-20260626T133250Z`。
>
> 最新正式 30 样本 run 已达到 `valid_sample_count=30`，JSONL/stream/summary 产物可复核，但整体 gate
> 仍为 `FailClosed`。唯一 fail-closed reason 是 final CSV writer 对
> `platform_sellable_maturity_samples.csv` 报错：`CSV error: found record with 50 fields, but the previous
> record has 51 fields`。因此不能标记为 passed。
>
> post-run `platform-open-orders-check-post-30probe-20260626T144528Z` 证明平台 open orders 为 `0`；
> post-live account snapshot `post-live-account-snapshot-20260626T145200Z` 显示 `open_order_count=0`，
> 但 Data API positions 为 `2`、`data_total_value_usdc=5`，reconciliation `allows_new_orders=false`。
> 因此当前不得继续真实资金 probe；下一步必须先 root-cause / fix sample CSV writer schema 对齐。
>
> 历史 run `platform-sellable-maturity-live-20260626T033334Z` 曾 fail-closed 于
> `sample-0012:buy submit was not accepted`，已由当前 BUY submit evidence/retry 修复覆盖。该修复会把
> `buy_submit_attempts` 写入 gate report / fail-closed trace，并且只对“无 platform order id、无 trade id、
> 无 transaction hash，且错误为 exact `MARKET_NOT_READY`、HTTP `425`、HTTP `429` 或 HTTP `500` exact
> `could not insert order`”的 BUY submit reject 做有限 retry；BUY `not enough balance / allowance`、永久参数/
> 认证错误、restricted mode / post-only / cancel-only / trading disabled、带落单证据的 ambiguous reject、
> 空/`UNKNOWN` 无 transient evidence 和普通 timeout / ambiguous `SdkError` 都不 retry，直接 fail closed
> with evidence。
> 扩大 wallet/model/market scope、SDK fallback、raw REST/manual signing 或 shadow implementation 仍不授权。
>
> 当前有效样本计数：最新正式真实资金 run
> `platform-sellable-maturity-live-20260626T133250Z` 已在 `platform_sellable_maturity_samples.jsonl`、
> `platform_sellable_maturity_samples.stream.jsonl` 和 `platform_sellable_maturity_summary.json` 中写出
> `30` 个 valid samples；但因 CSV final writer validation error，正式 gate 未通过。
>
> 2026-06-26 JST cleanup-audit-only 修复方案：本 probe 的核心目标是测量
> `BUY fill ledger apply -> first same-asset SELL clean accepted` 的时间。第一次同 asset SELL
> `clean_sell_accepted=true` 即为该样本 maturity 成功终点；SELL 后续是否成交、best-effort cancel
> 是否成功、cancel 是否返回 `matched orders can't be canceled` / `SdkRejected` / `SdkError`、以及
> optional open-order audit 是否为 `0`，全部只作为 cleanup audit / manual review evidence，不得把已
> clean accepted 的样本或整轮 run 改成 fail-closed。pre-probe 同 asset open SELL / platform balance
> baseline gate、SDK fallback 禁令、BUY partial cleanup 的 venue-dust 规则和真实资金前置 gate 不变。

## 0C. 2026-06-26 formal 30-sample live probe result

用户批准执行正式 `30` 有效样本真实资金 probe 后，本轮已执行完毕，但整体 gate **未通过**。

Formal live probe：

- command target run id：`platform-sellable-maturity-live-20260626T133250Z`
- program run id：`platform-sellable-maturity-1782480772434`
- 远端 run dir：
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/platform-sellable-maturity/platform-sellable-maturity-live-20260626T133250Z/`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260626T133250Z/`
- CLI summary：`status=FailClosed`、`valid_samples=30`、SDK post/cancel `672/32`。
- Gate report：`status=fail_closed`、`required_valid_samples=30`、`valid_sample_count=30`、
  `sdk_post_attempt_count=672`、`sdk_cancel_attempt_count=32`、`heartbeat_attempt_count=77`、
  `under_min_market_cleanup_attempt_count=0`。
- 唯一 fail-closed reason：
  `artifact_writer_validation_error:write .../platform_sellable_maturity_samples.csv: CSV error: found record with 50 fields, but the previous record has 51 fields`。
- 本轮不是 JSONL/stream 未写出：`platform_sellable_maturity_samples.jsonl` 与
  `platform_sellable_maturity_samples.stream.jsonl` 均为 `32` 行；`valid=30`、`invalid=2`。
- Invalid samples：`sample-0017` 为 `fill_size=4.999165` 且
  `cleanup_terminal_reason=venue_dust_below_threshold`；`sample-0019` 为 `fill_size=0`，两者
  `exclusion_reason=buy_fill_size_below_configured_probe_size`，均不计入 30 个有效样本。
- Per-sample cleanup audit 里，valid `sample-0003` 和 `sample-0023` 的
  `post_cancel_open_orders_count=1`；这只代表样本内 cleanup audit evidence，不等同于运行后最终平台
  open-order 状态。独立 post-run open-order gate 见下文，结果为 `open_order_count=0`。
- Summary metrics：`clean_accept_ms` count `30`、mean `1989.1667`、median `1939`、p75 `2510`、
  p90 `2676`、p95 `3357`、min `851`、max `3426`；`first_reject_ms` count `30`、mean
  `85.4`、median `80`、p75 `96`、p90 `107`、p95 `108`、min `71`、max `122`。
- Artifact sha256：
  - gate report：
    `d2a9427f0cf10b9649224c172d16838ea793f6bb8bb18109402e5877daff40a9`
  - fail trace：
    `e74fd13533679dd70b28b1e53df833bb8ded557ba90706ed9c6bfc0a0b0a7f55`
  - summary：
    `f697182c4537b14b4de871995d86257df6ca8bdf6d1c506624939b73d44f5acf`
  - samples JSONL：
    `9f581d1e0a1951af413f987c3e2a9caf03cf6227f5367f08ad1868a381060375`
  - probes JSONL：
    `54542f5a1182f8deffde3b925194a156919f2cc75fdacb0833a1c48aa9c1aed4`
  - bundle manifest：
    `fb8d3c1c4aa44992b7a7fb8701835ec7336f57535a6084b3c15a6501c96cc45a`

Pre/post open-order safety：

- pre-run open-order check `platform-open-orders-check-pre-30probe-20260626T133234Z` 已拉回，
  status `passed`、`open_order_count=0`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`。
  report sha256
  `c9d6fc5ffc323475e93eb2e24c873ec1224c7986764279cf64d1432ee4d2a8a8`，bundle manifest sha256
  `69d1122826c9d03a1a035fad97c46fc5b7540e3c9f9d87a0fdf7ea033e610163`。
- post-run open-order check `platform-open-orders-check-post-30probe-20260626T144528Z` 已拉回，
  status `passed`、`open_order_count=0`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`。
  report sha256
  `a5a8103ef751226041082d8d1e4408e2239b82c7689802018d62ee554f695f49`，bundle manifest sha256
  `7e53c66ae78918e59c49ddecefa42c253cf0b065ab0be294db8cc7f38213ee89`。

Post-live account snapshot：

- run id：`post-live-account-snapshot-20260626T145200Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/post-live-account-snapshot-20260626T145200Z/`
- `remote-dry-run` 写出 account/open-order/position/reconciliation artifacts，`fail_closed=true`，
  reason `clob_trades_query_failed:sdk_internal`。
- Snapshot：`open_order_count=0`，但 `data_position_count=2`、`data_total_value_usdc=5`。
  DOWN asset
  `40583622375196072489292938114999321362619885368738391817601948363698100270887` size `5`
  value `0.025`；UP asset
  `89970116419305287743685609967558456551325862000197769271435214920374609038052` size `5`
  value `4.975`。
- Reconciliation：`allows_new_orders=false`、`open_order_safe=true`、
  `position_value_safe=false`、`current_exposure_safe=false`、`trade_history_unavailable=true`、
  `audit_complete=false`；reasons 为 `data_position_up_mismatch`、`data_position_down_mismatch`、
  `trade_history_unavailable_blocks_new_orders`、`audit_incomplete`。
- sha256：`account_snapshot.json`
  `b885746c47c5ed1a1baf6c00ab1f5d77fe3a98989e0ff36d2299873e835198eb`；
  `open_order_snapshot.json`
  `ac1166c5ae8e447369bfed090f2071a3eb8982f467cda62894e6677a11bb5dfb`；
  `position_value_snapshot.json`
  `b9748c18c1a42af4c79cf5e377762cce86ebae53799d211bac7358bceda5104f`；
  `reconciliation_report.json`
  `b8427657ae369811e8575f1e6479f469dd525b7c510137b83785dd4a1702fd79`；
  bundle manifest
  `ff1281ab72b9df886aa14740be5a364f580f1a662342a1df5445457dff089b84`。

当前边界：

- 30 个有效样本数据已在 JSONL/stream/summary 中可复核，但正式 gate 仍因 CSV writer validation
  fail-closed，不能标记为 passed。
- 运行后 open orders 为 `0`；但 post-live account snapshot 仍显示 Data API positions，且
  reconciliation `allows_new_orders=false`。
- 不得继续真实资金 probe；下一步必须先 root-cause / fix `platform_sellable_maturity_samples.csv`
  字段数不一致，并复核 sample CSV/JSONL schema 对齐。

## 0B. 2026-06-26 artifact-smoke + streaming persistence 修复方案

### 0B.1 目标

本修复只解决当前 artifact 可观测性和单样本保存验证问题，不改变真实资金 probe 的业务目标：

- 新增 `--artifact-smoke-valid-samples 1`，用于真实资金前的单样本 artifact smoke。该 smoke 只证明一条
  valid sample 能被完整采集、持续写入并最终落盘，不得把正式目标从 `30` 个 valid samples 降级为 `1`。
- 正式 platform-sellable maturity probe 默认仍要求单轮 `30/30` valid samples；未显式启用 artifact
  smoke 时，`--valid-samples 1` 仍必须被拒绝。
- 将 probe / sample / buy evidence 从“程序结束时一次性写出”改为“采集过程中持续写出 forensic stream”，
  避免进程退出、final writer validation failure 或终端断开后无法复核已完成样本。
- 保留 canonical artifact 的严格语义：成功结束后仍由 final writer 写出经 validator 校验的正式 JSONL /
  JSON / CSV；streaming 文件用于运行中和失败后的 forensic review，不冒充正式 `30/30` 成功产物。
- 不扩大 wallet/model/market scope，不引入 raw REST / manual signing / shadow implementation，不改变
  BUY submit retry、heartbeat、partial-fill、venue-dust、under-min cleanup 或 cleanup-audit-only 的交易语义。

本轮用户授权边界：方案落盘后先派生 GPT-5.5/xhigh 只读 subagents 审查；审查通过才执行本地代码修复。
修复完成后再次派生 subagents 审查；审查通过后，已授权执行 fresh build、binary deploy、远端
`--no-live-funds` gate。真实资金 probe 明确不执行。

### 0B.2 修复思路

#### A. 显式区分正式样本目标和 artifact smoke 目标

当前 `PlatformSellableMaturityRunInput.valid_samples` 和
`PlatformSellableMaturityConfig.required_valid_samples` 都被硬限制为 `REQUIRED_VALID_SAMPLES=30`。因此直接运行
`--valid-samples 1` 会在采样前被拒绝，无法验证“只采样一次时数据是否正确写入保存”。

修复规则：

- CLI 新增 `--artifact-smoke-valid-samples <N>`，当前唯一允许值为 `1`。
- 未传 `--artifact-smoke-valid-samples`：
  - effective required valid samples 仍为 `30`；
  - `--valid-samples` 必须等于 `30`；
  - `PlatformSellableMaturityConfig.artifact_smoke=false`。
- 传 `--artifact-smoke-valid-samples 1`：
  - effective required valid samples 为 `1`；
  - `--valid-samples` 只能省略或保持默认 `30`；若用户同时显式传入非默认 `--valid-samples`，必须在
    CLI/input validation 阶段 fail closed，避免两个样本目标并存；
  - run report、summary、stream manifest 和 final summary 必须显式标记 `artifact_smoke=true`；
  - `required_valid_samples=1` 只在 artifact smoke mode 合法；
  - artifact smoke 结果不得被写成或解释成正式 `30/30` maturity dataset。
- 传其他 smoke 值、或在非 smoke mode 下把 `--valid-samples` 改成 `1`，都必须 fail closed before live funds。

该设计避免为正式 probe 放松现有 `30` 样本验收，同时提供一个明确、可审计的单样本保存测试入口。

#### B. 增加 streaming forensic writer，不替代 canonical final writer

当前 live path 先把 `probes`、`samples`、`buy_candidates`、`buy_submit_attempts` 等保存在内存中，只有在
run 结束或 fail trace 写出时才落盘。上一轮修复只能覆盖 final writer validation failure 后的 fail trace，
不能覆盖运行中断电、进程被 kill、SSH 断开或 sample 完成后 finalization 尚未执行的证据缺失。

修复规则：

- 在 live-funds path 创建 output dir 后立即 create-new 以下 forensic stream 文件：
  - `platform_sellable_maturity_stream_manifest.json`
  - `platform_sellable_maturity_events.stream.jsonl`
  - `platform_sellable_maturity_probes.stream.jsonl`
  - `platform_sellable_maturity_samples.stream.jsonl`
  - `platform_sellable_maturity_buy_candidates.stream.jsonl`
  - `platform_sellable_maturity_buy_submit_attempts.stream.jsonl`
  - `platform_sellable_maturity_market_discovery_wait_events.stream.jsonl`
- 每当对应 row 语义完成并进入内存集合时，同步 append 一行 JSON 并 flush。不得等到全 run 完成后才写。
- SELL probe 必须额外写事件流，保证核心 maturity 时点不是等 cleanup 后才落盘：
  - SELL post response 返回并判定 `clean_sell_accepted=true` 时，立即 append/flush
    `event_type="sell_probe_response"`，记录 sample id、probe index、asset、outcome、t_probe_submit_ms、
    t_probe_response_ms、sdk_status、platform_order_id、clean accept 标记和 normalized blank-error 结果；
  - accepted 后的 cancel/open-order audit 再 append/flush `event_type="sell_probe_cleanup_audit"` 或由最终
    probe row 表达；
  - canonical final probe row 仍保持当前最终结构，不用 event stream duplicate 去放松 final validator。
- streaming writer 使用 stream/final artifact 文件级 create-new/no-overwrite 语义；output dir 可由 runner
  `create_dir_all` 创建或已存在，但任何 stream/final artifact 文件名冲突都必须拒绝继续，避免混合两次 run。
- streaming append / flush 失败属于 audit persistence failure：记录 `streaming_artifact_write_error:{err}`，
  停止后续采样并 fail closed，同时尽力写 gate report / fail trace。
- canonical final writer 保持 strict validate-before-write。成功 run 会继续生成正式
  `platform_sellable_maturity_probes.jsonl`、`platform_sellable_maturity_samples.jsonl`、summary 和 CSV；
  streaming 文件只是额外 evidence，不降低 final writer validator。
- 若 sample 内部需要多次 SELL probe，probe row 必须按完成顺序持续写入 stream；不能只在 sample 完成后一次性补写。

#### C. `--no-live-funds` gate 边界保持不变

`--no-live-funds` 仍只验证环境、凭据、配置、SDK post/cancel not attempted、artifact writer 路径和 gate
报告，不采样、不发 BUY/SELL、不产生 valid sample。artifact smoke 是 live-funds 行为，必须在 fresh build、
binary deploy 和远端 `--no-live-funds` gate 通过后另行执行；本轮用户明确不授权真实资金 probe，因此
本轮实现后只执行到远端 `--no-live-funds` gate。

### 0B.3 执行步骤

1. 文档阶段：
   - 本节方案落盘到 active plan；
   - active changelog 记录方案、授权边界和待审查状态；
   - 派生 GPT-5.5/xhigh 只读 subagents 审查方案可执行性、过度设计风险和 gate 边界。
2. TDD 阶段：
   - 先写失败测试覆盖 `--artifact-smoke-valid-samples 1`、非 smoke `--valid-samples 1` 拒绝、
     streaming row 持续落盘、final writer 失败时 stream 已存在、`--no-live-funds` 不采样；
   - 确认 RED 后再实现。
3. 实现阶段：
   - CLI / run input 增加 artifact smoke 字段；
   - `PlatformSellableMaturityConfig` 增加 artifact smoke 标记并保持正式 `30` 样本默认严格；
   - runner live path 初始化 streaming writer；
   - 在 probe、sample、buy candidate、BUY submit attempt、market discovery wait event 进入内存集合时同步写 stream；
   - final writer 成功路径和 fail trace 路径保留现有 strict/canonical 语义。
4. 验证阶段：
   - 运行 focused tests；
   - 运行 full local gate；
   - 同步 active plan / changelog / `lastest-command.md` 中新增 smoke 命令、streaming artifacts 和验收判据。
5. 复审与授权执行阶段：
   - 派生 GPT-5.5/xhigh 只读 subagents 审查实现和测试；
   - 若审查不通过，修复后重复 review；
   - 审查通过后，先确认 active plan / changelog / `lastest-command.md` 已同步，创建 commit 并 push，
     记录 `git status --short --branch`、`HEAD`、`@{u}` 和 `HEAD == @{u}` 证据；
   - 只有本地代码和命令手册已同步、worktree 干净、HEAD 已推送后，才按用户授权执行 fresh release
     build、binary-only deploy、远端 `--no-live-funds` gate；
   - 不执行真实资金 probe。

### 0B.4 测试计划

必须新增或更新以下本地测试：

- CLI / input validation：
  - help 或 parser 覆盖 `--artifact-smoke-valid-samples`；
  - `--artifact-smoke-valid-samples 1` 允许 effective valid samples `1`；
  - smoke mode 下同时显式传非默认 `--valid-samples` 必须拒绝；省略 `--valid-samples` 或保持默认 `30` 时由
    smoke flag 覆盖为 effective `1`；
  - `--artifact-smoke-valid-samples 0/2/30` 拒绝；
  - 未启用 smoke 时 `--valid-samples 1` 继续拒绝。
- Config / writer validation：
  - `artifact_smoke=false, required_valid_samples=30` 通过；
  - `artifact_smoke=true, required_valid_samples=1` 通过；
  - `artifact_smoke=false, required_valid_samples=1` 拒绝；
  - `artifact_smoke=true, required_valid_samples!=1` 拒绝。
- Runner streaming persistence：
  - 单样本 smoke 成功后，streaming JSONL 和 canonical final artifacts 都存在，summary 显示
    `artifact_smoke=true`、`required_valid_samples=1`、`valid_sample_count=1`；
  - clean accepted SELL response 后、cleanup audit 前必须已有 `sell_probe_response` stream event；测试通过
    fake cleanup audit failure 或 staged writer 检查该事件已落盘，证明核心 maturity 时点不依赖 sample finalization；
  - final writer validation failure 时，streaming JSONL 已包含已完成 probe/sample rows，gate report 和
    fail trace 仍写出；
  - 多次 SELL probe 的 row 按完成顺序写入 stream；
  - streaming writer file-level create-new/no-overwrite 生效；
  - 可控 streaming append/flush failure 会写入 `streaming_artifact_write_error:{err}`、停止后续采样、尽力写
    gate report / fail trace，并断言失败后不会继续提交新的 BUY/SELL SDK intent。
- No-live gate：
  - `--no-live-funds` 不产生 sample/probe stream，不触发 SDK post/cancel；
  - gate report 继续显示 `NoLiveFundsPassed`。

最低本地 gate：

- `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`
- focused tests：
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test cli_platform_sellable_maturity --quiet`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity --quiet`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner --quiet`
- full gate：
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
  - `git diff --check`

### 0B.5 验收标准

- 正式 probe 默认仍是 `30` valid samples；任何非 smoke 的 `1` sample run 都不会被当成正式验收。
- artifact smoke 能用 `--artifact-smoke-valid-samples 1` 产生一个完整可复核样本，并在 report / summary /
  stream manifest 中清晰标注 smoke mode。
- probe / sample / BUY evidence 在 run 过程中持续落盘；即使 final writer 失败，也能从 stream 文件和 fail trace
  回答“已经完成了哪些样本、哪些 probe、何时 clean accepted、是否存在 cleanup evidence”。
- streaming artifacts 不降低 canonical artifact validator；正式 success 仍必须通过 final writer strict
  validation。
- fresh build 前必须完成 `lastest-command.md` 同步、commit/push、clean worktree 和 `HEAD == @{u}` 证据记录；
  禁止用未提交或未同步的新代码进入 binary deploy / remote gate。
- fresh build、binary deploy、远端 `--no-live-funds` gate 全部通过后，本轮停止；不执行真实资金 probe。

### 0B.6 本地实现状态

2026-06-26 JST 已按本节方案完成本地实现、实现复审、commit/push、fresh build、binary-only deploy 和远端
production `--no-live-funds` gate；本轮按用户要求停止在 no-live gate 后，未执行 artifact smoke 或真实资金
probe：

- CLI 新增 `--artifact-smoke-valid-samples`；smoke mode 只允许值 `1`，并且 `--valid-samples` 只能省略或保持
  默认 `30`。正式非 smoke mode 仍强制 `valid_samples=30`。
- `PlatformSellableMaturityConfig` 新增 `artifact_smoke` 标记；default config 仍是正式 `30` 样本，
  `artifact_smoke_one()` 只允许 `required_valid_samples=1`。
- run report、gate report、fail trace 和 final summary 均写出 `artifact_smoke` /
  `required_valid_samples`，避免把 smoke `1/1` 误读成正式 `30/30`。
- live-funds path 新增 forensic stream writer，create-new 写出：
  `platform_sellable_maturity_stream_manifest.json`、
  `platform_sellable_maturity_events.stream.jsonl`、
  `platform_sellable_maturity_probes.stream.jsonl`、
  `platform_sellable_maturity_samples.stream.jsonl`、
  `platform_sellable_maturity_buy_candidates.stream.jsonl`、
  `platform_sellable_maturity_buy_submit_attempts.stream.jsonl` 和
  `platform_sellable_maturity_market_discovery_wait_events.stream.jsonl`。
- SELL probe response 会立即写 `sell_probe_response` event；clean accepted 后的 cleanup audit 再写
  `sell_probe_cleanup_audit` event 和 final probe stream row。streaming writer failure 会进入
  `streaming_artifact_write_error:{...}` fail-closed，停止后续采样，并尽力保留 gate report / fail trace；若
  BUY 已被平台 accepted 后 buy-submit stream 写失败，会先 best-effort cancel accepted BUY，再 fail closed。
- `--no-live-funds` path 不初始化 sample/probe/event streams，不采样，不发 SDK post/cancel。
- 本地 focused tests 已通过：
  - `cli_platform_sellable_maturity` 6/6
  - `platform_sellable_maturity` 9/9
  - `platform_sellable_maturity_runner` 54/54
- 实现复审发现的测试缺口已补齐：
  - CLI 覆盖 `--artifact-smoke-valid-samples 0/2/30` 拒绝、非 smoke `--valid-samples 1` 早期拒绝；
  - runner 覆盖 final writer validation failure 后 stream probe/sample rows 已存在；
  - runner 覆盖多次 SELL probe stream row 按 `probe_index=1,2` 完成顺序写入；
  - runner 覆盖 stream file-level create-new/no-overwrite 冲突时 fail-closed before SDK submit。
- 本地 full gate 已通过：
  - `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
  - `git diff --check`
- GPT-5.5/xhigh 实现复审已通过：
  - CLI / smoke / config 语义 review PASS；
  - streaming persistence / live order safety review 初次要求补测试，补齐后 PASS；
  - docs / tests / deploy boundary review 两次要求补测试与状态记录，补齐后 PASS。
- Commit/push gate 已通过：
  - commit：`bb21d140cb373bd9b44f9c265e9314b4116da07f`
  - `git status --short --branch`：`## sdk-live-trade...origin/sdk-live-trade`
  - `HEAD == @{u}`
- Fresh release build 已通过：
  - dirty state：`clean`
  - git diff provenance sha256：
    `7b44ad9c8bd7bb9b2084e2aa0d9a2c106c30db014af8004d2a6941eb46a51a3d`
  - release binary sha256：
    `76fba30568449546584504e0a092a9c2c865431ee0262ad04f101ddad30cd0fa`
  - config sha256：
    `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`
  - model tree manifest sha256：
    `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`
- Binary-only deploy 已通过：
  - deploy id：`r5-bb21d14-binary-deploy-20260626T131826Z`
  - remote binary/config/model sha 校验通过
  - `r5-actor-rehearsal` validator/artifact_validator passed
  - `sdk_post_attempted=false`、`sdk_cancel_attempted=false`
  - no-submit rehearsal report sha256：
    `4930961849eca433ef6bf1dfc0fcecbfc830429be41a0c707ef3ac6169c2385c`
  - 本地 pullback：
    `poly-arb-ai/rust/sdk-live-trade/artifacts/deployments/pullback/r5-bb21d14-binary-deploy-20260626T131826Z/dry-run/`
- Production `--no-live-funds` gate 已通过：
  - run id：`platform-sellable-maturity-no-live-20260626T131913Z`
  - status：`NoLiveFundsPassed`
  - `valid_samples=0`、SDK post/cancel `0/0`、heartbeat `0`、`hard_reasons=0`
  - gate report：`status="no_live_funds_passed"`、`no_live_funds=true`、`artifact_smoke=false`、
    `required_valid_samples=30`、`valid_sample_count=0`、`sdk_post_attempt_count=0`、
    `sdk_cancel_attempt_count=0`、`heartbeat_attempt_count=0`、`fail_closed_reasons=[]`
  - stream files count：`0`
  - 本地 pullback：
    `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260626T131913Z/`
  - gate report sha256：
    `4618e29a771a8e7c42c4a15db3f0a413fdd963b61aae1cfe3c6ba7984fca08b0`
- One-sample artifact smoke 已在用户后续批准后通过：
  - run id：`platform-sellable-maturity-artifact-smoke-20260626T132728Z`
  - 前置只读 open-order gate：`platform-open-orders-check-pre-smoke-20260626T132716Z`，
    `open_order_count=0`
  - CLI summary：`status=Passed`、`artifact_smoke=true`、`required_valid_samples=1`、`valid_samples=1`、
    `sdk_post_attempts=27`、`sdk_cancel_attempts=1`、`hard_reasons=0`
  - gate report：`status="passed"`、`no_live_funds=false`、`artifact_smoke=true`、
    `required_valid_samples=1`、`valid_sample_count=1`、`sdk_post_attempt_count=27`、
    `sdk_cancel_attempt_count=1`、`heartbeat_attempt_count=2`、`fail_closed_reasons=[]`
  - final/stream 行数一致：`probes.jsonl=26`、`probes.stream.jsonl=26`、`samples.jsonl=1`、
    `samples.stream.jsonl=1`
  - summary `metrics.clean_accept_ms.count=1`，mean/median/min/max 均为 `2569ms`；
    `metrics.first_reject_ms.count=1`，mean/median/min/max 均为 `70ms`
  - clean accepted SELL response event 已在 cleanup audit 前写出：events stream 第 `26` 行
    `event_type="sell_probe_response"`、`clean_sell_accepted=true`，第 `27` 行
    `event_type="sell_probe_cleanup_audit"`
  - post-smoke 只读 open-order gate：`platform-open-orders-check-post-smoke-20260626T132750Z`，
    `open_order_count=0`
  - 本地 pullback：
    `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-artifact-smoke-20260626T132728Z/`
  - gate report sha256：
    `b5902438cfeba5469c173f2ddf5cabc8d17cf249926d2e54137924ec4c1e0adf`
  - artifact bundle manifest sha256：
    `fa86de220ac0794c6bf78c69ab323e60764a19b4ded702fbceec51c3abf399cd`
- 当时正式 `30/30` 真实资金 probe 未执行；后续用户已批准并执行正式 run
  `platform-sellable-maturity-live-20260626T133250Z`，结果见 `## 0C`。

## 0A. 2026-06-26 clean-accept artifact normalization / failure-evidence persistence 修复方案

### 0A.1 目标

本修复只解决 `platform-sellable-maturity-live-20260626T092500Z` 暴露的 artifact 写出失败和数据丢失问题：

- clean accepted SELL probe 在最终 artifact 中不得携带任何 reject/error 字段；尤其是 SDK / adapter
  返回的空字符串或空白字符串 `error_message`，必须在 runner 构造 probe row 时归一化为 `None`。
- artifact writer / validator 失败不得再留下空 run directory；只要 runner 内存里已有 probes / samples /
  counters / fail reasons，必须写出可复核的 fail-closed gate report 和 fail-closed trace。
- validator 仍保持严格，不通过放松 validator 来掩盖 runner row 语义错误。
- 不尝试把 `platform-sellable-maturity-live-20260626T092500Z` 追认为有效 `30/30` artifact；该 run 只能作为
  “强推断已进入 30-sample final writer path，但无可审计样本落盘”的失败证据。
- 不改变 trading semantics：不扩大 wallet/model/market scope，不引入 raw REST / manual signing /
  shadow implementation，不改变 heartbeat、partial-fill、under-min cleanup、cleanup-audit-only 的既有业务口径。

### 0A.2 修复思路

#### A. runner 侧清洗 clean accepted SELL probe 字段

问题位置：

- `poly-arb-ai/rust/sdk-live-trade/src/platform_sellable_maturity_runner.rs`
  - `clean_sell_accepted` 判定允许 `observation.error_message` 为 `None`、空字符串或 trim 后空白；
  - 但随后 `let error_message = post.and_then(|observation| observation.error_message.clone())` 会把
    `Some("")` 原样写入 `PlatformSellableMaturityProbeAttempt.error_message`。
- `poly-arb-ai/rust/sdk-live-trade/src/platform_sellable_maturity.rs`
  - `validate_platform_sellable_maturity_probe_attempt()` 对 `clean_sell_accepted=true` 的 row 要求
    `reject_class`、`error_message`、balance/order amount、maturity reject、non-maturity error fields
    全部为空。

修复规则：

- 在 runner 构造 probe row 前，只对 clean accepted SELL probe row 清空 blank `error_message` 和
  reject-derived fields。
- 若 `clean_sell_accepted=true`：
  - `error_message=None`
  - `reject_class=None`
  - `platform_balance_raw=None`
  - `platform_balance_shares=None`
  - `sum_matched_raw=None`
  - `sum_matched_shares=None`
  - `order_amount_raw=None`
  - `order_amount_shares=None`
  - `balance_ge_size=None`
  - `free_ge_size=None`
  - `non_maturity_error_class=None`
  - `is_maturity_reject=false`
- 不清理 accepted 后 cleanup audit 字段：`cancel_error`、`cancel_error_message`、
  `post_cancel_open_orders_count`、`open_order_clear_proof` 等仍按 cleanup-audit-only 规则保留。
- 若不是 clean accept，则 `error_message` 必须保留 adapter 原始观测值，不做 trim/drop，并继续按现有 reject /
  non-maturity error 分类写入字段；不得把真实 reject 清洗成 accepted。

建议实现形态保持局部，不新增跨模块抽象。可在 `run_one_sample()` SELL probe loop 内使用局部变量：

```rust
let observed_error_message = post.and_then(|observation| observation.error_message.clone());
let parsed_reject = if clean_sell_accepted {
    None
} else {
    observed_error_message
        .as_deref()
        .and_then(parse_platform_sellable_maturity_reject)
};
let error_message = if clean_sell_accepted {
    None
} else {
    observed_error_message
};
```

并确保 clean accepted 分支写入 probe row 的所有 reject-derived 字段均为 `None` / false。

#### B. final writer 失败转为可审计 fail-closed，而不是直接 `?` 返回

问题位置：

- `run_platform_sellable_maturity_with_gateway()` 只有在
  `fail_closed_reasons.is_empty() && valid_sample_count == input.valid_samples` 时调用
  `write_platform_sellable_maturity_artifacts(...)`。
- 当前调用使用 `?`；一旦 writer validation 报错，函数直接返回，后续
  `platform_sellable_maturity_gate_report.json` 和 `platform_sellable_maturity_fail_closed_trace.json`
  都不会写。
- writer 本身先 validate 全部 probes / samples，再写 canonical JSONL / JSON / CSV；因此 validation 错误会导致
  output dir 只有空目录。

修复规则：

- canonical writer 的 create-new / validate-before-write 语义保留；它仍负责成功 run 的权威 artifacts。
- runner finalization 改成 `match write_platform_sellable_maturity_artifacts(...)`：
  - `Ok(_)`：status=`Passed`，继续按现有路径写 gate report；
  - `Err(err)`：把 `artifact_writer_validation_error:{err}` 写入 `fail_closed_reasons`，status=`FailClosed`，
    并继续写 gate report + fail-closed trace，trace 中必须包含当前内存里的 probes、samples、buy_candidates、
    buy_submit_attempts、market_discovery_wait_events 和 counters。
- 不新增 incremental canonical JSONL streaming；本轮只要求 final writer validation failure 时保存 forensic
  failure bundle。断电/进程被 kill 的崩溃恢复另立计划，不在本修复中扩大范围。

建议实现形态：

```rust
let mut status = PlatformSellableMaturityRunStatus::FailClosed;
if fail_closed_reasons.is_empty() && valid_sample_count == input.valid_samples {
    match write_platform_sellable_maturity_artifacts(
        &input.output_dir,
        &PlatformSellableMaturityConfig::default(),
        &probes,
        &samples,
        input.now_ms,
    ) {
        Ok(_) => {
            status = PlatformSellableMaturityRunStatus::Passed;
        }
        Err(err) => {
            fail_closed_reasons.push(format!("artifact_writer_validation_error:{err}"));
        }
    }
}
```

随后无论 `Passed` 还是 `FailClosed`，都必须构造 `PlatformSellableMaturityRunReport` 并执行现有 gate report /
fail trace 写出路径。若当前代码的 fail trace 写出只在部分 fail-closed 分支执行，必须收敛为：

- `status == Passed`：写 gate report + canonical artifacts；
- `status == FailClosed`：写 gate report + `platform_sellable_maturity_fail_closed_trace.json`；
- writer validation failure 属于 fail-closed reason，不属于顶层未捕获 error。

#### C. 事故数据恢复边界

本轮已确认：

- 远端 run dir
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/platform-sellable-maturity/platform-sellable-maturity-live-20260626T092500Z/`
  只有空目录，没有程序写出的 JSONL / JSON / CSV / fail trace。
- 本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260626T092500Z/`
  只有 bundle manifest。
- post-live open-order check 只能证明 `open_order_count=0`；post-live account snapshot 只能证明存在一个
  Data API position size `5`，不能恢复 sample-level timeline。

因此不得在文档、报告或后续命令里声称该 run 已获得可审计 `30/30` 样本。允许的结论只有：

- stdout `valid_sample 30/30 ... start` 单独不是完成证据；
- 最终错误来自 `valid_sample_count == input.valid_samples` 后的 writer path，强推断内存里曾达到
  30 个 runner-valid samples；
- 由于无 probes / samples 落盘，无法恢复 `first_clean_accept_ms`、per-probe reject/accept timeline、
  orderbook context、heartbeat/order-query evidence 或全部 30 个样本 asset/order 明细。

### 0A.3 执行步骤

1. 检查当前工作树：

```bash
cd source://sdk
git status --short --branch
```

预期：只允许出现本修复相关文件变更；若出现无关变更，不得回滚，必须避开或先汇报。

2. 先写 runner 回归测试：clean accepted SELL post observation 带 `error_message=Some("")` 或
   `Some("   ")` 时，runner 应成功写出 canonical artifacts，probe JSONL 中
   `clean_sell_accepted=true`、`error_message=null`、所有 reject-derived fields 为 `null` / false。

目标文件：

- `poly-arb-ai/rust/sdk-live-trade/tests/platform_sellable_maturity_runner.rs`

建议新增 fixture 能力：

```rust
enum SubmitOutcome {
    Accepted,
    AcceptedWithBlankError { error_message: String },
    Rejected { error_message: String },
    // keep existing variants unchanged
}
```

测试断言至少包括：

```rust
let probes: Vec<serde_json::Value> = std::fs::read_to_string(
    output_dir.join("platform_sellable_maturity_probes.jsonl"),
)?
.lines()
.map(serde_json::from_str)
.collect::<Result<_, _>>()?;
let clean = probes
    .iter()
    .find(|probe| probe["clean_sell_accepted"] == true)
    .expect("clean accepted probe");
assert_eq!(clean["error_message"], serde_json::Value::Null);
assert_eq!(clean["reject_class"], serde_json::Value::Null);
assert_eq!(clean["platform_balance_raw"], serde_json::Value::Null);
assert_eq!(clean["is_maturity_reject"], false);
```

3. 先写 final writer failure 持久化测试：构造一个 runner 能达到 finalization 但 canonical writer validation
   失败的场景，断言：

- 命令/runner 返回 `status=FailClosed`，不是未捕获 error；
- `platform_sellable_maturity_gate_report.json` 存在；
- `platform_sellable_maturity_fail_closed_trace.json` 存在；
- gate report `fail_closed_reasons` 包含 `artifact_writer_validation_error:`;
- fail trace 中包含已收集的 probes / samples，数量大于 `0`。

优先做法是在 runner 测试里新增最小 test seam，只对测试可见地制造 invalid final probe/sample；如果现有结构
不方便，允许抽一个小的 finalization helper，但 helper 必须只服务当前 runner finalization，不能重构无关逻辑。

4. 保持 validator strict，并补充负向测试：raw `PlatformSellableMaturityProbeAttempt` 若
   `clean_sell_accepted=true` 且 `error_message=Some("")`，`validate_platform_sellable_maturity_probe_attempt()`
   必须返回 `clean accept must not include reject/error fields`。

目标文件：

- `poly-arb-ai/rust/sdk-live-trade/tests/platform_sellable_maturity.rs`

5. 实现 runner clean-accept normalization：

目标文件：

- `poly-arb-ai/rust/sdk-live-trade/src/platform_sellable_maturity_runner.rs`

要求：

- 只清洗 clean accepted SELL probe row 的 reject/error fields；
- 不改变 accepted 后 cleanup audit-only 字段；
- 不改变 non-clean reject / non-maturity error 分类；
- 不改 SDK adapter 的 accepted/rejected 分类，除非测试证明 adapter 自身输出语义与 runner 无法局部处理。

6. 实现 final writer validation failure 的 fail-closed evidence persistence：

目标文件：

- `poly-arb-ai/rust/sdk-live-trade/src/platform_sellable_maturity_runner.rs`

要求：

- 去掉 success writer path 的直接 `?`；
- writer error 写入 `fail_closed_reasons`；
- 保证 gate report 和 fail trace 使用 create-new 语义写出；
- 不把 writer validation failure 伪装成 success；
- 不写 canonical probes/samples/summary 文件作为成功 artifact。

7. 同步文档：

- `poly-arb-ai/sdk-live-trade-docs/plan/2026-06-25-platform-sellable-maturity-probe-plan.md`
- `poly-arb-ai/sdk-live-trade-docs/changelog/2026-06-25-platform-sellable-maturity-probe-plan.md`
- `lastest-command.md`

文档必须记录：

- 本修复不恢复 20260626T092500Z 的 30 个样本；
- 成功标准仍是未来 run 产出可审计 `30/30` valid samples；
- final writer validation failure 必须写 fail trace + gate report；
- 后续真实资金 run 仍需 fresh build、binary-only deploy、no-live gate、pullback 检查和 renewed approval。

8. 本地自审：

- 检查 diff 是否只触及上述目标文件；
- 检查是否有 raw REST / manual signing / shadow implementation；
- 检查是否改变了 heartbeat、partial-fill、under-min cleanup、cleanup-audit-only 的业务口径。

9. 派生 GPT-5.5/xhigh subagents 做只读复审：

- 代码/语义审查：clean accept normalization 是否正确、validator 是否仍严格；
- 持久化审查：writer failure 是否一定写 gate report/fail trace；
- 测试/验收审查：测试是否覆盖真实失败形态和后续 gate。

10. 复审通过后才能 commit/push。commit/push 之后，任何 fresh build、binary-only deploy、production
    `--no-live-funds` gate 和 live-funds probe 都必须重新获得用户明确批准。

### 0A.4 测试

本地 focused tests：

```bash
cd source://sdk
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test cli_platform_sellable_maturity -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_open_order_check -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test sdk_order_adapter -- --nocapture
```

必须新增或确认的测试语义：

- `platform_sellable_maturity_runner`：clean accepted SELL 带 blank error message 时，canonical artifact 写出成功，
  clean probe row 不含 reject/error fields。
- `platform_sellable_maturity_runner`：final writer validation failure 转为 fail-closed，且写出
  `platform_sellable_maturity_gate_report.json` 和 `platform_sellable_maturity_fail_closed_trace.json`。
- `platform_sellable_maturity`：raw clean accepted probe 带 `error_message=Some("")` 仍被 validator 拒绝。
- 既有 cleanup-audit-only 测试继续通过：accepted 后 cancel reject / SDK error / matched-cancel / open-order
  audit 非零不得推翻 valid sample。
- 既有 heartbeat + partial-fill + under-min cleanup 测试继续通过：本修复不得让 under-min / heartbeat
  语义回退。

full local gate：

```bash
cd source://sdk
cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet
git diff --check
```

预期：全部退出码为 `0`。

### 0A.5 验收

文档/代码验收：

- active plan、active changelog、`lastest-command.md` 均记录本修复边界。
- Rust diff 只触及 runner / tests / 必要文档；不得新增 raw REST、manual signing、shadow SDK path。
- validator 保持 strict：clean accepted row 带任何 reject/error 字段仍拒绝。
- runner 保证 clean accepted row 在写入 canonical artifact 前已归一化。
- final writer validation failure 不再导致空 output directory；至少写出：
  - `platform_sellable_maturity_gate_report.json`
  - `platform_sellable_maturity_fail_closed_trace.json`
  - fail reason `artifact_writer_validation_error:{err}`
  - trace 内的 probes / samples / counters / buy evidence。

运行验收：

- 本地 focused tests 和 full local gate 全部通过。
- GPT-5.5/xhigh 只读复审通过；若发现 actionable issue，必须修复并重复复审。
- commit/push 后才能进入 fresh build 审批。
- fresh build / binary-only deploy / production `--no-live-funds` gate / live probe 都不是本修复方案落盘的自动授权项。

未来真实资金验收：

- 新 live run 成功标准仍是单轮 `30/30` 可审计 valid samples，并写出 canonical probes/samples/summary JSONL /
  JSON / CSV。
- 若新 live run fail closed，必须能从 gate report / fail trace 直接回答：
  - 已收集多少 valid / invalid / excluded samples；
  - clean accept 是否被 blank error message 污染；
  - writer validation 是否失败；
  - probes / samples 是否已保存；
  - open-order / account / residual evidence 是什么。
- 不允许再出现“stdout 有进度，但 run dir 没有程序 artifact，无法复核样本”的失败形态。

### 0A.6 当前本地实现状态

2026-06-26 JST 已按本节方案完成本地代码修复、验证和 GPT-5.5/xhigh 只读复审：

- runner 已在 SELL probe row 构造前只对 clean accepted SELL row 清空 blank `error_message` 和
  reject-derived fields；非 clean reject / SDK error 的 `error_message` 保留 adapter 原始观测值，不做
  trim/drop。
- validator 保持 strict；raw clean accepted probe 只要带 `error_message=Some("")` 仍会拒绝为
  `clean accept must not include reject/error fields`。
- final writer success path 已去掉直接 `?` 返回；`write_platform_sellable_maturity_artifacts(...)`
  validation/write error 会转为 `artifact_writer_validation_error:{err}` fail-closed reason，并继续写出
  `platform_sellable_maturity_gate_report.json` 和 `platform_sellable_maturity_fail_closed_trace.json`。
- 新增 runner 回归测试：
  - `live_probe_normalizes_blank_error_message_on_clean_accepted_sell`
  - `live_probe_preserves_blank_error_message_on_non_clean_rejected_sell`
  - `live_probe_persists_fail_trace_when_final_writer_validation_fails`
- 新增 validator 负向覆盖：raw clean accepted probe 带 blank `error_message` 仍被 strict validator 拒绝。
- 本地 focused gates 已通过：
  - `platform_sellable_maturity_runner`：`49/49`
  - `platform_sellable_maturity`：`8/8`
  - `cli_platform_sellable_maturity`：`3/3`
  - `platform_open_order_check`：`3/3`
  - `sdk_order_adapter`：`17/17`
  - `heartbeat_watchdog`：`6/6`
- full local gate 已通过：
  - `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
  - `git diff --check`

用户随后批准并已执行 fresh release build、binary-only deploy、production `--no-live-funds` gate 和产物
拉回检查；真实资金 probe 未执行。执行证据见 active changelog 的
`2026-06-26 clean-accept 修复后 fresh build / deploy / no-live gate`。

## 0. 2026-06-26 本地实现收口：heartbeat + cumulative partial-fill + under-min cleanup

### 0.1 目标

本修复只解决 `platform-sellable-maturity-live-20260626T053750Z` 暴露的 probe runner
问题，不扩大 wallet、model、market 或 SDK fallback 范围：

- 复用现有官方 SDK heartbeat 实现，避免 GTC open remainder 因 heartbeat 缺失被平台自动取消而污染
  partial BUY 状态。
- 不把 heartbeat 当成必然成功；单次网络抖动、rate limit 或 SDK error 必须落盘并进入 degraded 处理。
  是否 fail closed 取决于真实持仓暴露：BUY 前可 censor/resample；BUY 已满 `5` 且 clean SELL 前必须
  fail closed with evidence。
- 正确累计一张 BUY order 的多笔 partial fill；只要累计 fill 最终达到 `configured_probe_size=5`，
  该 BUY 仍可进入有效样本流程，不得在第一次 partial fill 后提前 cleanup cancel。
- 当 BUY 最终累计 `0 < fill_size < min_order_size` 时，不进入 fixed-size limit SELL maturity probe；
  该样本标记为 invalid/excluded，并走 under-min cleanup / reconciliation 证据链。
- 所有新增网络能力必须走官方 Polymarket Rust SDK；不得引入 raw REST、manual signing 或 shadow
  implementation。

### 0.2 修复思路

#### A. Heartbeat liveness 必须复用现有实现

- 复用 `poly-arb-ai/rust/sdk-live-trade/src/heartbeat_watchdog.rs` 中的
  `OfficialHeartbeatGateway`、`HeartbeatWatchdogActor`、`HeartbeatWatchdogConfig::r5_r7_default()`
  和 `SdkRateLimiter::with_budgets(...).with_heartbeat_budget(...)`。
- `PlatformSellableMaturityOfficialGateway` 不自建 heartbeat REST 调用；应像 R5 runtime 一样由
  `main.rs` 创建 `OfficialHeartbeatGateway::new(&clients.clob_client)`，再把 gateway 引用传入
  maturity probe official gateway 或一个小的 heartbeat driver。
- heartbeat cadence 沿用当前生产语义：首次真实 BUY 前必须至少尝试一次 heartbeat；BUY wait collector
  按 heartbeat tick 校正 order state；SELL probe loop 在首次 SELL submit 前以及之后最多每 `5000ms`
  tick 一次，不能按 `20ms` SELL probe cadence 连续打 heartbeat。
- heartbeat `Posted`：允许继续 BUY fill 等待、SELL probe 或 heartbeat-safe cleanup。
- heartbeat `RateLimited` / `SdkError` / `PlatformError`：立即记录 heartbeat counters/status，暂停新增 BUY 和
  SELL submit；继续允许只读 order query、user-channel drain、open-order proof 和必要 cleanup evidence capture /
  reconciliation。
- heartbeat failure 的处理按真实持仓暴露分层，不能一概 resample：
  - BUY 前 heartbeat degraded：没有新真实订单，当前样本 excluded/censored 后 resample，不提交 BUY。
  - under-min partial BUY 且 heartbeat degraded：不提交 FAK cleanup，不 cancel BUY，只写
    `residual_evidence_only`、`raw_rest_fallback_used=false` 后 resample。
  - `fill_size >= probe_size` 后、first clean SELL accepted 前 heartbeat degraded：必须 fail closed with
    evidence，要求 open-order / residual / account reconciliation 后才能新增订单；不得带着已买到的 shares
    继续下一样本。
  - first clean SELL accepted 后 heartbeat degraded：样本仍 valid，后续只影响 cleanup audit。
- 当前实现复用 `HeartbeatWatchdogActor` 的 per-tick status，不额外声明 probe-local `last_posted_ms` /
  watchdog gap recovery 语义；如果后续要实现 gap recovery，必须另立 plan/code/test，不得在本文档中当作
  已完成能力。
- heartbeat 恢复/继续必须按层次判断，不能把下一次 `Posted` 当成无条件恢复：
  - observability continue：`RateLimited` / `SdkError` / `PlatformError` 期间仍继续 user-channel drain、
    CLOB order query、open-order proof、account/order snapshot 和必要 cleanup response capture。
  - same-order continue：下一次 heartbeat `Posted` 后，若同一 `platform_order_id` 的 CLOB / user-channel
    evidence 能证明 order 仍 `LIVE` 或 cumulative fill 单调增加，market 尚未 end / reduce-only，且 buy-fill
    deadline 未到，则继续等待同一 BUY 的后续 partial fill，不得因为曾出现一次 heartbeat 失败就 cancel。
  - new-submit resume：下一次 heartbeat `Posted` 后，还必须证明没有 unknown open order、没有 unresolved
    under-min residual、run 未处于 reduce/cancel/reconcile-only，且 pre-submit open-order / account state safe，
    才能提交新的 BUY 或 SELL probe。
  - valid-sample continue：`fill_size >= probe_size` 后，从 BUY fill ledger apply 到 first clean SELL accepted
    之间不得发生 heartbeat degraded / unsafe；若 heartbeat 失败发生在 clean accepted 之前，该 run 必须
    fail closed with evidence；若失败发生在 clean accepted 之后，样本仍 valid，后续只影响 cleanup audit。
- Under-min FAK cleanup 本质是新的 SELL submit，只能在 heartbeat safe / `Posted` 且 order state 已证明时执行。
  heartbeat degraded 或 watchdog unsafe 期间不得提交 FAK cleanup；只能写 residual / reconciliation evidence。

#### B. BUY partial fill 改成 condition-based cumulative order state

- 当前 `collect_buy_fill_from_user_stream()` 已按 `trade_id` 去重累计 user-channel trade size；修复不得破坏
  这个语义。
- 现有固定 `10_000ms` 后 `fill_size < 5` 立即 cleanup cancel 的流程必须改成 condition-based：
  - 收到 partial fill 后继续等待同一 `platform_order_id` 的后续 user-channel trade；
  - 周期性使用现有 `R5ClobQueryAdapter` / official SDK `client.order(order_id)` 查询 `size_matched`、
    `associate_trades` 和 terminal status；
  - 若 user-channel lag 但 CLOB query 显示 `size_matched` 增加，必须更新累计 evidence；
  - 若 order 仍 `LIVE` 且 heartbeat safe，不能 cancel；
  - 只有在 buy-fill deadline 到达、market 进入 reduce-only、heartbeat watchdog 不可恢复、或 CLOB/open-order
    evidence 证明该 order 已非 LIVE 时，才允许进入 partial terminal 处理。
- `buy_fill_deadline_ms` 固定复用当前命令的 `probe_timeout_ms`，默认 `60000ms`，并受 market end /
  reduce-only transition 约束；不得保留或新增隐藏的 `10_000ms then cancel` 逻辑。
- 多笔 partial fill 示例必须被支持：`1.2 + 2.1 + 1.7 = 5` 应生成一个有效 BUY fill evidence，
  继续进入 fixed-size SELL maturity probe。
- `fill_size >= 5` 时仍按当前有效样本口径处理：`sell_size` 固定 `5`，SELL probe 仍使用 non-crossing
  limit order，测量 `first_clean_accept_ms`。

#### C. Under-min partial BUY cleanup

- Terminal classifier 的优先级固定为：
  1. `fill_size >= probe_size`：valid BUY fill，进入 fixed-size SELL maturity probe；
  2. `0 < probe_size - fill_size <= venue_dust_threshold`：沿用 venue-dust terminal；
  3. non-dust `0 < fill_size < min_order_size`：under-min partial BUY；
  4. `min_order_size <= fill_size < probe_size` 且 residual 非 dust：unexpected partial terminal，样本 invalid，
     写 explicit residual / reconciliation evidence，不发 fixed-size SELL；
  5. no fill / no order evidence：按现有 fail-closed 或 resample 规则处理。
- 若最终累计 non-dust `0 < fill_size < min_order_size`，该 BUY 不计入有效样本，写
  `exclusion_reason=partial_buy_fill_below_min_order_size`。
- 该分支不得尝试用 `fill_size` 发 limit SELL；Polymarket 当前 BTC 5m market `min_order_size=5`，
  `3.3` shares 这类余额低于 limit order minimum。
- 如果官方 Rust SDK market order builder 可表达 `OrderType::FAK` SELL 且可以设置 worst-price limit，
  则实现 SDK-backed under-min market cleanup：
  - side 固定 `SELL`；
  - amount 固定为实际已成交 BUY shares `fill_size`，不是未成交 residual；实现前必须用官方 SDK 类型、
    本地官方文档镜像和单元测试证明 SELL FAK `Amount::shares(fill_size)` 不可能超过已持有 shares；
  - order type 固定 `FAK`；
  - worst-price limit 来自当前 orderbook best bid 减少受控 slippage ticks，不能无界卖出；
  - cleanup report、SDK response projection sha256、raw/projection error evidence、transaction hashes、
    filled size、residual size、sdk status 和 error message 必须落盘。
- 如果官方 Rust SDK 不能表达上述 market cleanup，必须停止实现并汇报 SDK 能力缺口，等待用户确认；不得改用
  raw REST 或 manual signing。
- 如果 FAK cleanup 返回 reject / `SdkError` / unsupported，不得把样本变 valid，也不得静默吞掉；必须写
  SDK response body/projection evidence、residual position evidence 和 `raw_rest_fallback_used=false`。
- under-min market cleanup 未完全成交时，不把样本变 valid，也不把残余静默忽略；必须写
  residual position evidence，并由 post-run account snapshot / reconciliation 报告暴露。
- heartbeat degraded / watchdog unsafe 期间不得提交 under-min FAK；该样本写
  `under_min_cleanup_status=residual_evidence_only`、`under_min_cleanup_raw_rest_fallback_used=false`
  和 residual/error evidence 后 resample。
- venue-dust 规则保留：`probe_size - fill_size <= 0.01` 的历史 dust terminal 仍按已有 venue-dust
  分支处理；本节主要处理 `sample-0003` 这类 residual `1.7` 的 non-dust under-min partial。

#### D. 审计与报告

新增或扩展 artifact 字段，保证事故可复核：

- run-level：`heartbeat_attempt_count`、`heartbeat_last_status`、`heartbeat_unsafe_count`、
  `heartbeat_censored_sample_count`。
- sample-level：`buy_fill_terminal_reason`、`buy_order_query_status`、`buy_order_query_size_matched`、
  `buy_order_query_associate_trades`、`heartbeat_status_during_buy_wait`、
  `heartbeat_status_during_sell_probe`、`under_min_cleanup_status`、`under_min_cleanup_order_type`、
  `under_min_cleanup_fill_size`、`under_min_cleanup_residual_size`、
  `under_min_cleanup_platform_order_id`、`under_min_cleanup_transaction_hashes`、
  `under_min_cleanup_order_adapter_report_sha256`。
- fail-closed trace 必须按触发条件保留 heartbeat attempts/status/timestamps、order query evidence、
  venue-dust cleanup cancel report、market cleanup report、SDK response body/projection sha256 和 residual
  position evidence；不得再出现“只写 hard reason、丢失 cancel response body”的审计缺口。
- 现有 `platform_sellable_maturity` validator 必须是 condition-based，不得过宽 hard gate：只有发生 heartbeat degraded 才要求
  heartbeat degraded evidence；只有发生 under-min 才要求 cleanup/residual evidence；first clean SELL accepted
  后的 cleanup audit 失败、缺失或非零 open-order audit 不得推翻 maturity valid sample。
- 不再声明独立 `platform_sellable_maturity_artifact_validator` target；相关负向覆盖保留在
  `--test platform_sellable_maturity` 内。
- `--no-live-funds` gate 不得 post heartbeat、不得 post/cancel/market-cleanup；其 heartbeat counters 必须为
  `0` 或 absent，cleanup / market-cleanup attempt counters 也必须为 `0` 或 absent，并继续作为纯 no-live gate。

### 0.3 执行步骤

1. TDD：新增 heartbeat degraded 与 cumulative partial-fill 回归测试，先确认当前代码失败。
2. 在 official maturity gateway 中接入现有 `OfficialHeartbeatGateway` / `HeartbeatWatchdogActor`，不新增 raw
   HTTP 入口。
3. 把 BUY fill collection 从 fixed `10s then cancel` 改为 condition-based cumulative state：user-channel
   累计 + CLOB order query 校正 + heartbeat liveness gate。
4. 实现 partial terminal 分类：
   - `fill_size >= probe_size`：valid BUY fill，进入现有 SELL maturity probe；
   - `probe_size - fill_size <= venue_dust_threshold`：沿用 venue-dust terminal；
   - non-dust `0 < fill_size < min_order_size`：invalid excluded sample，进入 under-min cleanup /
     reconciliation；
   - `min_order_size <= fill_size < probe_size` 且 residual 非 dust：unexpected partial terminal，写 residual /
     reconciliation evidence，不发 fixed-size SELL；
   - no fill / no order evidence：按现有 fail-closed 或 resample 规则处理。
5. 若 SDK 能力允许，实现 under-min SDK market FAK SELL cleanup；若 SDK 不允许，停止并汇报缺口，不落 raw
   REST 旁路。
6. 扩展 gate report、fail-closed trace、CSV/summary 和现有 `platform_sellable_maturity` validator，保证新增
   heartbeat/order-query/under-min cleanup 字段被校验。
7. 同步更新 active plan、changelog 和 `lastest-command.md` 中的命令、预期结果和 fail-closed 判据。
8. 本地验证通过后派生 GPT-5.5/xhigh 只读 subagent 审查代码、测试、文档和执行步骤。
9. 审查通过后 commit/push；任何后续真实资金 run 仍需重新获得用户对 fresh release build、binary-only
   deploy、远端 `--no-live-funds` gate 和 live-funds probe 的明确批准。

### 0.4 测试

必须新增或更新以下实际测试覆盖；不再引用不存在的单独 artifact-validator test target：

- `heartbeat_sdk_error_before_buy_censors_sample_without_submit`：BUY 前 heartbeat `SdkError` 不提交 BUY，样本
  excluded/censored 后 resample。
- `heartbeat_sdk_error_during_full_buy_wait_fail_closes_before_new_submit`：BUY 已满 `5` 后、clean SELL accepted
  前 heartbeat degraded 时 fail closed，不继续新增订单。
- `heartbeat_sdk_error_before_sell_fail_closes_without_sell_submit`：SELL 前 heartbeat degraded 不提交 SELL，并
  fail closed 要求 reconciliation。
- `heartbeat_degraded_blocks_under_min_market_cleanup_submit`：under-min partial BUY 下 heartbeat degraded 不提交
  FAK cleanup，不 cancel BUY，只写 residual evidence。
- `partial_buy_under_min_non_dust_is_excluded_without_canceling_buy`：`3.3/5` non-dust under-min 不 cancel BUY，
  不发 limit SELL，只走 SDK FAK market cleanup，且 amount=`fill_size`。
- `partial_buy_above_min_under_probe_is_unexpected_residual_without_cancel_or_sell`：
  `min_order_size <= fill_size < probe_size` 的异常 partial 不走旧 cancel，也不发 SELL。
- `partial_buy_venue_dust_cancel_reject_is_excluded_and_resampled_when_open_orders_clear` 和
  `partial_buy_above_venue_dust_under_min_is_excluded_without_canceling_buy`：venue-dust 优先级和 non-dust
  under-min 分支不混淆。
- `no_live_funds_gate_does_not_submit_or_cancel`：`--no-live-funds` gate 的 SDK post/cancel/heartbeat/cleanup
  attempt 均为 `0`。
- `submit_market_order_maps_build_sign_post_observations`：SDK market order adapter 覆盖 build/sign/post
  observation path。
- `platform_sellable_maturity` validator tests：在现有 test target 内校验新增 heartbeat/order-query/
  under-min cleanup/residual 字段；不存在独立 `platform_sellable_maturity_artifact_validator` target。

当前 fake runner 测试不声称完整覆盖官方 CLOB order-query recovery 或多笔 partial fill projection；这些能力由
官方 collector 代码路径实现，后续若要把多笔 partial / query projection 做成 synthetic gate，需要单独补
fake gateway order-query evidence，而不是在文档中声称已测。

本地 gate 顺序：

```bash
cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test heartbeat_watchdog -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test sdk_order_adapter -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet
git diff --check
```

### 0.5 验收

本地验收：

- 所有新增 focused tests 先 RED 后 GREEN，并保留失败原因摘要。
- Full `sdk-live-trade` test gate、`cargo fmt --check` 和 `git diff --check` 退出码均为 `0`。
- `platform_sellable_maturity` validator 必须接受新增 heartbeat/order-query/under-min cleanup 字段，并拒绝
  under-min BUY cancel/raw REST fallback；校验必须 condition-based，不得把 accepted 后 cleanup audit-only 场景误写成
  hard gate。
- 文档同步完成：active plan、active changelog、`lastest-command.md` 均记录新的修复边界和命令。

行为验收：

- 不再因为第一次 partial fill `<5` 立即 cancel；正常多笔 partial fill 累计到 `5` 后必须作为 valid BUY。
- heartbeat 失败不会被当成“必然平台失败”；无真实持仓暴露时单次失败只 censor sample / pause new submit；
  BUY 已满 `5` 且 clean SELL accepted 前发生 degraded 时必须 fail closed with evidence。
- heartbeat 恢复后不会无条件继续：同一 BUY order 必须有 `LIVE` / cumulative fill evidence 才继续等待；
  新订单必须有 open-order / residual / account safe proof 才能提交；clean accepted 前 full-fill heartbeat
  degraded 不能继续 resample 后提交新订单。
- `fill_size < min_order_size` 不会发 limit SELL；只能走 SDK-backed market cleanup 或明确 residual
  reconciliation；venue-dust residual 必须先于 under-min 分支处理。
- `--no-live-funds` gate 仍然不触发真实 SDK post/cancel/heartbeat/cleanup。
- 后续 live-funds run 若再次 fail closed，artifact 必须能直接回答：heartbeat 是否成功、BUY order 是否仍 live、
  partial fill 是否继续累计、cleanup cancel / market cleanup 返回了什么。

上线验收：

- fresh release build 必须记录 commit、dirty state、binary sha256、config sha256、model tree sha256。
- binary-only deploy 必须验证远端 binary/config/model sha，并通过 `r5-actor-rehearsal` 与
  platform-sellable local/remote artifact checks。
- 远端 production `--no-live-funds` gate 必须通过，且 `sdk_post_attempts=0`、`sdk_cancel_attempts=0`、
  heartbeat attempt 和 cleanup / market-cleanup attempt counters 为 `0` 或 absent。
- live 前 open-order check 必须为 `0`。
- 真实资金 probe 只有在上述全部通过且用户重新批准后才能执行；成功标准仍是单轮 `30/30` valid samples，
  excluded under-min / heartbeat-censored samples 不计入有效样本。

### 0.6 当前本地实现状态

2026-06-26 JST 本地代码已按本节方案完成以下收口，focused gates 与 full local gate 已通过，等待最终
subagent review：

- `PlatformSellableMaturityOfficialGateway` 已复用 `OfficialHeartbeatGateway` /
  `HeartbeatWatchdogActor`；不新增 raw REST heartbeat。
- BUY wait 已移除隐藏 `10s` deadline，改为 `probe_timeout_ms`，并在 heartbeat tick 后通过官方 SDK
  `client.order(order_id)` 查询 BUY order `status`、`size_matched`、`associate_trades`，用 query evidence
  校正 cumulative fill。
- BUY 前 heartbeat degraded 会 censor/resample；`fill_size >= probe_size` 后、clean SELL accepted 前 heartbeat
  degraded 会 fail closed with evidence；under-min FAK cleanup 在 heartbeat unsafe 时被阻断，只写
  residual-only evidence。
- non-dust `0 < fill_size < min_order_size` 不再走旧 BUY cleanup cancel；heartbeat safe 时使用官方 SDK
  market order builder 提交 `SELL` `OrderType::FAK`，`Amount::shares(fill_size)`，worst-price limit 来自
  当前 best bid，且 `raw_rest_fallback_used=false`。
- `--no-live-funds` 分支仍在进入 live gateway 前返回，SDK post/cancel/heartbeat/market-cleanup attempt
  均为 `0`。
- 已补 sample/gate report 字段：heartbeat counters、BUY order query projection、under-min cleanup /
  residual evidence。
- 当前 fake runner tests 不声明完整覆盖官方 CLOB order-query recovery 或多笔 partial-fill projection；这些仍是
  后续如需加强 synthetic gate 时的明确剩余测试口径。
- 本地验证已通过：`cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`、
  `platform_sellable_maturity_runner` `46/46`、`platform_sellable_maturity` `8/8`、`heartbeat_watchdog`
  `6/6`、`sdk_order_adapter` `17/17`、full
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`、`git diff --check`
  均退出码 `0`。
- 本段只说明当时的本地实现状态；当时 fresh release build、binary-only deploy、远端 production
  `--no-live-funds` gate、产物拉回和真实资金 probe 尚未执行，后续执行状态以本文顶部 current
  cursor 和 `## 0C` 为准。

## 1. 背景

历史真实资金 artifact 已证明一个具体问题：本地 ledger 在 BUY fill 后会先入账，模型随后可能立刻尝试 SELL，
但 Polymarket 平台侧同 asset 的可卖余额尚未成熟，导致 `not enough balance / allowance`。该错误消息通常带有
`balance`、`order amount`，有时还带有 `sum of matched orders`，可以反推出平台侧余额可见性的变化。

已有历史样本来自：

- `poly-arb-ai/rust/sdk-live-trade/artifacts/remote-r5-runs/r5-three-market-live-funds-*`
- `trading-runtime/orders.jsonl`
- `trading-runtime/fills.jsonl`

历史只读分析的初步结论是：

- 本地 ledger 入账后，第一次 SELL 余额不足通常在约 `0.2s - 0.5s` 内出现。
- 实际平台首次 clean SELL accepted 常见在约 `1.2s - 5.3s`。
- 只看 reject message 里的 `balance >= first_sell_size` 会更晚，已观察样本可到约 `46s`，因为平台余额可能同时被已有或匹配中的 SELL 占用。

这些历史样本可以作为基线，但不能直接作为训练部门的最终参数，因为模型自然行为会改变 SELL size、价格、挂单数量和撤单节奏。

## 2. 需求目标

目标是获得一个可靠、可复现、可量化的时间分布：

- 本地 ledger 已经入账后，平台侧同 asset 可卖余额多久才成熟。
- 给训练交易模型部门提供可用统计量：mean、median、p75、p90、p95、min、max、timeout rate。
- 区分三个不同口径，避免把平台 reject message、实际 SELL accepted 和可用空闲余额混在一起。

最终希望训练部门可以据此决定：

- 模型在 BUY fill 后多久以内不应立即反向 SELL。
- 是否需要在 action mask、reward、post-processing 或 runtime submit adapter 中加入 sellable maturity 延迟。
- 是否需要把本地 ledger account_state 与 platform-sellable submit cap 分开建模。

## 3. 核心口径

主指标：

- `t_first_clean_sell_accepted - t_ledger_apply`

辅助指标：

- `t_first_sell_reject - t_ledger_apply`
- `t_first_balance_ge_size - t_ledger_apply`
- `t_first_free_ge_size - t_ledger_apply`
- `attempt_count_to_clean_accept`
- `attempt_count_to_balance_ge_size`
- `attempt_count_to_free_ge_size`
- `balance_ge_size_censored_count`
- `free_ge_size_censored_count`
- `timeout_count`

字段定义：

- `t_ledger_apply`：同 asset 的 BUY fill 被本地 authoritative ledger apply 的时间。
- `first_sell_size`：本次 probe 固定尝试卖出的 size。
- `clean_sell_accepted`：SELL post observation 无 error、非 blank `platform_order_id`、`status=SdkAccepted`。
- `balance_ge_size`：reject message 中 `balance / 1_000_000 >= first_sell_size`。
- `free_ge_size`：reject message 中 `(balance - sum of matched orders) / 1_000_000 >= first_sell_size`。
- `balance_ge_size` / `free_ge_size` 只从 accepted 前的 SELL reject message 观测；如果 clean SELL accepted
  先发生，则对应字段必须记录为 `null`，并标记 `censored_due_to_clean_accept`，不得为了补齐该字段继续提交 SELL。

## 4. 推荐测试方案

采用受控 live probe，而不是直接让训练模型自然交易。

每个样本只测一个变量：同 asset BUY fill 本地入账后，平台侧可卖余额何时成熟。

单个样本流程：

1. 选择一个新的 `Polymarket BTC UP/DOWN 5MIN` market 和一个 outcome asset。
2. 记录 probe 前该 asset 的平台可卖余额 baseline。
3. 使用官方 Polymarket Rust SDK 提交一笔小额 BUY，目标是获得至少 `5` shares 的同 asset fill。
4. 等待 user-channel / normalized event 进入 order lifecycle，并写入本地 ledger。
5. 记录 `t_ledger_apply`、`buy_order_id`、`buy_trade_id`、`fill_size`。
6. 如果 `fill_size < configured_probe_size`，该 BUY 不计入有效样本，记录排除原因并重新采样。
7. 立即开始同 asset SELL probe，固定 `sell_size = configured_probe_size = 5` shares；同一样本内所有 SELL probe
   的 size 必须完全一致。
8. 每次 SELL probe 前读取当前 orderbook，并使用官方 Rust SDK 提交 maker-only / post-only、不会 cross 当前盘口的
   limit SELL；必须记录 `order_type`、`post_only`、`sell_limit_price`、probe 前 `best_bid` / `best_ask`。
9. 如果官方 Rust SDK 无法表达 maker-only / post-only 或无法保证订单不会立即成交，必须停止计划执行并汇报 SDK
   能力缺口、影响范围和可选方案，等待用户确认；不得自行改用 raw REST、manual signing 或 shadow implementation。
10. 如果 SELL reject，解析并记录 `balance`、`order amount`、`sum of matched orders`、reject classification。
11. 按固定 cadence 重复 SELL probe，直到出现 clean SELL accepted 或 timeout；429 / rate limit、network、server、
    SDK transient error 不计入 maturity reject，必须单独分类、backoff，并按规则排除样本或停止 run。
12. 一旦 clean SELL accepted，立即记录 `first_clean_accept_ms` 和 accepted SELL 的
    `platform_order_id`，停止该样本后续 SELL probe；该时间点就是有效样本的 maturity 成功终点。
13. 对 accepted SELL 执行 best-effort cleanup：尝试 cancel，并记录 cancel submit / ack / status /
    error / not-canceled reason。若 SELL 已成交、cancel rejected、cancel SDK error、或返回
    `matched orders can't be canceled`，只记录 cleanup audit / manual review evidence，不得把该样本
    或整轮 run fail closed。
14. accepted 后的 optional open-order audit 只用于人工复核：若查询成功，记录同 asset open SELL count
    和 proof；若查询失败或 count 非零，也不得推翻 `first_clean_accept_ms` 或样本有效性。runner 可继续
    进入下一样本，但下一样本的 BUY 前 baseline gate 仍必须阻止同 asset platform balance 或 open SELL 污染。

## 5. 采样 cadence 与样本量

默认 probe cadence：

- 第一笔 SELL probe：BUY fill ledger apply 后立即提交，不 sleep。
- `0s - 10s`：后续 probe 每 `20ms` 尝试一次。
- `10s - 60s`：后续 probe 每 `100ms` 尝试一次。
- `60s` 后仍未 clean accepted：标记 timeout。
- 如果连续出现 429 / rate limit、network、server 或 SDK transient error，先按指数 backoff 暂停 probe；
  这类错误不得计入 `first_sell_reject`、`balance_ge_size` 或 `free_ge_size`。无法恢复时该样本排除，
  若错误影响 run 级可信度则停止本轮 probe。

第一轮已确认约束：

- 固定采集 `30` 个有效样本。
- 固定使用 `5` shares 作为 `configured_probe_size` / first SELL probe size。
- BUY 使用 marketable limit order；`derived_buy_limit_price = max(best_ask, ceil_to_tick(1 / buy_size))`，
  以满足平台 `$1` 最小 BUY notional。该价格仍必须满足 `derived_buy_limit_price <= max_buy_price`
  且 `derived_buy_limit_price * buy_size <= max_buy_notional_usdc`，否则 BUY 前 fail closed。
- 尽量覆盖 UP / DOWN 两腿。
- 尽量覆盖不同 5MIN market window。

如果第一轮结果离散明显，例如 `p90 > 3 * median`，再扩展到 `60` 个有效样本。

## 6. 有效样本规则

样本纳入统计必须满足：

- 有同 asset BUY fill 的本地 ledger apply 证据。
- probe 前同 asset 没有未取消 SELL open order。
- `fill_size >= 5` shares，且每次 probe 固定 `sell_size = 5` shares；不足 `5` shares 的 partial fill
  必须排除或重新采样。
- probe 使用固定 SELL size，不能随模型输出变化，也不能用 `min(fill_size, configured_probe_size)` 改变有效样本 size。
- SELL probe 必须是官方 Rust SDK 可表达的 maker-only / post-only、不会 cross 当前盘口的 limit order。
- probe 不调用训练模型策略，不让模型同时生成额外 BUY/SELL。
- 同一时刻同 asset 只允许一个 active SELL probe。
- clean SELL accepted 后不得继续提交 SELL 来等待 `balance_ge_size` 或 `free_ge_size`，未观测到的 reject-derived
  指标必须按删失处理。
- clean SELL accepted 是样本 maturity 成功终点；accepted 后成交、cancel 失败、matched-cancel rejection、
  optional open-order audit 缺失或非零只进入 audit/manual review，不属于样本排除条件。
- 使用官方 Polymarket Rust SDK，不使用 raw REST、manual signing 或 shadow implementation。
- 如果 SDK 能力不足，必须先停止并汇报具体缺口、影响范围和可选方案，等待用户确认。

样本排除条件：

- BUY fill 没有进入本地 ledger。
- BUY fill 后立即 market end 或 market 不再接受 orders。
- SELL probe 期间出现 credential / allowance / wallet scope 异常，且无法解释为 sellable maturity。
- clean accepted 前出现非 maturity SELL reject / SDK error，且不能明确归类为可恢复 transient 并在 timeout
  内恢复。
- 429 / rate limit、network、server 或 SDK transient error 无法恢复，导致 maturity 时间线不可解释。
- artifact writer 缺失关键字段。

## 7. Artifact 设计

建议新增独立 artifact：

- `platform_sellable_maturity_probes.jsonl`
- `platform_sellable_maturity_samples.jsonl`
- `platform_sellable_maturity_summary.json`
- `platform_sellable_maturity_probes.csv`
- `platform_sellable_maturity_samples.csv`
- `platform_sellable_maturity_summary.csv`

`platform_sellable_maturity_probes.jsonl` 每行记录一次 probe 尝试：

```json
{
  "run_id": "r5-platform-sellable-maturity-wallet1-...",
  "sample_id": "sample-0001",
  "wallet_id": "wallet1",
  "condition_id": "0x...",
  "asset_id": "...",
  "outcome": "Up",
  "buy_order_id": "0x...",
  "buy_trade_id": "...",
  "pre_probe_platform_balance_raw": "<SDK balance_allowance conditional balance raw before BUY>",
  "pre_probe_open_sell_orders_count": 0,
  "fill_size": "5",
  "t_ledger_apply_ms": 1782130532329,
  "probe_index": 1,
  "t_probe_submit_ms": 1782130532580,
  "t_probe_response_ms": 1782130532587,
  "sell_size": "5",
  "order_type": "limit",
  "post_only": true,
  "best_bid": "0.49",
  "best_ask": "0.51",
  "sell_limit_price": "0.99",
  "non_marketable_check": true,
  "sdk_status": "UNKNOWN",
  "platform_order_id": null,
  "reject_class": "not_enough_balance_allowance",
  "error_message": "not enough balance / allowance: the balance is not enough -> balance: 0, order amount: 5000000",
  "platform_balance_raw": "0",
  "platform_balance_shares": "0",
  "sum_matched_raw": null,
  "sum_matched_shares": null,
  "order_amount_raw": "5000000",
  "order_amount_shares": "5",
  "balance_ge_size": false,
  "free_ge_size": null,
  "is_maturity_reject": true,
  "non_maturity_error_class": null,
  "clean_sell_accepted": false,
  "sell_probe_fill_detected": false,
  "cancel_submit_ms": null,
  "cancel_ack_ms": null,
  "cancel_after_accept_status": null,
  "cancel_error": null,
  "post_cancel_open_orders_count": null,
  "open_order_clear_proof": null,
  "exclusion_reason": null
}
```

`platform_sellable_maturity_samples.jsonl` 每行记录一个样本的最终归档口径：

```json
{
  "run_id": "r5-platform-sellable-maturity-wallet1-...",
  "sample_id": "sample-0001",
  "valid": true,
  "exclusion_reason": null,
  "wallet_id": "wallet1",
  "condition_id": "0x...",
  "asset_id": "...",
  "outcome": "Up",
  "fill_size": "5",
  "sell_size": "5",
  "t_ledger_apply_ms": 1782130532329,
  "first_reject_ms": 258,
  "first_clean_accept_ms": 2045,
  "first_balance_ge_size_ms": null,
  "balance_ge_size_censor_reason": "censored_due_to_clean_accept",
  "first_free_ge_size_ms": null,
  "free_ge_size_censor_reason": "censored_due_to_clean_accept",
  "attempt_count_to_clean_accept": 5,
  "attempt_count_to_balance_ge_size": null,
  "attempt_count_to_free_ge_size": null,
  "timeout": false,
  "sell_probe_fill_detected": true,
  "post_cancel_open_orders_count": 1,
  "open_order_clear_proof": "audit_only_open_sell_orders_nonzero"
}
```

上例展示 accepted 后 cleanup audit 的非理想结果仍可保留为 valid sample：`sell_probe_fill_detected=true`、
cancel rejected / `SdkError`、`post_cancel_open_orders_count > 0`、open-order audit 查询失败或 proof 缺失，
都不得推翻 `first_clean_accept_ms`。validator 只应校验这些 audit 字段的类型、非 blank 约束和时间因果；
不得把字段值非零、失败或缺失作为 valid sample 拒绝条件。

`platform_sellable_maturity_summary.json` 至少包含：

```json
{
  "run_id": "r5-platform-sellable-maturity-wallet1-...",
  "sample_count": 30,
  "valid_sample_count": 30,
  "excluded_sample_count": 0,
  "timeout_count": 0,
  "non_maturity_error_count": 0,
  "metrics": {
    "first_reject_ms": {
      "count": 30,
      "timeout_count": 0,
      "censored_count": 0,
      "mean": 258,
      "median": 250,
      "p75": 500,
      "p90": 500,
      "p95": 500,
      "min": 120,
      "max": 500
    },
    "clean_accept_ms": {
      "count": 30,
      "timeout_count": 0,
      "censored_count": 0,
      "mean": 2045,
      "median": 2045,
      "p75": 3000,
      "p90": 5200,
      "p95": 5900,
      "min": 1205,
      "max": 5236
    },
    "balance_ge_size_ms": {
      "count": 12,
      "timeout_count": 0,
      "censored_count": 18,
      "censored_due_to_clean_accept_count": 18,
      "mean": 9120,
      "median": 9212,
      "p75": 12000,
      "p90": 16000,
      "p95": 40000,
      "min": 1500,
      "max": 46000
    },
    "free_ge_size_ms": {
      "count": 10,
      "timeout_count": 0,
      "censored_count": 20,
      "censored_due_to_clean_accept_count": 20,
      "mean": 8500,
      "median": 8200,
      "p75": 11000,
      "p90": 15000,
      "p95": 38000,
      "min": 1500,
      "max": 43000
    }
  },
  "generated_at_ms": 1782130600000
}
```

示例数值只用于说明字段，不代表最终结论。

CSV 输出要求：

- `platform_sellable_maturity_probes.csv` 必须与 JSONL probe 明细一一对应，便于人工筛选、排序和复核。
- `platform_sellable_maturity_samples.csv` 必须与 sample JSONL 一一对应，便于人工按样本复核时间线、
  删失原因、排除原因和 accepted 后 cleanup audit evidence；该 evidence 可以是 cancel accepted、
  cancel rejected、`SdkError`、matched-cancel、open-order count 非零或 open-order audit 查询失败。
- `platform_sellable_maturity_summary.csv` 必须包含 summary JSON 的核心统计字段；可采用一行一个
  `metric_name` 的扁平格式，字段至少包含 `count`、`timeout_count`、`censored_count`、`mean`、
  `median`、`p75`、`p90`、`p95`、`min`、`max`。
- CSV 中的时间差字段直接输出毫秒数，不只输出格式化字符串。
- CSV 不能替代 JSONL / JSON；JSONL / JSON 仍是机器验收和 artifact validator 的权威结构化产物。

## 8. 验收标准

本测试计划完成后，应能给出：

- 每个有效样本的完整时间线。
- 每个样本的 first reject、first clean accepted、first balance-ge-size、first free-ge-size；accepted 前未观测到的
  balance/free 指标必须记录为 `null` 并给出删失原因。
- 对 first reject、clean accepted、balance-ge-size、free-ge-size 分别输出聚合统计：count、timeout/censored
  count、mean、median、p75、p90、p95、min、max。
- 面向训练部门的延迟建议必须同时给出 `median`、`p90` 和 `p95`，不得只选一个口径。
- 同时输出 CSV，供人工复核审查。
- 对异常样本的排除原因。
- 给训练部门的一句话建议，例如：`BUY fill 后 X ms 内避免提交同 asset SELL，建议使用 p90 或 p95 作为保守延迟。`
- accepted SELL 后续 cleanup audit：是否尝试 cancel、cancel submit / ack / status / error /
  not-canceled reason，以及 optional open-order audit 的 count / proof / 查询失败原因。该 cleanup audit
  只用于人工复核，不作为 maturity sample 是否有效的验收条件。

不得把以下内容当成验收通过：

- 只凭自然模型交易 artifact 的粗略统计。
- 只凭 reject count，不解析 balance / order amount / sum matched。
- 只凭 `balance >= size`，不确认 clean SELL accepted。
- 在同 asset 存在未取消 SELL open order 时继续把 reject 解释为 maturity delay。
- 为了补齐 reject-derived balance/free 指标，在 clean SELL accepted 后继续提交 SELL probe。
- 把 clean SELL accepted 后的 fill、cancel rejected、cancel SDK error 或 open-order audit 非零/缺失当成
  maturity sample 失败。
- 让 SELL probe 以可成交价格、非 maker-only / post-only 参数进入平台。

## 9. 执行前置条件

该 probe 属于真实资金路径，执行前必须满足：

- 当前 active blocker 已修复。
- 本地 focused tests / full local gate 通过。
- GPT-5.5/xhigh 只读 review 通过。
- fresh release build 完成。
- binary-only deploy 到 AWS Ireland sdk-live-trade 服务器完成。
- production `--no-live-funds` gate 通过。
- 用户单独明确批准本次 probe 的资金规模、样本数、market scope、timeout、rollback 条件。

在未满足这些条件前，本计划只允许用于审查和本地实现设计，不允许执行真实资金 probe。

## 10. 已确认参数

用户已在 2026-06-25 JST 确认：

- 第一轮样本数量固定为 `30` 个有效样本。
- `configured_probe_size` 固定使用 `5` shares。
- `platform-sellable-maturity-probe` 单笔 BUY notional cap 固定为 `5` USDC；按
  `buy_size=5`、`max_buy_price=0.99` 估算，第一轮 `30` 个有效样本的理论 BUY notional 上限约
  `148.5` USDC，实际成交价格可能低于该上限。
- BUY limit price 由 `max(best_ask, ceil_to_tick(1 / buy_size))` 派生；在 `buy_size=5` 时，
  低价 outcome 的最低可提交 BUY price 为 `0.20`。该规则不扩大 `max_buy_price=0.99`、
  单笔 `max_buy_notional_usdc=5` 或 run 级 conservative BUY intent notional cap。
- 若 BUY 累计 fill `< configured_probe_size`，不得再按旧口径直接 cleanup cancel。必须先按 terminal
  classifier 处理：live 且未到 `buy_fill_deadline_ms` 时继续等待；dust residual 走既有 venue-dust；
  non-dust under-min 只允许 heartbeat-safe SDK FAK cleanup 或 residual / reconciliation evidence；unexpected
  partial 写 explicit residual evidence。重采样不得突破 run 级 conservative BUY intent notional cap，cap =
  `valid_samples * max_buy_notional_usdc`。
- `median`、`p90`、`p95` 都必须输出并提供给训练部门。
- 必须同时输出 CSV，方便人工复核审查。
- 历史记录：用户曾批准 BUY min-notional remediation 后的本地验证、GPT-5.5/xhigh review、fresh release
  build、binary-only deploy 和 production `--no-live-funds` gate。该授权已被后续真实资金失败和当前
  BUY submit evidence/retry 修复 supersede；当前授权边界以本节末尾 cursor 为准。

## 11. 本地执行进度

历史执行范围：BUY min-notional remediation 曾按当时授权推进 fresh release build、binary-only deploy 和
production `--no-live-funds` gate。该范围已被后续真实资金失败和当前 BUY submit evidence/retry 修复 supersede；
当前不得据此直接执行 fresh build、deploy、no-live gate 或真实资金 probe。当前下一步只允许完成本地 review、
commit/push，并在后续重新申请 build/deploy/no-live/live approval。

- [x] 新增 `poly-arb-ai/rust/sdk-live-trade/src/platform_sellable_maturity.rs`，定义
  `platform_sellable_maturity_probes.jsonl`、`platform_sellable_maturity_samples.jsonl`、
  `platform_sellable_maturity_summary.json` 及对应 CSV 的结构化 schema、create-new 写出、summary 聚合。
- [x] 新增 `poly-arb-ai/rust/sdk-live-trade/tests/platform_sellable_maturity.rs`，覆盖 reject message
  解析、固定 `5` shares 样本规则、SELL probe `post_only` / non-cross 校验、clean accepted 作为
  maturity 成功终点、accepted 后 cleanup audit-only、删失统计、CSV 输出和 create-new/no-overwrite。
- [x] 本地 RED/GREEN focused gate 已执行：
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity -- --nocapture`。
- [x] GPT-5.5/xhigh review 首轮发现 validator 过宽问题后，已补齐硬边界：`configured_probe_size` /
  `required_valid_samples` 固定为 `5` / `30`、probe 前 same-asset open SELL count 必须为 `0`、
  clean accepted probe 不得同时携带 reject/error 字段、maturity reject 字段必须由 `error_message`
  反解析一致、valid sample 必须以 clean accept 或 timeout 结束、observed metric 不得同时标记删失、
  reject-derived metric 不得晚于 clean accept、writer 必须拒绝混合 `run_id` 或 orphan probe sample。
- [x] GPT-5.5/xhigh 复审后继续收紧 final artifact writer 和时间线：最终写出
  `platform_sellable_maturity_summary.json` / CSV 前，`valid_sample_count` 必须等于
  `required_valid_samples = 30`；maturity reject probe 不得携带 accepted/cancel evidence；
  `first_reject_ms` 也必须不晚于 `first_clean_accept_ms`。
- [x] 最终只读审查继续指出 final writer 需要跨行一致性门禁后，已补齐：sample id 必须唯一；
  每个 valid sample 必须有 probe evidence；probe 的 `wallet_id` / `condition_id` / `asset_id` /
  `outcome` / `fill_size` / `t_ledger_apply_ms` 必须匹配 sample；`first_reject_ms`、
  `first_clean_accept_ms`、`first_balance_ge_size_ms`、`first_free_ge_size_ms` 和对应
  `attempt_count_to_*` 必须能从 probe timeline 派生；valid sample 不允许 `exclusion_reason`；
  valid sample 对应 probe 不允许 `exclusion_reason`。
- [x] GPT-5.5/xhigh 后续复审指出 probe 分类和 accepted 后时间线仍需收紧后，已补齐：
  non-maturity error 的 `error_message` 不得能被解析为 maturity reject；clean accepted probe 的
  `cancel_submit_ms` 必须不早于 `t_probe_response_ms`，`cancel_ack_ms` 必须不早于
  `cancel_submit_ms`；同一样本出现 first clean accepted 后不得再有后续 probe rows；valid sample
  对应 probe row 携带 `exclusion_reason` 的负向覆盖已补齐。
- [x] GPT-5.5/xhigh 最终实现复审继续指出两个边界后，已补齐：maturity reject message
  解析出的 `order_amount_shares` 必须等于固定 `sell_size = 5`；first clean accepted 后的后续
  probe row 必须按真实 submit/response 时间拒绝，不能依赖不可信或重复的 `probe_index` 排序。
- [x] GPT-5.5/xhigh 最终边界复审继续指出 attempt count 仍可能受 `probe_index` 影响后，已补齐：
  每条 probe row 必须满足 `t_probe_submit_ms >= t_ledger_apply_ms` 且
  `t_probe_response_ms >= t_probe_submit_ms`；sample metric 与 `attempt_count_to_*` 改为按真实
  submit/response 时间派生，不按 `probe_index` 排序。
- [x] GPT-5.5/xhigh 文档/覆盖复审继续指出 equal timestamp 与 config 覆盖缺口后，已补齐：
  同一样本内重复 `(t_probe_submit_ms, t_probe_response_ms)` 会被拒绝为 ambiguous；调用方把
  `required_valid_samples` 设为 `29` 或 `31` 的负向覆盖已补齐，配置仍固定为 `30`。
- [x] GPT-5.5/xhigh 最终执行边界复审指出同 asset active SELL probe interval 可重叠后，已补齐：
  同一样本相邻 probe 的时间区间必须满足 `next.t_probe_submit_ms > previous.t_probe_response_ms`，
  否则 final writer 拒绝 artifact，确保同一时刻同 asset 只有一个 active SELL probe。
- [x] GPT-5.5/xhigh summary 口径复审指出 timeout 与 clean-accept censor 可混用后，已补齐：
  `first_clean_accept_ms` 缺失时，`balance_ge_size_censor_reason` /
  `free_ge_size_censor_reason` 必须为空；timeout 缺失指标只计入 `timeout_count`，
  不计入 `censored_due_to_clean_accept_count`。
- [x] GPT-5.5/xhigh non-blank 字段复审指出 whitespace-only 值可绕过后，已补齐：
  clean accept 的 `platform_order_id` 必须非空；accepted 后 cleanup audit 字段若出现，
  `cancel_after_accept_status`、probe/sample `open_order_clear_proof` 等字符串值均按
  `trim().is_empty()` 拒绝 blank 值，但 cleanup 字段缺失、失败或非零不得推翻 clean accept 样本有效性。
- [x] Post-GREEN full local gate 已在 2026-06-25 JST 执行通过：
  `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all --check`、
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`、
  `git diff --check`。
- [x] controlled live probe runner 已接入真实资金执行入口：新增
  `platform-sellable-maturity-probe` CLI、`--no-live-funds` gate、官方 SDK-backed live gateway、
  动态 BTC UP/DOWN 5MIN market discovery、user-channel BUY fill evidence、固定 `5` shares
  post-only / non-crossing SELL probe、clean accept 后 best-effort cleanup audit、
  create-new JSONL/JSON/CSV final artifact writer，以及每个 asset 只采一次的去重等待门禁。
- [x] runner pre-probe baseline 已补齐官方 SDK `balance_allowance` 证据：每个样本 BUY 前查询
  conditional token balance 和同 asset open SELL orders；若 pre-probe platform balance 已经
  `>= probe_size` 或 open SELL count 非零，则在 BUY 前 fail closed，避免历史持仓/挂单污染 maturity
  计时样本。`pre_probe_platform_balance_raw` 不再使用硬编码占位值。
- [x] runner SELL probe pacing 已补齐真实等待：第一笔 SELL probe 在 `t_ledger_apply` 后立即开始，
  后续 SELL probe 前按 configured fast/slow interval `sleep`；submit/response/cancel timestamp
  使用 wall-clock，避免只写递增 timestamp 但真实请求连发。
- [x] GPT-5.5/xhigh runner review 指出的真实资金 blockers 已补齐（历史口径，当前已由 `## 0` supersede）：
  BUY fill evidence 改为累计到 `probe_size`；当时 partial BUY fill 仍会 cleanup cancel、写 invalid sample 并重采样；
  第一笔 SELL probe 在 `t_ledger_apply` 后立即开始，后续 probe 才按 cadence 等待；clean accepted 后
  open-order audit 非零或查询失败只作为 manual review evidence；fail-closed live run 会额外写
  `platform_sellable_maturity_fail_closed_trace.json` 用于 BUY 前污染、SDK 能力缺口、pre-accept
  不可解释错误等硬边界；user-channel 订阅后会等待 SDK user-channel
  connection state 进入 connected 后才提交 BUY。
- [x] GPT-5.5/xhigh 复审指出 official user-channel timeout 分支仍会返回 error、绕过 partial invalid
  sample/resample 后，已补齐：官方 stream collector 在 timeout 时返回当前累计 partial evidence，并新增
  `collect_buy_fill_returns_partial_evidence_when_stream_times_out` 覆盖。
- [x] runner focused RED/GREEN gate 已执行：
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test cli_platform_sellable_maturity -- --nocapture`、
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner -- --nocapture`。
- [x] Post-runner full local gate 已执行：
  `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all --check`、
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`、
  `git diff --check`。
- [x] GPT-5.5/xhigh 只读 review 已执行并通过；review 覆盖官方 SDK-only 边界、user-channel 订阅时机、
  post-only/non-cross SELL、asset 去重、no-live 零 post/cancel、artifact schema、命令文档和真实资金安全门禁。
- [x] fresh release build 已在本地完成：`git_commit=49a534122b132b49d3d716032b8b242c9259d9d8`、
  `dirty_state=clean`、release binary sha256 =
  `6a0218090fd8e6300fea872f25b4febcbdb98dde58da03a11e0146964aeb4c19`。
- [x] binary-only deploy 已完成：`r5-49a5341-binary-deploy-20260625T133136Z`；远端
  `[PRIVATE_HOME]/sdk-live-trade` binary/config/model sha 校验通过，R5 actor rehearsal 输出
  `validator=passed`、`artifact_validator=passed`、`sdk_post_attempted=false`、
  `sdk_cancel_attempted=false`。
- [x] production `--no-live-funds` gate 已完成：远端 run
  `platform-sellable-maturity-no-live-20260625T133223Z` 输出 `status=NoLiveFundsPassed`、
  `sdk_post_attempts=0`、`sdk_cancel_attempts=0`。
- [x] 真实资金 probe 已执行一次并在 BUY 前 fail closed：远端 run
  `platform-sellable-maturity-live-20260625T133257Z` 输出 `status=FailClosed`、
  `valid_samples=0`、`sdk_post_attempts=0`、`sdk_cancel_attempts=0`，fail reason 为
  `sample-0000:buy notional is below platform minimum $1`。产物已拉回本地
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-20260625T133257Z/`。
- [x] GPT-5.5/xhigh 并行只读审查已定位 blocker：`best_ask * buy_size < 1` 是低价 outcome 的
  candidate / price derivation 问题，不是 SDK post/cancel 失败；直接 skip 会系统性排除低价腿，影响
  UP/DOWN 覆盖。
- [x] 用户已批准按最小修复方案继续：BUY limit price 改为
  `max(best_ask, ceil_to_tick(1 / buy_size))`，同时保留 `max_buy_price`、单笔
  `max_buy_notional_usdc`、run-level cap、pre-probe balance/open SELL、partial BUY cleanup、
  SELL post-only/non-cross gate；clean accepted 后成交、cancel 和 open-order audit 只记录 evidence，
  不作为 maturity fail-closed gate。
- [x] BUY min-notional TDD focused gate 已执行：新增低价 `best_ask=0.18` 派生 `0.20` 后完成
  `30` 个有效样本、derived price 超 `max_buy_price` BUY 前 fail-closed、derived notional 超
  `max_buy_notional_usdc` BUY 前 fail-closed、`ceil_to_tick` 向上取整、CLI flags 完整暴露等覆盖；
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test cli_platform_sellable_maturity -- --nocapture`
  和
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner -- --nocapture`
  均退出码 `0`。
- [x] GPT-5.5/xhigh 首轮只读 review 指出两个残留边界后，已补齐：
  `min_order_size <= 0` 必须在 SDK post/cancel 前 fail closed，run-level BUY intent notional cap
  必须有 dedicated test 和 `buy_candidates` fail-closed trace 证据。
- [x] BUY min-notional review remediation 后的 final full local gate 已执行：
  `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`、
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet` 和
  `git diff --check` 均退出码 `0`。
- [x] BUY min-notional 修复后的 GPT-5.5/xhigh 只读 review 已通过：代码/测试复审与文档/执行边界复审
  均为 `PASS`，无 actionable findings。
- [x] BUY min-notional remediation 已 commit/push：code commit
  `f685b55c03957ceab64973a2f0ba7be97e6cec4e` / `sdk-live-trade: fix platform sellable buy notional gate`
  已推送到 `origin/sdk-live-trade`。
- [x] fresh release build 已通过：release binary sha256 =
  `942b1fdc61838ccbc8ffa94e863bdd3515fec63922320b5ea47088b7c160029c`，config sha256 =
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`，model tree hash =
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`。
- [x] binary-only deploy 已通过：deploy id
  `r5-f685b55-binary-deploy-20260625T144053Z`，远端 binary/config/model sha 校验通过，
  rehearsal 输出 `validator=passed`、`artifact_validator=passed`、SDK post/cancel `false/false`。
- [x] production `--no-live-funds` gate 已通过：远端 run
  `platform-sellable-maturity-no-live-20260625T144138Z` 输出 `status=NoLiveFundsPassed`、
  `sdk_post_attempts=0`、`sdk_cancel_attempts=0`。产物已拉回本地
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260625T144138Z/`，
  gate report sha256 =
  `00dd30f1caf7eac541586840f5406787b0b021e7c83558cea6fbb5c93dac624e`。
- [x] BUY min-notional remediation 后的真实资金 probe 已执行并 fail closed：远端 run
  `platform-sellable-maturity-live-20260625T145028Z` 输出 `status=FailClosed`、
  `valid_samples=1`、`sdk_post_attempts=5`、`sdk_cancel_attempts=2`、`hard_reasons=1`。
  fail reason 为 `sample-0002:current market is reduce/cancel/reconcile only`。产物已拉回本地
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260625T145028Z/`；
  gate report sha256 =
  `2d45978a705915c36da10065fa141160ef21f341c2fe514863fd6e43a436b2da`，fail trace sha256 =
  `e8d1269ad7060751cf5307dcce2078e99f01cc40405240fb191f325e31a150bd`。
- [x] 本轮真实资金局部证据：`sample-0000` / UP 为单个有效 maturity sample，`fill_size=5`、
  `first_reject_ms=128`、`first_clean_accept_ms=1408`、`attempt_count_to_clean_accept=3`、
  `post_cancel_open_orders_count=0`。这只能证明单样本 maturity，不构成整轮 probe pass 或统计结论。
- [x] 本轮 artifact 未显示遗留 open SELL 的正向证据：`sample-0000` clean SELL accepted 后
  `cancel_after_accept_status=SdkAccepted`、`post_cancel_open_orders_count=0`、
  `open_order_clear_proof=clob_open_sell_orders_empty`。但当前 pullback 只有 gate report 和 fail trace，
  没有完整 orders/user-channel/open-order 原始 JSONL 或远端 CLOB snapshot；因此不能从当前 artifact
  独立证明 run 结束后所有平台 open orders 均为空。
- [x] 本轮真实资金无 min-notional 复发证据：`buy_candidates` 仅包含 `sample-0000` 和 `sample-0001`，
  两者均为 `decision=submitted`；`sample-0001` / DOWN 为 invalid sample，
  `exclusion_reason=buy_fill_size_below_configured_probe_size`、`fill_size=0`，随后进入 resample。
- [x] 当时执行边界已记录：本轮 fail-closed 后不得直接重跑，需先完成 root-cause review、修复方案、
  local tests、GPT-5.5/xhigh review、fresh release build、binary-only deploy、production
  `--no-live-funds` gate、产物拉回检查和 renewed approval。本轮已验证运行二进制对应 code commit
  `f685b55c`；该历史边界已被后续 reduce-only wait fix、BUY submit evidence/retry fix 和当前 `## 0`
  heartbeat + partial-fill 本地收口 supersede，当前 cursor 以文件顶部和末尾为准。
- [x] 2026-06-26 JST 已完成本轮 fail-closed root-cause review 和修复方案草案，详见
  `poly-arb-ai/sdk-live-trade-docs/plan/2026-06-26-platform-sellable-reduce-only-root-cause-fix-proposal.md`；
  两路 GPT-5.5/xhigh 只读 subagent review 对方案方向给出 PASS，但均要求 typed wait reason、
  BUY 前 wait-only、不吞 pending cleanup/active order 错误、补 wait artifact 和 open-order proof。
- [x] 用户已批准执行 2026-06-26 fix proposal。执行前只读 pre-check 已通过现有
  `remote-dry-run` 当前 market open-order snapshot 完成：远端 run
  `platform-open-order-precheck-20260625T152130Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-order-precheck-20260625T152130Z/`；
  `open_order_snapshot.json` 显示 `queried=true`、`ok=true`、`count=0`、`exposures=[]`，
  且 `sdk_post_attempted=false`、`sdk_cancel_attempted=false`。该证据只覆盖当前 market snapshot；
  本次代码已新增 dedicated 全平台 `platform-open-orders-check` CLI，下一次 live 前必须用新二进制再跑一次。
- [x] 本地 TDD 实现已完成：`discover_market()` 改为 typed
  `PlatformSellableMaturityDiscoveryOutcome::{Ready,Wait}`；reduce-only / already-used asset 等待写入
  `market_discovery_wait_events`；BUY submit 前新增最后一次 reduce-only wait guard；invalid BUY cleanup
  cancel 后必须通过 bounded pagination 证明同 asset open orders 为 `0` 并记录 64-hex SDK response
  projection sha256；wait event 保留并校验 `active_order_state` / `pending_cleanup`，携带 active order
  或 pending cleanup 时 fail closed；新增只读
  `platform-open-orders-check` CLI，使用官方 Rust SDK `orders` 查询全平台 open orders，不 submit/cancel。
- [x] 本地 focused tests 已通过：
  `platform_sellable_maturity_runner` 18/18、`platform_sellable_maturity` 8/8、
  `cli_platform_sellable_maturity` 2/2、`platform_open_order_check` 3/3。
- [x] 本地 full gate 已通过：
  `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check` 和
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`、
  `git diff --check` 均退出码 `0`。
- [x] GPT-5.5/xhigh 只读复审已完成两路 PASS。首轮发现 wait safety fields 不得被覆盖、
  raw response wording 不准确、缺少 active/pending cleanup 负向测试和 command docs 计数问题；
  已修复并完成回归复审，回归复审两路均无 actionable issue。
- [x] reduce-only wait fix 实现已 commit/push：`60b683fb8dd6a4e088373fd87acc4fe32f9d4ca5`
  (`sdk-live-trade: handle reduce-only probe wait`) 已推送到 `origin/sdk-live-trade`。
- [x] fresh release build 已按授权执行并通过：build HEAD
  `d220860921b34dabb1aa422ed999ed82e6c152a6`，dirty state `clean`，
  git diff provenance sha256
  `920a4317305548491f503e7fa99895b0c5defa6058d7f957e71237d26f4ac963`；release binary sha256
  `f943127de7d467d061b1961de67c9f4f6a3851d5915457017395e930f5a787ce`，config sha256
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`，model tree sha256
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`。
- [x] binary-only deploy 已通过：deploy id
  `r5-d220860-binary-deploy-20260625T172158Z`；脚本只复制 release binary、config 和 model tree，
  远端 binary/config/model sha 校验通过；`r5-actor-rehearsal` 输出 validator/artifact_validator
  passed，`sdk_post_attempted=false`、`sdk_cancel_attempted=false`；`no_submit_rehearsal_report.json`
  sha256 `5e3cedde15a9544d2c6cec61ef64095d99f22d39f09739c44883813ede03eba7`。
- [x] live 前 dedicated open-order gate 已通过：远端 run
  `platform-open-orders-check-20260625T172250Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-20260625T172250Z/`；
  `status=passed`、`open_order_count=0`、`open_order_ids=[]`、`sdk_post_attempted=false`、
  `sdk_cancel_attempted=false`。report sha256
  `12badce4c1b1ce9bbea6839afe07e1be3fd6bf92fdfacfdaf2893ac8561c3d6d`，bundle manifest sha256
  `70c3d9453649a506a6d752a9984438175b76d3cc9bc4267e91354df81483805f`。
- [x] production `--no-live-funds` gate 已通过：远端 run
  `platform-sellable-maturity-no-live-20260625T172313Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260625T172313Z/`；
  `status=no_live_funds_passed`、`no_live_funds=true`、`valid_sample_count=0`、
  `sdk_post_attempt_count=0`、`sdk_cancel_attempt_count=0`、`fail_closed_reasons=[]`。
  gate report sha256 `d1258020699c8ea38e61e35521dcb666e691183a816799ffc1ce41a52d6fd2f2`，
  bundle manifest sha256 `ab347ef4d3812b99f497dc917fdab107ddcf3124d5870801f626d7033502ad85`。
- [x] 历史 renewed 真实资金 probe 已按授权执行并 fail closed（已由
  `platform-sellable-maturity-live-20260626T033334Z` supersede）：远端 run
  `platform-sellable-maturity-live-20260625T172350Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260625T172350Z/`；
  CLI summary：`status=FailClosed`、`valid_samples=9`、`sdk_post_attempts=50`、
  `sdk_cancel_attempts=10`、`hard_reasons=1`。gate report：`status=fail_closed`、
  `valid_sample_count=9`、`market_discovery_wait_count=189`、
  `market_discovery_reduce_only_wait_count=8`；fail reason：
  `sample-0009:BUY cleanup cancel after insufficient fill was not accepted`。gate report sha256
  `28631dc314b35c9f17e8828a55781171240edca91248db72982e1866ce8cd0e2`，fail trace sha256
  `52fd3a9a31761cae94db52189e54c048ea56f6c39c9efa7b7e067dc06428f6be`，bundle manifest sha256
  `44d7d7aeaaa060fcddb090c0617bcb9b6317ae26f6f66cdb461c0ee0efe83e24`。
- [x] post-live open-order safety check 已通过：远端 run
  `platform-open-orders-check-post-live-20260625T174106Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-post-live-20260625T174106Z/`；
  `status=passed`、`open_order_count=0`、`open_order_ids=[]`，SDK response projection sha256
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`；report sha256
  `23376391c256338e247d7ee66124af0d7962df9168b8e7004087aa16450927fe`，bundle manifest sha256
  `217974746cf56d709748c73b91945ae5ce5089a065772d8525f565cbca0ffe38`。
- [x] post-live account snapshot 已拉回用于 residual exposure 证据：远端 run
  `post-live-account-snapshot-20260625T174249Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/post-live-account-snapshot-20260625T174249Z/`。
  Data API positions queried OK，`data_position_count=2`：sample-0008 UP asset
  `30406386996139829832337070085137874128812585032520671093904802343818679254932`
  size `5` value `2.125`；sample-0009 DOWN asset
  `101698463432434787332761595855115625023785413522703854250705780793619856313924`
  size `4.9939` value `2.8714`。`account_snapshot.json` sha256
  `d382a1e8dd139646f1e6094a2b92c4c27c81fc5db47a97c8c3f91b5065004b28`，
  `position_value_snapshot.json` sha256
  `05422a0763c2c78fc27744d489b8be1abf6f5b8ede3bd07ac2ab65e84c142505`，
  bundle manifest sha256 `453bf7b925c94399481eb5067c8b0aae71a05ef08f01dcf49ce58add99d94021`。
- [x] root cause 修正：`sample-0009` 不是普通 partial BUY cleanup failure。post-live account snapshot
  显示 DOWN position size `4.9939`，相对 `probe_size=5` 的 residual 为 `0.0061` shares，小于既有
  `venue_dust_threshold_shares=0.01`。platform-sellable maturity probe 的 partial BUY cleanup path
  未复用既有 venue-dust terminal semantics，因此把 dust residual 的 cancel reject 当成 hard fail。
- [x] venue-dust 本地 TDD 修复已完成：partial BUY residual `>0 && <= 0.01` 且 cleanup cancel
  为 `SdkRejected`、并带有 `not_canceled` 或 error message rejection evidence 时，必须继续通过
  official SDK-backed open-order proof 证明同 asset open orders 为 `0`，然后写 invalid/excluded
  sample 并 resample；该 sample 不计入 valid sample，不 mint shares，不把 `4.9939/5` 当成完整
  `5` shares。artifact 新增 `cleanup_buy_order_id`、
  `cleanup_cancel_not_canceled_json`、`cleanup_cancel_error_message`、`cleanup_venue_dust_shares` 和
  `cleanup_terminal_reason`，其中 terminal reason 固定为 `venue_dust_below_threshold`。残差大于
  threshold、cleanup cancel 为 `SdkError`、缺少 cancel rejection evidence 或 open-order proof 非 0
  仍 fail closed。
- [x] RED/GREEN 证据：新增测试
  `partial_buy_venue_dust_cancel_reject_is_excluded_and_resampled_when_open_orders_clear`，先失败为
  `left: FailClosed right: Passed`；修复后通过。新增负向测试
  `partial_buy_cancel_reject_above_venue_dust_still_fail_closes`，确认 `4.98/5` 这类残差 `0.02`
  不会被 venue-dust 放行；新增 `partial_buy_venue_dust_cancel_sdk_error_still_fail_closes` 和
  `partial_buy_venue_dust_cancel_reject_without_evidence_still_fail_closes`，确认 SDK/network error 与
  缺少 rejection evidence 的 cancel reject 不会被 venue-dust 放行。
- [x] focused/full local gates 已通过：
  `partial_buy_` filter 5/5、`platform_sellable_maturity_runner` 22/22、`platform_sellable_maturity` 8/8、
  `cli_platform_sellable_maturity` 2/2、`platform_open_order_check` 3/3；
  `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`、
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet` 和
  `git diff --check` 均退出码 `0`。
- [x] 修复后 GPT-5.5/xhigh 回归复审已通过：代码/测试 reviewer PASS；文档/计数 reviewer 仅指出
  `lastest-command.md` 缺少当前测试计数明细，已补齐。
- [x] 用户已批准执行 venue-dust fix 后的 fresh build、binary-only deploy、production `--no-live-funds`
  gate；全部通过后也批准执行真实资金 probe。
- [x] fresh release build 已按授权执行并通过：build HEAD
  `2bbe4e8596bf0aaa7de6330fb6faaa6742625445`，dirty state `clean`，
  git diff provenance sha256
  `dc74e92deeb9012668441d52ec88fd35fb292f052ea8c819fcca1e8b5c57fb9c`；release binary sha256
  `de556d46dc18a29945209d3edbe34cb31c6c5bccf8b64c058f7287899677e480`，config sha256
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`，model tree sha256
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`。
- [x] binary-only deploy 已通过：deploy id
  `r5-2bbe4e8-binary-deploy-20260625T185252Z`；脚本只复制 release binary、config 和 model tree，
  远端 binary/config/model sha 校验通过；`r5-actor-rehearsal` 输出 validator/artifact_validator
  passed，`sdk_post_attempted=false`、`sdk_cancel_attempted=false`；`no_submit_rehearsal_report.json`
  sha256 `24fea457c8377e4b75398d9ade43795826afc02b0fa37f7e62c988749d718916`。
- [x] live 前 dedicated open-order gate 已通过：远端 run
  `platform-open-orders-check-20260625T185345Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-20260625T185345Z/`；
  `status=passed`、`open_order_count=0`、`open_order_ids=[]`、`sdk_post_attempted=false`、
  `sdk_cancel_attempted=false`。SDK response projection sha256
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`，bundle manifest sha256
  `d45ecacfcdb7db78a0815b908dcb1fcb547beb8d20530f04d8542e58f3a1d9d6`。
- [x] production `--no-live-funds` gate 已通过：远端 run
  `platform-sellable-maturity-no-live-20260625T185410Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260625T185410Z/`；
  `status=no_live_funds_passed`、`no_live_funds=true`、`valid_sample_count=0`、
  `sdk_post_attempt_count=0`、`sdk_cancel_attempt_count=0`、`fail_closed_reasons=[]`。
  gate report sha256 `a581b4688075c9379d6bd7e40bce43ce293034dc6df5d70d39f2973580fc1b56`，
  bundle manifest sha256 `250d33873d908cb89cd84aace1d45a4588b917d3f1a0a24d14f1d8b4190fe97c`。
- [x] renewed 真实资金 probe 已按授权执行并 fail closed：远端 run
  `platform-sellable-maturity-live-20260625T185437Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260625T185437Z/`；
  CLI summary：`status=FailClosed`、`valid_samples=1`、`sdk_post_attempts=11`、
  `sdk_cancel_attempts=2`、`hard_reasons=1`。gate report：`status=fail_closed`、
  `valid_sample_count=1`、`market_discovery_wait_count=0`、
  `market_discovery_reduce_only_wait_count=0`；fail reason：
  `sample-0001:cancel after clean SELL accept was not accepted`。gate report sha256
  `b2445b0c383441157235a4bbde8fc362a1d3fbd0da63c882fc168f84499e007f`，fail trace sha256
  `6cd6ad14c596c1690e6e4fc54c261228c591b8b3a4fb860a99d9705e63ed5d5e`，bundle manifest sha256
  `e5438c7144ddda63f60558d11bcec13df5574f4fb051f2bb10ab048fd2adb821`。
- [x] post-live open-order safety check 已通过：远端 run
  `platform-open-orders-check-post-live-20260625T185510Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-post-live-20260625T185510Z/`；
  `status=passed`、`open_order_count=0`、`open_order_ids=[]`，SDK response projection sha256
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`；report sha256
  `c6ebf481c9605b60fdfd90e6023f55e265fbe3e76bf2f9fd2a57d92f2b47a597`，bundle manifest sha256
  `2f072870ec67131d3c33f6990fd21e8c7065f84e1a0db6a3d11660ec594edef4`。
- [x] post-live account snapshot 已拉回用于 residual exposure 证据：远端 run
  `post-live-account-snapshot-20260625T185752Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/post-live-account-snapshot-20260625T185752Z/`。
  Data API positions queried OK，`data_position_count=0`、`data_total_value_usdc=0`、
  `data_positions_usage=ReconciliationInputOnly`、
  `position_count=0`、`total_value_usdc=0`。`account_snapshot.json` sha256
  `5cc6abf8a5653de7ec1c8fe0ea71c411054b244af7ddc8261577e1f18141a31e`，
  `position_value_snapshot.json` sha256
  `5ec79a228f02f98c3e67a3ceaadddb4aef83bdfab64337e9ff887bc601c6edb1`，
  bundle manifest sha256 `eab791e56c4ca3a42b76085bd53ca5cf1e272602960313eb5fe9d8bafc590890`。
- [x] 当时失败归因（历史）：本轮不是 venue-dust partial BUY cleanup 路径复发。`sample-0001` clean SELL
  accepted，platform order id
  `0x30ad9e19bdb4ef454c68bf61a9d75d84591ffb6296dae383c1e285b595a5cde1`，随后 cleanup cancel
  返回 `SdkRejected`，runner 因 clean SELL accepted 后 cancel 未被接受而 fail closed。后续只读
  open-order/account checks 显示平台 open orders 和 Data API positions 均为 `0`，但该后验状态不能把
  当时 live run 改判为 passed。
- [x] cleanup-audit-only 方案复审已通过：样本成功终点收敛为 first same-asset SELL clean accepted，
  accepted 后成交/cancel/open-order audit 降级为 manual review evidence。
- [x] 本地 TDD 修复已完成：runner clean-accept 分支不再因 SELL cleanup cancel rejected / `SdkError` /
  matched-cancel / post-cancel open SELL 非零 / open-order audit 查询失败而 fail closed；artifact
  validator/final writer 接受 accepted 后非理想 cleanup audit；CLI 默认 cadence 改为 `20ms` / `100ms` /
  `60000ms`。
- [x] 本地 focused/full gates 已通过：`platform_sellable_maturity_runner`、`platform_sellable_maturity`、
  `cli_platform_sellable_maturity`、`platform_open_order_check`；以及
  `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`、
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`、`git diff --check`
  三条 full local gate。
- [x] cleanup-audit-only 实现 GPT-5.5/xhigh 只读复审已通过：实现复审确认 clean accept 后 cancel /
  open-order audit 不再写入 maturity `fail_closed_reasons`，validator 仅保留关键字段/时间线/非 blank
  校验，BUY partial cleanup venue-dust strict path 未被放松；文档/测试复审确认 handoff 不再保留旧 hard
  gate 口径。
- [x] cleanup-audit-only 修复 commit 已创建并 push：`865e0d87f540727740628a54e06e1856abf96291`。
- [x] 用户已批准 cleanup-audit-only 修复后的 fresh build、binary-only deploy、远端
  `--no-live-funds` gate，并在全部通过后执行真实资金 probe。
- [x] fresh release build 已按授权执行并通过：build HEAD
  `865e0d87f540727740628a54e06e1856abf96291`，dirty state `clean`，
  git diff provenance sha256
  `0aeb355a59f704c75d97ce6d3c7cf2bf0add1a1b85ca4c223d83293e4688e2e5`；release binary sha256
  `7473f6c9a5dc8a1a040a45ce1e3844ee20b3cb95b6a765f248df8f58e52c90e6`，config sha256
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`，model tree sha256
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`。
- [x] binary-only deploy 已通过：deploy id
  `r5-865e0d8-binary-deploy-20260626T033132Z`；脚本只复制 release binary、config 和 model tree，
  远端 binary/config/model sha 校验通过；`r5-actor-rehearsal` 输出 validator/artifact_validator
  passed，`sdk_post_attempted=false`、`sdk_cancel_attempted=false`；`no_submit_rehearsal_report.json`
  sha256 `1232b86dc2e1554411ca9b98c6820f6c83bfa09304994d05398c48f1f5fcd25e`。
- [x] no-live 前只读 open-order gate 已通过：远端 run
  `platform-open-orders-check-20260626T033225Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-20260626T033225Z/`；
  `status=passed`、`open_order_count=0`、`open_order_ids=[]`、`sdk_post_attempted=false`、
  `sdk_cancel_attempted=false`。SDK response projection sha256
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`，report sha256
  `39fe0e4abf69cb57964a14428b30e94605657cf07891d1cb3efa1652308ace08`，bundle manifest sha256
  `d58dd0cddcd5190fc7e3b2ab837bdbcf9509e5f8b597f17edbdeffd2977245a5`。
- [x] production `--no-live-funds` gate 已通过：远端 run
  `platform-sellable-maturity-no-live-20260626T033248Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260626T033248Z/`；
  `status=no_live_funds_passed`、`no_live_funds=true`、`sdk_post_attempt_count=0`、
  `sdk_cancel_attempt_count=0`、`fail_closed_reasons=[]`。gate report sha256
  `8e17fda21dbe170a4062eadafe3783b3158eb1d42a364d67b19c084cc0e38de9`，bundle manifest sha256
  `9315ab992e3aa2e5db58ea0b73e099c73ae5b0b0f3be81ea1dc9096c62372010`。
- [x] live 前只读 open-order gate 已通过：远端 run
  `platform-open-orders-check-pre-live-20260626T033315Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-pre-live-20260626T033315Z/`；
  `status=passed`、`open_order_count=0`、`open_order_ids=[]`、`sdk_post_attempted=false`、
  `sdk_cancel_attempted=false`。report sha256
  `f52bf673f68c5135868be30144c14c653abe3be927dcdd8571201c38cf930de8`，bundle manifest sha256
  `3eb3a2100345417186019311e3863e124f876a1a714a61be8a506c4bbf797377`。
- [x] renewed 真实资金 probe 已按授权执行并 fail closed：远端 run
  `platform-sellable-maturity-live-20260626T033334Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260626T033334Z/`；
  CLI summary：`status=FailClosed`、`valid_samples=11`、`sdk_post_attempts=271`、
  `sdk_cancel_attempts=12`、`hard_reasons=1`。gate report：`status=fail_closed`、
  `valid_sample_count=11`；fail reason：
  `sample-0012:buy submit was not accepted`。gate report sha256
  `393ea38e0c69a4816deaed7ed70272d8f2910fb13743805af2651ab9d08560e3`，fail trace sha256
  `1e12de7b19e452f8eaf570e5af86974b91dfae619540f87b5071d4ae03f9b056`，bundle manifest sha256
  `939c620dadea9b1e4d2186289532cff4be4a98b22bc44b1147c4ab0d08a0e969`。
- [x] 本轮有效样本和排除样本证据：`sample-0000` 到 `sample-0010` 共 `11` 个 valid sample；
  `first_clean_accept_ms` 分别为 `1964,2495,1828,2451,2307,821,2139,1016,1887,1396,1176`，
  median `1887ms`，max `2495ms`。`sample-0011` 为 partial BUY，fill `4.990929`，
  residual `0.009071`，按 venue-dust terminal 语义写 invalid sample 并重采样；该路径没有 fail closed。
- [x] post-live open-order safety check 已通过：远端 run
  `platform-open-orders-check-post-live-20260626T040306Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-post-live-20260626T040306Z/`；
  `status=passed`、`open_order_count=0`、`open_order_ids=[]`，SDK response projection sha256
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`；report sha256
  `c3aea890b062d30b0ac41c6aec90814614a1b250766a6bf60d4cea4885dc5352`，bundle manifest sha256
  `2721853d272bb323751419c64597dccbc5e7803c2ace56d6da049cb1c71690be`。
- [x] post-live account snapshot 已拉回用于 residual exposure 证据：远端 run
  `post-live-account-snapshot-20260626T040306Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/post-live-account-snapshot-20260626T040306Z/`。
  Data API positions queried OK，`data_position_count=0`、`data_total_value_usdc=0`、
  `position_count=0`、`total_value_usdc=0`，wallet balance 为 `75260557 raw_6_decimal_usdc`。
  `account_snapshot.json` sha256
  `65d146cf488633e6780a810446c8d61d4f4c0883c1155d627bba4e6a5cfceda4`，
  `position_value_snapshot.json` sha256
  `5ec79a228f02f98c3e67a3ceaadddb4aef83bdfab64337e9ff887bc601c6edb1`，bundle manifest sha256
  `fd88fe45ad9c223e9dbba8756f0cddd33584978c14bdf5e004b67b677eedc670`。
- [x] 当前失败归因边界：本轮不是 clean SELL accepted 后 cleanup cancel hard gate 复发，也不是
  venue-dust partial BUY cleanup 复发。`sample-0012` BUY 候选本地 pre-submit gate 通过：
  market `btc-updown-5m-1782446400`、UP、best ask `0.47`、buy price `0.47`、size `5`、
  notional `2.35`，但 `submit_limit_order` 返回非 `SdkAccepted`。当前 fail trace 只保留
  `buy_candidates`，没有持久化 BUY submit 的 `OrderAdapterReport` / SDK reject 原文。operator
  在平台账户观察到提示 `limit buy up failed`，与 artifact 中 `sample-0012` 的 UP BUY non-accepted
  方向一致；但该提示目前不是 SDK artifact 原文，因此下一步 root-cause review 必须先补 BUY reject
  evidence 落盘缺口。
- [x] BUY submit non-accepted 本地修复已实现并完成 full local test：`OrderAdapterObservation`
  新增 `post_response_success`、`sdk_http_status`、`sdk_status_body`、`retry_after_seconds` evidence；
  `platform_sellable_maturity_gate_report.json` 和 `platform_sellable_maturity_fail_closed_trace.json`
  新增 `buy_submit_attempts`，每次 BUY submit attempt 都保留 normalized `OrderAdapterReport`。
  runner 仅对白名单 transient reject 做 bounded retry：无 `platform_order_id`、无 `trade_ids`、无
  `transaction_hashes`，且错误为 `MARKET_NOT_READY`、HTTP `425`、HTTP `429` 或 HTTP `500`
  exact `could not insert order`。空/`UNKNOWN` status 但没有明确 transient evidence 时不 retry。BUY
  `not enough balance / allowance`、认证/签名/owner/signer/geoblock/banned、tick/min size/price/expiration/
  duplicate、restricted mode / post-only / cancel-only / trading disabled（即使带 `retry_after_seconds`）、
  带落单证据 reject、普通 timeout / ambiguous `SdkError` 均不 retry。run-level BUY intent
  notional cap 只在 BUY `SdkAccepted` 且有非空 platform order id 后累计，rejected BUY 不消耗 cap。
- [x] 本地验证：`cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test
  platform_sellable_maturity_runner --quiet` 通过 `41/41`；`--test sdk_order_adapter --quiet` 通过
  `16/16`；`--test platform_sellable_maturity --quiet` 通过 `8/8`；`--test
  cli_platform_sellable_maturity --quiet` 通过 `3/3`；`cargo test --manifest-path
  poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet` 全包通过。
- [x] GPT-5.5/xhigh 只读 review 已通过：文档边界 PASS，代码 review PASS；`cancel-only` no-retry
  minor 已补测试矩阵并完成增量复核。
- [x] 用户批准执行 commit `970bd20ab693bb1a7a29923af62cd485a1ab5bab` 的 fresh build、
  binary-only deploy、远端 `--no-live-funds` gate；全部通过后执行真实资金 probe。执行结果：
  fresh build 通过，binary sha256 =
  `acde204b0336d74793b0e61eb387ce224f8b3ef1c18debc0e31157da557fb565`；deploy id =
  `r5-970bd20-binary-deploy-20260626T053539Z`，dry-run report sha256 =
  `303771215e7b8c44acb8692148990371cb2d5591a1b134aed511b69b82bed00b`；no-live 前 open-order
  check `platform-open-orders-check-20260626T053624Z` 通过，report sha256 =
  `16b13ef379542540449097ff0f12ab83db584f73640fe9ed75ab939cac0e6a4e`；no-live gate
  `platform-sellable-maturity-no-live-20260626T053651Z` 通过，gate report sha256 =
  `741b3b457373271bb2c160c8aa1eee238a4daa40ad8b80bcfef5d3014d15f8d2`；live 前 open-order
  check `platform-open-orders-check-pre-live-20260626T053718Z` 通过，report sha256 =
  `8fd72b5481e6a0dbf8a254bbe8d5f83ffbb97449524f8190cffa206bd4da6f69`。
- [x] 本次真实资金 probe 已执行并 fail-closed：run id
  `platform-sellable-maturity-live-20260626T053750Z`，本地 pullback
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260626T053750Z/`；
  CLI summary `status=FailClosed`、`valid_samples=3`、SDK post/cancel `55/4`、`hard_reasons=1`；
  hard reason `sample-0003:BUY cleanup cancel after insufficient fill was not accepted`。gate report sha256 =
  `77bc6e454783bcad62d3bd23b345d333c1c4181b0ab9cbc7e34c927f2f16e724`，fail trace sha256 =
  `c771ecc6f27d695b64916a8d00ec364c0f36a9708077839ea8c1444f66b9acef`。`sample-0003`
  BUY submit accepted：order id
  `0x24968d855b840c810084c76bb9a36f0e56fb4431a36d99e1f379a34d217f54cd`，DOWN，price `0.52`，
  filled `3.3/5`，tx `0x869c7063b8e686df29717c3028acb16e7b4968a1ee55e9f7c9fdd8267f6fb99a`。
- [x] Post-live safety checks 已完成：open-order check
  `platform-open-orders-check-post-live-20260626T054054Z` 通过，open orders `0`，report sha256 =
  `4d08801bdd6dea621405b7877357790e84ebf6f0d788222077427104c9bd8ab2`；account snapshot
  `post-live-account-snapshot-20260626T054201Z` 已拉回，account snapshot sha256 =
  `b0d7feb3a62fa253a07c03b36ba0dd86051cfa3f406377f69352f7397addd867`，position/value snapshot
  sha256 = `613036a839ffd5fd8f7906075aa0534d611188277c70e846e69fa5041cd54aa3`，
  reconciliation report sha256 = `72570e0ab496ffb169960158ebc6e1dc599af6da033679f509b7d66eda28ff7f`。
  Snapshot 显示 `open_order_count=0`，但 `data_position_count=2`、`data_total_value_usdc=4.1245`，
  positions 为 UP `5` shares 和 DOWN `3.3` shares；`allows_new_orders=false`。
- [x] 随后 0B artifact-smoke + streaming persistence 修复、one-sample artifact smoke、fresh build、
  binary-only deploy、production `--no-live-funds` gate 均已完成并通过；用户批准后已执行正式
  30 有效样本真实资金 probe `platform-sellable-maturity-live-20260626T133250Z`。
- [x] 最新正式真实资金 probe 已拉回并复核：`valid_sample_count=30`，JSONL/stream/summary 可复核；
  但 gate status 为 `fail_closed`，fail reason 是
  `platform_sellable_maturity_samples.csv` CSV writer validation error：found record with `50` fields,
  but the previous record has `51` fields。因此不能标记为 passed。
- [x] 最新 post-run open-order check `platform-open-orders-check-post-30probe-20260626T144528Z`
  通过，`open_order_count=0`；post-live account snapshot `post-live-account-snapshot-20260626T145200Z`
  显示 `open_order_count=0`，但 `data_position_count=2`、`data_total_value_usdc=5`，
  reconciliation `allows_new_orders=false`。
- 当前 cursor：不得继续真实资金 probe。下一步必须先 root-cause / fix
  `platform_sellable_maturity_samples.csv` 字段数不一致，并复核 sample CSV/JSONL schema 对齐。
