/* OLLAMA WEB UI V4 — TAVILY SEARCH + GMAIL INTEGRATION */

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

// Gmail state
let gmailMode = false;
let gmailConnected = false;
let currentGmailAction = null;
const gmailBtn = $('gmailBtn'), gmailChip = $('gmailChip');
const inputBar = $('inputBar');
const gmailPanel = $('gmailPanel'), gmailForm = $('gmailForm'), gmailFormFields = $('gmailFormFields');

// ─── INIT ───
addEventListener('DOMContentLoaded', () => {
    checkStatus();
    checkGmailStatus();
    input.focus();
    setupDragDrop();
});

document.addEventListener('click', e => {
    if (!modelDropdown.contains(e.target)) modelDropdown.classList.remove('open');
});

// ─── STATUS / MODELS ───
async function checkStatus() {
    try {
        const r = await fetch('/api/models');
        if (!r.ok) throw 0;
        const d = await r.json();
        availableModels = d.models || [];
        statusDot.className = 'dot online';

        if (availableModels.length) {
            const preferred = availableModels.find(m => m.name.includes('qwen2.5-coder') || m.name.includes('qwen2.5'));
            selectedModel = selectedModel || (preferred ? preferred.name : availableModels[0].name);
        } else {
            selectedModel = null;
        }
        modelName.textContent = selectedModel || 'NO MODELS';
        renderModelMenu();
    } catch {
        statusDot.className = 'dot offline';
        modelName.textContent = 'OFFLINE';
        availableModels = [];
        renderModelMenu();
    }
}

function renderModelMenu() {
    modelMenu.innerHTML = '';
    if (!availableModels.length) {
        modelMenu.innerHTML = '<div class="model-item dim">NO MODELS FOUND</div>';
        return;
    }
    availableModels.forEach(m => {
        const item = document.createElement('div');
        item.className = 'model-item' + (m.name === selectedModel ? ' active' : '');
        item.textContent = m.name;
        item.onclick = () => {
            selectedModel = m.name;
            modelName.textContent = m.name;
            modelDropdown.classList.remove('open');
            renderModelMenu();
        };
        modelMenu.appendChild(item);
    });
}

function toggleModelMenu() {
    modelDropdown.classList.toggle('open');
}

// ─── GMAIL ───
async function checkGmailStatus() {
    try {
        const r = await fetch('/api/gmail/status');
        const d = await r.json();
        gmailConnected = !!d.connected;
        if (gmailConnected) {
            gmailBtn.classList.add('on');
            $('gmailStatusText').textContent = d.message || 'GMAIL CONNECTED';
        } else {
            gmailBtn.classList.remove('on');
            $('gmailStatusText').textContent = 'GMAIL NOT CONNECTED — CLICK CONNECT GMAIL KEY';
        }
    } catch {
        gmailConnected = false;
        gmailBtn.classList.remove('on');
    }
}

function setGmailUI(on) {
    gmailMode = on;
    gmailBtn.classList.toggle('on', on);
    gmailPanel.style.display = on ? 'block' : 'none';
    inputBar.classList.toggle('gmail-on', on);
    gmailChip.style.display = on ? 'flex' : 'none';
    if (on) gmailChip.innerHTML = 'GMAIL MODE ON <button onclick="exitGmailMode()">×</button>';
    input.disabled = on;
    input.placeholder = on ? 'GMAIL SELECTION MODE — CHOOSE AN OPTION' : 'MESSAGE...';
    if (!on) resetGmailSelection();
}

function resetGmailSelection() {
    document.querySelectorAll('input[name="gmailOpt"]').forEach(r => r.checked = false);
    gmailForm.style.display = 'none';
    gmailPanel.classList.remove('has-form');
    gmailFormFields.innerHTML = '';
    currentGmailAction = null;
}

function toggleGmailMode() {
    if (gmailMode) return exitGmailMode();
    webMode = false;
    webBtn.classList.remove('on');
    webChip.style.display = 'none';
    setGmailUI(true);
    checkGmailStatus();
    scroll();
}

function exitGmailMode() {
    setGmailUI(false);
    input.focus();
}

function pickCount(n) {
    $('mailCount').value = n;
    document.querySelectorAll('.count-chip').forEach(c => c.classList.toggle('on', +c.dataset.n === n));
}

function gmailAction(action) {
    currentGmailAction = action;
    gmailForm.style.display = 'block';
    gmailPanel.classList.add('has-form');
    gmailFormFields.innerHTML = '';

    if (action === 'connect') {
        gmailFormFields.innerHTML = '<p class="gmail-hint">THIS WILL OPEN A BROWSER WINDOW FOR GOOGLE OAUTH. MAKE SURE CREDENTIALS.JSON IS PRESENT.</p>';
        $('gmailSubmitBtn').textContent = 'CONNECT GMAIL KEY';
    } else if (action === 'read' || action === 'analyze') {
        gmailFormFields.innerHTML = `
            <label>HOW MANY MAILS TO VIEW? (MAX 5)</label>
            <input type="hidden" id="mailCount" value="5">
            <div class="count-row">${[1,2,3,4,5].map(n =>
                `<button type="button" class="count-chip${n === 5 ? ' on' : ''}" data-n="${n}" onclick="pickCount(${n})">${n}</button>`
            ).join('')}</div>`;
        $('gmailSubmitBtn').textContent = action === 'read' ? 'READ MAILS' : 'ANALYZE MAILS';
    } else if (action === 'draft' || action === 'save_draft') {
        gmailFormFields.innerHTML = `
            <label>RECIPIENT EMAIL</label>
            <input type="email" id="draftTo" placeholder="EXAMPLE@GMAIL.COM" class="gmail-input">
            <label>TOPIC / WHAT TO WRITE</label>
            <textarea id="draftTopic" rows="3" placeholder="WRITE ABOUT..." class="gmail-input"></textarea>`;
        $('gmailSubmitBtn').textContent = action === 'save_draft' ? 'GENERATE + SAVE DRAFT' : 'GENERATE DRAFT';
    }
    setTimeout(() => $('gmailSubmitBtn').scrollIntoView({ block: 'nearest', behavior: 'smooth' }), 30);
}

async function submitGmailForm() {
    if (!currentGmailAction) return;
    welcome.style.display = 'none';
    msgs.style.display = 'block';
    msgs.classList.add('on');

    const action = currentGmailAction;
    let userText = '';

    if (action === 'connect') {
        userText = 'CONNECT GMAIL KEY';
        addMsg('user', userText);
        const ai = addMsg('ai', '');
        const body = ai.querySelector('.msg-body');
        body.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
        try {
            const r = await fetch('/api/gmail/connect', { method: 'POST' });
            const d = await r.json();
            body.innerHTML = md(d.message || (d.ok ? 'GMAIL CONNECTED' : 'FAILED'));
            if (d.ok) {
                gmailConnected = true;
                checkGmailStatus();
            }
        } catch (e) {
            body.innerHTML = `<span style="color:var(--danger)">ERROR: ${e.message}</span>`;
        }
        return;
    }

    if (action === 'read' || action === 'analyze') {
        const count = Math.min(5, Math.max(1, parseInt($('mailCount')?.value || 5)));
        userText = action === 'read' ? `MAIL READ ${count} MAIL` : `ANALYZE ${count} MAILS`;
        addMsg('user', userText);
        const ai = addMsg('ai', '');
        const body = ai.querySelector('.msg-body');
        body.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';

        try {
            const endpoint = action === 'read' ? '/api/gmail/read' : '/api/gmail/analyze';
            const r = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ count, model: selectedModel })
            });
            const d = await r.json();
            if (!d.ok) {
                body.innerHTML = md(d.message || 'ERROR');
                return;
            }
            body.classList.add('cards');
            body.innerHTML = action === 'read' ? renderReadCards(d) : renderAnalysisCards(d);
            scroll();
        } catch (e) {
            body.innerHTML = `<span style="color:var(--danger)">ERROR: ${e.message}</span>`;
        }
        return;
    }

    if (action === 'draft' || action === 'save_draft') {
        const recipient = ($('draftTo')?.value || '').trim();
        const topic = ($('draftTopic')?.value || '').trim();
        if (!recipient || !topic) {
            alert('RECIPIENT AND TOPIC ARE REQUIRED');
            return;
        }
        userText = action === 'save_draft'
            ? `GENERATE + SAVE DRAFT TO: ${recipient}`
            : `GENERATE DRAFT TO: ${recipient}`;
        addMsg('user', userText);
        const ai = addMsg('ai', '');
        const body = ai.querySelector('.msg-body');
        body.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';

        try {
            const r = await fetch('/api/gmail/draft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    recipient,
                    topic,
                    save: action === 'save_draft',
                    model: selectedModel
                })
            });
            const d = await r.json();
            if (!d.ok) {
                body.innerHTML = md(d.message || 'ERROR');
                return;
            }
            body.classList.add('cards');
            body.innerHTML = renderDraftCard(d, recipient);
            scroll();
        } catch (e) {
            body.innerHTML = `<span style="color:var(--danger)">ERROR: ${e.message}</span>`;
        }
    }
}


// ─── GMAIL RESULT CARDS ───
const SECTION_KEYS = ['SUMMARY', 'CATEGORY', 'IMPORTANT POINTS', 'ACTION REQUIRED', 'SUGGESTED REPLY'];

function parseSender(from) {
    const m = String(from || '').match(/^\s*"?([^"<]*?)"?\s*<([^>]+)>\s*$/);
    if (m) return { name: m[1].trim() || m[2], addr: m[2] };
    return { name: from || 'UNKNOWN', addr: '' };
}

function parseAnalysis(text) {
    const out = {};
    const re = /(?:^|\n)\s*(?:\d+[.)]\s*)?\**\s*(SUMMARY|CATEGORY|IMPORTANT POINTS|ACTION REQUIRED|SUGGESTED REPLY)\s*\**\s*:?\**\s*/gi;
    const marks = [];
    let m;
    while ((m = re.exec(text)) !== null) marks.push({ key: m[1].toUpperCase(), start: m.index, end: re.lastIndex });
    marks.forEach((mk, i) => {
        out[mk.key] = text.slice(mk.end, i + 1 < marks.length ? marks[i + 1].start : undefined).trim();
    });
    return marks.length ? out : null;
}

function bulletsOf(t) {
    return t.split('\n').map(l => l.replace(/^\s*[-•*]\s*/, '').trim()).filter(Boolean);
}

function catClass(c) {
    const x = (c || '').toLowerCase();
    if (/work|job|career|business/.test(x)) return 'c-work';
    if (/personal|family|friend/.test(x)) return 'c-personal';
    if (/promo|market|offer|sale|ad/.test(x)) return 'c-promo';
    if (/financ|bill|bank|invoice|pay/.test(x)) return 'c-fin';
    if (/social|network/.test(x)) return 'c-social';
    if (/spam|phish|scam|suspic/.test(x)) return 'c-spam';
    return 'c-other';
}

function copyBtn(text, label) {
    return `<button class="mc-copy" data-copy="${encodeURIComponent(text)}" onclick="copyText(this)">${label || 'COPY'}</button>`;
}
function copyText(btn) {
    navigator.clipboard.writeText(decodeURIComponent(btn.dataset.copy)).then(() => {
        const old = btn.textContent; btn.textContent = 'COPIED ✓'; btn.classList.add('done');
        setTimeout(() => { btn.textContent = old; btn.classList.remove('done'); }, 1400);
    });
}

function mailHead(e) {
    const s = parseSender(e.from);
    const initial = (s.name.trim()[0] || '?').toUpperCase();
    return `
      <div class="mc-head">
        <div class="mc-avatar">${esc(initial)}</div>
        <div class="mc-who">
          <div class="mc-name">${esc(s.name)}</div>
          <div class="mc-addr">${esc(s.addr)}</div>
        </div>
        <div class="mc-meta"><span class="mc-num">EMAIL ${esc(e.number)}</span><span class="mc-date">${esc(e.date || '')}</span></div>
      </div>
      <div class="mc-subject">${esc(e.subject || '(NO SUBJECT)')}</div>`;
}

function renderReadCards(d) {
    let h = `<div class="mc-title"><i></i>LOADED ${d.count} EMAIL${d.count === 1 ? '' : 'S'}</div><div class="mc-list">`;
    d.emails.forEach(e => {
        h += `<article class="mail-card">${mailHead(e)}
          <div class="mc-section">
            <div class="mc-label">MESSAGE</div>
            <div class="mc-body">${esc(e.body || '').replace(/\n/g, '<br>')}</div>
          </div></article>`;
    });
    return h + '</div>';
}

function renderAnalysisCards(d) {
    let h = `<div class="mc-title"><i></i>AI ANALYSIS · ${d.results.length} EMAIL${d.results.length === 1 ? '' : 'S'}</div><div class="mc-list">`;
    d.results.forEach(e => {
        const p = parseAnalysis(e.summary || '');
        let inner = '';
        if (!p) {
            inner = `<div class="mc-section"><div class="mc-body">${esc(e.summary || '').replace(/\n/g, '<br>')}</div></div>`;
        } else {
            const cat = (p['CATEGORY'] || '').split('\n')[0].trim();
            const act = p['ACTION REQUIRED'] || '';
            const noAct = /no action|not need|not required|no need|none/i.test(act) && !/should not follow/i.test(act);
            const reply = (p['SUGGESTED REPLY'] || '').replace(/^\s*[-•*]\s*/, '').trim();
            const noReply = /^(no action|no reply|none|n\/a|there is no need)/i.test(reply) || !reply;
            if (cat) inner += `<div class="mc-badges"><span class="cat-badge ${catClass(cat)}">${esc(cat.toUpperCase())}</span>
                <span class="act-badge ${noAct ? 'ok' : 'warn'}">${noAct ? '✓ NO ACTION NEEDED' : '! ACTION NEEDED'}</span></div>`;
            if (p['SUMMARY']) inner += `<div class="mc-section"><div class="mc-label">SUMMARY</div><p class="mc-text">${esc(p['SUMMARY'])}</p></div>`;
            if (p['IMPORTANT POINTS']) inner += `<div class="mc-section"><div class="mc-label">IMPORTANT POINTS</div>
                <ul class="mc-points">${bulletsOf(p['IMPORTANT POINTS']).map(b => `<li>${esc(b)}</li>`).join('')}</ul></div>`;
            if (act && !noAct) inner += `<div class="mc-section"><div class="mc-label">ACTION REQUIRED</div>
                <ul class="mc-points warn">${bulletsOf(act).map(b => `<li>${esc(b)}</li>`).join('')}</ul></div>`;
            if (reply && !noReply) inner += `<div class="mc-section mc-reply"><div class="mc-label">SUGGESTED REPLY ${copyBtn(reply)}</div>
                <div class="mc-quote">${esc(reply).replace(/\n/g, '<br>')}</div></div>`;
        }
        h += `<article class="mail-card">${mailHead(e)}${inner}</article>`;
    });
    return h + '</div>';
}

function renderDraftCard(d, recipient) {
    const full = `SUBJECT: ${d.subject}\n\n${d.body}`;
    const saved = d.saved && d.draft_id;
    return `<div class="mc-title"><i></i>EMAIL DRAFT</div>
      <article class="mail-card draft">
        <div class="mc-badges">
          <span class="act-badge ${saved ? 'ok' : 'warn'}">${saved ? '✓ SAVED TO GMAIL DRAFTS' : 'NOT SAVED — COPY MANUALLY'}</span>
          <span class="cat-badge c-other">NOT SENT</span>
        </div>
        <div class="mc-field"><span>TO</span><b>${esc(recipient)}</b></div>
        <div class="mc-field"><span>SUBJECT</span><b>${esc(d.subject)}</b>${copyBtn(d.subject)}</div>
        <div class="mc-section"><div class="mc-label">BODY ${copyBtn(d.body)}</div>
          <div class="mc-quote">${esc(d.body).replace(/\n/g, '<br>')}</div></div>
        <div class="mc-foot">${copyBtn(full, 'COPY ALL')}${saved ? `<span class="mc-id">DRAFT ID · ${esc(d.draft_id)}</span>` : ''}</div>
      </article>`;
}

// ─── FILE ───
fileInput.addEventListener('change', async () => {
    const f = fileInput.files[0];
    if (!f) return;
    const fd = new FormData();
    fd.append('file', f);
    try {
        const r = await fetch('/api/upload', { method: 'POST', body: fd });
        const d = await r.json();
        if (d.error) throw new Error(d.error);
        attached = { name: d.filename, content: d.content };
        fileChip.style.display = 'flex';
        fileChip.innerHTML = `📎 ${d.filename}${d.truncated ? ' (TRUNCATED)' : ''} <button onclick="removeFile()">×</button>`;
        input.placeholder = 'ASK ABOUT THIS FILE...';
        input.focus();
    } catch (e) {
        alert('UPLOAD FAILED: ' + e.message);
    }
    fileInput.value = '';
});

function removeFile() {
    attached = null;
    fileChip.style.display = 'none';
    input.placeholder = gmailMode ? 'GMAIL SELECTION MODE' : 'MESSAGE...';
}

function setupDragDrop() {
    const wrap = document.body;
    wrap.addEventListener('dragover', e => { e.preventDefault(); });
    wrap.addEventListener('drop', e => {
        e.preventDefault();
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });
}

// ─── WEB SEARCH TOGGLE ───
function toggleWeb() {
    if (gmailMode) return; // disabled in gmail selection mode
    webMode = !webMode;
    webBtn.classList.toggle('on', webMode);
    webChip.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg> WEB SEARCH ON <button onclick="toggleWeb()">×</button>';
    webChip.style.display = webMode ? 'flex' : 'none';
    input.placeholder = webMode ? 'WEB CONNECTED (TAVILY)' : 'MESSAGE...';
    input.focus();
}

// ─── SEND ───
function handleSendClick() {
    if (generating) {
        if (ctrl) ctrl.abort();
        return;
    }
    if (gmailMode) return; // free message disabled in gmail mode
    send();
}

function setSendingState(on) {
    generating = on;
    sendBtn.classList.toggle('stopping', on);
    sendBtn.title = on ? 'STOP GENERATING' : 'SEND';
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

    const status = document.createElement('div');
    status.className = 'web-status';
    status.style.display = 'none';

    let full = '', first = true;
    try {
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text || `ANALYZE THIS FILE: ${attached?.name || ''}`,
                file_content: attached?.content || '',
                file_name: attached?.name || '',
                model: selectedModel || undefined,
                web_search: webMode
            }),
            signal: ctrl.signal
        });
        if (!r.ok) throw new Error('FAILED');

        const reader = r.body.getReader();
        const dec = new TextDecoder();
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            let chunk = dec.decode(value, { stream: true });

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
        if (e.name === 'AbortError') body.innerHTML = md(full + '\n\n_STOPPED_');
        else body.innerHTML = `<span style="color:var(--danger)">ERROR: ${e.message}</span>`;
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

// ─── MARKDOWN ───
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
    return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function scroll() {
    chatScroll.scrollTop = chatScroll.scrollHeight;
}

function resize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendClick();
    }
}

function newChat() {
    msgs.innerHTML = '';
    msgs.style.display = 'none';
    msgs.classList.remove('on');
    welcome.style.display = 'flex';
    attached = null;
    fileChip.style.display = 'none';
    input.value = '';
    input.focus();
}

function clearChat() {
    newChat();
}

function toggleShortcuts() {
    $('shortcutsModal').classList.toggle('open');
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && generating && ctrl) ctrl.abort();
    else if (e.key === 'Escape' && gmailMode) exitGmailMode();
    if (e.ctrlKey && e.shiftKey && e.key === 'N') { e.preventDefault(); newChat(); }
    if (e.ctrlKey && e.key === 'l') { e.preventDefault(); clearChat(); }
});
