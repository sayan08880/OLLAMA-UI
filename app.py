#!/usr/bin/env python3
"""
OLLAMA WEB UI v4 — with Tavily Web Search + Gmail Integration (HULK)
"""
from flask import Flask, render_template, request, jsonify, Response
import requests
import json
import os
import io
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0   # never cache static files
app.config['TEMPLATES_AUTO_RELOAD'] = True
ASSET_VERSION = str(int(time.time()))        # changes on every server start

OLLAMA_HOST = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_URL = "https://api.tavily.com/search"

ALLOWED_EXTS = {
    '.txt', '.md', '.markdown', '.rst',
    '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.htm', '.css', '.scss', '.sass',
    '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.java', '.kt', '.go', '.rs', '.swift',
    '.rb', '.php', '.pl', '.sh', '.bash', '.zsh', '.fish', '.ps1',
    '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.sql', '.r', '.m', '.lua', '.dart', '.scala', '.groovy', '.clj',
    '.cs', '.vb', '.fs', '.fsx', '.pas', '.dpr',
    '.log', '.csv', '.tsv', '.tex', '.bib',
    '.dockerfile', '.makefile', '.cmake', '.gradle', '.podfile',
}

# ─────────────────────────────────────────────
#  Tavily Web Search (replaces DuckDuckGo)
# ─────────────────────────────────────────────

def tavily_search(query, max_results=4):
    """Search using Tavily API. Returns list of {title, url, content}."""
    if not TAVILY_API_KEY:
        return [], "TAVILY API KEY IS MISSING. ADD IT TO .ENV"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False
    }
    try:
        r = requests.post(TAVILY_URL, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        sources = []
        for item in results:
            sources.append({
                "title": item.get("title", "NO TITLE"),
                "url": item.get("url", ""),
                "content": item.get("content", "")[:2500]
            })
        return sources, None
    except requests.Timeout:
        return [], "TAVILY SEARCH TIMED OUT"
    except requests.RequestException as e:
        return [], f"TAVILY ERROR: {str(e)}"
    except Exception as e:
        return [], f"SEARCH FAILED: {str(e)}"


def build_web_context(query, sources):
    context = ""
    for i, s in enumerate(sources, 1):
        context += f"SOURCE {i}\nTitle: {s['title']}\nURL: {s['url']}\nContent: {s['content']}\n\n"
    return f"""You are a web research assistant.

User question: {query}

Information collected from the internet:

{context}

Answer the user's question using the information above.
Rules:
- Give a clear and useful answer.
- Summarize the important information.
- Do not invent facts.
- If the information is uncertain, say so.
- Use simple language.
- At the end, list the sources and URLs."""


def extract_text_from_pdf(file_stream):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        return f"[ERROR READING PDF: {str(e)}]"


def extract_text_from_file(file_stream, filename):
    ext = os.path.splitext(filename.lower())[1]
    if ext == '.pdf':
        return extract_text_from_pdf(file_stream)
    if ext not in ALLOWED_EXTS:
        return f"[UNSUPPORTED FILE TYPE: {ext}]"
    try:
        content = file_stream.read().decode('utf-8')
    except UnicodeDecodeError:
        file_stream.seek(0)
        content = file_stream.read().decode('latin-1')
    return content


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", v=ASSET_VERSION)


@app.route("/api/models")
def get_models():
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "NO FILE"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "EMPTY"}), 400
    try:
        file_stream = io.BytesIO(file.read())
        content = extract_text_from_file(file_stream, file.filename)
        max_chars = 12000
        truncated = len(content) > max_chars
        display = content[:max_chars] if truncated else content
        return jsonify({
            "filename": file.filename,
            "content": display,
            "size": len(content),
            "truncated": truncated,
            "ext": os.path.splitext(file.filename.lower())[1]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message", "")
    fcontent = data.get("file_content", "")
    fname = data.get("file_name", "")
    model = data.get("model", MODEL_NAME)
    use_web = bool(data.get("web_search"))

    messages = []
    if fcontent and fname:
        ext = os.path.splitext(fname)[1].lstrip('.') or 'text'
        sys_msg = f"User uploaded file '{fname}'. Content:\n\n```{ext}\n{fcontent}\n```\n\nAnalyze or answer about this file."
        messages.append({"role": "system", "content": sys_msg})

    if use_web:
        def gen():
            yield "__STATUS__:SEARCHING THE WEB WITH TAVILY...\n"
            t0 = time.time()
            sources, err = tavily_search(msg)
            elapsed = time.time() - t0

            if err:
                yield f"__STATUS__:{err}\n"
                yield f"__STATUS__:ANSWERING FROM MODEL KNOWLEDGE...\n"
            elif sources:
                yield f"__STATUS__:FOUND {len(sources)} SOURCES IN {elapsed:.1f}S\n"
                messages.append({"role": "system", "content": build_web_context(msg, sources)})
            else:
                yield "__STATUS__:NO SEARCH RESULTS FOUND, ANSWERING FROM MODEL KNOWLEDGE\n"

            messages.append({"role": "user", "content": msg})
            payload = {"model": model, "messages": messages, "stream": True}

            try:
                with requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, stream=True, timeout=300) as r:
                    for line in r.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield chunk["message"]["content"]
                            if chunk.get("done"):
                                break
            except Exception as e:
                yield f"\n[ERROR: {str(e)}]"

        return Response(gen(), mimetype="text/plain")

    messages.append({"role": "user", "content": msg})
    payload = {"model": model, "messages": messages, "stream": True}

    def generate():
        try:
            with requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, stream=True, timeout=300) as r:
                for line in r.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                        if chunk.get("done"):
                            break
        except Exception as e:
            yield f"\n[ERROR: {str(e)}]"

    return Response(generate(), mimetype="text/plain")


# ─────────────────────────────────────────────
#  Gmail API endpoints
# ─────────────────────────────────────────────

@app.route("/api/gmail/status")
def gmail_status():
    try:
        from hulk.gmail_service import gmail_connection_status
        ok, msg = gmail_connection_status()
        return jsonify({"connected": ok, "message": msg.upper()})
    except Exception as e:
        return jsonify({"connected": False, "message": str(e).upper()})


@app.route("/api/gmail/connect", methods=["POST"])
def gmail_connect():
    try:
        from hulk.gmail_service import connect_gmail
        connect_gmail()
        from hulk.gmail_service import gmail_connection_status
        ok, msg = gmail_connection_status()
        return jsonify({"ok": True, "message": msg.upper()})
    except FileNotFoundError as e:
        return jsonify({"ok": False, "message": str(e).upper()}), 400
    except Exception as e:
        return jsonify({"ok": False, "message": f"CONNECT FAILED: {str(e)}".upper()}), 500


@app.route("/api/gmail/read", methods=["POST"])
def gmail_read():
    data = request.get_json() or {}
    count = int(data.get("count", 5))
    count = max(1, min(5, count))
    try:
        from hulk.gmail_service import fetch_latest_emails
        emails = fetch_latest_emails(count)
        # simplify for frontend
        out = []
        for e in emails:
            out.append({
                "number": e["number"],
                "from": e["from"],
                "subject": e["subject"],
                "date": e["date"],
                "body": e["body"][:2000],
                "id": e["id"]
            })
        return jsonify({"ok": True, "emails": out, "count": len(out)})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e).upper()}), 500


@app.route("/api/gmail/analyze", methods=["POST"])
def gmail_analyze():
    data = request.get_json() or {}
    count = int(data.get("count", 5))
    count = max(1, min(5, count))
    model = data.get("model", MODEL_NAME)

    try:
        from hulk.gmail_service import fetch_latest_emails
        from hulk.gmail_ai import analyze_email

        emails = fetch_latest_emails(count)
        if not emails:
            return jsonify({"ok": False, "message": "NO EMAILS FOUND"})

        results = []
        for email in emails:
            # use local ollama via requests for streaming-friendly later if needed
            summary = analyze_email(email)
            results.append({
                "number": email["number"],
                "from": email["from"],
                "subject": email["subject"],
                "date": email["date"],
                "summary": summary
            })
        return jsonify({"ok": True, "results": results})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e).upper()}), 500


@app.route("/api/gmail/draft", methods=["POST"])
def gmail_draft():
    data = request.get_json() or {}
    recipient = (data.get("recipient") or "").strip()
    topic = (data.get("topic") or "").strip()
    save = bool(data.get("save", False))

    if not recipient or not topic:
        return jsonify({"ok": False, "message": "RECIPIENT AND TOPIC ARE REQUIRED"}), 400

    try:
        from hulk.gmail_ai import generate_email_draft
        draft_text = generate_email_draft(recipient, topic)

        if draft_text.startswith("ERROR:"):
            return jsonify({"ok": False, "message": draft_text.upper()})

        # parse SUBJECT / BODY
        subject = ""
        body = ""
        if "SUBJECT:" in draft_text.upper() and "BODY:" in draft_text.upper():
            parts = draft_text.split("BODY:", 1)
            subj_part = parts[0]
            body = parts[1].strip() if len(parts) > 1 else ""
            for line in subj_part.splitlines():
                if line.upper().startswith("SUBJECT:"):
                    subject = line.split(":", 1)[1].strip()
                    break
            if not subject:
                subject = "NO SUBJECT"
        else:
            subject = "DRAFT"
            body = draft_text

        draft_id = None
        if save:
            from hulk.gmail_service import create_gmail_draft
            draft_id = create_gmail_draft(recipient, subject, body)

        return jsonify({
            "ok": True,
            "subject": subject,
            "body": body,
            "full": draft_text,
            "saved": save,
            "draft_id": draft_id
        })
    except Exception as e:
        return jsonify({"ok": False, "message": str(e).upper()}), 500


if __name__ == "__main__":
    print("=" * 55)
    print("  OLLAMA WEB UI V4 + HULK GMAIL + TAVILY SEARCH")
    print("  HTTP://LOCALHOST:5000")
    print("  CTRL+SHIFT+N = NEW CHAT")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
