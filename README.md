# Ollama Web UI

## Features

- **No sidebar** — clean top bar with model status and controls
- **File upload** — drag & drop or click paperclip (PDF, TXT, code files)
- **Streaming** — real-time token output
- **Web search** — click the globe button to search the web before answering
  - Parallel page fetching (fast), page caching, live search-status indicator
  - Sources are listed at the end of the answer
- **Fast & lightweight** — minimal JS, no bloat
- **Keyboard shortcuts:**
  - `Enter` — Send
  - `Shift+Enter` — New line
  - `Ctrl+Shift+N` — New chat
  - `Ctrl+L` — Clear chat
  - `Esc` — Stop generating

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000**

Make sure Ollama is running: `ollama serve`

## Supported Files

`.pdf` `.txt` `.md` `.py` `.js` `.html` `.css` `.c` `.cpp` `.java` `.go` `.rs` `.json` `.sql` `.sh` and 30+ more.

## Tips

- Click the globe icon to enable Web Search, then ask anything
- Upload a file, then type "explain this" or "find bugs"
- Large files auto-truncate to fit model context
- Everything runs locally — no data leaves your machine
