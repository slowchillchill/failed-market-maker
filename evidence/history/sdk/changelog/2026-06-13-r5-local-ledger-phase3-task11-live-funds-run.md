# 2026-06-13 R5 local-ledger Phase 3 Task 11 live-funds run

## 背景

当前 active authoritative plan：
`poly-arb-ai/sdk-live-trade-docs/plan/2026-06-13-r5-local-ledger-authoritative-trading-plan-compact.md`。

用户批准生成 fresh executable approval，并明确不需要二次确认，可直接启动 live-funds run。

## 构建与部署

- git commit：`69a297711a1fe773e12e8723a7d92881913ec529`
- git dirty state：`clean`
- git diff sha256：`fec857c82c0eeef2e8c315142e77314361efd29736eaf961a93691e7a66731db`
- release binary sha256：`97a94c1a6430ae744d1f608b5aff4a8801fdb65e934303ae87b707dd5bc1a2c4`
- config sha256：`e5b7ed7e1f1f70b775cc0e10622447957d81974f225df04289aeb63f7f604608`
- model tree manifest sha256：`a18d41cb90b012280ab32031542d8f5ba47fdf18619cd5d4c7eb599152df094a`
- 远端 binary-only deploy 已完成；未在 AWS Ireland runtime server 运行 cargo/build/test/fmt/check。
- rollback：
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/rollbacks/r5-fresh-executable-approval-20260613T100931Z/sdk-live-trade.prev`
- rollback sha256：`2c816adcde1a96e2c2715fbf17697660bddc11fe7e31edaaade341b47211c3f1`

## Approval 与执行结果

第一份 approval：

- approval id：`r5-fresh-executable-20260613T101424Z`
- approval sha256：`bc1ace0d016c430c6a9ab04a8f171476e3a9496656bef4f8e9a15336d424b78d`
- target：`btc-updown-5m-1781345700`
- result：submit 前 fail closed，因为 approval 披露的 `execution_disclosure.exact_condition_id`
  与 runtime evaluated condition id 不一致。
- SDK attempt：`sdk_post_attempted=false`、`sdk_cancel_attempted=false`

第二份 approval：

- approval id：`r5-fresh-executable-20260613T101709Z`
- approval sha256：`7bee341f117820fcd35804a0fd06680364e5367174b3acd3c490e9d57182cbce`
- target：`btc-updown-5m-1781346000`
- condition id：`0x60138f25294ea3eeb2de96f4f274fa18d5b98a718b455574a227f0b02f9d53c7`
- remote run path：
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/R5-execution/r5-fresh-executable-20260613T101709Z-run`
- local archive path：
  `poly-arb-ai/rust/sdk-live-trade/artifacts/remote-r5-runs/r5-fresh-executable-20260613T101709Z-run`

第二份 approval run 的顶层结果：

- `runtime_status=submit_cancel_runtime_armed`
- `fail_closed=false`
- `fail_closed_reasons=[]`
- `sdk_post_attempted=true`
- `sdk_cancel_attempted=true`
- `sdk_post_attempt_count=457`
- `sdk_cancel_attempt_count=240`
- `fill_count=371`
- `tick_coverage=1200`
- post final status：`SdkAccepted=368`、`SdkError=89`
- cancel final status：`SdkAccepted=135`、`SdkRejected=105`
- user-channel evidence rows：`1071`
- order-state arbitration rows：`608`
- `fills.jsonl=0`、`trades.jsonl=0`

Single-use marker：

- path：
  `[PRIVATE_HOME]/sdk-live-trade/artifacts/live-validation/approval-use-markers/r5-fresh-executable-20260613T101709Z.used.json`
- sha256：`d2364101cf21addd10c9fd225ba265a270fd9b006c8c4ef1c1bb25404ecaeea7`
- created_at：`2026-06-13T10:20:30.006519678+00:00`

Artifact sha 证据：

- `r5_execution_report.json` sha256：
  `a2e5bc9814bca2eb0ebda55c05aedb210d15bd4ad7d368440881b9d33d19fdb0`
- `run_manifest.json` sha256：
  `b4d1821f5b7620712753c2b9424e704fa20cf3e430cd4ef8d15c356503035121`
- `reconciliation_report.json` sha256：
  `18691fbc9fff020830075ee8a2f4642ce8ef684c3e8970f90a104a6b32ec8f8a`
- local artifact bundle manifest sha256：
  `722e0dbee0e4670583bbcc97ab86ec22e5454404b64c7e2b432b2fc728bd7b1f`

## 运行后 blocker

Post-run reconciliation 结果：

- `open_order_safe=true`
- `position_value_safe=true`
- `audit_complete=true`
- `current_exposure_safe=false`
- `trade_history_complete=false`
- `trade_history_unavailable=false`
- `allows_new_orders=false`
- repeated reason：`trade_history_filled_size_mismatch`

结论：

- 这次 run 已覆盖真实 SDK submit/cancel lifecycle。
- R5 reset 仍不能声明完成。
- 在解释或修复 `trade_history_filled_size_mismatch` 前，不得进入下一轮 fresh live-funds run。

## 文档同步

- compact plan 已把当前游标推进到 Phase 3 / Task 11 post-run blocker analysis。
- compact plan 已记录两份 approval、真实 SDK submit/cancel 结果、single-use marker 和 post-run blocker。
- `lastest-command.md` 已同步最新 R5 execution run 记录和下一次运行前的阻断条件。
