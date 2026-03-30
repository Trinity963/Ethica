@echo off
REM Ethica v0.1 — Environment Setup
REM Windows

echo Setting up Ethica environment...

python -m venv Ethica_env

call Ethica_env\Scripts\activate

pip install --upgrade pip -q

pip install -r requirements.txt

echo Ethica_env ready.
echo To activate: Ethica_env\Scripts\activate
