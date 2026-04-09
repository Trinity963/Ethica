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
    cfg = _load_config()
    dataset_path = Path(cfg.get("datasets_dir","")) / cfg.get("dataset_file","")
    if not dataset_path.exists():
        return f"EthicaTrainer — dataset not found at {dataset_path}"
    entries = []
    errors  = 0
    with dataset_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                errors += 1
    sample_first = entries[0]  if entries else {}
    sample_last  = entries[-1] if entries else {}
    lines = [
        "EthicaTrainer — Dataset Validation",
        f"  File        : {dataset_path.name}",
        f"  Total pairs : {len(entries):,}",
        f"  Parse errors: {errors}",
        "",
        "  First entry:",
        f"    system    : {sample_first.get('system','')[:80]}",
        f"    prompt    : {sample_first.get('prompt','')[:80]}",
        f"    completion: {sample_first.get('completion','')[:80]}",
        "",
        "  Last entry:",
        f"    prompt    : {sample_last.get('prompt','')[:80]}",
        f"    completion: {sample_last.get('completion','')[:80]}",
        "",
        "  Dataset valid — ready for trainer_run when RTX 5090 installed." if errors == 0
        else f"  WARNING — {errors} malformed lines. Repair before training.",
    ]
    return "\n".join(lines)

def trainer_run(input_text="", **kwargs):
    cfg = _load_config()
    try:
        import torch
        if not torch.cuda.is_available():
            return (
                "EthicaTrainer — trainer_run blocked.\n"
                "  CUDA not available — RTX 5090 required for training.\n"
                "  Dataset is ready. Config is ready. Waiting on hardware.\n"
                "  When GPU arrives: run trainer_run again."
            )
    except ImportError:
        return "EthicaTrainer — torch not available in this environment."
    base_model_dir = Path(cfg.get("base_models_dir","")) / cfg.get("base_model","")
    if not base_model_dir.exists():
        return (
            f"EthicaTrainer — base model weights not found at {base_model_dir}\n"
            f"  Download: huggingface-cli download {cfg.get('base_model_hf_id')} --local-dir {base_model_dir}"
        )
    trainer_script = Path(__file__).parent / "lora_trainer.py"
    if not trainer_script.exists():
        return "EthicaTrainer — lora_trainer.py not yet built. Session 073 target."
    log_file = Path(cfg.get("logs_dir","")) / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger.info(f"EthicaTrainer: launching training run -> {log_file}")
    subprocess.Popen(
        ["python3", str(trainer_script), "--config", str(Path(__file__).parent / "trainer_config.json")],
        stdout=open(log_file, "w"),
        stderr=subprocess.STDOUT
    )
    return (
        f"EthicaTrainer — Training launched.\n"
        f"  Log: {log_file}\n"
        f"  Monitor: tail -f {log_file}\n"
        f"  Ethica stays live while training runs in background."
    )

def trainer_merge(input_text="", **kwargs):
    cfg = _load_config()
    adapters_dir = Path(cfg.get("adapters_dir",""))
    if not adapters_dir.exists() or not any(adapters_dir.iterdir()):
        return "EthicaTrainer — no trained adapter found. Run trainer_run first."
    merge_script = Path(__file__).parent / "model_merger.py"
    if not merge_script.exists():
        return "EthicaTrainer — model_merger.py not yet built. Session 073 target."
    return "EthicaTrainer — trainer_merge: ready. Run after training completes."

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
