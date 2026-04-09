#!/usr/bin/env python3
"""
ethica_voice_server.py — Persistent XTTS voice server
Loads model once at startup. Accepts text via Unix socket.
Runs inside gage_env.
Socket: /tmp/ethica_voice.sock
Protocol: send text line, server synthesizes + plays, sends back "OK\n" or "ERR\n"
"""
import sys, os, json, socket, tempfile, subprocess, threading, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[VoiceServer] %(message)s")
log = logging.getLogger(__name__)

SOCKET_PATH  = "/tmp/ethica_voice.sock"
MODULE_DIR   = Path(__file__).parent
VOICES_FILE  = MODULE_DIR / "voices.json"
ACTIVE_VOICE = "Trinity"

def get_reference_wavs(ref_dir, min_bytes=200000):
    from pathlib import Path as P
    wavs = sorted(
        [str(p) for p in P(ref_dir).glob("*.wav") if p.stat().st_size >= min_bytes],
        key=lambda p: P(p).stat().st_size,
        reverse=True
    )
    return wavs[:10] if len(wavs) > 10 else wavs

def load_model():
    import torch
    _real_load = torch.load
    def _patched_load(f, map_location=None, pickle_module=None, weights_only=False, **kwargs):
        return _real_load(f, map_location=map_location, weights_only=weights_only, **kwargs)
    torch.load = _patched_load
    from TTS.api import TTS
    log.info("Loading XTTS v2 model — this takes ~60s on first run...")
    tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        progress_bar=False,
        gpu=False
    )
    log.info("XTTS v2 model loaded. Voice server ready.")
    return tts

def synthesize(tts, text, voice_name):
    with open(VOICES_FILE) as f:
        voices = json.load(f)
    if voice_name not in voices:
        log.error(f"Voice {voice_name!r} not in voices.json")
        return None
    ref_dir = MODULE_DIR / voices[voice_name]["ref_dir"]
    speaker_wavs = get_reference_wavs(str(ref_dir))
    if not speaker_wavs:
        log.error(f"No reference wavs in {ref_dir}")
        return None
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = tmp.name
    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_wavs,
        language="en",
        file_path=out_path
    )
    return out_path

def handle_client(conn, tts):
    try:
        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break
        msg = data.decode("utf-8").strip()
        if not msg:
            conn.sendall(b"ERR\n")
            return
        # Protocol: "VOICE:Trinity|text to speak" or just "text to speak"
        if msg.startswith("VOICE:"):
            parts = msg[6:].split("|", 1)
            voice = parts[0] if len(parts) == 2 else ACTIVE_VOICE
            text  = parts[1] if len(parts) == 2 else parts[0]
        else:
            voice = ACTIVE_VOICE
            text  = msg
        log.info(f"Synthesizing [{voice}]: {text[:60]}")
        out_path = synthesize(tts, text, voice)
        if out_path:
            subprocess.run(["aplay", "-q", out_path], timeout=60)
            os.unlink(out_path)
            conn.sendall(b"OK\n")
        else:
            conn.sendall(b"ERR\n")
    except Exception as e:
        log.error(f"handle_client error: {e}")
        try:
            conn.sendall(b"ERR\n")
        except Exception:
            pass
    finally:
        conn.close()

def main():
    tts = load_model()
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(5)
    os.chmod(SOCKET_PATH, 0o600)
    log.info(f"Listening on {SOCKET_PATH}")
    # Signal ready
    print("VOICE_SERVER_READY", flush=True)
    while True:
        try:
            conn, _ = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, tts), daemon=True)
            t.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.error(f"Accept error: {e}")
    server.close()
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

if __name__ == "__main__":
    main()
