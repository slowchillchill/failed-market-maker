"""Check the published archive without computing hashes. Run from repository root."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import onnx
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from inference.run import load_checkpoint, onnx_forward, deployment_forward


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert sum(m["training_candidate"] for m in manifest["models"]) == 24
    torch.set_num_threads(2)
    checked = 0
    for row in manifest["files"]:
        path = ROOT / row["path"]
        assert path.is_file(), row["path"]
        assert path.stat().st_size == row["bytes"], row["path"]
        assert "checkpoint_epoch" not in row["path"], row["path"]
        if path.suffix == ".json":
            json.loads(path.read_text())
    for model in manifest["models"]:
        for path in sorted((ROOT / model["path"]).rglob("*")):
            if path.suffix == ".pt":
                network, seq, features = load_checkpoint(path, model["family"])
                with torch.inference_mode():
                    outputs = network(torch.zeros(1, seq, features))
                outputs = outputs.values() if isinstance(outputs, dict) else outputs
                assert all(torch.isfinite(v).all() for v in outputs), str(path)
            elif path.suffix == ".onnx":
                onnx.checker.check_model(onnx.load(str(path)))
                assert all(np.isfinite(v).all() for v in onnx_forward(path).values()), str(path)
            elif path.suffix == ".npz":
                with np.load(path, allow_pickle=False) as data:
                    for key in data.files:
                        data[key]
            else:
                continue
            checked += 1
            print("PASS", path.relative_to(ROOT), flush=True)
    result = deployment_forward(ROOT / "models/mpv2_r1_a3_seq120_seed2",
                                np.zeros((1, 120, 160), dtype=np.float32),
                                np.array([[100, 100, 0, 0, 0]], dtype=np.float32))
    assert all(np.isfinite(v).all() for v in result.values())
    # Curated links must resolve; historical reports may reference omitted private artifacts.
    for path in list(ROOT.glob("*.md")) + list(ROOT.glob("models/*/README.md")):
        for url in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if "://" not in url and not url.startswith("#"):
                assert (path.parent / url.split("#")[0]).exists(), (str(path), url)
    print(f"PASS: {checked} model/companion files, deployment chain, manifest bytes and curated links")


if __name__ == "__main__":
    main()
