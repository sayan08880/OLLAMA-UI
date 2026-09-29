#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, Response
import requests
import json
import os
import io
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen2.5-coder:3b"

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
#  Web Search (logic from web_ai.py — optimized)
# ─────────────────────────────────────────────
WEB_MAX_RESULTS = 4          # results to open (fewer = faster)
WEB_CONTENT_CHARS = 2500     # chars per source (keeps context small = fast reply)
WEB_PAGE_TIMEOUT = 8         # seconds per page
WEB_CACHE_TTL = 600          # seconds — cache fetched pages

_page_cache = {}
_cache_lock = threading.Lock()
_search_executor = ThreadPoolExecutor(max_workers=WEB_MAX_RESULTS)


def web_search(query, max_results=WEB_MAX_RESULTS):
    """Search DuckDuckGo with one retry on failure."""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return []
    for attempt in range(2):
        try:
            with DDGS() as ddgs:
                raw = ddgs.text(query, max_results=max_results)
                return [
                    {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
                    for r in raw
                ]
        except Exception:
            if attempt == 0:
                time.sleep(0.6)
    return []


def get_page_text(url):
    """Fetch and clean a webpage. Cached for WEB_CACHE_TTL seconds."""
    with _cache_lock:
        hit = _page_cache.get(url)
    if hit and time.time() - hit[1] < WEB_CACHE_TTL:
        return hit[0]

    from bs4 import BeautifulSoup
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=WEB_PAGE_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for el in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
            el.decompose()
        text = soup.get_text(separator=" ", strip=True)[:WEB_CONTENT_CHARS]
        with _cache_lock:
            _page_cache[url] = (text, time.time())
        return text
    except Exception:
        return ""


def collect_web_sources(query):
    """Search + read pages IN PARALLEL. Returns (sources, errors)."""
    results = web_search(query)
    if not results:
        return [], []

    # de-duplicate URLs
    seen, uniq = set(), []
    for r in results:
        u = r["url"].split("#")[0]
        if u and u not in seen:
            seen.add(u)
            uniq.append(r)
    uniq = uniq[:WEB_MAX_RESULTS]

    sources = []
    futures = {
        _search_executor.submit(get_page_text, r["url"]): r for r in uniq
    }
    for fut in as_completed(futures):
        r = futures[fut]
        content = fut.result()
        if content:
            sources.append({"title": r["title"], "url": r["url"], "content": content})

    # keep original ranking order
    order = {r["url"]: i for i, r in enumerate(uniq)}
    sources.sort(key=lambda s: order.get(s["url"], 99))
    return sources, uniq


def build_web_context(query, sources):
    """Format sources into an Ollama-ready system prompt."""
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
        return f"[Error reading PDF: {str(e)}]"


def extract_text_from_file(file_stream, filename):
    ext = os.path.splitext(filename.lower())[1]
    if ext == '.pdf':
        return extract_text_from_pdf(file_stream)
    if ext not in ALLOWED_EXTS:
        return f"[Unsupported file type: {ext}]"
    try:
        content = file_stream.read().decode('utf-8')
    except UnicodeDecodeError:
        file_stream.seek(0)
        content = file_stream.read().decode('latin-1')
    return content


@app.route("/")
def index():
    return render_template("index.html")


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
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty"}), 400
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

    web_sources = []
    if use_web:
        # status events streamed to UI: "__STATUS__:text\n"
        yield_lines = []

        def gen():
            yield "__STATUS__:Searching the web...\n"
            t0 = time.time()
            sources, found = collect_web_sources(msg)
            elapsed = time.time() - t0

            if found:
                yield f"__STATUS__:Read {len(sources)} of {len(found)} pages in {elapsed:.1f}s\n"

            if sources:
                web_sources.extend(sources)
                messages.append({"role": "system", "content": build_web_context(msg, sources)})
            elif found:
                yield "__STATUS__:Pages could not be read, answering without web data\n"
            else:
                yield "__STATUS__:No search results found, answering from model knowledge\n"

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
                yield f"\n[Error: {str(e)}]"

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
            yield f"\n[Error: {str(e)}]"

    return Response(generate(), mimetype="text/plain")


if __name__ == "__main__":
    print("=" * 50)
    print("  Ollama Web UI v3")
    print("  http://localhost:5000")
    print("  Ctrl+Shift+N = New Chat")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
