#streamlit run gage_assistant.py
#run inside VSCode 


import os
import streamlit as st
import pyttsx3
import speech_recognition as sr
from transformers import pipeline
import os

# Read active file in VSCode
def read_active_code():
    try:
        file_path = os.environ.get("VSCODE_ACTIVE_FILE", None)
        if file_path and os.path.exists(file_path):
            with open(file_path, "r") as file:
                return file.read()
    except:
        return None

# Use file content as part of AI input
code_context = read_active_code()
if code_context:
    prompt = f"Here is my code:\n{code_context}\nHow can I improve this?"
else:
    prompt = "I have a coding question."

# Load AI model
code_assistant = pipeline("text-generation", model="mistralai/Mistral-7B-v0.1")

response = code_assistant(prompt, max_length=300)[0]["generated_text"]

# Initialize TTS Engine
engine = pyttsx3.init()
engine.setProperty("rate", 170)  # Speech speed

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Streamlit UI
st.title("👨‍💻 Gage - AI Coding Assistant")

st.markdown("""
**How to use:**
- Type your coding question or **use voice input**
- Gage will **generate, debug, or optimize code**
- Gage will also **speak responses**
""")

# Voice Recognition
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎤 Listening...")
        audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            st.write(f"🗣️ You said: {text}")
            return text
        except Exception:
            st.write("⚠️ Could not understand. Try again.")
            return ""

# Get user input (Text or Voice)
user_input = st.text_input("Ask Gage about your code:")
if st.button("🎤 Speak"):
    user_input = recognize_speech()

if user_input:
    # Add user message
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Generate AI response
    response = code_assistant(user_input, truncation=True, max_length=300, pad_token_id=50256)[0]["generated_text"]


    # Add AI response to chat history
    st.session_state["messages"].append({"role": "assistant", "content": response})

    # Speak AI response
    engine.say(response)
    engine.runAndWait()

    # Display response
    st.write("🧠 **Gage's Response:**")
    st.write(response)

    # Refresh UI
    st.rerun()
