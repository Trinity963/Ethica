# ============================================================
# Ethica v0.1 — llama_connector.py
# Local GGUF Connector via llama-cpp-python
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Direct Python access to every GGUF on disk.
# No Ollama. No subprocess. No network.
# Pure sovereign local inference.
#
# Supports any GGUF — DeepSeek, Mistral, Phi, WhiteRabbitNeo,
# CodeLLaMA, Gemma — whatever lives on the drive.
# ============================================================

import logging
import os
import threading

logger = logging.getLogger(__name__)


# ── Known Models ──────────────────────────────────────────────
# Map friendly names to GGUF paths
# Edit this to match your drive layout

KNOWN_MODELS = {
    "deepseek-7b":      "/srv/LLMs/models/DeepSeek-R1-Distill-Qwen-7B-GGUF/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
    "deepseek-7b-q3":   "/srv/LLMs/models/DeepSeek-R1-Distill-Qwen-7B-GGUF/DeepSeek-R1-Distill-Qwen-7B-Q3_K_L.gguf",
    "deepseek-7b-q5":   "/srv/LLMs/models/DeepSeek-R1-Distill-Qwen-7B-GGUF/DeepSeek-R1-Distill-Qwen-7B-Q5_K_L.gguf",
    "whiterabbit":      "/srv/LLMs/models/.ollama/WhiteRabbitNeo-2.5-Q4_K_M/WhiteRabbitNeo-2.5-Qwen-2.5-Coder-7B-Q4_K_M.gguf",
}

# Default model
DEFAULT_MODEL = "deepseek-7b"

# Context window — larger = more memory but richer context
CONTEXT_SIZE = 4096

# GPU layers — 0 = CPU only, increase if you have VRAM
GPU_LAYERS = 0


class LlamaConnector:
    """
    Ethica Local GGUF Connector.
    Uses llama-cpp-python to run any GGUF model directly.

    Drop-in replacement for OllamaConnector —
    same interface, same callbacks, sovereign local inference.
    """

    def __init__(self, model_name=DEFAULT_MODEL):
        self._model_name = model_name
        self._model_path = KNOWN_MODELS.get(model_name, model_name)
        self._llm = None
        self._inference_lock = threading.Lock()
        self._lock = threading.Lock()
        self._loading = False

    # ── Connection ────────────────────────────────────────────

    def check_connection(self):
        """
        Check if model file exists and is loadable.
        Returns (bool, info_string)
        """
        if not os.path.exists(self._model_path):
            return False, f"Model not found: {self._model_path}"
        size_gb = os.path.getsize(self._model_path) / (1024**3)
        return True, [f"{self._model_name} ({size_gb:.1f}GB)"]

    def list_models(self):
        """Return list of available model names that exist on disk."""
        available = []
        for name, path in KNOWN_MODELS.items():
            if os.path.exists(path):
                available.append(name)
        return available

    def set_model(self, model_name):
        """
        Switch active model.
        Unloads current model from memory — new model loads on next chat.
        """
        if model_name != self._model_name:
            self._model_name = model_name
            self._model_path = KNOWN_MODELS.get(model_name, model_name)
            # Unload current model
            with self._lock:
                self._llm = None

    # ── Model Loading ─────────────────────────────────────────

    def _ensure_loaded(self):
        """
        Load the model into memory if not already loaded.
        Thread-safe — only loads once.
        """
        if self._llm is not None:
            return

        with self._lock:
            if self._llm is not None:
                return

            if not os.path.exists(self._model_path):
                raise FileNotFoundError(
                    f"Model not found: {self._model_path}\n"
                    f"Check KNOWN_MODELS in llama_connector.py"
                )

            try:
                from llama_cpp import Llama
                logger.info("[LlamaConnector] Loading %s...", self._model_name)
                self._llm = Llama(
                    model_path=self._model_path,
                    n_ctx=CONTEXT_SIZE,
                    n_gpu_layers=GPU_LAYERS,
                    verbose=False,
                    n_threads=os.cpu_count(),
                )
                logger.info("[LlamaConnector] %s ready", self._model_name)
            except Exception as e:
                raise RuntimeError(f"Failed to load model: {e}")

    # ── Chat ──────────────────────────────────────────────────

    def chat(self, messages, stream=False):
        self._ensure_loaded()
        if stream:
            return self._chat_stream(messages)
        else:
            return self._chat_complete(messages)

    def _chat_complete(self, messages):
        """Non-streaming — returns full response string."""
        response = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=2048,
            temperature=0.7,
            stop=["<|im_end|>", "<|eot_id|>", "</s>"],
        )
        return response["choices"][0]["message"]["content"]

    def _chat_stream(self, messages):
        """
        Streaming — yields tokens as they generate.
        Same interface as OllamaConnector._chat_stream()
        """
        with self._inference_lock:
            stream = self._llm.create_chat_completion(
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
                stop=["<|im_end|>", "<|eot_id|>", "</s>"],
                stream=True,
            )
            for chunk in stream:
                delta = chunk["choices"][0].get("delta", {})
                token = delta.get("content", "")
                if token:
                    yield token

    # ── Generate (single prompt) ──────────────────────────────

    def generate(self, prompt, stream=False):
        """Simple single-prompt generation — no conversation history."""
        self._ensure_loaded()
        response = self._llm(
            prompt,
            max_tokens=2048,
            temperature=0.7,
            stream=stream,
        )
        if stream:
            for chunk in response:
                token = chunk["choices"][0].get("text", "")
                if token:
                    yield token
        else:
            return response["choices"][0]["text"]


# ── Model Scanner ─────────────────────────────────────────────

def scan_models(base_dirs=None):
    """
    Scan directories for GGUF files.
    Returns list of (name, path) tuples.
    Useful for populating the model selector in the sidebar.
    """
    if base_dirs is None:
        base_dirs = ["/srv/LLMs/models"]

    found = []
    for base in base_dirs:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            for f in files:
                if f.endswith(".gguf"):
                    path = os.path.join(root, f)
                    # Friendly name — folder/filename without extension
                    folder = os.path.basename(root)
                    name = f.replace(".gguf", "")
                    short = f"{folder}/{name}" if folder != "models" else name
                    found.append((short, path))
    return found
