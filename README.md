---
license: apache-2.0
language:
- en
- zh
tags:
- onnx
- pytorch
- reinforcement-learning
- time-series
- prediction-markets
- negative-results
---
# The Failed Market Maker

**An archive of a market-making project that did not establish a learned, independently verified live trading edge.** It includes the weights, the promising results, the losses, and the evidence that changed the interpretation of those results.

[完整中文](README.zh-CN.md) · [Models](MODELS.md) · [Results](RESULTS.md) · [Development story](STORY.md) · [Inference](INFERENCE.md) · [Provenance and redaction](PROVENANCE.md)

[GitHub](https://github.com/slowchillchill/failed-market-maker) · [Hugging Face](https://huggingface.co/slowchillchill/failed-market-maker) · [GitHub model release](https://github.com/slowchillchill/failed-market-maker/releases/tag/v1.0.0)

The project explored Polymarket BTC UP/DOWN five-minute markets using Polymarket order books, Binance market data and Chainlink observations. It evolved from a replay engine and feature pipeline, through supervised signals and offline policies, into an Alpha + MakerPolicy deployment and a newer architecture. This release preserves that progression without rebuilding the training or trading system.

## What is here

There are **24 retained trained candidates**: 3 M3, 1 M5 behavior-cloning model, 3 M5 IQL models, 8 Alpha models, 7 MakerPolicy models and 2 Phase 6.7 repair/control candidates. The Alpha + Policy live deployment is listed separately; adapted exports and deployment copies are not extra trained candidates. The other eight Phase 5.8 primary experiments remain in the experiment ledger even though their weights were not retained.

| Evidence | What it says | What remains unproven |
| --- | --- | --- |
| M3 supervised tests | Test AUC about 0.714 for B1/B2; their test top-decile EV is negative | AUC alone does not establish a profitable strategy |
| M5 BC / IQL | BC test accuracy 0.682590; IQL strongly favored Hold, with worse native than fixed execution results | Training/validation metrics are not paper or live PnL |
| Alpha | Eight retained models and all 16 primary experiment records | No standalone Alpha strategy PnL; independent test not executed |
| MakerPolicy | Low losses and positive window-sum replay PnL | Phase 6.5/6.6: `FAIL_NO_MAKER_EDGE`; Phase 6.7: `FAIL_CONTROL_AMPLIFICATION` |
| Paper | Five reports, including negative and prematurely stopped runs | Simulated fills, rebates and resets require their original assumptions |
| Live | Thirteen attributable local-ledger reports, plus startup and infrastructure failures | Final platform account PnL is **N/A — not reconciled** |

The June 2 paper run reported **+1,791.3144 USDC adjusted PnL** for the R1 Alpha + Policy combination, but decisions stopped on June 5. It was not a completed seven-day test. The June 22 12:06 live report recorded **−18.87545541 USDC local conservative NAV change**, including unrealized inventory; it was not a final platform account reconciliation. Both belong in the record. [Run-specific evidence](RESULTS.md)

## Download and run

The repository contains the bilingual narrative, model cards, contracts, original metric reports and inference code. GitHub Release holds a model archive with the same `models/<model_id>/` directory structure used on Hugging Face. Extract the archive into this repository root, or obtain the complete Hugging Face repository. Preserve companion files: the BC ONNX requires its `.onnx.data` file, and contracts/normalization must travel with each model.

```bash
python -m inference.run models/m3_run3/best_model.pt --family m3 --smoke
python -m inference.run models/m5_v7v72_bc/agent_model_m5.onnx --smoke
python -m inference.run models/mpv2_r1_a3_seq120_seed2 --smoke
```

Use an environment with the dependencies in [requirements.txt](requirements.txt). [Inference instructions](INFERENCE.md) describe actual input ordering and the distinction between a constructed-input check and historical evaluation. These commands place no orders and do not train or replay markets.

## Reading the archive

[manifest.json](manifest.json) is the unified inventory: model identities, exact files, byte counts, logical source locations, transformations, licenses and completeness gaps. [MODELS.md](MODELS.md) links every bilingual model card. [RESULTS.md](RESULTS.md) separates training, offline replay, paper and live results. Missing values always include a reason; they are never replaced with zero.

The newer architecture's formal trained model files, training scores and paper/live profitability are **N/A — no formal trained release in this archive**. Its component and interface checks are engineering evidence. Historical documents under `evidence/` are source records, not current deployment instructions; their relative links may refer to private historical files not included here.

Original code and weights are licensed under [Apache-2.0](LICENSE). Curated documents and reports are licensed under [CC-BY-4.0](LICENSE-CC-BY-4.0). Attribution and dependency boundaries appear in [NOTICE](NOTICE). Raw market datasets are not distributed.
