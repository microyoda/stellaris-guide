const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);
const campaign = params.get('campaign') || '';
const instance = params.get('instance') || '';
let target = params.get('target') || '';
let targets = [];
let route = null;
let stopped = false;

if (instance) document.title = `Stellaris Guide Research Route ${instance}`;

function node(tag, text = '', className = '') {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}
function art(id, className = '') {
  const wrap = node('span', '', className);
  const img = node('img');
  img.alt = '';
  img.src = `/api/tech-icon?id=${encodeURIComponent(id)}`;
  const fallback = node('span', '✦', 'fallback-art');
  fallback.hidden = true;
  img.addEventListener('error', () => { img.hidden = true; fallback.hidden = false; });
  wrap.append(img, fallback);
  return wrap;
}
function message(text, warning = false) {
  $('message').textContent = text;
  $('message').classList.toggle('warning', warning);
}
async function getJson(url) {
  const response = await fetch(url, {cache: 'no-store'});
  const body = await response.json();
  if (!response.ok) throw Object.assign(new Error(body.error || 'Route could not be loaded.'), {status: response.status});
  return body;
}
const GOALS = [
  {id:'tech_power_hub_2', label:'More energy'},
  {id:'tech_cruisers', label:'Bigger warships'},
  {id:'tech_basic_science_lab_2', label:'Faster research'},
  {id:'tech_alloys_2', label:'More alloys'}
];

function renderPicker(query = '') {
  const known = new Map(targets.map(tech => [tech.id, tech]));
  const cards = GOALS.filter(goal => known.has(goal.id)).map(goal => {
    const tech = known.get(goal.id);
    const button = node('button', '', `goal-card${target === goal.id ? ' active' : ''}`);
    button.type = 'button';
    button.append(art(goal.id));
    const copy = node('span');
    copy.append(node('strong', goal.label), node('small', tech.name));
    button.append(copy);
    button.addEventListener('click', () => choose(goal.id));
    return button;
  });
  $('goal-cards').replaceChildren(...cards);
  const match = query.trim().toLocaleLowerCase();
  const visible = targets.filter(tech => !match || `${tech.name} ${tech.id}`.toLocaleLowerCase().includes(match));
  const selected = known.get(target);
  const shown = visible.slice(0, 100);
  if (selected && !shown.some(tech => tech.id === target)) shown.unshift(selected);
  const select = $('target-select');
  select.replaceChildren(...shown.map(tech => {
    const option = node('option', `${tech.name} · ${tech.area || 'other'} · ${tech.state.replaceAll('_', ' ')}`);
    option.value = tech.id;
    return option;
  }));
  select.disabled = !shown.length;
  if (selected) select.value = target;
  if (match && !visible.length) message('No matching installed technology found.', true);
}

function renderDetail(step) {
  const panel = $('tech-detail');
  const byId = new Map((route.map_nodes || route.steps).map(item => [item.id, item]));
  const children = [node('span', `${(step.area || 'Research').toUpperCase()} · ${step.tier === null ? 'Tier unverified' : `Tier ${step.tier}`}`, 'eyebrow')];
  const title = node('div', '', 'detail-heading');
  title.append(art(step.id), node('h3', step.name));
  children.push(title, node('p', step.display_state));
  children.push(node('span', 'WHAT THIS RESEARCH IS', 'detail-label'),
    node('p', step.description || 'No plain-language description was verified in the installed game files.', 'detail-explanation'));
  children.push(node('span', 'WHY IT MAY MATTER', 'detail-label'),
    node('p', step.benefit || 'Specific benefits are unverified. Check the technology card in game.', 'detail-explanation'));
  if (step.gate && step.gate.state === 'closed') {
    children.push(node('p', `Tier ${step.tier} needs ${step.gate.required - step.gate.count} more previous-tier ${step.area} technologies.`, 'detail-warning'));
  }
  const needs = node('ul');
  for (const prerequisite of step.direct_prerequisites || []) {
    needs.append(node('li', `${prerequisite.name} · ${prerequisite.state.replaceAll('_', ' ')}`));
  }
  children.push(node('span', 'DIRECT PREREQUISITES', 'detail-label'), needs.children.length ? needs : node('p', 'None in the installed definition.'));
  for (const group of (route.one_of || []).filter(item => item.for_id === step.id)) {
    children.push(node('p', `Choose one: ${group.options.map(option => `${option.name} (${option.state.replaceAll('_', ' ')})`).join(' or ')}`));
  }
  if (step.alternative_for) children.push(node('p', 'This is one possible prerequisite. Its earlier requirements may need checking in game.', 'detail-warning'));
  const leads = step.id === route.target_id && step.state === 'researched'
    ? (route.next_unlocks || []).filter(item => item.distance === 1).map(item => item.name)
    : (route.map_edges || route.edges).filter(edge => edge.from === step.id).map(edge => byId.get(edge.to)?.name || edge.to);
  children.push(node('span', 'LEADS TO', 'detail-label'), node('p', leads.join(', ') || 'This is the selected goal.'));
  children.push(node('span', 'AVAILABILITY', 'detail-label'));
  children.push(node('p', step.eligibility === 'confirmed' ? 'Seen in your selected save.' :
    step.eligibility === 'blocked' ? 'A listed prerequisite or tier gate is still blocking this route.' :
    'Other eligibility and draw rules may apply. Check the game’s research cards.',
    step.eligibility === 'unverified' ? 'detail-warning' : ''));
  if (!step.localized) children.push(node('p', 'Installed English label unavailable; this name is derived from its ID.', 'detail-warning'));
  panel.replaceChildren(...children);
  document.querySelectorAll('.map-node').forEach(button => button.classList.toggle('selected', button.dataset.id === step.id));
}

function renderMap() {
  const map = $('route-map');
  const steps = route.map_nodes || route.steps || [];
  const areas = ['physics', 'society', 'engineering', 'other'].filter(area => steps.some(step => (step.area || 'other') === area));
  const maxColumn = Math.max(0, ...steps.map(step => step.column || 0));
  const colWidth = 225, nodeHeight = 100;
  const rows = new Map();
  const counts = new Map();
  for (const step of steps) {
    const key = `${step.area || 'other'}:${step.column || 0}`;
    rows.set(step.id, counts.get(key) || 0);
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  const laneHeight = area => 67 + nodeHeight * Math.max(1, ...Array.from({length:maxColumn + 1}, (_, col) => counts.get(`${area}:${col}`) || 0));
  const yStarts = new Map();
  let height = 0;
  for (const area of areas) { yStarts.set(area, height); height += laneHeight(area); }
  const width = Math.max(map.parentElement.clientWidth - 36, (maxColumn + 1) * colWidth + 28);
  map.style.width = `${width}px`;
  map.style.height = `${height}px`;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'route-edges');
  svg.setAttribute('width', String(width));
  svg.setAttribute('height', String(height));
  const byId = new Map(steps.map(step => [step.id, step]));
  const position = step => ({x:14 + (step.column || 0) * colWidth, y:yStarts.get(step.area || 'other') + 50 + rows.get(step.id) * nodeHeight});
  for (const edge of route.map_edges || route.edges || []) {
    const from = byId.get(edge.from), to = byId.get(edge.to);
    if (!from || !to) continue;
    const a = position(from), b = position(to);
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M ${a.x + 190} ${a.y + 43} C ${a.x + 211} ${a.y + 43}, ${b.x - 22} ${b.y + 43}, ${b.x} ${b.y + 43}`);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', from.state === 'researched' ? '#41cf91' : edge.type === 'one_of' ? '#f5bc49' : '#7595b0');
    path.setAttribute('stroke-width', edge.to === route.target_id ? '3' : '2');
    path.setAttribute('opacity', edge.to === route.target_id ? '1' : '0.48');
    if (from.state !== 'researched' || edge.type === 'one_of') path.setAttribute('stroke-dasharray', '5 5');
    svg.append(path);
  }
  const fragments = [svg];
  for (let col = 0; col <= maxColumn; col++) {
    const guide = node('span', `STEP ${col + 1}`, 'map-column');
    guide.style.left = `${14 + col * colWidth}px`;
    fragments.push(guide);
  }
  for (const area of areas) {
    const lane = node('div', area.toUpperCase(), 'map-lane');
    lane.style.top = `${yStarts.get(area) + 22}px`;
    fragments.push(lane);
  }
  for (const step of steps) {
    const button = node('button', '', `map-node ${step.state === 'saved_option' ? 'saved_option' : step.state === 'researched' ? 'researched' : step.state === 'researching' ? 'researching' : step.eligibility === 'blocked' ? 'blocked' : 'prerequisites_met'}${step.id === route.target_id ? ' goal' : ''}`);
    button.type = 'button';
    button.dataset.id = step.id;
    button.setAttribute('aria-label', `${step.name}, ${step.display_state}`);
    const xy = position(step);
    button.style.left = `${xy.x}px`;
    button.style.top = `${xy.y}px`;
    button.append(art(step.id));
    const copy = node('span');
    copy.append(node('strong', step.name), node('small', step.display_state));
    button.append(copy);
    button.addEventListener('click', () => renderDetail(step));
    fragments.push(button);
  }
  map.replaceChildren(...fragments);
  renderDetail(steps.find(step => step.state === 'saved_option') || steps.find(step => step.id === route.target_id) || steps[0]);
}

function renderNextUnlocks(data) {
  const items = data.next_unlocks || [];
  $('next-tech-section').hidden = data.steps?.at(-1)?.state !== 'researched' || !items.length;
  for (const [distance, id] of [[1, 'next-tech-direct'], [2, 'next-tech-later']]) {
    const cards = items.filter(item => item.distance === distance).map(item => {
      const card = node('button', '', 'next-tech-card');
      card.type = 'button';
      const copy = node('span');
      const relation = item.relation === 'one_of' ? 'One possible route' :
        distance === 1 ? 'Directly depends on this' : 'Further research path';
      const state = item.state === 'researched' ? 'Researched' :
        item.state === 'researching' ? 'Researching' :
        item.state === 'saved_option' ? 'On your cards' :
        item.dlc?.some(required => required.status !== 'present') ? 'Required DLC not confirmed' :
        item.missing_prerequisites.length ? 'Other prerequisites needed' :
        item.missing_alternative_groups.length ? 'One alternative needed' :
        item.tier_gate === 'closed' ? 'Tier gate not met' :
        'Listed prerequisites met; draw unverified';
      copy.append(node('strong', item.name),
        node('small', `${relation} · ${item.tier === null ? 'Tier unverified' : `Tier ${item.tier}`} · ${state}`));
      card.append(art(item.id, 'art'), copy);
      card.setAttribute('aria-label', `Explore route to ${item.name}. ${relation}. ${state}.`);
      card.addEventListener('click', () => choose(item.id));
      return card;
    });
    $(id).replaceChildren(...(cards.length ? cards : [node('p', 'No linked technology in this step.')]));
  }
}

function renderFuture(data) {
  const researched = data.steps?.at(-1)?.state === 'researched';
  const items = (data.future_opportunities || []).filter(item => !researched || item.distance > 2);
  $('future-section').hidden = !items.length;
  const cards = items.slice(0, 18).map(item => {
    const card = node('button', '', 'next-tech-card');
    card.type = 'button';
    const copy = node('span');
    const chain = item.path.map(link => link.name).join(' → ');
    const caveat = item.state !== 'unmet' ? 'Observed in selected save; verify current game state'
      : item.dlc?.some(required => required.status !== 'present')
      ? 'Required DLC unconfirmed' : item.draw_conditions_unverified
        ? 'Other draw conditions may apply' : 'Other eligibility may apply';
    copy.append(node('strong', item.name),
      node('small', `${item.distance} ${item.distance === 1 ? 'link' : 'links'} away · ${item.relation === 'one_of' ? 'one possible branch' : 'direct dependency chain'}`),
      node('small', item.state === 'saved_option' ? 'On your saved research cards' :
        item.state === 'researching' ? 'Researching in selected save' :
        item.state === 'researched' ? 'Already researched' : 'Possible later research'),
      node('small', chain),
      node('small', item.description || 'Description unavailable in installed game files.'),
      ...(item.blockers || []).map(blocker => node('small', blocker)),
      node('small', `${item.benefit} ${caveat}.`));
    card.append(art(item.id, 'art'), copy);
    card.setAttribute('aria-label', `Inspect possible route to ${item.name}. ${item.distance} links away.`);
    card.addEventListener('click', () => choose(item.id));
    return card;
  });
  if (items.length > 18) cards.push(node('p', `Showing the nearest 18 of ${items.length} linked technologies. Search for another target above.`));
  $('future-list').replaceChildren(...cards);
}

function renderRoute(data) {
  route = data;
  if (!data.steps?.length) {
    $('route-content').hidden = true;
    $('next-tech-section').hidden = true;
    $('future-section').hidden = true;
    message(data.reason || 'A route could not be verified for this save.', true);
    return;
  }
  $('route-content').hidden = false;
  $('save-context').textContent = `${data.empire || 'Your empire'} · ${data.date || 'Save date unavailable'} · ${data.release || 'Release unavailable'}`;
  $('route-status').textContent = data.status === 'verified_base_game' ? 'Matching base-game route' : 'Limited route · check in game';
  $('route-status').classList.toggle('warn', data.status !== 'verified_base_game');
  message('');
  $('route-title').textContent = data.name || data.target_id;
  $('target-description').textContent = data.description || 'In-game description unavailable from installed files.';
  $('target-benefit').textContent = data.benefit || 'Specific benefits are unverified; inspect its game card.';
  const researchedTarget = data.steps.at(-1).state === 'researched';
  $('map-title').textContent = `${researchedTarget ? 'Completed path from' : 'Full remaining chain to'} ${data.name || data.target_id}`;
  $('route-meta').textContent = researchedTarget
    ? `${data.area || 'Research'} · Researched in this save`
    : `${data.area || 'Research'} · ${data.steps.length} technologies on this path`;
  $('route-warning').hidden = data.status === 'verified_base_game';
  $('route-warning').textContent = data.reason || '';
  const img = $('target-icon');
  img.hidden = false;
  $('target-fallback').hidden = true;
  img.src = `/api/tech-icon?id=${encodeURIComponent(data.target_id)}`;
  img.onerror = () => { img.hidden = true; $('target-fallback').hidden = false; };
  $('route-progress').textContent = `${data.progress?.done || 0} of ${data.progress?.total || 0} route milestones complete`;
  $('route-progress-bar').style.width = `${data.progress?.total ? Math.min(100, 100 * data.progress.done / data.progress.total) : 0}%`;
  renderNextUnlocks(data);
  renderFuture(data);
  $('next-actions').replaceChildren(...(data.next_actions || [data.next_check]).map(action => node('li', action)));
  $('route-checklist').replaceChildren(...data.steps.map(step => {
    const row = node('li', `${step.name} · ${step.display_state}`, step.state === 'researched' ? 'done' : '');
    return row;
  }), ...(data.one_of || []).map(group => node('li',
    `Choose one for ${group.for_name}: ${group.options.map(option => option.name).join(' or ')}`,
    group.options.some(option => option.state === 'researched') ? 'done' : '')));
  $('route-gates').replaceChildren(...(data.route_gates || []).map(gate => {
    const row = node('div', '', `gate-row ${gate.state}`);
    const title = node('div');
    title.append(node('strong', `${gate.area} Tier ${gate.tier}`), node('small', gate.state === 'open' ? 'Open' : gate.state === 'closed' ? `Need ${gate.required - gate.count} more` : 'Check in game'));
    const track = node('div', '', 'progress-track');
    const bar = node('span');
    bar.style.width = gate.required ? `${Math.min(100, 100 * gate.count / gate.required)}%` : '0%';
    track.append(bar);
    row.append(title, track, node('small', gate.required === null ? 'Tier rule unavailable' : `${gate.display_count} / ${gate.required} previous-tier technologies`));
    return row;
  }));
  renderMap();
}

async function choose(nextTarget) {
  if (!nextTarget || stopped) return;
  target = nextTarget;
  params.set('target', target);
  history.replaceState(null, '', `${location.pathname}?${params}`);
  renderPicker($('target-search').value);
  try { renderRoute(await getJson(`/api/tech-route?${new URLSearchParams({campaign, target})}`)); }
  catch (error) { if (error.status === 409) stopped = true; message(error.message, true); }
}

$('target-search').addEventListener('input', event => renderPicker(event.target.value));
$('target-select').addEventListener('change', event => choose(event.target.value));
$('close-route').addEventListener('click', async () => {
  if (instance) {
    try {
      const response = await fetch('/api/tech-route/close', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({instance})});
      if (!response.ok) throw new Error('Could not close Edge automatically.');
      return;
    } catch (error) { message(`${error.message} Use the window X.`, true); }
  } else window.close();
});

async function start() {
  try {
    const data = await getJson(`/api/tech-route/targets?${new URLSearchParams({campaign})}`);
    targets = data.targets || [];
    if (!target || !targets.some(tech => tech.id === target)) target = targets.find(tech => tech.id === 'tech_power_hub_2')?.id || targets[0]?.id || '';
    renderPicker();
    if (target) await choose(target);
    else message('No installed technologies are available for this selected save.', true);
  } catch (error) { if (error.status === 409) stopped = true; message(error.message, true); }
}
start();
setInterval(async () => {
  if (stopped || !target) return;
  try {
    const data = await getJson(`/api/tech-route?${new URLSearchParams({campaign, target})}`);
    if (!route || data.modified !== route.modified) renderRoute(data);
  } catch (error) { if (error.status === 409) stopped = true; message(error.message, true); }
}, 15000);
