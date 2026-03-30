#!/usr/bin/env python3
# ============================================================
# ethica_tts.py — Ethica Voice Engine
# Runs inside gage_env. Called as subprocess by main_window.
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Usage: gage_env/bin/python3 ethica_tts.py "text to speak"
# Or via stdin: echo "text" | gage_env/bin/python3 ethica_tts.py
# ============================================================

import sys
import re
import pyttsx3


def clean_for_speech(text):
    """Strip UI/tool artifacts — speak only clean conversational text."""
    # Remove tool markers
    text = re.sub(r'\[DEBUG[^\]]*\]', '', text)
    text = re.sub(r'\[TOOL:[^\]]*\]', '', text)
    text = re.sub(r'\[CANVAS[^\]]*\]', '', text)
    text = re.sub(r'\[PROJECT[^\]]*\]', '', text)
    # Remove arrow markers
    text = re.sub(r'→.*?(Ops|debug tab|Canvas.*?tab)', '', text)
    text = re.sub(r'⟁.*?→.*', '', text)
    # Remove markdown
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', lambda m: m.group(0)[1:-1], text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s+', '', text)
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    # Remove glyph
    text = text.replace('⟁Σ∿∞', '')
    # Collapse whitespace
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def speak(text):
    text = clean_for_speech(text)
    if not text:
        return
    engine = pyttsx3.init()
    # Warm, moderate pace
    engine.setProperty('rate', 165)
    engine.setProperty('volume', 0.95)
    # Prefer a female voice if available
    voices = engine.getProperty('voices')
    for v in voices:
        if any(w in v.name.lower() for w in ('female', 'zira', 'hazel', 'victoria', 'karen', 'samantha')):
            engine.setProperty('voice', v.id)
            break
    engine.say(text)
    engine.runAndWait()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
    else:
        text = sys.stdin.read()
    speak(text)
