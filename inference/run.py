"""Run the archived interfaces. Inputs are raw ordered features, not normalized twice."""
import argparse
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch

from inference.alpha_model import AlphaModelV2
from inference.legacy_model import PolyArbSignalModel, PolyArbAgentModel
IQLModel = PolyArbAgentModel  # Historical BC and IQL architecture sources are identical.


def load_checkpoint(path, family):
    path = Path(path)
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    state = checkpoint.get("model_state_dict", checkpoint)
    if family == "alpha_v2":
        config = json.loads((path.parent / "train_config.json").read_text())["model_config"]
        model = AlphaModelV2(**config)
        seq_len, features = config["seq_len"], config["n_features"]
    else:
        args = checkpoint.get("args", {})
        seq_len = args.get("seq_len", 100 if family == "m5_iql" else 240)
        features = 65 if family == "m3" else 76
        cls = {"m3": PolyArbSignalModel, "m5_bc": PolyArbAgentModel, "m5_iql": IQLModel}[family]
        model = cls(seq_len=seq_len, d_model=state["transformer.proj.weight"].shape[0],
                    n_transformer_layers=len({k.split('.')[3] for k in state if k.startswith('transformer.transformer.layers.')}),
                    nhead=args.get("nhead", 4), dropout=args.get("dropout", 0.1), n_features=features)
    model.load_state_dict(state, strict=True)
    model.eval()
    return model, seq_len, features


def onnx_session(path):
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    return ort.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])


def onnx_forward(path, inputs=None):
    session = onnx_session(path)
    if inputs is None:
        inputs = {i.name: np.zeros(i.shape, dtype=np.float32) for i in session.get_inputs()}
    return dict(zip([o.name for o in session.get_outputs()], session.run(None, inputs)))


def deployment_forward(bundle, features, account_state):
    """account_state: cash, NAV, UP shares, DOWN shares, active resting count.

    cash and NAV are USDC (not raw six-decimal token units). No orders are placed.
    """
    bundle = Path(bundle)
    alpha = onnx_forward(bundle / "alpha/model.onnx", {"obs": features})
    alpha_input = np.concatenate([alpha["signal_logits"], alpha["signal_ev"]], axis=-1)
    return onnx_forward(bundle / "policy/model.onnx", {
        "features": features, "alpha": alpha_input, "account_state": account_state,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Checkpoint, ONNX, or deployment directory")
    parser.add_argument("--family", choices=["m3", "m5_bc", "m5_iql", "alpha_v2"])
    parser.add_argument("--inputs", type=Path, help="NPZ with the exact named raw inputs")
    parser.add_argument("--smoke", action="store_true", help="Construct zero inputs; proves execution only")
    args = parser.parse_args()
    if not args.smoke and args.inputs is None:
        parser.error("Provide --inputs or explicitly select --smoke")
    inputs = None
    if args.inputs:
        with np.load(args.inputs, allow_pickle=False) as data:
            inputs = {k: data[k] for k in data.files}
    torch.set_num_threads(2)
    if args.path.is_dir():
        inputs = inputs if inputs is not None else {
            "features": np.zeros((1, 120, 160), dtype=np.float32),
            "account_state": np.array([[100, 100, 0, 0, 0]], dtype=np.float32),
        }
        output = deployment_forward(args.path, **inputs)
    elif args.path.suffix == ".onnx":
        output = onnx_forward(args.path, inputs)
    else:
        if args.family is None:
            parser.error("--family is required for PyTorch checkpoints")
        model, seq_len, n_features = load_checkpoint(args.path, args.family)
        obs = np.zeros((1, seq_len, n_features), dtype=np.float32) if inputs is None else inputs["obs"]
        with torch.inference_mode():
            output = model(torch.from_numpy(obs))
        if not isinstance(output, dict):
            output = dict(zip(["signal_logits", "signal_ev"], output))
        output = {k: v.numpy() for k, v in output.items()}
    print(json.dumps({"synthetic": args.inputs is None, "outputs": {k: v.tolist() for k, v in output.items()}}, indent=2))


if __name__ == "__main__":
    main()
