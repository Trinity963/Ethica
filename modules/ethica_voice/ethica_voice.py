# ============================================================
# Ethica v0.1 — ethica_voice.py
# Voice Training Module — record, manage, select voice profiles
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Voice profiles stored in ~/Ethica/memory/voices/
# Each profile: samples/ dir + profile.json + model/ (when trained)
#
# Current backend: pyttsx3 (system voices)
# Future backend:  Coqui TTS on M5 — swap engine, profiles persist
#
# Tools:
#   voice_list    — list available voice profiles + system voices
#   voice_select  — set active voice (system or custom profile)
#   voice_record  — record a sample for custom voice training
#   voice_status  — show current voice config
# ============================================================

import json
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

BASE_DIR    = Path(__file__).parent.parent.parent
MEMORY_DIR  = BASE_DIR / "memory"
VOICES_DIR  = MEMORY_DIR / "voices"
VOICE_CONFIG= MEMORY_DIR / "voice_config.json"

# TTS script location
TTS_SCRIPT  = BASE_DIR / "modules" / "gage" / "ethica_tts.py"
TTS_PYTHON  = BASE_DIR / "modules" / "gage" / "gage_env" / "bin" / "python3"


def _read(path):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as e:
        return str(e)


def _get_system_voices():
    """Get available pyttsx3 system voices."""
    try:
        result = subprocess.run(
            [str(TTS_PYTHON), "-c",
             "import pyttsx3; e=pyttsx3.init(); "
             "[print(v.id+'|'+v.name) for v in e.getProperty('voices')]"],
            capture_output=True, text=True, timeout=10
        )
        voices = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                vid, name = line.split("|", 1)
                voices.append({"id": vid.strip(), "name": name.strip(), "type": "system"})
        return voices
    except Exception:
        return []


def _get_voice_config():
    config = _read(VOICE_CONFIG)
    if not config:
        config = {
            "version": "1.0",
            "active_voice": "system_default",
            "active_voice_id": None,
            "backend": "pyttsx3",
            "rate": 165,
            "volume": 0.95,
            "created": datetime.now().isoformat()
        }
    return config


# ── Tool: voice_list ──────────────────────────────────────────
def voice_list(input_str):
    """List available voices — system voices and custom profiles."""
    config   = _get_voice_config()
    active   = config.get("active_voice", "system_default")
    profiles = sorted(VOICES_DIR.glob("*/profile.json")) if VOICES_DIR.exists() else []

    lines = [
        "EthicaVoice — available voices",
        "─" * 40,
        f"Active: {active}  (backend: {config.get('backend', 'pyttsx3')})",
        "",
        "▸ CUSTOM PROFILES",
    ]

    if not profiles:
        lines.append("  (none yet — use 'voice record' to create one)")
    else:
        for pf in profiles:
            try:
                p = json.loads(pf.read_text())
                name     = p.get("name", pf.parent.name)
                samples  = p.get("sample_count", 0)
                trained  = "✓ trained" if p.get("trained") else "· samples only"
                marker   = " ◀ active" if name == active else ""
                lines.append(f"  {name:<20} {samples} sample(s)  {trained}{marker}")
            except Exception:
                pass

    lines += ["", "▸ SYSTEM VOICES"]
    sys_voices = _get_system_voices()
    if not sys_voices:
        lines.append("  (could not retrieve system voices)")
    else:
        for v in sys_voices[:10]:
            marker = " ◀ active" if v["id"] == config.get("active_voice_id") else ""
            lines.append(f"  {v['name'][:40]}{marker}")
        if len(sys_voices) > 10:
            lines.append(f"  ... and {len(sys_voices)-10} more")

    lines += [
        "",
        "Commands:",
        "  voice select <name or system voice name>",
        "  voice record <profile name>",
        "  voice status",
    ]

    return "\n".join(lines)


# ── Tool: voice_select ────────────────────────────────────────
def voice_select(input_str):
    """Select active voice. Input: profile name or system voice name."""
    target = input_str.strip()
    if not target:
        return "EthicaVoice — usage: voice select <name>"

    config = _get_voice_config()

    # Check custom profiles first
    if VOICES_DIR.exists():
        for pf in VOICES_DIR.glob("*/profile.json"):
            try:
                p = json.loads(pf.read_text())
                if p.get("name", "").lower() == target.lower():
                    if not p.get("trained"):
                        return (
                            f"EthicaVoice — profile '{target}' exists but hasn't been trained yet.\n"
                            f"  Record more samples and train on M5 first."
                        )
                    config["active_voice"]    = p["name"]
                    config["active_voice_id"] = None
                    config["backend"]         = "coqui"
                    _write(VOICE_CONFIG, config)
                    return f"EthicaVoice — active voice set to custom profile: {p['name']}"
            except Exception:
                pass

    # Check system voices
    sys_voices = _get_system_voices()
    matched = None
    for v in sys_voices:
        if target.lower() in v["name"].lower():
            matched = v
            break

    if matched:
        config["active_voice"]    = matched["name"]
        config["active_voice_id"] = matched["id"]
        config["backend"]         = "pyttsx3"
        _write(VOICE_CONFIG, config)

        # Update ethica_tts.py to use this voice — patch voice selection
        _patch_tts_voice(matched["id"])

        return f"EthicaVoice — active voice set to: {matched['name']}"

    return (
        f"EthicaVoice — no voice found matching '{target}'\n"
        "Run 'voice list' to see available voices."
    )


def _patch_tts_voice(voice_id):
    """Update ethica_tts.py to prefer a specific voice ID."""
    try:
        if not TTS_SCRIPT.exists():
            return
        content = TTS_SCRIPT.read_text(encoding="utf-8")
        # Update the SELECTED_VOICE_ID line or inject it
        import re
        if "SELECTED_VOICE_ID" in content:
            content = re.sub(
                r'SELECTED_VOICE_ID\s*=\s*["\'].*?["\']',
                f'SELECTED_VOICE_ID = "{voice_id}"',
                content
            )
        else:
            content = content.replace(
                "def clean_for_speech",
                f'SELECTED_VOICE_ID = "{voice_id}"\n\ndef clean_for_speech'
            )
            content = content.replace(
                "    for v in voices:\n        if any(w in v.name.lower() for w in",
                "    # Prefer selected voice\n"
                "    for v in voices:\n"
                "        if v.id == SELECTED_VOICE_ID:\n"
                "            engine.setProperty('voice', v.id)\n"
                "            break\n"
                "    else:\n"
                "     for v in voices:\n"
                "      if any(w in v.name.lower() for w in"
            )
        TTS_SCRIPT.write_text(content, encoding="utf-8")
    except Exception:
        pass


# ── Tool: voice_record ────────────────────────────────────────
def voice_record(input_str):
    """
    Record a voice sample for a custom profile.
    Input: profile name
    Records 5 seconds via arecord, saves to voices/name/samples/
    """
    name = input_str.strip()
    if not name:
        return "EthicaVoice — usage: voice record <profile name>"

    # Sanitize name
    safe_name = "".join(c for c in name if c.isalnum() or c in "-_").lower()
    if not safe_name:
        return "EthicaVoice — invalid profile name"

    profile_dir = VOICES_DIR / safe_name
    samples_dir = profile_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    # Load or create profile
    profile_file = profile_dir / "profile.json"
    profile = _read(profile_file)
    if not profile:
        profile = {
            "name":         safe_name,
            "created":      datetime.now().isoformat(),
            "sample_count": 0,
            "trained":      False,
            "backend":      "coqui_pending"
        }

    # Generate sample filename
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    sample_file = samples_dir / f"sample_{ts}.wav"

    # Sentences to read for consistent training samples
    sentences = [
        "Hello V. I'm Ethica. I'm here when you're ready.",
        "I walk beside you, not above you.",
        "What are we thinking about today?",
        "The system is running cleanly. All modules are active.",
        "I carry what I have gathered so far.",
    ]
    sample_idx = profile["sample_count"] % len(sentences)
    prompt_text = sentences[sample_idx]

    lines = [
        f"EthicaVoice — recording for profile: {safe_name}",
        f"Sample #{profile['sample_count'] + 1}",
        "─" * 40,
        "Please read aloud:",
        f"  \"{prompt_text}\"",
        "",
        "Recording 5 seconds via arecord...",
    ]

    def _record():
        try:
            subprocess.run([
                "arecord",
                "-d", "5",
                "-f", "S16_LE",
                "-r", "22050",
                "-c", "1",
                str(sample_file)
            ], timeout=8, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Update profile
            profile["sample_count"] += 1
            profile["last_sample"]   = datetime.now().isoformat()
            profile["samples"] = profile.get("samples", [])
            profile["samples"].append({
                "file":    sample_file.name,
                "prompt":  prompt_text,
                "recorded": datetime.now().isoformat()
            })
            _write(profile_file, profile)

        except Exception as e:
            print(f"[VoiceRecord] Error: {e}")

    thread = threading.Thread(target=_record, daemon=True)
    thread.start()
    thread.join(timeout=9)

    if sample_file.exists():
        size = round(sample_file.stat().st_size / 1024, 1)
        lines += [
            f"✓ Recorded: {sample_file.name} ({size} KB)",
            f"  Saved to: {samples_dir}",
            f"  Total samples: {profile['sample_count']}",
            "",
            "Next prompt for next recording:",
            f"  \"{sentences[(sample_idx + 1) % len(sentences)]}\"",
            "",
            "Collect 20+ samples for good voice training.",
            "Training runs on M5 with Coqui TTS.",
        ]
    else:
        lines += [
            "✗ Recording failed — check microphone",
            "  Try: arecord -l  to list devices",
        ]

    return "\n".join(lines)


# ── Tool: voice_status ────────────────────────────────────────
def voice_status(input_str):
    """Show current voice configuration."""
    config   = _get_voice_config()
    profiles = sorted(VOICES_DIR.glob("*/profile.json")) if VOICES_DIR.exists() else []

    total_samples = 0
    for pf in profiles:
        try:
            p = json.loads(pf.read_text())
            total_samples += p.get("sample_count", 0)
        except Exception:
            pass

    lines = [
        "EthicaVoice — status",
        "─" * 40,
        f"Active voice   : {config.get('active_voice', 'system_default')}",
        f"Backend        : {config.get('backend', 'pyttsx3')}",
        f"Rate           : {config.get('rate', 165)} wpm",
        f"Volume         : {config.get('volume', 0.95)}",
        f"Custom profiles: {len(profiles)}",
        f"Total samples  : {total_samples}",
        "",
        "▸ M5 MIGRATION NOTE",
        "  Install Coqui TTS in gage_env on M5:",
        "  pip install TTS",
        "  Then: voice select <your profile name>",
        "  Profiles in ~/Ethica/memory/voices/ will transfer automatically.",
    ]

    return "\n".join(lines)


# ── Module registry interface ──────────────────────────────────
TOOLS = {
    "voice_list":   voice_list,
    "voice_select": voice_select,
    "voice_record": voice_record,
    "voice_status": voice_status,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[EthicaVoice] Unknown tool: {tool_name}"
