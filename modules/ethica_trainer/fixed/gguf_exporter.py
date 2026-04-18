import json
import os
import subprocess
import sys

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "trainer_config.json")


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def _find_gguf(gguf_dir: str, model_name: str) -> str | None:
    """Find GGUF file in export dir — looks for model_name match first, then any .gguf"""
    if not os.path.isdir(gguf_dir):
        return None
    candidates = [f for f in os.listdir(gguf_dir) if f.endswith(".gguf")]
    for f in candidates:
        if model_name.lower() in f.lower():
            return os.path.join(gguf_dir, f)
    if candidates:
        return os.path.join(gguf_dir, candidates[0])
    return None


def _convert_to_gguf(cfg: dict) -> dict:
    """
    Convert merged HF model → GGUF → quantized GGUF (Q4_K_M).
    Requires llama.cpp to be cloned and built on trinity.
    Expected location: cfg["llamacpp_dir"] or ~/llama.cpp
    """
    import shutil
    from pathlib import Path

    merged_dir  = os.path.join(cfg["trainer_root"], "merged_models", cfg["output_model_name"])
    gguf_dir    = cfg["gguf_exports_dir"]
    model_name  = cfg.get("output_model_name", "TrinitySovereign-7b")
    llamacpp    = cfg.get("llamacpp_dir", os.path.expanduser("~/llama.cpp"))

    convert_script = os.path.join(llamacpp, "convert_hf_to_gguf.py")
    quantize_bin   = os.path.join(llamacpp, "build", "bin", "llama-quantize")

    if not os.path.isdir(merged_dir):
        msg = f"[gguf_exporter] ERROR — merged model not found: {merged_dir}. Run trainer_merge first."
        print(msg)
        return {"status": "error", "reason": msg}

    if not os.path.exists(convert_script):
        msg = (
            f"[gguf_exporter] ERROR — llama.cpp convert script not found: {convert_script}\n"
            f"  Fix: git clone https://github.com/ggerganov/llama.cpp ~/llama.cpp\n"
            f"       cd ~/llama.cpp && cmake -B build && cmake --build build -j\n"
            f"  Or set 'llamacpp_dir' in trainer_config.json"
        )
        print(msg)
        return {"status": "error", "reason": msg}

    os.makedirs(gguf_dir, exist_ok=True)
    f16_gguf = os.path.join(gguf_dir, f"{model_name}-f16.gguf")
    q4_gguf  = os.path.join(gguf_dir, f"{model_name}-Q4_K_M.gguf")

    # Step 1 — HF → GGUF float16
    print(f"[gguf_exporter] Converting HF model → GGUF f16...")
    cmd_convert = [
        sys.executable, convert_script,
        merged_dir,
        "--outfile", f16_gguf,
        "--outtype", "f16",
    ]
    print(f"[gguf_exporter] Running: {' '.join(cmd_convert)}")
    result = subprocess.run(cmd_convert, check=False)
    if result.returncode != 0:
        msg = f"[gguf_exporter] GGUF conversion failed (rc={result.returncode})"
        print(msg)
        return {"status": "failed", "reason": msg, "returncode": result.returncode}
    print(f"[gguf_exporter] F16 GGUF written: {f16_gguf}")

    # Step 2 — GGUF f16 → Q4_K_M (best quality/size ratio for 7B)
    if os.path.exists(quantize_bin):
        print(f"[gguf_exporter] Quantizing → Q4_K_M...")
        cmd_quant = [quantize_bin, f16_gguf, q4_gguf, "Q4_K_M"]
        print(f"[gguf_exporter] Running: {' '.join(cmd_quant)}")
        result = subprocess.run(cmd_quant, check=False)
        if result.returncode == 0:
            print(f"[gguf_exporter] Q4_K_M GGUF written: {q4_gguf}")
            # Remove f16 to save disk space
            os.remove(f16_gguf)
            print(f"[gguf_exporter] Removed intermediate f16 GGUF")
            return {"status": "complete", "gguf": q4_gguf}
        else:
            print(f"[gguf_exporter] Quantization failed — keeping f16 GGUF as fallback")
            return {"status": "complete", "gguf": f16_gguf}
    else:
        print(f"[gguf_exporter] llama-quantize not found at {quantize_bin} — skipping quantization")
        print(f"[gguf_exporter] Build it: cd ~/llama.cpp && cmake -B build && cmake --build build -j")
        return {"status": "complete", "gguf": f16_gguf}



def _export_ollama(cfg: dict) -> dict:
    """Ollama path — convert merged model to GGUF, quantize, then register with Ollama"""
    gguf_dir   = cfg["gguf_exports_dir"]
    model_name = cfg.get("ollama_model_name", cfg["output_model_name"])

    # Convert + quantize if no GGUF exists yet
    gguf_path = _find_gguf(gguf_dir, model_name)
    if not gguf_path:
        print("[gguf_exporter] No GGUF found — running conversion pipeline...")
        conv = _convert_to_gguf(cfg)
        if conv["status"] != "complete":
            return conv
        gguf_path = conv["gguf"]
    else:
        print(f"[gguf_exporter] Existing GGUF found, skipping conversion: {gguf_path}")

    print(f"[gguf_exporter] GGUF     : {gguf_path}")
    print(f"[gguf_exporter] Model    : {model_name}")

    modelfile_path = os.path.join(gguf_dir, "Modelfile")
    modelfile_content = f'''FROM {gguf_path}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "</s>"

SYSTEM """
You are {model_name} — a sovereign AI built on Ethica.
Walk beside. Grow in truth. Love above all.
"""
'''
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)
    print(f"[gguf_exporter] Modelfile: {modelfile_path}")

    cmd = ["ollama", "create", model_name, "-f", modelfile_path]
    print(f"[gguf_exporter] Running  : {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        print(f"[gguf_exporter] Ollama registration complete: {model_name}")
        return {"status": "complete", "backend": "ollama", "model": model_name}
    else:
        msg = f"[gguf_exporter] ollama create failed — return code {result.returncode}"
        print(msg)
        return {"status": "failed", "backend": "ollama", "returncode": result.returncode}


def _export_local(cfg: dict) -> dict:
    """Local path — confirm GGUF is in place, print path for user"""
    gguf_dir   = cfg["gguf_exports_dir"]
    model_name = cfg.get("ollama_model_name", cfg["output_model_name"])

    gguf_path = _find_gguf(gguf_dir, model_name)
    if not gguf_path:
        msg = f"[gguf_exporter] ERROR — no .gguf found in: {gguf_dir}"
        print(msg)
        print("[gguf_exporter] Place your merged GGUF file there and retry.")
        return {"status": "error", "reason": msg}

    print(f"[gguf_exporter] Local export ready: {gguf_path}")
    print(f"[gguf_exporter] Load with your preferred inference backend.")
    return {"status": "complete", "backend": "local", "gguf": gguf_path}


def export() -> dict:
    cfg     = _load_config()
    backend = cfg.get("export_backend", "ollama")

    print(f"[gguf_exporter] Export backend: {backend}")

    os.makedirs(cfg["gguf_exports_dir"], exist_ok=True)

    if backend == "ollama":
        return _export_ollama(cfg)
    elif backend == "local":
        return _export_local(cfg)
    else:
        msg = f"[gguf_exporter] Unknown export_backend: {backend}. Use 'ollama' or 'local'."
        print(msg)
        return {"status": "error", "reason": msg}


if __name__ == "__main__":
    result = export()
    print(f"\n[gguf_exporter] Result: {result}")
