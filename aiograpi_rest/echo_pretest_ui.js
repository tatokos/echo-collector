(() => {
  const style=document.createElement('style');
  style.textContent=`
    .workflow-filters{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}.workflow-btn,.signal-action{border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.035);color:#9fb3c5;border-radius:999px;padding:6px 9px;font-size:10px;cursor:pointer}.workflow-btn.active{border-color:rgba(88,186,255,.28);background:rgba(88,186,255,.10);color:#d9efff}.signal-actions{display:flex;gap:6px;margin-top:10px;align-items:center}.signal-action:hover{background:rgba(255,255,255,.07);color:#eef5ff}.signal-action.active{border-color:rgba(69,213,138,.20);color:#b5f5d1}.signal-action.ignore.active{border-color:rgba(255,191,105,.20);color:#ffe0a8}.signal-status{font-size:10px;color:#71889c;margin-left:auto;text-transform:capitalize}.health-card{margin-top:10px;padding:11px;border:1px solid rgba(255,255,255,.08);border-radius:13px;background:rgba(255,255,255,.025)}.health-row{display:flex;justify-content:space-between;gap:12px;font-size:11px;padding:4px 0;color:#8fa5ba}.health-row strong{font-weight:600;color:#d8e5ef}.health-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px;background:#45d58a}.health-dot.caution{background:#ffbf69}.health-dot.paused{background:#ff7f8f}`;
  document.head.appendChild(style);

  let statusFilter='new';

  const weight=document.getElementById('weightInput');
  if(weight){weight.min='-100';weight.max='100';weight.title='Positive weights boost relevance; negative weights reduce it.'}

  const toolbar=document.querySelector('.toolbar');
  if(toolbar){
    const holder=document.createElement('div');
    holder.className='workflow-filters';
    holder.innerHTML=`<button class="workflow-btn active" data-status="new">New</button><button class="workflow-btn" data-status="reviewed">Reviewed</button><button class="workflow-btn" data-status="ignored">Ignored</button><button class="workflow-btn" data-status="all">All states</button>`;
    toolbar.insertAdjacentElement('afterend',holder);
    holder.addEventListener('click',e=>{const b=e.target.closest('[data-status]');if(!b)return;statusFilter=b.dataset.status;holder.querySelectorAll('.workflow-btn').forEach(x=>x.classList.toggle('active',x===b));loadFeed();});
  }

  renderFeed=function(){
    const q=document.getElementById('searchInput').value.trim().toLowerCase();
    const items=feedItems.filter(p=>!q||`${p.username||''} ${p.caption||''} ${p.reason||''}`.toLowerCase().includes(q));
    const el=document.getElementById('feed');
    if(!items.length){el.innerHTML='<div class="empty"><strong>No matching signals</strong>Try another filter or search term.</div>';return}
    el.innerHTML=items.map(p=>{
      const tokens=reasonTokens(p.reason);
      const media=p.thumbnail_url?`<img class="thumb" src="${esc(p.thumbnail_url)}" alt="">`:'<div class="thumb placeholder">◎</div>';
      const why=tokens.length?tokens.map(t=>`<span class="reason-chip">${esc(t)}</span>`).join(''):`<span class="reason-fallback">${esc(p.reason||'No configured signal matched')}</span>`;
      const reviewed=p.status==='reviewed',ignored=p.status==='ignored';
      return `<article class="signal"><div class="thumb-wrap"><a class="signal-link" href="${esc(p.permalink||'#')}" target="_blank" rel="noopener">${media}</a></div><div class="signal-main"><div class="signal-top"><div><a class="signal-link" href="${esc(p.permalink||'#')}" target="_blank" rel="noopener"><div class="account">@${esc(p.username)}</div></a><div class="meta">${p.published_at?new Date(p.published_at).toLocaleString():''}</div></div><div class="score-box"><span class="badge ${esc(p.relevance)}">${esc(p.relevance)}</span><div class="score-num">${Number(p.relevance_score||0)}/100</div></div></div><div class="caption">${esc(p.caption||'No caption')}</div><div class="why"><div class="why-title">Why Echo flagged this</div><div class="reason-chips">${why}</div></div><div class="signal-actions"><button class="signal-action ${reviewed?'active':''}" onclick="setPostStatus('${p.id}','reviewed')">✓ Review</button><button class="signal-action ignore ${ignored?'active':''}" onclick="setPostStatus('${p.id}','ignored')">Ignore</button><span class="signal-status">${esc(p.status||'new')}</span></div></div></article>`;
    }).join('');
  };

  loadFeed=async function(){
    try{
      const params=new URLSearchParams();
      if(currentFilter!=='ALL')params.set('relevance',currentFilter);
      if(statusFilter!=='all')params.set('status',statusFilter);
      const d=await api('/echo/feed'+(params.toString()?`?${params}`:''));
      feedItems=d.items||[];renderFeed();document.getElementById('statusText').textContent='Live';
    }catch(e){document.getElementById('statusText').textContent='Unavailable';toast(e.message)}
  };

  window.setPostStatus=async function(id,status){
    if(!requireAdmin())return;
    try{await api(`/echo/posts/${id}/status`,{method:'PATCH',headers:adminHeaders(),body:JSON.stringify({status})});await loadFeed();toast(status==='reviewed'?'Marked as reviewed':'Ignored')}catch(e){toast(e.message)}
  };

  const connection=document.querySelector('.connection-card');
  if(connection){
    const health=document.createElement('div');health.className='health-card';health.id='echoHealthCard';health.innerHTML='<div class="health-row"><span>Safe Collection</span><strong>Loading…</strong></div>';connection.insertAdjacentElement('afterend',health);
  }

  async function loadHealth(){
    const el=document.getElementById('echoHealthCard');if(!el)return;
    try{
      const r=await fetch('/echo/instagram/status',{cache:'no-store'});const d=await r.json();const h=d.health||{};const state=(h.state||'healthy').toLowerCase();
      const last=h.last_success_at?relativeTime(h.last_success_at):'No scan yet';const requests=Number(h.requests_last_run||0);
      el.innerHTML=`<div class="health-row"><span>Status</span><strong><span class="health-dot ${state}"></span>${state.charAt(0).toUpperCase()+state.slice(1)}</strong></div><div class="health-row"><span>Safe Collection</span><strong>${h.safe_mode===false?'OFF':'ON'}</strong></div><div class="health-row"><span>Last successful scan</span><strong>${esc(last)}</strong></div><div class="health-row"><span>Requests last run</span><strong>${requests}</strong></div>`;
    }catch(_){el.innerHTML='<div class="health-row"><span>Health</span><strong>Unavailable</strong></div>'}
  }

  loadFeed();loadHealth();setInterval(loadHealth,60000);
})();
