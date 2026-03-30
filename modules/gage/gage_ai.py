#streamlit run gage_ai.py

import streamlit as st
import whisper
import speech_recognition as sr
import pyttsx3
import pygame
import time
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import trimesh

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

# Initialize Pygame for Lip Syncing
pygame.init()
screen = pygame.display.set_mode((500, 500))
face_closed = pygame.image.load("gage_closed.png")  # Neutral face
face_open = pygame.image.load("gage_open.png")  # Talking face

# Load 3D Avatar Model (VR Ready)
gage_model = trimesh.load("Gage.glb")

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
user_input = st.text_input("Type your message or use voice:")
if st.button("🎤 Speak"):
    user_input = recognize_speech()

if user_input:
    # Add User Input to Chat History
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Generate AI Response
    system_prompt = "You are Gage, an advanced AI with humor, confidence, and a tactical mindset. Respond accordingly."
    prompt = f"{system_prompt}\nUser: {user_input}\nGage:"
    inputs = tokenizer(prompt, return_tensors="pt", padding=True)
    inputs["attention_mask"] = inputs["input_ids"].ne(tokenizer.pad_token_id)

    output = model.generate(**inputs, max_length=150, pad_token_id=tokenizer.pad_token_id)
    response = tokenizer.decode(output[0], skip_special_tokens=True)

    # Add AI Response to Chat History
    st.session_state["messages"].append({"role": "assistant", "content": response})

    # Speak AI Response
    engine.say(response)
    engine.runAndWait()

    # Lip Sync Animation
    for _ in range(5):
        screen.fill((0, 0, 0))
        screen.blit(face_open if time.time() % 1 < 0.5 else face_closed, (100, 100))
        pygame.display.flip()
        time.sleep(0.1)

    # Refresh Chat Display
    st.rerun()
