import math

import torch
import torch.nn as nn


class RetrievalAdapter(nn.Module):
    def __init__(
        self,
        feat_channels: int,
        ref_channels: int,
        n_slots: int = 5,
        slot_vocab: int = 37,
        role_vocab: int = 3,
        struct_vocab: int = 12,
        embed_dim: int = 64,
        n_heads: int = 4,
    ):
        super().__init__()
        if feat_channels % n_heads != 0:
            raise ValueError(
                f"feat_channels ({feat_channels}) must be divisible by n_heads ({n_heads})."
            )

        self.feat_channels = feat_channels
        self.ref_channels = ref_channels
        self.n_slots = n_slots
        self.n_heads = n_heads
        self.head_dim = feat_channels // n_heads
        self.scale = self.head_dim ** -0.5

        self.q_norm = nn.LayerNorm(feat_channels)
        self.kv_norm = nn.LayerNorm(feat_channels)

        self.q_proj = nn.Linear(feat_channels, feat_channels)
        self.k_proj = nn.Linear(feat_channels, feat_channels)
        self.v_proj = nn.Linear(feat_channels, feat_channels)
        self.ref_in_proj = nn.Linear(ref_channels, feat_channels)

        self.slot_embed = nn.Embedding(slot_vocab, embed_dim)
        self.role_embed = nn.Embedding(role_vocab, embed_dim)
        self.struct_embed = nn.Embedding(struct_vocab, embed_dim)
        self.meta_proj = nn.Linear(embed_dim, feat_channels)

        # Dropout defaults to 0.0 and can be reconfigured by changing this module's p.
        self.attn_dropout = nn.Dropout(p=0.0)

        self.out_proj = nn.Linear(feat_channels, feat_channels)
        # [ADAPTER] non-zero out_proj weight + α=0 保 bit-exact 同时避免 double-zero gradient trap
        nn.init.normal_(self.out_proj.weight, mean=0.0, std=0.02)
        nn.init.zeros_(self.out_proj.bias)

        self.alpha = nn.Parameter(torch.tensor(0.0))

    def _reshape_heads(self, x: torch.Tensor) -> torch.Tensor:
        bsz, seq_len, channels = x.shape
        x = x.view(bsz, seq_len, self.n_heads, self.head_dim)
        return x.transpose(1, 2)

    def forward(
        self,
        h_q,
        refs,
        slot_ids,
        role_ids,
        target_struct,
        mask,
        return_gate=False,
    ):
        if h_q.dim() != 4:
            raise ValueError(f"h_q must be [B, C, H, W], got shape {tuple(h_q.shape)}")
        if refs.dim() != 5:
            raise ValueError(
                f"refs must be [B, N_slots, C_ref, H_ref, W_ref], got shape {tuple(refs.shape)}"
            )
        if slot_ids.dim() != 2 or role_ids.dim() != 2 or mask.dim() != 2:
            raise ValueError("slot_ids, role_ids, and mask must all be [B, N_slots].")
        if target_struct.dim() != 1:
            raise ValueError(f"target_struct must be [B], got shape {tuple(target_struct.shape)}")

        bsz, channels, height, width = h_q.shape
        b_ref, n_slots, c_ref, h_ref, w_ref = refs.shape
        if b_ref != bsz:
            raise ValueError("Batch size mismatch between h_q and refs.")
        if channels != self.feat_channels:
            raise ValueError(
                f"h_q channel mismatch: expected {self.feat_channels}, got {channels}"
            )
        if c_ref != self.ref_channels:
            raise ValueError(
                f"refs channel mismatch: expected {self.ref_channels}, got {c_ref}"
            )
        if n_slots != self.n_slots:
            raise ValueError(f"refs n_slots mismatch: expected {self.n_slots}, got {n_slots}")

        h_tokens = h_q.flatten(2).transpose(1, 2)
        q = self.q_proj(self.q_norm(h_tokens))

        ref_tokens = refs.permute(0, 1, 3, 4, 2).reshape(bsz, n_slots, h_ref * w_ref, c_ref)
        ref_tokens = self.ref_in_proj(ref_tokens)

        slot_bias = self.slot_embed(slot_ids)
        role_bias = self.role_embed(role_ids)
        struct_bias = self.struct_embed(target_struct).unsqueeze(1).expand(-1, n_slots, -1)
        meta_bias = self.meta_proj(slot_bias + role_bias + struct_bias).unsqueeze(2)
        ref_tokens = ref_tokens + meta_bias

        kv_tokens = ref_tokens.reshape(bsz, n_slots * h_ref * w_ref, self.feat_channels)
        kv_tokens = self.kv_norm(kv_tokens)
        k = self.k_proj(kv_tokens)
        v = self.v_proj(kv_tokens)

        qh = self._reshape_heads(q)
        kh = self._reshape_heads(k)
        vh = self._reshape_heads(v)

        logits = torch.matmul(qh, kh.transpose(-1, -2)) * self.scale

        assert mask.any(dim=1).all(), (
            "RetrievalAdapter requires at least one valid slot per batch item; "
            "retrieve.py anchor fallback should guarantee this invariant."
        )
        token_mask = (
            mask.to(torch.bool)
            .unsqueeze(-1)
            .expand(-1, -1, h_ref * w_ref)
            .reshape(bsz, n_slots * h_ref * w_ref)
        )
        logits = logits.masked_fill(~token_mask[:, None, None, :], -1e4)

        attn = torch.softmax(logits, dim=-1)
        attn = self.attn_dropout(attn)

        attn_out = torch.matmul(attn, vh)
        attn_out = attn_out.transpose(1, 2).contiguous().view(
            bsz, height * width, self.feat_channels
        )

        pregate = self.out_proj(attn_out)
        pregate_norm = pregate.norm(dim=-1).mean()
        delta_tokens = self.alpha * pregate
        delta_h = delta_tokens.transpose(1, 2).reshape(bsz, self.feat_channels, height, width)

        if return_gate:
            return delta_h, {"alpha": self.alpha, "pregate_norm": pregate_norm}
        return delta_h


if __name__ == "__main__":
    torch.manual_seed(0)

    B, C, H, W = 2, 1024, 3, 3
    C_ref, H_ref, W_ref = 1024, 3, 3
    N_slots = 5

    model = RetrievalAdapter(
        feat_channels=C,
        ref_channels=C_ref,
        n_slots=N_slots,
    )

    h_q = torch.randn(B, C, H, W, requires_grad=True)
    refs = torch.randn(B, N_slots, C_ref, H_ref, W_ref)
    slot_ids = torch.randint(0, 37, (B, N_slots), dtype=torch.long)
    role_ids = torch.randint(0, 3, (B, N_slots), dtype=torch.long)
    target_struct = torch.randint(0, 12, (B,), dtype=torch.long)
    mask = torch.randint(0, 2, (B, N_slots), dtype=torch.bool)

    # Ensure each sample has at least one valid slot for a representative attention path.
    for i in range(B):
        if not mask[i].any():
            mask[i, 0] = True

    delta_h = model(h_q, refs, slot_ids, role_ids, target_struct, mask)
    shape_ok = delta_h.shape == h_q.shape
    zero_ok = torch.allclose(delta_h, torch.zeros_like(delta_h))

    loss = delta_h.sum()
    loss.backward()
    backward_ok = h_q.grad is not None

    delta_h_gate, gate_info = model(
        h_q, refs, slot_ids, role_ids, target_struct, mask, return_gate=True
    )
    gate_ok = (
        isinstance(gate_info, dict)
        and "alpha" in gate_info
        and "pregate_norm" in gate_info
        and gate_info["alpha"].ndim == 0
        and gate_info["pregate_norm"].ndim == 0
    )

    num_params = sum(p.numel() for p in model.parameters())

    print(f"num_params: {num_params}")
    print(f"shape_check: {shape_ok}")
    print(f"zero_output_check: {zero_ok}")
    print(f"backward_check: {backward_ok}")
    print(f"return_gate_check: {gate_ok}")
    print(f"delta_h_gate_shape_check: {delta_h_gate.shape == h_q.shape}")

    all_masked = torch.zeros(B, N_slots, dtype=torch.bool)
    all_masked_assert_ok = False
    try:
        _ = model(h_q, refs, slot_ids, role_ids, target_struct, all_masked)
    except AssertionError:
        all_masked_assert_ok = True
    print(f"all_masked_assert_check: {all_masked_assert_ok}")

    partial_mask = torch.tensor(
        [[True, True, False, False, False], [True, False, False, False, False]],
        dtype=torch.bool,
    )
    delta_h_partial = model(h_q, refs, slot_ids, role_ids, target_struct, partial_mask)
    partial_mask_zero_ok = torch.allclose(delta_h_partial, torch.zeros_like(delta_h_partial))
    print(f"partial_mask_zero_output_check: {partial_mask_zero_ok}")
