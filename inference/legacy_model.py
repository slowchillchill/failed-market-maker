"""
PolyArbSignalModel — Phase 1 supervised pretraining architecture.

Branch layout (matches FEATURE_COLS in dataloader.py, indices fixed):
    obs[:, :,  0:36] → PolymarketBranch  (TCN, out 64)
    obs[:, :, 36:59] → BinanceBranch     (TCN, Binance 20 + BLB 3 = 23, out 64)
    obs[:, :, 59:63] → ChainlinkBranch   (MLP per-timestep, out 64)
    obs[:, :, 63:65] → time context      (injected directly into TinyCausalTransformer)

All branches → concat (B, T, 192) + time (B, T, 2) → linear(194, d_model) →
    TinyCausalTransformer (d_model=128, 2 layers, 4 heads) →
    SignalHead(state[:, -1, :]) → (logits [B, 2], ev_pred [B, 2])
"""

import math
import torch
import torch.nn as nn
from torch import Tensor


# ---------------------------------------------------------------------------
# Building block: causal 1-D convolution unit
# ---------------------------------------------------------------------------

class CausalConv1dBlock(nn.Module):
    """Single causal dilated conv block with residual connection.

    Left-pads by dilation * (kernel_size - 1) so output length == input length
    and no future information leaks in.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 4,
        dilation: int = 1,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.pad = dilation * (kernel_size - 1)
        self.conv = nn.Conv1d(
            in_channels,
            out_channels,
            kernel_size=kernel_size,
            dilation=dilation,
            padding=0,
        )
        self.norm = nn.LayerNorm(out_channels)
        self.act = nn.ReLU()
        self.drop = nn.Dropout(dropout)
        # 1×1 projection for residual when channel dims differ
        self.res_proj = (
            nn.Conv1d(in_channels, out_channels, kernel_size=1)
            if in_channels != out_channels
            else nn.Identity()
        )

    def forward(self, x: Tensor) -> Tensor:
        # x: (B, C, T) — channels-first for Conv1d
        residual = self.res_proj(x)
        out = torch.nn.functional.pad(x, (self.pad, 0))
        out = self.conv(out)             # (B, out_channels, T)
        out = out.transpose(1, 2)       # (B, T, out_channels) for LayerNorm
        out = self.norm(out)
        out = out.transpose(1, 2)       # back to (B, out_channels, T)
        out = self.act(out)
        out = self.drop(out)
        return out + residual


# ---------------------------------------------------------------------------
# CausalTCN: stack of CausalConv1dBlocks
# ---------------------------------------------------------------------------

class CausalTCN(nn.Module):
    """4-layer causal TCN with exponentially growing dilation [1,2,4,8].

    Args:
        in_dim:   number of input features (channels)
        out_dim:  output channels per timestep (default 64)
    Input:  (B, T, in_dim)   — time-last is natural for dataset, convert inside
    Output: (B, T, out_dim)
    """

    def __init__(
        self,
        in_dim: int,
        out_dim: int = 64,
        kernel_size: int = 4,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        dilations = [1, 2, 4, 8]
        layers = []
        c_in = in_dim
        for d in dilations:
            layers.append(CausalConv1dBlock(c_in, out_dim, kernel_size, d, dropout))
            c_in = out_dim
        self.net = nn.Sequential(*layers)

    def forward(self, x: Tensor) -> Tensor:
        # x: (B, T, in_dim)
        x = x.transpose(1, 2)          # (B, in_dim, T)
        x = self.net(x)                # (B, out_dim, T)
        return x.transpose(1, 2)       # (B, T, out_dim)


# ---------------------------------------------------------------------------
# Branch encoders
# ---------------------------------------------------------------------------

class PolymarketBranch(nn.Module):
    """Encodes Polymarket Up+Down orderbook features (36 cols → 64 per timestep)."""

    def __init__(self, dropout: float = 0.1) -> None:
        super().__init__()
        self.tcn = CausalTCN(in_dim=36, out_dim=64, dropout=dropout)

    def forward(self, x: Tensor) -> Tensor:
        # x: (B, T, 36)
        return self.tcn(x)              # (B, T, 64)


class BinanceBranch(nn.Module):
    """Encodes Binance raw+derived+depth (20) + BLB (3) = 23 cols → 64 per timestep."""

    def __init__(self, dropout: float = 0.1) -> None:
        super().__init__()
        self.tcn = CausalTCN(in_dim=23, out_dim=64, dropout=dropout)

    def forward(self, x: Tensor) -> Tensor:
        # x: (B, T, 23)
        return self.tcn(x)              # (B, T, 64)


class ChainlinkBranch(nn.Module):
    """Encodes Chainlink features (4 cols → 64) per timestep via MLP.

    Chainlink updates ~1 Hz; temporal context is handled by the Transformer
    fusion layer, so per-timestep MLP is sufficient here.
    """

    def __init__(self, dropout: float = 0.1) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 64),
            nn.ReLU(),
        )

    def forward(self, x: Tensor) -> Tensor:
        # x: (B, T, 4)
        return self.net(x)              # (B, T, 64)


# ---------------------------------------------------------------------------
# TinyCausalTransformer fusion layer
# ---------------------------------------------------------------------------

class TinyCausalTransformer(nn.Module):
    """Fuses branch encodings with causal self-attention.

    Input:
        branch_concat: (B, T, 192)  — concat of 3 × 64-dim branch outputs
        time_ctx:      (B, T, 2)    — time_to_expiry_ms + step_index

    Processing:
        1. project: linear(194, d_model)
        2. add sinusoidal positional encoding
        3. 2-layer TransformerEncoderLayer with causal mask
    Output: (B, T, d_model)
    """

    def __init__(
        self,
        d_model: int = 128,
        n_layers: int = 2,
        nhead: int = 4,
        dim_feedforward: int = 256,
        dropout: float = 0.1,
        max_seq_len: int = 512,
    ) -> None:
        super().__init__()
        self.proj = nn.Linear(192 + 2, d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,   # (B, T, d_model) convention
            norm_first=True,    # Pre-LN for training stability
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)

        # Sinusoidal positional encoding (fixed, not learned)
        pe = self._make_pe(max_seq_len, d_model)
        self.register_buffer("pe", pe)  # (1, max_seq_len, d_model)

    @staticmethod
    def _make_pe(max_len: int, d_model: int) -> Tensor:
        pos = torch.arange(max_len).unsqueeze(1).float()
        div = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe = torch.zeros(1, max_len, d_model)
        pe[0, :, 0::2] = torch.sin(pos * div)
        pe[0, :, 1::2] = torch.cos(pos * div[: d_model // 2])
        return pe

    @staticmethod
    def _causal_mask(seq_len: int, device: torch.device) -> Tensor:
        """Additive causal mask: 0.0 for visible, -inf for future positions.

        Using float additive mask (not bool) + is_causal=True is the correct
        way to enable SDPA/FlashAttention in PyTorch 2.x: the bool mask path
        forces the slower generic attention kernel.
        """
        return nn.Transformer.generate_square_subsequent_mask(seq_len, device=device)

    def forward(self, branch_concat: Tensor, time_ctx: Tensor) -> Tensor:
        # branch_concat: (B, T, 192), time_ctx: (B, T, 2)
        x = torch.cat([branch_concat, time_ctx], dim=-1)   # (B, T, 194)
        x = self.proj(x)                                    # (B, T, d_model)
        T = x.size(1)
        x = x + self.pe[:, :T, :]                          # add positional encoding
        # Float additive mask + is_causal=True → SDPA dispatches to FlashAttention on CUDA
        mask = self._causal_mask(T, x.device)
        x = self.transformer(x, mask=mask, is_causal=True)  # (B, T, d_model)
        return x


# ---------------------------------------------------------------------------
# Input normalizer (non-learnable, computed from training data)
# ---------------------------------------------------------------------------

class InputNormalizer(nn.Module):
    """Per-feature standardization: x → (x - mean) / std.

    mean and std are registered as non-learnable buffers so they are saved
    and loaded with the model checkpoint automatically.

    Missing values (NaN, from zero-padding or sparse features) are replaced
    with 0.0 AFTER normalization, which maps to the feature mean —
    a neutral "no information" sentinel.

    Usage:
        normalizer = InputNormalizer(n_features=65)
        normalizer.set_stats(mean_arr, std_arr)   # call once before training
        x_norm = normalizer(x)                    # called in model.forward()
    """

    def __init__(self, n_features: int = 65) -> None:
        super().__init__()
        self.register_buffer("_mean", torch.zeros(n_features, dtype=torch.float32))
        self.register_buffer("_std", torch.ones(n_features, dtype=torch.float32))

    def set_stats(self, mean: "np.ndarray", std: "np.ndarray") -> None:
        import numpy as np
        self._mean.copy_(torch.from_numpy(np.asarray(mean, dtype=np.float32)))
        self._std.copy_(torch.from_numpy(np.asarray(std, dtype=np.float32)))

    def forward(self, x: Tensor) -> Tensor:
        # x: (B, T, F) or (B, F)
        normed = (x - self._mean) / self._std
        # NaN (missing values / zero-padding) → 0.0 (= "feature mean" in normalized space)
        # Use `normed != normed` (IEEE NaN property) instead of nan_to_num for DML compatibility
        nan_mask = normed != normed
        return torch.where(nan_mask, torch.zeros_like(normed), normed)


# ---------------------------------------------------------------------------
# SignalHead
# ---------------------------------------------------------------------------

class SignalHead(nn.Module):
    """Output head for Phase 1 supervised pretraining.

    Takes the last-timestep state embedding and produces:
        logits   (B, 2): raw class logits for Up/Down (passed to CrossEntropyLoss)
        ev_pred  (B, 2): predicted [ev_up, ev_down] — regressed against y_ev_up/down

    Both heads share a Linear(d_model, 64) stem.
    """

    def __init__(self, d_model: int = 128) -> None:
        super().__init__()
        self.stem = nn.Sequential(nn.Linear(d_model, 64), nn.ReLU())
        self.cls_head = nn.Linear(64, 2)
        self.ev_head = nn.Linear(64, 2)

    def forward(self, state: Tensor) -> tuple[Tensor, Tensor]:
        # state: (B, d_model) — last timestep only
        h = self.stem(state)
        logits = self.cls_head(h)   # (B, 2)
        ev_pred = self.ev_head(h)   # (B, 2)  [ev_up, ev_down]
        return logits, ev_pred


# ---------------------------------------------------------------------------
# Top-level model
# ---------------------------------------------------------------------------

class PolyArbSignalModel(nn.Module):
    """Multi-branch TCN + TinyCausalTransformer + SignalHead for Phase 1.

    Column slicing (matches FEATURE_COLS in dataloader.py):
        obs[:, :,  0:36]  → PolymarketBranch
        obs[:, :, 36:59]  → BinanceBranch   (Binance 20 + BLB 3)
        obs[:, :, 59:63]  → ChainlinkBranch
        obs[:, :, 63:65]  → time_ctx injected into TinyCausalTransformer

    Args:
        seq_len:             expected sequence length (for PE buffer sizing)
        d_model:             Transformer hidden dim (default 128)
        n_transformer_layers: number of TransformerEncoderLayer stacks (default 2)
        nhead:               attention heads (default 4)
        dropout:             applied in TCN blocks, Transformer, and MLP

    Forward:
        obs: (B, T, 65)  float32
        returns: (logits [B, 2], ev_pred [B, 2])
    """

    def __init__(
        self,
        seq_len: int = 240,
        d_model: int = 128,
        n_transformer_layers: int = 2,
        nhead: int = 4,
        dropout: float = 0.1,
        n_features: int = 65,
    ) -> None:
        super().__init__()
        self.normalizer = InputNormalizer(n_features=n_features)
        self.poly_branch = PolymarketBranch(dropout=dropout)
        self.binance_branch = BinanceBranch(dropout=dropout)
        self.chainlink_branch = ChainlinkBranch(dropout=dropout)
        self.transformer = TinyCausalTransformer(
            d_model=d_model,
            n_layers=n_transformer_layers,
            nhead=nhead,
            dim_feedforward=d_model * 2,
            dropout=dropout,
            max_seq_len=max(seq_len + 16, 512),
        )
        self.head = SignalHead(d_model=d_model)

    def forward(self, obs: Tensor) -> tuple[Tensor, Tensor]:
        # obs: (B, T, 65) — raw feature values, may contain NaN
        obs = self.normalizer(obs)          # → zero mean, unit var; NaN → 0.0

        poly_feat = obs[:, :, 0:36]        # Polymarket Up+Down (normalized)
        bin_feat = obs[:, :, 36:59]        # Binance + BLB (normalized)
        cl_feat = obs[:, :, 59:63]         # Chainlink (normalized)
        time_ctx = obs[:, :, 63:65]        # time context (normalized)

        poly_enc = self.poly_branch(poly_feat)      # (B, T, 64)
        bin_enc = self.binance_branch(bin_feat)     # (B, T, 64)
        cl_enc = self.chainlink_branch(cl_feat)     # (B, T, 64)

        branch_concat = torch.cat([poly_enc, bin_enc, cl_enc], dim=-1)  # (B, T, 192)
        state_seq = self.transformer(branch_concat, time_ctx)            # (B, T, d_model)

        last_state = state_seq[:, -1, :]   # (B, d_model) — only last timestep
        logits, ev_pred = self.head(last_state)
        return logits, ev_pred

    def state_embedding(self, obs: Tensor) -> Tensor:
        """Return the last-timestep state embedding (B, d_model) without heads.

        Useful for downstream models that reuse the pretrained backbone.
        """
        obs = self.normalizer(obs)
        poly_enc = self.poly_branch(obs[:, :, 0:36])
        bin_enc = self.binance_branch(obs[:, :, 36:59])
        cl_enc = self.chainlink_branch(obs[:, :, 59:63])
        time_ctx = obs[:, :, 63:65]
        branch_concat = torch.cat([poly_enc, bin_enc, cl_enc], dim=-1)
        state_seq = self.transformer(branch_concat, time_ctx)
        return state_seq[:, -1, :]


# ---------------------------------------------------------------------------
# M4 Agent output heads
# ---------------------------------------------------------------------------

class PolicyHead(nn.Module):
    """6-action policy: Hold, OpenUp, OpenDown, Reduce, Close, Flip."""

    def __init__(self, d_model: int = 128) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_model, 32), nn.ReLU(), nn.Linear(32, 6))

    def forward(self, state: Tensor) -> Tensor:
        return self.net(state)  # (B, 6) raw logits


class SizeHead(nn.Module):
    """3-level target position: small, medium, large."""

    def __init__(self, d_model: int = 128) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_model, 32), nn.ReLU(), nn.Linear(32, 3))

    def forward(self, state: Tensor) -> Tensor:
        return self.net(state)  # (B, 3) raw logits


class OrderTypeHead(nn.Module):
    """2-class: Market vs Limit."""

    def __init__(self, d_model: int = 128) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_model, 32), nn.ReLU(), nn.Linear(32, 2))

    def forward(self, state: Tensor) -> Tensor:
        return self.net(state)  # (B, 2) raw logits


class LimitPriceLevelHead(nn.Module):
    """5-level: JoinBest, Improve1Tick, Improve2Tick, Passive1Tick, Passive2Tick."""

    def __init__(self, d_model: int = 128) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_model, 32), nn.ReLU(), nn.Linear(32, 5))

    def forward(self, state: Tensor) -> Tensor:
        return self.net(state)  # (B, 5) raw logits


class RiskHead(nn.Module):
    """Scalar risk score in [0, 1] for soft-clipping increase deltas."""

    def __init__(self, d_model: int = 128) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_model, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, state: Tensor) -> Tensor:
        return torch.sigmoid(self.net(state))  # (B, 1) in [0, 1]


# ---------------------------------------------------------------------------
# M5: StateBranch + FusionProjection (late fusion for agent state features)
# ---------------------------------------------------------------------------

class StateBranch(nn.Module):
    """Encodes 11-dim agent state features (indices 65:76) into a 64-dim vector."""

    def __init__(self, in_features: int = 11, hidden: int = 32, out_features: int = 64,
                 dropout: float = 0.1) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, out_features),
            nn.ReLU(),
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.net(x)  # (B, 64)


class FusionProjection(nn.Module):
    """Projects concatenated backbone (128) + state_branch (64) = 192 → 128."""

    def __init__(self, in_features: int = 192, out_features: int = 128) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(in_features, out_features), nn.ReLU())

    def forward(self, x: Tensor) -> Tensor:
        return self.net(x)  # (B, 128)


# ---------------------------------------------------------------------------
# PolyArbAgentModel — full agent model with pretrained backbone
# ---------------------------------------------------------------------------

class PolyArbAgentModel(nn.Module):
    """Full agent model: pretrained backbone + SignalHead + 5 new policy heads.

    The backbone (normalizer + branches + transformer) is loaded from a
    Phase 1 ``PolyArbSignalModel`` checkpoint via ``from_pretrained()``.

    M5 adds late fusion: frozen backbone(128) + StateBranch(64) → FusionProjection(192→128).
    New heads are randomly initialized and trained via RL in M5.

    Forward returns a dict of all head outputs for easy ONNX export.
    """

    # Number of market features consumed by the backbone (M3 columns 0:65)
    BACKBONE_FEATURES = 65
    # Number of agent state features (M5 columns 65:76)
    STATE_FEATURES = 11

    def __init__(
        self,
        seq_len: int = 240,
        d_model: int = 128,
        n_transformer_layers: int = 2,
        nhead: int = 4,
        dropout: float = 0.1,
        n_features: int = 76,
    ) -> None:
        super().__init__()
        self.n_features = n_features
        # Backbone (shared) — normalizes only the first 65 market features
        self.normalizer = InputNormalizer(n_features=self.BACKBONE_FEATURES)
        self.poly_branch = PolymarketBranch(dropout=dropout)
        self.binance_branch = BinanceBranch(dropout=dropout)
        self.chainlink_branch = ChainlinkBranch(dropout=dropout)
        self.transformer = TinyCausalTransformer(
            d_model=d_model,
            n_layers=n_transformer_layers,
            nhead=nhead,
            dim_feedforward=d_model * 2,
            dropout=dropout,
            max_seq_len=max(seq_len + 16, 512),
        )
        # Signal head (from Phase 1)
        self.signal_head = SignalHead(d_model=d_model)
        # M5: StateBranch + FusionProjection (late fusion)
        self.state_normalizer = InputNormalizer(n_features=self.STATE_FEATURES)
        self.state_branch = StateBranch(
            in_features=self.STATE_FEATURES, out_features=64, dropout=dropout,
        )
        self.fusion_proj = FusionProjection(in_features=d_model + 64, out_features=d_model)
        # Agent heads (M4, randomly initialized)
        self.policy_head = PolicyHead(d_model=d_model)
        self.size_head = SizeHead(d_model=d_model)
        self.order_type_head = OrderTypeHead(d_model=d_model)
        self.limit_price_level_head = LimitPriceLevelHead(d_model=d_model)
        self.risk_head = RiskHead(d_model=d_model)

    def _state_embedding(self, obs: Tensor) -> tuple[Tensor, Tensor]:
        """Compute backbone and fused state embeddings.

        obs: (B, T, 76) — first 65 cols are market features, last 11 are agent state.
        Returns: (backbone_out, fused) — both (B, d_model).

        backbone_out: pure market signal (used by policy_head and signal_head —
            direction decisions should not depend on agent session context).
        fused: backbone + agent state (used by size/order_type/limit/risk heads
            and by Q/V networks in IQL — value estimation benefits from full context).
        """
        # Backbone processes first 65 market features
        market_obs = self.normalizer(obs[:, :, :self.BACKBONE_FEATURES])
        poly_enc = self.poly_branch(market_obs[:, :, 0:36])
        bin_enc = self.binance_branch(market_obs[:, :, 36:59])
        cl_enc = self.chainlink_branch(market_obs[:, :, 59:63])
        time_ctx = market_obs[:, :, 63:65]
        branch_concat = torch.cat([poly_enc, bin_enc, cl_enc], dim=-1)
        state_seq = self.transformer(branch_concat, time_ctx)
        backbone_out = state_seq[:, -1, :]  # (B, d_model)

        # StateBranch processes last 11 agent state features (last timestep only)
        state_feat = self.state_normalizer(obs[:, -1, self.BACKBONE_FEATURES:])  # (B, 11)
        state_enc = self.state_branch(state_feat)  # (B, 64)

        # Late fusion
        fused = self.fusion_proj(torch.cat([backbone_out, state_enc], dim=-1))  # (B, d_model)
        return backbone_out, fused

    def forward(self, obs: Tensor) -> dict[str, Tensor]:
        backbone_out, fused = self._state_embedding(obs)
        # Direction decisions use pure market signal (no agent state leak)
        signal_logits, signal_ev = self.signal_head(backbone_out)
        return {
            "signal_logits": signal_logits,    # (B, 2)
            "signal_ev": signal_ev,            # (B, 2)
            "policy_logits": self.policy_head(backbone_out),         # (B, 6)
            # Execution heads use fused (need position/cash/session context)
            "size_logits": self.size_head(fused),             # (B, 3)
            "order_type_logits": self.order_type_head(fused), # (B, 2)
            "limit_price_level_logits": self.limit_price_level_head(fused),  # (B, 5)
            "risk_score": self.risk_head(fused),              # (B, 1)
        }

    @classmethod
    def from_pretrained(
        cls,
        checkpoint_path: str,
        **kwargs,
    ) -> "PolyArbAgentModel":
        """Load backbone + SignalHead weights from a Phase 1 checkpoint.

        The checkpoint is a ``PolyArbSignalModel`` state_dict saved by
        ``train.py`` (possibly with ``_orig_mod.`` prefix from torch.compile).

        New agent heads and M5 modules (state_branch, fusion_proj, state_normalizer)
        remain randomly initialized. Backbone can optionally be frozen by caller.
        """
        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        state_dict = ckpt.get("model_state_dict", ckpt)

        # Strip torch.compile prefix if present
        cleaned = {}
        for k, v in state_dict.items():
            k = k.removeprefix("_orig_mod.")
            cleaned[k] = v

        # Infer d_model from the transformer projection layer
        d_model = cleaned.get("transformer.proj.weight", torch.empty(128, 194)).shape[0]
        model = cls(d_model=d_model, **kwargs)

        # Map Phase 1 'head.' → Agent 'signal_head.'
        remapped = {}
        for k, v in cleaned.items():
            if k.startswith("head."):
                remapped["signal_" + k] = v
            else:
                remapped[k] = v

        # Load with strict=False to allow missing new head params
        missing, unexpected = model.load_state_dict(remapped, strict=False)
        # New heads + M5 fusion modules may be missing from pretrained checkpoint
        new_head_prefixes = ("policy_head.", "size_head.", "order_type_head.",
                             "limit_price_level_head.", "risk_head.",
                             "state_branch.", "fusion_proj.", "state_normalizer.")
        for key in missing:
            if not key.startswith(new_head_prefixes):
                raise RuntimeError(f"Unexpected missing key from pretrained: {key}")
        if unexpected:
            raise RuntimeError(f"Unexpected keys in pretrained checkpoint: {unexpected}")
        return model
