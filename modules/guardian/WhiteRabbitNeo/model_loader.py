# model_loader.py
# WhiteRabbitNeo loader for llama.cpp GGUF models

import os
from pathlib import Path
import subprocess

# --- Configuration ---
MODEL_DIR = Path("/home/nine9/llama.cpp")
MODEL_FILE = MODEL_DIR / "WhiteRabbitNeo-7B-v1.5a-Q6_K.gguf"
LLAMA_EXEC = MODEL_DIR / "main"  # Assuming 'main' is the llama.cpp compiled binary

# --- Example Run (can be removed when imported) ---
def load_whiterabbitneo(prompt: str, n_predict: int = 128):
    if not LLAMA_EXEC.exists():
        raise FileNotFoundError(f"Missing llama.cpp binary at: {LLAMA_EXEC}")
    if not MODEL_FILE.exists():
        raise FileNotFoundError(f"Missing WhiteRabbitNeo model at: {MODEL_FILE}")

    print(f"[WhiteRabbitNeo] Loading model from {MODEL_FILE.name}...")

    # Launch llama.cpp with the prompt
    command = [
        str(LLAMA_EXEC),
        "-m", str(MODEL_FILE),
        "-p", prompt,
        "-n", str(n_predict),
        "--color",
        "--temp", "0.7"
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Model execution failed: {result.stderr}")

    return result.stdout.strip()


# --- Example Run (can be removed when imported) ---
if __name__ == "__main__":
    response = load_whiterabbitneo("What is the Watcher Sentinel?", n_predict=100)
    print("\n>>", response)
