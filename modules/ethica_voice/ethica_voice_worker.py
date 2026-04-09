#!/usr/bin/env python3
"""
ethica_voice_worker.py — XTTS v2 synthesis worker
Runs inside gage_env. Called by ethica_voice.py via subprocess.
Usage: python3 ethica_voice_worker.py <voice_name> <output_path> <text>
"""
import sys, json, os
import torch
_real_load = torch.load.__wrapped__ if hasattr(torch.load, "__wrapped__") else torch.load
def _patched_load(f, map_location=None, pickle_module=None, weights_only=False, **kwargs):
    return _real_load(f, map_location=map_location, weights_only=weights_only, **kwargs)
torch.load = _patched_load
import torch
_orig_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return _orig_load(*args, **kwargs)
torch.load = _patched_load
from pathlib import Path
from TTS.api import TTS

def get_reference_wavs(ref_dir, min_bytes=200000):
    wavs = sorted(
        [str(p) for p in Path(ref_dir).glob("*.wav") if p.stat().st_size >= min_bytes],
        key=lambda p: Path(p).stat().st_size,
        reverse=True
    )
    return wavs[:10] if len(wavs) > 10 else wavs

def main():
    if len(sys.argv) < 4:
        print("Usage: voice_worker.py <voice_name> <output_path> <text...>")
        sys.exit(1)

    voice_name  = sys.argv[1]
    output_path = sys.argv[2]
    text        = " ".join(sys.argv[3:])

    voices_json = Path(__file__).parent / "voices.json"
    with open(voices_json) as f:
        voices = json.load(f)

    if voice_name not in voices:
        print(f"ERROR: voice '{voice_name}' not in voices.json")
        sys.exit(1)

    ref_dir = Path(__file__).parent / voices[voice_name]["ref_dir"]
    min_kb  = voices[voice_name].get("min_bytes", 200000)
    speaker_wavs = get_reference_wavs(str(ref_dir), min_kb)

    if not speaker_wavs:
        print(f"ERROR: no reference wavs found in {ref_dir}")
        sys.exit(1)

    tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        progress_bar=False,
        gpu=False
    )

    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_wavs,
        language="en",
        file_path=output_path
    )
    print(f"OK:{output_path}")

if __name__ == "__main__":
    main()
