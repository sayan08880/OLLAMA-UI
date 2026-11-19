# OLLAMA WEB UI V4 + HULK

Local Ollama chat UI with **Tavily Web Search** and **Gmail Integration**.

## Features

- Streaming chat with any Ollama model
- File upload (PDF, code, text)
- **Tavily API Web Search** (replaces old DuckDuckGo)
- **Gmail Integration**
  - Connect Gmail key (OAuth)
  - After connect → free message mode is disabled
  - Selection mode only:
    - MAIL READ (choose 1–5)
    - ANALYZE MAILS (AI summary)
    - GENERATE DRAFT
    - SAVE DRAFT TO GMAIL (never auto-sends)
- All UI labels in CAPITAL letters
- Keyboard shortcuts preserved

## Setup

```bash
cd OLLAMA-UI-UPDATED
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1. Environment

```bash
cp .env.example .env
# Edit .env and put your Tavily API key
```

### 2. Gmail (optional)

1. Place your Google OAuth Desktop `credentials.json` in this folder.
2. First time: click **GMAIL** button → **CONNECT GMAIL KEY**
3. Browser opens → login → token.json is created automatically.

### 3. Run

```bash
ollama serve          # in another terminal
python app.py
```

Open http://localhost:5000

## Gmail Selection Flow

1. Click the envelope (Gmail) button.
2. The selection panel opens **in the input box position** and free chat is disabled.
3. Pick one dot-box option (stacked vertically):
   - ( ) 1 · **CONNECT GMAIL KEY**
   - ( ) 2 · **MAIL READ** → choose 1–5 → RUN
   - ( ) 3 · **ANALYZE MAILS** → choose 1–5 → AI summarizes each
   - ( ) 4 · **GENERATE DRAFT** → recipient + topic
   - ( ) 5 · **SAVE DRAFT TO GMAIL** → generates + saves as draft (never sends)
4. Use **EXIT GMAIL** (or press ESC) to return to normal chat.

## UI

Glassmorphism theme: frosted translucent panels, animated aurora background,
glowing accents, gradient send button. Also fixed: shortcuts modal and model
dropdown styling, and duplicated CSS.

## Result Layout

- **MAIL READ** → one glass card per email (sender avatar, address, date, subject, scrollable message).
- **ANALYZE MAILS** → one card per email: category badge, ACTION NEEDED / NO ACTION status,
  summary, important points as a list, and a suggested reply with a COPY button.
- **DRAFTS** → TO / SUBJECT / BODY fields with copy buttons, SAVED / NOT SENT status.

## Security

Never share:

- `.env`
- `credentials.json`
- `token.json`

## Notes

- Web search now uses Tavily (API key required).
- Old DuckDuckGo + page scraping removed.
- All other features (models, file upload, streaming, shortcuts) kept.
