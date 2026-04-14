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


def _export_ollama(cfg: dict) -> dict:
    """Ollama path — generate Modelfile and run ollama create"""
    gguf_dir   = cfg["gguf_exports_dir"]
    model_name = cfg.get("ollama_model_name", cfg["output_model_name"])

    gguf_path = _find_gguf(gguf_dir, model_name)
    if not gguf_path:
        msg = f"[gguf_exporter] ERROR — no .gguf found in: {gguf_dir}"
        print(msg)
        print("[gguf_exporter] Place your merged GGUF file there and retry.")
        return {"status": "error", "reason": msg}

    print(f"[gguf_exporter] GGUF     : {gguf_path}")
    print(f"[gguf_exporter] Model    : {model_name}")

    modelfile_path = os.path.join(gguf_dir, "Modelfile")
    modelfile_content = f'''FROM {gguf_path}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"

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
