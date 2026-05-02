import random
import sys
import types
import importlib
import importlib.util
from pathlib import Path

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from configs.fontdiffuser import get_parser


def make_default_args():
    parser = get_parser()
    return parser.parse_args([])


def load_build_unet_without_src_init():
    src_pkg = types.ModuleType("src")
    src_pkg.__path__ = [str(PROJECT_ROOT / "src")]
    sys.modules["src"] = src_pkg

    modules_pkg = types.ModuleType("src.modules")
    modules_pkg.__path__ = [str(PROJECT_ROOT / "src" / "modules")]
    sys.modules["src.modules"] = modules_pkg

    unet_mod = importlib.import_module("src.modules.unet")
    content_mod = importlib.import_module("src.modules.content_encoder")
    style_mod = importlib.import_module("src.modules.style_encoder")

    src_pkg.UNet = unet_mod.UNet
    src_pkg.ContentEncoder = content_mod.ContentEncoder
    src_pkg.StyleEncoder = style_mod.StyleEncoder
    src_pkg.SCR = object

    build_path = PROJECT_ROOT / "src" / "build.py"
    spec = importlib.util.spec_from_file_location("fontdiffuser_build", build_path)
    build_mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(build_mod)
    return build_mod.build_unet


def load_retrieval_adapter_class():
    adapter_path = PROJECT_ROOT / "src" / "modules" / "retrieval_adapter.py"
    spec = importlib.util.spec_from_file_location("retrieval_adapter_module", adapter_path)
    adapter_mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(adapter_mod)
    return adapter_mod.RetrievalAdapter


def make_dummy_encoder_hidden_states(batch_size: int, device: torch.device):
    style_img_feature = torch.randn(batch_size, 1024, 3, 3, device=device)
    style_hidden_states = style_img_feature.permute(0, 2, 3, 1).reshape(batch_size, 9, 1024)

    content_residual_features = [
        torch.randn(batch_size, 3, 96, 96, device=device),
        torch.randn(batch_size, 64, 48, 48, device=device),
        torch.randn(batch_size, 128, 24, 24, device=device),
        torch.randn(batch_size, 256, 12, 12, device=device),
        torch.randn(batch_size, 512, 6, 6, device=device),
    ]

    style_content_res_features = [
        torch.randn(batch_size, 3, 96, 96, device=device),
        torch.randn(batch_size, 64, 48, 48, device=device),
        torch.randn(batch_size, 128, 24, 24, device=device),
        torch.randn(batch_size, 256, 12, 12, device=device),
        torch.randn(batch_size, 512, 6, 6, device=device),
    ]

    return [
        style_img_feature,
        content_residual_features,
        style_hidden_states,
        style_content_res_features,
    ]


def make_retrieval_inputs(batch_size: int, n_slots: int, device: torch.device):
    refs = torch.randn(batch_size, n_slots, 64, 48, 48, device=device)
    slot_ids = torch.randint(0, 37, (batch_size, n_slots), dtype=torch.long, device=device)
    role_ids = torch.randint(0, 3, (batch_size, n_slots), dtype=torch.long, device=device)
    target_struct = torch.randint(0, 12, (batch_size,), dtype=torch.long, device=device)
    mask = torch.randint(0, 2, (batch_size, n_slots), dtype=torch.bool, device=device)
    for b in range(batch_size):
        if not mask[b].any():
            mask[b, 0] = True

    return {
        "refs": refs,
        "slot_ids": slot_ids,
        "role_ids": role_ids,
        "target_struct": target_struct,
        "mask": mask,
    }


def main():
    torch.manual_seed(1234)
    random.seed(1234)

    device = torch.device("cpu")
    batch_size = 2
    n_slots = 5

    args = make_default_args()
    if hasattr(args, "device"):
        args.device = "cpu"
    build_unet = load_build_unet_without_src_init()
    unet = build_unet(args)
    unet.to(device)
    unet.eval()

    RetrievalAdapter = load_retrieval_adapter_class()
    adapter = RetrievalAdapter(
        feat_channels=64,
        ref_channels=64,
        n_slots=n_slots,
    )
    adapter.to(device)
    adapter.eval()

    noisy_hidden_states = torch.randn(batch_size, 3, 96, 96, device=device)
    timesteps = torch.randint(0, 1000, (batch_size,), dtype=torch.long, device=device)
    encoder_hidden_states = make_dummy_encoder_hidden_states(batch_size=batch_size, device=device)
    retrieval_inputs = make_retrieval_inputs(batch_size=batch_size, n_slots=n_slots, device=device)

    bit_exact_noise = False
    bit_exact_offset = False
    bit_exact_check = False
    max_abs_diff_noise = None
    max_abs_diff_offset = None
    max_abs_diff = None

    with torch.no_grad():
        out_baseline = unet(
            sample=noisy_hidden_states,
            timestep=timesteps,
            encoder_hidden_states=encoder_hidden_states,
            content_encoder_downsample_size=args.content_encoder_downsample_size,
        )
        unet.up_blocks[2].retrieval_adapter = adapter
        out_with_adapter = unet(
            sample=noisy_hidden_states,
            timestep=timesteps,
            encoder_hidden_states=encoder_hidden_states,
            content_encoder_downsample_size=args.content_encoder_downsample_size,
            retrieval_inputs=retrieval_inputs,
        )

    bit_exact_noise = torch.equal(out_baseline[0], out_with_adapter[0])
    bit_exact_offset = torch.equal(out_baseline[1], out_with_adapter[1])
    bit_exact_check = bit_exact_noise and bit_exact_offset
    if not bit_exact_noise:
        max_abs_diff_noise = (out_baseline[0] - out_with_adapter[0]).abs().max().item()
    if not bit_exact_offset:
        max_abs_diff_offset = (out_baseline[1] - out_with_adapter[1]).abs().max().item()
    if not bit_exact_check:
        diffs = []
        if max_abs_diff_noise is not None:
            diffs.append(max_abs_diff_noise)
        if max_abs_diff_offset is not None:
            diffs.append(max_abs_diff_offset)
        max_abs_diff = max(diffs) if diffs else 0.0

    unet.zero_grad(set_to_none=True)
    out_train = unet(
        sample=noisy_hidden_states,
        timestep=timesteps,
        encoder_hidden_states=encoder_hidden_states,
        content_encoder_downsample_size=args.content_encoder_downsample_size,
        retrieval_inputs=retrieval_inputs,
    )
    loss = out_train[0].sum() + out_train[1]
    loss.backward()

    grad_nonzero = False
    for name, param in adapter.named_parameters():
        if param.grad is None:
            grad_norm = 0.0
        else:
            grad_norm = param.grad.norm().item()
        print(f"adapter_grad_norm[{name}]: {grad_norm}")
        if (not name.startswith("out_proj")) and grad_norm > 0.0:
            grad_nonzero = True

    for p in unet.parameters():
        p.requires_grad_(False)
    for p in unet.up_blocks[2].retrieval_adapter.parameters():
        p.requires_grad_(True)

    trainable_params = sum(p.numel() for p in unet.parameters() if p.requires_grad)
    adapter_params = sum(p.numel() for p in unet.up_blocks[2].retrieval_adapter.parameters())
    freeze_check = trainable_params == adapter_params

    print(f"device: {device}")
    print(f"bit_exact_check: {bit_exact_check}")
    if not bit_exact_check:
        print(f"bit_exact_noise: {bit_exact_noise}")
        print(f"bit_exact_offset: {bit_exact_offset}")
        print(f"max_abs_diff_noise: {max_abs_diff_noise}")
        print(f"max_abs_diff_offset: {max_abs_diff_offset}")
        print(f"max_abs_diff: {max_abs_diff}")
        raise AssertionError("bit_exact_check failed (see max_abs_diff_* above)")
    print(f"adapter_grad_nonzero_check: {grad_nonzero}")
    if not grad_nonzero:
        print("adapter_grad_norms_all (for grad check failure):")
        for name, param in adapter.named_parameters():
            gn = 0.0 if param.grad is None else param.grad.norm().item()
            print(f"  {name}: {gn}")
        raise AssertionError("adapter_grad_nonzero_check failed (all adapter grads zero or out_proj-only)")
    print(f"trainable_params: {trainable_params}")
    print(f"adapter_params: {adapter_params}")
    print(f"freeze_check: {freeze_check}")


if __name__ == "__main__":
    main()
