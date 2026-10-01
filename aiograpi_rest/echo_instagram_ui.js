(() => {
  const style = document.createElement('style');
  style.textContent = `
    .ig-actions{display:flex;gap:7px;margin-top:10px}.ig-connect{border:1px solid rgba(88,186,255,.27);background:rgba(88,186,255,.13);color:#fff;border-radius:10px;padding:8px 10px;cursor:pointer}.ig-state{display:inline-flex;align-items:center;gap:6px}.ig-state-dot{width:7px;height:7px;border-radius:50%;background:#ffbf69}.ig-state.connected .ig-state-dot,.ig-state.healthy .ig-state-dot{background:#45d58a}.ig-state.caution .ig-state-dot{background:#ffbf69}.ig-state.paused .ig-state-dot{background:#ff7f8f}.ig-help{font-size:11px;color:#8fa5ba;margin-top:8px;line-height:1.5}.ig-safe{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:10px;padding:8px 10px;border:1px solid rgba(255,255,255,.07);border-radius:11px;background:rgba(255,255,255,.025);font-size:11px;color:#8fa5ba}.ig-safe strong{color:#cfe0ee}.ig-modal-wrap{position:fixed;inset:0;display:grid;place-items:center;background:rgba(2,8,14,.62);backdrop-filter:blur(8px);opacity:0;pointer-events:none;transition:.18s;z-index:60;padding:20px}.ig-modal-wrap.open{opacity:1;pointer-events:auto}.ig-modal{width:min(430px,100%);border:1px solid rgba(255,255,255,.13);border-radius:22px;background:linear-gradient(180deg,rgba(18,36,57,.99),rgba(9,22,36,.99));padding:20px;box-shadow:0 24px 70px rgba(0,0,0,.35)}.ig-modal-head{display:flex;justify-content:space-between;gap:14px}.ig-modal h4{font-size:19px;margin:0 0 5px}.ig-modal p{font-size:12px;color:#8fa5ba;margin:0;line-height:1.55}.ig-x{border:0;background:transparent;color:#8197ab;font-size:22px;cursor:pointer;padding:0}.ig-form{display:grid;gap:10px;margin-top:18px}.ig-field{display:grid;gap:5px}.ig-field label{font-size:11px;color:#8fa5ba}.ig-input{width:100%;border:1px solid rgba(255,255,255,.09);border-radius:12px;background:rgba(255,255,255,.045);color:#eef5ff;padding:10px 11px;outline:none}.ig-input:focus{border-color:rgba(88,186,255,.35)}.ig-submit{border:1px solid rgba(88,186,255,.27);background:rgba(88,186,255,.14);color:#fff;border-radius:12px;padding:10px 12px;cursor:pointer;margin-top:4px}.ig-submit:disabled{opacity:.55}.ig-error{display:none;padding:9px 10px;border-radius:11px;background:rgba(255,127,143,.08);border:1px solid rgba(255,127,143,.14);color:#ffb5bf;font-size:11px}.ig-error.show{display:block}.ig-success{display:none;padding:12px;border-radius:14px;background:rgba(69,213,138,.07);border:1px solid rgba(69,213,138,.14);color:#b5f5d1;font-size:12px}.ig-success.show{display:block}.ig-hidden-frame{display:none}`;
  document.head.appendChild(style);

  const card = [...document.querySelectorAll('.connection-card')].find(el => el.textContent.includes('Technical account') || el.textContent.includes('Instagram'));
  if (!card) return;

  card.innerHTML = `
    <div class="connection-top"><strong>Instagram</strong><span id="igStatus" class="ig-state"><span class="ig-state-dot"></span><span>Checking…</span></span></div>
    <div class="connection-copy" id="igCopy">Checking Instagram connection.</div>
    <div class="ig-safe"><span>Safe Collection</span><strong id="igSafeMode">ON</strong></div>
    <div class="ig-actions"><button class="ig-connect" id="igConnectBtn">Connect Instagram</button></div>
    <div class="ig-help" id="igHealthHelp">Low-volume, read-only monitoring with automatic safety pauses.</div>`;

  const modal = document.createElement('div');
  modal.className = 'ig-modal-wrap';
  modal.innerHTML = `<div class="ig-modal">
    <div class="ig-modal-head"><div><h4>Connect Instagram</h4><p>Enter the technical account credentials and Echo will connect it.</p></div><button class="ig-x" id="igClose">×</button></div>
    <form class="ig-form" id="igLoginForm" action="/auth/login" method="post" target="igLoginFrame">
      <div class="ig-field"><label>Username</label><input class="ig-input" name="username" autocomplete="username" required></div>
      <div class="ig-field"><label>Password</label><input class="ig-input" name="password" type="password" autocomplete="current-password" required></div>
      <div class="ig-field" id="igCodeField" style="display:none"><label>Verification code</label><input class="ig-input" name="verification_code" inputmode="numeric" autocomplete="one-time-code"></div>
      <input type="hidden" name="proxy" value=""><input type="hidden" name="locale" value=""><input type="hidden" name="timezone" value="">
      <div class="ig-error" id="igError">Instagram did not accept the login. If Instagram sent you a verification code, enter it below and try again.</div>
      <div class="ig-success" id="igSuccess">Instagram connected successfully. Safe Collection is active.</div>
      <button class="ig-submit" id="igSubmit" type="submit">Connect</button>
    </form>
    <iframe class="ig-hidden-frame" name="igLoginFrame" id="igLoginFrame"></iframe>
  </div>`;
  document.body.appendChild(modal);

  const statusEl=document.getElementById('igStatus');
  const copyEl=document.getElementById('igCopy');
  const connectBtn=document.getElementById('igConnectBtn');
  const healthHelp=document.getElementById('igHealthHelp');
  const form=document.getElementById('igLoginForm');
  const frame=document.getElementById('igLoginFrame');
  const submit=document.getElementById('igSubmit');
  const error=document.getElementById('igError');
  const success=document.getElementById('igSuccess');
  const codeField=document.getElementById('igCodeField');

  function healthLabel(data){
    if(!data.configured)return 'Not connected';
    if(data.health==='paused')return 'Paused';
    if(data.health==='caution')return 'Caution';
    return 'Healthy';
  }

  function setStatus(data){
    const configured=!!data.configured;
    const health=data.health||'healthy';
    statusEl.className='ig-state '+(configured?health:'');
    statusEl.lastElementChild.textContent=healthLabel(data);
    connectBtn.textContent=configured?'Reconnect':'Connect Instagram';
    if(!configured){
      copyEl.textContent='Connect an Instagram account to enable automatic monitoring.';
      healthHelp.textContent='Low-volume, read-only monitoring with automatic safety pauses.';
      return;
    }
    if(health==='paused'){
      copyEl.textContent=data.requires_reconnect?'Monitoring stopped automatically. Reconnect Instagram before continuing.':'Monitoring is temporarily paused for safety.';
      healthHelp.textContent='Echo will not send Instagram requests while the safety pause is active.';
    }else if(health==='caution'){
      copyEl.textContent='Echo detected a suspicious response and slowed monitoring automatically.';
      healthHelp.textContent='Safe Collection is applying a cooldown before the next request.';
    }else{
      copyEl.textContent='Automatic monitoring is ready.';
      healthHelp.textContent=`Safe Collection ON · ${data.requests_last_run||0} collector requests in the last scan.`;
    }
  }

  async function loadStatus(){
    try{
      const r=await fetch('/echo/instagram/status',{cache:'no-store'});
      const d=await r.json();
      setStatus(d);
      return d;
    }catch(_){
      setStatus({configured:false,health:'healthy'});
      return {configured:false};
    }
  }

  connectBtn.onclick=()=>{error.classList.remove('show');success.classList.remove('show');modal.classList.add('open')};
  document.getElementById('igClose').onclick=()=>modal.classList.remove('open');
  modal.onclick=e=>{if(e.target===modal)modal.classList.remove('open')};
  form.addEventListener('submit',()=>{submit.disabled=true;submit.textContent='Connecting…';error.classList.remove('show');success.classList.remove('show')});
  frame.addEventListener('load',async()=>{
    if(!submit.disabled)return;
    await new Promise(r=>setTimeout(r,600));
    const state=await loadStatus();
    submit.disabled=false;
    submit.textContent='Connect';
    if(state.configured){
      try{await fetch('/echo/instagram/resume',{method:'POST'})}catch(_){}
      await loadStatus();
      success.classList.add('show');
      form.querySelector('[name=password]').value='';
      setTimeout(()=>modal.classList.remove('open'),900);
    }else{
      codeField.style.display='grid';
      error.classList.add('show');
    }
  });
  loadStatus();
})();
