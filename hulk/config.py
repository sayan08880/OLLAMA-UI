import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (parent of hulk/)
_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")
load_dotenv()  # also try cwd

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

GMAIL_CLIENT_FILE = os.getenv("GMAIL_CLIENT_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")

# Resolve relative paths against project root
if not os.path.isabs(GMAIL_CLIENT_FILE):
    GMAIL_CLIENT_FILE = str(_root / GMAIL_CLIENT_FILE)
if not os.path.isabs(GMAIL_TOKEN_FILE):
    GMAIL_TOKEN_FILE = str(_root / GMAIL_TOKEN_FILE)

try:
    GMAIL_MAX_READ = int(os.getenv("GMAIL_MAX_READ", "5"))
except ValueError:
    GMAIL_MAX_READ = 5

GMAIL_MAX_READ = max(1, min(5, GMAIL_MAX_READ))

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

APP_NAME = "OLLAMA UI + HULK"
APP_VERSION = "4.0.0"
