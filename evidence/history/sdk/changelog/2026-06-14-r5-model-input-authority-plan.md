# 2026-06-14 R5 model input authority and lifecycle consistency plan

## 背景

用户根据 2026-06-13 live-funds run 的 PnL/reporting 差异、raw USDC 单位问题和 artifact
审查结果，怀疑模型没有正确看到当前持仓盈亏和真实账户数据。主 agent 派生 GPT-5.5/xhigh
subagents 做只读审查后确认：旧 run 中 `cash/nav` 曾以 raw 6-decimal 大数进入
`model_visible_account_state`；同一进程内已入账 shares/active order count 会进入模型，但启动前
平台持仓、历史亏损或未恢复本地 ledger 不会自动进入 initial ledger；artifact 也缺少 per-tick
feature/policy tensor 可复算证据。

## 变更

- 在当前权威计划
  `poly-arb-ai/sdk-live-trade-docs/plan/2026-06-13-r5-local-ledger-authoritative-trading-plan-compact.md`
  新增 `Phase 4 / Task 13：模型输入权威性与订单 lifecycle 一致性修复`。
- Task 13 将下一阶段阻断修复拆成 startup ledger authority、raw USDC 全入口归一、decision input
  generation、SDK/user-channel evidence visibility boundary、pre-ack user-channel buffer/replay、
  SDK matched post synthetic fill 与 real trade exactly-once、accepted post reservation failure
  fail-closed、真实 model input/output audit hash、normalization contract 复核和 PnL/reporting 分层。
- GPT-5.5/xhigh plan review remediation 后，Task 13 进一步补充：
  - official-history 恢复必须证明 maker/taker/all wallet fills 覆盖；SDK 不能证明时 fail closed。
  - startup ledger restore 必须落到唯一 verified restore API，恢复 applied trade ids、cost basis、
    realized/settled PnL；active reservations 若缺少可完整重建 runtime active-order state 的证据则
    fail closed。
  - startup 官方 SDK account / position / open order / trade-history 恢复必须 bounded async，并在进入
    market loop 前完成或 fail closed；热路径不得发起、等待或阻塞平台账户/仓位/历史查询。
  - raw USDC 必须走 typed amount `{value, units, source}`，不得靠金额大小猜单位。
  - `visible_at_ms <= t_decision` 的 evidence drain 顺序必须早于 active count / NAV / TTL / model input，
    future evidence 不得 suppress 当前 due TTL cancel。
  - pre-ack user trade buffer 必须在 mapper 丢 candidate id 前截获 raw trade，并落 capacity/expiry telemetry。
  - matched-post synthetic/real exactly-once 必须在 `OrderArbitrator` 层处理。
  - feature labels 必须来自 `V2_FEATURE_NAMES`；`cash/nav` 只属于 `account_state` 审计，不作为 V2 160
    维 feature label。
  - fresh run artifact 必须用 tensor sidecar 或等价 proof 让 validator 可重算 feature/account/alpha/policy
    hash，并拒绝 fake non-placeholder hash。
  - 二次 GPT-5.5/xhigh plan review 后，Task 13 的验收测试进一步补全 cancel/no-submit/no-change
    policy-rendered strategy outcome 的 `policy_output_hash` 链接，明确 pre-policy `inference_no_order`
    不伪造 policy/strategy linkage，补全 `account_state_hash`、
    `alpha_hash`、`policy_output_hash` fake hash 和 sidecar mismatch/orphan 负例，并补全
    normalization contract evidence 的 artifact-validator 负例。
- 更新当前游标和完成标准：Task 13 本地关闭后仍不得生成 fresh executable approval，不得执行
  live-funds run；下一轮资金运行必须另走 fresh approval 和 fresh binary/build/deploy 验证。
- Task 13 Step 1/2 follow-up：`live_validation_r5_execution.rs` from-files runtime 已在进入 market loop
  前执行 bounded official SDK startup account/open-order/trade-history/Data API snapshot，并把 snapshot
  report 收敛为 startup ledger authority 后恢复 initial ledger；snapshot fail-closed、已有 open order 或
  未覆盖 trade history 会在 submit 前 fail closed。
- Task 13 Step 2 follow-up：approval `execution_disclosure.local_starting_cash_usdc` 已新增显式
  `local_starting_cash_units`，仅允许 `usdc_decimal` / `raw_6_decimal_usdc`；production from-files
  initial ledger 不再使用 approval starting cash，测试保留的 raw-like helper 缺失 units 时会 fail closed。

## 2026-06-14 实现进展

本轮已完成 R5 Task 13 本地实现、targeted/full verification 和 GPT-5.5 xhigh review gate；改动范围仍限制在 R5 Task 13：

- 文档状态修正：权威 plan 的 Task 13 checklist、Step 1-13、最终 full verification 和
  GPT-5.5/xhigh review gate 均已更新为本地关闭；2026-06-14 用户后续批准并执行的 fresh
  live-funds run 已记录为 fail-closed blocker，不构成下一轮资金运行授权。
- 同步 `lastest-command.md` 的 R5 startup gate 语义：平台账户、Data API 和 CLOB history 仍不得作为
  trading-loop/hot-path gate；Task 13 允许且要求 market loop 前 bounded official SDK startup recovery
  生成/校验 startup ledger authority，恢复超时、SDK 能力不足或证据不一致必须在 submit 前 fail closed。
- 新增 `r5_startup_ledger_authority.rs` 与测试，建立 startup authority contract、typed `UsdcAmount`、
  resume checkpoint scope/hash 校验、official-history maker/taker/all-wallet coverage 校验和 verified
  ledger restore API。
- resume checkpoint loader 已收紧：路径拒绝已存在 symlink ancestor/path，`resume_checkpoint` evidence
  使用实际读取 bytes 的 sha256；checkpoint 恢复必须与 startup platform snapshot 的 cash/positions/open-orders
  交叉校验，任何未恢复 open order、cash mismatch 或 position mismatch 都在 market loop 前 fail closed。
- 修复 SDK startup account snapshot raw 6-decimal USDC 入口：`account_snapshot.rs` 写出
  `balance_units`，`no_submit_rehearsal.rs` 复用 `startup_balance_usdc`。
- 修复 no-submit/rehearsal decision input generation 固定 0 的问题，并将 runtime model input audit 绑定到
  feature/account/alpha/policy hash。
- Runtime 审计不再写 placeholder `feature_hash="000...0"` / `account_state_hash="111...1"`；artifact
  validator 会重算 account/feature hash，拒绝缺失 feature tensor sidecar、fake feature hash、
  fake account hash、missing alpha values 和 missing policy output values，并验证 normalization contract
  evidence；fake alpha/policy hash 负例已补齐。
- accepted post reservation 失败改为 fail closed，记录 `r5_accepted_post_reservation_failed:*`。
- `UserChannelMapper` 新增 `UnresolvedTrade`，pre-ack user-channel trade 在 known order 注册前保留
  candidate order ids、matched amount、event timestamp、local observed timestamp 和 raw payload hash。
- Runtime 新增 bounded unresolved user trade buffer/replay；post ack 注册 known order 后会在下一次模型输入前
  replay；buffer capacity/expiry 会 fail closed，且 retained expired unresolved buffer 不得抢占同一 slot
  已到期 TTL cancel。
- `R5SdkLiveTickSource` 已把 SDK user-channel `UnresolvedTrade` 传入 runtime unresolved buffer；pending
  unresolved trade 未过期且暂不可 replay 时，runtime tick-local no-submit，不再继续发出新 submit，同时仍先刷新
  ledger/account_state 并允许 due TTL cancel 进入 cancel path。
- `R5SdkLiveTickSource` 内部 pending user-channel lifecycle/unresolved buffer 已加本地限容，overflow 写入
  tick-local reason，避免进入 runtime 前先形成无界 Vec。
- User-channel lifecycle evidence 新增 `local_observed_ms` / `visible_at_ms`，runtime 会 defer
  `visible_at_ms > slot.tick_ms` 的 lifecycle evidence；SDK completion defer/apply targeted regression
  已补齐。
- SDK completion 在当前 decision/event time 之后完成时会 defer 到后续可见边界或 runtime-end drain，
  避免当前 tick 模型输入消费未来 ack/fill。
- Normalization contract 已收紧为 alpha 必须匹配 shared normalization；policy normalization 若与 shared 不一致，
  必须由 artifact manifest 显式写 `policy_normalization_source="not_used_by_policy_onnx"` 且 verdict passed。
- 新增 matched-post synthetic fill 与后续 real trade id 去重回归测试；review remediation 后，later real
  user-channel trade 即使是实际 adapter 形状 `PartialFill + size_matched=None + terminal_status=None`，只要
  订单已由 `sdk_matched_post:<order>:` synthetic fill 标记为 Filled，就走 audit-only dedupe，不再因
  ledger apply failed 升级 fail-close。
- Hegel 第二轮 re-review 发现 matched-post audit-only guard 过宽；已新增
  `r5_matched_post_conflicting_real_trade_requires_reconciliation`，并收窄为后续 real trade 只有与
  synthetic fill 在 order/asset/side/price/size/ledger-impact 数值上等价才 audit-only，不等价直接
  `matched_post_real_trade_conflict` fail-close。
- Review remediation 后，lifecycle blocked report 不再被粗暴全部升级为 fail-close；仅
  `ledger_fill_apply_failed` 这类会造成 ledger/arbitrator 不一致风险的 blocked reason 会升级停机，保留既有
  可审计 warning 行为，避免扩大交易阻断面。
- Runtime audit 对每条 `model_visible_account_state` 都写可复算 `account_state_hash` / labels / values；
  artifact validator 现在会拒绝 non-model-action tick 删除 account hash 的 artifact，并拒绝
  `decision_input_generation` 随 tick 回退或重复。
- 首轮 GPT-5.5/xhigh implementation review 已执行：startup/units/docs 审查 PASS；runtime/lifecycle 与
  artifact/model-audit 审查 FAIL 中的 actionable 项已完成 remediation。TTL due 与 expired unresolved 同 tick
  的风险已用 targeted tests 覆盖：新来的 expired unresolved trade 与 retained expired unresolved buffer
  均不得抢占 due TTL cancel；policy-rendered strategy output-to-intent validator 链接已补齐，pre-policy
  `inference_no_order` 明确无 policy/strategy linkage。
- Task 13 Step 1/2 追加实现：from-files `runtime_context` startup step 现在复用 official SDK
  `run_startup_account_snapshot()`，按 selected market/wallet scope 构造 `AccountSnapshotContext`，将
  `StartupAccountSnapshotReport` 转成 `StartupAuthoritySnapshot`，再通过
  `build_r5_startup_ledger_authority()` / `initial_ledger_from_startup_authority()` 生成 initial ledger。
  该路径保持在 bounded startup watchdog / timeout 内，进入 market loop 后不做平台账户/仓位/历史查询。
- Approval schema 追加 `local_starting_cash_units` 并强制校验；旧的 production raw-like integer heuristic
  已从 from-files initial ledger 路径移除。
- 复审 remediation：startup authority summary 已写入 `r5_execution_report.json` / `run_manifest.json`，
  包括 mode/status、snapshot age、evidence hashes、elapsed/timeout 和 applied-trade /
  active-reservation count；from-files snapshot age 改为 startup snapshot 查询开始到 authority build 完成
  的耗时，不再把 snapshot timestamp 与 authority `now_ms` 设成同一时刻；`run_manifest.json` 路径已改为
  runtime audit bundle create-new manifest 直接携带该 summary，不依赖 execution wrapper 事后补写。
- Task 13 Step 1 追加实现：approval `execution_disclosure.resume_checkpoint_path` 支持 scope 校验；
  checkpoint loader 计算实际读取 bytes 的 sha256 作为 `resume_checkpoint` evidence，拒绝 symlink path/
  ancestor，恢复 cash/shares/cost basis/realized/settled PnL 与 applied trade ids，并与 platform snapshot
  交叉校验。active reservation ids 不能完整重建 runtime active-order/TTL/strategy state 时显式 fail closed，
  不把未恢复挂单伪装为 active count 0。
- Task 13 Step 8-12 追加实现：feature labels 来自 `V2_FEATURE_NAMES`，补齐 agent/PnL label coverage；
  post-run report 分离 model-local ledger PnL 与 platform wallet total PnL；无完整平台 snapshot 或 NAV
  不可观察时写 unavailable；artifact validator 补齐 wrong rolling-window hash、fake alpha/policy hash、
  strategy linkage、reservation failure、unresolved buffer 和 PnL/reporting invariant。
- Mill re-review remediation：OrderArbitrator 现在对 partial 与 terminal matched-post 都执行 synthetic-to-real
  id replacement，alias 后第二个 same-size real trade 会以 `matched_post_real_trade_conflict` fail closed；
  retained expired unresolved buffer 触发 fail-closed 前会按当前 `now_ms` 生成所有已到期 TTL cancel，而不是只处理
  earliest due order。
- Follow-up review remediation：确认 `matched_post_real_trade_conflict` 是 lifecycle/ledger authority
  failure guard，不是模型交易决策限制；runtime 现在在 deferred/source/replay lifecycle merge 或 SDK completion
  merge 后，只要已有 fail-close reason，就在进入 active count、NAV、account_state、inference 或 SDK submit
  前同 tick short-circuit；SDK completion wait loop 内也会立即 break 成 fail-closed tick report，不再重新进入
  source context / active count。
- deferred lifecycle evidence queue 与 deferred SDK completion queue 均已加 bounded capacity，future-visible
  drain 改为稳定顺序；overflow 在进入模型输入前 fail closed，不再允许未界定的本地 lifecycle/SDK backlog
  污染后续 tick。
- incoming unresolved overflow / expiry fail-close 前的 due TTL cancel 优先级已用 regression 覆盖；retained
  buffer 与 incoming ingest direct 分支均要求先 enqueue due TTL cancel，再记录 unresolved fail-close。
- artifact validator 增加 post-policy decision tick 必须有 expected `production_strategy_*` outcome row 的反向
  invariant；删除整行 strategy outcome 的 artifact 会以 `post_policy_strategy_audit_missing` 拒绝。
- Pascal follow-up review 发现 SDK completion fail-close short-circuit 缺独立回归；已新增
  `r5_runtime_sdk_completion_fail_close_short_circuits_before_next_live_tick`，覆盖 visible SDK completion merge
  产生 fail-close 后 tick1 不调用 live source、不进入 inference、不二次 submit。
- 文档同步：blocking pattern scan 允许人工确认的 `#[cfg(test)]` fixture 写文件命中，但 production blocking
  命中必须为 0；Task 13 文件清单补入 `r5_model_input_audit.rs`；model artifact 明确为运行产物，不得通过
  Git/GitHub/服务器 `git pull` 同步，也不得放入 `wallets/`。

当前剩余 gate：

- Task 13 本地实现、targeted/full verification、GPT-5.5/xhigh review gate 和文档收尾已完成。
- 用户后续批准的 fresh executable approval `r5-fresh-executable-20260614T120348Z` 已生成并执行；
  该 live-funds run 真实进入 SDK post/cancel 路径，但以 fail-closed 结束。Task 13 本地关闭和这次
  fail-closed run 均不构成下一轮资金运行授权。

## 验证

已执行：

```bash
git diff --check
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade r5_user_channel_buffers_trade_for_unknown_order_until_post_ack_registers_known_order --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade r5_runtime_replays_pre_ack_user_channel_trade_before_next_model_input --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_runtime_pending_unresolved_user_trade_blocks_new_submit_without_fail_close --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade r5_runtime_defers_user_channel_trade_observed_after_decision_tick --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_order_lifecycle r5_matched_post --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_runtime_model_visible_account_state_always_writes_recomputable_account_hash --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_runtime_model_visible_account_state_generation_is_monotonic_by_tick --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_artifact_validator_rejects_missing_account_hash_on_non_model_action_tick --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_artifact_validator_rejects_non_monotonic_decision_input_generation_by_tick --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_runtime_ttl_due_cancel_runs_before_unresolved_trade_expiry_fail_close --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_runtime_ttl_due_cancel_runs_before_unresolved_trade_overflow_fail_close --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade due_ttl_cancel_is_prepared_before_retained_unresolved_buffer_fail_close -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade r5_runtime_pre_policy_inference_no_order_skip_has_no_strategy_policy_linkage --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade drain_visible_lifecycle_evidence --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade r5_runtime_sdk_completion_fail_close_short_circuits_before_next_live_tick --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_runtime_deferred_lifecycle_queue_overflow_fail_closes_before_submit --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_runtime_matched_post_conflict_fail_closes_before_same_tick_submit --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_artifact_validator_rejects_post_policy_tick_without_strategy_row --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade drain_visible_sdk_completions --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade deferred_sdk_completion_capacity_exceeded_fail_closes --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade no_submit_rehearsal::tests::r5_live_tick_source_pending_user_channel_items_are_bounded --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test user_channel --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_user_channel_lifecycle --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_order_lifecycle --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test order_arbitration -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test ledger -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test live_validation_r5_execution --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test live_validation_r5 --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade live_validation_r5_execution::tests --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_artifact_validator --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_startup_ledger_authority -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test production_strategy_intent -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test live_validation_r5 -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade startup_snapshot_report_restores_resume_checkpoint_before_market_loop -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade startup_resume_checkpoint_loader_uses_file_sha_as_checkpoint_evidence -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade startup_resume_checkpoint_loader_rejects_symlink_path -- --nocapture
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade restored_applied_trade_ids_dedupe_without_order_payload -- --nocapture
cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all
cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check
cargo check --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet
```

结果：targeted / related suites 当前退出码为 0；`r5_startup_ledger_authority` 16/16、
`live_validation_r5` 14/14、`live_validation_r5_execution` 24/24、`r5_artifact_validator` 25/25、
`r5_single_market_runtime` 101/101、`r5_order_lifecycle` 19/19、`order_arbitration` 12/12、
`ledger` 11/11、`production_strategy_intent` 13/13 通过；checkpoint loader/restore、retained-buffer
TTL helper 和 restored applied trade id ledger filters 通过。最终 fresh `cargo fmt --all -- --check`、
`git diff --check`、`cargo check -p sdk-live-trade --quiet` 和完整 package test 均已退出码 0；blocking
pattern scan 只命中 `#[cfg(test)]` fixture 写文件。Hilbert/Mill/Singer follow-up re-review 均 PASS。
最新 Pascal/Peirce/Averroes follow-up re-review 均 PASS。

## 2026-06-14 fresh executable live-funds run

- 提交并推送：`90838a0 sdk-live-trade: close r5 model input authority`
  (`90838a07e4412f5d4d42d3e941ac89cc6f119d1f`) 已 push 到 `origin/sdk-live-trade`。
- fresh release binary：`poly-arb-ai/rust/sdk-live-trade/target/release/sdk-live-trade`，
  binary sha256 `dd6d3b09f247ef0d6b70ea8c1db4739cd70212600a1a70e7ad7299e2366be5d6`；
  build git dirty state `clean`，git diff sha256
  `218f6e2e9f339166c0ccdf8821503bc18336abdb0d8be89cf633d4b06e337bf0`。
- fresh approval：`r5-fresh-executable-20260614T120348Z`，local path
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/approvals/r5-fresh-executable-20260614T120348Z.json`，
  remote path
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/approvals/r5-fresh-executable-20260614T120348Z.json`，
  approval sha256 `15183018d9ca2c9395ceec9bfe463c3bbdc26b8bb05a3fc17168a4f9ebc4492a`。
- exact market：`btc-updown-5m-1781438700`，window `1781438700..1781439000`，condition id
  `0xb5030d3e05cc7dbeed3e1040005cf24944eee9491a184878d4051c1632fee396`。
- run artifacts：remote
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/R5-execution/r5-fresh-executable-20260614T120348Z-run`，
  local archive
  `poly-arb-ai/rust/sdk-live-trade/artifacts/remote-r5-runs/r5-fresh-executable-20260614T120348Z-run`，
  artifact bundle sha256 `8a9ee64f059870410317496bf7e8724eb874a5c7ebdace7620e6c684644ea064`。
- result：`runtime_status=submit_cancel_runtime_pending`、`fail_closed=true`、`sdk_post_attempted=true`、
  `sdk_cancel_attempted=true`、`sdk_post_attempt_count=4`、`sdk_cancel_attempt_count=4`。
- fail-closed reasons：
  `r5_single_market_runtime_live_feature_refresh_failed:r5_live_feature_producer:CadenceGap { expected_ts_ms: 1781438746000, decision_ts_ms: 1781438746250 }`
  and
  `r5_runtime_audit_bundle_failed:ttl_cancel_not_terminal_or_accepted_for_live_order:0x4754670fe82f30122e4d9d64ab27dd82a7b9359d23fa796e70f943a7b3fbc16e`。
- 初步定位：TTL timer 在 `1781438745777` 触发并消费了一格 decision-slot，导致
  `LiveFeatureProducer` 之后看到 `1781438746000 -> 1781438746250` 的 lattice gap；同一订单先由
  `model_no_quote` cancel accepted，随后 TTL cancel 返回 already canceled，现有 TTL artifact validator 未把该
  先行终态识别为 TTL evidence。
- next gate：修复上述 blocker，重新执行 targeted/full verification 与 review；下一轮 live-funds run 必须先完成
  fresh binary/build/deploy 验证，再重新生成绑定该产物和新 market/window 的 fresh executable approval，并获得用户明确批准。

## 2026-06-14 cadence / TTL evidence blocker 本地修复

- 用户批准执行顺序：先本地修复 cadence/TTL evidence blocker，再重新验证/review；生成新的 fresh
  executable approval 后允许直接执行 live-funds run，不复用 `r5-fresh-executable-20260614T120348Z`。
- runtime 修复：`R5LiveTickOrTtlDue::TtlDue` 触发后，对 quote-ready 且未 fail-closed 的 decision slot
  只写独立 TTL timer audit tick，再继续等待同一个 lattice slot 的 live feature tick；market-closed /
  hard-guard slot 保持消耗 slot 的既有语义，避免 market closed TTL regression。
- artifact validator 修复：accepted live post 仍必须存在 TTL cancel command / due / ack timing evidence；
  但当 TTL cancel 本身返回 already-canceled 类结果时，允许同一 `platform_order_id` 的 SDK cancel
  terminal/accepted evidence 来自先行 `model_no_quote` 等 cancel path，避免 false-fail；该 fallback
  只接受 `cancels.jsonl` row `timestamp_ms <= TTL cancel attempt timestamp_ms` 的同订单 evidence。
- audit timestamp 修复：runtime 现在为每个 `R5ApprovedSdkExecutionOutcome` 保留 SDK actor request/done
  timing，`orders.jsonl` / `cancels.jsonl` / arbitration / fills rows 使用对应 outcome 的 done time 写
  `timestamp_ms`，post/cancel payload 也写出 `sdk_actor_request_start_ts_ms` 与 `sdk_actor_done_ms`。
- 新增 regression：
  - `r5_runtime_ttl_timer_does_not_consume_quote_ready_decision_slot`
  - `r5_artifact_validator_accepts_ttl_cancel_when_prior_model_cancel_closed_order`
  - `r5_artifact_validator_rejects_ttl_cancel_prior_terminal_for_different_order`
  - `r5_artifact_validator_rejects_ttl_cancel_same_order_terminal_after_ttl_attempt`
- 本地验证已通过：
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_runtime_ttl_timer_does_not_consume_quote_ready_decision_slot -- --nocapture`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_artifact_validator_accepts_ttl_cancel_when_prior_model_cancel_closed_order -- --nocapture`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_artifact_validator_rejects_ttl_cancel_prior_terminal_for_different_order -- --nocapture`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_artifact_validator_rejects_ttl_cancel_same_order_terminal_after_ttl_attempt -- --nocapture`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime --quiet`：105/105
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_artifact_validator --quiet`：25/25
  - `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`
  - `git diff --check`
  - production blocking-pattern scan：production 0 命中，仅 `#[cfg(test)]` fixture 的 2 个写文件命中
  - `cargo check --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
- GPT-5.5/xhigh review gate 已关闭：Confucius follow-up validator review 和 Laplace follow-up runtime /
  validator review 均 PASS，无 Critical/Important blocker；Laplace 剩余一条 future-hardening 建议不阻塞合并。
- 本地提交已 push：`01d314a sdk-live-trade: fix r5 ttl cadence evidence blocker`。

## 2026-06-14 cadence / TTL blocker follow-up fresh live-funds run

- fresh release build：commit `01d314ad4b63f13d6428e89b11bf76f60399fc96`，dirty state `clean`，
  dirty diff sha256 `b45df812ef20f55fe6196acb5a5519ca6f8113b67ff1a39623b44de4bc7a6a85`，
  binary sha256 `c645e38ac87b499f87c22b4e93a1fcede72bb76a4a559e40d70678900dadd033`。
- fresh binary/deploy rehearsal：
  `r5-cadence-ttl-fresh-binary-rehearsal-20260614T131550Z`，remote path
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/no-submit-rehearsal/phase4-cadence-ttl-fresh-binary-rehearsal/r5-cadence-ttl-fresh-binary-rehearsal-20260614T131550Z`，
  local path
  `poly-arb-ai/rust/sdk-live-trade/artifacts/remote-r5-runs/r5-cadence-ttl-fresh-binary-rehearsal-20260614T131550Z`；
  report sha256 `67e7a44ad325fcc93a7c11df3625ab630f71151bc6211053dde65b5158dd4782`，
  artifact bundle manifest sha256 `b8316a0af406691f86f55e6d9d8b56e338ed09261b208e4b569d3ee3f59f1b97`，
  feature rows `240`、ready ticks `116`、inference success `116`、SDK post/cancel attempted 均为 `false`。
- 13:25 approval `r5-fresh-executable-20260614T132509Z` 因生成时已错过该窗口启动点未执行。
- 13:30 approval `r5-fresh-executable-20260614T132754Z` 启动后在 SDK submit 前 fail closed：
  `r5_live_runtime_onnx_runtime_unavailable:ORT_DYLIB_PATH does not point to an existing libonnxruntime shared library`；
  `sdk_post_attempted=false`、`sdk_cancel_attempted=false`，single-use marker absent，旧 output dir 已存在且该 approval
  不复用。命令手册已补充 R5 live execution 也必须像 no-submit rehearsal 一样在远端 shell 注入
  `ORT_DYLIB_PATH=[PRIVATE_HOME]/sdk-live-trade/lib/libonnxruntime.so.1`；approval-bound CLI command 本身不包含该
  env prefix。
- executed approval：`r5-fresh-executable-20260614T133230Z`，approval sha256
  `a201aa14ae32988982e7fbe589138f787b9d4f867ffb462febd4b38e3973cac0`，exact market
  `btc-updown-5m-1781444100`，condition id
  `0xb0811f1d9cdf091b1cd2c34f75e65d474143006f36de4daa4f602578745cff95`，window
  `1781444100..1781444400`。
- live result：`runtime_status=submit_cancel_runtime_pending`、`fail_closed=true`、
  `sdk_post_attempted=true`、`sdk_cancel_attempted=true`、`sdk_post_attempt_count=5`、
  `sdk_cancel_attempt_count=4`、`fill_count=2`、`tick_coverage=127`。fail-closed reasons：
  `r5_order_lifecycle_blocked:new_trade_after_filled` and
  `r5_runtime_audit_bundle_failed:ttl_cancel_enqueue_late:0x4804be3a20560a0d88ec287193d7152eb3e03a9e86afffc619c52cf0e5f6fea5:148`。
- final local ledger：`cash=84.21048802`、`shares_up=6.210509`、`shares_down=0`、
  `cost_basis_up=1.46631198`、applied trade ids
  `3c187bc7-7be2-4de6-b944-dfef10e15430` and `d0c1bc74-6382-41c7-b2f9-8ae19b318c5e`。
  final reconciliation verdict is safe/complete:
  `open_order_safe=true`、`position_value_safe=true`、`current_exposure_safe=true`、
  `trade_history_complete=true`、`audit_complete=true`、`allows_new_orders=true`。
- local archive:
  `poly-arb-ai/rust/sdk-live-trade/artifacts/remote-r5-runs/r5-fresh-executable-20260614T133230Z-run`；
  report sha256 `b84bd256e6ab468d49de04987a50d5b931df1ed4c083df7b10b4ad976950bdd0`，
  run manifest sha256 `5de32ecaf1d0f9ff3d5329297a765b8eba0b40273ef93e66789993fb8574c869`，
  artifact bundle manifest sha256 `2f36e4fb6edd6f1f86c59761d8397738746f89043c4502bf27b637ef1aea4890`。
- single-use marker:
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/approval-use-markers/r5-fresh-executable-20260614T133230Z.used.json`，
  sha256 `d3e89aa9fba0083d264b2e5c450845384d36430782190f99a62c59c94918f8b7`。
- next gate：不得继续生成 fresh approval / live-funds run。必须先本地分析并修复新的
  `new_trade_after_filled` lifecycle blocker 和 `ttl_cancel_enqueue_late` TTL timing blocker，重新验证/review 后再进入
  fresh approval。

## 2026-06-14 lifecycle / TTL timing blocker 本地修复

- 修复范围：针对 `r5-fresh-executable-20260614T133230Z` 暴露的
  `r5_order_lifecycle_blocked:new_trade_after_filled` 与
  `ttl_cancel_enqueue_late:...:148`。未引入 raw REST、manual signing 或自建 SDK 旁路。
- TTL 根因：官方 Rust SDK 的 `SignedOrder` 只暴露 payload/signature/owner/post 参数，`post_order`
  返回前没有可取消的 platform order id。旧 runtime 用 `sdk_submit_start_ms` / `t_exchange_arrival_ms`
  作为 TTL cancel due 锚点，导致 post ack 晚于 `submit_start+250ms` 时，cancel 一注册就产生 late evidence。
- TTL 修复：`r5_single_market_runtime.rs` 保留 `t_exchange_arrival_ms` 作为 submit/arrival evidence，
  新增 `ttl_cancel_anchor_ts_ms`，R5 live accepted post 使用 `ttl_cancel_anchor="post_ack_cancelable_order_id"`，
  `ttl_cancel_request_due_ts_ms = ttl_cancel_anchor_ts_ms + 250`。`r5_artifact_validator.rs` 同步校验
  anchor 类型、anchor timestamp、due/expected ack timing 和 late enqueue/request/ack。accepted LIVE post
  的 TTL timing 现在还会回连 `orders.jsonl` 的 `sdk_actor_request_start_ts_ms` /
  `sdk_actor_done_ms`：`t_exchange_arrival_ms` 必须等于 actor request start，`ttl_cancel_anchor_ts_ms`
  必须等于 actor done，且 `orders.jsonl` row `timestamp_ms` 必须等于 actor done。
- lifecycle 根因：`sdk_order_actor.rs` 之前把 matched/filled/cannot-cancel rejection 本地化为无
  trade_id / fill_size 的 `Terminal(Filled)` arbitration input；随后真实 user-channel trade 到达时会被
  order lifecycle 识别成 `new_trade_after_filled`。
- lifecycle 修复：matched/filled cancel rejection 不再生成 terminal fill lifecycle evidence，不清 active order；
  若没有 accepted cancel、user-channel trade/fill 或其它官方 terminal evidence 闭合该订单，runtime fail closed。
- 新增/更新 regression：
  - `r5_cancel_rejected_as_matched_does_not_emit_terminal_fill_without_trade_evidence`
  - `r5_cancel_rejected_as_filled_does_not_emit_terminal_fill_without_trade_evidence`
  - `r5_runtime_ttl_cancel_uses_post_ack_anchor_when_post_ack_crosses_submit_start_due`
  - `r5_cancel_rejected_as_matched_without_trade_evidence_fails_closed_without_clob_query`
  - `r5_runtime_ttl_cancels_active_order_before_next_policy_call` 追加 artifact mutation：accepted LIVE post
    若把 registration/due/ack 全部伪造成旧 `ttl_cancel_anchor="t_exchange_arrival"`，即使内部 timing
    自洽，也必须被 `ttl_live_post_bad_anchor:*` 拒绝。
  - 同一测试追加 shifted post-ack anchor mutation：若 decisions 内 registration/due/ack 全部使用一致但
    与 `orders.jsonl` `sdk_actor_done_ms` 不一致的 `ttl_cancel_anchor_ts_ms`，必须被
    `ttl_live_post_anchor_ts_mismatch:*` 拒绝。
- 已通过 verification：
  - `cargo check -p sdk-live-trade --quiet`
  - `cargo test -p sdk-live-trade --test sdk_order_actor r5_cancel_rejected_as_ --quiet`
  - `cargo test -p sdk-live-trade --test sdk_order_actor --quiet` (`20/20`)
  - `cargo test -p sdk-live-trade --test r5_artifact_validator --quiet` (`25/25`)
  - `cargo test -p sdk-live-trade --test r5_single_market_runtime ttl --quiet` (`18/18`)
  - `cargo test -p sdk-live-trade --test r5_single_market_runtime --quiet` (`106/106`)
  - `cargo fmt --all -- --check`
  - `git diff --check`
  - 本轮 production 变更文件 blocking scan：production hot path `0` 命中，仅 `#[cfg(test)]` fixture
    `read_to_string` 命中。
  - 标准 R5 production blocking-pattern scan：production code `0` 命中；仅
    `live_validation_r5_execution.rs` 的 `#[cfg(test)]` checkpoint fixture `std::fs::write` 两处命中。
  - `cargo test -p sdk-live-trade --quiet` 初次运行因历史 `/tmp/sdk-live-trade-*` 临时目录积累触发
    `Disk quota exceeded`；清理 `/tmp/sdk-live-trade-*` 后重新执行通过。该失败是本机临时目录配额问题，
    不是本轮 lifecycle/TTL runtime 逻辑失败。
- GPT-5.5/xhigh parallel review gate 已关闭：Pasteur TTL validator review、Einstein lifecycle review 和
  Turing docs/gate review 均 PASS，无 actionable blocker。Pasteur 提到的 `orders.jsonl timestamp_ms`
  direct mutation test 仅为可选 hardening；当前 validator 已直接拒绝 `timestamp_ms != sdk_actor_done_ms`。
- superseded gate：该 lifecycle/TTL timing 修复段的 commit/push、fresh binary/build/deploy rehearsal、
  fresh approval 和 follow-up run 已由后续 `r5-fresh-executable-20260614T150337Z` / `r5-fresh-executable-20260614T160847Z`
  关闭并 supersede；最终 cursor 见下方 “17:13 fresh run TTL ack / lifecycle cadence blocker 本地修复”。

## 历史状态（已被 15:03 fresh run 取代）

- completed checkpoint：`90838a0 sdk-live-trade: close r5 model input authority` 已提交并 push；Task 13
  本地实现、targeted/full verification 和 GPT-5.5 xhigh review gate 已关闭；`01d314a` cadence/TTL
  evidence blocker fix 已提交并 push。
- open Phase：Phase 4。
- historical open Task：post-cadence follow-up live run `new_trade_after_filled` / `ttl_cancel_enqueue_late` blocker 本地
  修复已通过 full verification 和 GPT-5.5/xhigh parallel review gate。
- superseded next gate：该段对应 13:32 前的旧 cursor；15:03 fresh run 已使用新的 approval 并暴露
  same-order overlap evidence blocker。当前 cursor 见下方 “overlapping model cancel / TTL evidence
  blocker 本地修复”。

## 2026-06-14 lifecycle / TTL timing blocker follow-up fresh live-funds run

- 本地修复提交并推送：`f1f59782bc471611238e7ba8f757c710902daf25`
  (`sdk-live-trade: fix r5 lifecycle ttl timing blockers`) 已 push 到 `origin/sdk-live-trade`。
- fresh release build：commit `f1f59782bc471611238e7ba8f757c710902daf25`，dirty state `clean`，
  git diff sha256 `eb2eb6eef4a523ac5fcd058c487d408737ef3770a4973fdf7ac1caa8e8fa2c75`，
  binary sha256 `19fe29f93b96f3cea4c7a637b80f3d5587cf73340ae784955b9a38dc114af16a`。
- fresh binary/deploy rehearsal：`r5-lifecycle-ttl-fresh-binary-rehearsal-20260614T145746Z`，
  remote path
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/no-submit-rehearsal/phase4-lifecycle-ttl-fresh-binary-rehearsal/r5-lifecycle-ttl-fresh-binary-rehearsal-20260614T145746Z`，
  local archive
  `poly-arb-ai/rust/sdk-live-trade/artifacts/remote-r5-runs/r5-lifecycle-ttl-fresh-binary-rehearsal-20260614T145746Z`；
  `feature_rows=240`、`ready_ticks=83`、`inference_success_count=83`、
  `sdk_post_attempted=false`、`sdk_cancel_attempted=false`，report sha256
  `fd6df27d320069879659366a03a5bca31b23b0f064914c90efb2f5d48404254f`，
  artifact bundle manifest sha256 `1af7207055b67fa22e42003517103a36c6e4ef7b5b98c982f6d61ebaa46a5ba5`。
- target market probe：`btc-updown-5m-1781449800`，window `1781449800..1781450100`，
  condition id `0x0dafe8851246f3661710f371e2b28394a9f11997b428b4837cdb795939876fc2`，
  target startup balance `84527087` raw 6-decimal USDC，open orders `0`，positions `0`，
  target report sha256 `64026cdede9917cf56d67a2fd37872f08a7d0e5c8a77cd021942b17a0ff323d8`。
- fresh approval：`r5-fresh-executable-20260614T150337Z`，local path
  `poly-arb-ai/rust/sdk-live-trade/artifacts/live-validation/approvals/r5-fresh-executable-20260614T150337Z.json`，
  remote path
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/approvals/r5-fresh-executable-20260614T150337Z.json`，
  approval sha256 `6cf8345d611f633568ec53c4aa45e30281d45109b0909ba8a7361262b7f72e58`。
- live-funds run：remote output dir
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/R5-execution/r5-fresh-executable-20260614T150337Z-run`，
  local archive
  `poly-arb-ai/rust/sdk-live-trade/artifacts/remote-r5-runs/r5-fresh-executable-20260614T150337Z-run`，
  artifact bundle manifest sha256 `d93f4a63bc32d9c00554a8ace8039abdb7d90feead16aaf96921cdda6e165818`。
- result：`runtime_status=submit_cancel_runtime_pending`、`fail_closed=true`、`sdk_post_attempted=true`、
  `sdk_cancel_attempted=true`、`sdk_post_attempt_count=8`、`sdk_cancel_attempt_count=11`、
  `fill_count=0`、`cancel_ack_count=7`、`tick_coverage=130`。
- fail-closed reasons：
  `ttl_cancel_unresolved_after_sdk_outcome:0x67fa34084f934d195f66ac6c0592bdada9021b99bea949e9aed3315df80ad2aa`
  and
  `r5_runtime_audit_bundle_failed:ttl_cancel_ack_missing_for_live_order:0x333ea979fc6fa1c24ed806c53e28ddc2cc2bdf30527cd0845e98e4934046c767`。
- reconciliation verdict：`open_order_safe=true`、`position_value_safe=true`、
  `current_exposure_safe=true`、`trade_history_complete=true`、`audit_complete=true`、
  `allows_new_orders=true`。
- report sha256：`r5_execution_report.json`
  `f2899e652ec7a9e459dc6f999f3749c1eab7f7ded9a258e4cac60edd71ed305b`；
  `run_manifest.json` `b9f786ff7ce3ab665336a90b04232595b4904d99682a9ec910908f90af55fa27`；
  `reconciliation_report.json` `598396097c07c7ab100890b80ca02fa2b51ba4201ca47245865e091005e5acf2`。
- single-use marker：remote
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/approval-use-markers/r5-fresh-executable-20260614T150337Z.used.json`，
  marker sha256 `9c3a7ffa0d7293a67be38cb27b361d3ea924863d8c8dc6291e4379af5151fba8`；
  approval 已使用且不可复用。
- 定位：旧 `new_trade_after_filled` 和 `ttl_cancel_enqueue_late:...:148` 未复现；本 run 暴露的是不同的
  same-order overlap。`model_no_quote` cancel 在 `1781449832007` 发出，TTL cancel 在
  `1781449832075` 发出；DOWN 订单 `0x333e...c767` 的 model cancel 在
  `1781449832084` 被 SDK accepted，随后 TTL cancel 返回 `the order is already canceled`，旧 runtime 已删除
  TTL state，未写 TTL ack；UP 订单 `0x67fa...d2aa` 的 model cancel 返回
  `matched orders can't be canceled`，TTL cancel 返回 `order can't be found - already canceled or matched`，
  缺少 trade/fill evidence，仍是必须 fail-closed 的 lifecycle authority ambiguity。
- 硬件判断：本 run 的 TTL enqueue/request lateness 为 `1ms`，不是之前的 `148ms` late evidence；2 vCPU/2G
  RAM 服务器不适合作为 Rust 构建机这一约束仍成立，但本 blocker 是 SDK cancel outcome / audit evidence
  arbitration 问题，不是可由增加 CPU 直接修复的性能问题。

## 2026-06-14 overlapping model cancel / TTL evidence blocker 本地修复

- 修复范围：针对 `r5-fresh-executable-20260614T150337Z` 暴露的 same-order
  `model_no_quote` cancel / TTL cancel overlap evidence blocker；未引入 raw REST、manual signing、
  CLOB query fallback 或自建 SDK 旁路。
- runtime 修复：`r5_single_market_runtime.rs` 在 model submit/cancel SDK completion apply 后、TTL state
  cleanup 前，若同一订单已有 TTL cancel request sent，且同一 model cancel 的 SDK terminal evidence 满足
  `model_cancel_request_start <= ttl_request_sent` 与 `model_cancel_done <= ttl_expected_ack`，写入
  `ttl_cancel_ack`，`ttl_cancel_policy_status="overlapped_terminal"`，并带上 terminal source /
  transition / status evidence。matched/filled/cannot-cancel rejection 仍不伪造成 terminal，也不清 active order。
- artifact validator 修复：`r5_artifact_validator.rs` 不再把 `cancels.jsonl` row `timestamp_ms`
  当成 TTL cancel attempt，而改用 payload `sdk_actor_request_start_ts_ms`；同单 terminal evidence 只在
  prior completion 或严格 overlap window 内可满足 TTL invariant；不同订单和同单但 request start 晚于 TTL
  attempt 的事后 terminal 仍拒绝。
- 首轮 GPT-5.5/xhigh review blocker 处理：
  - runtime overlap helper 进一步收窄为同一订单、`!blocked`、`authoritative_update=true`、
    `model_cancel_request_start <= ttl_request_sent <= model_cancel_done <= ttl_expected_ack`；
    非权威/audit-only、blocked、done 早于 TTL request、done 晚于 expected ack、request start 晚于 TTL
    request 均不得写 `overlapped_terminal` ack。
  - artifact validator 进一步拒绝 `request_start > done` 的 malformed terminal evidence，避免伪造
    same-order prior terminal。
- 新增 / 更新回归：
  - `overlapping_model_cancel_terminal_records_ttl_ack`
  - `overlapping_model_cancel_terminal_ack_requires_authoritative_overlap`
  - `overlapping_model_cancel_terminal_ack_deduplicates_existing_ack`
  - `r5_artifact_validator_accepts_ttl_cancel_when_overlapping_model_cancel_closed_order`
  - `r5_artifact_validator_rejects_ttl_cancel_terminal_request_start_after_done`
  - `r5_artifact_validator_rejects_ttl_cancel_same_order_terminal_after_ttl_attempt` 更新为 request-start
    晚于 TTL attempt 的负例。
- 当前 verification 已通过：
  - `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`
  - `git diff --check`
  - `cargo check --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
  - R5 production blocking-pattern scan：production hot path `0` 命中，仅
    `live_validation_r5_execution.rs` 的 `#[cfg(test)]` checkpoint fixture `std::fs::write` 两处命中。
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade overlapping_model_cancel_terminal_records_ttl_ack --quiet`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime ttl --quiet` (`20/20`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_artifact_validator --quiet` (`25/25`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test sdk_order_actor --quiet` (`20/20`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime --quiet` (`108/108`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
- GPT-5.5/xhigh re-review gate 已关闭：Copernicus runtime review、Mencius artifact validator review 和
  Lagrange docs/gate review 均 PASS，无剩余 actionable blocker。
- superseded gate：该 overlap 修复段的 commit/push、fresh binary/build/deploy rehearsal、fresh approval
  和 follow-up run 已由 `r5-fresh-executable-20260614T160847Z` 关闭并 supersede，并已被 17:13 fresh
  run 再次 supersede；最终 cursor 见下方 “17:13 fresh run TTL ack / lifecycle cadence blocker 本地修复”。

## 2026-06-14 sub-TTL model cancel / TTL due cadence blocker 本地修复

- 触发 run：same-order overlap 修复 commit `b590c9a043d359a88743683c0ee8a035c8bbf089` 后，用户批准的
  fresh executable approval `r5-fresh-executable-20260614T160847Z` 已执行并拉回 artifact。
  run 进入真实 SDK submit/cancel 路径，但 fail closed：
  `runtime_status=submit_cancel_runtime_pending`、`sdk_post_attempted=true`、`sdk_cancel_attempted=true`、
  `sdk_post_attempt_count=76`、`sdk_cancel_attempt_count=79`、`fill_count=0`、`cancel_ack_count=71`、
  `tick_coverage=200`。
- fail-closed reasons：
  `ttl_cancel_unresolved_after_sdk_outcome:0x4944a171e6715d9b4d7b0a0631d8533cc0fb426b3956461769ee2c0e9674e592`
  和
  `r5_runtime_audit_bundle_failed:ttl_cancel_not_terminal_or_accepted_for_live_order:0x4944a171e6715d9b4d7b0a0631d8533cc0fb426b3956461769ee2c0e9674e592`。
  local archive：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/remote-r5-runs/r5-fresh-executable-20260614T160847Z-run`；
  approval sha256 `d930a8ca02d19e66899617945eb4d1094309d53227c5e7bc36495fa06e8bd323`，
  binary sha256 `04af298e4cb0cbc4bcb7febeb03b33af3820d7b8fdc9a744d10b4204c99613c6`，
  artifact bundle manifest sha256 `058dc6072808bbeba5dc357a012a5d639c2384531d9813f197fecdee0df5c7f6`，
  single-use marker sha256 `9a70d35fc33ceca95fc4c9db24d0fd84c453e4eaf581232d502fa1811097e0d1`。
  该 approval 已使用且不可复用。
- 根因：previous overlap 修复处理的是 TTL request 已发出后的同单 terminal evidence 归属；本 run 暴露的是
  更早一层 cadence ordering bug。accepted LIVE post 后，TTL due 为 `1781453449572`，但下一条模型
  tick `1781453449500` 发生在 TTL due 前，runtime 仍允许策略根据模型输出渲染
  `model_no_quote` cancel；该 cancel request start `1781453449507`，比 TTL request start
  `1781453449573` 更早。两笔 cancel 随后返回 matched/already-canceled ambiguity，缺少 authoritative
  terminal/fill evidence，validator 正确 fail closed。
- 硬件判断：该 run 的 actor queue lag 为 `0ms`，TTL request lateness 为 `1ms`，不是上一轮
  `148ms` late evidence；2 vCPU/2G RAM live 服务器仍不适合作为 Rust 构建机，但本 blocker 不是
  CPU/RAM 直接导致的性能问题。
- runtime 修复：`r5_single_market_runtime.rs` 在已注册 TTL order 且 `decision_tick_ms <
  ttl_cancel_request_due_ts_ms`、`cancel_requested=false` 时，输出
  `model_status="ttl_cancel_waiting_for_due"`、`no_order_reason="ttl_cancel_waiting_for_due"`、
  `strategy_intent="ttl_cancel_waiting_for_due"` 的 no-order tick，并跳过 inference、policy render 和
  model submit/cancel SDK command。到达 due 后，仍由 TTL scan 发送 `reason="ttl_expired"` cancel。
- 新增 / 更新回归：
  - `r5_runtime_ttl_waiting_blocks_sub_ttl_model_cancel`
  - `two_slot_sub_ttl_strategy_plan`
- 当前 verification 已通过：
  - RED：该 regression 在 runtime 修复前失败，tick 1 仍进入 `approved_sdk_outcome`。
  - GREEN：该 regression 在 runtime 修复后通过。
  - Zeno root-cause review 发现旧 `production_strategy_cancel_orders` 正向 linkage runtime test 被
    sub-TTL regression 替换；经复核，旧 runtime 场景要求模型在 accepted LIVE TTL order 到期前抢先
    `model_no_quote` cancel，已被本轮 TTL contract 废弃。处理方式为保留 runtime sub-TTL no-cancel
    regression，并在 `production_strategy_intent.rs` 的 reprice/no-quote cancel 正向测试补充
    `production_strategy_cancel_orders` / `cancel_pending` / `cancel_order_count=1` audit 断言。
  - Zeno root-cause review 同时发现 16:08 run `runtime_status` 文档 token 大小写与 artifact 不一致；
    plan / changelog / command doc 已统一为 artifact 原文 `submit_cancel_runtime_pending`。
  - `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`
  - `git diff --check`
  - R5 production blocking-pattern scan：production hot path `0` 命中，仅
    `live_validation_r5_execution.rs` 的 `#[cfg(test)]` checkpoint fixture `std::fs::write` 两处命中。
  - `cargo check --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_runtime_ttl_waiting_blocks_sub_ttl_model_cancel -- --nocapture`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test production_strategy_intent --quiet`
    (`13/13`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime ttl --quiet`
    (`21/21`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_artifact_validator --quiet`
    (`25/25`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime --quiet`
    (`108/108`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
- GPT-5.5/xhigh parallel review gate 已关闭：Helmholtz runtime/cadence review、Zeno artifact[PRIVATE_ROOT]-cause
  review 和 Avicenna docs/gate review 均 PASS。
- superseded gate：该 sub-TTL 修复段的 commit/push、fresh binary/build/deploy rehearsal、fresh approval
  和 follow-up run 已由 `r5-fresh-executable-20260614T171300Z` 关闭并 supersede；当前 gate 见下方
  “17:13 fresh run TTL ack / lifecycle cadence blocker 本地修复”。

## 2026-06-14 17:13 fresh run TTL ack / lifecycle cadence blocker 本地修复

- 触发 run：sub-TTL 修复 commit `2826d6731e998f5a27ddd1d3696411654566ab70` 后，用户批准继续
  fresh approval / live-funds run。fresh binary sha256 为
  `fffdd4057addaf7b5279e7dcd0d30a919699aed02af07501505a768264384c25`；fresh executable approval
  `r5-fresh-executable-20260614T171300Z` 绑定 `btc-updown-5m-1781457300`，approval sha256
  `d7024cc995e64c62d0a650b06c07b7b274a8184aabf4f1b8fba2512d8333e72d`。
- run 进入真实 SDK submit/cancel 路径，但 fail closed：
  `runtime_status=submit_cancel_runtime_pending`、`sdk_post_attempted=true`、`sdk_cancel_attempted=true`、
  `sdk_post_attempt_count=2`、`sdk_cancel_attempt_count=2`、`cancel_ack_count=2`、`fill_count=0`、
  `tick_coverage=129`。single-use marker sha256 为
  `209ee8e62c9a3be7629deca188fc1c2778838831e38b1f04d9d306d9c588b4ad`；approval 已使用且不可复用。
- fail-closed reasons：
  `r5_single_market_runtime_live_feature_refresh_failed:r5_live_feature_producer:CadenceGap { expected_ts_ms: 1781457331750, decision_ts_ms: 1781457332000 }`
  和
  `r5_runtime_audit_bundle_failed:ttl_cancel_ack_missing_for_live_order:0xf515d8708788c28c345f800544846b8dd02b4957c020675633dc7e2b8d69de7a`。
  local archive：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/remote-r5-runs/r5-fresh-executable-20260614T171300Z-run`；
  run report sha256 `886b21c1db8f08fe82de2bcc11bd1eb7deed576c2fb6b1f5fce2e44359721cf7`，
  run manifest sha256 `b763314d44a55c360e5b7b7acd2d433ae829aae451abc5fc45aa8416d60dfbc9`，
  artifact bundle manifest sha256 `eece7ce5dc469c7693f0c4949644fe9fbeea5c22bee50f1b64aff8e77ea0371a`。
- 账户/订单安全结果：final reconciliation verdict 为 `open_order_safe=true`、
  `position_value_safe=true`、`current_exposure_safe=true`、`trade_history_complete=true`、
  `audit_complete=true`、`allows_new_orders=true`；final local ledger 为 `cash=80.198287`、
  `open_order_notional=0`、`shares_up=0`、`shares_down=0`。
- 根因判断：
  - TTL ack：UP order 的 user-channel `CancelComplete` 先于 SDK cancel response 到达并成为
    authoritative ledger update；后续 SDK cancel response 变成 audit-only。旧 runtime 只在 SDK cancel
    response 分支写 `ttl_cancel_ack`，没有在 source lifecycle branch 为 pending TTL cancel 写 ack，
    导致 artifact validator 正确报 `ttl_cancel_ack_missing_for_live_order`。
  - CadenceGap：source lifecycle refresh 分支遇到单个 250ms lattice gap 时把
    `LiveFeatureProducer` 的 `CadenceGap` 升级成 global fail-closed。修复后该分支只把当前 tick 标记为
    `FeatureCadenceGap` no-order，不补虚假 feature row，不允许模型在该 tick 下单。
- 硬件判断：本 run 的 TTL enqueue late 为 `1ms`、actor queue lag 为 `0ms`；远端运行后
  `nproc=2`、memory available 约 `1474MiB`、`load average=0.00`。AWS live 服务器仍禁止 Rust
  编译，但本 blocker 不是 2 vCPU/2G RAM 饱和直接造成。
- runtime 修复：
  - `append_ttl_cancel_ack_events_from_lifecycle()`：任一权威 lifecycle `CancelComplete`（包括
    user-channel 先到）都可为已 request 的 TTL cancel 写 `ttl_cancel_ack`，并用
    `local_observed_ms/visible_at_ms` 计算 ack timing；blocked、audit-only、非 pending TTL 均跳过。
  - `feature_readiness_after_lifecycle()` 的 `r5_live_feature_producer:CadenceGap` 不再 global
    fail-closed；当前 tick 输出 `FeatureCadenceGap` no-order。
- artifact validator 修复：
  - GPT-5.5/xhigh artifact review 指出 validator 不能只依赖 runtime producer 正常行为；旧口径会把
    `cancels.jsonl` 的 `arbitration_inputs: CancelComplete` 单独当作 TTL cancel terminal evidence，
    即使 cancel observation 是 `SdkRejected` 且 `canceled_order_ids=[]`。
  - 已收紧为只有 `SdkAccepted + canceled_order_ids` 或独立 user-channel terminal evidence 才能满足
    TTL cancel terminal/accepted invariant；`arbitration_inputs` 不再单独证明 terminal。
- 新增回归：
  - `ttl_cancel_ack_can_be_written_from_user_channel_cancel_complete`
  - `r5_runtime_lifecycle_feature_refresh_cadence_gap_no_orders_current_tick`
  - `r5_execution_validator_rejects_ttl_cancel_terminal_claim_without_accepted_cancel`
- 当前已通过的新增 targeted verification：
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --lib ttl_cancel_ack_can_be_written_from_user_channel_cancel_complete -- --nocapture`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_runtime_lifecycle_feature_refresh_cadence_gap_no_orders_current_tick -- --nocapture`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_artifact_validator r5_execution_validator_rejects_ttl_cancel_terminal_claim_without_accepted_cancel -- --nocapture`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_artifact_validator --quiet`
    (`26/26`)
- full local verification 已通过：
  - `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`
  - `git diff --check`
  - production blocking scan：production `0` 命中，仅
    `live_validation_r5_execution.rs` 的 `#[cfg(test)]` checkpoint fixture `std::fs::write` 两处命中。
  - `cargo check --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime --quiet`
    (`109/109`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
- GPT-5.5/xhigh re-review 已关闭：Dewey runtime PASS、Heisenberg artifact-validator PASS、
  Ptolemy docs/gate PASS。
- superseded gate：该 17:13 blocker 修复已完成 commit/push、fresh binary/deploy rehearsal、
  fresh approval 和 18:05 follow-up run；当前 gate 见下方“18:05 fresh run matched/not-found cancel
  rejection blocker”。

## 2026-06-14 18:05 fresh run matched/not-found cancel rejection blocker

- 17:13 blocker 修复已完成 commit/push：`8f952afa934a5727c21fa5afb40e3b8ad5748186`。
  fresh binary 在本地构建，sha256 为
  `979cb8a5506843c04f15b4b816be1335b642ae94cf1944579421212851f91b51`；fresh no-submit rehearsal
  `r5-lifecycle-ack-fresh-binary-rehearsal-20260614T180057Z` 已通过，remote artifact path 为
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/no-submit-rehearsal/phase4-lifecycle-ack-fresh-binary-rehearsal/r5-lifecycle-ack-fresh-binary-rehearsal-20260614T180057Z`。
- 生成并执行 fresh executable approval `r5-fresh-executable-20260614T180542Z`，approval sha256
  `6650c588b81a33168a85ab02b2437bd2ba719af5acd3bc1dfed6aeb7218546ff`，market slug
  `btc-updown-5m-1781460600`，condition id
  `0xcb98fdb3814d764b9184377e1bc1f7d814f511646865ecd8d37ab71ebb2d0bd1`。approval 已使用且不可复用。
- run artifact：
  remote `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/R5-execution/r5-fresh-executable-20260614T180542Z-run`；
  local `poly-arb-ai/rust/sdk-live-trade/artifacts/remote-r5-runs/r5-fresh-executable-20260614T180542Z-run`；
  `r5_execution_report.json` sha256 `d5c86c5c3b256c40d9967ea47dd7d1c026b3bdc237ed84378acf0f1bbfe5e4ac`；
  `run_manifest.json` sha256 `5ff28947fbc35d7d0141707fae0b6f619bb351e13d826571458cedc4836f5fc7`。
- 结果：`runtime_status=submit_cancel_runtime_pending`、`fail_closed=true`、`sdk_post_attempted=true`、
  `sdk_cancel_attempted=true`、`sdk_post_attempt_count=2`、`sdk_cancel_attempt_count=3`、
  `submit_count=2`、`cancel_count=3`、`cancel_ack_count=1`、`fill_count=0`、`tick_coverage=123`。
  fail-closed reasons：
  `ttl_cancel_unresolved_after_sdk_outcome:0xe30530b04878fc734bc969c7b894f42ae780035db001a9d18db045069b9c1190`
  和
  `r5_runtime_audit_bundle_failed:ttl_cancel_not_terminal_or_accepted_for_live_order:0xe30530b04878fc734bc969c7b894f42ae780035db001a9d18db045069b9c1190`。
- 订单证据：UP BUY `0xe30530b04878fc734bc969c7b894f42ae780035db001a9d18db045069b9c1190`
  与 DOWN BUY `0xcc119cbe65e89aeada3d7cfa645b72d60937dab401dad78830961f32129e9e29` 均 accepted
  LIVE；DOWN TTL cancel `SdkAccepted` 且 `canceled_order_ids` 包含该订单，已闭合；UP TTL cancel
  `SdkRejected`，`not_canceled` 先返回 `matched orders can't be canceled`，runtime-end scoped cleanup
  又返回 `order can't be found - already canceled or matched`，但 `user_channel.jsonl`、`fills.jsonl`、
  `trades.jsonl` 均为 0 行，因此不能把该字符串直接当作 fill/cancel terminal evidence。
- 资金/账户证据：final official SDK account snapshot queried OK，显示 balance `80.198287`、
  `data_position_count=0`、`clob_trade_count=0`，但 `open_order_count=1`，UP order
  `0xe30530b04878fc734bc969c7b894f42ae780035db001a9d18db045069b9c1190` 仍在
  `sdk_open_orders` 中，`remaining_size=5`、`size_matched=0`、local ledger 仍保留
  `reserved_notional=1.5` / `open_order_notional=1.5`。因此当前 blocker 不是单纯 audit false
  positive；必须先确认/撤销遗留 open order 或补充官方 terminal evidence。
- 硬件判断：TTL due enqueue late 为 `2ms`、SDK actor queue lag 为 `0ms`；本轮 blocker 不是 2 vCPU /
  2G RAM 饱和造成。硬件约束仍成立：AWS live 服务器只运行 binary，不得在其上执行 Rust build/check/test。
- 当前建议：先处理遗留 open order 的 official-SDK-backed emergency cancel / snapshot confirmation；然后本地修复
  matched/not-found cancel rejection evidence path，要求不能把 `not_canceled` 字符串伪造成成交，必须由
  user-channel、accepted cancel、order detail 或 trade history 等官方证据闭合 ledger；修复后再走 targeted/full
  verification、GPT-5.5/xhigh review、commit/push、fresh binary/deploy rehearsal 和新的 fresh approval。

## 2026-06-14 18:05 matched/not-found evidence blocker 本地修复

- 修复范围：
  - `r5_single_market_runtime.rs` 现在在 post-market final audit 阶段调用 tick source
    `final_reconciliation_snapshot()`，优先消费 official final snapshot；source 返回 unsafe verdict 时写
    `final_reconciliation_unsafe:*` 并 fail closed。若 source 返回 `None`，继续使用 synthetic local fallback；
    若 post-market hard-stop 没有剩余预算，则不调用 source hook，避免硬停机后继续做官方查询。
  - `r5_artifact_validator.rs` 现在只允许结构化 `order_state_arbitration.jsonl`
    `event="clob_order_evidence"` / `source="official_sdk_clob_order_query"` 且
    `terminal_status` 为 `Canceled`、`Filled`、`Confirmed` 或 `Failed` 的 CLOB order detail evidence
    闭合 ambiguous TTL cancel；`Live` 等非 terminal 状态和 `not_canceled` 字符串仍拒绝。
  - 既有 `SdkAccepted + canceled_order_ids` 与 user-channel terminal evidence 仍可闭合 TTL cancel；
    `arbitration_inputs: CancelComplete` 配合 `SdkRejected` 仍不得单独证明 terminal。
- 新增/更新回归：
  - `r5_execution_validator_accepts_ambiguous_ttl_cancel_with_clob_order_terminal_evidence`
  - `r5_execution_validator_rejects_ambiguous_ttl_cancel_with_non_terminal_clob_order_evidence`
  - `r5_execution_validator_rejects_ambiguous_ttl_cancel_with_non_official_clob_order_evidence`
  - `r5_runtime_live_tick_source_missing_final_reconciliation_falls_back_to_local_audit`
  - `r5_runtime_post_market_hard_stop_blocks_final_reconciliation_source`
  - `r5_runtime_elapsed_post_market_deadline_blocks_final_reconciliation_source`
  - `r5_runtime_final_reconciliation_unsafe_verdict_fail_closes`
- 当前已通过 verification：
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_artifact_validator ambiguous_ttl_cancel -- --nocapture`
    (`3/3`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_artifact_validator r5_execution_validator_rejects_ttl_cancel_terminal_claim_without_accepted_cancel -- --nocapture`
    (`1/1`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime final_reconciliation -- --nocapture`
    (`4/4`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime r5_cancel_rejected_as_matched_without_trade_evidence_fails_closed_without_clob_query -- --exact --nocapture`
    (`1/1`)
  - `cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check`
  - `git diff --check`
  - `cargo check --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_artifact_validator --quiet`
    (`29/29`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test r5_single_market_runtime --quiet`
    (`110/110`)
  - `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet`
- Blocking/write scan：`rg -n "std::fs::write|fs::write" poly-arb-ai/rust/sdk-live-trade/src --glob '*.rs'`
  仅命中 src 内 `#[test]` / `#[cfg(unix)]` fixture 写入，未由本轮改动新增生产 hot-path 阻塞写文件。
- 外部证据口径：官方 Polymarket cancel/create/user-channel 文档和社区同类问题均支持本轮判断：
  cancel rejection 文本是 SDK/API outcome，不是 ledger terminal proof；必须由 accepted cancel、user-channel、
  order detail 或 trade history 等官方结构化证据闭合。
- gate 状态：当前尚未生成新的 fresh executable approval，未执行新的 live-funds run。旧 approval
  `r5-fresh-executable-20260614T180542Z` 已使用且不可复用；下一轮 live-funds run 前仍必须先处理遗留
  UP open order `0xe30530b04878fc734bc969c7b894f42ae780035db001a9d18db045069b9c1190` 的 official
  recovery/confirmation gate，并重新完成 fresh binary/build/deploy rehearsal 与 fresh approval。
