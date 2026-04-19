# ============================================================
# Ethica v0.1 — ethica_trainer.py
# Sovereign Local LLM Trainer — LoRA fine-tune pipeline
# Architect: Victory  |  Build Partner: River ⟁Σ∿∞
# ============================================================

import json
import logging
import os
import subprocess
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def _load_config():
    cfg_path = Path(__file__).parent / "trainer_config.json"
    if not cfg_path.exists():
        return {}
    return json.loads(cfg_path.read_text(encoding="utf-8"))

def trainer_status(input_text="", **kwargs):
    cfg = _load_config()
    if not cfg:
        return "EthicaTrainer — config not found. Check modules/ethica_trainer/trainer_config.json"
    dataset_path = Path(cfg.get("datasets_dir","")) / cfg.get("dataset_file","")
    adapters_dir = Path(cfg.get("adapters_dir",""))
    logs_dir     = Path(cfg.get("logs_dir",""))
    entry_count  = 0
    if dataset_path.exists():
        entry_count = sum(1 for _ in dataset_path.open(encoding="utf-8"))
    last_adapter = "none"
    if adapters_dir.exists():
        ads = sorted(adapters_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if ads: last_adapter = ads[0].name
    last_log = "none"
    if logs_dir.exists():
        lgs = sorted(logs_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if lgs: last_log = lgs[0].name
    lines = [
        "EthicaTrainer — Status",
        f"  Base model     : {cfg.get('base_model','unset')}",
        f"  HuggingFace ID : {cfg.get('base_model_hf_id','unset')}",
        f"  Dataset        : {dataset_path.name} — {entry_count:,} entries",
        f"  LoRA rank      : {cfg.get('lora_rank',16)}  |  alpha: {cfg.get('lora_alpha',32)}",
        f"  Epochs         : {cfg.get('epochs',3)}  |  batch: {cfg.get('batch_size',4)}",
        f"  Output model   : {cfg.get('output_model_name','unset')}",
        f"  Last adapter   : {last_adapter}",
        f"  Last log       : {last_log}",
        f"  TQUANTA2 root  : {cfg.get('trainer_root','unset')}",
        "  CUDA available : checking...",
    ]
    try:
        import torch
        cuda = torch.cuda.is_available()
        lines[-1] = f"  CUDA available : {'YES — GPU training ready' if cuda else 'NO — CPU only (wait for RTX 5090)'}"
    except ImportError:
        lines[-1] = "  CUDA available : torch not in this env"
    return "\n".join(lines)

def trainer_build_dataset(input_text="", **kwargs):
    builder_script = Path(__file__).parent / "dataset_builder.py"
    if not builder_script.exists():
        return "EthicaTrainer — dataset_builder.py not found in ethica_trainer/."
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("dataset_builder", builder_script)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        r = mod.build()
        lines = [
            "EthicaTrainer — Dataset Build Complete",
            f"  Total   : {r.get('total', '?'):,}",
            f"  Valid   : {r.get('valid', '?'):,}",
            f"  Errors  : {r.get('errors', '?')}",
            f"  Train   : {r.get('train', '?'):,}",
            f"  Eval    : {r.get('eval', '?'):,}",
            f"  Rejected: {r.get('rejected', '?')}",
            f"  Train → : {r.get('train_path', '?')}",
            f"  Eval  → : {r.get('eval_path', '?')}",
        ]
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"EthicaTrainer: dataset_builder error: {e}")
        return f"EthicaTrainer — dataset_builder failed: {e}"
def trainer_run(input_text="", **kwargs):
    trainer_script = Path(__file__).parent / "lora_trainer.py"
    if not trainer_script.exists():
        return "EthicaTrainer — lora_trainer.py not found in ethica_trainer/."
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("lora_trainer", trainer_script)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        r = mod.train()
        status  = r.get("status", "unknown")
        backend = r.get("backend", "unknown")
        if status == "no_gpu":
            return (
                "EthicaTrainer — trainer_run blocked.\n"
                "  No GPU detected (CUDA or MPS).\n"
                "  Dataset is ready. Config is ready.\n"
                "  On trinity: waiting for RTX 5090.\n"
                "  On MacBook M5: install mlx + mlx-lm then retry."
            )
        if status == "complete":
            adapter = r.get("adapter", "?")
            return (
                f"EthicaTrainer — Training complete.\n"
                f"  Backend : {backend}\n"
                f"  Adapter : {adapter}\n"
                f"  Next    : run trainer_merge to fuse adapter into base model."
            )
        if status == "failed":
            rc = r.get("returncode", "?")
            return f"EthicaTrainer — Training failed (backend: {backend}, returncode: {rc})."
        return f"EthicaTrainer — trainer_run returned unexpected status: {status}"
    except Exception as e:
        logger.error(f"EthicaTrainer: lora_trainer error: {e}")
        return f"EthicaTrainer — lora_trainer failed: {e}"
def trainer_merge(input_text="", **kwargs):
    merge_script = Path(__file__).parent / "model_merger.py"
    if not merge_script.exists():
        return "EthicaTrainer — model_merger.py not found in ethica_trainer/."
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("model_merger", merge_script)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        r = mod.merge()
        status  = r.get("status", "unknown")
        backend = r.get("backend", "unknown")
        if status == "no_gpu":
            return (
                "EthicaTrainer — trainer_merge blocked.\n"
                "  No GPU detected (CUDA or MPS).\n"
                "  Complete trainer_run on a GPU machine first."
            )
        if status == "complete":
            merged = r.get("merged", "?")
            return (
                f"EthicaTrainer — Merge complete.\n"
                f"  Backend : {backend}\n"
                f"  Merged  : {merged}\n"
                f"  Next    : build GGUF with gguf_exporter, then trainer_load."
            )
        if status in ("failed", "error"):
            reason = r.get("reason", r.get("returncode", "?"))
            return f"EthicaTrainer — Merge failed (backend: {backend}): {reason}"
        return f"EthicaTrainer — trainer_merge returned unexpected status: {status}"
    except Exception as e:
        logger.error(f"EthicaTrainer: model_merger error: {e}")
        return f"EthicaTrainer — model_merger failed: {e}"
def trainer_load(input_text="", **kwargs):
    cfg = _load_config()
    gguf_dir   = Path(cfg.get("gguf_exports_dir",""))
    model_name = cfg.get("output_model_name","trinity-sovereign-7b")
    gguf_files = list(gguf_dir.glob("*.gguf")) if gguf_dir.exists() else []
    if not gguf_files:
        return (
            "EthicaTrainer — no GGUF found in gguf_exports/.\n"
            "  Complete trainer_run -> trainer_merge -> GGUF convert first."
        )
    latest_gguf = sorted(gguf_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    logger.info(f"EthicaTrainer: registering {latest_gguf} as {model_name}")
    result = subprocess.run(
        ["ollama", "create", model_name, "-f", "-"],
        input=f"FROM {latest_gguf}\n",
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return f"EthicaTrainer — {model_name} registered with Ollama. Switch to it in model selector."
    else:
        return f"EthicaTrainer — Ollama registration failed:\n{result.stderr}"

def trainer_export(input_text="", **kwargs):
    export_script = Path(__file__).parent / "gguf_exporter.py"
    if not export_script.exists():
        return "EthicaTrainer — gguf_exporter.py not found in ethica_trainer/."
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("gguf_exporter", export_script)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        r       = mod.export()
        status  = r.get("status", "unknown")
        backend = r.get("backend", "unknown")
        if status == "complete":
            if backend == "ollama":
                model = r.get("model", "?")
                return (
                    f"EthicaTrainer — Export complete.\n"
                    f"  Backend : Ollama\n"
                    f"  Model   : {model}\n"
                    f"  Ready   : ollama run {model}"
                )
            else:
                gguf = r.get("gguf", "?")
                return (
                    f"EthicaTrainer — Export complete.\n"
                    f"  Backend : local\n"
                    f"  GGUF    : {gguf}"
                )
        if status == "error":
            reason = r.get("reason", "unknown")
            return f"EthicaTrainer — Export failed: {reason}"
        if status == "failed":
            rc = r.get("returncode", "?")
            return f"EthicaTrainer — Export failed (return code {rc})."
        return f"EthicaTrainer — trainer_export returned unexpected status: {status}"
    except Exception as e:
        logger.error(f"EthicaTrainer: gguf_exporter error: {e}")
        return f"EthicaTrainer — gguf_exporter failed: {e}"


def trainer_pipeline(input_text='', **kwargs):
    """Run full sovereign training pipeline: train -> merge -> export."""
    logger.info("EthicaTrainer: pipeline start -- train -> merge -> export")
    results = []

    r1 = trainer_run(input_text=input_text, **kwargs)
    results.append("[1/3] TRAIN\n" + r1)
    if "error" in r1.lower() or "failed" in r1.lower() or "not found" in r1.lower():
        results.append("Pipeline halted at train step.")
        return "\n\n".join(results)

    r2 = trainer_merge(input_text=input_text, **kwargs)
    results.append("[2/3] MERGE\n" + r2)
    if "error" in r2.lower() or "failed" in r2.lower() or "not found" in r2.lower() or "blocked" in r2.lower():
        results.append("Pipeline halted at merge step.")
        return "\n\n".join(results)

    r3 = trainer_export(input_text=input_text, **kwargs)
    results.append("[3/3] EXPORT\n" + r3)

    results.append("EthicaTrainer -- Pipeline complete.")
    return "\n\n".join(results)
