#streamlit run gage_ai.py

import streamlit as st
import whisper
import speech_recognition as sr
import pyttsx3
# import pygame  # reserved for standalone lip sync process
import time
from transformers import AutoModelForCausalLM, AutoTokenizer
import trimesh
import pathlib

# Load Whisper model for real-time speech recognition
model_whisper = whisper.load_model("base")

# Load AI Chat Model (GPT-like)
model_name = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# Load TTS Engine
engine = pyttsx3.init()
engine.setProperty("rate", 150)  # Adjust speed
engine.setProperty("voice", "english+f3")  # Change voice tone

# Initialize Pygame for Lip Syncing (only if display available)
# Pygame lip sync disabled in Streamlit context — reserved for standalone pygame process
_pygame_ok = False
screen = None
face_closed = None
face_open   = None

# Load 3D Avatar Model (VR Ready)
GAGE_GLB = pathlib.Path("/home/trinity/Ethica/assets/Gage.glb")
gage_model = trimesh.load(str(GAGE_GLB)) if GAGE_GLB.exists() else None

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Streamlit UI Setup
st.title("🤖 Talk to Gage - Your AI Companion")

# Display Gage's 3D Avatar
st.write("🕶️ **Meet Gage in 3D:**")
st.components.v1.html("""
    <model-viewer src="Gage.glb" 
        alt="Gage Avatar"
        auto-rotate
        camera-controls
        ar>
    </model-viewer>
""", height=400)

# Display Chat History
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Voice Recognition Function
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎤 Listening...")
        audio = recognizer.listen(source)

        try:
            text = model_whisper.transcribe(audio)["text"]
            st.write(f"🗣️ You said: {text}")
            return text
        except Exception:
            st.write("⚠️ Could not understand. Try again.")
            return ""

# Get User Input (Text or Voice)
user_input = st.chat_input("Type your message or use voice:")
if st.button("🎤 Speak"):
    user_input = recognize_speech()

if user_input:
    # Add User Input to Chat History
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Generate AI Response via Ollama
    system_prompt = "You are Gage, an advanced AI with humor, confidence, and a tactical mindset. Respond accordingly."
    try:
        import requests as _requests
        resp = _requests.post("http://localhost:11434/api/chat", json={
            "model": "minimax-m2.7:cloud",
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input}
            ]
        }, timeout=60)
        response = resp.json().get("message", {}).get("content", "").strip()
        if not response:
            response = "Gage is thinking... (empty response from Ollama)"
    except Exception as e:
        response = f"Gage error: {e}"

    # Add AI Response to Chat History
    st.session_state["messages"].append({"role": "assistant", "content": response})

    # Speak AI Response
    # Speak response in background thread so UI renders immediately
    import threading as _threading
    def _speak():
        engine.say(response)
        engine.runAndWait()
    _threading.Thread(target=_speak, daemon=True).start()

    # Lip Sync Animation (only if pygame display available)
    if _pygame_ok and screen:
        for _ in range(5):
            screen.fill((0, 0, 0))
            screen.blit(face_open if time.time() % 1 < 0.5 else face_closed, (100, 100))
            screen.flip()  # noqa — guarded by _pygame_ok
            time.sleep(0.1)

    # Refresh Chat Display
    st.rerun()
