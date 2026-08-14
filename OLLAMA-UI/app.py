#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, Response
import requests
import json
import os
import io

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

    messages = []
    if fcontent and fname:
        ext = os.path.splitext(fname)[1].lstrip('.') or 'text'
        sys_msg = f"User uploaded file '{fname}'. Content:\n\n```{ext}\n{fcontent}\n```\n\nAnalyze or answer about this file."
        messages.append({"role": "system", "content": sys_msg})
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
