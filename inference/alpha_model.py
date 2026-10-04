from __future__ import annotations

import torch.nn as nn
from torch import Tensor

from inference.legacy_model import InputNormalizer, SignalHead


class AlphaModelV2(nn.Module):
    """Minimal causal alpha model for the 160-dimensional V2 tick stream."""

    def __init__(
        self,
        *,
        seq_len: int = 240,
        n_features: int = 160,
        d_model: int = 128,
        n_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.n_features = n_features
        self.normalizer = InputNormalizer(n_features=n_features)
        self.input_proj = nn.Linear(n_features, d_model)
        self.encoder = nn.GRU(
            input_size=d_model,
            hidden_size=d_model,
            num_layers=n_layers,
            batch_first=True,
            dropout=dropout if n_layers > 1 else 0.0,
        )
        _ = seq_len
        self.head = SignalHead(d_model=d_model)

    def forward(self, obs: Tensor) -> tuple[Tensor, Tensor]:
        if obs.size(-1) != self.n_features:
            raise ValueError(
                f"AlphaModelV2 expected {self.n_features} features, got {obs.size(-1)}"
            )
        x = self.normalizer(obs)
        x = self.input_proj(x)
        encoded, _hidden = self.encoder(x)
        return self.head(encoded[:, -1, :])
