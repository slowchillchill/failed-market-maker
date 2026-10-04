# 2026-06-14 R5 starting cash raw USDC normalization

## 背景

用户只批准修复 R5 from-files execution 中 `local_starting_cash_usdc` 被 SDK raw 6-decimal
balance 污染后的单位风险；synthetic final account snapshot、post-run platform snapshot、
trade-history reporting/PnL reporting 其它问题本轮不处理。

## 变更

- `live_validation_r5_execution` 在 `local_starting_cash_from_approval` 入口归一 SDK raw
  6-decimal USDC balance：例如 approval disclosure 里的 `100194754` 会在进入
  `AuthoritativeLedger::new` 前转为 `100.194754`。
- 兼容既有已归一 USDC Decimal fixture，例如 `5.00` 仍按 `5.00` 处理。
- 未修改 executable command、部署命令或运行方式；`lastest-command.md` 未修改。

## RED / GREEN

- RED：
  - 新增 `local_starting_cash_from_approval_normalizes_sdk_raw_usdc_units` 后，
    `cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade local_starting_cash_from_approval_normalizes_sdk_raw_usdc_units --quiet`
    失败于 `left: 100194754`、`right: 100.194754`。
- GREEN：
  - `local_starting_cash_from_approval` 对 raw-like integer balance 执行 `/ 1_000_000` 归一后，
    focused regression 通过。

## 验证

执行时间：2026-06-14T04:40:20+09:00。

```bash
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade local_starting_cash_from_approval_normalizes_sdk_raw_usdc_units --quiet
cargo fmt --manifest-path poly-arb-ai/rust/Cargo.toml --all -- --check
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --test live_validation_r5_execution --quiet
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml -p sdk-live-trade --quiet
```

预期与结果：以上命令均退出码为 0。

## 当前状态

- completed checkpoint：R5 starting cash raw USDC normalization scoped fix。
- open Phase：Phase 4。
- open Task：Phase 4 / Task 12 后续由用户安排决定是否进入 fresh executable approval / live-funds run 准备。
- next gate：本轮不生成 fresh approval，不执行 live-funds run。
