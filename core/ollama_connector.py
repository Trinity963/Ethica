# ============================================================
# Ethica v0.1 — ollama_connector.py
# Ollama Backend Connector
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import requests
import json


class OllamaConnector:
    """
    Ethica Ollama Connector.
    Handles all communication with the Ollama backend.
    - Connection health check
    - Model listing
    - Chat completion (streaming + non-streaming)
    - Model switching
    - Works with local AND Ollama cloud models
    - No hardcoded paths — host is fully configurable
    """

    def __init__(self, host="http://localhost:11434", model="mistral"):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = 300   # seconds — generous for deep thoughtful responses

    # ── Connection ────────────────────────────────────────────

    def check_connection(self):
        """
        Check if Ollama is reachable and model is available.
        Returns (bool, info_string)
        """
        try:
            response = requests.get(
                f"{self.host}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return True, models
            return False, "Ollama responded but returned an error"
        except requests.exceptions.ConnectionError:
            return False, "Cannot reach Ollama — is it running?"
        except requests.exceptions.Timeout:
            return False, "Ollama connection timed out"
        except Exception as e:
            return False, str(e)

    def list_models(self):
        """
        Return list of available model names from Ollama.
        Returns [] if unreachable.
        """
        ok, result = self.check_connection()
        if ok and isinstance(result, list):
            return result
        return []

    def set_model(self, model_name):
        """Switch active model."""
        self.model = model_name.strip()

    def set_host(self, host):
        """Switch Ollama host — supports cloud endpoints."""
        self.host = host.rstrip("/")

    # ── Chat ──────────────────────────────────────────────────

    def chat(self, messages, stream=False):
        """
        Send a chat request to Ollama.
        messages: list of {"role": "user"|"assistant"|"system", "content": "..."}
        stream: if True, returns a generator of response chunks
        Returns full response string (non-streaming) or generator (streaming)
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "num_predict": 2048,
                "temperature": 0.7
            }
        }

        try:
            if stream:
                return self._chat_stream(payload)
            else:
                return self._chat_complete(payload)

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Ollama is not running. Start Ollama and try again."
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(
                "Ollama took too long to respond. "
                "Try a smaller model or check your system."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama error: {str(e)}")

    def _chat_complete(self, payload):
        """Non-streaming chat — returns full response string."""
        payload["stream"] = False

        response = requests.post(
            f"{self.host}/api/chat",
            json=payload,
            timeout=self.timeout
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("message", {}).get("content", "")
        else:
            raise RuntimeError(
                f"Ollama returned status {response.status_code}: "
                f"{response.text[:200]}"
            )

    def _chat_stream(self, payload):
        """
        Streaming chat — yields response chunks as they arrive.
        Each chunk is a string token.
        """
        payload["stream"] = True

        with requests.post(
            f"{self.host}/api/chat",
            json=payload,
            stream=True,
            timeout=self.timeout
        ) as response:

            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama returned status {response.status_code}"
                )

            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

    # ── Generate (single prompt, no history) ─────────────────

    def generate(self, prompt, stream=False):
        """
        Simple single-prompt generation — no conversation history.
        Useful for one-shot tasks.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }

        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                raise RuntimeError(
                    f"Ollama generate error: {response.status_code}"
                )

        except requests.exceptions.ConnectionError:
            raise ConnectionError("Ollama is not running.")
        except Exception as e:
            raise RuntimeError(str(e))
