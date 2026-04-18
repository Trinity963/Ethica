import json
import os
import sys


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


def _train_cuda(cfg: dict) -> dict:
    """CUDA path — peft + transformers + trl + bitsandbytes"""
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, TaskType
    from trl import SFTTrainer, SFTConfig
    from datasets import load_dataset

    tquanta2    = cfg["trainer_root"]
    base_id     = cfg.get("base_model_mlx") or os.path.join(cfg["base_models_dir"], cfg["base_model"])
    train_path  = os.path.join(tquanta2, "datasets", "train.jsonl")
    eval_path   = os.path.join(tquanta2, "datasets", "eval.jsonl")
    adapter_out = os.path.join(tquanta2, "adapters", cfg["output_model_name"])
    log_dir     = os.path.join(tquanta2, "logs")

    print(f"[lora_trainer] Backend : CUDA ({torch.cuda.get_device_name(0)})")
    print(f"[lora_trainer] Base    : {base_id}")
    print(f"[lora_trainer] Train   : {train_path}")
    print(f"[lora_trainer] Output  : {adapter_out}")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(base_id, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False
    model.enable_input_require_grads()
    model.gradient_checkpointing_enable()

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=cfg["lora_rank"],
        lora_alpha=cfg["lora_alpha"],
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",   # attention
            "gate_proj", "up_proj", "down_proj",        # MLP / FFN
        ],
        lora_dropout=cfg.get("lora_dropout", 0.05),
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    dataset = load_dataset("json", data_files={"train": train_path, "eval": eval_path})

    # Use the Mistral-formatted `text` field written by dataset_builder.py.
    # Do NOT reformat here — dataset_builder owns the chat template.
    if "text" not in dataset["train"].column_names:
        raise ValueError(
            "[lora_trainer] Dataset missing 'text' field. "
            "Run trainer_build_dataset first to generate train.jsonl with correct Mistral formatting."
        )

    sft_cfg = SFTConfig(
        output_dir=adapter_out,
        num_train_epochs=cfg["epochs"],
        per_device_train_batch_size=cfg.get("batch_size", 4),
        gradient_accumulation_steps=cfg.get("gradient_accumulation_steps", 8),
        learning_rate=cfg.get("learning_rate", 5e-5),
        warmup_ratio=cfg.get("warmup_ratio", 0.03),
        lr_scheduler_type=cfg.get("lr_scheduler", "cosine"),
        fp16=True,
        logging_dir=log_dir,
        logging_steps=50,
        save_strategy="epoch",
        eval_strategy="epoch",
        dataset_text_field="text",
        max_seq_length=cfg.get("max_seq_length", 2048),
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_cfg,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"],
        tokenizer=tokenizer,
    )

    trainer.train()
    model.save_pretrained(adapter_out)
    tokenizer.save_pretrained(adapter_out)

    print(f"[lora_trainer] CUDA training complete. Adapter saved: {adapter_out}")
    return {"status": "complete", "backend": "cuda", "adapter": adapter_out}


def _train_mps(cfg: dict) -> dict:
    """MPS path — mlx-lm LoRA (Apple Silicon)"""
    import subprocess

    tquanta2    = cfg["trainer_root"]
    train_path  = os.path.join(tquanta2, "datasets", "train.jsonl")
    eval_path   = os.path.join(tquanta2, "datasets", "eval.jsonl")
    adapter_out = os.path.join(tquanta2, "adapters", cfg["output_model_name"])
    base_id     = os.path.join(cfg["base_models_dir"], cfg["base_model"])

    os.makedirs(adapter_out, exist_ok=True)

    print(f"[lora_trainer] Backend : MPS (Apple Silicon)")
    print(f"[lora_trainer] Base    : {base_id}")
    print(f"[lora_trainer] Train   : {train_path}")
    print(f"[lora_trainer] Output  : {adapter_out}")

    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model",        base_id,
        "--train",
        "--data",         os.path.join(tquanta2, "datasets"),
        "--adapter-path", adapter_out,
        "--num-layers",   str(cfg["lora_rank"]),
        "--iters",        "1000",
        "--batch-size",   "1",
        "--learning-rate","1e-4",
        "--steps-per-report","50",
        "--steps-per-eval","200",
        "--val-batches",  "5",
        "--save-every",   "100",
        "--max-seq-length","1024",
        "--grad-checkpoint",
    ]

    print(f"[lora_trainer] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        print(f"[lora_trainer] MPS training complete. Adapter saved: {adapter_out}")
        return {"status": "complete", "backend": "mps", "adapter": adapter_out}
    else:
        print(f"[lora_trainer] MPS training failed. Return code: {result.returncode}")
        return {"status": "failed", "backend": "mps", "returncode": result.returncode}


def train() -> dict:
    cfg     = _load_config()
    backend = _detect_backend()

    if backend == "none":
        msg = (
            "[lora_trainer] No GPU backend detected.\n"
            "  CUDA: RTX 5090 not yet installed on trinity.\n"
            "  MPS:  Run on MacBook Pro M5 with mlx-lm installed.\n"
            "  Install: pip install mlx mlx-lm  (Mac) or\n"
            "           pip install torch peft transformers trl bitsandbytes accelerate  (CUDA)"
        )
        print(msg)
        return {"status": "no_gpu", "backend": "none"}

    if backend == "cuda":
        return _train_cuda(cfg)

    if backend == "mps":
        return _train_mps(cfg)


if __name__ == "__main__":
    result = train()
    print(f"\n[lora_trainer] Result: {result}")
