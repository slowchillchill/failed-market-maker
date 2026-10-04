# 三模型 72h Paper Runtime 结论 - run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z

## 结论

- 测试已到期结束：`2026-05-22 14:15:00 UTC` / `2026-05-22 23:15:00 UTC+09:00`；manifest duration `72.07h`，`health.jsonl` 记录 `duration_markets_reached=1`。
- 远端服务状态：`inactive/dead`，`ExecMainStatus=0`，run 窗口内 journal warning/error 计数为 `0/0`。
- 完整 artifact 已拉回本地并校验：远端/本地 `14` 个文件 SHA-256 一致，`sha256sum.diff` 为空。
- 主排名按 runtime 风控分段账本的 `adjusted_total_pnl_usdc`：`m3_b2` 第一，`m5_baseline` 接近持平但略负，`m3_b1` 明确失败。

## Profile 对比

| profile | adjusted_total | 累计PnL最高 | 累计PnL最低 | 账本最高NAV(PnL) | 账本最低NAV(PnL) | NAV delta | realized_pnl | closed/current | decisions | orders/fills | fill% | fee | rebate accrued/pending | risk final | TP/SL closes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| m5_baseline | `-0.4547` | `+21.6209` | `-100.9817` | `193.6782 (+93.6782)` | `50.1235 (-49.8765)` | `+6.8511` | `+2.0770` | `-7.3058`/`+6.8511` | `726980` | `13811`/`855` | `6.19%` | `9.0116` | `13.3249`/`3.0992` | `active` | `2`/`2` |
| m3_b1 | `-104.6874` | `+65.4555` | `-104.6874` | `151.8012 (+51.8012)` | `50.0285 (-49.9715)` | `-49.0623` | `-98.7230` | `-104.6874`/`+0.0000` | `499880` | `4192`/`316` | `7.54%` | `43.9725` | `1.1706`/`1.1706` | `await_segment_safe_to_reset/stop_loss` | `3`/`4` |
| m3_b2 | `+43.0920` | `+82.0271` | `-30.7802` | `149.1412 (+49.1412)` | `50.0564 (-49.9436)` | `+22.3428` | `-4.8673` | `+43.0920`/`+0.0000` | `290860` | `11195`/`430` | `3.84%` | `74.6309` | `2.7949`/`1.2409` | `await_segment_safe_to_reset/take_profit` | `10`/`4` |

## 解读

- `m3_b2` 是本轮唯一明显正收益模型：`adjusted_total_pnl_usdc=+43.0920`，14 次风控分段关闭中 10 次 TP、4 次 SL。它不是一路平滑上涨，仍出现多次约 `-50` USDC 的 SL，但 TP 段累计覆盖了损失。
- 表格里的 `累计PnL最高/最低` 使用和 `adjusted_total` 一致的跨 segment 累计口径：已关闭 segment PnL 累计 + 当前 active segment 的 `nav - 100`。
- 表格里的 `账本最高NAV(PnL)` / `账本最低NAV(PnL)` 使用 monitor 的 `NAV/PnL` 口径：逐行读取 `decisions.jsonl`，统计 72h 内模型账户 `nav` 最高/最低，并在括号中给出相对初始 100 USDC 的 PnL。`adjusted_total` 仍是风控分段关闭后的 aggregate 结果，两个口径不能混用。
- `m5_baseline` 的最终 NAV 是 `+6.8511`，但分段风控已累计关闭 `-7.3058`，所以按同一 TP/SL 账本的最终 adjusted 结果是 `-0.4547`。不能只看最后一个 active segment 的 NAV。
- `m3_b1` 最终 `adjusted_total_pnl_usdc=-104.6874`，最后状态是 `await_segment_safe_to_reset/stop_loss`，属于明确淘汰结果。
- `realized_pnl_usdc` 与 `adjusted_total_pnl_usdc` 不同口径：前者来自 trades/settlement 行；后者来自风控关闭时的保守 NAV + segment reset 账本。本轮模型排名应以 adjusted 为主，因为这是这次 TP/SL 三模型实验的实际控制口径。
- manifest 仍记录 `unsettled_at_shutdown=3`，即每个 profile 还有 1 个 shutdown 时未完全 settle 的项目；因此 realized-only 口径不适合作为最终排名，下一轮应把到期后的 settle-only 等待做进收尾流程，目标是 `unsettled_at_shutdown=0`。

## 风险细节

- `m3_b2`: close_count `14`, trigger_counts `{'take_profit': 10, 'stop_loss': 4}`, trigger_pnl `{'take_profit': 243.4697, 'stop_loss': -200.3777}`。
  best `m3_b2:8` `take_profit` `+34.1309` at `2026-05-21 04:29:41 UTC`；worst `m3_b2:9` `stop_loss` `-50.2337` at `2026-05-21 07:45:15 UTC`；last `m3_b2:14` `take_profit` `+21.7560` at `2026-05-22 13:49:21 UTC`。
- `m5_baseline`: close_count `4`, trigger_counts `{'stop_loss': 2, 'take_profit': 2}`, trigger_pnl `{'stop_loss': -100.1738, 'take_profit': 92.868}`。
  best `m5_baseline:4` `take_profit` `+65.6077` at `2026-05-22 11:57:18 UTC`；worst `m5_baseline:1` `stop_loss` `-50.1139` at `2026-05-20 08:37:54 UTC`；last `m5_baseline:4` `take_profit` `+65.6077` at `2026-05-22 11:57:18 UTC`。
- `m3_b1`: close_count `7`, trigger_counts `{'take_profit': 3, 'stop_loss': 4}`, trigger_pnl `{'take_profit': 97.0249, 'stop_loss': -201.7123}`。
  best `m3_b1:1` `take_profit` `+36.1455` at `2026-05-19 17:14:28 UTC`；worst `m3_b1:7` `stop_loss` `-51.2494` at `2026-05-22 07:07:34 UTC`；last `m3_b1:7` `stop_loss` `-51.2494` at `2026-05-22 07:07:34 UTC`。

## 产物

- `remote_run`: `source://paper/paper-trade-history/run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z/remote_run`
- `report_md`: `source://paper/paper-trade-history/run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z/codex_reports/report-20260522T234126Z.md`
- `report_json`: `source://paper/paper-trade-history/run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z/codex_reports/report-20260522T234126Z.json`
- `final_md`: `source://paper/paper-trade-history/run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z/codex_reports/final_conclusion.md`
- `final_json`: `source://paper/paper-trade-history/run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z/codex_reports/final_conclusion.json`
- `sha256_diff`: `source://paper/paper-trade-history/run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z/codex_reports/sha256sum.diff`
- `service_evidence`: `source://paper/paper-trade-history/run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z/codex_reports/service_evidence.txt`
