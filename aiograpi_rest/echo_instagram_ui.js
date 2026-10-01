(() => {
  const style = document.createElement('style');
  style.textContent = `
    .ig-actions{display:flex;gap:7px;margin-top:10px;align-items:center}.ig-connect{border:1px solid rgba(88,186,255,.27);background:rgba(88,186,255,.13);color:#fff;border-radius:10px;padding:8px 10px;cursor:pointer}.ig-connect:hover{background:rgba(88,186,255,.19)}.ig-state{display:inline-flex;align-items:center;gap:6px}.ig-state-dot{width:7px;height:7px;border-radius:50%;background:#ffbf69}.ig-state.connected .ig-state-dot{background:#45d58a}.ig-help{font-size:11px;color:#8fa5ba;margin-top:8px;line-height:1.5}.ig-modal-wrap{position:fixed;inset:0;display:grid;place-items:center;background:rgba(2,8,14,.62);backdrop-filter:blur(8px);opacity:0;pointer-events:none;transition:.18s;z-index:60;padding:20px}.ig-modal-wrap.open{opacity:1;pointer-events:auto}.ig-modal{width:min(440px,100%);border:1px solid rgba(255,255,255,.13);border-radius:20px;background:linear-gradient(180deg,rgba(18,36,57,.99),rgba(9,22,36,.99));padding:18px;box-shadow:0 24px 70px rgba(0,0,0,.35)}.ig-modal h4{font-size:18px;margin:0 0 6px}.ig-modal p{font-size:12px;color:#8fa5ba;margin:0 0 14px;line-height:1.55}.ig-step{display:flex;gap:10px;padding:10px 0;border-top:1px solid rgba(255,255,255,.07)}.ig-step:first-of-type{border-top:0}.ig-num{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;background:rgba(88,186,255,.12);color:#bfe3ff;font-size:11px;flex:0 0 auto}.ig-step b{display:block;font-size:12px;margin-bottom:2px}.ig-step span{font-size:11px;color:#8fa5ba}.ig-modal-actions{display:flex;justify-content:flex-end;gap:7px;margin-top:14px}.ig-btn{border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.045);color:#dce8f3;border-radius:10px;padding:8px 10px;cursor:pointer}.ig-btn.primary{border-color:rgba(88,186,255,.27);background:rgba(88,186,255,.14);color:#fff}`;
  document.head.appendChild(style);

  const card = [...document.querySelectorAll('.connection-card')].find(el => el.textContent.includes('Technical account'));
  if (!card) return;

  card.innerHTML = `
    <div class="connection-top"><strong>Instagram</strong><span id="igStatus" class="ig-state"><span class="ig-state-dot"></span><span>Checking…</span></span></div>
    <div class="connection-copy" id="igCopy">Checking collector connection.</div>
    <div class="ig-actions"><button class="ig-connect" id="igConnectBtn">Connect Instagram</button></div>
    <div class="ig-help">Connection is configured privately on Render, so the Instagram session never passes through this chat or the Echo interface.</div>`;

  const modal = document.createElement('div');
  modal.className = 'ig-modal-wrap';
  modal.id = 'igModal';
  modal.innerHTML = `<div class="ig-modal">
    <h4>Connect Instagram</h4>
    <p>Use a dedicated technical account. The safest setup keeps the Instagram session only in Render's private environment variables.</p>
    <div class="ig-step"><div class="ig-num">1</div><div><b>Create or use a technical Instagram account</b><span>A separate account is recommended instead of a personal profile.</span></div></div>
    <div class="ig-step"><div class="ig-num">2</div><div><b>Add the session privately in Render</b><span>Open the Echo service Environment section and add <strong>INSTAGRAM_SESSION_ID</strong>. Do not paste the value into this chat.</span></div></div>
    <div class="ig-step"><div class="ig-num">3</div><div><b>Return to Echo</b><span>Refresh this page. Echo will detect the connection automatically and the hourly scheduler can use it.</span></div></div>
    <div class="ig-modal-actions"><button class="ig-btn" id="igClose">Close</button><a class="ig-btn primary" href="https://dashboard.render.com/web/srv-dat7cibncjis73ddh79g" target="_blank" rel="noopener" style="text-decoration:none">Open Render</a></div>
  </div>`;
  document.body.appendChild(modal);

  const statusEl = document.getElementById('igStatus');
  const copyEl = document.getElementById('igCopy');
  const connectBtn = document.getElementById('igConnectBtn');

  function setStatus(connected) {
    statusEl.className = 'ig-state' + (connected ? ' connected' : '');
    statusEl.lastElementChild.textContent = connected ? 'Connected' : 'Not connected';
    copyEl.textContent = connected ? 'Technical account session detected. Automatic monitoring is ready.' : 'Connect a technical Instagram account to enable automatic collection.';
    connectBtn.textContent = connected ? 'Connection settings' : 'Connect Instagram';
  }

  async function loadStatus() {
    try {
      const r = await fetch('/echo/instagram/status', {cache:'no-store'});
      if (!r.ok) throw new Error();
      const d = await r.json();
      setStatus(!!d.configured);
    } catch (_) { setStatus(false); }
  }

  connectBtn.addEventListener('click', () => modal.classList.add('open'));
  document.getElementById('igClose').addEventListener('click', () => modal.classList.remove('open'));
  modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('open'); });
  loadStatus();
})();
