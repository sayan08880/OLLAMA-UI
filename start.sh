
#!/usr/bin/env bash

APP_DIR="$HOME/.AI/OLLAMA-UI-VX10"
VENV="$HOME/.ai"
URL="http://127.0.0.1:5000"
LOG="/tmp/hulk-webui.log"

GREEN='\033[1;32m'
RESET='\033[0m'

cd "$APP_DIR" || exit 1

clear

# Activate Python environment
if [ ! -f "$VENV/bin/activate" ]; then
    echo "ERROR: .ai environment not found!"
    exit 1
fi

source "$VENV/bin/activate"

# Check dependencies
if [ -f requirements.txt ]; then
    python -m pip install -q -r requirements.txt || exit 1
fi

# Start app if server is unavailable
if ! curl -fsS "$URL" >/dev/null 2>&1; then
    nohup python -u app.py > "$LOG" 2>&1 </dev/null &
fi

# Wait for server
ready=0

printf "${GREEN}STARTING THE APP......${RESET}"

for i in {1..60}; do
    if curl -fsS "$URL" >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done

if [ "$ready" -ne 1 ]; then
    printf "\n${GREEN}✗${RESET}\n"
    exit 1
fi

printf " ${GREEN}✓${RESET}\n"

# Open browser
xdg-open "$URL" >/dev/null 2>&1 &
