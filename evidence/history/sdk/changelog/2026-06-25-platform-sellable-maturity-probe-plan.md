# platform-sellable maturity probe changelog

> **状态：current active changelog。创建日期：2026-06-25 JST。**
> 对应 active authoritative plan：
> `poly-arb-ai/sdk-live-trade-docs/plan/2026-06-25-platform-sellable-maturity-probe-plan.md`。
> 旧 `2nd-moneyrun-bugs-fix.md` plan/changelog 已归档，只作为历史真实资金 run、Phase 9/10 blocker
> 与 platform-sellable maturity 背景证据。

## 2026-06-26 formal 30-sample live probe execution

用户批准执行正式 `30` 有效样本真实资金 probe。本轮已执行并拉回产物，但整体 gate **未通过**。

Pre-run open-order gate：

- run id：`platform-open-orders-check-pre-30probe-20260626T133234Z`
- status：`passed`
- `open_order_count=0`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-pre-30probe-20260626T133234Z/`
- report sha256：
  `c9d6fc5ffc323475e93eb2e24c873ec1224c7986764279cf64d1432ee4d2a8a8`
- bundle manifest sha256：
  `69d1122826c9d03a1a035fad97c46fc5b7540e3c9f9d87a0fdf7ea033e610163`

Formal live probe：

- command target run id：`platform-sellable-maturity-live-20260626T133250Z`
- program run id：`platform-sellable-maturity-1782480772434`
- status：`FailClosed`
- CLI summary：`valid_samples=30`、SDK post/cancel `672/32`。
- gate report：`status=fail_closed`、`required_valid_samples=30`、`valid_sample_count=30`、
  `sdk_post_attempt_count=672`、`sdk_cancel_attempt_count=32`、`heartbeat_attempt_count=77`、
  `under_min_market_cleanup_attempt_count=0`。
- fail-closed reason：
  `artifact_writer_validation_error:write .../platform_sellable_maturity_samples.csv: CSV error: found record with 50 fields, but the previous record has 51 fields`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260626T133250Z/`
- JSONL/stream 行数：`samples.jsonl=32`、`samples.stream.jsonl=32`、`probes.jsonl=640`、
  `probes.stream.jsonl=640`、`events.stream.jsonl=670`、`buy_candidates.stream.jsonl=32`、
  `buy_submit_attempts.stream.jsonl=32`、`market_discovery_wait_events.stream.jsonl=828`。
- 样本口径：`valid=30`、`invalid=2`。两条 invalid 均为
  `buy_fill_size_below_configured_probe_size`：`sample-0017` fill `4.999165` 且
  venue dust terminal；`sample-0019` fill `0`。
- Per-sample cleanup audit 里，valid `sample-0003` 和 `sample-0023` 的
  `post_cancel_open_orders_count=1`；这只代表样本内 cleanup audit evidence，不等同于运行后最终平台
  open-order 状态。独立 post-run open-order gate 为 `open_order_count=0`。
- Summary metrics：`clean_accept_ms` count `30`、mean `1989.1667`、median `1939`、p75 `2510`、
  p90 `2676`、p95 `3357`、min `851`、max `3426`；`first_reject_ms` count `30`、mean
  `85.4`、median `80`、p75 `96`、p90 `107`、p95 `108`、min `71`、max `122`。
- gate report sha256：
  `d2a9427f0cf10b9649224c172d16838ea793f6bb8bb18109402e5877daff40a9`
- fail trace sha256：
  `e74fd13533679dd70b28b1e53df833bb8ded557ba90706ed9c6bfc0a0b0a7f55`
- summary sha256：
  `f697182c4537b14b4de871995d86257df6ca8bdf6d1c506624939b73d44f5acf`
- samples JSONL sha256：
  `9f581d1e0a1951af413f987c3e2a9caf03cf6227f5367f08ad1868a381060375`
- probes JSONL sha256：
  `54542f5a1182f8deffde3b925194a156919f2cc75fdacb0833a1c48aa9c1aed4`
- bundle manifest sha256：
  `fb8d3c1c4aa44992b7a7fb8701835ec7336f57535a6084b3c15a6501c96cc45a`

Post-run open-order gate：

- run id：`platform-open-orders-check-post-30probe-20260626T144528Z`
- status：`passed`
- `open_order_count=0`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-post-30probe-20260626T144528Z/`
- report sha256：
  `a5a8103ef751226041082d8d1e4408e2239b82c7689802018d62ee554f695f49`
- bundle manifest sha256：
  `7e53c66ae78918e59c49ddecefa42c253cf0b065ab0be294db8cc7f38213ee89`

Post-live account snapshot：

- run id：`post-live-account-snapshot-20260626T145200Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/post-live-account-snapshot-20260626T145200Z/`
- `remote-dry-run` account snapshot `fail_closed=true`，reason
  `clob_trades_query_failed:sdk_internal`。
- Snapshot：`open_order_count=0`，`data_position_count=2`、`data_total_value_usdc=5`。
  DOWN asset
  `40583622375196072489292938114999321362619885368738391817601948363698100270887` size `5`
  value `0.025`；UP asset
  `89970116419305287743685609967558456551325862000197769271435214920374609038052` size `5`
  value `4.975`。
- Reconciliation：`allows_new_orders=false`、`open_order_safe=true`、
  `position_value_safe=false`、`current_exposure_safe=false`、`trade_history_unavailable=true`、
  `audit_complete=false`；reasons 包含 `data_position_up_mismatch`、`data_position_down_mismatch`、
  `trade_history_unavailable_blocks_new_orders` 和 `audit_incomplete`。
- `account_snapshot.json` sha256：
  `b885746c47c5ed1a1baf6c00ab1f5d77fe3a98989e0ff36d2299873e835198eb`
- `open_order_snapshot.json` sha256：
  `ac1166c5ae8e447369bfed090f2071a3eb8982f467cda62894e6677a11bb5dfb`
- `position_value_snapshot.json` sha256：
  `b9748c18c1a42af4c79cf5e377762cce86ebae53799d211bac7358bceda5104f`
- `reconciliation_report.json` sha256：
  `b8427657ae369811e8575f1e6479f469dd525b7c510137b83785dd4a1702fd79`
- bundle manifest sha256：
  `ff1281ab72b9df886aa14740be5a364f580f1a662342a1df5445457dff089b84`

当前边界：本轮 30 个有效样本数据已经在 JSONL/stream/summary 中可复核，但正式 gate 因
`platform_sellable_maturity_samples.csv` 字段数不一致 fail-closed，不能标记为 passed。运行后 open
orders 为 `0`，但 account snapshot 显示 Data API positions 且 reconciliation `allows_new_orders=false`。
不得继续真实资金 probe；下一步先 root-cause/fix CSV writer schema 对齐。

## 2026-06-26 artifact-smoke + streaming persistence 修复方案落盘

根据用户要求，已在 active plan 新增
`## 0B. 2026-06-26 artifact-smoke + streaming persistence 修复方案`。本次记录的是待审查方案，
尚未修改 Rust 代码、尚未 fresh build、尚未 binary deploy、尚未执行远端 `--no-live-funds` gate，也不授权
真实资金 probe。

方案目标：

- 新增 `--artifact-smoke-valid-samples 1`，用于单样本 artifact smoke，验证一条 valid sample 能持续写入并
  最终落盘。
- 正式 platform-sellable maturity probe 默认仍要求 `30/30` valid samples；未启用 smoke 时
  `--valid-samples 1` 继续拒绝，避免把正式目标降级成单样本。
- smoke mode 下 `--valid-samples` 只能省略或保持默认 `30`，由 `--artifact-smoke-valid-samples 1` 覆盖为
  effective `1`；若显式传非默认 `--valid-samples`，必须 fail closed。
- 将 probe / sample / buy evidence 增加 forensic stream 持续写入，覆盖进程中断、final writer validation
  failure 或终端断开后的可复核性缺口。
- SELL post response 判定 `clean_sell_accepted=true` 时，必须立即写入 `sell_probe_response` event stream；
  cleanup/cancel/open-order audit 另写后续 event 或最终 probe row，避免 accepted 后 cleanup 前崩溃导致核心
  maturity 时点没有落盘证据。
- canonical final writer 仍保持 strict validate-before-write；streaming 文件只作为 forensic evidence，不冒充
  正式 success artifact。
- `--no-live-funds` 仍不采样、不发 BUY/SELL、不产生 valid sample。

方案执行边界：

- 待审查文件：active plan 本节、active changelog 本节。
- 代码目标：
  `poly-arb-ai/rust/sdk-live-trade/src/platform_sellable_maturity.rs`、
  `poly-arb-ai/rust/sdk-live-trade/src/platform_sellable_maturity_runner.rs` 和 CLI 入口。
- 测试目标：
  `poly-arb-ai/rust/sdk-live-trade/tests/cli_platform_sellable_maturity.rs`、
  `poly-arb-ai/rust/sdk-live-trade/tests/platform_sellable_maturity.rs`、
  `poly-arb-ai/rust/sdk-live-trade/tests/platform_sellable_maturity_runner.rs`。
- 命令手册目标：实现阶段同步更新 `lastest-command.md`，加入 artifact smoke 命令、streaming artifact 文件和
  验收判据。
- 不改 SDK adapter，除非实现阶段测试证明 runner / artifact 层无法覆盖；不新增 raw REST、manual signing 或
  shadow implementation。

方案测试边界：

- CLI / input validation 覆盖 `--artifact-smoke-valid-samples 1`、非法 smoke 值、非 smoke
  `--valid-samples 1` 拒绝。
- Config / writer validation 覆盖正式 `30` 样本和 smoke `1` 样本的合法/非法组合。
- Runner streaming persistence 覆盖单样本 smoke 成功、final writer validation failure 时 stream 已存在、
  SELL response clean accept 立即写 event、streaming append/flush failure 停止后续采样并 fail closed、多次
  SELL probe 顺序写入、stream/final artifact 文件级 create-new/no-overwrite。
- No-live gate 覆盖不采样、不写 sample/probe stream、不触发 SDK post/cancel。

验收边界：

- 方案必须先经 GPT-5.5/xhigh 只读 subagents 审查；不通过则先修正文档方案。
- 方案审查通过后才执行本地代码修复。
- 实现完成后再次派生 subagents 审查；审查通过后，按用户授权只执行 fresh build、binary deploy、远端
  `--no-live-funds` gate。
- fresh build 前必须先同步 active plan / changelog / `lastest-command.md`，创建 commit 并 push，确认
  worktree 干净且 `HEAD == @{u}`，并记录 `git status --short --branch`、`HEAD` 和 `@{u}` 证据；禁止用
  未提交或未同步的新代码进入 binary deploy / remote gate。
- 本轮明确不执行真实资金 probe。

## 2026-06-26 artifact-smoke + streaming persistence 本地实现

根据用户批准和方案 subagent 复审通过结果，已完成本地实现。本节记录本地代码/测试收口；后续 fresh build、
binary deploy、远端 `--no-live-funds` gate 执行证据见下一节。真实资金 probe 仍不执行。

实现内容：

- CLI 新增 `--artifact-smoke-valid-samples`。当前只允许值 `1`；smoke mode 下 `--valid-samples` 只能省略或
  保持默认 `30`，由 smoke flag 覆盖成 effective `1`。非 smoke mode 仍强制正式目标 `30`。
- `PlatformSellableMaturityConfig` 新增 `artifact_smoke`；default config 仍是正式 `30`，`artifact_smoke_one()`
  只允许 one-sample smoke。
- run report、gate report、fail trace 和 final summary 新增 `artifact_smoke` / `required_valid_samples`，
  防止把 smoke `1/1` 误解为正式 `30/30`。
- live-funds path 新增 forensic stream writer：
  `platform_sellable_maturity_stream_manifest.json`、
  `platform_sellable_maturity_events.stream.jsonl`、
  `platform_sellable_maturity_probes.stream.jsonl`、
  `platform_sellable_maturity_samples.stream.jsonl`、
  `platform_sellable_maturity_buy_candidates.stream.jsonl`、
  `platform_sellable_maturity_buy_submit_attempts.stream.jsonl` 和
  `platform_sellable_maturity_market_discovery_wait_events.stream.jsonl`。
- SELL post response 立即写 `sell_probe_response` event；clean accepted 后 cleanup audit 再写
  `sell_probe_cleanup_audit` event / final probe stream row。
- streaming append/flush failure 写入 `streaming_artifact_write_error:{...}`，停止后续采样并尽力写
  gate report / fail trace；若 BUY 已被平台 accepted 后 buy-submit stream 写失败，会先 best-effort cancel
  accepted BUY，再 fail closed。
- `--no-live-funds` 仍不采样、不发 BUY/SELL、不初始化 sample/probe/event stream。

TDD / focused verification：

- RED 已确认：
  - CLI help 不暴露 `--artifact-smoke-valid-samples`，smoke + explicit non-default `--valid-samples` 未按预期拒绝。
  - `PlatformSellableMaturityConfig::artifact_smoke_one()`、stream 文件常量、runner report/input 字段不存在。
- GREEN 已确认：
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test cli_platform_sellable_maturity --quiet`
    passed 6/6。
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity --quiet`
    passed 9/9。
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner --quiet`
    passed 54/54。
- 实现复审发现的测试缺口已补齐：
  - CLI 覆盖 `--artifact-smoke-valid-samples 0/2/30` 拒绝、非 smoke `--valid-samples 1` 早期拒绝。
  - runner 覆盖 final writer validation failure 时 stream probe/sample rows 已存在。
  - runner 覆盖多次 SELL probe stream row 按完成顺序写入。
  - runner 覆盖 stream file-level create-new/no-overwrite 冲突时 fail-closed before SDK submit。
- Full local gate 已通过：
  - `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
  - `git diff --check`
- GPT-5.5/xhigh 实现复审已通过：
  - CLI / smoke / config 语义 review PASS。
  - streaming persistence / live order safety review 初次要求补 final-writer stream rows、probe stream 顺序和
    file create-new 冲突测试；补齐后 PASS。
  - docs / tests / deploy boundary review 初次要求补 CLI invalid combo、runner stream 必测项，二次要求修正
    `lastest-command.md` 顶部当前状态并把 `git diff --check` 列入 full gate；补齐后 PASS。

## 2026-06-26 artifact-smoke + streaming persistence fresh build / deploy / no-live

根据用户授权，在 0B 实现复审通过后已执行 fresh release build、binary-only deploy、远端 production
`--no-live-funds` gate 和产物拉回检查。本轮按用户要求不执行 artifact smoke，不执行真实资金 probe。

Commit/push gate：

- commit：`bb21d140cb373bd9b44f9c265e9314b4116da07f`
- `git status --short --branch`：`## sdk-live-trade...origin/sdk-live-trade`
- `HEAD == @{u}`

Fresh release build：

- dirty state：`clean`
- git diff provenance sha256：
  `7b44ad9c8bd7bb9b2084e2aa0d9a2c106c30db014af8004d2a6941eb46a51a3d`
- release binary sha256：
  `76fba30568449546584504e0a092a9c2c865431ee0262ad04f101ddad30cd0fa`
- config sha256：
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`
- model tree manifest sha256：
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`

Binary-only deploy：

- deploy id：`r5-bb21d14-binary-deploy-20260626T131826Z`
- remote binary/config/model sha 校验通过
- `r5-actor-rehearsal` validator/artifact_validator passed
- `sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- no-submit rehearsal report sha256：
  `4930961849eca433ef6bf1dfc0fcecbfc830429be41a0c707ef3ac6169c2385c`
- deploy pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/deployments/pullback/r5-bb21d14-binary-deploy-20260626T131826Z/dry-run/`
- artifact bundle manifest sha256：
  `dfa2e689798b7c7706f0fdedce9824c8d6dd01a73b8e6640f9e7355eb6e8c5a9`

Production `--no-live-funds` gate：

- run id：`platform-sellable-maturity-no-live-20260626T131913Z`
- CLI summary：`status=NoLiveFundsPassed`、`valid_samples=0`、`sdk_post_attempts=0`、
  `sdk_cancel_attempts=0`、`heartbeat_attempts=0`、`hard_reasons=0`
- gate report：`status="no_live_funds_passed"`、`no_live_funds=true`、`artifact_smoke=false`、
  `required_valid_samples=30`、`valid_sample_count=0`、`sdk_post_attempt_count=0`、
  `sdk_cancel_attempt_count=0`、`heartbeat_attempt_count=0`、`fail_closed_reasons=[]`
- stream files count：`0`
- no-live pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260626T131913Z/`
- gate report sha256：
  `4618e29a771a8e7c42c4a15db3f0a413fdd963b61aae1cfe3c6ba7984fca08b0`
- artifact bundle manifest sha256：
  `baa50d21eda1016e555abc1eb19f8834a48b91bda8dacdade85b9ad31cb958d7`

## 2026-06-26 one-sample artifact smoke live-funds execution

用户随后明确要求执行真实资金一次采样，验证数据是否正确持续写入落盘。本轮只执行 one-sample artifact
smoke，不执行正式 `30/30` 真实资金 probe。

前置只读 open-order gate：

- run id：`platform-open-orders-check-pre-smoke-20260626T132716Z`
- status：`passed`
- `open_order_count=0`、`open_order_ids=[]`
- `sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-pre-smoke-20260626T132716Z/`
- report sha256：
  `2e0a3a35c14d940f2aab33cd1b25670d2467ce77fc0e991147d8dcef8ab5e8d5`

Artifact smoke live-funds run：

- run id：`platform-sellable-maturity-artifact-smoke-20260626T132728Z`
- CLI summary：`status=Passed`、`artifact_smoke=true`、`required_valid_samples=1`、`valid_samples=1`、
  `sdk_post_attempts=27`、`sdk_cancel_attempts=1`、`hard_reasons=0`
- gate report：`status="passed"`、`no_live_funds=false`、`artifact_smoke=true`、
  `required_valid_samples=1`、`valid_sample_count=1`、`sdk_post_attempt_count=27`、
  `sdk_cancel_attempt_count=1`、`heartbeat_attempt_count=2`、`fail_closed_reasons=[]`
- final/stream 行数一致：`platform_sellable_maturity_probes.jsonl=26`、
  `platform_sellable_maturity_probes.stream.jsonl=26`、`platform_sellable_maturity_samples.jsonl=1`、
  `platform_sellable_maturity_samples.stream.jsonl=1`
- summary `metrics.clean_accept_ms.count=1`，mean/median/min/max 均为 `2569ms`；
  `metrics.first_reject_ms.count=1`，mean/median/min/max 均为 `70ms`
- final sample：`valid=true`、`first_reject_ms=70`、`first_clean_accept_ms=2569`、
  `attempt_count_to_clean_accept=26`、`post_cancel_open_orders_count=0`、
  `open_order_clear_proof="clob_open_sell_orders_empty"`
- clean accepted SELL response event 已在 cleanup audit 前写出：events stream 第 `26` 行是
  `event_type="sell_probe_response"`、`clean_sell_accepted=true`，第 `27` 行是
  `event_type="sell_probe_cleanup_audit"`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-artifact-smoke-20260626T132728Z/`
- gate report sha256：
  `b5902438cfeba5469c173f2ddf5cabc8d17cf249926d2e54137924ec4c1e0adf`
- summary sha256：
  `192e2df6a06759b38a9fad92e1fb3313a2e76c8e47017fc749ff2a539590a8f2`
- probes JSONL sha256：
  `76bb1d6af23ac4869b0408580a10774fcebbd7c6d72e5fca4d26dca6a1ef19b4`
- samples JSONL sha256：
  `fd64320ee51bae4c1f3315ec5c82fcc02a9113bc8febdde6bf0b1e115edccfa7`
- events stream sha256：
  `bc7a13515ca544717281e08b2dc6114da35cd0e716a32106714779b2b80c2b4a`
- artifact bundle manifest sha256：
  `fa86de220ac0794c6bf78c69ab323e60764a19b4ded702fbceec51c3abf399cd`

Post-smoke 只读 open-order gate：

- run id：`platform-open-orders-check-post-smoke-20260626T132750Z`
- status：`passed`
- `open_order_count=0`、`open_order_ids=[]`
- `sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-post-smoke-20260626T132750Z/`
- report sha256：
  `77b949c8f633629d7661b9e535ca2352ca016e694483891e7b870481662bd204`

## 2026-06-26 JST `138bbe7` renewed live execution

用户批准执行 fresh build、binary deploy、远端 `--no-live-funds` gate；这些全部通过后执行真实资金
probe。本轮执行 commit `138bbe70db2c3e67ff70506763fa5e99207d8499`。

Fresh release build：

- dirty state：`clean`
- git diff provenance sha256：`bdb08a790ad1a206ac8d8df577028f29bd5f53509cdcae2c156513fe1a314777`
- release binary sha256：
  `77832e5cd7ddc70356c26abe11e6afed392898e61a034e667d49568758a6336f`
- config sha256：
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`
- model tree manifest sha256：
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`

Binary-only deploy：

- deploy id：`r5-138bbe7-binary-deploy-20260626T092307Z`
- remote binary/config/model sha 校验通过
- `r5-actor-rehearsal` validator/artifact_validator passed
- `sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- no-submit rehearsal report sha256：
  `8817f008ab9275dba5f8b67dd9c90fd8c0222066781a35ada6afb63008c5317e`

No-live 前只读 open-order gate：

- run id：`platform-open-orders-check-20260626T092359Z`
- status：`passed`
- `open_order_count=0`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-20260626T092359Z/`
- report sha256：
  `9ae89416eeac5ae23c241f9f655c2b6f623d7380718bb907a776d4796b6e1be0`

Production `--no-live-funds` gate：

- run id：`platform-sellable-maturity-no-live-20260626T092420Z`
- status：`NoLiveFundsPassed`
- `valid_samples=0`、SDK post/cancel `0/0`、heartbeat `0`、under-min market cleanup `0`、`hard_reasons=0`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260626T092420Z/`
- gate report sha256：
  `0f59f6ceb47a3a6ac42ff57b779ebe66a329eafa0f902f53f98250ac2493f70b`

Live 前只读 open-order gate：

- run id：`platform-open-orders-check-pre-live-20260626T092444Z`
- status：`passed`
- `open_order_count=0`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-pre-live-20260626T092444Z/`
- report sha256：
  `65e01e7c1e98a2d0b86f387b8f15a80fe344546c5c002c14a1935ebacc3b40a7`

真实资金 probe：

- run id：`platform-sellable-maturity-live-20260626T092500Z`
- exit code：`1`
- 最后错误：`clean accept must not include reject/error fields`
- stdout 显示已推进到最后阶段：
  `valid_sample 30/30 attempt_sample_index=30 start sample_id=sample-0030`，随后仍等待未采样 asset /
  active market，最终在 artifact writer/validator 阶段退出。
- 远端 run directory：
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/platform-sellable-maturity/platform-sellable-maturity-live-20260626T092500Z/`
  没有程序写出的 report / JSONL / CSV / fail trace；本地 pullback 只有 bundle manifest。
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260626T092500Z/`
- bundle manifest sha256：
  `900515a01002eb7c2815c8ace68c98d9fb9a988f99ffbb8c223eccecd824d51c`

失败初判：

- 这次不是 BUY submit reject 复发，也不是 partial BUY cleanup cancel blocker 复发。
- 错误来自本地 artifact validator：`clean_sell_accepted=true` 的 probe row 仍带了 reject/error 字段。
- 当前代码 clean accept 判定允许 `error_message=Some("")` 这类空字符串通过：
  `message.trim().is_empty()`；但 validator 要求 clean accepted probe 的 `reject_class`、`error_message`、
  platform balance/order amount/maturity reject 等字段必须全部为 `None` / false。
- 因错误发生在最终 artifact writer 前，本轮没有可信 gate report 可确认最终 `valid_sample_count`，
  不能把 stdout 的 `30/30 start` 当作已完成 30 个可审计有效样本。

Post-live safety checks：

- open-order check run id：`platform-open-orders-check-post-live-20260626T104042Z`
- status：`passed`
- `open_order_count=0`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-post-live-20260626T104042Z/`
- report sha256：
  `1372617ea10e3b7fe9dad439bfad3469a6a5a1b299d4039236198e108b0ec69d`

Post-live account snapshot：

- run id：`post-live-account-snapshot-20260626T104145Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/post-live-account-snapshot-20260626T104145Z/`
- `account_snapshot.json` sha256：
  `a9e6d6683d063f283b0936b56fe035a74dc90cf86dbc48595ecbb2ed397ef389`
- `open_order_snapshot.json` sha256：
  `ac1166c5ae8e447369bfed090f2071a3eb8982f467cda62894e6677a11bb5dfb`
- `position_value_snapshot.json` sha256：
  `1caecae36e41d47c3a7a52274af8a3121974e1e19fe4b576209a32fe71e2ee3f`
- `reconciliation_report.json` sha256：
  `b6cc1a59bcf86bc40db7d698fade40a6b6e6058f489655f6b65b49a33aae471e`
- `deployment_dry_run_report.json` sha256：
  `730e3ba2c921ae4a2130f437b9f67a2295f46586feb9d0f2030aa8b60558ddd1`
- Snapshot 显示 `open_order_count=0`，但 `data_position_count=1`、`data_total_value_usdc=2.525`，
  position asset
  `59830341499786524719805348626137282684786338528952843427767581011974806656368` size `5`。
- Reconciliation `allows_new_orders=false`，reasons 包含 `data_position_up_mismatch`、
  `data_position_value_total_mismatch`、`trade_history_unavailable_blocks_new_orders` 和 `audit_incomplete`。

事故当时边界：不得继续真实资金 probe。后续必须先做 root-cause review，修复 clean-accept artifact
normalization / fail-trace 持久化缺口，补本地验证与 review，commit/push 后重新走 fresh build、
binary-only deploy、production `--no-live-funds` gate、产物拉回检查和 renewed approval。当前本地修复进度见
下方“本地实现”记录。

## 2026-06-26 clean-accept artifact normalization / failure-evidence persistence 修复方案落盘

根据用户要求，已在 active plan 新增
`## 0A. 2026-06-26 clean-accept artifact normalization / failure-evidence persistence 修复方案`，并同步
`lastest-command.md` 的执行边界。本次只落盘修复方案和审查入口，不修改 Rust 代码，不授权 fresh build、
binary-only deploy、production `--no-live-funds` gate 或真实资金 probe。

方案目标：

- 修复 runner clean accepted SELL probe 的字段归一化：`SdkAccepted + platform_order_id + blank
  error_message` 可以作为 clean accept，但 final artifact row 必须把 blank `error_message` 清洗为 `None`，
  且不携带任何 reject-derived fields。
- 保持 artifact validator strict：raw clean accepted row 只要带 `reject_class`、`error_message`、
  maturity reject / balance / amount / non-maturity error evidence，仍必须拒绝。
- 修复 final writer validation failure 的证据丢失：`write_platform_sellable_maturity_artifacts(...)`
  报错时不得直接 `?` 返回；runner 必须转为 fail-closed，写出
  `platform_sellable_maturity_gate_report.json` 和
  `platform_sellable_maturity_fail_closed_trace.json`，并保留内存中的 probes / samples / counters /
  buy evidence。
- 不把 `platform-sellable-maturity-live-20260626T092500Z` 追认为有效 `30/30` artifact；该 run 只能作为
  “强推断已进入 30-sample final writer path，但无可审计样本落盘”的失败证据。

方案执行文件边界：

- 代码目标：`poly-arb-ai/rust/sdk-live-trade/src/platform_sellable_maturity_runner.rs`。
- 测试目标：
  `poly-arb-ai/rust/sdk-live-trade/tests/platform_sellable_maturity_runner.rs` 和
  `poly-arb-ai/rust/sdk-live-trade/tests/platform_sellable_maturity.rs`。
- 文档目标：active plan、active changelog、`lastest-command.md`。
- 不改 SDK adapter，除非后续测试证明 runner 局部清洗无法覆盖真实 adapter 输出。
- 不新增 raw REST、manual signing、shadow implementation 或 incremental canonical JSONL streaming。

方案测试边界：

- `platform_sellable_maturity_runner` 必须新增 blank `error_message` clean accept 回归测试，并断言 canonical
  probe row 的 `error_message=null`、reject fields 全空。
- `platform_sellable_maturity_runner` 必须新增 final writer validation failure persistence 测试，并断言 gate
  report / fail trace 均存在且 trace 包含已收集 probes / samples。
- `platform_sellable_maturity` 必须保持 strict validator，并补充 raw clean accepted probe 带
  `error_message=Some("")` 的负向覆盖。
- full local gate 仍是 `cargo fmt --check`、`cargo test -p sdk-live-trade --quiet`、`git diff --check`。

方案验收边界：

- 不得再出现 writer validation failure 后 run dir 只有空目录、无 gate report / fail trace 的形态。
- 新 live run 的成功标准仍是单轮 `30/30` 可审计 valid samples；fail-closed 时必须可从 artifact 回答
  valid/excluded sample 数、clean accept 字段污染、writer validation error、probes/samples 是否保存。
- 方案全文落盘后必须派生 GPT-5.5/xhigh 只读 subagents 审查可执行性；若 review 发现 actionable issue，
  先修正文档方案并重复 review。

## 2026-06-26 clean-accept artifact normalization / failure-evidence persistence 本地实现

根据用户批准，已执行 active plan `## 0A` 的本地代码修复。本次不授权 fresh build、binary-only deploy、
production `--no-live-funds` gate 或真实资金 probe。

实现内容：

- `platform_sellable_maturity_runner.rs` 在 SELL probe row 构造前只对 clean accepted SELL row 清空 blank
  `error_message` 和 reject-derived fields；非 clean reject / SDK error 的 `error_message` 保留 adapter
  原始观测值，不做 trim/drop。
- `platform_sellable_maturity.rs` validator 保持 strict；raw clean accepted row 带 blank `error_message`
  仍被拒绝。
- final writer success path 不再用直接 `?` 丢失证据；canonical writer validation/write error 会写入
  `artifact_writer_validation_error:{err}`，run status 转为 `FailClosed`，并继续写出 gate report 和
  fail-closed trace，保留内存中的 probes / samples / buy evidence。
- 测试 fake gateway 新增 accepted SELL blank error 和 blank post-cancel proof seam，仅用于复现本次事故形态。

TDD / 测试证据：

- RED 已确认：
  - `live_probe_normalizes_blank_error_message_on_clean_accepted_sell` 在修复前失败于
    `clean accept must not include reject/error fields`。
  - `live_probe_persists_fail_trace_when_final_writer_validation_fails` 在修复前失败于
    `open_order_clear_proof must not be blank`，且没有 auditable fail-closed report/trace。
- GREEN 已确认：
  - clean accepted normalization 和 final writer failure persistence 两个 runner 回归测试均通过。
  - `live_probe_preserves_blank_error_message_on_non_clean_rejected_sell` 通过，确认非 clean reject / SDK
    error 的原始错误观测不会被 clean-accept normalization 吞掉。
  - `platform_sellable_maturity` strict validator target `8/8` 通过。
- focused gates 已通过：
  - `platform_sellable_maturity_runner` `49/49`
  - `platform_sellable_maturity` `8/8`
  - `cli_platform_sellable_maturity` `3/3`
  - `platform_open_order_check` `3/3`
  - `sdk_order_adapter` `17/17`
  - `heartbeat_watchdog` `6/6`
- full local gate 已通过：
  - `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
  - `git diff --check`

GPT-5.5/xhigh 只读复审已通过：

- code boundary review 起初发现非 clean `SdkRejected` / `SdkError` 的 blank `error_message` 会被 trim/drop
  成 `null`；已修复为只清空 clean accepted row，非 clean row 保留 adapter 原始观测值，并补充
  `live_probe_preserves_blank_error_message_on_non_clean_rejected_sell` 回归测试。
- final writer failure persistence review 通过，确认 writer validation/write error 仍转为
  `artifact_writer_validation_error:{err}` fail-closed reason，gate report / fail trace 仍 create-new 写出并保留
  probes / samples / buy evidence。
- docs/status review 起初发现 `lastest-command.md`、active plan 顶部摘要和 changelog 历史段落有 stale
  current-status wording；已收敛为本地 root-cause/fix/full gate/review 完成，fresh build、binary-only deploy、
  production `--no-live-funds` gate 和真实资金 probe 仍需 renewed approval。

当前边界：fresh build、binary-only deploy、production `--no-live-funds` gate 和真实资金 probe 仍需 renewed
approval。

## 2026-06-26 clean-accept 修复后 fresh build / deploy / no-live gate

用户批准执行 fresh build、binary deploy、远端 `--no-live-funds` gate；明确不执行真实资金 probe。本轮只执行到
production no-live gate，并完成产物拉回检查。

Fresh release build：

- build HEAD：`c73c4c7a9fc39c66389190ec431fb4b812e9f33d`
- dirty state：`clean`
- git diff provenance sha256：`055e250df8c11fc7cedc6f12e75a64515943b6494e08d025da9f3d40f7b1b8ea`
- release binary sha256：`cbc9a6f73ccf1056147e3bc107a4d64191efddfc161a234d9feaf33639440c49`
- config sha256：`e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`
- model tree manifest sha256：`a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`

Binary-only deploy / dry-run：

- deploy id：`r5-c73c4c7-binary-deploy-20260626T120746Z`
- remote binary/config/model sha 与本地一致。
- `r5-actor-rehearsal`：`validator=passed`、`artifact_validator=passed`、`artifacts_checked=17`、
  `evaluated_ticks=1`、`feature_rows=1`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`。
- `no_submit_rehearsal_report.json` sha256：
  `2851c543f7dabbe456df5778bc81bc60591eaddbda9d34ef9546523b0d44791c`
- 本地拉回目录：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/deployments/pullback/r5-c73c4c7-binary-deploy-20260626T120746Z/dry-run/`

Production `--no-live-funds` gate：

- run id：`platform-sellable-maturity-no-live-20260626T120832Z`
- CLI summary：`status=NoLiveFundsPassed`、`valid_samples=0`、`sdk_post_attempts=0`、
  `sdk_cancel_attempts=0`、`hard_reasons=0`
- gate report：`status="no_live_funds_passed"`、`no_live_funds=true`、`valid_sample_count=0`、
  `sdk_post_attempt_count=0`、`sdk_cancel_attempt_count=0`、`heartbeat_attempt_count=0`、
  `under_min_market_cleanup_attempt_count=0`、`fail_closed_reasons=[]`
- gate report sha256：
  `d1c7bc51021a7b9cd1e8e012daa631cf9271452413346fe406580495294cae50`
- 远端目录：
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/platform-sellable-maturity/platform-sellable-maturity-no-live-20260626T120832Z/`
- 本地拉回目录：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260626T120832Z/`

当时真实资金 probe 未执行。后续 live 执行状态以本 changelog 顶部最新记录为准；若后续要继续 live，
必须重新明确批准，并重新确认目标 HEAD / binary provenance。

## 2026-06-26 heartbeat + partial-fill 本地实现收口

根据用户批准，已把 `heartbeat + cumulative partial-fill + under-min cleanup` 从文档方案推进到本地代码实现。
本次仍不授权 fresh build、binary-only deploy、production `--no-live-funds` gate 或真实资金 probe；这些 gate
必须在最终 review 通过、commit/push 后重新获得明确批准。

本地实现要点：

- `PlatformSellableMaturityOfficialGateway` 复用现有 `OfficialHeartbeatGateway` /
  `HeartbeatWatchdogActor`，不新增 raw REST heartbeat。
- BUY wait 使用 `probe_timeout_ms=60000ms` 作为 deadline，不再保留隐藏 `10s then cancel`。
- BUY wait 在 heartbeat tick 后通过官方 Rust SDK `client.order(order_id)` 查询 BUY order，
  将 `status`、`size_matched`、`associate_trades` 投影进 cumulative fill evidence 和 sample artifact。
- BUY 前 heartbeat degraded 时样本 excluded/censored 且不提交 BUY；`fill_size >= probe_size` 后、clean SELL
  accepted 前 heartbeat degraded 时 fail closed with evidence，不允许带着未清理真实持仓继续下一样本；under-min
  partial BUY 下 heartbeat degraded 会阻断 FAK cleanup，只写 `residual_evidence_only` 和
  `raw_rest_fallback_used=false`。
- non-dust `0 < fill_size < min_order_size` 不再 cancel BUY，也不发 limit SELL；heartbeat safe 时通过官方 SDK
  market order builder 提交 `SELL` `OrderType::FAK`，`Amount::shares(fill_size)`，amount 是实际已成交 BUY
  shares，不是未成交 residual。
- gate report / fail-closed trace 增加 heartbeat counters 和 under-min market-cleanup attempt counter；
  sample schema 增加 heartbeat、BUY order query、under-min cleanup / residual evidence 字段，其中 under-min
  cleanup 记录 platform order id、transaction hashes 和 adapter report sha256。
- `--no-live-funds` gate 分支仍保持无真实 SDK post/cancel/heartbeat/market-cleanup attempt。
- 当前 fake runner tests 不声明完整覆盖官方 CLOB order-query recovery 或多笔 partial-fill projection；若后续需要
  synthetic gate，必须补 fake gateway order-query evidence。

已新增/更新本地覆盖：

- `platform_sellable_maturity_runner`：heartbeat before BUY degraded、full BUY heartbeat degraded fail-closed、
  SELL 前 heartbeat degraded fail-closed、degraded blocks under-min FAK、under-min FAK cleanup、unexpected
  partial residual、venue-dust precedence、no-live no heartbeat/cleanup、BUY submit retry等，共 `46/46`。
- `platform_sellable_maturity`：validator 接受 under-min residual-only / FAK evidence，并拒绝 under-min BUY
  cancel/raw REST fallback，共 `8/8`。
- `heartbeat_watchdog`：`6/6`。
- `sdk_order_adapter`：`17/17`，其中 market order submit 复用 build/sign/post observation path。
- `cargo check --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade` 已退出码 `0`。
- 最终本地 gate 已通过：`cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`、
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`、`git diff --check`
  均退出码 `0`。

## 2026-06-26 heartbeat + partial-fill 修复方案落盘

根据 `platform-sellable-maturity-live-20260626T053750Z` 的 `sample-0003` partial BUY 失败复盘和用户纠偏，
active plan 已新增 `## 0. 2026-06-26 本地实现收口：heartbeat + cumulative partial-fill + under-min cleanup`。

本次只更新文档，不修改 Rust 代码，不授权 fresh build、binary-only deploy、production `--no-live-funds`
gate 或真实资金 probe。修复方案的核心边界如下：

- heartbeat 必须复用现有 `OfficialHeartbeatGateway` / `HeartbeatWatchdogActor`；不得自建 raw REST
  heartbeat，也不得把 heartbeat 当成必然成功。
- heartbeat 单次 `RateLimited` / `SdkError` / `PlatformError` 会暂停新增订单并记录 audit；无真实持仓暴露时可
  censor/resample，BUY 已满 `5` 且 clean SELL accepted 前 degraded 时必须 fail closed with evidence。
- heartbeat 恢复/继续条件已明确：下一次 `Posted` 只是必要条件；同一 BUY order 必须有 `LIVE` 或
  cumulative fill 单调增加证据才能继续等待；新提交必须先证明 open-order / residual / account safe；
  BUY 已满 `5` 后、clean SELL accepted 前被 heartbeat degraded 污染时必须 fail closed with evidence，
  clean accepted 后的 failure 只写 cleanup audit。
- 复审收口已补充：现有 heartbeat actor 只提供 per-tick status；当前实现不声明额外
  `last_posted_ms` / watchdog gap recovery 能力。heartbeat degraded / unsafe 时不得提交 under-min FAK cleanup。
- BUY partial fill 必须按同一 `platform_order_id` 累计；正常多笔 partial fill 累计到 `5` 的订单不得被提前
  cleanup cancel，仍应作为 valid BUY 进入 fixed-size SELL maturity probe。
- partial terminal classifier 顺序已固定为 valid `>= probe_size`、venue-dust residual、non-dust under-min、
  unexpected partial、no fill/no evidence；`buy_fill_deadline_ms` 固定复用 `probe_timeout_ms=60000ms` 并受
  reduce-only / market end 约束。
- `0 < fill_size < min_order_size` 的 under-min partial BUY 不得发 limit SELL；该样本 invalid/excluded，
  只能走 SDK-backed market FAK cleanup 或 residual reconciliation evidence。
- FAK cleanup 前必须证明官方 SDK SELL FAK `amount` 单位是实际已成交 BUY shares `fill_size`，不是
  未成交 residual；reject / `SdkError` / unsupported 必须保留 SDK response/projection、residual evidence 和
  `raw_rest_fallback_used=false`。
- 现有 `platform_sellable_maturity` validator 收口为 condition-based：只在对应事件发生时要求
  heartbeat/order-query/under-min evidence，不得把 clean accepted 后 cleanup audit-only 场景变成 hard gate。
- `--no-live-funds` gate 仍必须保持无真实 SDK post/cancel/heartbeat/cleanup attempt。
- 后续执行前必须按 active plan 的测试与验收完成本地验证、GPT-5.5/xhigh subagent review、commit/push；
  真实资金 probe 仍需 renewed approval。

## 2026-06-26 cleanup-audit-only 修复方案

根据 renewed live probe `platform-sellable-maturity-live-20260625T185437Z` 的失败归因和用户复核意见，
本次修订 active plan 的成功/验收口径：

- 本 probe 的目标是测量 `BUY fill ledger apply -> first same-asset SELL clean accepted` 的 maturity
  时间；第一次同 asset SELL `clean_sell_accepted=true` 即为有效样本成功终点。
- clean SELL accepted 后必须停止该样本后续 SELL probe，不再为了 `balance_ge_size` / `free_ge_size`
  继续提交 probe；accepted 前未观测到的 reject-derived 指标继续按 `censored_due_to_clean_accept`
  处理。
- accepted SELL 后续是否成交、best-effort cancel 是否成功、cancel 是否返回 `matched orders can't be canceled`
  / `SdkRejected` / `SdkError`、以及 optional open-order audit 是否为 `0`，全部只记录为 cleanup audit /
  manual review evidence，不得把已 clean accepted 的样本或整轮 run 改成 fail-closed。
- pre-probe 同 asset platform balance / open SELL baseline gate 不变；BUY partial cleanup 的 venue-dust
  规则不变；SDK fallback、raw REST、manual signing 和 shadow implementation 仍不授权。
- clean accepted 前出现非 maturity SELL reject / SDK error，且不能明确归类为可恢复 transient 并在 timeout
  内恢复时，仍属于时间线不可解释的 fail-closed / exclusion 边界。
- 默认 cadence 改为：第一笔 SELL probe 在 BUY fill ledger apply 后立即提交；`0s - 10s` 每 `20ms`；
  `10s - 60s` 每 `100ms`；timeout 仍为 `60000ms`。
- 本次方案复审通过后，代码修复必须同步更新 runner、artifact validator、focused tests、full local gate、
  active docs 和 `lastest-command.md`；真实资金 probe 仍必须重新经过 fresh build、binary-only deploy、
  production `--no-live-funds` gate、产物拉回检查和 renewed approval。
- 本节 supersede 下方历史执行记录中关于 clean accepted 后 cancel/open-order clear 作为 hard gate 的旧口径；
  下方相关条目仅保留为当时实现和失败边界的历史记录。

本地 TDD 实现已完成：

- runner clean-accept 分支改为 cleanup audit-only：第一次 same-asset SELL clean accepted 后立即记录
  `first_clean_accept_ms` 并停止该样本后续 SELL probe；SELL 后续 cancel rejected、cancel `SdkError`、
  `matched orders can't be canceled`、post-cancel open SELL 非零或 open-order audit 查询失败，都记录到
  probe/sample audit fields，不再进入 maturity `fail_closed_reasons`。
- artifact validator / final writer 已放松 accepted 后 cleanup audit：`sell_probe_fill_detected=true`、
  `post_cancel_open_orders_count > 0`、`open_order_clear_proof=null` 或 audit error proof 不再拒绝 valid
  sample；出现的 audit 字符串仍按 trim 后非空校验，时间字段仍保持因果顺序。
- CLI 默认 cadence 已改为 `fast_probe_interval_ms=20`、`slow_probe_interval_ms=100`，`probe_timeout_ms`
  继续为 `60000`；第一笔 SELL probe 仍在 `t_ledger_apply` 后立即提交。
- 本地 focused gates 已通过：`platform_sellable_maturity_runner`、`platform_sellable_maturity`、
  `cli_platform_sellable_maturity`、`platform_open_order_check`。
- 本地 full gate 已通过：`cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`、
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`、`git diff --check`，
  三条命令退出码均为 `0`。

## 2026-06-25 权威计划切换与 probe 参数确认

用户要求将此前权威文档和 changelog 及相关引用标记为归档，并将
`poly-arb-ai/sdk-live-trade-docs/plan/2026-06-25-platform-sellable-maturity-probe-plan.md`
标记为新的权威计划文档。

本次文档更新完成以下事项：

- 将 `poly-arb-ai/sdk-live-trade-docs/plan/2nd-moneyrun-bugs-fix.md` 标记为 archived authoritative plan。
- 将 `poly-arb-ai/sdk-live-trade-docs/changelog/2nd-moneyrun-bugs-fix.md` 标记为 archived changelog。
- 将 `AGENTS.md` 的 sdk-live-trade 当前权威入口改为新的 probe plan/changelog。
- 将 `lastest-command.md` 的 active authoritative plan / changelog 改为新的 probe plan/changelog。
- 将新的 probe plan 标记为 current active authoritative plan。
- 记录用户确认的 probe 参数：第一轮固定 `30` 个有效样本，`configured_probe_size` 固定 `5` shares，
  输出 `median` / `p90` / `p95`，并同时输出 CSV 供人工复核。

执行边界：

- 本次只更新文档状态和引用，不修改 Rust 代码。
- 本次不授权 fresh build、binary-only deploy、production `--no-live-funds` gate 或真实资金 probe。
- 真实资金 probe 仍必须在 active plan 规定的前置 gate 完成后，由用户单独明确批准。

## 2026-06-25 subagent review 后的计划收紧

根据 GPT-5.5/xhigh 只读审查反馈，已收紧 probe 计划的安全和统计口径：

- `AGENTS.md` 不再把当前 active plan 的自动推进范围写成旧 Phase 0-4，改为当前计划明确列出的本地文档、
  实现设计、验证和 review 项。
- SELL probe 必须固定 `sell_size = 5` shares；`fill_size < 5` 的 BUY fill 不计入有效样本。
- SELL probe 必须使用官方 Rust SDK 可表达的 maker-only / post-only、不会 cross 当前盘口的 limit order；
  若 SDK 无法保证该语义，必须停止并等待用户确认。
- clean SELL accepted 后必须立即停止后续 probe 并 cancel；accepted 前未观测到的 `balance_ge_size` /
  `free_ge_size` 记录为删失，不得为了补齐字段继续提交 SELL。
- 新增 sample-level artifact / CSV、post-cancel open-order-clear proof、reject classification、order params、
  rate-limit/network/server/SDK transient error 分类，以及 first reject / clean accept / balance-ge-size /
  free-ge-size 的独立统计字段要求。
- 第二轮复审后补齐 `balance_ge_size_ms` / `free_ge_size_ms` 的通用 `censored_count` 字段，保留
  `censored_due_to_clean_accept_count` 作为原因细分，避免 summary JSON 与 CSV 扁平统计 schema 不一致。

## 2026-06-25 本地 artifact/summary schema 实现

本次按 active plan 的本地自动执行范围完成 platform-sellable maturity probe 的 artifact 与统计基础层：

- 新增 `poly-arb-ai/rust/sdk-live-trade/src/platform_sellable_maturity.rs`。
- 新增 `poly-arb-ai/rust/sdk-live-trade/tests/platform_sellable_maturity.rs`。
- 在 `sdk-live-trade` crate 中登记 workspace 已有的 `csv = "1.4"` 依赖，用于输出 plan 要求的 CSV。
- 实现 `not enough balance / allowance` reject message 的 `balance`、`order amount`、
  `sum of matched orders` 解析，并派生 `balance_ge_size` / `free_ge_size`。
- 实现 sample/probe 校验：固定 `configured_probe_size = 5` shares、有效样本 `fill_size >= 5`、
  每次 SELL probe `sell_size = 5`、`post_only=true`、SELL limit 不 cross 当前 `best_bid`、clean accepted
  后必须 cancel 并证明同 asset open orders 清空。
- 实现 JSONL / JSON / CSV create-new/no-overwrite 写出，以及 `first_reject_ms`、`clean_accept_ms`、
  `balance_ge_size_ms`、`free_ge_size_ms` 的 `mean` / `median` / `p75` / `p90` / `p95` / `min` / `max`、
  `timeout_count` 和删失计数。

已执行 focused RED/GREEN gate：

```bash
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity -- --nocapture
```

首轮 GPT-5.5/xhigh review 指出 validator 过宽后，已补齐以下回归测试和实现：

- `configured_probe_size` / `required_valid_samples` 必须固定为 `5` / `30`，不能由调用方改成其他值后仍通过。
- 每次 probe 前 `pre_probe_open_sell_orders_count` 必须为 `0`。
- clean accepted probe 不得同时携带 `reject_class`、`error_message`、balance/order amount 字段、
  `is_maturity_reject=true` 或 non-maturity error 字段。
- maturity reject 校验必须重新解析 `error_message`，并比对 raw/share/boolean 派生字段。
- valid sample 必须以 clean accept 或 timeout 结束；observed metric 不得同时携带 censor reason；
  `first_balance_ge_size_ms` / `first_free_ge_size_ms` 不得晚于 `first_clean_accept_ms`。
- artifact writer 必须拒绝混合 `run_id`，并拒绝没有对应 sample row 的 probe `sample_id`。

复审继续发现 final writer 与时间线仍需收紧后，已补齐：

- final artifact writer 在写出 `platform_sellable_maturity_summary.json` / CSV 前，必须校验
  `valid_sample_count == required_valid_samples == 30`；少于或多于固定有效样本数都不能生成最终命名 artifact。
- maturity reject probe 也必须与 accepted/cancel evidence 互斥，不能携带 `sdk_status=SdkAccepted`、
  `platform_order_id`、cancel ack 或 post-cancel clear proof。
- `first_reject_ms` 必须不晚于 `first_clean_accept_ms`，与 `balance_ge_size` / `free_ge_size`
  的时间线边界一致。

最终只读审查继续指出 final writer 需要跨行一致性门禁后，已补齐：

- final writer 拒绝 duplicate `sample_id`、0 probe rows、valid sample 缺少 probe evidence、probe
  静态字段与 sample 不一致，以及 sample metric 不能从 probe timeline 派生的 artifact。
- 对 valid sample，probe 的 `wallet_id` / `condition_id` / `asset_id` / `outcome` / `fill_size` /
  `t_ledger_apply_ms` 必须匹配 sample。
- `first_reject_ms`、`first_clean_accept_ms`、`first_balance_ge_size_ms`、`first_free_ge_size_ms`
  和对应 `attempt_count_to_*` 必须由同一 sample 的 probe rows 派生。
- valid sample 不允许携带 `exclusion_reason`；valid sample 对应 probe rows 也不允许
  `exclusion_reason`。

后续 GPT-5.5/xhigh 只读复审继续指出 probe 分类和 accepted 后时间线仍需收紧后，已补齐：

- non-maturity error row 的 `error_message` 如果能被解析为 `not enough balance / allowance`
  maturity reject，则必须拒绝，避免绕过 maturity reject 的反解析一致性校验。
- clean accepted probe 的 cancel 时间必须保持因果顺序：`cancel_submit_ms >= t_probe_response_ms`，
  且 `cancel_ack_ms >= cancel_submit_ms`。
- 同一样本出现 first clean accepted 后，不允许继续写入后续 probe rows。
- 保留并补齐 valid sample 对应 probe rows 携带 `exclusion_reason` 的负向测试覆盖。

最终实现复审继续指出两个边界后，已补齐：

- maturity reject message 解析出的 `order_amount_shares` 必须等于固定 `sell_size = 5`，避免
  `sell_size=5` 的 probe 携带 `order amount: 4000000` 并污染 `balance_ge_size` /
  `free_ge_size`。
- first clean accepted 后的后续 probe row 按真实 submit/response 时间拒绝，不依赖不可信、
  偏小或重复的 `probe_index` 排序。

最终边界复审继续指出 attempt count 仍可能受 `probe_index` 影响后，已补齐：

- 每条 probe row 必须满足 `t_probe_submit_ms >= t_ledger_apply_ms` 和
  `t_probe_response_ms >= t_probe_submit_ms`。
- sample metric 与 `attempt_count_to_*` 改为按真实 `t_probe_submit_ms` /
  `t_probe_response_ms` 时间线派生，不再按 `probe_index` 排序。
- 增加 out-of-order pre-accept `probe_index` 负向覆盖，确保 clean accept 的 attempt count
  不能被偏小或重排的 `probe_index` 污染。

文档/覆盖复审继续指出 equal timestamp 与 config 负向覆盖缺口后，已补齐：

- 同一样本内重复 `(t_probe_submit_ms, t_probe_response_ms)` 会被拒绝为 ambiguous，避免相同时间
  rows 重新把 attempt count tie-breaker 交给 `probe_index`。
- 补齐调用方将 `required_valid_samples` 设为 `29` 或 `31` 的负向测试，确认配置仍固定为 `30`。

最终执行边界复审指出同 asset active SELL probe interval 可重叠后，已补齐：

- 同一样本相邻 probe 的时间区间必须满足
  `next.t_probe_submit_ms > previous.t_probe_response_ms`，否则 final writer 拒绝 artifact。
- 增加 overlapping probe interval 负向测试，覆盖同一时刻同 asset 只有一个 active SELL probe 的计划规则。

summary 口径复审指出 timeout 与 clean-accept censor 可混用后，已补齐：

- `first_clean_accept_ms` 缺失时，`balance_ge_size_censor_reason` /
  `free_ge_size_censor_reason` 必须为空。
- timeout 样本的缺失 reject-derived 指标只进入 `timeout_count`，不进入
  `censored_due_to_clean_accept_count`。
- 增加 timeout sample 携带 `censored_due_to_clean_accept` 的负向测试，以及 timeout summary
  `timeout_count=1` / `censored_count=0` 的正向断言。

non-blank 字段复审指出 whitespace-only 值可绕过后，已补齐：

- clean accept 的 `platform_order_id`、`cancel_after_accept_status`、probe/sample
  `open_order_clear_proof` 均按 `trim().is_empty()` 拒绝 blank 值。
- 增加 whitespace-only platform order id、cancel status、open-order-clear proof 的负向测试。

Post-GREEN full local gate 已在 2026-06-25 JST 执行通过：

```bash
cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all --check
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet
git diff --check
```

执行边界不变：本次不接入真实资金 runner，不执行 fresh release build、binary-only deploy、
production `--no-live-funds` gate 或真实资金 probe。

## 2026-06-25 controlled live probe runner 接入

用户批准先接入受控 platform-sellable maturity probe runner，再继续 fresh release build、
binary-only deploy、production `--no-live-funds` gate 和真实资金 probe。
后续复审 remediation 完成后，用户授权边界已同步为：review、本地 gate、fresh release build、
binary-only deploy、production `--no-live-funds` gate 全部通过后，可执行本次固定 scope 真实资金 probe；
任何 gate 失败或新 blocker 必须停止。

本次实现完成：

- 新增 `poly-arb-ai/rust/sdk-live-trade/src/platform_sellable_maturity_runner.rs`。
- 新增 `platform-sellable-maturity-probe` CLI，参数包含 `--config`、`--wallet-env`、`--output-dir`、
  `--no-live-funds`、`--live-funds-approved-by`、`--valid-samples`、`--probe-size`、`--buy-size`、
  `--max-buy-price`、`--max-buy-notional-usdc` 和 `--probe-timeout-ms`。
- `--no-live-funds` gate 会读取 config、校验 production model artifact contract、加载 wallet env、
  构造官方 SDK clients，并写出 `platform_sellable_maturity_gate_report.json`；该 gate 不调用
  SDK submit/cancel。
- live runner 通过官方 Rust SDK 路径执行：Gamma discovery 选择当前 BTC UP/DOWN 5MIN market；
  `OfficialSdkOrderGateway` / `SdkOrderAdapter` 负责 BUY/SELL submit 和 cancel；CLOB orderbook
  用于 SELL post-only/non-cross price；user-channel mapper 作为 BUY fill 本地入账证据。
- runner 固定 `valid_samples = 30`、`probe_size = 5`；BUY size 必须 `>= probe_size`，且 BUY notional
  必须满足平台最小值和 `--max-buy-notional-usdc`。CLI 默认单笔 BUY cap 为 `5` USDC；按
  `buy_size=5`、`max_buy_price=0.99` 估算，第一轮理论 BUY notional 上限约 `148.5` USDC。
- 历史口径，已由 2026-06-26 heartbeat + partial-fill 修复方案 supersede：当时 BUY fill evidence
  累计 user-channel trade size，直到达到 `probe_size` 或 evidence timeout；累计 fill `< probe_size` 时会
  cancel 该 BUY order、写入 invalid sample exclusion reason，并继续重采样。当前实现不得沿用该旧
  cleanup cancel 口径，必须按 active plan `## 0` 的 terminal classifier 处理。
- GPT-5.5/xhigh 复审指出 official user-channel timeout 分支仍会返回 error、绕过 invalid sample/resample
  后，已把官方 stream collector 改为在 timeout 时返回当前累计 partial evidence，并增加
  `collect_buy_fill_returns_partial_evidence_when_stream_times_out` 单元覆盖。
- 每个 asset 在同一 run 内只允许采一个有效样本；如果当前 discovery 返回已采过的 asset，runner 会等待下一次
  discovery，避免前一次 BUY 留下的同 asset 持仓污染后续 SELL accept 时间。
- 每个样本 BUY 前通过官方 SDK `balance_allowance` 查询 conditional token balance，并查询同 asset
  open SELL orders；若 pre-probe platform balance 已经 `>= probe_size` 或 open SELL count 非零，
  runner 会在 BUY 前 fail closed。`pre_probe_platform_balance_raw` 记录 SDK 查询值，不再使用硬编码占位。
- SELL probe 固定 `post_only=true`，并派生 `sell_limit_price = best_bid + tick_size`，要求
  `sell_limit_price > best_bid` 且不超过 `1.0`。
- 第一笔 SELL probe 在 `t_ledger_apply` 后立即开始；后续 SELL probe 提交前按 fast/slow probe interval
  真实 `sleep`，并使用 wall-clock submit/response/cancel timestamp；补齐了防止只递增 artifact timestamp、
  真实请求却连发的 focused test。
- clean SELL accepted 后立即 cancel，并通过官方 CLOB open orders 查询证明同 asset open SELL count 为 `0`；
  final artifacts 仍由既有 `platform_sellable_maturity` writer create-new 写出 JSONL/JSON/CSV。
- clean SELL accepted 后若 cancel 失败或 post-cancel 同 asset open SELL count 非零，runner 会 fail closed，
  并额外 create-new 写出 `platform_sellable_maturity_fail_closed_trace.json`，保留 partial probes/samples 和
  fail-closed reasons。
- runner 会在 stderr 输出每个样本的开始进度和等待未使用 asset 的状态，避免长时间真实 probe 静默。

已执行 focused RED/GREEN gate：

```bash
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test cli_platform_sellable_maturity -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner -- --nocapture
```

结果：两个 focused gate 均退出码 `0`。其中 runner gate 覆盖 no-live 零 post/cancel、synthetic live
30 valid 样本、pre-probe balance 已达 `probe_size` 时 BUY 前 fail-closed、部分 BUY fill 的
cancel/exclusion/resample、official stream timeout partial evidence、第一笔 SELL 立即开始且后续 interval 真实等待、post-only/non-cross SELL、
clean accept 后 cancel、post-cancel open SELL 非零 fail-closed，以及 fail-closed trace artifact。

Post-runner full local gate 已执行：

```bash
cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all --check
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet
git diff --check
```

结果：三条命令均退出码 `0`。

## 2026-06-25 gate execution and live fail-closed

GPT-5.5/xhigh 只读 review、本地 gate、fresh release build、binary-only deploy 和 production
`--no-live-funds` gate 已按顺序执行。

已验证：

- GPT-5.5/xhigh 只读 review 通过，无剩余 actionable blocker。
- fresh release build：`git_commit=49a534122b132b49d3d716032b8b242c9259d9d8`、
  `dirty_state=clean`，release binary sha256 =
  `6a0218090fd8e6300fea872f25b4febcbdb98dde58da03a11e0146964aeb4c19`。
- binary-only deploy：`r5-49a5341-binary-deploy-20260625T133136Z`，远端 binary/config/model sha
  校验通过，R5 actor rehearsal 输出 `validator=passed`、`artifact_validator=passed`、
  `sdk_post_attempted=false`、`sdk_cancel_attempted=false`。
- production `--no-live-funds` gate：`platform-sellable-maturity-no-live-20260625T133223Z`，
  输出 `status=NoLiveFundsPassed`、`sdk_post_attempts=0`、`sdk_cancel_attempts=0`。

真实资金 probe 已执行一次：`platform-sellable-maturity-live-20260625T133257Z`。该 run 在 BUY 前
fail closed，未发生真实 SDK post/cancel：

- CLI summary：`status=FailClosed`、`valid_samples=0`、`sdk_post_attempts=0`、
  `sdk_cancel_attempts=0`、`hard_reasons=1`。
- fail reason：`sample-0000:buy notional is below platform minimum $1`。
- 远端产物：
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/platform-sellable-maturity/platform-sellable-maturity-live-20260625T133257Z/`。
- 本地拉回产物：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-20260625T133257Z/`。

当前 blocker：runner 使用当前 outcome `best_ask * buy_size` 检查平台 `$1` 最小订单额；当
`buy_size=5` 且低价 outcome `best_ask < 0.20` 时，订单在 BUY 前 fail closed。下一步不得直接重跑
相同二进制补采样；需要先决定是把低 notional candidate 作为 invalid sample/resample，还是把 BUY
limit price 提高到满足平台最小额的最低价格，并重新走 review/build/deploy/no-live gate。

## 2026-06-25 BUY min-notional remediation

用户批准采用 GPT-5.5/xhigh 并行只读审查后的最小修复方案：不跳过低价 outcome，而是把 BUY limit
price 派生为 `max(best_ask, ceil_to_tick(1 / buy_size))`。该方案保持 `buy_size=5`、`probe_size=5`、
`max_buy_price=0.99`、单笔 `max_buy_notional_usdc=5` 和 run-level conservative BUY intent cap 不变；
若 derived price 或 derived notional 超过 cap，仍在 BUY 前 fail closed。

本次代码改动：

- `platform_sellable_maturity_runner` 新增 `ceil_to_tick` 和 BUY candidate decision evidence。
- 低价 outcome 的 BUY pre-submit price 由 `best_ask` 改为
  `max(best_ask, ceil_to_tick(1 / buy_size))`；例如 `buy_size=5` 且 `best_ask=0.18` 时，
  `derived_buy_limit_price=0.20`、`buy_intent_notional=1.00`。
- `platform_sellable_maturity_fail_closed_trace.json` 新增 `buy_candidates`，记录
  `best_bid`、`best_ask`、`tick_size`、`min_order_size`、`platform_min_notional_usdc`、
  `min_notional_price_tick_ceil`、`derived_buy_limit_price`、`buy_price_source`、
  `best_ask_notional`、`buy_intent_notional`、`max_buy_price`、`max_buy_notional_usdc`、
  `decision` 和 `decision_reason`，避免 BUY 前 fail-closed 时 trace 为空、无法复核价格和 notional。
- `validate_book` 现在显式拒绝 `min_order_size <= 0`，避免异常 orderbook metadata 绕过
  pre-submit gate。
- runner tests 的默认 `max_buy_notional_usdc` 已收敛到 production-aligned `5`。
- CLI help test 补齐 `--buy-size`、`--max-buy-price`、`--max-buy-notional-usdc` 和
  `--probe-timeout-ms` 覆盖。

已执行 RED/GREEN focused gate：

```bash
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner low_buy_notional_raises_buy_limit_to_platform_minimum_and_collects_30_valid_samples -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner derived_buy_price_above_max_buy_price_fail_closes_before_sdk_post -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner derived_buy_notional_above_max_buy_notional_fail_closes_before_sdk_post -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner nonpositive_min_order_size_fail_closes_before_sdk_post -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner run_buy_notional_cap_fail_closes_with_candidate_trace_before_next_sdk_post -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade platform_sellable_maturity_runner::tests::ceil_to_tick_rounds_platform_min_notional_price_up -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test cli_platform_sellable_maturity -- --nocapture
```

结果：上述 focused gates 均退出码 `0`。

Full local gate 已执行：

```bash
cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet
git diff --check
```

结果：上述 full local gate 在首轮 remediation 后曾退出码 `0`。GPT-5.5/xhigh 首轮 review 随后指出
`min_order_size <= 0` 与 run-level BUY intent notional cap 缺少 dedicated coverage；已补齐 focused
RED/GREEN 和实现。review remediation 后重新执行
`cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`、
`cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet` 和
`git diff --check`，三条命令均退出码 `0`。之后仍需 GPT-5.5/xhigh 只读 review、commit/push、
fresh release build、binary-only deploy 和 production `--no-live-funds` gate；这些 gate 全部通过后，
才能进入下一次真实资金 probe approval。

## 2026-06-25 BUY min-notional remediation build/deploy/no-live evidence

BUY min-notional remediation 后的只读复审、发布和远端 no-live gate 已完成：

- GPT-5.5/xhigh 只读复审：代码/测试复审与文档/执行边界复审均为 `PASS`，无 actionable findings。
- commit/push：`f685b55c03957ceab64973a2f0ba7be97e6cec4e`
  (`sdk-live-trade: fix platform sellable buy notional gate`) 已推送到 `origin/sdk-live-trade`。
- fresh release build：`git_commit=f685b55c03957ceab64973a2f0ba7be97e6cec4e`，
  `worktree_status_sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`，
  `diff_sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`，
  release binary sha256 =
  `942b1fdc61838ccbc8ffa94e863bdd3515fec63922320b5ea47088b7c160029c`。
- config sha256 =
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`；model tree hash =
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`。
- binary-only deploy：`r5-f685b55-binary-deploy-20260625T144053Z`，远端 binary/config/model sha
  校验通过，R5 actor rehearsal 输出 `validator=passed`、`artifact_validator=passed`、
  `sdk_post_attempted=false`、`sdk_cancel_attempted=false`，report sha256 =
  `c5ef27c442a3a9de94e075a09ad096763750126b883ee488f7cf44882ad2c752`。
- production `--no-live-funds` gate：`platform-sellable-maturity-no-live-20260625T144138Z`，
  输出 `status=NoLiveFundsPassed`、`valid_samples=0`、`sdk_post_attempts=0`、
  `sdk_cancel_attempts=0`、`hard_reasons=0`。
- no-live 产物已拉回：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260625T144138Z/`，
  gate report sha256 =
  `00dd30f1caf7eac541586840f5406787b0b021e7c83558cea6fbb5c93dac624e`；本地 JSON 断言
  `status=="no_live_funds_passed"`、`no_live_funds==true`、SDK post/cancel `0/0` 通过。

本段记录 remediation 后、真实资金 run 前的 pre-live gate 证据；后续真实资金结果见下一节。本轮已验证
运行二进制对应 code commit `f685b55c`；若后续发生代码、命令、配置或运行参数变化，必须重新
build/deploy/no-live。

## 2026-06-25 BUY min-notional remediation live-funds result

用户批准后已执行 fixed-scope 真实资金 probe：
`platform-sellable-maturity-live-20260625T145028Z`。本轮不是 probe pass，而是 fail-closed：

- CLI summary：`status=FailClosed`、`valid_samples=1`、`sdk_post_attempts=5`、
  `sdk_cancel_attempts=2`、`hard_reasons=1`。
- gate report fail reason：`sample-0002:current market is reduce/cancel/reconcile only`。
- 远端产物：
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/platform-sellable-maturity/platform-sellable-maturity-live-20260625T145028Z/`。
- 本地拉回产物：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260625T145028Z/`。
- sha256：gate report =
  `2d45978a705915c36da10065fa141160ef21f341c2fe514863fd6e43a436b2da`；fail trace =
  `e8d1269ad7060751cf5307dcce2078e99f01cc40405240fb191f325e31a150bd`。

本轮 artifact 证据：

- `sample-0000` / UP 是单个有效 maturity sample：`fill_size=5`、
  `first_reject_ms=128`、`first_clean_accept_ms=1408`、`attempt_count_to_clean_accept=3`、
  `post_cancel_open_orders_count=0`、`open_order_clear_proof=clob_open_sell_orders_empty`。
- 当前 artifact 没有显示遗留 open SELL 的正向证据：`sample-0000` clean SELL accepted 后
  `cancel_after_accept_status=SdkAccepted`、`post_cancel_open_orders_count=0`。但 pullback 目录只有
  gate report 和 fail trace，没有完整 orders/user-channel/open-order 原始 JSONL 或远端 CLOB snapshot；
  因此不能从当前 artifact 独立证明 run 结束后所有平台 open orders 均为空。
- `sample-0001` / DOWN 是 invalid sample：`exclusion_reason=buy_fill_size_below_configured_probe_size`、
  `fill_size=0`；runner 随后继续 resample。
- `buy_candidates` 只包含 `sample-0000` 和 `sample-0001`，且两者均为 `decision=submitted`；
  低价 BUY min-notional blocker 未复发。
- `sample-0002` 在等待未使用 asset 后遇到当前 market 的 reduce/cancel/reconcile-only safety guard；
  代码路径对应 `ActiveWindowPermission::ReduceCancelReconcileOnly` / `allows_new_quote()==false`，即
  market 末尾 10 秒 no-new-quote 边界。

当前 blocker：runner 在等待下一个 unused asset 时，如果当前 window 已进入末尾 reduce-only 区间，会
立即 fail closed，而不是继续等待下一 window。下一次真实资金 probe 不得直接重跑；必须先完成 root-cause
review、修复方案、local tests、GPT-5.5/xhigh review、fresh release build、binary-only deploy、
production `--no-live-funds` gate、产物拉回检查和 renewed approval。

## 2026-06-26 reduce-only root-cause review / fix proposal

已完成 `platform-sellable-maturity-live-20260625T145028Z` 的 root-cause review，并整理供用户审查的修复方案：

- 新增 proposal：
  `poly-arb-ai/sdk-live-trade-docs/plan/2026-06-26-platform-sellable-reduce-only-root-cause-fix-proposal.md`。
- root cause 确认：official gateway 在 current market 进入末尾 `10s`
  `ReduceCancelReconcileOnly` 后返回 plain `Err("current market is reduce/cancel/reconcile only")`；
  `discover_unused_market()` 直接传播错误，导致 sample BUY 前的 waitable state 被当成 run-level hard fail。
- 该问题不改变安全语义：`ReduceCancelReconcileOnly` / `allows_new_quote()==false` 仍必须禁止新增 BUY/SELL；
  修复只允许在 `discovery_before_buy`、尚未 BUY submit、无 active order、无 pending cleanup 时等待下一 window。
- 推荐方案：改成 typed discovery outcome / wait reason；不得通过字符串匹配吞错误；BUY submit 前补最后一次
  reduce-only guard；invalid BUY cleanup 后补同 asset open-order clear proof；gate report 和 fail trace
  补 discovery wait evidence。
- 两路 GPT-5.5/xhigh 只读 subagent review 均给出 PASS，且要求下一次真实资金 probe 前先补只读平台
  open-order check。该 check 只能使用官方 SDK / CLOB read query，不得 submit/cancel。

本次只更新审查文档和执行 cursor，不实现代码，不执行 build/deploy/no-live，不授权再次真实资金 probe。

## 2026-06-26 reduce-only wait fix 本地实现

用户批准执行 2026-06-26 fix proposal 后，已完成本地 TDD 实现和验证；本次仍未执行 fresh release build、
binary-only deploy、production `--no-live-funds` gate 或真实资金 probe。

实现内容：

- `PlatformSellableMaturityGateway::discover_market()` 从直接返回 market / plain error 改为 typed
  `PlatformSellableMaturityDiscoveryOutcome::{Ready, Wait}`。
- official gateway 在当前 BTC UP/DOWN 5MIN market 进入末尾 `ReduceCancelReconcileOnly` 时返回
  wait event；该 path 不订阅 user-channel、不更新 current market、不返回可提交 market。
- `discover_unused_market()` 只在 BUY submit 前处理 waitable reduce-only / already-used asset 状态；
  `NoCandidates`、`NotAcceptingOrders`、SDK/Gamma/user-channel 等真实 unsafe/error 仍 fail closed。
- wait event 的 `active_order_state` 和 `pending_cleanup` 保留原始语义并在等待前校验；若 wait event
  携带 active order 或 pending cleanup，runner fail closed，不会把字段覆盖成安全值。
- BUY submit 前新增 `pre_buy_submit_wait()` guard；如果 discovery 之后、BUY 提交之前跨入末尾
  reduce-only 区间，runner 记录 wait event 并重新 discovery，不提交 BUY。
- gate report 和 fail trace 新增 `market_discovery_wait_count`、
  `market_discovery_reduce_only_wait_count` 和 `market_discovery_wait_events[]`。
- invalid BUY cleanup cancel accepted 后，必须查询同 asset open orders；若 count 非 `0` 或 proof 缺失，
  run fail closed。sample artifact 新增 `cleanup_cancel_status`、`cleanup_cancel_submit_ms`、
  `cleanup_cancel_ack_ms`、`cleanup_open_order_count`、`cleanup_open_order_clear_proof` 和
  `cleanup_open_order_response_projection_sha256`，validator 要求 SDK response projection sha 为 64 位 hex
  sha256。official gateway 的同 asset open-order proof 使用 bounded pagination 汇总所有 SDK orders pages，
  重复 cursor 或超过页数上限仍 fail closed。
- 新增 `open_order_check` 模块和 `platform-open-orders-check` CLI，使用官方 Rust SDK `orders`
  read query 分页读取 wallet open orders，写 create-new
  `platform_open_order_check_report.json`，并固定 `sdk_post_attempted=false`、
  `sdk_cancel_attempted=false`。若发现任何 open order 或 SDK query fail，该 CLI 非零退出并阻断后续 gate。

执行前只读 pre-check 已通过现有 `remote-dry-run` 当前 market snapshot 完成：

- run id：`platform-open-order-precheck-20260625T152130Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-order-precheck-20260625T152130Z/`
- `open_order_snapshot.json`：`queried=true`、`ok=true`、`count=0`、`exposures=[]`
- `deployment_dry_run_report.json`：`sdk_post_attempted=false`、`sdk_cancel_attempted=false`，
  fail-closed 仅因为 no-live dry-run 的 `reconciliation:audit_incomplete`

该 pre-check 是现有 dry-run 的当前 market snapshot，不替代本次新增的全平台 `platform-open-orders-check`；
下一次 live 前必须用部署后的新二进制再执行一次 dedicated check。为保持官方 SDK-first 边界，本次不声明
HTTP raw response bytes，只记录 SDK typed response projection sha256。

已执行 focused RED/GREEN gate：

```bash
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test cli_platform_sellable_maturity -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_open_order_check -- --nocapture
```

结果：`platform_sellable_maturity_runner` 18/18、`platform_sellable_maturity` 8/8、
`cli_platform_sellable_maturity` 2/2、`platform_open_order_check` 3/3 均通过。

已执行 full local gate：

```bash
cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet
git diff --check
```

结果：三条命令均退出码 `0`。下一步是 GPT-5.5/xhigh 只读复审；复审通过前不得 build/deploy/no-live/live。

GPT-5.5/xhigh 只读复审结果：

- 首轮安全/方案复审指出 wait event 的 `active_order_state` / `pending_cleanup` 不能被覆盖成安全值，
  且 cleanup/open-order 证据不能误称 raw response；已修复为保留并校验 wait safety fields，artifact
  字段和文档改为 SDK response projection sha256。
- 首轮代码/文档复审指出 proposal 要求的 active/pending cleanup 负向测试缺口和 `lastest-command.md`
  focused command 计数错误；已补齐 `discovery_wait_with_pending_cleanup_fail_closes_before_submit`、
  `pre_buy_wait_with_active_order_state_fail_closes_without_submit`，并修正文档计数。
- 修复后重新执行 full local gate：
  `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`、
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`、
  `git diff --check`，三条命令均退出码 `0`。
- 回归复审两路均为 `PASS`，无剩余 actionable issue。

commit/push：reduce-only wait fix 实现已提交并推送到 `origin/sdk-live-trade`：
`60b683fb8dd6a4e088373fd87acc4fe32f9d4ca5`
(`sdk-live-trade: handle reduce-only probe wait`)。

当前边界：停在 fresh release build 前；fresh release build、binary-only deploy、production
`--no-live-funds` gate 和 renewed live probe 尚未执行。

## 2026-06-26 JST renewed live probe fail-closed after partial BUY cleanup

用户批准执行 fresh release build、binary-only deploy、远端 `--no-live-funds` gate，并在这些全部通过后执行
真实资金 probe。本轮已按顺序执行，前置 gate 全部通过，但真实资金 probe fail-closed，未达到 `30` 个有效样本。

fresh release build：

- HEAD：`d220860921b34dabb1aa422ed999ed82e6c152a6`
- dirty state：`clean`
- git diff provenance sha256：
  `920a4317305548491f503e7fa99895b0c5defa6058d7f957e71237d26f4ac963`
- release binary sha256：
  `f943127de7d467d061b1961de67c9f4f6a3851d5915457017395e930f5a787ce`
- config sha256：
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`
- model tree sha256：
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`

binary-only deploy：

- deploy id：`r5-d220860-binary-deploy-20260625T172158Z`
- remote binary/config/model sha 校验通过。
- `r5-actor-rehearsal` 输出 validator/artifact_validator passed，
  `sdk_post_attempted=false`、`sdk_cancel_attempted=false`。
- `no_submit_rehearsal_report.json` sha256：
  `5e3cedde15a9544d2c6cec61ef64095d99f22d39f09739c44883813ede03eba7`

live 前 open-order check：

- run id：`platform-open-orders-check-20260625T172250Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-20260625T172250Z/`
- `status=passed`、`open_order_count=0`、`open_order_ids=[]`、
  `sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- report sha256：`12badce4c1b1ce9bbea6839afe07e1be3fd6bf92fdfacfdaf2893ac8561c3d6d`
- bundle manifest sha256：`70c3d9453649a506a6d752a9984438175b76d3cc9bc4267e91354df81483805f`

production `--no-live-funds` gate：

- run id：`platform-sellable-maturity-no-live-20260625T172313Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260625T172313Z/`
- `status=no_live_funds_passed`、`no_live_funds=true`、`valid_sample_count=0`、
  `sdk_post_attempt_count=0`、`sdk_cancel_attempt_count=0`、`fail_closed_reasons=[]`
- gate report sha256：`d1258020699c8ea38e61e35521dcb666e691183a816799ffc1ce41a52d6fd2f2`
- bundle manifest sha256：`ab347ef4d3812b99f497dc917fdab107ddcf3124d5870801f626d7033502ad85`

真实资金 probe：

- run id：`platform-sellable-maturity-live-20260625T172350Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260625T172350Z/`
- CLI summary：`status=FailClosed`、`valid_samples=9`、`sdk_post_attempts=50`、
  `sdk_cancel_attempts=10`、`hard_reasons=1`
- gate report：`status=fail_closed`、`valid_sample_count=9`、
  `market_discovery_wait_count=189`、`market_discovery_reduce_only_wait_count=8`
- fail reason：`sample-0009:BUY cleanup cancel after insufficient fill was not accepted`
- gate report sha256：`28631dc314b35c9f17e8828a55781171240edca91248db72982e1866ce8cd0e2`
- fail trace sha256：`52fd3a9a31761cae94db52189e54c048ea56f6c39c9efa7b7e067dc06428f6be`
- bundle manifest sha256：`44d7d7aeaaa060fcddb090c0617bcb9b6317ae26f6f66cdb461c0ee0efe83e24`

post-live safety checks：

- open-order check run id：`platform-open-orders-check-post-live-20260625T174106Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-post-live-20260625T174106Z/`
- `status=passed`、`open_order_count=0`、`open_order_ids=[]`，SDK response projection sha256
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`
- open-order report sha256：`23376391c256338e247d7ee66124af0d7962df9168b8e7004087aa16450927fe`
- account snapshot run id：`post-live-account-snapshot-20260625T174249Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/post-live-account-snapshot-20260625T174249Z/`
- Data API positions queried OK，`data_position_count=2`：sample-0008 UP asset
  `30406386996139829832337070085137874128812585032520671093904802343818679254932`
  size `5` value `2.125`；sample-0009 DOWN asset
  `101698463432434787332761595855115625023785413522703854250705780793619856313924`
  size `4.9939` value `2.8714`
- `account_snapshot.json` sha256：
  `d382a1e8dd139646f1e6094a2b92c4c27c81fc5db47a97c8c3f91b5065004b28`
- `position_value_snapshot.json` sha256：
  `05422a0763c2c78fc27744d489b8be1abf6f5b8ede3bd07ac2ab65e84c142505`

Root-cause notes:

- The code path is the BUY partial-fill branch: `collect_buy_fill()` returned cumulative fill below `probe_size=5`,
  then runner attempted cleanup cancel and required `cancel_report.final_status == SdkAccepted`.
- `SdkOrderAdapter` classifies a single-order cancel as accepted only if the target order id appears in SDK
  `canceled`; otherwise it is `SdkRejected`.
- The fail trace currently preserves `buy_candidates`, `samples` and `probes`, but does not persist the failing
  BUY cleanup cancel report, not_canceled reason, or BUY order id for `sample-0009`; this is an audit gap.
- Post-live official SDK open-order check proves no remaining open orders, while post-live Data API positions prove
  residual positions remain. The next fix proposal must handle both: stronger evidence persistence and explicit
  residual exposure semantics for partial BUY fills.

Current cursor: do not directly rerun live funds. Next step is root-cause review / fix proposal for
`sample-0009` partial BUY cleanup cancel fail-closed, followed by local tests, GPT-5.5/xhigh review, fresh build,
binary-only deploy, production `--no-live-funds` gate and renewed approval before any new live probe.

## 2026-06-26 JST venue-dust fix for sample-0009 partial BUY cleanup

用户指出这次失败需要考虑既有 venue-dust 处理。重新核对后，`sample-0009` 的 BUY 成交
`4.9939/5`，residual 为 `0.0061` shares，低于既有 `venue_dust_threshold_shares=0.01`。因此本轮
root cause 修正为：platform-sellable maturity probe 的 partial BUY cleanup path 没有接入既有
venue-dust terminal semantics，把 dust residual 下的 cancel reject 当成了 hard fail。

venue-dust 修复前有效样本数：

- 当时 run `platform-sellable-maturity-live-20260625T172350Z`：`9/30`。
- 加上上一轮 `platform-sellable-maturity-live-20260625T145028Z` 的 `sample-0000`：历史累计同口径
  `10/30`。
- `sample-0009` 的 `4.9939/5` 是 venue-dust invalid/excluded sample，不计入 valid sample。

本地修复：

- 在 partial BUY cleanup 分支计算 `probe_size - fill_size`。
- 当 residual `>0 && <= venue_dust_threshold_shares()` 且 cleanup cancel 为 `SdkRejected`、并带有
  `not_canceled` 或 error message rejection evidence 时，不直接 hard fail；先用 official SDK-backed
  open-order proof 证明同 asset open orders 为 `0`。
- proof 为 `0` 时写 invalid sample 并 resample，`cleanup_cancel_status="VenueDustTerminal"`，
  `cleanup_terminal_reason="venue_dust_below_threshold"`。
- 不 mint dust shares，不把 `4.9939/5` 当成完整 `5` shares，不计入 valid sample。
- residual 大于 threshold、cleanup cancel 为 `SdkError`、缺少 cancel rejection evidence 或 open-order proof
  非 `0` 仍 fail closed。
- sample artifact 新增 `cleanup_buy_order_id`、`cleanup_cancel_not_canceled_json`、
  `cleanup_cancel_error_message`、`cleanup_venue_dust_shares` 和 `cleanup_terminal_reason`。

TDD / verification：

- RED：
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test platform_sellable_maturity_runner partial_buy_venue_dust_cancel_reject_is_excluded_and_resampled_when_open_orders_clear -- --nocapture`
  失败为 `left: FailClosed right: Passed`。
- GREEN focused：`partial_buy_` filter 下 5/5 通过，覆盖普通 partial cleanup、venue-dust cleanup
  reject/resample、residual `0.02` 大于 dust threshold 仍 fail-closed、`SdkError` 不得被 dust terminal
  吸收、缺少 cancel rejection evidence 不得被 dust terminal 吸收。
- focused gates：
  `platform_sellable_maturity_runner` 22/22、`platform_sellable_maturity` 8/8、
  `cli_platform_sellable_maturity` 2/2、`platform_open_order_check` 3/3 均通过。
- full local gates：
  `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`、
  `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`、
  `git diff --check` 均退出码 `0`。

修复后 GPT-5.5/xhigh 回归复审：

- 代码/测试 reviewer：PASS，无 blocking findings；确认 `VenueDustTerminal` 已收紧到 dust residual、
  `SdkRejected`、rejection evidence 和 SDK-backed open-order proof `0`。
- 文档/计数 reviewer：仅指出 `lastest-command.md` 顶部缺少当前测试计数明细；已补齐。

当时边界（已由下一节 `185437Z` execution supersede）：等待 fresh build、binary-only deploy、
production `--no-live-funds` gate 和 renewed live probe 的重新批准；任何新真实资金 probe 仍需要
fresh build/deploy/no-live/pullback gate 和 renewed approval。

## 2026-06-26 JST venue-dust fix 后 build/deploy/no-live/live execution

用户批准执行 venue-dust fix 后的 fresh build、binary-only deploy、远端 `--no-live-funds` gate，并在全部通过后
批准执行真实资金 probe。本轮全部使用 commit
`2bbe4e8596bf0aaa7de6330fb6faaa6742625445`，未在 AWS host 上运行 Rust 编译。

Fresh release build：

- build HEAD：`2bbe4e8596bf0aaa7de6330fb6faaa6742625445`
- dirty state：`clean`
- git diff provenance sha256：
  `dc74e92deeb9012668441d52ec88fd35fb292f052ea8c819fcca1e8b5c57fb9c`
- release binary sha256：
  `de556d46dc18a29945209d3edbe34cb31c6c5bccf8b64c058f7287899677e480`
- config sha256：
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`
- model tree manifest sha256：
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`

Binary-only deploy：

- deploy id：`r5-2bbe4e8-binary-deploy-20260625T185252Z`
- remote binary/config/model sha 校验通过。
- `r5-actor-rehearsal` validator/artifact_validator passed。
- `sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- `no_submit_rehearsal_report.json` sha256：
  `24fea457c8377e4b75398d9ade43795826afc02b0fa37f7e62c988749d718916`

Live 前只读 open-order gate：

- run id：`platform-open-orders-check-20260625T185345Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-20260625T185345Z/`
- `status=passed`、`open_order_count=0`、`open_order_ids=[]`、
  `sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- SDK response projection sha256：
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`
- report sha256：`e40530c7490262149f967a8f674e38f7bbcc226d4361124aa53b6a91f9d19c8f`
- bundle manifest sha256：`d45ecacfcdb7db78a0815b908dcb1fcb547beb8d20530f04d8542e58f3a1d9d6`

Production `--no-live-funds` gate：

- run id：`platform-sellable-maturity-no-live-20260625T185410Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260625T185410Z/`
- `status=no_live_funds_passed`、`no_live_funds=true`、`valid_sample_count=0`、
  `sdk_post_attempt_count=0`、`sdk_cancel_attempt_count=0`、`fail_closed_reasons=[]`
- gate report sha256：`a581b4688075c9379d6bd7e40bce43ce293034dc6df5d70d39f2973580fc1b56`
- bundle manifest sha256：`250d33873d908cb89cd84aace1d45a4588b917d3f1a0a24d14f1d8b4190fe97c`

真实资金 probe：

- run id：`platform-sellable-maturity-live-20260625T185437Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260625T185437Z/`
- CLI summary：`status=FailClosed`、`valid_samples=1`、`sdk_post_attempts=11`、
  `sdk_cancel_attempts=2`、`hard_reasons=1`
- gate report：`status=fail_closed`、`valid_sample_count=1`、
  `market_discovery_wait_count=0`、`market_discovery_reduce_only_wait_count=0`
- fail reason：`sample-0001:cancel after clean SELL accept was not accepted`
- gate report sha256：`b2445b0c383441157235a4bbde8fc362a1d3fbd0da63c882fc168f84499e007f`
- fail trace sha256：`6cd6ad14c596c1690e6e4fc54c261228c591b8b3a4fb860a99d9705e63ed5d5e`
- bundle manifest sha256：`e5438c7144ddda63f60558d11bcec13df5574f4fb051f2bb10ab048fd2adb821`

Post-live safety checks：

- open-order check run id：`platform-open-orders-check-post-live-20260625T185510Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-post-live-20260625T185510Z/`
- `status=passed`、`open_order_count=0`、`open_order_ids=[]`、SDK response projection sha256
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`
- open-order report sha256：`c6ebf481c9605b60fdfd90e6023f55e265fbe3e76bf2f9fd2a57d92f2b47a597`
- bundle manifest sha256：`2f072870ec67131d3c33f6990fd21e8c7065f84e1a0db6a3d11660ec594edef4`
- account snapshot run id：`post-live-account-snapshot-20260625T185752Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/post-live-account-snapshot-20260625T185752Z/`
- Data API positions queried OK，`data_position_count=0`、`data_total_value_usdc=0`、
  `data_positions_usage=ReconciliationInputOnly`、
  `position_count=0`、`total_value_usdc=0`
- `account_snapshot.json` sha256：
  `5cc6abf8a5653de7ec1c8fe0ea71c411054b244af7ddc8261577e1f18141a31e`
- `position_value_snapshot.json` sha256：
  `5ec79a228f02f98c3e67a3ceaadddb4aef83bdfab64337e9ff887bc601c6edb1`
- local bundle manifest sha256：
  `eab791e56c4ca3a42b76085bd53ca5cf1e272602960313eb5fe9d8bafc590890`

当时失败原因（历史，已由 `platform-sellable-maturity-live-20260626T033334Z` supersede）：

- 本轮不是 venue-dust partial BUY cleanup 路径复发。`sample-0001` 已经完成 BUY fill `5`，
  clean SELL probe 被 SDK 接受，platform order id
  `0x30ad9e19bdb4ef454c68bf61a9d75d84591ffb6296dae383c1e285b595a5cde1`。
- fail-closed 发生在 clean SELL accepted 后的 cleanup cancel：`cancel_after_accept_status=SdkRejected`、
  `cancel_error="cancel after clean SELL accept was not accepted"`。
- 后验只读检查显示平台 open orders 和 Data API positions 均为 `0`，但该后验状态不能把 live run
  改判为 passed；下一步仍需针对 clean SELL accepted cleanup-cancel `SdkRejected` 做 root-cause review。

当时有效样本数（历史）：

- 当时最新 run `platform-sellable-maturity-live-20260625T185437Z`：`1/30`。
- 已拉回 live runs 按 `condition_id + asset_id` 去重后的历史累计 raw valid samples：`11/30`
  (`145028Z` 的 `1`、`172350Z` 的 `9`、`185437Z` 的 `1`)。
- 计划目标仍是单轮获得 `30` 个有效样本；当前未达标。

当时边界（历史）：不得直接重跑真实资金 probe。下一步是本轮 `sample-0001` clean SELL accepted cleanup-cancel
`SdkRejected` 的 root-cause review、修复方案、local tests、GPT-5.5/xhigh review、fresh build、
binary-only deploy、production `--no-live-funds` gate、产物拉回检查和 renewed approval。

## 2026-06-26 JST cleanup-audit-only 后 build/deploy/no-live/live execution

用户批准执行 cleanup-audit-only 修复后的 fresh build、binary-only deploy、远端 `--no-live-funds`
gate，并在全部通过后执行真实资金 probe。本轮全部使用 commit
`865e0d87f540727740628a54e06e1856abf96291`，未在 AWS host 上运行 Rust 编译。

Fresh release build：

- build HEAD：`865e0d87f540727740628a54e06e1856abf96291`
- dirty state：`clean`
- git diff provenance sha256：
  `0aeb355a59f704c75d97ce6d3c7cf2bf0add1a1b85ca4c223d83293e4688e2e5`
- release binary sha256：
  `7473f6c9a5dc8a1a040a45ce1e3844ee20b3cb95b6a765f248df8f58e52c90e6`
- config sha256：
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`
- model tree manifest sha256：
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`

Binary-only deploy：

- deploy id：`r5-865e0d8-binary-deploy-20260626T033132Z`
- remote binary/config/model sha 校验通过。
- `r5-actor-rehearsal` validator/artifact_validator passed。
- `sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- `no_submit_rehearsal_report.json` sha256：
  `1232b86dc2e1554411ca9b98c6820f6c83bfa09304994d05398c48f1f5fcd25e`

Pre-live gates：

- no-live 前只读 open-order check：`platform-open-orders-check-20260626T033225Z`，
  `status=passed`、`open_order_count=0`、`open_order_ids=[]`、report sha256
  `39fe0e4abf69cb57964a14428b30e94605657cf07891d1cb3efa1652308ace08`，bundle manifest sha256
  `d58dd0cddcd5190fc7e3b2ab837bdbcf9509e5f8b597f17edbdeffd2977245a5`。
- production `--no-live-funds` gate：`platform-sellable-maturity-no-live-20260626T033248Z`，
  `status=no_live_funds_passed`、`sdk_post_attempt_count=0`、`sdk_cancel_attempt_count=0`、
  `fail_closed_reasons=[]`，gate report sha256
  `8e17fda21dbe170a4062eadafe3783b3158eb1d42a364d67b19c084cc0e38de9`，bundle manifest sha256
  `9315ab992e3aa2e5db58ea0b73e099c73ae5b0b0f3be81ea1dc9096c62372010`。
- live 前只读 open-order check：`platform-open-orders-check-pre-live-20260626T033315Z`，
  `status=passed`、`open_order_count=0`、`open_order_ids=[]`、report sha256
  `f52bf673f68c5135868be30144c14c653abe3be927dcdd8571201c38cf930de8`，bundle manifest sha256
  `3eb3a2100345417186019311e3863e124f876a1a714a61be8a506c4bbf797377`。

真实资金 probe：

- run id：`platform-sellable-maturity-live-20260626T033334Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260626T033334Z/`
- CLI summary：`status=FailClosed`、`valid_samples=11`、`sdk_post_attempts=271`、
  `sdk_cancel_attempts=12`、`hard_reasons=1`
- gate report：`status=fail_closed`、`valid_sample_count=11`
- fail reason：`sample-0012:buy submit was not accepted`
- gate report sha256：`393ea38e0c69a4816deaed7ed70272d8f2910fb13743805af2651ab9d08560e3`
- fail trace sha256：`1e12de7b19e452f8eaf570e5af86974b91dfae619540f87b5071d4ae03f9b056`
- bundle manifest sha256：`939c620dadea9b1e4d2186289532cff4be4a98b22bc44b1147c4ab0d08a0e969`

有效样本与排除样本：

- `sample-0000` 到 `sample-0010` 共 `11` 个 valid sample。
- `first_clean_accept_ms`：`1964,2495,1828,2451,2307,821,2139,1016,1887,1396,1176`；
  median `1887ms`，max `2495ms`。
- `sample-0011` 为 partial BUY，fill `4.990929`、residual `0.009071`，命中
  `VenueDustTerminal`，写 invalid sample 并重采样；该路径未 fail closed。

Post-live safety checks：

- open-order check：`platform-open-orders-check-post-live-20260626T040306Z`，
  `status=passed`、`open_order_count=0`、`open_order_ids=[]`，report sha256
  `c3aea890b062d30b0ac41c6aec90814614a1b250766a6bf60d4cea4885dc5352`，bundle manifest sha256
  `2721853d272bb323751419c64597dccbc5e7803c2ace56d6da049cb1c71690be`。
- account snapshot：`post-live-account-snapshot-20260626T040306Z`，
  Data API positions queried OK，`data_position_count=0`、`data_total_value_usdc=0`、
  `position_count=0`、`total_value_usdc=0`，wallet balance `75260557 raw_6_decimal_usdc`。
  `account_snapshot.json` sha256
  `65d146cf488633e6780a810446c8d61d4f4c0883c1155d627bba4e6a5cfceda4`；
  `position_value_snapshot.json` sha256
  `5ec79a228f02f98c3e67a3ceaadddb4aef83bdfab64337e9ff887bc601c6edb1`；bundle manifest sha256
  `fd88fe45ad9c223e9dbba8756f0cddd33584978c14bdf5e004b67b677eedc670`。

当前失败原因边界：

- 本轮不是 clean SELL accepted 后 cleanup cancel hard gate 复发，也不是 venue-dust partial BUY cleanup
  复发。
- `sample-0012` BUY 候选本地 pre-submit gate 通过：market `btc-updown-5m-1782446400`、UP、
  best ask `0.47`、buy price `0.47`、size `5`、notional `2.35`，但 `submit_limit_order`
  返回非 `SdkAccepted`。
- operator 在平台账户观察到提示 `limit buy up failed`，与 artifact 中 `sample-0012` 的 UP BUY
  non-accepted 方向一致；但当前 fail trace 没有持久化 BUY submit 的 `OrderAdapterReport` /
  SDK reject 原文，因此下一步 root-cause review 必须先补 BUY reject evidence 落盘缺口。

当前有效样本数：

- 最新 run `platform-sellable-maturity-live-20260626T033334Z`：`11/30`。
- 本计划下此前已拉回 live runs 去重 raw valid samples 为 `11/30`；本轮新增 11 个 valid sample。
  是否把历史与本轮合并为训练可用样本，必须在 root-cause review 后基于去重规则和同一统计口径确认。
- 计划目标仍是单轮获得 `30` 个有效样本；当前未达标。

当时边界（历史，已由下一节本地修复 supersede）：不得直接重跑真实资金 probe。下一步是
`sample-0012` BUY submit non-accepted 的 root-cause review、BUY reject evidence 落盘修复方案、
local tests、GPT-5.5/xhigh review、fresh build、binary-only deploy、production `--no-live-funds` gate、
产物拉回检查和 renewed approval。

## 2026-06-26 JST BUY submit evidence/retry 本地修复

用户批准执行 `sample-0012` BUY submit non-accepted 的本地修复。本次只在本地 worktree 修改代码和文档；
未执行 fresh release build、binary-only deploy、远端 `--no-live-funds` gate 或真实资金 probe。

实现变更：

- `OrderAdapterObservation` 新增审计字段：`post_response_success`、`sdk_http_status`、
  `sdk_status_body`、`retry_after_seconds`。`post_response_success` 来自官方 Rust SDK post response；
  SDK status error 的 HTTP status/body/retry-after 仅在官方 SDK error 可 downcast 时填充，不引入
  raw REST、manual signing 或 shadow implementation。
- `platform_sellable_maturity_gate_report.json` 和
  `platform_sellable_maturity_fail_closed_trace.json` 新增 `buy_submit_attempts`。每次 BUY submit attempt
  记录 `sample_id`、`attempt_index`、market/asset/outcome、BUY price/size/notional、submit/response
  timestamp、`final_status`、`reject_class`、`retry_decision`、`retry_after_ms` 和 normalized
  `OrderAdapterReport`。
- BUY submit retry 改为白名单 bounded retry：只有无 `platform_order_id`、无 `trade_ids`、无
  `transaction_hashes`，且错误属于 `MARKET_NOT_READY`、HTTP `425`、HTTP `429` 或 HTTP `500`
  exact `could not insert order` 时，才允许最多初次 + 3 次 retry。空/`UNKNOWN` status 但没有明确
  transient evidence 时不 retry。
- BUY `not enough balance / allowance`、认证/签名/owner/signer/geoblock/banned、tick/min size/price/
  expiration/duplicate、restricted mode / post-only / cancel-only / trading disabled、带落单证据
  reject、普通 timeout / ambiguous `SdkError` 均不 retry，直接 fail closed with evidence。
- `cumulative_buy_intent_notional` 从 submit 前移动到 BUY `SdkAccepted` 且有非空 platform order id 后；
  rejected BUY 不消耗 run-level accepted BUY notional cap。
- SELL probe 语义未改：first same-asset clean SELL accepted 仍是 maturity 成功终点；accepted 后成交、
  cancel、open-order audit 仍只作为 cleanup/manual-review evidence。venue-dust partial BUY cleanup
  语义未改。

测试验证：

- `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test
  platform_sellable_maturity_runner --quiet`：`41/41` passed。
- `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test
  sdk_order_adapter --quiet`：`16/16` passed。
- `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test
  platform_sellable_maturity --quiet`：`8/8` passed。
- `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test
  cli_platform_sellable_maturity --quiet`：`3/3` passed。
- `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`：passed。
- `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`：passed。
- `git diff --check`：passed。

新增覆盖：

- transient BUY reject retry 后 accepted，并写入 `buy_submit_attempts`。
- retryable BUY reject exhausting 后 fail closed，并记录全部 4 次 attempts。
- permanent reject 不 retry。
- 带 `platform_order_id`、`trade_ids` 或 `transaction_hashes` 的 ambiguous reject 不 retry。
- BUY `not enough balance / allowance` 不 retry。
- HTTP `500` exact `could not insert order` 且无落单证据时可 bounded retry。
- HTTP `500` 非 exact `could not insert order` 不 retry。
- 普通 timeout / ambiguous `SdkError` 不 retry。
- restricted mode / post-only / cancel-only / trading disabled 即使带 `retry_after_seconds` 也不自动 retry，
  只记录 `retry_after_ms` 供人工复核。
- 空/`UNKNOWN` status 但没有明确 transient evidence 时不 retry。
- lowercase `market not ready` 不等于 exact `MARKET_NOT_READY`，不 retry。
- rejected BUY 不消耗 run-level accepted BUY notional cap。

GPT-5.5/xhigh 只读 review 已通过：文档边界 PASS，代码 review PASS；代码 review 的 `cancel-only`
no-retry minor 已补入测试矩阵并完成增量复核。当前变更集提交/推送后，fresh build、binary-only
deploy、production `--no-live-funds` gate 和真实资金 probe 仍未授权，必须后续单独申请并获得
renewed approval。

## 2026-06-26 JST `970bd20` renewed live execution

用户批准执行 fresh build、binary deploy、远端 `--no-live-funds` gate；这些全部通过后执行真实资金
probe。本轮执行 commit `970bd20ab693bb1a7a29923af62cd485a1ab5bab`。

Fresh release build：

- dirty state：`clean`
- git diff provenance sha256：`c8ae712976577a3ccad6cefd3a05e59ed2e89332247c5e9b20e5d3a5a6123d03`
- release binary sha256：
  `acde204b0336d74793b0e61eb387ce224f8b3ef1c18debc0e31157da557fb565`
- config sha256：
  `e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`
- model tree manifest sha256：
  `a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`

Binary-only deploy：

- deploy id：`r5-970bd20-binary-deploy-20260626T053539Z`
- remote binary/config/model sha 校验通过
- `r5-actor-rehearsal` validator/artifact_validator passed
- `sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- no-submit rehearsal report sha256：
  `303771215e7b8c44acb8692148990371cb2d5591a1b134aed511b69b82bed00b`

No-live 前只读 open-order gate：

- run id：`platform-open-orders-check-20260626T053624Z`
- status：`passed`
- `open_order_count=0`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-20260626T053624Z/`
- report sha256：
  `16b13ef379542540449097ff0f12ab83db584f73640fe9ed75ab939cac0e6a4e`

Production `--no-live-funds` gate：

- run id：`platform-sellable-maturity-no-live-20260626T053651Z`
- status：`NoLiveFundsPassed`
- `valid_samples=0`、SDK post/cancel `0/0`、`hard_reasons=0`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-no-live-20260626T053651Z/`
- gate report sha256：
  `741b3b457373271bb2c160c8aa1eee238a4daa40ad8b80bcfef5d3014d15f8d2`

Live 前只读 open-order gate：

- run id：`platform-open-orders-check-pre-live-20260626T053718Z`
- status：`passed`
- `open_order_count=0`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-pre-live-20260626T053718Z/`
- report sha256：
  `8fd72b5481e6a0dbf8a254bbe8d5f83ffbb97449524f8190cffa206bd4da6f69`

真实资金 probe：

- run id：`platform-sellable-maturity-live-20260626T053750Z`
- status：`FailClosed`
- CLI summary：`valid_samples=3`、SDK post/cancel `55/4`、`hard_reasons=1`
- hard reason：`sample-0003:BUY cleanup cancel after insufficient fill was not accepted`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-sellable-maturity-live-20260626T053750Z/`
- gate report sha256：
  `77bc6e454783bcad62d3bd23b345d333c1c4181b0ab9cbc7e34c927f2f16e724`
- fail trace sha256：
  `c771ecc6f27d695b64916a8d00ec364c0f36a9708077839ea8c1444f66b9acef`

失败证据：

- 这次不是 BUY submit reject 复发。`sample-0000..0003` BUY submit 均为 `SdkAccepted` 且有
  non-empty platform order id。
- `sample-0003` BUY：market `btc-updown-5m-1782452400`、DOWN、best ask `0.52`、buy price
  `0.52`、configured buy size `5`、notional `2.60`。
- `sample-0003` BUY submit accepted order id：
  `0x24968d855b840c810084c76bb9a36f0e56fb4431a36d99e1f379a34d217f54cd`。
- SDK post response for `sample-0003`：`sdk_status=MATCHED`、`making_amount=1.716`、
  `taking_amount=3.3`、tx
  `0x869c7063b8e686df29717c3028acb16e7b4968a1ee55e9f7c9fdd8267f6fb99a`。
- 因 `fill_size=3.3 < probe_size=5` 且 residual `1.7` 大于 venue-dust threshold，runner 进入
  partial BUY cleanup cancel 路径；cleanup cancel report 非 `SdkAccepted`，当前代码按 hard
  fail-closed 处理。
- `sample-0000..0002` 仍为 valid samples：first clean SELL accepted 分别约 `909ms`、`1049ms`、
  `1991ms`，post-cancel open orders 均为 `0`。

Post-live safety checks：

- open-order check run id：`platform-open-orders-check-post-live-20260626T054054Z`
- status：`passed`
- `open_order_count=0`、`sdk_post_attempted=false`、`sdk_cancel_attempted=false`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/platform-open-orders-check-post-live-20260626T054054Z/`
- report sha256：
  `4d08801bdd6dea621405b7877357790e84ebf6f0d788222077427104c9bd8ab2`

Post-live account snapshot：

- run id：`post-live-account-snapshot-20260626T054201Z`
- 本地 pullback：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/pullback/post-live-account-snapshot-20260626T054201Z/`
- `account_snapshot.json` sha256：
  `b0d7feb3a62fa253a07c03b36ba0dd86051cfa3f406377f69352f7397addd867`
- `position_value_snapshot.json` sha256：
  `613036a839ffd5fd8f7906075aa0534d611188277c70e846e69fa5041cd54aa3`
- `reconciliation_report.json` sha256：
  `72570e0ab496ffb169960158ebc6e1dc599af6da033679f509b7d66eda28ff7f`
- Snapshot 显示 `open_order_count=0`，但 `data_position_count=2`、`data_total_value_usdc=4.1245`，
  position/value 包含 UP `5` shares（value `2.025`）和 DOWN `3.3` shares（value `1.9634`）。
- Reconciliation `allows_new_orders=false`，reasons 包含 `data_position_up_mismatch`、
  `data_position_down_mismatch`、`data_position_value_total_mismatch`、`trade_history_unavailable_blocks_new_orders`
  和 `audit_incomplete`。

当前边界：不得继续真实资金 probe。`sample-0003` partial BUY cleanup cancel fail-closed 已完成 root-cause
review；active plan `## 0` 本地代码/文档收口和本地验证已完成，当前待执行 GPT-5.5/xhigh subagent
复审与必要 remediation。任何后续 live 仍需 fresh build、binary-only deploy、production
`--no-live-funds` gate、产物拉回检查和 renewed approval。
