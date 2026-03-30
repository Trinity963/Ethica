#!/bin/bash
# Ethica v0.1 — Environment Setup
# Linux / macOS

echo "🟣 Setting up Ethica environment..."

# Create virtual environment
python3 -m venv Ethica_env

# Activate
source Ethica_env/bin/activate

# Upgrade pip silently
pip install --upgrade pip -q

# Install dependencies
pip install -r requirements.txt

echo "✅ Ethica_env ready."
echo "👉 To activate: source Ethica_env/bin/activate"
