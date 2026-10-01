(() => {
  const style = document.createElement('style');
  style.textContent = `
    .ig-actions{display:flex;gap:7px;margin-top:10px;align-items:center}.ig-connect{border:1px solid rgba(88,186,255,.27);background:rgba(88,186,255,.13);color:#fff;border-radius:10px;padding:8px 10px;cursor:pointer}.ig-connect:hover{background:rgba(88,186,255,.19)}.ig-state{display:inline-flex;align-items:center;gap:6px}.ig-state-dot{width:7px;height:7px;border-radius:50%;background:#ffbf69}.ig-state.connected .ig-state-dot{background:#45d58a}.ig-state.temporary .ig-state-dot{background:#58baff}.ig-help{font-size:11px;color:#8fa5ba;margin-top:8px;line-height:1.5}.ig-modal-wrap{position:fixed;inset:0;display:grid;place-items:center;background:rgba(2,8,14,.62);backdrop-filter:blur(8px);opacity:0;pointer-events:none;transition:.18s;z-index:60;padding:20px}.ig-modal-wrap.open{opacity:1;pointer-events:auto}.ig-modal{width:min(430px,100%);border:1px solid rgba(255,255,255,.13);border-radius:20px;background:linear-gradient(180deg,rgba(18,36,57,.99),rgba(9,22,36,.99));padding:18px;box-shadow:0 24px 70px rgba(0,0,0,.35)}.ig-modal h4{font-size:18px;margin:0 0 6px}.ig-modal p{font-size:12px;color:#8fa5ba;margin:0 0 14px;line-height:1.55}.ig-input{width:100%;border:1px solid rgba(255,255,255,.08);border-radius:11px;background:rgba(255,255,255,.045);color:#eef5ff;padding:10px;outline:none}.ig-input:focus{border-color:rgba(88,186,255,.35)}.ig-note{margin-top:9px;padding:9px 10px;border:1px solid rgba(255,255,255,.07);border-radius:11px;background:rgba(255,255,255,.025);font-size:11px;color:#8fa5ba}.ig-modal-actions{display:flex;justify-content:flex-end;gap:7px;margin-top:12px}.ig-btn{border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.045);color:#dce8f3;border-radius:10px;padding:8px 10px;cursor:pointer}.ig-btn.primary{border-color:rgba(88,186,255,.27);background:rgba(88,186,255,.14);color:#fff}.ig-spinner{display:none;margin-left:7px}.ig-loading .ig-spinner{display:inline}.ig-step{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:#7890a6;margin-bottom:5px}`;
  document.head.appendChild(style);

  const card = [...document.querySelectorAll('.connection-card')].find(el => el.textContent.includes('Technical account'));
  if (!card) return;

  card.innerHTML = `
    <div class="connection-top"><strong>Instagram</strong><span id="igStatus" class="ig-state"><span class="ig-state-dot"></span><span>Checking…</span></span></div>
    <div class="connection-copy" id="igCopy">Checking collector connection.</div>
    <div class="ig-actions"><button class="ig-connect" id="igConnectBtn">Connect Instagram</button></div>
    <div class="ig-help">Use a dedicated technical account. Echo never asks you to paste the session into this chat.</div>`;

  const modal = document.createElement('div');
  modal.className = 'ig-modal-wrap';
  modal.id = 'igModal';
  modal.innerHTML = `<div class="ig-modal">
    <div class="ig-step">Instagram connection</div>
    <h4>Connect a technical account</h4>
    <p>Paste a valid Instagram session ID from the dedicated account. Echo will validate it directly against Instagram. Your Instagram password is not entered here.</p>
    <input class="ig-input" id="igSessionInput" type="password" placeholder="Instagram session ID" autocomplete="off">
    <div class="ig-note">For now, validation creates a temporary collector session. Durable automatic monitoring uses the encrypted Vault connection prepared for Echo.</div>
    <div class="ig-modal-actions"><button class="ig-btn" id="igCancel">Cancel</button><button class="ig-btn primary" id="igValidate">Validate & connect <span class="ig-spinner">…</span></button></div>
  </div>`;
  document.body.appendChild(modal);

  const statusEl = document.getElementById('igStatus');
  const copyEl = document.getElementById('igCopy');
  const connectBtn = document.getElementById('igConnectBtn');
  const input = document.getElementById('igSessionInput');
  const validateBtn = document.getElementById('igValidate');

  function setStatus(status) {
    statusEl.className = 'ig-state ' + status;
    if (status === 'connected') {
      statusEl.lastElementChild.textContent = 'Connected';
      copyEl.textContent = 'Encrypted session available to the automatic collector.';
      connectBtn.textContent = 'Reconnect';
    } else if (status === 'temporary') {
      statusEl.lastElementChild.textContent = 'Temporary';
      copyEl.textContent = 'Session validated on the current collector instance.';
      connectBtn.textContent = 'Reconnect';
    } else {
      statusEl.lastElementChild.textContent = 'Not connected';
      copyEl.textContent = 'Connect a dedicated Instagram technical account to start collecting public posts.';
      connectBtn.textContent = 'Connect Instagram';
    }
  }

  async function loadStatus() {
    try {
      const r = await fetch('/echo/instagram/status');
      if (!r.ok) throw new Error();
      const d = await r.json();
      setStatus(d.status || 'disconnected');
    } catch (_) { setStatus('disconnected'); }
  }

  function openModal() { modal.classList.add('open'); setTimeout(() => input.focus(), 80); }
  function closeModal() { modal.classList.remove('open'); input.value = ''; }
  connectBtn.addEventListener('click', openModal);
  document.getElementById('igCancel').addEventListener('click', closeModal);
  modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

  validateBtn.addEventListener('click', async () => {
    const sessionid = input.value.trim();
    if (!sessionid) return;
    validateBtn.classList.add('ig-loading');
    validateBtn.disabled = true;
    try {
      const form = new FormData();
      form.append('sessionid', sessionid);
      const r = await fetch('/auth/login/by/sessionid', { method: 'POST', body: form });
      if (!r.ok) throw new Error('Instagram rejected this session.');
      const result = await r.json();
      if (!result) throw new Error('Instagram session is not valid.');
      sessionStorage.setItem('echoInstagramSession', String(result));
      closeModal();
      setStatus('temporary');
      if (typeof toast === 'function') toast('Instagram session validated');
    } catch (e) {
      if (typeof toast === 'function') toast(e.message || 'Could not connect Instagram');
    } finally {
      validateBtn.classList.remove('ig-loading');
      validateBtn.disabled = false;
    }
  });

  loadStatus();
})();
