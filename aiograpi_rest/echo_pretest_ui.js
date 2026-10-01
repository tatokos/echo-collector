(() => {
  const style = document.createElement('style');
  style.textContent = `
    :root{--echo-card-radius:24px;--echo-media-radius:18px;--echo-soft:rgba(255,255,255,.045);--echo-soft-2:rgba(255,255,255,.07)}
    .toolbar{margin-bottom:8px}
    .workflow-shell{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:4px 0 14px}
    .workflow-filters{display:flex;gap:6px;flex-wrap:wrap}
    .workflow-btn,.signal-action,.open-instagram{border:1px solid rgba(255,255,255,.075);background:rgba(255,255,255,.03);color:#94a9bc;border-radius:999px;padding:7px 10px;font-size:10.5px;font-weight:650;letter-spacing:.01em;cursor:pointer;transition:background .16s ease,border-color .16s ease,color .16s ease,transform .16s ease}
    .workflow-btn:hover,.signal-action:hover,.open-instagram:hover{background:rgba(255,255,255,.065);color:#f1f7fc;transform:translateY(-1px)}
    .workflow-btn.active{border-color:rgba(88,186,255,.3);background:rgba(88,186,255,.11);color:#dff2ff}
    .refresh-note{font-size:10.5px;color:#61788d;white-space:nowrap}
    .feed{gap:14px}
    .signal{position:relative;display:grid;grid-template-columns:minmax(190px,210px) minmax(0,1fr);gap:20px;padding:14px;border:1px solid rgba(255,255,255,.075);border-radius:var(--echo-card-radius);background:linear-gradient(145deg,rgba(17,35,55,.82),rgba(7,20,33,.8));box-shadow:0 18px 55px rgba(0,0,0,.16),inset 0 1px rgba(255,255,255,.025);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);overflow:hidden;transform:translateZ(0)}
    .signal::before{content:'';position:absolute;left:0;top:20px;bottom:20px;width:2px;border-radius:0 2px 2px 0;background:rgba(148,169,188,.22)}
    .signal[data-relevance="ALTA"]::before{background:rgba(69,213,138,.62)}
    .signal[data-relevance="MEDIA"]::before{background:rgba(255,191,105,.58)}
    .signal[data-relevance="BASSA"]::before{background:rgba(88,186,255,.5)}
    .signal:hover{border-color:rgba(255,255,255,.13);box-shadow:0 24px 68px rgba(0,0,0,.22),inset 0 1px rgba(255,255,255,.035);transform:translateY(-2px)}
    .thumb-wrap{position:relative;min-width:0}
    .media-link{display:block;position:relative;border-radius:var(--echo-media-radius);overflow:hidden;background:linear-gradient(145deg,#142a43,#0b1b2c);aspect-ratio:1/1;outline:none}
    .media-link:focus-visible{box-shadow:0 0 0 3px rgba(88,186,255,.22)}
    .thumb{width:100%;height:100%;border-radius:0;object-fit:cover;transition:transform .28s ease,filter .28s ease}
    .media-link:hover .thumb{transform:scale(1.025);filter:brightness(1.04)}
    .thumb.placeholder{height:100%;display:flex;align-items:center;justify-content:center;font-size:27px;color:#617c95;background:radial-gradient(circle at 30% 25%,rgba(88,186,255,.12),transparent 35%),linear-gradient(145deg,#142a43,#0b1b2c)}
    .media-kind{position:absolute;left:10px;bottom:10px;display:inline-flex;align-items:center;gap:5px;padding:5px 8px;border:1px solid rgba(255,255,255,.14);border-radius:999px;background:rgba(4,13,22,.66);backdrop-filter:blur(14px);color:#eaf4fb;font-size:9.5px;font-weight:750;letter-spacing:.06em;text-transform:uppercase}
    .signal-main{display:flex;flex-direction:column;min-width:0;padding:3px 4px 2px 0}
    .signal-top{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}
    .identity{min-width:0}
    .account-row{display:flex;align-items:center;gap:8px;min-width:0}
    .account{font-size:14px;font-weight:760;letter-spacing:-.01em;color:#f2f7fb;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .account-link{text-decoration:none;color:inherit;min-width:0}
    .account-link:hover .account{color:#cdeaff}
    .meta-line{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:4px;color:#70869a;font-size:10.5px}
    .meta-sep{opacity:.5}
    .score-box{display:flex;flex-direction:column;align-items:flex-end;gap:5px;white-space:nowrap}
    .badge{padding:5px 8px;border-radius:999px;font-size:9.5px;font-weight:800;letter-spacing:.055em;text-transform:uppercase}
    .badge.ALTA{color:#bcf6d5;background:rgba(69,213,138,.085);border-color:rgba(69,213,138,.18)}
    .badge.MEDIA{color:#ffe1ad;background:rgba(255,191,105,.075);border-color:rgba(255,191,105,.16)}
    .badge.BASSA{color:#c2e4ff;background:rgba(88,186,255,.07);border-color:rgba(88,186,255,.16)}
    .badge.SCARTATA{color:#91a4b5;background:rgba(255,255,255,.035);border-color:rgba(255,255,255,.07)}
    .score-num{font-size:10px;color:#61788d;margin:0}
    .caption{margin:13px 0 14px;color:#dce7ef;font-size:13px;line-height:1.62;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
    .why{padding:12px 13px;border:1px solid rgba(255,255,255,.055);border-radius:15px;background:rgba(255,255,255,.022);margin-top:auto}
    .why-title{display:flex;align-items:center;gap:7px;font-size:9.5px;text-transform:uppercase;letter-spacing:.105em;color:#71899e;margin-bottom:8px;font-weight:750}
    .why-title::before{content:'✦';font-size:9px;color:#74c8ff}
    .reason-chips{display:flex;flex-wrap:wrap;gap:6px}
    .reason-chip{font-size:10.5px;padding:5px 8px;border-radius:999px;background:rgba(88,186,255,.055);border:1px solid rgba(88,186,255,.1);color:#bedef5}
    .reason-fallback{font-size:10.5px;color:#7d91a4;line-height:1.45}
    .signal-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:12px}
    .signal-actions{display:flex;gap:6px;align-items:center;margin:0;flex-wrap:wrap}
    .signal-action.active{border-color:rgba(69,213,138,.2);background:rgba(69,213,138,.055);color:#bdf2d4}
    .signal-action.ignore.active{border-color:rgba(255,191,105,.19);background:rgba(255,191,105,.05);color:#ffe0a8}
    .signal-status{font-size:9.5px;color:#60788d;text-transform:uppercase;letter-spacing:.08em;margin-left:2px}
    .open-instagram{display:inline-flex;align-items:center;gap:7px;text-decoration:none;color:#b8d3e6;background:rgba(255,255,255,.025)}
    .open-instagram::after{content:'↗';font-size:11px}
    .empty.echo-empty{padding:58px 28px;border-style:solid;border-color:rgba(255,255,255,.065);background:radial-gradient(circle at 50% 0,rgba(88,186,255,.065),transparent 38%),rgba(255,255,255,.018)}
    .empty-orb{width:42px;height:42px;margin:0 auto 14px;border-radius:50%;background:radial-gradient(circle at 36% 30%,#edf9ff 0 7%,#68c6ff 23%,#315eff 63%,#183055);box-shadow:0 0 30px rgba(88,186,255,.2)}
    .empty.echo-empty strong{font-size:16px;color:#e2edf5;margin-bottom:6px}
    .empty-copy{max-width:430px;margin:0 auto;color:#8296a9;font-size:12px;line-height:1.6}
    .empty-steps{display:flex;justify-content:center;gap:7px;flex-wrap:wrap;margin-top:16px}
    .empty-step{padding:6px 9px;border:1px solid rgba(255,255,255,.06);border-radius:999px;background:rgba(255,255,255,.025);font-size:10px;color:#879caf}
    .empty-cta{margin-top:18px;border:1px solid rgba(88,186,255,.24);background:rgba(88,186,255,.105);color:#e8f6ff;border-radius:11px;padding:9px 12px;cursor:pointer;font-size:11px;font-weight:700}
    .health-card{margin-top:10px;padding:12px;border:1px solid rgba(255,255,255,.075);border-radius:15px;background:rgba(255,255,255,.022)}
    .health-row{display:flex;justify-content:space-between;gap:12px;font-size:11px;padding:4px 0;color:#8499ac}.health-row strong{font-weight:650;color:#dce8f1}.health-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px;background:#45d58a;box-shadow:0 0 12px rgba(69,213,138,.25)}.health-dot.caution{background:#ffbf69;box-shadow:none}.health-dot.paused{background:#ff7f8f;box-shadow:none}
    .loading-card{display:grid;grid-template-columns:190px minmax(0,1fr);gap:20px;padding:14px;border:1px solid rgba(255,255,255,.055);border-radius:var(--echo-card-radius);background:rgba(255,255,255,.018)}
    .skeleton{position:relative;overflow:hidden;background:rgba(255,255,255,.045)}
    .skeleton::after{content:'';position:absolute;inset:0;transform:translateX(-100%);background:linear-gradient(90deg,transparent,rgba(255,255,255,.035),transparent);animation:echo-shimmer 1.45s infinite}
    .sk-media{border-radius:var(--echo-media-radius);aspect-ratio:1}.sk-line{height:10px;border-radius:999px;margin-bottom:10px}.sk-line.w1{width:28%}.sk-line.w2{width:68%}.sk-line.w3{width:92%}.sk-line.w4{width:50%}@keyframes echo-shimmer{100%{transform:translateX(100%)}}
    button:focus-visible,a:focus-visible{outline:2px solid rgba(88,186,255,.55);outline-offset:2px}
    @media(max-width:760px){
      .workflow-shell{align-items:flex-start;flex-direction:column;margin-bottom:12px}.refresh-note{display:none}
      .signal{grid-template-columns:1fr;gap:13px;padding:11px;border-radius:20px}.signal::before{top:16px;bottom:auto;left:16px;right:16px;width:auto;height:2px;border-radius:2px}
      .media-link{aspect-ratio:16/10;border-radius:15px}.signal-main{padding:1px 2px 2px}.signal-top{gap:10px}.caption{font-size:12.5px;margin:11px 0 12px;-webkit-line-clamp:4}.why{padding:11px}.signal-footer{align-items:flex-start;flex-direction:column}.open-instagram{align-self:stretch;justify-content:center}.loading-card{grid-template-columns:1fr}.sk-media{aspect-ratio:16/10}.workflow-btn{padding:7px 9px}
    }
    @media(prefers-reduced-motion:reduce){.signal,.thumb,.workflow-btn,.signal-action,.open-instagram{transition:none}.skeleton::after{animation:none}}
  `;
  document.head.appendChild(style);

  let statusFilter = 'new';
  let lastFeedLoadedAt = null;

  const relevanceLabels = { ALTA: 'High', MEDIA: 'Medium', BASSA: 'Low', SCARTATA: 'Discarded' };

  const weight = document.getElementById('weightInput');
  if (weight) {
    weight.min = '-100';
    weight.max = '100';
    weight.title = 'Positive weights boost relevance; negative weights reduce it.';
  }

  const toolbar = document.querySelector('.toolbar');
  if (toolbar) {
    const shell = document.createElement('div');
    shell.className = 'workflow-shell';
    shell.innerHTML = `
      <div class="workflow-filters" role="group" aria-label="Signal workflow status">
        <button type="button" class="workflow-btn active" data-status="new">New</button>
        <button type="button" class="workflow-btn" data-status="reviewed">Reviewed</button>
        <button type="button" class="workflow-btn" data-status="ignored">Ignored</button>
        <button type="button" class="workflow-btn" data-status="all">All</button>
      </div>
      <div class="refresh-note" id="echoRefreshNote">Live feed</div>`;
    toolbar.insertAdjacentElement('afterend', shell);
    shell.addEventListener('click', e => {
      const b = e.target.closest('[data-status]');
      if (!b) return;
      statusFilter = b.dataset.status;
      shell.querySelectorAll('.workflow-btn').forEach(x => x.classList.toggle('active', x === b));
      loadFeed();
    });
  }

  function kindFor(post) {
    const type = String(post.product_type || '').toLowerCase();
    if (['clips', 'reels', 'reel'].includes(type) || post.video_url) return 'Reel';
    if (Number(post.media_type) === 8) return 'Carousel';
    if (Number(post.media_type) === 1) return 'Post';
    return 'Instagram';
  }

  function timeLabel(value) {
    if (!value) return 'Unknown time';
    return relativeTime(value).replace('Just now', 'Now');
  }

  function exactTime(value) {
    if (!value) return '';
    try { return new Date(value).toLocaleString(); } catch (_) { return ''; }
  }

  function emptyState() {
    const hasSources = Array.isArray(sourceItems) && sourceItems.length > 0;
    const hasObjectives = Array.isArray(objectiveItems) && objectiveItems.length > 0;
    const title = statusFilter === 'new' ? 'No new signals right now' : 'Nothing here yet';
    const copy = hasSources
      ? 'Echo is monitoring quietly. New relevant posts will appear here as soon as they are collected.'
      : 'Connect Instagram, add a source and tell Echo what matters. The feed will stay quiet until there is a signal worth showing.';
    const steps = !hasSources
      ? `<div class="empty-steps"><span class="empty-step">1 · Connect Instagram</span><span class="empty-step">2 · Add source</span><span class="empty-step">3 · Add objective</span></div>`
      : (!hasObjectives ? `<div class="empty-steps"><span class="empty-step">Add an objective to improve relevance</span></div>` : '');
    return `<div class="empty echo-empty"><div class="empty-orb"></div><strong>${title}</strong><div class="empty-copy">${copy}</div>${steps}<button type="button" class="empty-cta" onclick="openMonitoring()">Open Monitoring</button></div>`;
  }

  function loadingState() {
    const card = `<div class="loading-card" aria-hidden="true"><div class="skeleton sk-media"></div><div><div class="skeleton sk-line w1"></div><div class="skeleton sk-line w2"></div><div style="height:22px"></div><div class="skeleton sk-line w3"></div><div class="skeleton sk-line w3"></div><div class="skeleton sk-line w4"></div></div></div>`;
    return card + card;
  }

  renderFeed = function () {
    const q = document.getElementById('searchInput').value.trim().toLowerCase();
    const items = feedItems.filter(p => !q || `${p.username || ''} ${p.caption || ''} ${p.reason || ''}`.toLowerCase().includes(q));
    const el = document.getElementById('feed');
    if (!items.length) {
      el.innerHTML = q ? '<div class="empty echo-empty"><div class="empty-orb"></div><strong>No matching signals</strong><div class="empty-copy">Try a different search or relevance filter.</div></div>' : emptyState();
      return;
    }

    el.innerHTML = items.map(p => {
      const tokens = reasonTokens(p.reason);
      const media = p.thumbnail_url
        ? `<img class="thumb" src="${esc(p.thumbnail_url)}" alt="Instagram content from @${esc(p.username)}" loading="lazy">`
        : '<div class="thumb placeholder">◎</div>';
      const why = tokens.length
        ? tokens.map(t => `<span class="reason-chip">${esc(t)}</span>`).join('')
        : `<span class="reason-fallback">${esc(p.reason || 'No configured signal matched')}</span>`;
      const reviewed = p.status === 'reviewed';
      const ignored = p.status === 'ignored';
      const kind = kindFor(p);
      const relevance = relevanceLabels[p.relevance] || p.relevance || 'Signal';
      const url = esc(p.permalink || '#');
      const time = timeLabel(p.published_at);
      const exact = exactTime(p.published_at);

      return `<article class="signal" data-relevance="${esc(p.relevance || '')}">
        <div class="thumb-wrap">
          <a class="media-link" href="${url}" target="_blank" rel="noopener" aria-label="Open ${esc(kind)} by @${esc(p.username)} on Instagram">
            ${media}<span class="media-kind">${kind === 'Reel' ? '▶' : '◫'} ${esc(kind)}</span>
          </a>
        </div>
        <div class="signal-main">
          <div class="signal-top">
            <div class="identity">
              <div class="account-row"><a class="account-link" href="${url}" target="_blank" rel="noopener"><div class="account">@${esc(p.username)}</div></a></div>
              <div class="meta-line"><span title="${esc(exact)}">${esc(time)}</span><span class="meta-sep">·</span><span>${esc(kind)}</span></div>
            </div>
            <div class="score-box"><span class="badge ${esc(p.relevance)}">${esc(relevance)}</span><div class="score-num">${Number(p.relevance_score || 0)}/100 relevance</div></div>
          </div>
          <div class="caption">${esc(p.caption || 'No caption')}</div>
          <div class="why"><div class="why-title">Why Echo surfaced this</div><div class="reason-chips">${why}</div></div>
          <div class="signal-footer">
            <div class="signal-actions">
              <button type="button" class="signal-action ${reviewed ? 'active' : ''}" onclick="setPostStatus('${p.id}','reviewed')" aria-label="Mark signal as reviewed">✓ Reviewed</button>
              <button type="button" class="signal-action ignore ${ignored ? 'active' : ''}" onclick="setPostStatus('${p.id}','ignored')" aria-label="Ignore signal">Ignore</button>
              <span class="signal-status">${esc(p.status || 'new')}</span>
            </div>
            <a class="open-instagram" href="${url}" target="_blank" rel="noopener">Open on Instagram</a>
          </div>
        </div>
      </article>`;
    }).join('');
  };

  loadFeed = async function () {
    const el = document.getElementById('feed');
    if (!lastFeedLoadedAt && el) el.innerHTML = loadingState();
    try {
      const params = new URLSearchParams();
      if (currentFilter !== 'ALL') params.set('relevance', currentFilter);
      if (statusFilter !== 'all') params.set('status', statusFilter);
      const d = await api('/echo/feed' + (params.toString() ? `?${params}` : ''));
      feedItems = d.items || [];
      lastFeedLoadedAt = new Date();
      renderFeed();
      document.getElementById('statusText').textContent = 'Live';
      const note = document.getElementById('echoRefreshNote');
      if (note) note.textContent = `Updated ${lastFeedLoadedAt.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}`;
    } catch (e) {
      document.getElementById('statusText').textContent = 'Unavailable';
      if (el) el.innerHTML = '<div class="empty echo-empty"><div class="empty-orb"></div><strong>Feed unavailable</strong><div class="empty-copy">Echo could not refresh signals. The next automatic refresh will retry.</div></div>';
      toast(e.message);
    }
  };

  window.setPostStatus = async function (id, status) {
    if (!requireAdmin()) return;
    try {
      await api(`/echo/posts/${id}/status`, { method: 'PATCH', headers: adminHeaders(), body: JSON.stringify({ status }) });
      await loadFeed();
      toast(status === 'reviewed' ? 'Marked as reviewed' : 'Signal ignored');
    } catch (e) { toast(e.message); }
  };

  const connection = document.querySelector('.connection-card');
  if (connection && !document.getElementById('echoHealthCard')) {
    const health = document.createElement('div');
    health.className = 'health-card';
    health.id = 'echoHealthCard';
    health.innerHTML = '<div class="health-row"><span>Safe Collection</span><strong>Loading…</strong></div>';
    connection.insertAdjacentElement('afterend', health);
  }

  async function loadHealth() {
    const el = document.getElementById('echoHealthCard');
    if (!el) return;
    try {
      const r = await fetch('/echo/instagram/status', { cache: 'no-store' });
      const d = await r.json();
      const h = d.health || {};
      const state = (h.state || 'healthy').toLowerCase();
      const last = h.last_success_at ? relativeTime(h.last_success_at) : 'No scan yet';
      const requests = Number(h.requests_last_run || 0);
      el.innerHTML = `<div class="health-row"><span>Status</span><strong><span class="health-dot ${state}"></span>${state.charAt(0).toUpperCase() + state.slice(1)}</strong></div><div class="health-row"><span>Safe Collection</span><strong>${h.safe_mode === false ? 'OFF' : 'ON'}</strong></div><div class="health-row"><span>Last successful scan</span><strong>${esc(last)}</strong></div><div class="health-row"><span>Requests last run</span><strong>${requests}</strong></div>`;
    } catch (_) {
      el.innerHTML = '<div class="health-row"><span>Health</span><strong>Unavailable</strong></div>';
    }
  }

  loadFeed();
  loadHealth();
  setInterval(loadHealth, 60000);
})();
