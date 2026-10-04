# Choose a model / 选择模型

[English overview](README.md#models) · [中文成绩总览](README.zh-CN.md#models) · [Inference / 推理](INFERENCE.md)

24 retained training candidates, grouped by family. Short names link to cards with exact IDs, scores, source reports and downloads. The deployment is listed separately. / 24 个留存训练候选按家族分组；短名称链接到包含完整身份、成绩、来源和下载的模型卡，部署组合单列。

## M3 · supervised signals / 监督信号

| Model / 模型卡 | Parameters / 参数量 | Retained format / 留存格式 | Key result / 主要成绩 |
| --- | --- | --- | --- |
| [M3 run3](models/m3_run3/README.md) | 419556 | PT | Test / 测试 AUC **0.743551** |
| [M3 B1](models/m3_run_v7_M3-B1/README.md) | 419556 | PT + ONNX | Test / 测试 AUC **0.713834** |
| [M3 B2](models/m3_run_v7_M3-B2/README.md) | 419556 | PT + ONNX | Test / 测试 AUC **0.713882** |

## M5 BC · behavior cloning / 行为克隆

| Model / 模型卡 | Parameters / 参数量 | Retained format / 留存格式 | Key result / 主要成绩 |
| --- | --- | --- | --- |
| [M5 BC](models/m5_v7v72_bc/README.md) | 467957 | PT + ONNX | Test accuracy / 测试准确率 **0.682590** |

## M5 IQL · offline execution / 离线执行

| Model / 模型卡 | Parameters / 参数量 | Retained format / 留存格式 | Key result / 主要成绩 |
| --- | --- | --- | --- |
| [IQL-0](models/m5_iql_0/README.md) | 467957 | PT + ONNX | Hold best / 最佳轮 Hold **92.60%**; fixed/native returns in card / 固定与原生收益见卡片 |
| [IQL-1](models/m5_iql_1/README.md) | 467957 | PT + ONNX | Hold best / 最佳轮 Hold **85.25%**; fixed/native returns in card / 固定与原生收益见卡片 |
| [IQL-2](models/m5_iql_2/README.md) | 467957 | PT + ONNX | Hold best / 最佳轮 Hold **94.25%**; fixed/native returns in card / 固定与原生收益见卡片 |

## Alpha V2 · predictive models / 预测模型

| Model / 模型卡 | Parameters / 参数量 | Retained format / 留存格式 | Key result / 主要成绩 |
| --- | --- | --- | --- |
| [R1 A3 · s2](models/alpha_primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed2/README.md) | 227268 | PT + ONNX | val.auc **0.868495**; true_best_side_auc **0.595098** |
| [R1 A3 · s3](models/alpha_primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed3/README.md) | 227268 | PT | val.auc **0.861482**; true_best_side_auc **0.571024** |
| [R2 A1 · s2](models/alpha_primary_R2_A1_seq120_bs2048_ep30_lev0p5_sr0p0_sm0p1_seed2/README.md) | 227268 | PT | val.auc **0.872110**; true_best_side_auc **0.667253** |
| [R3 A6 · s2](models/alpha_primary_R3_A6_seq120_bs2048_ep30_lev0p5_sr0p05_sm0p1_seed2/README.md) | 227268 | PT | val.auc **0.866127**; true_best_side_auc **0.665461** |
| [R4 LB2 · s1](models/alpha_primary_R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed1/README.md) | 227268 | PT | val.auc **0.853418**; true_best_side_auc **0.649595** |
| [R4 LB2 · s2](models/alpha_primary_R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed2/README.md) | 227268 | PT | val.auc **0.871611**; true_best_side_auc **0.674253** |
| [R5 A4 · s3](models/alpha_primary_R5_A4_seq120_bs2048_ep30_lev0p5_sr0p0_sm0p0_seed3/README.md) | 227268 | PT | val.auc **0.867386**; true_best_side_auc **0.590465** |
| [R6 C2 · s2](models/alpha_primary_R6_C2_control_seq180_bs4096_ep30_lev0p25_sr0p1_sm0p0_seed2/README.md) | 227268 | PT | val.auc **0.864232**; true_best_side_auc **0.776629** |

## MakerPolicy V2 · Phase 6.5

| Model / 模型卡 | Parameters / 参数量 | Retained format / 留存格式 | Key result / 主要成绩 |
| --- | --- | --- | --- |
| [R1 A3 · s2](models/policy_primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed2/README.md) | 272149 | ONNX | **FAIL_NO_MAKER_EDGE** |
| [R1 A3 · s3](models/policy_primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed3/README.md) | 272149 | ONNX | **FAIL_NO_MAKER_EDGE** |
| [R2 A1 · s2](models/policy_primary_R2_A1_seq120_bs2048_ep30_lev0p5_sr0p0_sm0p1_seed2/README.md) | 272149 | ONNX | **FAIL_NO_MAKER_EDGE** |
| [R3 A6 · s2](models/policy_primary_R3_A6_seq120_bs2048_ep30_lev0p5_sr0p05_sm0p1_seed2/README.md) | 272149 | ONNX | **FAIL_NO_MAKER_EDGE** |
| [R4 LB2 · s1](models/policy_primary_R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed1/README.md) | 272149 | ONNX | **FAIL_NO_MAKER_EDGE** |
| [R4 LB2 · s2](models/policy_primary_R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed2/README.md) | 272149 | ONNX | **FAIL_NO_MAKER_EDGE** |
| [R6 C2 · s2](models/policy_primary_R6_C2_control_seq180_bs4096_ep30_lev0p25_sr0p1_sm0p0_seed2/README.md) | 272149 | ONNX | **FAIL_NO_MAKER_EDGE** |

## MakerPolicy V2 · Phase 6.7

| Model / 模型卡 | Parameters / 参数量 | Retained format / 留存格式 | Key result / 主要成绩 |
| --- | --- | --- | --- |
| [6.7 C0](models/policy_phase67_C0_control_anchor/README.md) | 272149 | ONNX | **FAIL_CONTROL_AMPLIFICATION** |
| [6.7 P1](models/policy_phase67_P1_signed_reward_filter/README.md) | 272149 | ONNX | **FAIL_CONTROL_AMPLIFICATION** |

## Deployment combination / 部署组合

| Model / 模型卡 | Parameters / 参数量 | Retained format / 留存格式 | Key result / 主要成绩 |
| --- | --- | --- | --- |
| [R1 Alpha + Policy](models/mpv2_r1_a3_seq120_seed2/README.md) | See component cards / 见组件模型卡 | ONNX | 2 paper runs + 13 live reports / 2 次模拟盘及 13 份实盘报告；final platform PnL N/A — unreconciled / 平台最终收益未核对 |

Only R1 s2 retains a complete historical Alpha + Policy ONNX pair; six other Phase 6.5 policies lack the paired Alpha ONNX. / 仅 R1 s2 保留完整历史 Alpha＋Policy ONNX 组合；其余六个 Phase 6.5 Policy 缺配对 Alpha ONNX。

[All 16 Alpha experiments / 全部 16 次 Alpha 实验](catalog/alpha-experiments.json): the eight missing weight sets remain in the ledger. / 另外八次权重未留存，指标仍保留。

Training, offline replay, paper and live are separate evidence levels. N/A always retains its reason in the cards and results. / 训练、离线回放、模拟盘与实盘分别报告；缺失值的原因见模型卡与成绩页。
