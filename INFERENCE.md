# Minimal inference / 最小推理

These examples consume archived weights. They do not reconstruct training, market feature generation, exchange execution or risk management. / 本示例读取历史权重，不重建训练、市场特征生成、交易执行或风控。

Use Python with NumPy, PyTorch, ONNX and ONNX Runtime. Tested versions are recorded in [verification/models.json](verification/models.json); dependencies are listed in [requirements.txt](requirements.txt). / 验证版本见报告，依赖见清单。

| Family / 家族 | Raw input / 原始输入 | Output / 输出 |
| --- | --- | --- |
| M3 run3 | `obs: float32[1,240,65]` | signal logits + EV |
| M3 B1/B2 checkpoint | `obs: float32[1,100,65]` | signal logits + EV |
| M3 B1/B2 collection | `obs: float32[1,100,76]` | 7 named outputs; added-head training scores N/A / 7项输出，新增头无训练成绩 |
| M5 BC | `obs: float32[1,240,76]` | signal, policy, size, order type, price level, risk |
| M5 IQL | `obs: float32[1,100,76]` | same output names / 同上 |
| Alpha V2 | `obs: float32[1,T,160]`, T=120 or control 180 | `signal_logits[1,2]`, `signal_ev[1,2]` |
| MakerPolicy V2 | `features[1,T,160]`, `alpha[1,4]`, `account_state[1,5]` | `quote_logits[1,4]`, `offset_logits[1,4,3]`, `size_logits[1,4,1]`, `risk_score[1,1]` |

Feature order: [65 columns](contracts/feature_cols.json), [76 columns](contracts/m5_feature_cols.json), [160-feature specification](models/mpv2_r1_a3_seq120_seed2/feature_spec.json). Model normalization is embedded in the graph/state; raw inputs must not be normalized a second time. The NPZ files retain the corresponding statistics. / 特征必须按合同顺序排列；归一化已在模型内部，不要重复执行，NPZ保留对应统计量。

`alpha` order is `[signal_logits[0], signal_logits[1], signal_ev[0], signal_ev[1]]`. `account_state` order is `[cash, nav_before, shares_up, shares_down, active_resting_count]`. **Cash and NAV use USDC, not raw six-decimal token units.** The deployment runner chains Alpha into Policy and returns raw model outputs. It does not decode or submit orders. / 账户现金与NAV使用USDC，不能输入原始代币整数单位。组合入口串联两个模型，只返回原始输出。

The [v1.0.0 release](https://github.com/slowchillchill/failed-market-maker/releases/tag/v1.0.0) contains a historical full snapshot. In a current checkout, extract its model directory while excluding old model cards with `tar -xzf failed-market-maker-v1.0.0.tar.gz --exclude='models/*/README.md' models/`; unpack the entire archive in a separate directory if you need the historical documents. / v1.0.0 是历史完整快照；当前仓库仅提取模型目录并排除旧模型卡，历史整包应在独立目录解压，以免覆盖新版文档。

From the repository root, after obtaining model files:

```bash
python -m inference.run models/m3_run_v7_M3-B1/best_model.pt --family m3 --smoke
python -m inference.run models/m3_run_v7_M3-B1/collection-paper/model.onnx --smoke
python -m inference.run models/m5_iql_0/final_model.pt --family m5_iql --smoke
python -m inference.run models/alpha_primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed2/best_model.pt --family alpha_v2 --smoke
python -m inference.run models/mpv2_r1_a3_seq120_seed2 --smoke
```

For actual prepared input, save an NPZ with `obs` for an M3/M5/Alpha model; use `features`, `alpha`, `account_state` for a standalone Policy, or `features`, `account_state` for the paired deployment. Arrays must have the exact float32 shapes above. Then replace `--smoke` with `--inputs input.npz`. / 实际输入保存为NPZ，键名和float32形状必须与对应接口一致，再用 `--inputs input.npz` 替换 `--smoke`。

```python
import numpy as np
np.savez("input.npz", features=np.zeros((1,120,160), dtype=np.float32),
         account_state=np.array([[100,100,0,0,0]], dtype=np.float32))
```

The example arrays are synthetic. A finite forward only proves execution, not causal feature correctness, learned behavior or profitability. `.pt` loading uses `torch.load(..., weights_only=True)`, strict architecture loading and CPU execution. The six Phase 6.5 policies without paired historical Alpha ONNX can be run with explicitly supplied Alpha arrays; this does not recreate their historical complete ONNX deployment. / 构造数组只能证明前向可执行。PyTorch使用受限加载。缺配对Alpha历史ONNX的六个Policy可接受显式Alpha数组，但不等于恢复完整历史部署。

Keep `agent_model_m5.onnx.data` beside the BC ONNX. Preserve `model_bundle.json`, feature specifications and action/reward configuration with their model. Historical bundle digests refer to pre-redaction originals; no standalone SHA verification was performed during this release. / BC外部权重必须同目录；伴随合同与配置必须保留。历史摘要指向脱敏前原件，本次未执行独立SHA验证。
