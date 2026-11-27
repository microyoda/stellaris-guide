/* Fleet observations and planning use the selected save. A manual naval limit is
   kept by the local app per campaign because the save cannot verify that maximum. */
let fleetClass = null;
let fleetDesignId = null;
let fleetTargetId = null;
let fleetPlan = {};
let fleetCompare = [];
let fleetCampaign = null;
let fleetGoal = 'balanced';
let fleetEnemyDefense = 'unknown';
let fleetEnemyWeapons = 'unknown';
let fleetCrisisPreset = 'none';

const fleetCrisisBlueprints = {
  prethoryn: {
    label: 'Prethoryn Scourge',
    enemyDefense: 'armor',
    enemyWeapons: 'explosive',
    sections: 'Tachyon Lance Battleships (X + L) + Plasma/Carrier Cruisers + Picket/Flak Destroyers',
    weapons: 'Energy weapons (Tachyon Lance, Plasma, Lasers) + Strike Craft — Prethoryn have zero shields and massive armor + hull; skip Kinetic.',
    defenses: '100% Armor (skip shields entirely) + Flak & Point-Defense screens to intercept biological missiles and strike craft.',
    auxComputer: 'Aux: Auxiliary Fire-Control / Regenerative Hull / Afterburners · Computer: Artillery or Carrier (Picket on PD escorts)',
    note: 'Crisis preset (Prethoryn Scourge): stack Defender of the Galaxy (+50%) & Galactic Threats Committee (+20%) if available. Confirm unlocked tiers & upkeep in Ship Designer.',
  },
  unbidden: {
    label: 'The Unbidden',
    enemyDefense: 'shield',
    enemyWeapons: 'energy',
    sections: 'Spinal Mount Artillery Battleships (X + L) + Titans (Perdition Beam + 6 L) built to kite slow Unbidden fleets',
    weapons: 'Pure Kinetic (Giga Cannon + Kinetic Artillery) to shred massive shields — avoid pure bypass (Arc Emitters) inside Dimensional Anchor systems where shield hardening spikes.',
    defenses: 'Maximum Shields (skip armor entirely) — Unbidden Matter Disintegrators melt armor and hull but deal reduced damage to shields.',
    auxComputer: 'Aux: Shield Capacitors + Afterburners (to stay at max range) · Computer: Artillery',
    note: 'Crisis preset (The Unbidden / Extradimensional Invaders): destroy Dimensional Anchors before hitting the Portal. Confirm unlocked tiers & power in Ship Designer.',
  },
  contingency: {
    label: 'The Contingency',
    enemyDefense: 'shield',
    enemyWeapons: 'energy',
    sections: 'Focused Arc Emitter Carrier Battleships (X + H + M) + Disruptor/Missile Cruisers',
    weapons: 'Bypass weapons (Focused Arc Emitters, Disruptors, Missiles, Strike Craft) — exploits the Contingency’s 1:4:4 Hull/Armor/Shield ratio and low hardening.',
    defenses: 'Balanced ~50% Shields / ~50% Armor — Contingency weapons deal heavy mixed damage across shields and armor.',
    auxComputer: 'Aux: Shield Capacitors or Afterburners · Computer: Carrier or Artillery (pair with Juggernaut range aura if available)',
    note: 'Crisis preset (The Contingency): clear Sterilization Hubs and check machine/synth pop events. Confirm unlocked tiers & upkeep in Ship Designer.',
  },
  cetana: {
    label: 'Cetana (Synthetic Queen)',
    enemyDefense: 'armor',
    enemyWeapons: 'unknown',
    sections: 'Massed Torpedo Frigates (1 G + 1 S) for the flagship DPS check + Artillery/Carrier Battleships to clear patrol fleets',
    weapons: 'Devastator Torpedoes (high raw damage vs huge flagship health pool) — penetration/bypass builds (Arc Emitters) underperform against Cetana’s flagship.',
    defenses: 'High-tier mixed Armor & Shields on escorts; keep Torpedo Frigates lean and fast so alloys scale fleet numbers.',
    auxComputer: 'Aux: Afterburners (closing speed on Frigates) · Computer: Torpedo on Frigates, Artillery/Carrier on escort fleets',
    note: 'Crisis preset (Cetana — The Machine Age DLC): manage her Situation timeline carefully. Confirm unlocked tiers, power, and alloy upkeep in Ship Designer.',
  },
};

const fleetOrder = [
  'corvette', 'frigate', 'destroyer', 'cruiser', 'battleship', 'titan', 'juggernaut', 'colossus',
  'mauler', 'weaver', 'harbinger', 'stinger', 'arkship', 'military_arkship',
];
const fleetTitle = value => String(value || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
const fleetNumber = value => Number(value || 0).toLocaleString(undefined, {maximumFractionDigits: 1});
const fleetClassName = size => fleetTitle(size || 'ship');

const fleetDlcAliases = {
  first_contact_story_pack: 'first_contact',
  ancient_relics_story_pack: 'ancient_relics',
  distant_stars_story_pack: 'distant_stars',
  leviathans_story_pack: 'leviathans',
  grand_archive_story_pack: 'grand_archive',
  the_machine_age: 'machine_age',
  stellaris_nomads: 'nomads',
  stellaris_willpower: 'willpower',
};

function fleetActiveDlcs(snapshot) {
  const summary = snapshot?.campaign?.dlc_summary;
  if (summary) {
    return summary.known && Array.isArray(summary.active_ids) ? new Set(summary.active_ids) : null;
  }
  const raw = snapshot?.campaign?.required_dlcs;
  if (!Array.isArray(raw)) return null;
  return new Set(raw.map(item => {
    const slug = String(item).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
    return fleetDlcAliases[slug] || slug;
  }));
}

function fleetManualLimit(config) {
  const value = config?.fleet_limit;
  return Number.isInteger(value) && value > 0 && value <= 100000 ? value : null;
}

function fleetWeakest(fleets) {
  return (fleets || []).filter(f => Number.isFinite(f.size) &&
    Number.isFinite(f.planned_size) && f.planned_size > 0 && f.size < f.planned_size)
    .sort((a, b) => a.size / a.planned_size - b.size / b.planned_size)[0] || null;
}

function fleetVerdict(snapshot, manualLimit) {
  const fleet = fleetWeakest(snapshot.ship_builds?.fleets);
  const used = snapshot.player?.naval_used;
  const over = Number.isFinite(manualLimit) && Number.isFinite(used) ? used - manualLimit : null;
  if (over > 0) return {
    title: 'Raise naval capacity before adding ships',
    detail: `${fleetNumber(used)} used is ${fleetNumber(over)} above the ${fleetNumber(manualLimit)} limit you entered from Stellaris. Building now may increase fleet upkeep.`,
    steps: ['Raise your naval limit in game, then check the new value here.',
      fleet ? `Return to ${fleet.name}: ${fleetNumber(fleet.size)} of ${fleetNumber(fleet.planned_size)} on its saved plan.` : 'Review your fleet plans after capacity improves.'],
    fleet,
  };
  if (fleet) return {
    title: `Rebuild ${fleet.name}`,
    detail: `${fleetNumber(fleet.size)} of ${fleetNumber(fleet.planned_size)} on its saved Fleet Manager plan · ${fleet.ship_count} ships · ${fleetNumber(fleet.power)} saved power.`,
    steps: [`Compare the saved ${Object.keys(fleet.classes || {}).map(fleetClassName).join(' and ')} designs below.`,
      manualLimit ? 'Check the planner against your entered naval limit.' : 'Enter the naval limit shown in game before ordering ships.'],
    fleet,
  };
  if (!snapshot.ship_builds?.fleets?.length) return {
    title: 'No owned military fleets found',
    detail: 'This save did not provide an owned military fleet to plan around.',
    steps: ['Check that the selected autosave is the campaign you are playing.',
      'Open Stellaris Fleet Manager to confirm whether a fleet exists.'],
    fleet: null,
  };
  return {
    title: 'Review your fleet mix',
    detail: 'No owned military fleet is visibly below its saved Fleet Manager plan.',
    steps: ['Compare your saved combat designs.', 'Check your naval limit in game before a large build.'],
    fleet: null,
  };
}

function fleetPlanTotals(designs, quantities, currentUsed, limit, target) {
  let added = 0;
  let count = 0;
  let known = true;
  for (const design of designs) {
    const quantity = Math.max(0, Math.min(99, Number(quantities[design.id]) || 0));
    if (!quantity) continue;
    count += quantity;
    if (!Number.isFinite(design.naval_usage)) known = false;
    else added += quantity * design.naval_usage;
  }
  return {
    count, added: known ? added : null,
    empireAfter: known && Number.isFinite(currentUsed) ? currentUsed + added : null,
    planAfter: known && Number.isFinite(target?.size) ? target.size + added : null,
    overLimit: known && Number.isFinite(limit) && Number.isFinite(currentUsed) && currentUsed + added > limit,
  };
}

function fleetArt(size, className = '') {
  const icons = {corvette:'tech_corvettes', frigate:'tech_torpedoes_1',
    destroyer:'tech_destroyers', cruiser:'tech_cruisers',
    battleship:'tech_battleships', titan:'tech_titans'};
  const isWeb = typeof window !== 'undefined' && Boolean(window.STELLARIS_WEB_MODE);
  const icon = isWeb ? null : icons[size];
  const fallback = (typeof window !== 'undefined' && window.StellarisArt?.shipSvg)
    ? window.StellarisArt.shipSvg(size)
    : '<span aria-hidden="true">◇</span>';
  return `<span class="fleet-art ${esc(className)}">${icon ? `<img src="/api/tech-icon?id=${encodeURIComponent(icon)}" alt="" onerror="this.hidden=true">` : ''}<span class="fleet-art-fallback" aria-hidden="true">${fallback}</span></span>`;
}

function fleetSlots(design) {
  const slots = design.slots || [];
  const core = design.required_components || [];
  if (!slots.length && !core.length) return '<p class="fleet-muted">No saved component slots could be read.</p>';
  const renderTag = (slotLabel, rawName, fallbackSize = '•') => {
    const raw = String(rawName || 'Unknown part');
    const slotUpper = String(slotLabel || '').toUpperCase();
    const kind = (/^AUX/.test(slotUpper) || /AFTERBURNER|AUX|CAPACITOR|REGEN|FIRE_CONTROL|COMPUTER/i.test(raw)) ? 'aux'
      : /TORPEDO|MISSILE|HANGAR|STRIKE_CRAFT/i.test(raw) ? 'explosive'
      : /POINT_DEFENSE|FLAK/i.test(raw) ? 'pd'
      : /LASER|PLASMA|DISRUPTOR|ARC_EMITTER|LANCE|NEUTRON/i.test(raw) ? 'energy'
      : /MASS_DRIVER|RAILGUN|AUTOCANNON|KINETIC|GAUSS/i.test(raw) ? 'kinetic'
      : /SHIELD/i.test(raw) ? 'shield'
      : /ARMOR|CRYSTAL|PLATING/i.test(raw) ? 'armor'
      : 'other';
    const size = String(slotLabel || '').split('_')[0];
    const label = fleetTitle(raw.replace(/^(SMALL|MEDIUM|LARGE|EXTRA_LARGE|TITANIC)_/, ''));
    return `<span class="fleet-slot ${kind}" title="${esc(slotLabel || 'Core')}: ${esc(raw)}"><b>${esc(size.slice(0, 1) || fallbackSize)}</b><span>${esc(label)}</span></span>`;
  };
  const slotHtml = slots.map(item => renderTag(item.slot || 'Slot', item.component)).join('');
  const coreHtml = core.length
    ? `<div class="fleet-core-slots"><small>Core systems:</small>${core.map(name => renderTag('CORE', name, 'C')).join('')}</div>`
    : '';
  return `<div class="fleet-slots">${slotHtml}</div>${coreHtml}`;
}

function fleetLoadoutCounts(design) {
  const counts = {weapons: 0, shields: 0, armor: 0, aux: 0};
  for (const item of (design?.slots || [])) {
    const raw = String(item.component || '').toUpperCase();
    const slot = String(item.slot || '').toUpperCase();
    if (/^AUX/.test(slot) || /AUX|AFTERBURNER|CAPACITOR|REGEN|FIRE_CONTROL/.test(raw)) counts.aux++;
    else if (/SHIELD/.test(raw)) counts.shields++;
    else if (/ARMOR|CRYSTAL|PLATING/.test(raw)) counts.armor++;
    else if (/GUN|TORPEDO|MISSILE|HANGAR|PD|POINT_DEFENSE|FLAK|WEAPON/.test(slot) ||
      /LASER|PLASMA|DISRUPTOR|MASS_DRIVER|RAILGUN|AUTOCANNON|KINETIC|TORPEDO|MISSILE|HANGAR|FLAK|POINT_DEFENSE|LANCE|EMITTER/.test(raw)) {
      counts.weapons++;
    }
  }
  return counts;
}

function fleetBuildBlueprint(size, goal, enemyDefense, enemyWeapons, context = {}) {
  const hull = size || 'corvette';
  const activeDlcs = context.activeDlcs;
  const researched = context.researched || {};
  const hasTech = prefix => Object.keys(researched).some(id => id.startsWith(prefix));
  const crisis = context.crisisPreset && fleetCrisisBlueprints[context.crisisPreset];
  if (crisis) {
    const dlcNote = context.crisisPreset === 'cetana' && activeDlcs && !activeDlcs.has('machine_age')
      ? ' Note: The Machine Age DLC is not listed in this save.' : '';
    const nomadNote = context.isNomad
      ? ' Nomad warning: crisis fleets destroy Arkships outright rather than disabling them.' : '';
    return {
      title: `${crisis.label} counter blueprint (viewing ${fleetClassName(hull)})`,
      sections: crisis.sections,
      weapons: crisis.weapons,
      defenses: crisis.defenses,
      auxComputer: crisis.auxComputer,
      note: `${crisis.note}${dlcNote}${nomadNote}`,
    };
  }
  const isBioHull = ['mauler', 'weaver', 'harbinger', 'stinger'].includes(hull);
  const canCloak = !activeDlcs || activeDlcs.has('first_contact');

  const sections = {
    corvette: goal === 'screening' ? 'Picket Ship (1 PD + 2 S) or Interceptor (3 S)'
      : 'Interceptor (3 S) or Missile Boat (1 G + 1 S)',
    frigate: 'Torpedo Hull (1 G Torpedo + 1 S) — ambush / anti-capital role',
    destroyer: enemyWeapons === 'explosive' || goal === 'screening'
      ? 'Picket Ship Bow + Picket Ship Stern (PD/Flak + S/M)'
      : 'Gunship or Artillery Bow + Picket/Gunship Stern',
    cruiser: goal === 'damage' ? 'Torpedo Brawler (G/S) or Broadside / Artillery (M/L)'
      : goal === 'screening' ? 'Hangar Core (Strike Craft + PD) + Gunship/Broadside'
      : 'Hangar Core (Carrier) or Broadside/Missile Core (versatile mid-late hull)',
    battleship: goal === 'screening' ? 'Spinal Mount Bow + Carrier Core + Broadside Stern'
      : 'Spinal Mount Bow (X) + Artillery or Carrier Core + Broadside/Artillery Stern',
    titan: 'Perdition Beam (T) + 6 Large Artillery slots + Fleet Aura (e.g., Shield Dampener or Inspiring Presence)',
    juggernaut: 'Mobile Shipyard + 2 Spinal X + 6 Strike Craft Hangars + 5 M slots + Empire Aura',
    colossus: 'Planet-killer weapon slot only (no standard combat weapons — always escort with combat fleets)',
    arkship: 'Nomads Arkship modules (verify Weapon & Defense Preferences in Policies)',
    military_arkship: 'Nomads Tier III Military Arkship (1 per fleet) — verify Arkship policies',
    mauler: 'BioGenesis Mauler (close-range biological hull — confirm organic weapon & food/alloy upkeep)',
    weaver: 'BioGenesis Weaver (support/aura biological hull — pair with combat hulls)',
    harbinger: 'BioGenesis Harbinger (carrier/mid-range biological hull)',
    stinger: 'BioGenesis Stinger (late-game long-range biological hull)',
  };

  let weapons;
  if (hull === 'colossus') {
    weapons = 'Planet-killer weapon only (World Cracker, Global Pacifier, Neutron Sweep, etc.) — no combat weapon slots.';
  } else if (hull === 'juggernaut') {
    weapons = enemyDefense === 'shield'
      ? '2 Focused Arc Emitters or Giga Cannons (X) + Strike Craft Hangars + Kinetic/Whirlwind Missiles (M)'
      : enemyDefense === 'armor'
      ? '2 Tachyon Lances or Focused Arc Emitters (X) + Strike Craft Hangars + Plasma/Missiles (M)'
      : '2 Focused Arc Emitters (X) + Strike Craft Hangars + Whirlwind Missiles (M)';
  } else if (hull === 'titan') {
    weapons = enemyDefense === 'shield'
      ? 'Perdition Beam (T) + 6 Kinetic Artillery (L) to strip shields at long range'
      : enemyDefense === 'armor'
      ? 'Perdition Beam (T) + 6 Large Plasma / Lasers (L) to burn armor at long range'
      : 'Perdition Beam (T) + Kinetic Artillery (L) mixed with Large Plasma/Lasers (L)';
  } else if (isBioHull) {
    weapons = enemyDefense === 'shield'
      ? 'Organic kinetic / shield-bypass weapons matching this biological hull stage — verify unlocked organic components in Ship Designer'
      : enemyDefense === 'armor'
      ? 'Organic energy / armor-piercing weapons matching this biological hull stage — verify unlocked organic components in Ship Designer'
      : 'Organic weapons tailored to this biological hull growth stage (check organic weapon slots and Food/Alloy upkeep in Ship Designer)';
  } else if (enemyDefense === 'shield') {
    weapons = hull === 'frigate'
      ? 'Torpedoes (G, bypass shields) + Autocannon / Disruptor (S)'
      : hull === 'battleship'
      ? 'Focused Arc Emitter (X, bypasses shields & armor) or Giga Cannon (X) + Kinetic Artillery (L) / Strike Craft'
      : hull === 'destroyer' && enemyWeapons === 'explosive'
      ? 'Flak/Point-Defense + Kinetic (Railguns/Autocannons) or S/M Missiles'
      : 'Kinetic (Autocannons / Gauss / Kinetic Artillery) or Shield-Bypass (Disruptors / Missiles)';
  } else if (enemyDefense === 'armor') {
    weapons = hull === 'frigate'
      ? 'Torpedoes / Neutron Launchers (G) + Plasma / Laser (S)'
      : hull === 'battleship'
      ? 'Tachyon Lance or Focused Arc Emitter (X) + Large Plasma / Lasers (L) or Strike Craft'
      : 'Energy (Lasers / Plasma) or Armor-piercing Disruptors / Missiles (or Neutron Launchers in G slots on Cruisers/Frigates)';
  } else if (goal === 'screening') {
    weapons = hull === 'cruiser' || hull === 'battleship'
      ? 'Strike Craft (Hangars) + Flak/Point-Defense + Whirlwind Missiles (M)'
      : 'Flak (vs Strike Craft) or Point-Defense (vs Missiles) + rapid-fire S weapons';
  } else if (hull === 'frigate') {
    weapons = 'Torpedoes (G slot, high damage vs Cruisers/Battleships/Starbases) + Disruptor or Autocannon (S)';
  } else if (hull === 'corvette') {
    weapons = goal === 'damage'
      ? 'All Disruptors (S, bypasses shields & armor) OR 2 Kinetic (Autocannons/Railguns) + 1 Energy (Laser/Plasma)'
      : 'Balanced 2 Kinetic + 1 Laser/Plasma (S), or S-slot Missiles + Disruptor once unlocked';
  } else if (hull === 'battleship') {
    weapons = 'Spinal X weapon (Focused Arc Emitter or Giga Cannon/Tachyon Lance) + Strike Craft Hangars + Whirlwind Missiles (M) or Kinetic Artillery (L)';
  } else if (hull === 'cruiser') {
    weapons = 'Whirlwind Missiles (M) + Strike Craft (kiting) OR Torpedoes (G) + Autocannons/Disruptors (brawler)';
  } else {
    weapons = 'Mix Kinetic (strips shields) + Energy (burns armor), or Missiles/Disruptors for bypass damage';
  }

  let defenses;
  if (enemyWeapons === 'kinetic') {
    defenses = 'Armor-heavy (~70–80% Armor, 20–30% Shields or Crystal Hull) — Kinetic deals bonus damage to Shields and reduced damage to Armor.';
  } else if (enemyWeapons === 'energy') {
    defenses = 'Shield-heavy (~70–80% Shields, 20–30% Armor) — Energy weapons deal bonus damage to Armor and reduced damage to Shields.';
  } else if (enemyWeapons === 'explosive') {
    defenses = 'Armor-leaning (~70% Armor, 30% Shields/Hull) + Point-Defense/Flak escorts — Missiles & Torpedoes bypass Shields completely.';
  } else if (goal === 'low-cost') {
    defenses = 'Armor-leaning or Crystal Hull Plating to save reactor power and keep alloy/rare-resource costs lower.';
  } else if (goal === 'survival') {
    defenses = 'Balanced ~50% Armor / ~50% Shields (highest unlocked tier) — add Hull Plating if enemy uses bypass weapons (Disruptors/Arc Emitters).';
  } else {
    defenses = 'Balanced ~50% Armor / ~50% Shields using your highest unlocked tier; shift toward Armor if reactor power runs tight.';
  }

  let auxComputer;
  if (hull === 'colossus') {
    auxComputer = 'Aux: Afterburners or Regenerative Hull Tissue (survival & transit speed) · Standard Colossus computer (keep escorted)';
  } else if (hull === 'juggernaut') {
    auxComputer = 'Aux: Regenerative Hull / Shield Capacitors · Computer: Carrier (stay back to repair and launch strike craft)';
  } else if (hull === 'corvette') {
    auxComputer = goal === 'mobility' || goal === 'balanced'
      ? 'Aux: Afterburners (evasion & speed) · Computer: Swarm (brawler) or Artillery (missile kiter)'
      : 'Aux: Afterburners · Computer: Swarm (close-in) or Picket (high tracking)';
  } else if (hull === 'frigate') {
    auxComputer = canCloak
      ? 'Aux: Afterburners (or Cloaking Field with First Contact) · Computer: Torpedo'
      : 'Aux: Afterburners · Computer: Torpedo';
  } else if (hull === 'destroyer') {
    auxComputer = 'Aux: Afterburners or Auxiliary Fire-Control · Computer: Picket (anti-corvette/missile tracking)';
  } else if (hull === 'cruiser') {
    auxComputer = 'Aux: Afterburners (speed/kiting) or Regenerative Hull / Shield Capacitors · Computer: Carrier, Torpedo, or Line';
  } else if (hull === 'titan') {
    auxComputer = 'Aux: Auxiliary Fire-Control or Shield Capacitors / Regenerative Hull · Computer: Artillery (keep Perdition Beam & Aura at max range)';
  } else if (hull === 'battleship') {
    auxComputer = 'Aux: Afterburners (kiting) or Auxiliary Fire-Control / Shield Capacitors · Computer: Artillery or Carrier';
  } else {
    auxComputer = 'Aux: Afterburners or Regenerative Hull / Shield Capacitors · Computer matching your weapon range';
  }

  const techNotes = [];
  if (Object.keys(researched).length) {
    const unlocked = [
      hasTech('tech_shields_') && 'Shields',
      hasTech('tech_ship_armor_') && 'Armor',
      hasTech('tech_lasers_') && 'Lasers',
      hasTech('tech_mass_drivers_') && 'Kinetic',
      hasTech('tech_missiles_') && 'Missiles',
      hasTech('tech_torpedoes_') && 'Torpedoes',
      hasTech('tech_disruptors_') && 'Disruptors',
      hasTech('tech_strike_craft_') && 'Strike Craft',
      hasTech('tech_afterburners_') && 'Afterburners',
    ].filter(Boolean);
    if (unlocked.length) techNotes.push(`Recorded tech families in save: ${unlocked.join(', ')}.`);
  }
  if (activeDlcs && activeDlcs.has('first_contact') && ['corvette', 'frigate'].includes(hull)) {
    techNotes.push('First Contact: Frigates/Corvettes pair well with Cloaking for torpedo ambushes.');
  }
  if (activeDlcs && activeDlcs.has('grand_archive') && context.shipsetKind === 'fauna') {
    techNotes.push('Space fauna: re-check combat computers after upgrades.');
  }
  techNotes.push('Verify unlocked component tiers, reactor power, and alloy/strategic-resource upkeep in Ship Designer.');

  return {
    title: `${fleetClassName(hull)} configuration (${fleetTitle(goal)}${enemyDefense !== 'unknown' || enemyWeapons !== 'unknown' ? ' · countered' : ''})`,
    sections: sections[hull] || 'Inspect available bow/core/stern sections in Ship Designer for your weapon range.',
    weapons,
    defenses,
    auxComputer,
    note: techNotes.join(' '),
  };
}

/* Qualitative, save-grounded finder. No saved design is assumed buildable. */
function fleetAssess(design, goal, enemyDefense, enemyWeapons, context = {}) {
  const parts = (design.slots || []).map(slot => String(slot.component || '').toUpperCase());
  const has = pattern => parts.some(part => pattern.test(part));
  const offensiveTypes = [
    has(/TORPEDO|MISSILE|SCOURGE/) && 'explosive',
    has(/LASER|PLASMA|DISRUPTOR|ARC_EMITTER/) && 'energy',
    has(/MASS_DRIVER|RAILGUN|AUTOCANNON|KINETIC/) && 'kinetic',
  ].filter(Boolean);
  const offense = offensiveTypes.length > 1 ? 'mixed' : offensiveTypes[0] || 'unknown';
  const defense = has(/SHIELD/) && has(/ARMOR/) ? 'mixed' :
    has(/SHIELD/) ? 'shield' : has(/ARMOR/) ? 'armor' : 'unknown';
  const missing = (design.component_evidence || []).flatMap(item => item.unresearched_tech || []);
  const reasons = [];
  if (missing.length) reasons.push(`Research not recorded: ${[...new Set(missing)].join(', ')}.`);
  if (context.mods?.length) reasons.push('Save lists mods; modified fitting rules have not been checked.');
  if (context.version && !/(?:^|\D)4\.5\./.test(String(context.version)))
    reasons.push('Save is outside the verified 4.5 rules family.');
  reasons.push('Confirm hull, sections, slots, power, DLC, cost and available parts in Ship Designer.');
  const status = missing.length ? 'blocked' : 'conditional';
  let fit = 'insufficient';
  let why = 'No enemy equipment is known; inspect the opponent before choosing a counter.';
  if (enemyDefense !== 'unknown') {
    const match = (enemyDefense === 'shield' && (offensiveTypes.includes('kinetic') || has(/DISRUPTOR|ARC_EMITTER/))) ||
      (enemyDefense === 'armor' && (offensiveTypes.includes('energy') || offensiveTypes.includes('explosive')));
    fit = match ? 'fitting' : offense === 'unknown' ? 'insufficient' : 'tradeoff';
    why = match ? `Its recorded ${offense} weapons may suit the ${enemyDefense} defense you reported; check the exact weapon tooltips.` :
      offense === 'unknown' ? 'Weapon details are missing from this saved design.' :
      `Its ${offense} weapons are not a verified counter to the ${enemyDefense} defense you reported.`;
  } else if (goal === 'damage' && offense !== 'unknown') {
    fit = 'fitting'; why = `Recorded ${offense} weapons offer an offensive starting point; actual damage is unverified.`;
  } else if (goal === 'survival' && defense !== 'unknown') {
    fit = 'fitting'; why = `Recorded ${defense} defenses offer a survival starting point; actual durability is unverified.`;
  } else if (goal === 'low-cost' || goal === 'mobility' || goal === 'screening') {
    fit = 'insufficient'; why = `${fleetTitle(goal)} cannot be compared from the recorded parts and cost alone.`;
  } else if (!parts.length) {
    fit = 'insufficient'; why = 'Component slots could not be read from this save.';
  }
  if (enemyWeapons !== 'unknown') {
    const helpful = (enemyWeapons === 'kinetic' && (defense === 'armor' || defense === 'mixed')) ||
      (enemyWeapons === 'energy' && (defense === 'shield' || defense === 'mixed')) ||
      (enemyWeapons === 'explosive' && has(/POINT_DEFENSE|FLAK/));
    if (enemyDefense === 'unknown' && !['low-cost', 'mobility', 'screening'].includes(goal))
      fit = helpful ? 'fitting' : defense === 'unknown' ? 'insufficient' : 'tradeoff';
    else if (fit === 'fitting' && !helpful) fit = 'tradeoff';
    why += helpful ? ` Its recorded protection may help against the ${enemyWeapons} weapons you reported; confirm exact modifiers.` :
      ` Enemy ${enemyWeapons} weapons were reported; check this design's defenses against their exact modifiers.`;
  }
  if (['low-cost', 'mobility', 'screening'].includes(goal)) {
    fit = 'insufficient';
    why += ' This goal requires cost, movement or screening evidence that the save does not verify.';
  }
  const selectedPolicies = (context.policies || []).filter(item =>
    ['fleet_doctrine', 'weapon_preference', 'defense_preference'].includes(item.key));
  const policyFit = selectedPolicies.length ? selectedPolicies.map(item =>
    `${item.policy_label}: ${item.selected_label}`).join(' · ') +
    `. This saved design records ${offense} weapons and ${defense} defenses. Check whether those parts match the selected settings in Ship Designer; policy effects and alternatives are not verified.` :
    'No selected fleet doctrine or ship preference could be read.';
  return {design, source: design.design_check?.auto_generated ? 'Auto-design' : 'Saved design',
    status, reasons, offense, defense, fit, why, policyFit};
}

function fleetFinder(designs, size, goal, enemyDefense, enemyWeapons, context = {}) {
  const candidates = designs.filter(design => design.size_key === size)
    .map(design => fleetAssess(design, goal, enemyDefense, enemyWeapons, context));
  const order = {fitting: 0, general: 1, tradeoff: 2, insufficient: 3};
  candidates.sort((a, b) => Number(a.status === 'blocked') - Number(b.status === 'blocked') ||
    order[a.fit] - order[b.fit] ||
    String(a.design.name).localeCompare(String(b.design.name)));
  const fitting = candidates.filter(item => item.fit === 'fitting' && item.status !== 'blocked');
  const top = fitting[0] || candidates.find(item => item.fit === 'tradeoff' && item.status !== 'blocked');
  return {candidates, top, tied: !!top && fitting.length > 1,
    decision: top ? 'Review existing design' : 'Need more information'};
}

function fleetConcept(size, goal, enemyWeapons, context = {}) {
  const activeDlcs = context.activeDlcs;
  const ideas = {
    corvette: 'Check a small, mobile ship for screening or early damage; inspect its actual speed and available slots.',
    frigate: 'Check a torpedo-capable strike ship when facing larger targets; inspect approach range and survival.',
    destroyer: enemyWeapons === 'explosive' ?
      'Check a point-defense escort against the missiles you reported; verify coverage and weapon slots.' :
      'Check an escort layout; point defense is useful only if the opponent fields interceptable threats.',
    cruiser: activeDlcs && !activeDlcs.has('apocalypse') ?
      'Without Apocalypse Titans, Cruiser/Battleship cores paired with Flak/PD screens anchor late-game fleets.' :
      'Check a versatile mid-to-late hull (hangar, artillery, or torpedo core) in Ship Designer.',
    arkship: 'Nomads Tier III Military Arkships are limited to one per fleet; check Arkship/Waystation policies in game.',
    military_arkship: 'Nomads Tier III Military Arkships are limited to one per fleet; check Arkship/Waystation policies in game.',
    mauler: 'BioGenesis biological hull: confirm both Food and Alloy costs and organic component slots in Ship Designer.',
    stinger: 'BioGenesis late-game biological hull: confirm Food and Alloy upkeep and range profile in Ship Designer.',
  };
  const objective = goal === 'low-cost' ? 'Compare the actual alloy cost and upkeep in Ship Designer.' :
    goal === 'mobility' ? 'Compare actual speed and range in Ship Designer.' :
    goal === 'survival' ? 'Compare armor, shields and effective durability in Ship Designer.' :
    goal === 'damage' ? 'Compare weapon range and damage against the expected target in Ship Designer.' :
    'Choose a specific goal or enter observed enemy equipment to narrow the choice.';
  const dlcHints = [];
  if (activeDlcs && activeDlcs.has('grand_archive') && context.shipsetKind === 'fauna') {
    dlcHints.push('Space fauna: verify combat computers did not reset after upgrades.');
  }
  if (activeDlcs && activeDlcs.has('first_contact')) {
    dlcHints.push('First Contact active: smaller hulls take lower cloaking penalties, but high enemy intel reveals cloaked fleets.');
  }
  return `${ideas[size] || 'Inspect the hull and available sections in Ship Designer.'} ${objective}${dlcHints.length ? ' ' + dlcHints.join(' ') : ''}`;
}

function renderFleet(snapshot, config = {}) {
  const root = $('fleet-dashboard');
  const data = snapshot.ship_builds || {};
  const designs = data.designs || [];
  const fleets = data.fleets || [];
  const campaign = snapshot.campaign?.id || 'unknown';
  if (fleetCampaign !== campaign) {
    fleetCampaign = campaign; fleetClass = null; fleetDesignId = null;
    fleetTargetId = null; fleetPlan = {}; fleetCompare = [];
    fleetGoal = 'balanced'; fleetEnemyDefense = 'unknown'; fleetEnemyWeapons = 'unknown'; fleetCrisisPreset = 'none';
  }
  const manualLimit = fleetManualLimit(config);
  const verdict = fleetVerdict(snapshot, manualLimit);
  if (!fleets.some(f => f.id === fleetTargetId)) fleetTargetId = verdict.fleet?.id || fleets[0]?.id || null;
  const target = fleets.find(f => f.id === fleetTargetId);
  const activeDlcs = fleetActiveDlcs(snapshot);
  const profile = snapshot.player?.profile || {};
  const defaultClasses = profile.shipset_kind === 'biological' ? ['mauler', 'weaver', 'harbinger'] : ['corvette', 'frigate', 'destroyer'];
  const allClasses = [...new Set([...defaultClasses, ...designs.map(d => d.size_key).filter(Boolean)])]
    .filter(size => size !== 'titan' || designs.some(d => d.size_key === 'titan') || !activeDlcs || activeDlcs.has('apocalypse'))
    .sort((a, b) => (fleetOrder.indexOf(a) < 0 ? 99 : fleetOrder.indexOf(a)) - (fleetOrder.indexOf(b) < 0 ? 99 : fleetOrder.indexOf(b)));
  const priorityClass = Object.entries(verdict.fleet?.classes || {}).sort((a, b) => b[1] - a[1])[0]?.[0];
  if (!allClasses.includes(fleetClass)) fleetClass = allClasses.includes(priorityClass) ? priorityClass : allClasses[0] || null;
  const classDesigns = designs.filter(d => d.size_key === fleetClass);
  if (!classDesigns.some(d => d.id === fleetDesignId)) fleetDesignId = classDesigns[0]?.id || null;
  const selected = designs.find(d => d.id === fleetDesignId);
  fleetCompare = fleetCompare.filter(id => designs.some(d => d.id === id)).slice(0, 3);
  if (!fleetCompare.length) fleetCompare = designs.slice(0, 2).map(d => d.id);
  const compared = fleetCompare.map(id => designs.find(d => d.id === id)).filter(Boolean);
  const used = snapshot.player?.naval_used;
  const military = snapshot.player?.military;
  const alloys = snapshot.player?.stock?.alloys;
  const alloyIncome = snapshot.player?.net?.alloys;
  const contacts = (snapshot.contacts || []).filter(c => Number.isFinite(c.military) && c.military > 0);
  const strongest = contacts.sort((a, b) => b.military - a.military)[0];
  const mix = data.class_usage || {};
  const mixTotal = Object.values(mix).reduce((sum, value) => sum + value, 0);
  const policyDetails = data.policy_details || [];
  const totals = fleetPlanTotals(designs, fleetPlan, used, manualLimit, target);
  const activeCrisis = fleetCrisisBlueprints[fleetCrisisPreset] || null;
  const effectiveDefense = activeCrisis ? activeCrisis.enemyDefense : fleetEnemyDefense;
  const effectiveWeapons = activeCrisis ? activeCrisis.enemyWeapons : fleetEnemyWeapons;
  const finder = fleetFinder(designs, fleetClass, fleetGoal, effectiveDefense, effectiveWeapons,
    {version: snapshot.version, mods: snapshot.campaign?.mods || [], policies: policyDetails});
  const finderTop = finder.top;
  const blueprint = fleetBuildBlueprint(fleetClass, fleetGoal, fleetEnemyDefense, fleetEnemyWeapons,
    {activeDlcs, shipsetKind: profile.shipset_kind, researched: snapshot.technology?.researched || {},
      crisisPreset: fleetCrisisPreset, isNomad: Boolean(profile.is_nomad)});
  const blueprintHtml = `
    <div class="fleet-blueprint" aria-label="Recommended ship configuration">
      <div class="fleet-blueprint-head"><span class="eyebrow">SUGGESTED SHIP DESIGNER CONFIGURATION · CONDITIONAL</span><strong>${esc(blueprint.title)}</strong></div>
      <dl class="fleet-blueprint-grid">
        <div><dt>Sections &amp; role</dt><dd>${esc(blueprint.sections)}</dd></div>
        <div><dt>Weapons</dt><dd>${esc(blueprint.weapons)}</dd></div>
        <div><dt>Armor &amp; shields</dt><dd>${esc(blueprint.defenses)}</dd></div>
        <div><dt>Aux &amp; computer</dt><dd>${esc(blueprint.auxComputer)}</dd></div>
      </dl>
      <small>${esc(blueprint.note)}</small>
    </div>`;
  const topCounts = finderTop ? fleetLoadoutCounts(finderTop.design) : null;
  const finderPolicy = policyDetails.slice(0, 3).map(item =>
    `${item.policy_label}: ${item.selected_label}`).join(' · ');

  root.innerHTML = `
    <div class="fleet-context"><span class="eyebrow">SELECTED AUTOSAVE · ${esc(snapshot.date || 'date unknown')}</span><span>${esc(snapshot.version || 'Version unknown')}${snapshot.campaign?.mods?.length ? ` · ${snapshot.campaign.mods.length} save-listed mods` : ''}</span></div>
    <section class="panel fleet-finder" aria-label="Fleet Design Finder">
      <div class="fleet-section-title"><div><span class="eyebrow">DESIGN FINDER</span><h2>What should I build?</h2></div><small>${designs.length ? '' : 'No saved combat designs · '}Save date ${esc(snapshot.date || 'unknown')} · ${esc(snapshot.version || 'version unknown')}</small></div>
      <div class="fleet-class-tabs" role="group" aria-label="Choose hull">${allClasses.map(size => `<button type="button" aria-pressed="${size === fleetClass}" class="${size === fleetClass ? 'active' : ''}" data-fleet-class="${esc(size)}">${fleetArt(size)}${esc(fleetClassName(size))} <small>${designs.filter(d => d.size_key === size).length} saved</small></button>`).join('')}</div>
      <div class="fleet-finder-controls"><fieldset><legend>Your goal</legend>${[['balanced','Balanced'],['damage','Damage'],['survival','Survival'],['screening','Screening'],['low-cost','Low cost'],['mobility','Mobility']].map(([value,label]) => `<button type="button" data-fleet-goal="${value}" aria-pressed="${fleetGoal === value}" class="${fleetGoal === value ? 'active' : ''}">${label}</button>`).join('')}</fieldset>
      <label>Enemy defenses you saw<select id="fleet-enemy-defense"><option value="unknown">Unknown</option><option value="shield" ${fleetEnemyDefense === 'shield' ? 'selected' : ''}>Mostly shields</option><option value="armor" ${fleetEnemyDefense === 'armor' ? 'selected' : ''}>Mostly armor</option></select></label>
      <label>Enemy weapons you saw<select id="fleet-enemy-weapons"><option value="unknown">Unknown</option><option value="kinetic" ${fleetEnemyWeapons === 'kinetic' ? 'selected' : ''}>Kinetic</option><option value="energy" ${fleetEnemyWeapons === 'energy' ? 'selected' : ''}>Energy</option><option value="explosive" ${fleetEnemyWeapons === 'explosive' ? 'selected' : ''}>Missiles or torpedoes</option></select></label>
      <label>Crisis counter preset<select id="fleet-crisis-preset"><option value="none" ${fleetCrisisPreset === 'none' ? 'selected' : ''}>None (custom)</option><option value="prethoryn" ${fleetCrisisPreset === 'prethoryn' ? 'selected' : ''}>Prethoryn Scourge</option><option value="unbidden" ${fleetCrisisPreset === 'unbidden' ? 'selected' : ''}>The Unbidden</option><option value="contingency" ${fleetCrisisPreset === 'contingency' ? 'selected' : ''}>The Contingency</option><option value="cetana" ${fleetCrisisPreset === 'cetana' ? 'selected' : ''}>Cetana (Synthetic Queen)</option></select></label></div>
      <div class="fleet-finder-result">${finderTop ? `${fleetArt(fleetClass)}<div class="fleet-finder-body"><span class="eyebrow">${esc(finder.decision)} · ${esc(finderTop.source)} · ${esc(finderTop.status)}</span><h3>${esc(finderTop.design.name)}</h3><p>${esc(finderTop.why)}</p><small class="fleet-loadout-summary">Saved loadout: ${topCounts.weapons} weapon · ${topCounts.shields} shield · ${topCounts.armor} armor · ${topCounts.aux} aux slot(s)</small>${fleetSlots(finderTop.design)}<small>${esc(finderTop.reasons.join(' '))}</small>${finder.tied ? '<small>Several designs are equally suitable from available evidence; names set display order only.</small>' : ''}</div>` : `${fleetArt(fleetClass)}<div class="fleet-finder-body"><span class="eyebrow">${esc(finder.decision)} · Guide concept only</span><h3>${esc(fleetClassName(fleetClass))} design guide</h3><p>No single saved design is verified as the best match yet. Use the suggested Ship Designer configuration below, or compare your saved ${esc(fleetClassName(fleetClass))} loadouts.</p></div>`}</div>
      ${blueprintHtml}
      <details class="fleet-finder-choices" open><summary>Compare ${finder.candidates.length} saved ${esc(fleetClassName(fleetClass))} designs</summary><div>${finder.candidates.slice(0, 5).map(item => { const c = fleetLoadoutCounts(item.design); return `<article>${fleetArt(item.design.size_key)}<div><strong>${esc(item.design.name)}</strong><small>${esc(item.source)} · ${esc(item.status)} · ${esc(item.fit === 'insufficient' ? 'insufficient data' : item.fit === 'fitting' ? 'suitable from known evidence' : 'trade-off or baseline')}</small><p>${esc(item.why)}</p><small>Attack ${esc(item.offense)} (${c.weapons}w) · Shields ${c.shields} · Armor ${c.armor} · Naval use ${Number.isFinite(item.design.naval_usage) ? fleetNumber(item.design.naval_usage) : 'unknown'}</small>${fleetSlots(item.design)}</div><button type="button" data-fleet-design="${item.design.id}">Inspect</button></article>`; }).join('') || '<p>No saved design for this hull. Check Ship Designer for available sections and parts.</p>'}</div></details>
      ${finderTop ? '' : `<p class="fleet-concept">Guide concept · conditional: ${esc(fleetConcept(fleetClass, fleetGoal, fleetEnemyWeapons, {activeDlcs, shipsetKind: profile.shipset_kind}))}</p>`}
      <small>${esc(finderTop?.policyFit || (finderPolicy ? `Selected settings: ${finderPolicy}. Check their effect in Ship Designer.` : 'Selected fleet settings could not be read.'))} Alternatives require a check in the in-game Policies screen. Opponent equipment above is player supplied; hidden designs are not used.</small>
      <button type="button" class="fleet-compare-toggle" data-open-compare aria-controls="fleet-compare-panel" aria-expanded="false">Open detailed comparison</button>
    </section>
    <div class="fleet-kpis">
      <article class="panel"><span>NAVAL CAPACITY</span><strong>${Number.isFinite(used) ? fleetNumber(used) : '—'}${manualLimit ? ` / ${fleetNumber(manualLimit)}` : ' used'}</strong><small>${manualLimit && Number.isFinite(used) ? (used > manualLimit ? `${fleetNumber(used - manualLimit)} above entered limit` : `${fleetNumber(manualLimit - used)} below entered limit`) : 'Used capacity or maximum unavailable'}</small></article>
      <article class="panel"><span>YOUR FLEET POWER</span><strong>${Number.isFinite(military) ? fleetNumber(military) : '—'}</strong><small>Empire value recorded in save</small></article>
      <article class="panel"><span>STRONGEST KNOWN RIVAL</span><strong>${strongest ? fleetNumber(strongest.military) : 'Unknown intel'}</strong><small>${strongest ? `${esc(strongest.name)} · save-only spoiler` : 'No verified rival power shown'}</small></article>
      <article class="panel"><span>ALLOYS</span><strong>${Number.isFinite(alloys) ? fleetNumber(alloys) : '—'}</strong><small>${Number.isFinite(alloyIncome) ? `${alloyIncome >= 0 ? '+' : ''}${fleetNumber(alloyIncome)} / month` : 'Monthly change unknown'}</small></article>
    </div>
    <article class="panel fleet-cap-entry"><label for="fleet-cap-limit">Naval limit shown in Stellaris <small>(optional; saved on this PC for this campaign)</small></label><div><input id="fleet-cap-limit" type="number" min="1" max="100000" step="1" inputmode="numeric" value="${manualLimit || ''}" placeholder="For example, 140"><button type="button" data-save-limit>Use limit</button><button type="button" data-clear-limit ${manualLimit ? '' : 'hidden'}>Clear</button></div><small>The save provides used capacity, but not a reliable maximum. Enter the top-bar limit to check over-capacity builds.</small></article>
    <article class="panel fleet-verdict"><div><span class="eyebrow">NEXT FLEET MOVE</span><h2>${esc(verdict.title)}</h2><p>${esc(verdict.detail)}</p></div><ol>${verdict.steps.map(step => `<li>${esc(step)}</li>`).join('')}</ol></article>
    <div class="fleet-section-title"><div><span class="eyebrow">YOUR FLEETS</span><h2>Saved military fleets</h2></div><small>${fleets.length} fleets · ${esc(data.usage_status === 'matches_saved_total' ? 'class sizes reconcile with saved naval use' : 'some size details unavailable')}</small></div>
    <div class="fleet-cards">${fleets.length ? fleets.map(fleet => {
      const fraction = Number.isFinite(fleet.size) && fleet.planned_size > 0 ? fleet.size / fleet.planned_size : null;
      const dominant = Object.entries(fleet.classes || {}).sort((a, b) => b[1] - a[1])[0]?.[0];
      return `<article class="panel fleet-card ${fleet.id === fleetTargetId ? 'selected' : ''}">${fleetArt(dominant)}<div><strong>${esc(fleet.name)}</strong><small>${esc(fleet.location || 'Location unknown')} · ${fleetNumber(fleet.power)} saved power</small><div class="fleet-bar"><i style="width:${fraction == null ? 0 : Math.min(100, fraction * 100)}%"></i></div><small>${Number.isFinite(fleet.size) ? fleetNumber(fleet.size) : 'Size unknown'}${Number.isFinite(fleet.planned_size) ? ` / ${fleetNumber(fleet.planned_size)} saved plan` : ' · plan unavailable'} · ${fleet.ship_count} ships${fleet.classes_complete === false ? ' · class mix partial' : ''}</small>${fraction != null && fraction < .7 ? '<span class="fleet-warning">Below 70% of saved plan</span>' : ''}</div><button type="button" data-target-fleet="${fleet.id}">${fleet.id === fleetTargetId ? 'Planning' : 'Plan build'}</button></article>`;
    }).join('') : '<div class="panel fleet-empty">No owned military fleet could be read from this save.</div>'}</div>
    <article class="panel fleet-mix"><div class="fleet-section-title"><div><span class="eyebrow">CURRENT MIX</span><h2>Your deployed ship classes</h2></div></div>${mixTotal ? `<div class="fleet-mix-bar">${Object.entries(mix).map(([size, amount]) => `<span class="${esc(size)}" style="width:${100 * amount / mixTotal}%" title="${esc(fleetClassName(size))}: ${fleetNumber(amount)} saved naval use"></span>`).join('')}</div><div class="fleet-mix-legend">${Object.entries(mix).map(([size, amount]) => `<span><i class="${esc(size)}"></i>${esc(fleetClassName(size))} ${fleetNumber(amount)}</span>`).join('')}</div>` : '<p>Mix unavailable from this save.</p>'}<small>Naval use by class is inferred from saved Fleet Manager plans${data.usage_status === 'matches_saved_total' ? ' and matches the empire total.' : '; the complete empire total did not reconcile.'}</small></article>
    <div class="fleet-section-title"><div><span class="eyebrow">DESIGN FINDER</span><h2>Your saved combat designs</h2></div><small>Compare recorded parts; build costs and combat stats are unavailable</small></div>
    <div class="fleet-class-tabs" role="tablist" aria-label="Ship classes">${allClasses.map(size => `<button type="button" role="tab" aria-selected="${size === fleetClass}" class="${size === fleetClass ? 'active' : ''}" data-fleet-class="${esc(size)}">${esc(fleetClassName(size))} <small>${designs.filter(d => d.size_key === size).length}</small></button>`).join('') || '<span>No saved combat designs</span>'}</div>
    <div class="fleet-design-layout"><div class="panel fleet-design-list">${classDesigns.map(design => `<button type="button" class="fleet-design-choice ${design.id === fleetDesignId ? 'active' : ''}" data-fleet-design="${design.id}">${fleetArt(design.size_key)}<span><strong>${esc(design.name)}</strong><small>${esc(design.role)} · ${design.slots?.length || 0} recorded parts${Number.isFinite(design.naval_usage) ? ` · ${fleetNumber(design.naval_usage)} naval use` : ''}</small></span><b>›</b></button>`).join('') || '<p class="fleet-muted">No saved design in this class.</p>'}</div>
      <article class="panel fleet-design-detail">${selected ? `<div class="fleet-design-head">${fleetArt(selected.size_key)}<div><span class="eyebrow">SAVED DESIGN · ${esc(fleetClassName(selected.size_key))}</span><h3>${esc(selected.name)}</h3><small>Saved role: ${esc(selected.role)}${selected.design_check?.auto_generated ? ' · Game auto-design' : ''}</small></div></div><p>These are its recorded slots and parts.</p>${fleetSlots(selected)}<div class="fleet-design-actions"><button type="button" data-compare="${selected.id}">${fleetCompare.includes(selected.id) ? 'Remove comparison' : 'Compare design'}</button><button type="button" data-add-design="${selected.id}">Add to plan +</button></div>` : '<p>Select a design to inspect its saved parts.</p>'}</article></div>
    <article class="panel fleet-compare"><div class="fleet-section-title"><div><span class="eyebrow">COMPARE</span><h2>Recorded design differences</h2></div><small>Up to 3 designs</small></div><div class="fleet-compare-cards">${compared.map(design => `<div class="fleet-compare-card">${fleetArt(design.size_key)}<strong>${esc(design.name)}</strong><small>${esc(fleetClassName(design.size_key))} · ${design.slots?.length || 0} parts · ${Number.isFinite(design.naval_usage) ? fleetNumber(design.naval_usage) + ' naval use' : 'naval use unknown'}</small>${fleetSlots(design)}<button type="button" data-add-design="${design.id}">Add to plan +</button></div>`).join('') || '<p>Choose designs to compare.</p>'}</div><small>Saved components alone do not establish which design is strongest. Check the in-game Ship Designer for alloy cost, power, upkeep, and actual buildability.</small></article>
    <article class="panel fleet-planner"><div class="fleet-section-title"><div><span class="eyebrow">BUILD PLANNER</span><h2>Plan your next ships</h2></div></div><label for="fleet-target">Add to fleet</label><select id="fleet-target">${fleets.map(f => `<option value="${f.id}" ${f.id === fleetTargetId ? 'selected' : ''}>${esc(f.name)}</option>`).join('')}</select><div class="fleet-plan-lines">${designs.filter(d => fleetPlan[d.id] > 0).map(d => `<div class="fleet-plan-line"><span>${esc(d.name)} <small>${esc(fleetClassName(d.size_key))}</small></span><div><button type="button" data-plan-step="-1" data-plan-design="${d.id}" aria-label="Remove one ${esc(d.name)}">−</button><strong>${fleetPlan[d.id]}</strong><button type="button" data-plan-step="1" data-plan-design="${d.id}" aria-label="Add one ${esc(d.name)}">+</button></div></div>`).join('') || '<p class="fleet-muted">Use “Add to plan” on a saved design above.</p>'}</div><div class="fleet-plan-result"><strong>${totals.count} ships planned</strong><span>${totals.count === 0 ? 'Add a saved design to estimate naval use.' : totals.added == null ? 'Naval use unknown' : `+${fleetNumber(totals.added)} naval use${Number.isFinite(used) && Number.isFinite(totals.empireAfter) ? ` · empire ${fleetNumber(used)} → ${fleetNumber(totals.empireAfter)}` : ' · empire total unknown'}`}</span>${target && totals.planAfter != null && target.planned_size != null ? `<span>${esc(target.name)}: ${fleetNumber(target.size)} → ${fleetNumber(totals.planAfter)}; saved plan ${fleetNumber(target.planned_size)}</span>` : ''}${totals.overLimit ? '<b>Over your entered naval limit. Raise capacity before ordering.</b>' : ''}</div><small>Alloy cost, build time, upkeep and power added cannot be verified from these saved designs; confirm the order in Stellaris.</small></article>
    <article class="panel fleet-policies"><div class="fleet-section-title"><div><span class="eyebrow">FLEET SETTINGS</span><h2>Saved military policies</h2></div></div>${policyDetails.length ? `<div>${policyDetails.slice(0, 3).map(item => `<p><strong>${esc(item.policy_label)}</strong><span>${esc(item.selected_label)}</span></p>`).join('')}</div><details><summary>Show all ${policyDetails.length} policies</summary><div>${policyDetails.map(item => `<p><strong>${esc(item.policy_label)}</strong><span>${esc(item.selected_label)}${item.status === 'verified_base_game' ? '' : ' · label unverified'}</span></p>`).join('')}</div></details>` : '<p>No military policies could be read.</p>'}</article>
    <p class="fleet-source-note">Fleet, design and resource values come from the selected save. Class naval use is inferred from saved plans. The manual capacity maximum comes from your entry, not the save. Game effects, mods and ship stats require in-game confirmation.</p>`;

  const comparePanel = root.querySelector('.fleet-compare');
  const compareToggle = root.querySelector('[data-open-compare]');
  if (comparePanel && compareToggle) {
    comparePanel.id = 'fleet-compare-panel';
    comparePanel.hidden = true;
    root.querySelector('.fleet-finder')?.insertAdjacentElement('afterend', comparePanel);
    const closeCompare = () => {
      comparePanel.hidden = true; compareToggle.setAttribute('aria-expanded', 'false');
      compareToggle.focus();
    };
    comparePanel.insertAdjacentHTML('afterbegin', '<button type="button" class="fleet-compare-close" aria-label="Close comparison">Close ×</button>');
    comparePanel.querySelector('.fleet-compare-close')?.addEventListener('click', closeCompare);
    compareToggle.addEventListener('click', () => {
      comparePanel.hidden = !comparePanel.hidden;
      compareToggle.setAttribute('aria-expanded', String(!comparePanel.hidden));
      if (!comparePanel.hidden) comparePanel.querySelector('.fleet-compare-close')?.focus();
    });
    comparePanel.addEventListener('keydown', event => { if (event.key === 'Escape') closeCompare(); });
  }
  const saveLimit = async value => {
    const limit = Number(value);
    if (!Number.isInteger(limit) || limit < 1 || limit > 100000) {
      showNotice('Enter a naval limit from 1 to 100,000.'); return;
    }
    try {
      const result = await post('/api/fleet-limit', {campaign_id: snapshot.campaign?.id, limit});
      config.fleet_limit = result.fleet_limit;
      renderFleet(snapshot, config);
    } catch (error) { showNotice(error.message); }
  };
  root.querySelector('#fleet-cap-limit')?.addEventListener('change', event => saveLimit(event.target.value));
  root.querySelector('[data-save-limit]')?.addEventListener('click', () => saveLimit(root.querySelector('#fleet-cap-limit')?.value));
  root.querySelector('[data-clear-limit]')?.addEventListener('click', async () => {
    try {
      const result = await post('/api/fleet-limit', {campaign_id: snapshot.campaign?.id, limit: null});
      config.fleet_limit = result.fleet_limit;
      renderFleet(snapshot, config);
    } catch (error) { showNotice(error.message); }
  });
  root.querySelectorAll('[data-target-fleet]').forEach(button => button.addEventListener('click', () => {
    fleetTargetId = Number(button.dataset.targetFleet); renderFleet(snapshot, config);
  }));
  root.querySelector('#fleet-target')?.addEventListener('change', event => {
    fleetTargetId = Number(event.target.value); renderFleet(snapshot, config);
  });
  root.querySelectorAll('[data-fleet-class]').forEach(button => button.addEventListener('click', () => {
    fleetClass = button.dataset.fleetClass; fleetDesignId = null; renderFleet(snapshot, config);
    root.querySelector(`[data-fleet-class="${fleetClass}"]`)?.focus();
  }));
  root.querySelectorAll('[data-fleet-goal]').forEach(button => button.addEventListener('click', () => {
    fleetGoal = button.dataset.fleetGoal; renderFleet(snapshot, config);
    root.querySelector(`[data-fleet-goal="${fleetGoal}"]`)?.focus();
  }));
  root.querySelector('#fleet-enemy-defense')?.addEventListener('change', event => {
    fleetEnemyDefense = event.target.value; fleetCrisisPreset = 'none'; renderFleet(snapshot, config);
    root.querySelector('#fleet-enemy-defense')?.focus();
  });
  root.querySelector('#fleet-enemy-weapons')?.addEventListener('change', event => {
    fleetEnemyWeapons = event.target.value; fleetCrisisPreset = 'none'; renderFleet(snapshot, config);
    root.querySelector('#fleet-enemy-weapons')?.focus();
  });
  root.querySelector('#fleet-crisis-preset')?.addEventListener('change', event => {
    fleetCrisisPreset = event.target.value; renderFleet(snapshot, config);
    root.querySelector('#fleet-crisis-preset')?.focus();
  });
  root.querySelectorAll('[data-fleet-design]').forEach(button => button.addEventListener('click', () => {
    const fromFinder = Boolean(button.closest?.('.fleet-finder-choices'));
    fleetDesignId = Number(button.dataset.fleetDesign); renderFleet(snapshot, config);
    const detail = root.querySelector('.fleet-design-detail');
    if (fromFinder && detail?.scrollIntoView) {
      detail.scrollIntoView({behavior: 'smooth', block: 'nearest'});
      root.querySelector(`.fleet-design-list [data-fleet-design="${fleetDesignId}"]`)?.focus?.({preventScroll: true});
    } else {
      root.querySelector(`[data-fleet-design="${fleetDesignId}"]`)?.focus?.();
    }
  }));
  root.querySelectorAll('[data-compare]').forEach(button => button.addEventListener('click', () => {
    const id = Number(button.dataset.compare);
    fleetCompare = fleetCompare.includes(id) ? fleetCompare.filter(value => value !== id) : [...fleetCompare.slice(-2), id];
    renderFleet(snapshot, config);
  }));
  root.querySelectorAll('[data-add-design]').forEach(button => button.addEventListener('click', () => {
    const id = Number(button.dataset.addDesign);
    fleetPlan[id] = Math.min(99, (fleetPlan[id] || 0) + 1); renderFleet(snapshot, config);
  }));
  root.querySelectorAll('[data-plan-step]').forEach(button => button.addEventListener('click', () => {
    const id = Number(button.dataset.planDesign);
    fleetPlan[id] = Math.max(0, Math.min(99, (fleetPlan[id] || 0) + Number(button.dataset.planStep)));
    renderFleet(snapshot, config);
  }));
}
