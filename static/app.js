const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
let state = null;
let token = '';
let activeView = 'main';
let trendMetric = 'military';
let galaxyMetric = 'military';
let watchlistItems = [];
let watchlistIndex = 0;
let watchlistTimer = null;
let selectedPlanet = null;
let selectedEmpire = null;
let empireCategory = 'military';
let selectedShip = null;
let techRouteWindow = null;
let flagStamp = '';
let lastRenderKey = '';
let questionHistory = {recent:[], frequent:[]};
let attachedImage = null;
let cropOrigin = null;
let cropBox = null;
const defaultChatHint = 'Tab completes a command · Enter sends';
function campaignPinId(snapshot) {
  const id = snapshot?.campaign?.id;
  return typeof id === 'string' && /^[a-f0-9]{16}$/.test(id) ? id : null;
}

function pinnedGoal(snapshot, value = state?.pin) {
  const id = campaignPinId(snapshot);
  return id && value?.campaign_id === id && typeof value.key === 'string' && value.key.length <= 100 &&
    typeof value.title === 'string' && value.title.length <= 160 ? value : null;
}

function goalDisplay(snapshot, advice, savedPin = state?.pin) {
  if (!snapshot) return {goals:[], pin:null, matchedPin:null, dormant:false};
  const pin = pinnedGoal(snapshot, savedPin);
  const catalog = advice?.goal_catalog || advice?.goals || [];
  const matchedPin = pin && catalog.find(goal => goal.key === pin.key);
  const goals = matchedPin ? [matchedPin, ...(advice?.goals || []).filter(goal => goal.key !== pin.key)].slice(0, 5) : (advice?.goals || []);
  return {goals, pin, matchedPin, dormant:Boolean(pin && !matchedPin)};
}

function criticalResources(snapshot) {
  return Object.entries(snapshot?.resource_runway || {}).filter(([, cover]) => cover.urgency === 'urgent');
}

const viewCopy = {
  main: ['Your command center', 'Clear priorities from your latest autosave.'],
  planets: ['Your colonies', 'See which colony needs attention and what to consider building.'],
  empires: ['Known empires', 'Compare your position and what your intelligence actually reveals.'],
  tech: ['Your research path', 'Compare visible choices with the bottleneck in your empire.'],
  ships: ['Your fleet', 'See your saved fleets, compare designs, and plan the next build.']
};
const quickQuestions = {
  main: ["What's my economy looking like?", 'Am I on track for this year?', 'Who should I be worried about?', 'Should I attack the fallen empire?'],
  planets: ['Which colony needs attention first?', 'What should I build on my colonies?', 'Do I have an amenities problem?', 'Why is planetary automation idle?'],
  empires: ['Who should I be worried about?', 'Why is my vassal loyalty dropping?', 'How does my fleet compare?'],
  tech: ['What technology should I choose next?', 'Which branch needs attention?', 'How can I increase research output?', 'What are the Dangerous Technology risks?'],
  ships: ['What armor or shield configuration should I build on my ships?', 'How to increase naval capacity?', 'How to increase starbase capacity?', 'What ships should I build now?']
};

function dynamicQuickQuestions(snapshot, advice, view) {
  const items = [];
  const seen = new Set();
  const push = (text, urgent = false) => {
    const key = String(text || '').trim().toLowerCase();
    if (!key || seen.has(key)) return;
    seen.add(key);
    items.push({text, urgent});
  };
  if (snapshot) {
    const player = snapshot.player || {};
    const profile = player.profile || {};
    const net = player.net || {};
    const netKnown = player.net_known || {};
    const planets = snapshot.planets || [];
    const contacts = snapshot.contacts || [];
    const bench = advice?.benchmark || {};
    const year = Number(bench.year || String(snapshot.date || '').split('.')[0] || 0);

    // 1. Contacted active crisis (spoiler-safe: only from visible contacts).
    for (const crisis of (bench.contacted_crises || []).slice(0, 1)) {
      if (crisis?.label) push(`How to counter ${crisis.label}?`, true);
    }

    // 2. Revolt risk or urgent unstable colony.
    const unstable = planets
      .filter(p => p && p.name && typeof p.stability === 'number' && Number.isFinite(p.stability) && p.stability < 40)
      .sort((a, b) => a.stability - b.stability);
    if (unstable.length) {
      const worst = unstable[0];
      if (worst.stability < 25) push(`How do I stop ${worst.name} revolt?`, true);
      else if (view === 'main' || view === 'planets') push(`How do I fix stability on ${worst.name}?`, true);
    }

    // 3. Largest tracked resource deficit.
    const deficits = ['consumer_goods', 'trade', 'energy', 'minerals', 'alloys', 'food']
      .filter(k => typeof net[k] === 'number' && Number.isFinite(net[k]) && netKnown[k] !== false && net[k] < 0)
      .sort((a, b) => net[a] - net[b]);
    if (deficits.length && (view === 'main' || view === 'planets' || view === 'ships')) {
      const resLabel = deficits[0].replaceAll('_', ' ');
      push(`How to increase ${resLabel}?`, true);
    }

    // 4. Starbase overcap.
    if (typeof player.starbase_used === 'number' && typeof player.starbase_capacity === 'number' &&
        player.starbase_capacity > 0 && player.starbase_used > player.starbase_capacity) {
      push('How to increase starbase capacity?', true);
    }

    // 5. Active war against the player.
    const atWar = contacts.some(c => c && (c.wars || []).some(w => w && w.against_player));
    if (atWar && (view === 'main' || view === 'ships' || view === 'empires')) {
      push('What armor or shield configuration should I build on my ships?', true);
    }

    // 6. Tab-specific live cues.
    if (view === 'tech') {
      const research = player.research || {};
      const branches = ['physics', 'society', 'engineering'].filter(b => typeof research[b] === 'number');
      if (branches.length) {
        const weakest = branches.sort((a, b) => research[a] - research[b])[0];
        push(`How is my ${weakest} research?`, false);
      }
      if (year >= 2280) push('What are the Dangerous Technology risks?', false);
    }

    // 7. Year & DLC milestones.
    if (view === 'main') {
      if (year >= 2400) push('How to prepare for the endgame crisis?', false);
      else if (year >= 2300) push('How to prepare for a midgame crisis?', false);
      if (profile.is_nomad) push('How do Nomad Arkships and Waylines work?', false);
      const versionStr = String(snapshot.campaign?.save_version || snapshot.version || '');
      const dlcs = snapshot.campaign?.dlc_summary?.active_ids || [];
      if (/4\.6\./.test(versionStr) && dlcs.includes('willpower')) {
        push('How do Ideologies and Galactic Halls work?', false);
      }
    }
  }
  for (const fallback of (quickQuestions[view] || quickQuestions.main)) {
    push(fallback, false);
  }
  return items.slice(0, 5);
}

function number(value) { return Number(value || 0).toLocaleString(undefined, {maximumFractionDigits: 1}); }
function signed(value) { const n = Number(value || 0); return `${n >= 0 ? '+' : ''}${number(n)}`; }
function valueClass(value) { return Number(value || 0) < 0 ? 'negative' : 'positive'; }
function providerName(value) { return ({off:'Built-in guide', ollama:'Ollama', lmstudio:'LM Studio', openrouter:'OpenRouter'})[value] || 'Built-in guide'; }

async function post(path, body = {}) {
  if (window.STELLARIS_API?.post) return await window.STELLARIS_API.post(path, body);
  const response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json','X-Guide-Token':token}, body:JSON.stringify(body)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'The request failed');
  return result;
}

function showNotice(message, kind = '') {
  $('notice').hidden = !message;
  $('notice').textContent = message || '';
  $('notice').className = `notice ${kind}`;
}

function setText(id, value) { $(id).textContent = value; }

function renderIndicators(snapshot) {
  const p = snapshot.player;
  const energy = p.net.energy || 0, alloys = p.net.alloys || 0;
  setText('metric-energy', signed(energy)); $('metric-energy').className = valueClass(energy);
  setText('stock-energy', `stock ${number(p.stock.energy)}`);
  setText('metric-alloys', signed(alloys)); $('metric-alloys').className = valueClass(alloys);
  setText('stock-alloys', `stock ${number(p.stock.alloys)}`);
  setText('metric-fleet', number(p.military));
  setText('metric-naval', `naval use ${number(p.naval_used)}`);
  setText('metric-colonies', number(p.colonies));
  setText('metric-size', `empire size ${number(p.empire_size)}`);
}

function renderHealth(snapshot) {
  const p = snapshot.player || {};
  const coreResources = ['energy','minerals','food','consumer_goods','alloys'];
  const deficits = coreResources.filter(key => Number(p.net?.[key] || 0) < 0 && p.net_known?.[key] !== false);
  const unavailable = coreResources.filter(key => snapshot.resource_runway?.[key]?.status === 'unknown' || p.net_known?.[key] === false || p.net?.[key] === undefined);
  const science = ['physics','society','engineering'].reduce((sum,key) => sum + Number(p.research?.[key] || 0), 0);
  const economyPreview = deficits.length ? `${deficits.length} deficit${deficits.length === 1 ? '' : 's'}: ${deficits.map(key => key.replaceAll('_',' ')).join(', ')}` : unavailable.length ? 'Resource data incomplete' : 'No monthly deficit recorded';
  setText('health-preview', `${economyPreview}${unavailable.length ? ` · ${unavailable.length} unknown` : ''} · Science ${number(science)}/mo · Starbases ${p.starbase_capacity ? `${number(p.starbase_used)}/${number(p.starbase_capacity)}` : 'unknown'} · Expand`);
  const resource = (key, label, icon) => {
    if (p.net?.[key] === undefined && p.stock?.[key] === undefined && !snapshot.resource_runway?.[key]) return '';
    const cover = snapshot.resource_runway?.[key];
    const net = cover ? cover.net : p.net?.[key];
    const tone = cover?.urgency === 'urgent' ? 'urgent' : cover?.urgency === 'watch' ? 'watch' : cover?.status === 'unknown' ? 'unknown' : 'healthy';
    const runway = cover?.status === 'depleting' ? `About ${number(cover.months)} months cover · ${esc(cover.date || 'save date unknown')}`
      : cover?.status === 'no_depletion' ? 'No depletion at saved rate'
      : 'Runway unknown';
    const stock = cover ? cover.stock : p.stock?.[key];
    return `<div class="health-item ${tone}"><span>${icon} ${label}</span><strong>${net == null ? 'Unknown' : `${signed(net)}/mo`}</strong><small>Stock ${stock == null ? 'unknown' : number(stock)} · ${runway}</small></div>`;
  };
  const research = ['physics','society','engineering'].map(key =>
    `<div class="health-item"><span>${esc(key[0].toUpperCase()+key.slice(1))}</span><strong>${p.research?.[key] === undefined ? 'Unknown' : `${number(p.research[key])}/mo`}</strong></div>`).join('');
  const starbase = p.starbase_capacity ? `${number(p.starbase_used)} / ${number(p.starbase_capacity)}` : 'Unknown';
  const dlcSummary = snapshot.campaign?.dlc_summary;
  const dlcPills = dlcSummary?.display?.length
    ? dlcSummary.display.map(item => `<span class="health-dlc-pill" title="${esc(item.source === 'base_game' ? 'Included in base game (4.5+)' : 'Recorded in save')}">${esc(item.name)}</span>`).join('')
    : `<span class="health-dlc-pill">${dlcSummary?.known ? 'Base game only' : 'DLC list not recorded'}</span>`;
  const profile = p.profile || {};
  const profileBits = [
    profile.authority ? profile.authority.replace(/^auth_/, '').replaceAll('_', ' ') : null,
    profile.is_nomad ? 'Nomad' : null,
    profile.shipset_kind && profile.shipset_kind !== 'mechanical' ? `${profile.shipset_kind} ships` : null,
    profile.ideology_active ? 'Ideology active' : null,
  ].filter(Boolean);
  $('health-groups').innerHTML = `
    <div class="health-group"><h3>Economy</h3><div class="health-items">${resource('energy','Energy','⚡')}${resource('minerals','Minerals','◆')}${resource('food','Food','◉')}${resource('consumer_goods','Consumer goods','▣')}${resource('alloys','Alloys','⬡')}${resource('trade','Trade','⇄')}</div></div>
    <div class="health-group"><h3>Progress</h3><div class="health-items">${research}${resource('unity','Unity','✦')}</div></div>
    <div class="health-group"><h3>Capacity &amp; DLCs</h3><div class="health-items"><div class="health-item"><span>Empire size</span><strong>${number(p.empire_size)}</strong></div><div class="health-item"><span>Naval use / limit</span><strong>${number(p.naval_used)} / ${p.naval_capacity == null ? 'unknown' : number(p.naval_capacity)}</strong></div><div class="health-item ${p.starbase_capacity && p.starbase_used > p.starbase_capacity ? 'urgent' : ''}"><span>Starbases</span><strong>${starbase}</strong></div>${profileBits.length ? `<div class="health-item"><span>Empire profile</span><strong>${esc(profileBits.join(' · '))}</strong></div>` : ''}</div><div class="health-dlc-pills">${dlcPills}</div></div>`;
  $('spoiler-banner').hidden = !state?.config?.spoilers_active;
}

function renderMain(snapshot, advice) {
  setText('plan-window', advice?.window || 'Next 5–10 years');
  const {goals, pin, matchedPin, dormant} = goalDisplay(snapshot, advice);
  const risk = criticalResources(snapshot);
  $('critical-risk').hidden = !risk.length;
  $('critical-risk').textContent = risk.length ? `Resource stock risk: ${risk.map(([key, cover]) => `${key.replaceAll('_',' ')} about ${number(cover.months)} months cover`).join('; ')} at the saved rate. Check the current in-game balance.` : '';
  $('pin-notice').hidden = !dormant;
  $('pin-notice').innerHTML = dormant ? `Pinned goal “${esc(pin.title)}” is unavailable in the latest save. The current suggestion stays first. <button type="button" id="clear-dormant-pin">Clear pin</button>` : '';
  const expandedDetails = new Set([...document.querySelectorAll('#goals details[open][data-detail-key]')].map(item => item.dataset.detailKey));
  $('goals').innerHTML = goals.length ? goals.map((goal, index) => {
    const progress = goal.progress || {};
    const percent = Math.max(0, Math.min(100, Number(progress.percent || 0)));
    const steps = goal.steps || [];
    const pbKey = `pb:${goal.key}`;
    const actKey = `act:${goal.key}`;
    const moreKey = `more:${goal.key}`;
    return `<div class="goal ${index === 0 ? 'lead-goal' : 'support-goal'}"><span class="number">${index + 1}</span><div class="goal-body">
      ${index === 0 ? `<span class="eyebrow">${pin && pin.key === goal.key ? 'PINNED CAMPAIGN FOCUS' : 'SUGGESTED FOCUS'}</span>` : ''}
      <div class="goal-heading"><strong>${esc(goal.title)}</strong>${campaignPinId(snapshot) ? `<button type="button" class="goal-pin" data-pin-goal="${esc(goal.key)}" aria-pressed="${Boolean(pin && pin.key === goal.key)}">${pin && pin.key === goal.key ? 'Pinned' : 'Pin goal'}</button>` : ''}</div><p>${esc(goal.detail)}</p><small class="goal-priority">${esc(goal.rank_reason || '')}</small>
      ${goal.playbook ? `<details class="goal-playbook" data-detail-key="${esc(pbKey)}" ${expandedDetails.has(pbKey) ? 'open' : ''}><summary>Strategy playbook · ${esc(goal.playbook.match === 'matched' ? 'Conditions match' : 'Check missing facts')} · Rules: ${esc(goal.playbook.rules_status)} · Strategy: ${esc(goal.playbook.strategy_status)}</summary><p>${esc(goal.playbook.rules_status === 'needs recheck' ? 'This playbook was checked for a different game version or checksum. Verify it against your current game before using it.' : goal.playbook.match === 'investigate' ? 'The save lacks a fact needed to confirm this playbook. Check the situation in game first.' : goal.playbook.title)}</p>${goal.playbook.rules_status === 'conditional' ? '<p>Rule details may vary with your game or mods. Confirm in game.</p>' : ''}${goal.playbook.strategy_status === 'untested' ? '<p>This strategy has not yet been validated as an effective build.</p>' : ''}<p>Trade-off: ${esc(goal.playbook.trade_off)}</p><p>Change course if: ${esc(goal.playbook.change_course_if)}</p><small>Checked against ${esc(goal.playbook.validated_release)} · ${esc(goal.playbook.id)} rev ${esc(goal.playbook.revision)}</small><small>Sources: ${(goal.playbook.sources || []).map(source => `${esc(source.kind)} (${esc(source.ref)})`).join('; ')}</small></details>` : ''}
      <div class="goal-progress"><span>Progress ${esc(progress.label || 'check next autosave')}</span><b>${percent}%</b></div>
      <div class="goal-progress-track"><i style="width:${percent}%"></i></div>
      ${steps.length ? `<details class="goal-actions" data-goal-key="${esc(goal.key)}" data-detail-key="${esc(actKey)}" ${expandedDetails.has(actKey) ? 'open' : ''}>
        <summary>How to achieve this <span>${steps.length} ${steps.length === 1 ? 'step' : 'steps'}</span></summary>
        <div class="goal-steps">
        ${steps.slice(0, 2).map((step, i) => { const stepKey = `step:${goal.key}:${i}`; return `<div class="goal-step"><b>${i+1}</b><div><strong>${esc(step.action)}</strong><details data-detail-key="${esc(stepKey)}" ${expandedDetails.has(stepKey) ? 'open' : ''}><summary>Why and what to check</summary><small>${esc(step.reason)}</small><em>Check: ${esc(step.check)}</em></details></div></div>`; }).join('')}
        ${steps.length > 2 ? `<details data-detail-key="${esc(moreKey)}" ${expandedDetails.has(moreKey) ? 'open' : ''}><summary>Show ${steps.length - 2} more step(s)</summary>${steps.slice(2).map(step => `<p>${esc(step.action)} ${esc(step.check)}</p>`).join('')}</details>` : ''}
        </div></details>` : ''}</div><time>BY ${esc(goal.due)}</time></div>`;
  }).join('') : '<div class="empty">No plan is available from this save yet.</div>';
  watchlistItems = advice?.alerts || [];
  renderBenchmark(snapshot, advice);
  renderWatchlist();
  renderChart(state.history || []);
  renderEmpires(snapshot);
}

function renderBenchmark(snapshot, advice) {
  const card = $('campaign-benchmark');
  const body = $('benchmark-body');
  if (!card || !body) return;
  const bench = advice?.benchmark;
  if (!bench) { card.hidden = true; return; }
  card.hidden = false;
  const stageLabel = `STAGE ${bench.stage} OF 4 · ${String(bench.stage_name || '').toUpperCase()}`;
  const eyebrow = $('benchmark-stage-eyebrow');
  const title = $('benchmark-title');
  const preview = $('benchmark-preview');
  if (eyebrow) eyebrow.textContent = stageLabel;
  if (title) title.textContent = bench.before_first
    ? `Year ${bench.year} · Building toward Year ${bench.current_year}`
    : `Year ${bench.year || '—'} · Checkpoint Year ${bench.current_year}`;
  const metrics = bench.metrics || [];
  const onTrack = metrics.filter(m => m.status === 'on_track').length;
  const warnCount = (bench.checks || []).filter(c => !c.ok).length;
  if (preview) {
    const nextText = bench.next ? ` · Next: Year ${bench.next.year}` : '';
    const warnText = warnCount ? ` · ${warnCount} readiness warning(s)` : ' · Checks healthy';
    preview.textContent = `${onTrack}/${metrics.length} baseline ranges met${warnText}${nextText} · expand`;
  }
  const statusLabel = s => ({on_track: 'On track', building: 'Building', behind: 'Behind', unknown: 'Unknown'}[s] || s);
  const metricsHtml = metrics.map(m => {
    const val = typeof m.current === 'number' ? `${number(m.current)}${m.unit}` : 'Unknown';
    return `<div class="benchmark-metric status-${esc(m.status)}"><span>${esc(m.label)}</span><strong>${esc(val)}</strong><small>1× target: ${number(m.target_low)}–${number(m.target_high)}${esc(m.unit)} · ${esc(statusLabel(m.status))}</small></div>`;
  }).join('');
  const checksHtml = (bench.checks || []).map(c =>
    `<li class="${c.ok ? 'ok' : 'warn'}"><b>${c.ok ? '✓' : '!'}</b><span><strong>${esc(c.label)}:</strong> ${esc(c.detail)}</span></li>`
  ).join('');
  const nextHtml = bench.next
    ? `<div class="benchmark-next"><span class="eyebrow">NEXT MILESTONE · YEAR ${esc(bench.next.year)} (${esc(bench.next.stage_name)})</span><p>${esc(bench.next.focus)}</p></div>`
    : '';
  body.innerHTML = `<p class="benchmark-focus">${esc(bench.focus || '')}${bench.is_nomad ? ' (Nomads: focus on Arkship modules & Waylines rather than fixed colonies.)' : ''}</p>`
    + `<div class="benchmark-metrics">${metricsHtml}</div>`
    + `<ul class="benchmark-checks">${checksHtml}</ul>`
    + nextHtml
    + `<small class="benchmark-caveat">${esc(bench.caveat || '')}</small>`;
}

function renderWatchlist() {
  const ticker = $('watchlist-ticker');
  if (!watchlistItems.length) { ticker.hidden = true; return; }
  watchlistIndex %= watchlistItems.length;
  const item = watchlistItems[watchlistIndex];
  ticker.hidden = false;
  $('watchlist-position').textContent = `${watchlistIndex + 1}/${watchlistItems.length}`;
  $('watchlist-current').innerHTML = `<strong>${esc(item.title)}</strong><span>${esc(item.detail)}</span>`;
  $('watchlist-current').title = `${item.title}: ${item.detail}`;
}

function moveWatchlist(direction, manual = true) {
  if (!watchlistItems.length) return;
  watchlistIndex = (watchlistIndex + direction + watchlistItems.length) % watchlistItems.length;
  renderWatchlist();
  if (manual) scheduleWatchlistAdvance();
}

function scheduleWatchlistAdvance() {
  clearTimeout(watchlistTimer);
  watchlistTimer = setTimeout(() => {
    if (!document.hidden) moveWatchlist(1, false);
    scheduleWatchlistAdvance();
  }, 7000);
}

function renderChart(history) {
  const svg = $('trend-chart');
  const points = history.map(item => ({date:item.date, value:Number(item.player?.[trendMetric] || 0)}));
  if (!points.length) { svg.innerHTML = '<text x="20" y="80" class="chart-label">No history yet. More autosaves will build this chart.</text>'; return; }
  const width = 700, height = 260, left = 55, right = 20, top = 20, bottom = 38;
  const values = points.map(p => p.value); let min = Math.min(...values), max = Math.max(...values);
  if (min === max) { min -= Math.max(1, min * .05); max += Math.max(1, max * .05); }
  const x = i => left + i * ((width - left - right) / Math.max(points.length - 1, 1));
  const y = v => top + (max - v) * ((height - top - bottom) / (max - min));
  const coords = points.map((p,i) => `${x(i)},${y(p.value)}`).join(' ');
  const area = `${left},${height-bottom} ${coords} ${x(points.length-1)},${height-bottom}`;
  svg.innerHTML = `<defs><linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#58ded7" stop-opacity=".27"/><stop offset="1" stop-color="#58ded7" stop-opacity="0"/></linearGradient></defs>` +
    [0,.5,1].map(step => { const gy=top+step*(height-top-bottom), val=max-step*(max-min); return `<line x1="${left}" y1="${gy}" x2="${width-right}" y2="${gy}" class="axis-line"/><text x="4" y="${gy+4}" class="chart-label">${number(val)}</text>`; }).join('') +
    `<polygon points="${area}" class="trend-area"/><polyline points="${coords}" class="trend-line"/>` +
    points.map((p,i) => `<circle cx="${x(i)}" cy="${y(p.value)}" r="4" class="trend-point"><title>${esc(p.date)}: ${number(p.value)}</title></circle>`).join('') +
    `<text x="${left}" y="${height-8}" class="chart-label">${esc(points[0].date)}</text><text text-anchor="end" x="${width-right}" y="${height-8}" class="chart-label">${esc(points.at(-1).date)}</text>`;
}

function renderEmpires(snapshot) {
  document.querySelectorAll('#galaxy-tabs button').forEach(button => {
    const active = button.dataset.galaxyMetric === galaxyMetric;
    button.classList.toggle('active', active);
    button.setAttribute('aria-selected', String(active));
  });
  const contacts = snapshot.contacts || [];
  const list = $('empires');
  const previousScroll = list.scrollTop;
  const previousMetric = list.dataset.metric;
  const previousKnown = list.dataset.complete;
  const previousCount = list.dataset.count;
  if (galaxyMetric === 'opinion') {
    $('galaxy-summary').textContent = 'Their opinion of you · most negative first';
    $('galaxy-note').textContent = 'Opinion describes a relationship. It is not a measure of military, economy, or technology strength.';
    const ordered = [...contacts].sort((a, b) => (a.opinion ?? Infinity) - (b.opinion ?? Infinity));
    const scale = Math.max(1, ...ordered.map(c => Math.abs(Number(c.opinion) || 0)));
    list.innerHTML = ordered.length ? ordered.map(c => {
      const known = typeof c.opinion === 'number' && Number.isFinite(c.opinion);
      const width = known ? Math.max(2, Math.abs(c.opinion) / scale * 100) : 0;
      return `<div class="galaxy-rank-row ${known && c.opinion < 0 ? 'opinion-negative' : 'opinion-positive'}"><span class="galaxy-name">${esc(c.name)}</span><span class="galaxy-value">${known ? `${signed(c.opinion)} opinion` : 'Unknown opinion'}</span><div class="galaxy-bar"><i style="width:${width}%"></i></div></div>`;
    }).join('') : '<div class="empty">No contacted empires are readable from this save.</div>';
    list.scrollTop = previousMetric === 'opinion' ? previousScroll : 0;
    Object.assign(list.dataset, {metric:'opinion', complete:'', count:String(contacts.length)});
    return;
  }
  const ownScore = snapshot.player?.[galaxyMetric];
  const entries = [{name:snapshot.empire, value:ownScore, you:true}, ...contacts.map(c => ({name:c.name, value:c[galaxyMetric], you:false}))];
  const known = value => typeof value === 'number' && Number.isFinite(value);
  const complete = entries.every(entry => known(entry.value));
  entries.sort((a,b) => (known(b.value) ? b.value : -Infinity) - (known(a.value) ? a.value : -Infinity) || (a.you ? -1 : b.you ? 1 : a.name.localeCompare(b.name)));
  const ownRank = complete ? 1 + entries.filter(entry => entry.value > ownScore).length : null;
  $('galaxy-summary').innerHTML = `Your empire: <strong>${esc(snapshot.empire)}</strong> · ${ownRank ? `Rank #${ownRank} of ${entries.length}` : 'Rank unavailable'} · ${known(ownScore) ? number(ownScore) : 'Unknown'}`;
  $('galaxy-note').textContent = complete ? 'Strength values recorded in the save; exact foreign figures may be hidden in game and need in-game verification.' : 'Exact rival strengths are unavailable at current intel. Enable spoilers in Settings to compare save-recorded values.';
  const max = Math.max(1, ...entries.filter(entry => known(entry.value)).map(entry => entry.value));
  list.innerHTML = entries.map(entry => {
    const value = known(entry.value) ? entry.value : null;
    const rank = complete ? `#${1 + entries.filter(other => other.value > value).length}` : '—';
    const ratio = entry.you ? 'baseline' : value == null || !known(ownScore) || ownScore <= 0 ? 'comparison unavailable' : `${(value / ownScore).toFixed(1)}× yours`;
    const width = value == null ? 0 : Math.max(2, Math.min(100, value / max * 100));
    return `<div class="galaxy-rank-row ${entry.you ? 'you' : ''}"><span class="galaxy-rank">${rank}</span><span class="galaxy-name">${entry.you ? 'YOU · ' : ''}${esc(entry.name)}</span><span class="galaxy-value">${value == null ? 'Unknown' : `${number(value)} · ${ratio}`}</span><div class="galaxy-bar"><i style="width:${width}%"></i></div></div>`;
  }).join('');
  const ownRow = list.querySelector('.galaxy-rank-row.you');
  const shouldCenter = previousMetric !== galaxyMetric || previousKnown !== String(complete) || previousCount !== String(contacts.length);
  if (shouldCenter && ownRow) list.scrollTop = Math.max(0, ownRow.offsetTop - list.offsetTop - list.clientHeight / 2);
  else list.scrollTop = previousScroll;
  Object.assign(list.dataset, {metric:galaxyMetric, complete:String(complete), count:String(contacts.length)});
}

function empireKindLabel(kind) { return kind === 'default' ? 'Regular empire' : (kind || 'Empire').replaceAll('_', ' '); }
function renderEmpiresView(snapshot) {
  const contacts = [...(snapshot.contacts || [])];
  const metric = ['military','economy','technology'].includes(empireCategory) ? empireCategory : null;
  if (metric) contacts.sort((a,b) => (b[metric] ?? -1) - (a[metric] ?? -1));
  else if (empireCategory === 'diplomacy') contacts.sort((a,b) => (a.opinion ?? 999) - (b.opinion ?? 999));
  else contacts.sort((a,b) => (b.intel ?? -1) - (a.intel ?? -1));
  if (!contacts.some(c => c.id === selectedEmpire)) selectedEmpire = contacts[0]?.id ?? null;
  document.querySelectorAll('#empire-category-tabs button').forEach(button => {
    button.classList.toggle('active', button.dataset.category === empireCategory);
    button.setAttribute('aria-selected', button.dataset.category === empireCategory ? 'true' : 'false');
  });
  const knownValues = metric && contacts.every(c => c[metric] !== undefined);
  const ownRank = knownValues ? 1 + contacts.filter(c => c[metric] > snapshot.player[metric]).length : null;
  const ownValue = metric ? number(snapshot.player[metric]) : empireCategory === 'intel' ? 'Your perspective' : 'Your empire';
  $('empire-list').innerHTML = `<div class="select-item own-empire pinned-empire"><header><strong>${esc(snapshot.empire)} · You</strong><span>${ownRank ? `#${ownRank}` : 'Reference'}</span></header><p>${ownValue}</p></div>` +
    (contacts.length ? contacts.map(c => `<button class="select-item ${selectedEmpire === c.id ? 'selected' : ''}" data-empire="${c.id}"><header><strong>${esc(c.name)}</strong><span>${metric ? (c[metric] === undefined ? 'Unknown' : number(c[metric])) : empireCategory === 'intel' ? (c.intel == null ? 'Unknown intel' : `${number(c.intel)} intel`) : (c.opinion == null ? 'Unknown opinion' : signed(c.opinion))}</span></header><p>${esc(empireKindLabel(c.kind))}${c.spy_network ? ' · Your spy network' : ''}</p></button>`).join('') : '<div class="empty">No contacted empires in this save.</div>');
  document.querySelectorAll('[data-empire]').forEach(button => button.onclick = () => { selectedEmpire = Number(button.dataset.empire); renderEmpiresView(snapshot); });
  const empire = contacts.find(c => c.id === selectedEmpire);
  if (!empire) { $('empire-detail').innerHTML = '<div class="empty">Choose a contacted empire.</div>'; return; }
  const visible = key => empire[key] === undefined ? 'Unknown at current intel' : number(empire[key]);
  const ratio = key => empire[key] === undefined || !snapshot.player[key] ? '' : ` · ${(empire[key] / snapshot.player[key]).toFixed(1)}× yours`;
  let categoryHtml = '';
  if (metric) {
    categoryHtml = `<div class="comparison"><span>${esc(empireCategory)} strength</span><strong>${visible(metric)}${ratio(metric)}</strong><small>${empire[metric] === undefined ? 'Exact foreign power is hidden in normal mode. Check in-game Contacts and intel.' : 'From save · hidden in game · spoilers enabled'}</small></div>`;
    if (empireCategory === 'military' && empire.wars?.length) categoryHtml += `<div class="job-advice"><h3>Wars</h3>${empire.wars.map(war => `<p>${war.against_player ? 'At war with you' : 'Recorded war · spoiler'} · ${esc(war.side)} side · war exhaustion ${war.exhaustion == null ? 'unknown' : `${number(war.exhaustion)}%`}</p>`).join('')}<small>Exhaustion belongs to a war side, not an empire's overall strength.</small></div>`;
    if (empireCategory === 'economy' && empire.hidden) categoryHtml += `<details class="spoiler-details"><summary>Hidden stockpiles and monthly balances</summary>${Object.entries(empire.hidden.stock || {}).filter(([key]) => ['energy','minerals','food','consumer_goods','alloys'].includes(key)).map(([key,value]) => `<p>${esc(key.replaceAll('_',' '))}: ${number(value)} stock · ${signed(empire.hidden.net?.[key])}/mo</p>`).join('') || '<p>Not recorded in this save.</p>'}<small>From save · hidden in game</small></details>`;
  } else if (empireCategory === 'diplomacy') {
    const persKey = String(empire.personality || '').toLowerCase();
    const persLabel = persKey ? persKey.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase()) : 'Unknown at current intel';
    const persHint = persKey === 'fanatical_befrienders'
      ? ' Warning: Fanatical Befrienders have +100 base opinion yet 2× Aggressiveness and 1.5× Bravery (willing to attack Superior empires).'
      : ['fanatic_purifiers', 'devouring_swarm', 'exterminators', 'metalhead'].includes(persKey)
      ? ' Warning: Total-war / extreme-aggression AI personality; friendly diplomacy is restricted or unreliable.'
      : ['hegemonic_imperialists', 'democratic_crusaders', 'slaving_despots', 'honorbound_warriors'].includes(persKey)
      ? ' Note: Expansionist / aggressive AI personality; check borders and defensive pacts even if opinion is neutral.'
      : '';
    categoryHtml = `<div class="detail-stats"><div><span>Opinion of you</span><strong>${empire.opinion == null ? 'Unknown' : signed(empire.opinion)}</strong></div><div><span>AI personality</span><strong>${esc(persLabel)}</strong></div><div><span>Known stance</span><strong>${empire.relation?.hostile ? 'Hostile' : 'Not verified'}</strong></div><div><span>Embassy</span><strong>${empire.relation?.embassy ? 'Yes' : 'No record'}</strong></div></div><p class="detail-note">Subject ties, claims, treaties and diplomatic weight need validated save fields. Opinion alone does not predict war.${esc(persHint)}</p>`;
  } else {
    categoryHtml = `<div class="detail-stats"><div><span>Intel</span><strong>${empire.intel == null ? 'Unknown' : number(empire.intel)}</strong></div><div><span>Your spy network</span><strong>${empire.spy_network ? 'Recorded' : 'No record'}</strong></div></div><p class="detail-note">Unknown figures are not zero. Further espionage details will appear after their save fields have been verified.</p>`;
  }
  $('empire-detail').innerHTML = `<div class="detail-hero"><div><span class="eyebrow">CONTACTED EMPIRE</span><h2>${esc(empire.name)}</h2><p>${esc(empireKindLabel(empire.kind))} · Intel ${empire.intel == null ? 'unknown' : number(empire.intel)}</p></div></div>${categoryHtml}`;
}

function renderPlanets(snapshot) {
  const planets = snapshot.planets || [];
  const urgent = planets.filter(p => ['urgent','watch'].includes(p.recommendation.level)).length;
  setText('planet-count', `${planets.length} colonies`); setText('planet-badge', urgent ? String(urgent) : '');
  if (!planets.some(p => p.id === selectedPlanet)) selectedPlanet = planets[0]?.id ?? null;
  $('planet-list').innerHTML = planets.length ? planets.map(planet => `<button class="select-item ${planet.id === selectedPlanet ? 'active' : ''}" data-planet="${planet.id}"><header><strong>${esc(planet.name)}</strong><span class="status ${esc(planet.recommendation.level)}">${esc(planet.recommendation.level)}</span></header><p>${planet.system ? `${esc(planet.system)} system · ` : ''}${esc(planet.designation)} · ${number(planet.pops)} pops · ${number(planet.stability)}% stability</p></button>`).join('') : '<div class="empty">No owned colonies could be read.</div>';
  document.querySelectorAll('[data-planet]').forEach(button => button.addEventListener('click', () => { selectedPlanet = Number(button.dataset.planet); renderPlanets(snapshot); }));
  const planet = planets.find(p => p.id === selectedPlanet);
  if (!planet) { $('planet-detail').innerHTML = '<div class="empty">Choose a colony to see its details.</div>'; return; }
  const rec = planet.recommendation;
  const profitEntries = Object.entries(planet.profits || {}).filter(([,v]) => v !== 0).slice(0,8);
  const planetSvg = window.StellarisArt?.planetSvg ? window.StellarisArt.planetSvg(planet.class_key || planet.class) : '';
  const planetArt = window.STELLARIS_WEB_MODE
    ? `<img hidden data-local-art-kind="planet" data-local-art-key="${esc(planet.class_key || '')}" alt="" onerror="this.hidden=true">${planetSvg}`
    : `<img src="/api/planet-icon?id=${encodeURIComponent(planet.class_key || '')}" alt="" onerror="this.hidden=true">${planetSvg}`;
  $('planet-detail').innerHTML = `<div class="detail-hero"><div><span class="eyebrow">COLONY ${planet.id}</span><h2>${esc(planet.name)}</h2><p>${esc(planet.class)} · Size ${planet.size_known ? number(planet.size) : 'unknown'} · ${esc(planet.designation)}${planet.system ? ` · ${esc(planet.system)} system` : ''}</p></div><div class="planet-orb">${planetArt}</div></div>` +
    `<div class="detail-stats"><div><span>Stability</span><strong class="${planet.stability < 50 ? 'negative' : ''}">${number(planet.stability)}%</strong></div><div><span>Population</span><strong>${number(planet.pops)}</strong></div><div><span>Free housing</span><strong class="${planet.free_housing < 2 ? 'negative' : ''}">${signed(planet.free_housing)}</strong></div><div><span>Free amenities</span><strong class="${planet.free_amenities < 0 ? 'negative' : ''}">${signed(planet.free_amenities)}</strong></div></div>` +
    `<div class="recommendation"><span class="eyebrow">BUILD RECOMMENDATION</span><h3>${esc(rec.title)}</h3><p>${esc(rec.action)}</p><p>${esc(rec.reason)}</p></div>` +
    `<div class="resource-row"><span class="resource-pill">${number(planet.districts)} districts</span><span class="resource-pill">${number(planet.buildings)} buildings</span><span class="resource-pill">Crime ${number(planet.crime)}%</span>${profitEntries.map(([key,value]) => `<span class="resource-pill">${esc(key.replaceAll('_',' '))} ${signed(value)}</span>`).join('')}</div>`;
  window.StellarisLocalArt?.hydrate?.($('planet-detail'));
  const jobs = planet.jobs || [];
  const jobAdvice = planet.job_advice || [];
  $('planet-detail').insertAdjacentHTML('beforeend', `<details class="planet-jobs" open><summary>Jobs & controls <span>${jobs.length} types</span></summary>
    <p class="detail-note">Cygnus workforce is grouped. Values below are workforce equivalents from the save; check the in-game Jobs panel before changing a setting.</p>
    <div class="job-list">${jobs.length ? jobs.map(job => `<div class="job-row"><strong>${esc(job.type.replaceAll('_',' '))}</strong><span>${number(job.filled)} filled · ${job.capacity == null ? 'capacity unknown' : `${number(job.capacity)} capacity`}${job.limit == null ? '' : ` · ${number(job.limit)} allowed`}${job.disabled ? ' · disabled' : ''}</span></div>`).join('') : '<p>No job settings could be read.</p>'}</div>
    ${jobAdvice.length ? `<div class="job-advice"><h3>Job suggestions</h3>${jobAdvice.map(item => `<div><strong>${esc(item.action)}</strong><p>${esc(item.observation)} ${esc(item.tradeoff)}</p><small>${esc(item.check)} ${esc(item.confidence)}</small></div>`).join('')}</div>` : '<p class="detail-note">No specific job change is supported by this save. Review unemployment and priorities in game.</p>'}
    </details>`);
}

function renderTech(snapshot) {
  if (typeof renderTechOverview === 'function') {
    renderTechOverview(snapshot);
    return;
  }
  const branches = snapshot.technology?.branches || {};
  const symbols = {physics:'⚛',society:'♧',engineering:'⚙'};
  $('tech-branches').innerHTML = ['physics','society','engineering'].map(name => { const branch=branches[name] || {}; return `<article class="panel tech-card"><div class="tech-icon">${branch.current_id && !window.STELLARIS_WEB_MODE ? `<img src="/api/tech-icon?id=${encodeURIComponent(branch.current_id)}" alt="" onerror="this.hidden=true">` : symbols[name]}</div><span class="eyebrow">${name.toUpperCase()}</span><h2>${esc(name[0].toUpperCase()+name.slice(1))} research</h2><div class="tech-current"><span>CURRENT PROJECT</span><strong>${esc(branch.current || 'Choose research')}</strong><small>${branch.progress_known ? `${number(branch.progress)} saved progress` : 'Progress unknown'}${branch.started ? ` · since ${esc(branch.started)}` : ''}</small><small class="tech-trend">${esc(branch.trend?.observation || 'No comparable save yet.')}${branch.trend?.from_date ? ` ${esc(branch.trend.from_date)} → ${esc(branch.trend.to_date)}` : ''}</small></div><div class="tech-pick"><span class="eyebrow">SUGGESTED NEXT PICK</span><strong>${esc(branch.recommendation || 'Review options')}</strong><p>${esc(branch.reason || 'Compare the in-game effects with your current goal.')}</p></div>${branch.focus_path ? `<div class="tech-path"><span class="eyebrow">FOCUSED PATH · ${esc(branch.focus_path.target)}</span><div>${(branch.focus_path.steps || []).map(item => `<span class="path-node ${item.visible ? 'visible' : ''}">${esc(item.name)}</span>`).join('<span class="path-arrow">→</span>')}</div><small>${esc(branch.focus_path.caveat)}</small></div>` : ''}
      <div class="pill-row">${(branch.alternatives || []).map(item => `<span class="pill">${esc(item)}</span>`).join('')}</div></article>`; }).join('');
  ['physics','society','engineering'].forEach((name, index) => {
    const branch = branches[name] || {};
    const target = branch.focus_path?.target_id || branch.current_id || branch.alternative_ids?.[0];
    if (target) $('tech-branches').children[index]?.insertAdjacentHTML('beforeend', `<button type="button" class="button" data-tech-route="${esc(target)}">Explore ${esc(branch.focus_path?.target || branch.current || name + ' research')} route ↗</button>`);
  });
}

function renderShips(snapshot) {
  renderFleet(snapshot, state?.config || {});
}

function renderQuickActions() {
  const items = dynamicQuickQuestions(state?.snapshot, state?.advice, activeView);
  $('quick-actions').innerHTML = items.map(item =>
    `<button type="button" class="${item.urgent ? 'quick-urgent' : ''}" data-quick="${esc(item.text)}">${esc(item.text)}</button>`
  ).join('');
  document.querySelectorAll('[data-quick]').forEach(button => button.addEventListener('click', () => {
    $('question').value = `/ask ${button.dataset.quick}`;
    $('question').focus();
    updateCommandMenu();
  }));
}

function renderSignature(data) {
  const s = data?.snapshot;
  return JSON.stringify([
    data?.status, data?.error, data?.demo_preset, data?.save_token,
    s?.path, s?.modified, s?.date, s?.version, s?.campaign?.id,
    s?.campaign?.required_dlcs, s?.technology?.overview?.status,
    data?.config?.game_folder, data?.config?.provider, data?.config?.spoilers_active,
    data?.config?.fleet_limit, data?.pin?.key, (data?.history || []).length,
  ]);
}

function render(data, force = false) {
  state = data; token = data.token || token;
  setText('provider-label', providerName(data.config?.provider));
  $('spoiler-toggle').checked = Boolean(data.config?.spoilers_active);
  const sig = renderSignature(data);
  if (!force && sig === lastRenderKey && data.status === 'ready') {
    if ($('notice').textContent === 'Checking the save folder now…') showNotice('');
    return;
  }
  lastRenderKey = sig;
  if (data.status !== 'ready' || !data.snapshot) {
    setText('sync-title', data.status === 'error' ? 'Save check failed' : 'Waiting for a save');
    setText('sync-detail', data.web_mode ? 'Drop a .sav file or pick a demo' : 'Automatic every 15 seconds');
    $('goals').innerHTML = '<div class="empty">Choose a readable save to see your next moves.</div>';
    $('critical-risk').hidden = true;
    $('pin-notice').hidden = true;
    $('watchlist-ticker').hidden = true;
    if ($('campaign-benchmark')) $('campaign-benchmark').hidden = true;
    showNotice(data.error || 'Start Stellaris or choose the correct save folder in Settings.');
    return;
  }
  const snapshot = data.snapshot;
  showNotice('');
  setText('sync-title', data.web_mode ? 'Browser local mode' : 'Synced to latest autosave');
  setText('sync-detail', data.web_mode ? 'Saves stay in your browser' : 'Automatic every 15 seconds');
  const initialMessage = $('chat-log').querySelector('.message:only-child');
  if (initialMessage && initialMessage.textContent.startsWith('Your latest save will')) initialMessage.textContent = `Save ${snapshot.date} is ready. Ask about the page you are viewing.`;
  setText('campaign-label', snapshot.empire);
  const stamp = `${snapshot.path || ''}:${snapshot.modified || ''}:${JSON.stringify(snapshot.flag?.colors || [])}`;
  if (stamp !== flagStamp) {
    flagStamp = stamp;
    const flag = $('empire-flag');
    if (data.web_mode) {
      if (window.StellarisArt?.flagDataUrl) {
        flag.hidden = false;
        flag.src = window.StellarisArt.flagDataUrl(snapshot.flag);
      } else {
        flag.hidden = true;
      }
    } else {
      flag.hidden = false;
      flag.onerror = () => {
        flag.onerror = null;
        if (window.StellarisArt?.flagDataUrl) flag.src = window.StellarisArt.flagDataUrl(snapshot.flag);
        else flag.hidden = true;
      };
      flag.src = `/api/flag?v=${encodeURIComponent(stamp)}`;
    }
  } setText('game-date', `${snapshot.date} · ${snapshot.version}`);
  renderIndicators(snapshot); renderHealth(snapshot); renderMain(snapshot, data.advice || {});
  renderPlanets(snapshot); renderEmpiresView(snapshot); renderTech(snapshot); renderShips(snapshot); renderQuickActions();
}

async function fetchState() {
  try {
    if (window.STELLARIS_API?.getState) { render(await window.STELLARIS_API.getState()); return; }
    const response = await fetch('/api/state', {cache:'no-store'}); render(await response.json());
  }
  catch (error) { showNotice(`The local guide is not responding: ${error.message}`); }
}

function setView(view) {
  activeView = view;
  document.body.dataset.view = view;
  document.querySelectorAll('.tab').forEach(tab => tab.classList.toggle('active', tab.dataset.view === view));
  document.querySelectorAll('.view').forEach(panel => panel.classList.toggle('active', panel.id === `view-${view}`));
  setText('page-title', viewCopy[view][0]); setText('page-subtitle', viewCopy[view][1]);
  renderQuickActions();
}

function addMessage(text, type) {
  const div = document.createElement('div'); div.className = `message ${type}`; div.textContent = text; $('chat-log').appendChild(div); $('chat-log').scrollTop = $('chat-log').scrollHeight; return div;
}

function renderQuestionHistory(data) {
  questionHistory = data || {recent:[], frequent:[]};
  const sections = [
    ['Recent', 'recent', questionHistory.recent || []],
    ['Often asked', 'frequent', questionHistory.frequent || []]
  ];
  $('history-content').innerHTML = sections.map(([title, key, items]) => items.length
    ? `<div class="history-section">${title}</div>${items.map((item, index) => `<button class="history-item" type="button" data-history-section="${key}" data-history-index="${index}" title="Fill chat with this question"><span>${item.has_image ? '▣ ' : ''}${esc(item.question)}</span>${key === 'frequent' ? `<small>×${number(item.count)}</small>` : ''}</button>`).join('')}`
    : '').join('') || '<p class="empty">Questions you ask will appear here.</p>';
  $('clear-history').hidden = !(questionHistory.recent || []).length;
}

async function fetchQuestionHistory() {
  try { renderQuestionHistory(await post('/api/history')); }
  catch (error) { $('history-content').textContent = `History unavailable: ${error.message}`; }
}

function closeQuestionHistory() {
  $('question-history').hidden = true;
  $('history-toggle').setAttribute('aria-expanded', 'false');
}

function renderAttachment() {
  $('attachment-preview').hidden = !attachedImage;
  $('attachment-image').src = attachedImage || '';
  $('chat-hint').textContent = attachedImage
    ? state?.config?.provider === 'openrouter'
      ? 'Screenshot ready · Send uploads this image and question to OpenRouter'
      : 'Screenshot ready · Send shares this image with your selected local model'
    : defaultChatHint;
}

function closeScreenshot() {
  $('screenshot-overlay').hidden = true;
  $('capture-canvas').width = 0;
  $('capture-canvas').height = 0;
  $('crop-selection').hidden = true;
  $('use-crop').disabled = true;
  cropOrigin = null;
  cropBox = null;
}

function openCapturePreview(image, imageWidth, imageHeight) {
  const canvas = $('capture-canvas');
  canvas.width = imageWidth; canvas.height = imageHeight;
  canvas.getContext('2d').drawImage(image, 0, 0);
  const width = Math.max(100, Math.min(canvas.width, window.innerWidth - 80, 1100, Math.floor(window.innerHeight * .62 * canvas.width / canvas.height)));
  $('capture-stage').style.width = `${width}px`;
  $('capture-stage').style.height = `${Math.round(width * canvas.height / canvas.width)}px`;
  cropOrigin = null; cropBox = null;
  $('crop-selection').hidden = true; $('use-crop').disabled = true;
  $('screenshot-overlay').hidden = false;
  $('close-screenshot').focus();
}

async function captureNativeTarget(target) {
  const result = await post('/api/capture', {target});
  const image = new Image();
  await new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = () => reject(new Error('The captured frame could not be opened'));
    image.src = result.image;
  });
  openCapturePreview(image, image.naturalWidth, image.naturalHeight);
  $('capture-choice-overlay').hidden = true;
}

function showCaptureChoice(targets, reason = '') {
  $('capture-choice-hint').textContent = reason || (targets.stellaris?.length ? 'Choose a Stellaris window.' : 'No visible Stellaris window was found. Restore the game if minimized, or use borderless/windowed mode, then try again. You can also choose another window or the screen.');
  const windows = targets.windows || [];
  $('capture-choices').innerHTML = windows.map(item => `<button type="button" data-capture-target="${item.id}"><strong>${item.stellaris ? '★ Stellaris · ' : ''}${esc(item.title)}</strong><small>${esc(item.app || 'Window')}</small></button>`).join('') + '<button type="button" data-capture-target="screen"><strong>Entire screen</strong><small>All monitors; review before attaching</small></button>';
  document.querySelectorAll('[data-capture-target]').forEach(button => button.onclick = async () => {
    button.disabled = true;
    try { await captureNativeTarget(button.dataset.captureTarget); }
    catch (error) { $('capture-choice-hint').textContent = `Capture failed: ${error.message}. Choose another source.`; }
    finally { button.disabled = false; }
  });
  $('capture-choice-overlay').hidden = false;
}

async function captureScreenshot() {
  try {
    const targets = await post('/api/capture-targets');
    if (targets.native) {
      if (targets.stellaris?.length === 1) {
        try { await captureNativeTarget(targets.stellaris[0].id); return; }
        catch (error) { showCaptureChoice(targets, `Stellaris capture failed: ${error.message}. Choose a window or screen.`); return; }
      }
      showCaptureChoice(targets);
      return;
    }
  } catch (_) { /* Source mode may use the browser capture picker. */ }
  await captureBrowserScreenshot();
}

async function captureBrowserScreenshot() {
  if (!navigator.mediaDevices?.getDisplayMedia) {
    addMessage('This browser cannot capture the screen. Open Stellaris Guide in an up-to-date browser and try again.', 'warning');
    return;
  }
  let stream;
  try {
    // The browser asks the player which screen or window to share.
    stream = await navigator.mediaDevices.getDisplayMedia({video:true, audio:false});
    const video = document.createElement('video');
    video.muted = true;
    video.srcObject = stream;
    const ready = new Promise((resolve, reject) => {
      if (video.readyState >= 2 && video.videoWidth) resolve();
      else {
        video.addEventListener('loadeddata', resolve, {once:true});
        video.addEventListener('error', () => reject(new Error('The captured screen could not be read.')), {once:true});
      }
    });
    await video.play();
    await ready;
    if (!video.videoWidth || !video.videoHeight) throw new Error('The chosen screen has no image yet. Try again.');
    openCapturePreview(video, video.videoWidth, video.videoHeight);
  } catch (error) {
    if (!['NotAllowedError', 'AbortError'].includes(error.name)) addMessage(`Screenshot capture failed: ${error.message}`, 'warning');
  } finally {
    stream?.getTracks().forEach(track => track.stop());
  }
}

function cropPoint(event) {
  const bounds = $('capture-canvas').getBoundingClientRect();
  return {
    x: Math.max(0, Math.min(bounds.width, event.clientX - bounds.left)),
    y: Math.max(0, Math.min(bounds.height, event.clientY - bounds.top))
  };
}

function updateCropSelection(point) {
  if (!cropOrigin) return;
  const x = Math.min(cropOrigin.x, point.x), y = Math.min(cropOrigin.y, point.y);
  cropBox = {x, y, width:Math.abs(point.x - cropOrigin.x), height:Math.abs(point.y - cropOrigin.y)};
  const selection = $('crop-selection');
  selection.hidden = false;
  Object.assign(selection.style, {left:`${x}px`, top:`${y}px`, width:`${cropBox.width}px`, height:`${cropBox.height}px`});
  $('use-crop').disabled = cropBox.width < 16 || cropBox.height < 16;
}

function useScreenshotRegion(fullImage = false) {
  const source = $('capture-canvas');
  const bounds = source.getBoundingClientRect();
  if (!source.width || !source.height || (!fullImage && !cropBox)) return;
  const area = fullImage ? {x:0, y:0, width:bounds.width, height:bounds.height} : cropBox;
  const sx = Math.round(area.x * source.width / bounds.width);
  const sy = Math.round(area.y * source.height / bounds.height);
  const sw = Math.max(1, Math.round(area.width * source.width / bounds.width));
  const sh = Math.max(1, Math.round(area.height * source.height / bounds.height));
  const scale = Math.min(1, 1600 / Math.max(sw, sh));
  const crop = document.createElement('canvas');
  crop.width = Math.max(1, Math.round(sw * scale));
  crop.height = Math.max(1, Math.round(sh * scale));
  crop.getContext('2d').drawImage(source, sx, sy, sw, sh, 0, 0, crop.width, crop.height);
  const image = crop.toDataURL('image/jpeg', .82);
  if (image.length > 5_000_000) {
    addMessage('That image is too large. Select a smaller region and try again.', 'warning');
    return;
  }
  attachedImage = image;
  renderAttachment();
  closeScreenshot();
  $('question').focus();
}

async function sendQuestion() {
  const image = attachedImage;
  let question = $('question').value.trim();
  if (!question && !image) return;
  if (!question) question = 'What is shown in this screenshot, and what should I do next?';
  if (image && (state?.config?.provider === 'off' || !state?.config?.model)) {
    addMessage('Screenshot analysis needs a vision-capable model. Choose Ollama, LM Studio, or OpenRouter in Settings, then try again.', 'warning');
    return;
  }
  addMessage(`${question}${image ? '\n▣ Selected screenshot attached' : ''}`, 'user');
  $('question').value = ''; updateCommandMenu();
  const thinking = addMessage(`${providerName(state?.config?.provider)} is thinking…`, 'thinking');
  $('send-btn').disabled = true; $('capture-btn').disabled = true;
  try {
    const result = await post('/api/ask', {question, context:activeView, image});
    thinking.remove(); addMessage(result.answer, 'assistant'); setText('provider-label', result.source);
    if (result.history) renderQuestionHistory(result.history);
    if (result.warning) addMessage(`AI provider issue: ${result.warning}`, 'warning');
    if (!image || result.image_analyzed) { attachedImage = null; renderAttachment(); }
    else $('question').value = question;
  } catch (error) { thinking.remove(); addMessage(error.message, 'warning'); $('question').value = question; }
  finally { $('send-btn').disabled = false; $('capture-btn').disabled = false; $('question').focus(); }
}

function updateCommandMenu() {
  const value = $('question').value;
  $('command-menu').hidden = !(value.startsWith('/') && !value.includes(' '));
}

function providerChanged() {
  const value = $('provider').value;
  $('key-wrap').hidden = value !== 'openrouter';
  setText('model-help', value === 'off' ? 'Common save questions work without AI. Screenshots need a vision-capable model.' : value === 'lmstudio' ? 'Start the LM Studio server on port 1234. Choose a vision-capable model for screenshots.' : value === 'ollama' ? 'Use an installed Ollama model. Screenshots need a vision-capable model.' : 'Use an OpenRouter model ID with image support for screenshots. Availability and free limits vary.');
  renderAttachment();
}

function openSettings() {
  const config = state?.config || {};
  $('save-folder').value = config.save_folder || ''; $('game-folder').value = config.game_folder || ''; $('provider').value = config.provider || 'off'; $('model').value = config.model || ''; $('api-key').value = ''; providerChanged();
  $('spoiler-toggle').checked = Boolean(config.spoilers_active);
  $('settings-overlay').hidden = false; $('save-folder').focus();
}

document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => setView(tab.dataset.view)));
$('tech-branches').addEventListener('click', async event => {
  const button = event.target.closest('[data-tech-route]');
  const campaign = state?.snapshot?.campaign?.id;
  if (!button || !campaign) return;
  const target = button.dataset.techRoute;
  if (window.STELLARIS_WEB_MODE && window.STELLARIS_API?.openTechRouteModal) {
    setText('tech-route-status', '');
    window.STELLARIS_API.openTechRouteModal(target);
    return;
  }
  if (/Edg\//.test(navigator.userAgent) && !window.chrome?.webview) {
    const url = `/tech-route.html?campaign=${encodeURIComponent(campaign)}&target=${encodeURIComponent(target)}`;
    techRouteWindow = window.open(url, 'StellarisGuideTechRoute', 'popup=yes,width=1080,height=780');
    if (techRouteWindow) techRouteWindow.focus();
    else setText('tech-route-status', 'The route window was blocked. Allow popups for this local Guide and try again.');
  } else {
    try {
      await post('/api/tech-route/open', {campaign_id:campaign, target});
      setText('tech-route-status', 'Technology route opened in Microsoft Edge.');
    } catch (error) {
      setText('tech-route-status', error.message);
    }
  }
});
document.querySelectorAll('#empire-category-tabs button').forEach(button => button.addEventListener('click', () => {
  empireCategory = button.dataset.category;
  if (state?.snapshot) renderEmpiresView(state.snapshot);
}));
document.querySelectorAll('#galaxy-tabs button').forEach(button => button.addEventListener('click', () => {
  galaxyMetric = button.dataset.galaxyMetric;
  if (state?.snapshot) renderEmpires(state.snapshot);
}));
$('watchlist-prev').addEventListener('click', () => moveWatchlist(-1));
$('watchlist-next').addEventListener('click', () => moveWatchlist(1));
$('goals').addEventListener('click', async event => {
  const button = event.target.closest('[data-pin-goal]');
  const snapshot = state?.snapshot;
  if (!button || !snapshot) return;
  const goal = (state.advice?.goal_catalog || state.advice?.goals || []).find(item => item.key === button.dataset.pinGoal);
  if (!goal) return;
  const current = pinnedGoal(snapshot);
  try {
    const result = await post('/api/pin', {campaign_id:campaignPinId(snapshot), goal_key:current?.key === goal.key ? null : goal.key});
    state.pin = result.pin;
    renderMain(snapshot, state.advice || {});
  } catch (error) {
    showNotice(error.message);
    await fetchState();
  }
});
$('pin-notice').addEventListener('click', async event => {
  if (event.target.id !== 'clear-dormant-pin' || !state?.snapshot) return;
  try {
    const result = await post('/api/pin', {campaign_id:campaignPinId(state.snapshot), goal_key:null});
    state.pin = result.pin;
    renderMain(state.snapshot, state.advice || {});
  } catch (error) { showNotice(error.message); }
});
scheduleWatchlistAdvance();
$('open-empires').addEventListener('click', () => setView('empires'));
document.querySelectorAll('#trend-switch button').forEach(button => button.addEventListener('click', () => { trendMetric = button.dataset.metric; document.querySelectorAll('#trend-switch button').forEach(item => item.classList.toggle('active', item === button)); renderChart(state?.history || []); }));
$('history-toggle').addEventListener('click', () => {
  const opening = $('question-history').hidden;
  $('question-history').hidden = !opening;
  $('history-toggle').setAttribute('aria-expanded', String(opening));
});
$('history-content').addEventListener('click', event => {
  const button = event.target.closest('[data-history-section]');
  if (!button) return;
  const item = questionHistory[button.dataset.historySection]?.[Number(button.dataset.historyIndex)];
  if (!item) return;
  $('question').value = item.question;
  $('chat-hint').textContent = item.has_image && !attachedImage ? 'Attach a new screenshot with the camera before sending.' : defaultChatHint;
  updateCommandMenu(); closeQuestionHistory(); $('question').focus();
});
$('clear-history').addEventListener('click', async () => {
  if (!window.confirm('Clear saved question history on this PC?')) return;
  try { renderQuestionHistory(await post('/api/history/clear')); }
  catch (error) { addMessage(`Could not clear history: ${error.message}`, 'warning'); }
});
document.addEventListener('click', event => { if (!event.target.closest('.history-wrap')) closeQuestionHistory(); });
$('capture-btn').addEventListener('click', captureScreenshot);
$('remove-attachment').addEventListener('click', () => { attachedImage = null; renderAttachment(); });
$('close-screenshot').addEventListener('click', closeScreenshot);
$('screenshot-overlay').addEventListener('click', event => { if (event.target === $('screenshot-overlay')) closeScreenshot(); });
$('use-full-screenshot').addEventListener('click', () => useScreenshotRegion(true));
$('use-crop').addEventListener('click', () => useScreenshotRegion(false));
$('capture-canvas').addEventListener('pointerdown', event => {
  if (event.button !== 0) return;
  cropOrigin = cropPoint(event);
  updateCropSelection(cropOrigin);
  $('capture-canvas').setPointerCapture(event.pointerId);
});
$('capture-canvas').addEventListener('pointermove', event => { if (cropOrigin) updateCropSelection(cropPoint(event)); });
$('capture-canvas').addEventListener('pointerup', event => {
  if (cropOrigin) updateCropSelection(cropPoint(event));
  cropOrigin = null;
  if ($('capture-canvas').hasPointerCapture(event.pointerId)) $('capture-canvas').releasePointerCapture(event.pointerId);
});
$('capture-canvas').addEventListener('pointercancel', () => { cropOrigin = null; });
$('ask-form').addEventListener('submit', event => { event.preventDefault(); sendQuestion(); });
$('question').addEventListener('input', updateCommandMenu);
$('question').addEventListener('keydown', event => {
  if (event.key === 'Tab' && !$('command-menu').hidden) { event.preventDefault(); $('question').value = '/ask '; $('command-menu').hidden = true; }
  else if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendQuestion(); }
});
$('command-menu').querySelector('button').addEventListener('click', () => { $('question').value='/ask '; $('command-menu').hidden=true; $('question').focus(); });
$('refresh-btn').addEventListener('click', async () => { try { showNotice('Checking the save folder now…'); await post('/api/refresh'); await fetchState(); } catch (error) { showNotice(error.message); } });
$('feedback-btn').addEventListener('click', () => { $('feedback-overlay').hidden = false; $('feedback-rating').value = ''; document.querySelectorAll('[data-feedback-rating]').forEach(button => button.classList.remove('active')); $('feedback-error').textContent = ''; }); $('close-feedback').addEventListener('click', () => $('feedback-overlay').hidden = true); document.querySelectorAll('[data-feedback-rating]').forEach(button => button.addEventListener('click', () => { $('feedback-rating').value = button.dataset.feedbackRating; document.querySelectorAll('[data-feedback-rating]').forEach(item => item.classList.toggle('active', item === button)); })); $('feedback-form').addEventListener('submit', async event => { event.preventDefault(); setText('feedback-error', ''); try { await post('/api/feedback', {rating:$('feedback-rating').value, reason:$('feedback-reason').value, comment:$('feedback-comment').value, view:activeView}); $('feedback-overlay').hidden = true; $('feedback-form').reset(); showNotice('Thanks — your feedback was saved on this PC.', 'success'); } catch (error) { setText('feedback-error', error.message); } }); $('settings-btn').addEventListener('click', openSettings); $('close-settings').addEventListener('click', () => $('settings-overlay').hidden=true);
$('spoiler-toggle').addEventListener('change', async event => {
  if (event.target.checked) {
    event.target.checked = false;
    $('spoiler-ack').checked = false;
    $('spoiler-enable').disabled = true;
    $('spoiler-overlay').hidden = false;
    $('spoiler-ack').focus();
  } else {
    try { await post('/api/spoilers', {enable:false}); await fetchState(); }
    catch (error) { setText('settings-error', error.message); event.target.checked = true; }
  }
});
$('spoiler-ack').addEventListener('change', () => { $('spoiler-enable').disabled = !$('spoiler-ack').checked; });
function cancelSpoilerConsent() { $('spoiler-overlay').hidden = true; $('spoiler-toggle').checked = false; }
$('spoiler-cancel').addEventListener('click', cancelSpoilerConsent);
$('spoiler-overlay').addEventListener('click', event => { if (event.target === $('spoiler-overlay')) cancelSpoilerConsent(); });
$('spoiler-enable').addEventListener('click', async () => {
  if (!$('spoiler-ack').checked) return;
  $('spoiler-enable').disabled = true;
  try {
    await post('/api/spoilers', {enable:true, acknowledged:true, confirmation:'ENABLE SPOILERS'});
    $('spoiler-overlay').hidden = true;
    await fetchState();
  } catch (error) { setText('settings-error', error.message); $('spoiler-enable').disabled = false; }
});
$('close-capture-choice').addEventListener('click', () => { $('capture-choice-overlay').hidden = true; });
$('capture-choice-overlay').addEventListener('click', event => { if (event.target === $('capture-choice-overlay')) $('capture-choice-overlay').hidden = true; });
$('settings-overlay').addEventListener('click', event => { if (event.target === $('settings-overlay')) $('settings-overlay').hidden=true; });
$('provider').addEventListener('change', providerChanged);
$('browse-folder').addEventListener('click', async () => { try { const result=await post('/api/choose-folder'); if (result.folder) $('save-folder').value=result.folder; } catch(error) { setText('settings-error', error.message); } });
$('settings-form').addEventListener('submit', async event => { event.preventDefault(); setText('settings-error',''); try { await post('/api/config',{save_folder:$('save-folder').value,game_folder:$('game-folder').value,provider:$('provider').value,model:$('model').value,api_key:$('api-key').value}); $('settings-overlay').hidden=true; await fetchState(); } catch(error) { setText('settings-error',error.message); } });
$('quit-btn').addEventListener('click', async () => { try { await post('/api/quit'); document.body.innerHTML='<div style="padding:60px;color:#eef6fb;font-family:Segoe UI;background:#07111d;min-height:100vh"><h1>Stellaris Guide has closed.</h1><p>You can close this browser tab.</p></div>'; } catch(error) { setText('settings-error',error.message); } });
window.addEventListener('keydown', event => {
  if (event.key === 'Escape') { $('settings-overlay').hidden=true; closeQuestionHistory(); closeScreenshot(); }
});

fetchState().then(() => { if (token) fetchQuestionHistory(); });
setInterval(fetchState, 15000);

