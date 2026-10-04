# The Failed Market Maker：一个失败做市模型的成长记录

**这个项目未能证明已经学到、且经平台最终收益核对的实盘交易优势。** 本档案公开权重、曾经看起来有希望的成绩、负收益，以及改变这些成绩解释的失败证据。

[English](README.md) · [模型清单](MODELS.md) · [完整成绩](RESULTS.zh-CN.md) · [成长故事](STORY.zh-CN.md) · [最小推理](INFERENCE.md) · [来源与脱敏](PROVENANCE.md)

[GitHub](https://github.com/slowchillchill/failed-market-maker) · [Hugging Face](https://huggingface.co/slowchillchill/failed-market-maker) · [模型下载包](https://github.com/slowchillchill/failed-market-maker/releases/tag/v1.0.0)

项目围绕 Polymarket BTC UP/DOWN 五分钟市场，使用 Polymarket 盘口、Binance 行情和 Chainlink 观察数据。从回放引擎和特征工程起步，先训练监督信号，再尝试行为克隆和离线强化学习，最终形成 Alpha＋MakerPolicy 的模拟盘与实盘组合，并转向新版架构。这次发布保留这一过程，不重建完整训练或交易工程。

## 公开内容

共 **24 个保留权重的训练候选**：3 个 M3、1 个 M5 BC、3 个 M5 IQL、8 个 Alpha、7 个 MakerPolicy、2 个 Phase 6.7 修复／对照候选。实盘部署组合单独列出，适配导出与部署副本不重复计算。Phase 5.8 共16次primary实验，另外8次虽然权重未保留，指标仍进入台账。

| 证据层次 | 已有事实 | 不能据此证明 |
| --- | --- | --- |
| M3监督测试 | B1/B2测试AUC约0.714，top-decile EV为负 | AUC不能单独证明策略盈利 |
| M5 BC/IQL | BC测试accuracy 0.682590；IQL大量选择Hold，原生执行弱于固定执行 | 训练与验证指标不是模拟盘或实盘收益 |
| Alpha | 8份权重和全部16次primary实验记录 | 没有单体策略收益，未执行独立test |
| MakerPolicy | 很低的损失和正的窗口回放收益之和 | Phase6.5/6.6为FAIL_NO_MAKER_EDGE；Phase6.7为FAIL_CONTROL_AMPLIFICATION |
| Paper | 5次报告，保留亏损和提前终止运行 | 模拟成交、返佣和风控重置依赖原始假设 |
| Live | 13次可归属本地账本报告，以及启动、基础设施失败 | 平台最终账户收益N/A：尚未核对 |

06-02开始的paper运行中，R1 Alpha＋Policy报告 **+1791.3144 USDC adjusted PnL**，但06-05已经停止决策，不是完成七天测试。06-22 12:06的live报告记录 **−18.87545541 USDC本地保守NAV变化**，其中包含未实现持仓，也不是平台最终账户收益。这两类结果都应保留。[逐次证据](RESULTS.zh-CN.md)

## 下载与推理

GitHub仓库保存双语故事、模型卡、合同、原始指标报告和推理代码；Release中的模型包保留 `models/<model_id>/` 结构，与Hugging Face一致。将模型包解压到仓库根目录，或下载完整Hugging Face仓库。BC ONNX必须保留同目录 `.onnx.data`；每份模型都要保留归一化、特征与配置文件。

```bash
python -m inference.run models/m3_run3/best_model.pt --family m3 --smoke
python -m inference.run models/m5_v7v72_bc/agent_model_m5.onnx --smoke
python -m inference.run models/mpv2_r1_a3_seq120_seed2 --smoke
```

在已有[依赖](requirements.txt)的环境运行。输入顺序、USDC单位和归一化规则见[最小推理说明](INFERENCE.md)。这些命令只执行构造输入前向，不下单、不训练、不回放市场，成功不代表盈利。

## 如何审阅

[统一清单](manifest.json)列出model_id、文件、字节数、逻辑来源、脱敏转换、许可证及完整性缺口。[模型清单](MODELS.md)链接每张双语卡，[成绩页](RESULTS.zh-CN.md)分开训练、离线回放、paper和live。N/A总是注明原因，不替换为零。

新版架构正式训练权重、训练成绩、paper/live盈利成绩均为 **N/A：本档案没有正式训练交付**。组件、接口及性能验证单列为工程证据。`evidence/` 内历史文档是原始过程记录，不是当前部署指令；其中相对链接可能指向未公开的历史私有文件。

原创代码及权重采用 [Apache-2.0](LICENSE)，整理文档和报告采用 [CC-BY-4.0](LICENSE-CC-BY-4.0)。归属和第三方依赖边界见[NOTICE](NOTICE)。不分发原始市场数据集。
