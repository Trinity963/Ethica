#!/bin/bash
# Ethica launcher — starts voice server then Ethica
ETHICA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAGE_PYTHON="$ETHICA_ROOT/modules/gage/gage_env/bin/python3"
VOICE_SERVER="$ETHICA_ROOT/modules/ethica_voice/ethica_voice_server.py"
SOCKET=/tmp/ethica_voice.sock

# Kill old socket if stale
[ -S "$SOCKET" ] && rm -f "$SOCKET"

# Launch voice server in background
$GAGE_PYTHON $VOICE_SERVER &
VOICE_PID=$!
echo "[Ethica] Voice server launching (PID $VOICE_PID)..."

# Wait for socket to appear (max 120s)
for i in $(seq 1 60); do
    [ -S "$SOCKET" ] && break
    sleep 2
done

if [ ! -S "$SOCKET" ]; then
    echo "[Ethica] WARNING: Voice server did not start — continuing without voice"
fi

# Launch Ethica
source "$ETHICA_ROOT/Ethica_env/bin/activate"
python3 "$ETHICA_ROOT/main.py"

# Cleanup on exit
kill $VOICE_PID 2>/dev/null
