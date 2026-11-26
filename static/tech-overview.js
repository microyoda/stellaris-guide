/* Research-slot presentation. The saved alternatives are confirmed; tier gates are base-game checks. */
function renderTechOverview(snapshot) {
  const technology = snapshot.technology || {};
  const branches = technology.branches || {};
  const overview = technology.overview || {};
  const names = overview.labels || {};
  const icons = {physics:'⚛', society:'✥', engineering:'⚙'};
  const title = value => value.charAt(0).toUpperCase() + value.slice(1);
  const routeButton = (id, label, accessibleLabel=label) => id ? `<button type="button" class="research-route-link" data-tech-route="${esc(id)}" aria-label="${esc(accessibleLabel)}">${esc(label)} ↗</button>` : '';
  const isWeb = typeof window !== 'undefined' && Boolean(window.STELLARIS_WEB_MODE);
  const techImg = id => (!isWeb && id) ? `<img src="/api/tech-icon?id=${encodeURIComponent(id)}" alt="">` : '';
  const card = area => {
    const branch = branches[area] || {};
    const currentId = branch.current_id || '';
    const currentName = names[currentId] || branch.current || 'Choose research in game';
    const alternatives = branch.alternative_ids || [];
    const gate = overview.gates?.[area];
    const gateLabel = !gate || gate.required == null ? 'Tier rule unavailable' :
      gate.status === 'unverified' ? (gate.required === 0 ? 'No base-game count needed · verify mods' : `Base-game count ${gate.display_count} / ${gate.required} · verify mods`) :
      gate.required === 0 ? 'No Tier 1 count needed for Tier 2' :
      gate.status === 'open' ? `Tier 2 open · ${gate.display_count} / ${gate.required}` :
      `Tier 2 needs ${gate.required - gate.count} more · ${gate.display_count} / ${gate.required}`;
    const gatePercent = gate?.required ? Math.min(100, 100 * gate.count / gate.required) : 0;
    return `<article class="research-slot ${area}">
      <div class="research-slot-head"><span class="research-area-icon">${icons[area]}</span><strong>${title(area)}</strong><small>Research slot</small></div>
      <div class="research-current"><span class="eyebrow">RESEARCHING NOW</span><div class="research-project">
        <span class="research-art">${techImg(currentId)}<i>${icons[area]}</i></span>
        <div><strong>${esc(currentName)}</strong><small>${branch.progress_known ? `${number(branch.progress)} saved progress` : 'Progress not recorded'}${branch.started ? ` · since ${esc(branch.started)}` : ''}</small></div></div>
        <p>${esc(branch.trend?.observation || 'A completion estimate is not available from this save.')}</p>
        ${routeButton(currentId, 'See current route', `Explore route for ${currentName}`)}</div>
      <div class="research-options"><span class="eyebrow">YOUR CARDS RIGHT NOW <small>${alternatives.length} OPTIONS</small></span>
        ${alternatives.length ? alternatives.map((id, index) => {
          const name = names[id] || branch.alternatives?.[index] || id;
          const suggested = String(branch.alternatives?.[index] || name).toLowerCase() === String(branch.recommendation || '').toLowerCase();
          return `<div class="research-option ${suggested ? 'suggested' : ''}"><span class="research-art">${techImg(id)}<i>${icons[area]}</i></span>
            <div><strong>${esc(name)}</strong><small>${suggested ? 'Suggested for your current bottleneck · ' : ''}On your saved research cards</small></div>${routeButton(id, 'Route', `Explore route for ${name}`)}</div>`;
        }).join('') : '<p class="research-empty">No alternatives could be read from this save. Check the in-game research screen.</p>'}</div>
      <button type="button" class="research-tier" data-tier-toggle="${area}" aria-expanded="false">
        <span>Next tier · ${title(area)} Tier 2</span><strong>${esc(gateLabel)}</strong>
        <span class="research-tier-track"><i style="width:${gatePercent}%"></i></span></button>
      <div class="research-tier-detail" data-tier-detail="${area}" hidden>
        <p>${gate?.required === 0 ? 'The installed base-game rule requires no Tier 1 research count for Tier 2.' : `A tier gate counts researched Tier 1 ${area} technologies.`} A met gate does not guarantee a particular card will appear.${gate?.status === 'unverified' ? ' Mods may change this rule; verify it in game.' : ''}</p>
        ${gate?.completed?.length ? `<small>Recorded Tier 1 research: ${gate.completed.map(esc).join(', ')}</small>` : '<small>No completed Tier 1 names available.</small>'}
        ${gate?.on_cards?.length ? `<p>Tier 1 cards that may advance this gate:</p><div>${gate.on_cards.map(item => routeButton(item.id, item.name, `Explore route for ${item.name}`)).join('')}</div>` : ''}
      </div>
    </article>`;
  };
  $('tech-branches').innerHTML = ['physics','society','engineering'].map(card).join('');
  $('tech-branches').querySelectorAll('.research-art img').forEach(img => {
    img.addEventListener('error', () => { img.hidden = true; });
  });
  $('tech-branches').querySelectorAll('[data-tier-toggle]').forEach(button => {
    button.addEventListener('click', () => {
      const detail = $('tech-branches').querySelector(`[data-tier-detail="${button.dataset.tierToggle}"]`);
      detail.hidden = !detail.hidden;
      button.setAttribute('aria-expanded', String(!detail.hidden));
    });
  });
}
