/* ================================================================
   BerrAI – Personal AI Agent  |  Frontend Application Logic
   ================================================================ */

// ── State ──────────────────────────────────────────────────────────
const state = {
  authenticated: false,
  isLoading: false,
  sessionId: 'session_' + Date.now(),
  recognition: null,
  isRecording: false,
  isCancelling: false,
  isPaused: false,
};

// ── DOM Elements ───────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const chatArea = $('chat-area');
const chatMessages = $('chat-messages');
const welcomeScreen = $('welcome-screen');
const messageInput = $('message-input');
const btnSend = $('btn-send');
const btnVoice = $('btn-voice');
const voiceOverlay = $('voice-overlay');
const voiceTranscript = $('voice-transcript');
const statusDot = $('status-dot');
const statusText = $('status-text');
const btnAuthText = $('btn-auth-text');
const btnAuth = $('btn-auth');
const bgParticles = $('bg-particles');

// ── Initialize ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkAuthStatus();
  initParticles();
  initSpeechRecognition();
});

// ── Auth ───────────────────────────────────────────────────────────
async function checkAuthStatus() {
  try {
    const res = await fetch('/auth/status');
    const data = await res.json();
    state.authenticated = data.authenticated;
    updateAuthUI();
  } catch (err) {
    console.error('Auth check failed:', err);
    statusText.textContent = 'Bağlantı hatası';
  }
}

function updateAuthUI() {
  if (state.authenticated) {
    statusDot.classList.add('connected');
    statusText.textContent = 'Google hesabı bağlı';
    btnAuthText.textContent = 'Bağlantıyı Kes';
    btnAuth.classList.add('logout');
  } else {
    statusDot.classList.remove('connected');
    statusText.textContent = 'Bağlı değil';
    btnAuthText.textContent = 'Google ile Bağlan';
    btnAuth.classList.remove('logout');
  }
}

async function handleAuth() {
  if (state.authenticated) {
    // Logout
    try {
      await fetch('/auth/logout', { method: 'POST' });
      state.authenticated = false;
      updateAuthUI();
      showToast('Bağlantı kesildi', 'info');
    } catch (err) {
      showToast('Çıkış yapılamadı', 'error');
    }
  } else {
    // Login – redirect to Google
    window.location.href = '/auth/login';
  }
}

// ── Chat ───────────────────────────────────────────────────────────
async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || state.isLoading) return;

  // Hide welcome, show messages
  welcomeScreen.style.display = 'none';
  chatMessages.style.display = 'flex';

  // Add user message
  addMessage(text, 'user');
  messageInput.value = '';
  autoResize(messageInput);
  toggleSendBtn();

  // Show typing indicator
  const typingId = showTyping();

  state.isLoading = true;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        session_id: state.sessionId,
      }),
    });

    const data = await res.json();
    removeTyping(typingId);
    addMessage(data.reply, 'assistant');
  } catch (err) {
    removeTyping(typingId);
    addMessage('❌ Bağlantı hatası oluştu. Lütfen tekrar deneyin.', 'assistant');
    showToast('Sunucu bağlantı hatası', 'error');
  }

  state.isLoading = false;
}

function sendQuickAction(text) {
  messageInput.value = text;
  toggleSendBtn();
  sendMessage();
}

function addMessage(content, role) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}`;

  const avatar = role === 'assistant' ? '🤖' : '👤';
  const time = new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });

  msgDiv.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-content">
      <div class="message-bubble">${role === 'assistant' ? renderMarkdown(content) : escapeHtml(content)}</div>
      <div class="message-time">${time}</div>
    </div>
  `;

  chatMessages.appendChild(msgDiv);
  scrollToBottom();
}

function showTyping() {
  const id = 'typing-' + Date.now();
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message assistant';
  msgDiv.id = id;
  msgDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <div class="message-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  chatMessages.appendChild(msgDiv);
  scrollToBottom();
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

async function clearChat() {
  try {
    await fetch(`/api/chat/clear?session_id=${state.sessionId}`, { method: 'POST' });
    chatMessages.innerHTML = '';
    chatMessages.style.display = 'none';
    welcomeScreen.style.display = 'flex';
    showToast('Sohbet temizlendi', 'info');
  } catch (err) {
    showToast('Sohbet temizlenemedi', 'error');
  }
}

function scrollToBottom() {
  chatArea.scrollTo({ top: chatArea.scrollHeight, behavior: 'smooth' });
}

// ── Voice Recognition ──────────────────────────────────────────────
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    btnVoice.style.display = 'none';
    console.warn('Web Speech API not supported');
    return;
  }

  state.recognition = new SpeechRecognition();
  state.recognition.lang = 'tr-TR';
  state.recognition.continuous = true;
  state.recognition.interimResults = true;

  state.recognition.onresult = (event) => {
    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];
      if (result.isFinal) {
        finalTranscript += result[0].transcript;
      } else {
        interimTranscript += result[0].transcript;
      }
    }

    if (finalTranscript) {
      const current = messageInput.value.trim();
      messageInput.value = current ? current + ' ' + finalTranscript.trim() : finalTranscript.trim();
      toggleSendBtn();
    }

    // Modal üzerindeki yazıya eski metinleri de dahil et
    const fullText = (messageInput.value.trim() + ' ' + interimTranscript).trim();
    voiceTranscript.textContent = fullText || '…';
  };

  state.recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    if (event.error !== 'no-speech' && event.error !== 'aborted') {
      showToast('Ses algılama hatası: ' + event.error, 'error');
    }
    // Sadece error olduğunda tamamen kapatmıyoruz, belki pausedır diye
    if (!state.isPaused && !state.isCancelling) {
      cancelVoice();
    }
  };

  state.recognition.onend = () => {
    if (state.isCancelling) return;

    if (state.isPaused) {
      // Just stopped for pausing, do nothing
      return;
    }

    if (state.isRecording) {
      // If still recording and not paused, restart (continuous listening hack)
      try { state.recognition.start(); } catch (e) { }
    } else {
      // Not recording anymore, not paused, not cancelling -> shouldn't automatically send unless we explicitly call sendVoiceMessage,
      // but to keep the previous "background close" auto-send logic we check if there's text
      setTimeout(() => {
        if (state.isCancelling || state.isPaused) return;
        const text = messageInput.value.trim();
        if (text && !state.isLoading) {
          sendMessage();
        }
      }, 200);
    }
  };
}

function toggleVoice() {
  if (state.isRecording) {
    // If background clicked or button clicked again while active, let's treat it as send to close it
    sendVoiceMessage();
  } else {
    startVoice();
  }
}

function startVoice() {
  if (!state.recognition) {
    showToast('Tarayıcınız ses algılamayı desteklemiyor', 'error');
    return;
  }

  state.isCancelling = false;
  state.isRecording = true;
  state.isPaused = false;

  if ($('btn-voice-control')) {
    $('btn-voice-control').textContent = 'Duraklat';
  }
  const visualizer = document.querySelector('.voice-visualizer');
  if (visualizer) visualizer.style.animationPlayState = 'running';
  const title = document.querySelector('.voice-modal h3');
  if (title) title.textContent = 'Dinliyorum…';

  messageInput.value = ''; // clear previous transcript
  btnVoice.classList.add('recording');
  voiceOverlay.classList.add('active');
  voiceTranscript.textContent = '…';

  try {
    state.recognition.start();
  } catch (e) {
    console.error('Could not start recognition:', e);
  }
}

function toggleVoiceRecording() {
  if (!state.isRecording) return;

  const btn = $('btn-voice-control');
  const visualizer = document.querySelector('.voice-visualizer');
  const title = document.querySelector('.voice-modal h3');

  if (state.isPaused) {
    // Resume
    state.isPaused = false;
    if (btn) btn.textContent = 'Duraklat';
    if (visualizer) visualizer.style.animationPlayState = 'running';
    if (title) title.textContent = 'Dinliyorum…';
    try { state.recognition.start(); } catch (e) { }
  } else {
    // Pause
    state.isPaused = true;
    if (btn) btn.textContent = 'Devam Et';
    if (visualizer) visualizer.style.animationPlayState = 'paused';
    if (title) title.textContent = 'Duraklatıldı';
    try { state.recognition.stop(); } catch (e) { }
  }
}

function sendVoiceMessage() {
  if (state.isCancelling) return;

  state.isRecording = false;
  state.isPaused = false;
  btnVoice.classList.remove('recording');
  voiceOverlay.classList.remove('active');

  // If there's an interim transcript not finalized yet, grab it from voiceTranscript if it hasn't been appended to messageInput
  // Actually, voiceTranscript.textContent has the full text reliably now.
  let finalFullText = voiceTranscript.textContent !== '…' ? voiceTranscript.textContent : '';
  if (finalFullText) {
    messageInput.value = finalFullText;
  }

  if (state.recognition) {
    try { state.recognition.stop(); } catch (e) { }
  }

  // Birazcık bekle (stop events ateşlensin diye), sonrasında gönder
  setTimeout(() => {
    if (state.isCancelling) return;
    const text = messageInput.value.trim();
    if (text && !state.isLoading) {
      sendMessage();
    }
  }, 100);
}

function cancelVoice() {
  state.isCancelling = true;
  state.isRecording = false;
  state.isPaused = false;
  btnVoice.classList.remove('recording');
  voiceOverlay.classList.remove('active');

  messageInput.value = '';
  voiceTranscript.textContent = '…';
  toggleSendBtn();

  if (state.recognition) {
    try { state.recognition.stop(); } catch (e) { }
  }
}

// ── Input Helpers ──────────────────────────────────────────────────
function handleKeyDown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function toggleSendBtn() {
  const hasText = messageInput.value.trim().length > 0;
  btnSend.classList.toggle('active', hasText);
}

// ── Sidebar Toggle (mobile) ───────────────────────────────────────
function toggleSidebar() {
  const sidebar = $('sidebar');
  sidebar.classList.toggle('open');
}

// ── Toast Notifications ────────────────────────────────────────────
function showToast(message, type = 'info') {
  const container = $('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ── Markdown Renderer ──────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return '';

  let html = escapeHtml(text);

  // Code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Headers
  html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // Auto-link raw URLs that are not already in an href attribute
  html = html.replace(/(^|[^"'])(https?:\/\/[^\s<]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');

  // Unordered lists
  html = html.replace(/^\s*[-*] (.*$)/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

  // Numbered lists
  html = html.replace(/^\s*\d+\. (.*$)/gm, '<li>$1</li>');

  // Blockquotes
  html = html.replace(/^&gt; (.*$)/gm, '<blockquote>$1</blockquote>');

  // Tables
  html = html.replace(/(?:^\|.*\|\n?)+/gm, (match) => {
    const rows = match.trim().split('\n');
    let head = '';
    let body = '';

    rows.forEach((row, i) => {
      // Ignore separator rows (e.g. |---|---|)
      if (/^\|[\s-:]+\|$/.test(row.trim())) return;

      const cols = row.split('|').slice(1, -1).map(c => c.trim());
      const isHeader = i === 0;

      let rowHtml = '<tr>' + cols.map(c => `<${isHeader ? 'th' : 'td'}>${c}</${isHeader ? 'th' : 'td'}>`).join('') + '</tr>';

      if (isHeader) {
        head += rowHtml;
      } else {
        body += rowHtml;
      }
    });

    return `<div class="table-container"><table><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
  });

  // Paragraphs (double newlines)
  html = html.replace(/\n\n/g, '</p><p>');
  html = html.replace(/\n/g, '<br>');

  // Wrap in paragraph if needed
  if (!html.startsWith('<')) {
    html = '<p>' + html + '</p>';
  }

  return html;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── Background Particles ───────────────────────────────────────────
function initParticles() {
  const count = 30;
  for (let i = 0; i < count; i++) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.left = Math.random() * 100 + '%';
    particle.style.top = Math.random() * 100 + '%';
    particle.style.animationDelay = Math.random() * 6 + 's';
    particle.style.animationDuration = 4 + Math.random() * 4 + 's';
    bgParticles.appendChild(particle);
  }
}
