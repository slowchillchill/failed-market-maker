# 成绩与证据

[English](RESULTS.md) · [模型清单](MODELS.md)

训练损失、离线回放、模拟盘和真实资金账本分别报告。所有N/A都有原因，不能当作0或从未运行。金额为USDC。

## M3

| 模型 | 最佳轮次 | 训练损失 | 验证集 AUC | 测试集 AUC | 测试集最高十分位 EV |
| --- | --- | --- | --- | --- | --- |
| m3_run3 | 1 | 1.941012 | 0.773355 | 0.743551 | 0.245144 |
| m3_run_v7_M3-B1 | 13 | 0.277852 | 0.735678 | 0.713834 | -0.105901 |
| m3_run_v7_M3-B2 | 12 | 0.299922 | 0.735113 | 0.713882 | -0.086622 |

B1、B2固定执行测试收益分别为+92.2782、+137.8349，和AUC测试不是同一指标。 [source / 来源](evidence/history/m3m5/changelog/M3M5调参实验记录v7.md)

## M5 BC / IQL

BC最佳权重train/val/test accuracy分别为0.848722 / 0.710701 / 0.682590. 末轮epoch 4的val accuracy为0.703286；test N/A：未独立测试。

| 候选 | 最佳轮次 | 策略损失 | 验证集 Q 损失 | 最佳轮 Hold 占比 | 第50轮 Hold 占比 |
| --- | --- | --- | --- | --- | --- |
| m5_iql_0 | 46 | 4.649556 | 0.029637 | 92.60% | 93.85% |
| m5_iql_1 | 35 | 4.590885 | 0.028484 | 85.25% | 89.20% |
| m5_iql_2 | 43 | 4.635094 | 0.035254 | 94.25% | 95.30% |


| 24 validation windows / 24验证窗口 | Fixed execution / 固定执行 | Native execution / 原生执行 |
| --- | --- | --- |
| IQL-0 | +4.9118625% | +0.0220625% |
| IQL-1 | +2.9931583% | −2.1676542% |
| IQL-2 | +5.2948708% | −2.1522250% |

上表为平均窗口收益率，仅是离线验证；IQL独立test指标、paper/live均N/A：未找到独立对应报告。 [raw fixed/native reports / 固定与原生原始报告](evidence/m3m5-offline)

## Alpha Phase 5.8

| 候选 | 最佳轮次 | 训练损失 | val.auc | true_best_side_auc | 所选方向最高十分位 EV |
| --- | --- | --- | --- | --- | --- |
| R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed2 | 1 | 1.416982 | 0.868495 | 0.595098 | 0.065216 |
| R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed3 | 2 | 1.352764 | 0.861482 | 0.571024 | 0.138491 |
| R2_A1_seq120_bs2048_ep30_lev0p5_sr0p0_sm0p1_seed2 | 4 | 1.195743 | 0.872110 | 0.667253 | 0.042430 |
| R3_A6_seq120_bs2048_ep30_lev0p5_sr0p05_sm0p1_seed2 | 3 | 1.185670 | 0.866127 | 0.665461 | 0.013070 |
| R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed1 | 2 | 1.138801 | 0.853418 | 0.649595 | 0.093210 |
| R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed2 | 1 | 1.236778 | 0.871611 | 0.674253 | 0.047972 |
| R5_A4_seq120_bs2048_ep30_lev0p5_sr0p0_sm0p0_seed3 | 1 | 2.359265 | 0.867386 | 0.590465 | 0.026660 |
| R6_C2_control_seq180_bs4096_ep30_lev0p25_sr0p1_sm0p0_seed2 | 3 | 0.714006 | 0.864232 | 0.776629 | 0.068376 |

八个候选的独立test均N/A：未执行独立测试；单体paper/live均N/A：没有独立策略运行报告。R1 seed2仅作为组合一部分，不重复记组合收益。16次实验全部进入[experiment ledger / 实验台账](catalog/alpha-experiments.json)。

## MakerPolicy Phase 6.5–6.7

| 候选 | 最后 BC 损失 | 最后离线强化学习损失 |
| --- | --- | --- |
| primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed2 | 0.000110815 | 0.000076921 |
| primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed3 | 0.000117271 | 0.000079444 |
| primary_R2_A1_seq120_bs2048_ep30_lev0p5_sr0p0_sm0p1_seed2 | 0.000113844 | 0.000065989 |
| primary_R3_A6_seq120_bs2048_ep30_lev0p5_sr0p05_sm0p1_seed2 | 0.000113422 | 0.000071329 |
| primary_R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed1 | 0.000149778 | 0.000161845 |
| primary_R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed2 | 0.000143163 | 0.000158601 |
| primary_R6_C2_control_seq180_bs4096_ep30_lev0p25_sr0p1_sm0p0_seed2 | 0.000122122 | 0.000061272 |
| phase67_C0_control_anchor | 0.156779423 | 0.001588044 |
| phase67_P1_signed_reward_filter | 0.576368110 | 0.303230513 |

独立Val/Test loss均N/A：没有独立损失报告。下列收益来自回放，不能填补test loss。七个Phase6.5候选每个263窗口全部公开；Phase6.6仅三个候选每个30窗口，其余独立回放N/A：未独立测试。

| 阶段 | 候选 | 窗口数 | 各窗口收益之和 | 失败结论 |
| --- | --- | --- | --- | --- |
| phase65 | primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed2 | 263 | +46401.5289 | FAIL_NO_MAKER_EDGE |
| phase65 | primary_R6_C2_control_seq180_bs4096_ep30_lev0p25_sr0p1_sm0p0_seed2 | 263 | +46395.7014 | FAIL_NO_MAKER_EDGE |
| phase65 | primary_R3_A6_seq120_bs2048_ep30_lev0p5_sr0p05_sm0p1_seed2 | 263 | +46373.2969 | FAIL_NO_MAKER_EDGE |
| phase65 | primary_R2_A1_seq120_bs2048_ep30_lev0p5_sr0p0_sm0p1_seed2 | 263 | +46367.9046 | FAIL_NO_MAKER_EDGE |
| phase65 | primary_R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed2 | 263 | +46366.3567 | FAIL_NO_MAKER_EDGE |
| phase65 | primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed3 | 263 | +46360.5781 | FAIL_NO_MAKER_EDGE |
| phase65 | primary_R4_LB2_512_seq120_bs512_ep30_lev0p5_sr0p05_sm0p1_seed1 | 263 | +46356.4291 | FAIL_NO_MAKER_EDGE |
| phase66 | primary_R1_A3_seq120_bs2048_ep30_lev0p25_sr0p0_sm0p0_seed2 | 30 | +5336.6038 | FAIL_NO_MAKER_EDGE |
| phase66 | primary_R3_A6_seq120_bs2048_ep30_lev0p5_sr0p05_sm0p1_seed2 | 30 | +5334.8892 | FAIL_NO_MAKER_EDGE |
| phase66 | primary_R6_C2_control_seq180_bs4096_ep30_lev0p25_sr0p1_sm0p0_seed2 | 30 | +5332.3356 | FAIL_NO_MAKER_EDGE |
| phase67 | phase67_C0_control_anchor | 263 | +45844.6815 | FAIL_CONTROL_AMPLIFICATION |
| phase67 | phase67_P1_signed_reward_filter | 263 | +6867.8120 | FAIL_CONTROL_AMPLIFICATION |

各窗口是独立运行，不是一个账户的连续收益或收益率。Phase6.5/6.6共同输入上解码动作相同，未证明maker优势；Phase6.7对照放大，独立测试N/A：失败后未启动。 [evidence links / 证据链接](catalog/offline-results.json)

## Paper trade / 模拟盘

| 运行标识（UTC） | 指标口径 | B1 | B2 | BC（m5_baseline） | R1 Alpha＋Policy |
| --- | --- | --- | --- | --- | --- |
| [run-p22-three-profile-72h-20260517T022156Z](evidence/paper/run-p22-three-profile-72h-20260517T022156Z/reports/report-20260517T083623Z.json) | nav_delta_total | +100.0507 | -99.0588 | -99.5530 | N/A — not included / 未包含 |
| [run-tpsl-three-profile-72h-no-raw-tp30-20260517T223411Z](evidence/paper/run-tpsl-three-profile-72h-no-raw-tp30-20260517T223411Z/final-reports/report-20260519T135915Z.json) | adjusted_total_pnl_usdc | -55.7933 | +78.4222 | -47.7168 | N/A — not included / 未包含 |
| [run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z](evidence/paper/run-tpsl-three-profile-72h-no-raw-v2merge-tp30-20260519T141035Z/codex_reports/report-20260522T234126Z.json) | adjusted_total_pnl_usdc | -104.6874 | +43.0920 | -0.4547 | N/A — not included / 未包含 |
| [run-four-profile-72h-mpv2-restart-20260527T161918Z](evidence/paper/run-four-profile-72h-mpv2-restart-20260527T161918Z/reports/report-20260530T162518Z.json) | adjusted_total_pnl_usdc | -127.7975 | -100.6707 | +20.1954 | +1114.9697 |
| [run-four-profile-7d-direct-official-20260602T135518Z](evidence/paper/run-four-profile-7d-direct-official-20260602T135518Z/reports/standard/report-terminated-20260607T122104Z.json) | adjusted_total_pnl_usdc | -298.0387 | -224.9895 | +84.7787 | +1791.3144 |

五次报告时长依次为6.22小时（提前停止）、39.30小时（提前停止）、72.07小时、71.98小时，以及06-02开始的终止运行。最后一轮不是完成七天测试：B1/B2末次决策分别为06-05 11:37:05/11:44:01 UTC，BC和R1为18:09:59；进程06-07才终止。逐模型首末决策时间见[paper ledger / 模拟盘台账](catalog/paper-results.json)。

adjusted_total_pnl_usdc包括已关闭风控段和当前有效段；重置补本金不是收益，不能简化为末NAV减100。返佣按标准JSON的accrual/payout/pending分别展示，不相加重复记账。风格分析中的疑似重复汇总返佣不进入摘要。不同运行不相加为历史总收益，未结算、排队与提前停止假设继续保留。其余候选paper为N/A：无对应运行报告。

## Live trade / 真实资金

仅归属mpv2_r1_a3_seq120_seed2。下面是原运行报告值，未重新核算。

| 运行标识（UTC） | 保守 NAV 变化 | 仅已实现部分 | 平台最终账户收益 |
| --- | --- | --- | --- |
| [20260618T194241Z](evidence/live/r5-three-market-live-funds-20260618T194241Z/trading-runtime/run_manifest.json) | 0.290000 | 0.05 | N/A — not reconciled / 未核对 |
| [20260618T211230Z](evidence/live/r5-three-market-live-funds-20260618T211230Z/trading-runtime/run_manifest.json) | -5.500000 | 0 | N/A — not reconciled / 未核对 |
| [20260618T215747Z](evidence/live/r5-three-market-live-funds-20260618T215747Z/trading-runtime/run_manifest.json) | 0.250000 | 0 | N/A — not reconciled / 未核对 |
| [20260618T230237Z](evidence/live/r5-three-market-live-funds-20260618T230237Z/trading-runtime/run_manifest.json) | N/A — NAV unobservable / NAV不可观测 | 0 | N/A — not reconciled / 未核对 |
| [20260619T002200Z](evidence/live/r5-three-market-live-funds-20260619T002200Z/trading-runtime/run_manifest.json) | N/A — NAV unobservable / NAV不可观测 | 0 | N/A — not reconciled / 未核对 |
| [20260619T020053Z](evidence/live/r5-three-market-live-funds-20260619T020053Z/trading-runtime/run_manifest.json) | N/A — NAV unobservable / NAV不可观测 | 0 | N/A — not reconciled / 未核对 |
| [20260619T092850Z](evidence/live/r5-three-market-live-funds-20260619T092850Z/trading-runtime/run_manifest.json) | N/A — NAV unobservable / NAV不可观测 | -0.3166666666666666666666666667 | N/A — not reconciled / 未核对 |
| [20260621T022402Z](evidence/live/r5-three-market-live-funds-20260621T022402Z/trading-runtime/run_manifest.json) | 0.00000 | 0 | N/A — not reconciled / 未核对 |
| [20260621T061651Z](evidence/live/r5-three-market-live-funds-20260621T061651Z/trading-runtime/run_manifest.json) | N/A — NAV unobservable / NAV不可观测 | 0 | N/A — not reconciled / 未核对 |
| [20260621T131804Z](evidence/live/r5-three-market-live-funds-20260621T131804Z/trading-runtime/run_manifest.json) | N/A — NAV unobservable / NAV不可观测 | -2.9291068562050986592668483156 | N/A — not reconciled / 未核对 |
| [20260621T150800Z](evidence/live/r5-three-market-live-funds-20260621T150800Z/trading-runtime/run_manifest.json) | N/A — NAV unobservable / NAV不可观测 | 0.0 | N/A — not reconciled / 未核对 |
| [20260622T082624Z](evidence/live/r5-three-market-live-funds-20260622T082624Z/trading-runtime/run_manifest.json) | -8.50500000 | -0.3298076923076923076923076923 | N/A — not reconciled / 未核对 |
| [20260622T120633Z](evidence/live/r5-three-market-live-funds-20260622T120633Z/trading-runtime/run_manifest.json) | -18.87545541 | -4.1507300217332112807109676924 | N/A — not reconciled / 未核对 |

06-21 02:24一轮零下单零成交，其0仅属于该轮。NAV不可观测时，已实现为0也不代表总收益为0。报告保留SDK尝试数、成交计数、停止原因、未实现持仓和账本限制，并明确final_platform_pnl_unavailable与platform_pnl_evidence_complete=false；不能合计累计净盈利、补造收益率、最大回撤或最终权益。其他模型live为N/A：未找到对应运行证据。

## Other stages / 其他阶段

M1是回放引擎，M2是特征工程；早期规则策略无训练权重。M3 A6和M5 BC-6权重N/A：未找到保留权重；其离线对照仍公开，BC-6测试PnL −11.0374，FAIL。新版架构正式训练权重、训练成绩、paper/live盈利成绩均N/A：没有正式训练交付；组件、初始化和性能验证只属工程证据。

06-04—05旧live runtime有真实下单与余额记录，但成交查询、收益核算不完整；06-12—14 SDK有真实成交，同时发现原始USDC单位进入模型输入的问题；两阶段模型收益均N/A：不足以完整核算。06-19 01:54启动失败，未进入交易，不能写零收益。06-25—26平台卖出可用性探针是基础设施实验：30个有效样本，clean_accept_ms中位数1939、P95 3357，整体gate因CSV writer验证未通过；模型收益N/A：非策略盈利实验。

[historical evidence / 历史证据](evidence/history) · [new architecture / 新架构证据](evidence/new-architecture)
