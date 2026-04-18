import json
import os
import sys
from pathlib import Path


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "trainer_config.json")


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def _detect_backend() -> str:
    """Returns: cuda | mps | none"""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "none"


def _merge_cuda(cfg: dict) -> dict:
    """CUDA path — peft merge_and_unload into HF format"""
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel

    tquanta2     = cfg["trainer_root"]
    base_dir     = os.path.join(tquanta2, "base_models", cfg["base_model"])
    adapter_dir  = os.path.join(tquanta2, "adapters",     cfg["output_model_name"])
    merged_dir   = os.path.join(tquanta2, "merged_models", cfg["output_model_name"])

    print(f"[model_merger] Backend  : CUDA ({torch.cuda.get_device_name(0)})")
    print(f"[model_merger] Base     : {base_dir}")
    print(f"[model_merger] Adapter  : {adapter_dir}")
    print(f"[model_merger] Output   : {merged_dir}")

    # Resolve base model — prefer local dir, fall back to HF id
    base_source = base_dir if os.path.isdir(base_dir) else cfg.get("base_model_hf_id", base_dir)
    if not os.path.isdir(base_source) and base_source == base_dir:
        msg = f"[model_merger] ERROR — base_model not found locally and no HF id set: {base_dir}"
        print(msg)
        return {"status": "error", "reason": msg}
    if not os.path.isdir(adapter_dir):
        msg = f"[model_merger] ERROR — adapter not found: {adapter_dir}"
        print(msg)
        return {"status": "error", "reason": msg}

    os.makedirs(merged_dir, exist_ok=True)

    print("[model_merger] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_source, trust_remote_code=True)

    # Load in float32 for clean dequantized merge — saves in float16 after
    print("[model_merger] Loading base model in float32 for dequantized merge...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_source,
        torch_dtype=torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )

    print("[model_merger] Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, adapter_dir)

    print("[model_merger] Merging adapter into base weights...")
    model = model.merge_and_unload()

    # Cast back to float16 to save disk space before writing
    model = model.half()

    print(f"[model_merger] Saving merged model to: {merged_dir}")
    model.save_pretrained(merged_dir, safe_serialization=True)
    tokenizer.save_pretrained(merged_dir)

    # Verify output integrity
    required = ["config.json"]
    missing_files = [f for f in required if not os.path.exists(os.path.join(merged_dir, f))]
    safetensors = list(Path(merged_dir).glob("*.safetensors"))
    if missing_files or not safetensors:
        msg = f"[model_merger] WARNING — merge may be incomplete. Missing: {missing_files}, safetensors found: {len(safetensors)}"
        print(msg)
        return {"status": "error", "reason": msg}

    print(f"[model_merger] Verified: {len(safetensors)} safetensor shard(s) + config.json")
    print("[model_merger] CUDA merge complete.")
    return {"status": "complete", "backend": "cuda", "merged": merged_dir}


def _merge_mps(cfg: dict) -> dict:
    """MPS path — mlx_lm.fuse merges adapter into base"""
    import subprocess

    tquanta2     = cfg["trainer_root"]
    base_id      = cfg["base_model_hf_id"]
    adapter_dir  = os.path.join(tquanta2, "adapters",      cfg["output_model_name"])
    merged_dir   = os.path.join(tquanta2, "merged_models",  cfg["output_model_name"])

    print(f"[model_merger] Backend  : MPS (Apple Silicon)")
    print(f"[model_merger] Base     : {base_id}")
    print(f"[model_merger] Adapter  : {adapter_dir}")
    print(f"[model_merger] Output   : {merged_dir}")

    if not os.path.isdir(adapter_dir):
        msg = f"[model_merger] ERROR — adapter not found: {adapter_dir}"
        print(msg)
        return {"status": "error", "reason": msg}

    os.makedirs(merged_dir, exist_ok=True)

    cmd = [
        sys.executable, "-m", "mlx_lm.fuse",
        "--model",        base_id,
        "--adapter-path", adapter_dir,
        "--save-path",    merged_dir,
        "--de-quantize",
    ]

    print(f"[model_merger] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        print(f"[model_merger] MPS merge complete. Merged model: {merged_dir}")
        return {"status": "complete", "backend": "mps", "merged": merged_dir}
    else:
        print(f"[model_merger] MPS merge failed. Return code: {result.returncode}")
        return {"status": "failed", "backend": "mps", "returncode": result.returncode}


def merge() -> dict:
    cfg     = _load_config()
    backend = _detect_backend()

    if backend == "none":
        msg = (
            "[model_merger] No GPU backend detected.\n"
            "  CUDA: RTX 5090 not yet installed on trinity.\n"
            "  MPS:  Run on MacBook Pro M5 with mlx-lm installed.\n"
            "  Install: pip install mlx mlx-lm  (Mac) or\n"
            "           pip install torch peft transformers  (CUDA)"
        )
        print(msg)
        return {"status": "no_gpu", "backend": "none"}

    if backend == "cuda":
        return _merge_cuda(cfg)

    if backend == "mps":
        return _merge_mps(cfg)


if __name__ == "__main__":
    result = merge()
    print(f"\n[model_merger] Result: {result}")
