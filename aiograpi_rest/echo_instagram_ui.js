(() => {
  const style = document.createElement('style');
  style.textContent = `
    .ig-actions{display:flex;gap:7px;margin-top:10px;align-items:center}.ig-connect{border:1px solid rgba(88,186,255,.27);background:rgba(88,186,255,.13);color:#fff;border-radius:10px;padding:8px 10px;cursor:pointer}.ig-connect:hover{background:rgba(88,186,255,.19)}.ig-state{display:inline-flex;align-items:center;gap:6px}.ig-state-dot{width:7px;height:7px;border-radius:50%;background:#ffbf69}.ig-state.connected .ig-state-dot{background:#45d58a}.ig-help{font-size:11px;color:#8fa5ba;margin-top:8px;line-height:1.5}.ig-modal-wrap{position:fixed;inset:0;display:grid;place-items:center;background:rgba(2,8,14,.62);backdrop-filter:blur(8px);opacity:0;pointer-events:none;transition:.18s;z-index:60;padding:20px}.ig-modal-wrap.open{opacity:1;pointer-events:auto}.ig-modal{width:min(470px,100%);max-height:92vh;overflow:auto;border:1px solid rgba(255,255,255,.13);border-radius:22px;background:linear-gradient(180deg,rgba(18,36,57,.99),rgba(9,22,36,.99));padding:19px;box-shadow:0 24px 70px rgba(0,0,0,.35)}.ig-modal-head{display:flex;justify-content:space-between;gap:14px}.ig-modal h4{font-size:19px;margin:0 0 5px}.ig-modal p{font-size:12px;color:#8fa5ba;margin:0;line-height:1.55}.ig-x{border:0;background:transparent;color:#8197ab;font-size:22px;cursor:pointer;padding:0}.ig-progress{display:flex;gap:6px;margin:16px 0 18px}.ig-progress span{height:3px;flex:1;border-radius:99px;background:rgba(255,255,255,.07)}.ig-progress span.active{background:rgba(88,186,255,.55)}.ig-panel{display:none}.ig-panel.active{display:block}.ig-step-card{padding:13px;border:1px solid rgba(255,255,255,.07);border-radius:15px;background:rgba(255,255,255,.025);margin-top:10px}.ig-step-card b{display:block;font-size:12px;margin-bottom:4px}.ig-step-card span{font-size:11px;color:#8fa5ba;line-height:1.5}.ig-key{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:10px;padding:9px 10px;border:1px solid rgba(88,186,255,.14);border-radius:11px;background:rgba(88,186,255,.055)}.ig-key code{font-size:11px;color:#c5e7ff;overflow-wrap:anywhere}.ig-modal-actions{display:flex;justify-content:flex-end;gap:7px;margin-top:16px;flex-wrap:wrap}.ig-btn{border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.045);color:#dce8f3;border-radius:10px;padding:9px 11px;cursor:pointer;text-decoration:none}.ig-btn:hover{background:rgba(255,255,255,.075)}.ig-btn.primary{border-color:rgba(88,186,255,.27);background:rgba(88,186,255,.14);color:#fff}.ig-btn.primary:hover{background:rgba(88,186,255,.2)}.ig-btn:disabled{opacity:.55}.ig-success{display:flex;align-items:center;gap:10px;padding:12px;border-radius:14px;background:rgba(69,213,138,.07);border:1px solid rgba(69,213,138,.14);margin:10px 0}.ig-check{width:28px;height:28px;border-radius:50%;display:grid;place-items:center;background:rgba(69,213,138,.14);color:#8ef0ba;font-weight:800}.ig-error{display:none;margin-top:10px;padding:9px 10px;border-radius:11px;background:rgba(255,127,143,.08);border:1px solid rgba(255,127,143,.14);color:#ffb5bf;font-size:11px}.ig-error.show{display:block}`;
  document.head.appendChild(style);

  const card = [...document.querySelectorAll('.connection-card')].find(el => el.textContent.includes('Technical account'));
  if (!card) return;

  card.innerHTML = `
    <div class="connection-top"><strong>Instagram</strong><span id="igStatus" class="ig-state"><span class="ig-state-dot"></span><span>Checking…</span></span></div>
    <div class="connection-copy" id="igCopy">Checking collector connection.</div>
    <div class="ig-actions"><button class="ig-connect" id="igConnectBtn">Connect Instagram</button></div>
    <div class="ig-help">Guided setup. You will only leave Echo for the two private security steps.</div>`;

  const modal = document.createElement('div');
  modal.className = 'ig-modal-wrap';
  modal.id = 'igModal';
  modal.innerHTML = `<div class="ig-modal">
    <div class="ig-modal-head"><div><h4>Connect Instagram</h4><p id="igSubtitle">Three short steps. Echo tells you exactly what to click.</p></div><button class="ig-x" id="igClose">×</button></div>
    <div class="ig-progress"><span id="igP1" class="active"></span><span id="igP2"></span><span id="igP3"></span></div>

    <section class="ig-panel active" id="igPanel1">
      <div class="ig-step-card"><b>1. Generate the Instagram session</b><span>Open Echo's secure login helper. Click <strong>Try it out</strong>, enter the technical Instagram account, then <strong>Execute</strong>. Copy only the value shown in <strong>Response body</strong>.</span></div>
      <div class="ig-step-card"><b>Use a technical account</b><span>Do not use your main personal Instagram account. The login helper is part of Echo and the password is not sent to this chat.</span></div>
      <div class="ig-modal-actions"><button class="ig-btn" id="igCancel">Cancel</button><a class="ig-btn primary" id="igOpenLogin" href="/docs#/Auth/auth_login_auth_login_post" target="_blank" rel="noopener">Generate session</a></div>
    </section>

    <section class="ig-panel" id="igPanel2">
      <div class="ig-step-card"><b>2. Save it privately</b><span>Open the Echo service on Render. In the left menu choose <strong>Environment</strong> → <strong>Add Environment Variable</strong>.</span></div>
      <div class="ig-key"><code>INSTAGRAM_SESSION_ID</code><button class="ig-btn" id="igCopyKey">Copy key</button></div>
      <div class="ig-step-card"><b>Paste the session as the Value</b><span>Use the session you copied in step 1, then choose <strong>Save and deploy</strong>. You do not need to change the plan or buy anything.</span></div>
      <div class="ig-modal-actions"><button class="ig-btn" id="igBack1">Back</button><a class="ig-btn primary" id="igOpenRender" href="https://dashboard.render.com/web/srv-dat7cibncjis73ddh79g" target="_blank" rel="noopener">Open Environment settings</a></div>
    </section>

    <section class="ig-panel" id="igPanel3">
      <div class="ig-success"><div class="ig-check">✓</div><div><b>Final check</b><p>Return here after saving the variable and let Echo verify the connection.</p></div></div>
      <div class="ig-error" id="igCheckError"></div>
      <div class="ig-modal-actions"><button class="ig-btn" id="igBack2">Back</button><button class="ig-btn primary" id="igCheckBtn">Check connection</button></div>
    </section>
  </div>`;
  document.body.appendChild(modal);

  const statusEl = document.getElementById('igStatus');
  const copyEl = document.getElementById('igCopy');
  const connectBtn = document.getElementById('igConnectBtn');
  const checkError = document.getElementById('igCheckError');

  function setStep(n) {
    [1,2,3].forEach(i => {
      document.getElementById(`igPanel${i}`).classList.toggle('active', i === n);
      document.getElementById(`igP${i}`).classList.toggle('active', i <= n);
    });
  }

  function setStatus(connected) {
    statusEl.className = 'ig-state' + (connected ? ' connected' : '');
    statusEl.lastElementChild.textContent = connected ? 'Connected' : 'Not connected';
    copyEl.textContent = connected ? 'Instagram is connected. Automatic monitoring is ready.' : 'Connect a technical Instagram account to enable automatic collection.';
    connectBtn.textContent = connected ? 'Connection settings' : 'Connect Instagram';
  }

  async function loadStatus() {
    try {
      const r = await fetch('/echo/instagram/status', {cache:'no-store'});
      if (!r.ok) throw new Error();
      const d = await r.json();
      setStatus(!!d.configured);
      return !!d.configured;
    } catch (_) {
      setStatus(false);
      return false;
    }
  }

  function openModal() {
    checkError.classList.remove('show');
    setStep(statusEl.classList.contains('connected') ? 3 : 1);
    modal.classList.add('open');
  }

  function closeModal() { modal.classList.remove('open'); }

  connectBtn.addEventListener('click', openModal);
  document.getElementById('igClose').addEventListener('click', closeModal);
  document.getElementById('igCancel').addEventListener('click', closeModal);
  document.getElementById('igOpenLogin').addEventListener('click', () => setStep(2));
  document.getElementById('igOpenRender').addEventListener('click', () => setStep(3));
  document.getElementById('igBack1').addEventListener('click', () => setStep(1));
  document.getElementById('igBack2').addEventListener('click', () => setStep(2));
  document.getElementById('igCopyKey').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText('INSTAGRAM_SESSION_ID'); document.getElementById('igCopyKey').textContent='Copied'; setTimeout(()=>document.getElementById('igCopyKey').textContent='Copy key',1500); } catch (_) {}
  });
  document.getElementById('igCheckBtn').addEventListener('click', async () => {
    checkError.classList.remove('show');
    const ok = await loadStatus();
    if (ok) closeModal();
    else { checkError.textContent = 'Echo cannot see the connection yet. Check that the key is INSTAGRAM_SESSION_ID, the session is in Value, and you selected Save and deploy.'; checkError.classList.add('show'); }
  });
  modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
  loadStatus();
})();
