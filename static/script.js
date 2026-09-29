/* Ollama Web UI v3 — Fast, Minimal, No Sidebar */

const $ = id => document.getElementById(id);
const chatScroll = $('chatScroll'), welcome = $('welcome'), msgs = $('messages');
const input = $('userInput'), sendBtn = $('sendBtn'), fileInput = $('fileInput');
const fileChip = $('fileChip'), statusDot = $('statusDot'), modelName = $('modelName');
const sendIcon = $('sendIcon'), stopIcon = $('stopIcon');
const modelDropdown = $('modelDropdown'), modelMenu = $('modelMenu'), modelPillBtn = $('modelPillBtn');

let generating = false, ctrl = null, attached = null;
let webMode = false;
const webBtn = $('webBtn'), webChip = $('webChip');
let availableModels = [], selectedModel = null;

// ─── Init ───
addEventListener('DOMContentLoaded', () => {
    checkStatus();
    input.focus();
    setupDragDrop();
});

document.addEventListener('click', e => {
    if (!modelDropdown.contains(e.target)) modelDropdown.classList.remove('open');
});

// ─── Status / Models ───
async function checkStatus() {
    try {
        const r = await fetch('/api/models');
        if (!r.ok) throw 0;
        const d = await r.json();
        availableModels = d.models || [];
        statusDot.className = 'dot online';

        if (availableModels.length) {
            const preferred = availableModels.find(m => m.name.includes('qwen2.5-coder'));
            selectedModel = selectedModel || (preferred ? preferred.name : availableModels[0].name);
        } else {
            selectedModel = null;
        }
        modelName.textContent = selectedModel || 'No models';
        renderModelMenu();
    } catch {
        statusDot.className = 'dot offline';
        modelName.textContent = 'Offline';
        availableModels = [];
        renderModelMenu();
    }
}

function renderModelMenu() {
    if (!availableModels.length) {
        modelMenu.innerHTML = '<div class="model-menu-empty">No models found</div>';
        return;
    }
    modelMenu.innerHTML = availableModels.map(m => `
        <button class="model-menu-item ${m.name === selectedModel ? 'active' : ''}" onclick="selectModel('${m.name.replace(/'/g, "\\'")}')">
            <span>${m.name}</span>
            <svg class="model-check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
        </button>
    `).join('');
}

function toggleModelMenu() {
    modelDropdown.classList.toggle('open');
}

function selectModel(name) {
    selectedModel = name;
    modelName.textContent = name;
    modelDropdown.classList.remove('open');
    renderModelMenu();
}

// ─── Keyboard ───
function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
    if (e.key === 'n' && e.ctrlKey && e.shiftKey) { e.preventDefault(); newChat(); }
    if (e.key === 'l' && e.ctrlKey && !e.shiftKey) { e.preventDefault(); clearChat(); }
    if (e.key === 'Escape' && generating && ctrl) { ctrl.abort(); }
}

function resize(t) { t.style.height = 'auto'; t.style.height = Math.min(t.scrollHeight, 180) + 'px'; }

// ─── File Upload ───
function setupDragDrop() {
    const overlay = document.createElement('div');
    overlay.className = 'drag-overlay';
    overlay.innerHTML = '<p>Drop file to upload</p>';
    document.body.appendChild(overlay);

    ['dragenter','dragover','dragleave','drop'].forEach(e =>
        document.body.addEventListener(e, ev => { ev.preventDefault(); ev.stopPropagation(); }, false)
    );
    document.body.addEventListener('dragenter', () => overlay.classList.add('on'));
    overlay.addEventListener('dragleave', () => overlay.classList.remove('on'));
    overlay.addEventListener('drop', e => {
        overlay.classList.remove('on');
        if (e.dataTransfer.files.length) upload(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', e => { if (e.target.files[0]) upload(e.target.files[0]); });
}

async function upload(file) {
    sendBtn.disabled = true;
    const fd = new FormData();
    fd.append('file', file);
    try {
        const r = await fetch('/api/upload', { method: 'POST', body: fd });
        const d = await r.json();
        if (d.error) throw new Error(d.error);
        attached = { name: d.filename, content: d.content };
        showChip(d.filename, d.truncated);
        input.placeholder = 'Ask about ' + d.filename + '...';
        input.focus();
    } catch (e) {
        alert('Upload failed: ' + e.message);
    } finally {
        sendBtn.disabled = false;
        fileInput.value = '';
    }
}

function showChip(name, truncated) {
    fileChip.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg> ${name}${truncated ? ' (truncated)' : ''} <button onclick="removeFile()">×</button>`;
    fileChip.style.display = 'flex';
}

function removeFile() {
    attached = null;
    fileChip.style.display = 'none';
    input.placeholder = 'Message...';
}

// ─── Web Search Toggle ───
function toggleWeb() {
    webMode = !webMode;
    webBtn.classList.toggle('on', webMode);
    webChip.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg> Web search ON <button onclick="toggleWeb()">×</button>';
    webChip.style.display = webMode ? 'flex' : 'none';
    input.placeholder = webMode ? 'Web Connected' : 'Message...';
    input.focus();
}

// ─── Send ───
function handleSendClick() {
    if (generating) {
        if (ctrl) ctrl.abort();
        return;
    }
    send();
}

function setSendingState(on) {
    generating = on;
    sendBtn.classList.toggle('stopping', on);
    sendBtn.title = on ? 'Stop generating' : 'Send';
    sendIcon.style.display = on ? 'none' : 'block';
    stopIcon.style.display = on ? 'block' : 'none';
}

async function send() {
    const text = input.value.trim();
    if ((!text && !attached) || generating) return;

    welcome.style.display = 'none';
    msgs.style.display = 'block';
    msgs.classList.add('on');

    const display = attached && !text ? `📎 ${attached.name}` : attached ? `📎 ${attached.name}\n${text}` : text;
    addMsg('user', display);
    input.value = ''; resize(input);

    const ai = addMsg('ai', '');
    const body = ai.querySelector('.msg-body');
    const typing = document.createElement('div');
    typing.className = 'typing';
    typing.innerHTML = '<span></span><span></span><span></span>';
    body.appendChild(typing);

    setSendingState(true);
    ctrl = new AbortController();

    // status line for web search progress
    const status = document.createElement('div');
    status.className = 'web-status';
    status.style.display = 'none';

    let full = '', first = true;
    try {
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text || `Analyze this file: ${attached?.name || ''}`,
                file_content: attached?.content || '',
                file_name: attached?.name || '',
                model: selectedModel || undefined,
                web_search: webMode
            }),
            signal: ctrl.signal
        });
        if (!r.ok) throw new Error('Failed');

        const reader = r.body.getReader();
        const dec = new TextDecoder();
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            let chunk = dec.decode(value, { stream: true });

            // consume backend status events "__STATUS__:text\n"
            while (chunk.includes('__STATUS__:')) {
                const sIdx = chunk.indexOf('__STATUS__:');
                const eIdx = chunk.indexOf('\n', sIdx);
                const statusText = chunk.slice(sIdx + 10, eIdx === -1 ? undefined : eIdx);
                chunk = chunk.slice(0, sIdx) + (eIdx === -1 ? '' : chunk.slice(eIdx + 1));
                if (first) {
                    typing.remove();
                    body.appendChild(status);
                    status.style.display = 'flex';
                }
                status.innerHTML = '<span class="spinner"></span>' + esc(statusText);
                scroll();
            }
            if (!chunk) continue;

            full += chunk;
            if (first) { body.innerHTML = ''; first = false; }
            if (status.parentNode === body) status.remove();
            body.innerHTML = md(full);
            scroll();
        }
    } catch (e) {
        if (e.name === 'AbortError') body.innerHTML = md(full + '\n\n_Stopped_');
        else body.innerHTML = `<span style="color:var(--danger)">Error: ${e.message}</span>`;
    } finally {
        setSendingState(false); ctrl = null; scroll();
    }
}

function addMsg(role, text) {
    const d = document.createElement('div');
    d.className = 'msg ' + role;
    d.innerHTML = `<div class="msg-av">${role === 'user' ? 'Y' : 'AI'}</div><div class="msg-body">${role === 'user' ? esc(text).replace(/\n/g, '<br>') : text}</div>`;
    msgs.appendChild(d);
    scroll();
    return d;
}

// ─── Markdown (fast, minimal) ───
function md(t) {
    let h = esc(t);
    h = h.replace(/```([\w]*)([\s\S]*?)```/g, (_, lang, code) => `<pre><code>${code.trim()}</code></pre>`);
    h = h.replace(/`([^`]+)`/g, '<code>$1</code>');
    h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');
    h = h.replace(/^(#{1,3})\s+(.+)$/gm, (_, hashes, title) => `<h${hashes.length}>${title}</h${hashes.length}>`);
    h = h.replace(/\n/g, '<br>');
    return h;
}

function esc(t) {
    const d = document.createElement('div');
    d.textContent = t;
    return d.innerHTML;
}

function scroll() { chatScroll.scrollTop = chatScroll.scrollHeight; }

// ─── Chat Controls ───
function newChat() {
    msgs.innerHTML = ''; msgs.style.display = 'none'; msgs.classList.remove('on');
    welcome.style.display = 'flex'; removeFile();
    input.value = ''; resize(input); input.focus();
    if (ctrl) ctrl.abort();
    setSendingState(false);
}

function clearChat() {
    msgs.innerHTML = '';
    if (ctrl) ctrl.abort();
    setSendingState(false);
    input.focus();
}

function toggleShortcuts() {
    $('shortcutsModal').classList.toggle('active');
}

addEventListener('beforeunload', () => { if (ctrl) ctrl.abort(); });
