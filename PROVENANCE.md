# Provenance, omissions and redaction / 来源、缺口与脱敏

[manifest.json](manifest.json) is the publication file inventory, with stable model IDs, relative paths, bytes, formats, licenses, logical sources, transformations and evaluation links. Complete absolute source mappings are retained privately by the publisher; they are not included in either platform. / 统一清单保留模型身份、文件、字节数、格式、许可证、逻辑来源、脱敏转换和成绩链接；完整绝对路径映射只在发布者本机保留。

Logical source labels distinguish the legacy training tree, the M3/M5 training tree, paper tree, V2 tree, SDK deployment and newer architecture. Same-named M3 collection exports from training and paper remain separate. The `m5_baseline` deployment alias points to v7v72 BC, not a second independently trained model. / 逻辑来源区分各工作树；同名collection不合并；m5_baseline是BC部署别名。

Public copies replace private home paths, infrastructure addresses, training hosts, wallet addresses and credential values with explicit markers. Checkpoint metadata can be reserialized after restricted loading; every tensor was compared directly to the local source. BC ONNX private paths were removed only from export metadata, with the graph computation and external-data references preserved. [Transformation report](verification/onnx-redaction.json) · [Load/forward evidence](verification/models.json). / 公开副本脱敏私人路径、主机、钱包和凭据；checkpoint仅改元数据，逐张量与原件比较；BC ONNX仅清理导出元数据。

Historical digest fields are retained as unverified provenance of the original artifacts. They do not claim to authenticate redacted JSON or reserialized weights. No new standalone digest calculation or comparison is part of publication acceptance. Official upload protocols may perform their required content hashing under the publication authorization. / 历史摘要不用于认证脱敏后副本，不新增独立SHA校验；上传协议必需处理按发布授权执行。

The binary weights and inference code use Apache-2.0; curated prose, model cards, metrics and historical reports use CC-BY-4.0. Feature/normalization artifacts necessary to use weights follow Apache-2.0. Underlying third-party software retains its own licenses. Raw market datasets are not part of this release. / 代码权重及推理所需特征归一化采用Apache-2.0，整理文档、指标及报告采用CC-BY-4.0，第三方依赖保留自身许可证。

Explicit gaps:

- M3 A6 / M5 BC-6: weights N/A — not retained; their evaluation/failure records remain. / 权重未留存，评测仍保留。
- Eight of sixteen primary Alpha experiments: weights N/A — not retained locally. / 16次实验中8次未保留权重。
- Policy `.pt`: N/A — only historical ONNX weights survive. Six Phase 6.5 policies lack paired Alpha ONNX; their Alpha PyTorch candidates survive. No replacement export was manufactured. / Policy无本地pt；六个候选缺配对历史Alpha ONNX，未伪造导出。
- M3 exact split manifests referenced by old checkpoint paths: N/A — not found locally. Dataset paths, recorded parameters, logs and historical split rules remain; do not claim exact data replay from this archive alone. / M3旧路径引用的精确切分清单未找到，不能据本包声称精确数据重现。
- June 19 01:54 startup failure: trading-runtime manifest N/A — no retained trading-runtime manifest, execution report preserved. / 启动失败只留执行报告。
- Independent tests absent from a stage are not replaced with training-boundary replay. Standalone model paper/live is not replaced with deployment-combination results. / 训练边界回放不能替代独立测试，组合收益不能回填单体。
- Final platform account PnL: N/A — not reconciled in the retained live reports. / 实盘报告未完成平台最终账户核对。
- Per-epoch checkpoints, invalid bundles, incomplete `.bak0428` exports, redundant deployment aliases and raw trading event streams are outside the official model download collection. / 逐轮权重、失效组合和备份、重复别名及原始交易事件流不进入正式模型集合。

Historical source documents preserve their original languages and obsolete decisions. They are provided as evidence, not current instructions or endorsements. Their internal links can point outside this selected archive. The curated English and Chinese guides contain the current publication interpretation. / 历史文档保持原语言及当时结论，内部链接可能指向未公开文件；本次双语整理页说明当前证据解释。

Additional selected sources / 补充来源：[June 4–5 legacy runtime](evidence/legacy-live), [June 12–14 SDK execution](evidence/early-live).
