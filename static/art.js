/* Original inline SVG artwork for Stellaris Guide (zero copyrighted game assets).
   Provides rich framed sci-fi emblems for Web mode and acts as crisp fallback
   whenever local Steam .dds game art is not loaded. */
(() => {
  let svgUid = 0;
  const FLAG_COLORS = {
    blue: '#2a6bb8', dark_blue: '#163460', light_blue: '#5aaeff',
    teal: '#2caea8', dark_teal: '#145a5d', turquoise: '#45d3c8',
    green: '#3da867', dark_green: '#1c5a37', light_green: '#70e19a',
    red: '#c94949', dark_red: '#6e1d24', burgundy: '#7a2238',
    orange: '#db8039', dark_orange: '#8c4416', yellow: '#e2c04c', gold: '#d8ad45',
    purple: '#8858c8', dark_purple: '#43256d', indigo: '#4b48a8', pink: '#d46b9e',
    grey: '#6a7d8f', dark_grey: '#324150', black: '#0c1622', white: '#e5eff7', brown: '#7c5337',
  };

  function shipSvg(sizeKey) {
    const id = ++svgUid;
    const bgId = `sg-sbg-${id}`;
    const hullId = `sg-hull-${id}`;
    const bioId = `sg-bio-${id}`;
    const glowId = `sg-sglow-${id}`;
    const key = String(sizeKey || '').toLowerCase();
    const shapes = {
      corvette: `<path d="M32 7 L44 39 L32 33 L20 39 Z" fill="url(#${hullId})" stroke="#7ce8e2" stroke-width="1.6"/><path d="M32 14 L37 31 L32 27 L27 31 Z" fill="#c9fbf8" opacity="0.88"/><circle cx="32" cy="21" r="2" fill="#ffffff"/><path d="M25 39 L25 50 M39 39 L39 50" stroke="url(#${glowId})" stroke-width="2.6" stroke-linecap="round"/>`,
      frigate: `<path d="M32 6 L42 21 L46 42 L32 36 L18 42 L22 21 Z" fill="url(#${hullId})" stroke="#f0b668" stroke-width="1.6"/><path d="M28 14 H36 L38 30 H26 Z" fill="#ffd79a" opacity="0.72"/><circle cx="32" cy="18" r="3" fill="#ffad54"/><path d="M26 41 L26 53 M38 41 L38 53" stroke="url(#${glowId})" stroke-width="2.8" stroke-linecap="round"/>`,
      destroyer: `<path d="M32 5 L41 19 L50 36 L45 44 L32 38 L19 44 L14 36 L23 19 Z" fill="url(#${hullId})" stroke="#a69bff" stroke-width="1.6"/><rect x="28" y="16" width="8" height="17" rx="2" fill="#d8d4ff" opacity="0.82"/><circle cx="22" cy="34" r="2" fill="#7ce8e2"/><circle cx="42" cy="34" r="2" fill="#7ce8e2"/><path d="M24 43 L24 54 M32 40 L32 55 M40 43 L40 54" stroke="url(#${glowId})" stroke-width="2.4" stroke-linecap="round"/>`,
      cruiser: `<path d="M32 4 L42 15 L45 26 L53 35 L48 46 L32 41 L16 46 L11 35 L19 26 L22 15 Z" fill="url(#${hullId})" stroke="#55d8aa" stroke-width="1.6"/><path d="M27 16 H37 V37 H27 Z" fill="#9bf2d1" opacity="0.82"/><path d="M20 31 H44" stroke="#bdf7e4" stroke-width="1.4" opacity="0.7"/><path d="M21 46 L21 56 M32 43 L32 57 M43 46 L43 56" stroke="url(#${glowId})" stroke-width="2.6" stroke-linecap="round"/>`,
      battleship: `<path d="M32 3 L41 12 L46 20 L55 31 L51 48 L39 44 L32 49 L25 44 L13 48 L9 31 L18 20 L23 12 Z" fill="url(#${hullId})" stroke="#e2829e" stroke-width="1.6"/><path d="M27 11 H37 V40 H27 Z" fill="#f7b9cb" opacity="0.78"/><circle cx="19" cy="34" r="2.6" fill="#7ce8e2"/><circle cx="45" cy="34" r="2.6" fill="#7ce8e2"/><path d="M32 6 V16" stroke="#fff2b2" stroke-width="2.2"/><path d="M20 48 L20 58 M32 50 L32 59 M44 48 L44 58" stroke="url(#${glowId})" stroke-width="2.8" stroke-linecap="round"/>`,
      titan: `<path d="M32 2 L39 10 L44 16 L47 27 L57 37 L52 51 L39 47 L32 53 L25 47 L12 51 L7 37 L17 27 L20 16 L25 10 Z" fill="url(#${hullId})" stroke="#e6cf75" stroke-width="1.7"/><path d="M32 5 V45" stroke="#ffe794" stroke-width="2.8"/><circle cx="32" cy="24" r="5.5" fill="#ffe794" opacity="0.88"/><circle cx="32" cy="24" r="2.2" fill="#ffffff"/><path d="M18 51 L18 60 M32 54 L32 61 M46 51 L46 60" stroke="url(#${glowId})" stroke-width="2.8" stroke-linecap="round"/>`,
      arkship: `<ellipse cx="32" cy="30" rx="23" ry="15" fill="url(#${hullId})" stroke="#58ded7" stroke-width="1.8"/><ellipse cx="32" cy="30" rx="13" ry="7.5" fill="#18475a" stroke="#9cf5f0" stroke-width="1.3"/><circle cx="32" cy="30" r="4" fill="#58ded7"/><circle cx="32" cy="30" r="1.6" fill="#ffffff"/><path d="M17 44 L21 56 M32 46 L32 58 M47 44 L43 56" stroke="url(#${glowId})" stroke-width="2.6" stroke-linecap="round"/>`,
      mauler: `<path d="M32 7 C43 13 49 26 45 43 C38 38 35 46 32 52 C29 46 26 38 19 43 C15 26 21 13 32 7 Z" fill="url(#${bioId})" stroke="#70e19a" stroke-width="1.7"/><circle cx="32" cy="24" r="4.5" fill="#c7ffd8"/><path d="M23 29 Q32 36 41 29 M25 35 Q32 40 39 35" fill="none" stroke="#c7ffd8" stroke-width="1.4"/>`,
    };
    const aliases = {
      military_arkship: 'arkship', juggernaut: 'titan', colossus: 'titan',
      weaver: 'mauler', harbinger: 'mauler', stinger: 'mauler',
    };
    const resolvedKey = Object.hasOwn(shapes, key) ? key : (Object.hasOwn(aliases, key) ? aliases[key] : 'corvette');
    const body = shapes[resolvedKey];
    return `<svg class="sg-svg-art" viewBox="0 0 64 64" aria-hidden="true"><defs>`
      + `<radialGradient id="${bgId}" cx="50%" cy="40%" r="65%"><stop offset="0%" stop-color="#193b54"/><stop offset="100%" stop-color="#07131f"/></radialGradient>`
      + `<linearGradient id="${hullId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#4e8aa6"/><stop offset="55%" stop-color="#224a63"/><stop offset="100%" stop-color="#0f2336"/></linearGradient>`
      + `<linearGradient id="${bioId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3fa176"/><stop offset="100%" stop-color="#113328"/></linearGradient>`
      + `<linearGradient id="${glowId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ffe09e"/><stop offset="100%" stop-color="#ff7a3d" stop-opacity="0.1"/></linearGradient>`
      + `</defs><rect width="64" height="64" rx="8" fill="url(#${bgId})"/>`
      + `<circle cx="12" cy="14" r="0.9" fill="#d9f4ff" opacity="0.6"/><circle cx="52" cy="18" r="1.1" fill="#d9f4ff" opacity="0.5"/><circle cx="50" cy="52" r="0.8" fill="#89dce0" opacity="0.5"/>`
      + `${body}</svg>`;
  }

  function planetSvg(classKey) {
    const id = ++svgUid;
    const gradId = `sg-planet-${id}`;
    const haloId = `sg-halo-${id}`;
    const key = String(classKey || '').toLowerCase();
    let c1 = '#5bb9ec', c2 = '#1f6e59', c3 = '#0a2338', ring = false, city = false;
    if (/gaia/.test(key)) { c1 = '#7cf2b4'; c2 = '#2ba4db'; c3 = '#114548'; }
    else if (/ocean|aquatic/.test(key)) { c1 = '#6ed0ff'; c2 = '#1c75c4'; c3 = '#0a244f'; }
    else if (/desert|arid|savannah/.test(key)) { c1 = '#f0bc73'; c2 = '#b3642d'; c3 = '#47220f'; }
    else if (/arctic|alpine|tundra/.test(key)) { c1 = '#e3f4ff'; c2 = '#74acd4'; c3 = '#1b3954'; }
    else if (/machine|city|ecumenopolis|relic/.test(key)) { c1 = '#9cc2d6'; c2 = '#395264'; c3 = '#101b26'; ring = true; city = true; }
    else if (/hive|infested/.test(key)) { c1 = '#a6dc64'; c2 = '#4e6f2c'; c3 = '#1a2810'; }
    else if (/nuked|tomb/.test(key)) { c1 = '#b5aa9d'; c2 = '#5e5248'; c3 = '#201b18'; }
    else if (/habitat|ringworld/.test(key)) { c1 = '#75f2ea'; c2 = '#247280'; c3 = '#0a2030'; ring = true; }
    return `<svg class="sg-svg-art sg-planet-svg" viewBox="0 0 64 64" aria-hidden="true"><defs>`
      + `<radialGradient id="${haloId}" cx="50%" cy="50%" r="50%"><stop offset="68%" stop-color="${c1}" stop-opacity="0.32"/><stop offset="100%" stop-color="${c1}" stop-opacity="0"/></radialGradient>`
      + `<radialGradient id="${gradId}" cx="32%" cy="28%" r="70%"><stop offset="0%" stop-color="${c1}"/><stop offset="56%" stop-color="${c2}"/><stop offset="100%" stop-color="${c3}"/></radialGradient>`
      + `</defs><rect width="64" height="64" rx="10" fill="#07131f"/>`
      + `<circle cx="11" cy="12" r="0.9" fill="#ffffff" opacity="0.65"/><circle cx="54" cy="16" r="1" fill="#bdeeff" opacity="0.55"/><circle cx="52" cy="52" r="0.8" fill="#ffffff" opacity="0.45"/>`
      + `<circle cx="32" cy="32" r="27" fill="url(#${haloId})"/>`
      + `${ring ? '<ellipse cx="32" cy="33" rx="28" ry="8.5" fill="none" stroke="#8de8ec" stroke-width="2.2" opacity="0.62" transform="rotate(-18 32 33)"/>' : ''}`
      + `<circle cx="32" cy="32" r="20" fill="url(#${gradId})" stroke="${c1}" stroke-opacity="0.55" stroke-width="1.2"/>`
      + `<path d="M16 26 Q26 21 36 26 T49 25" fill="none" stroke="#ffffff" stroke-opacity="0.28" stroke-width="3" stroke-linecap="round"/>`
      + `<path d="M19 38 Q30 34 45 39" fill="none" stroke="#000000" stroke-opacity="0.26" stroke-width="3" stroke-linecap="round"/>`
      + `${city ? '<circle cx="26" cy="30" r="1.3" fill="#ffdf8a"/><circle cx="35" cy="33" r="1.2" fill="#70e1d6"/><circle cx="31" cy="24" r="1.1" fill="#ffdf8a"/><circle cx="39" cy="29" r="1.2" fill="#ffdf8a"/>' : ''}`
      + `</svg>`;
  }

  function techSvg(area, techId = '') {
    const uid = ++svgUid;
    const bgId = `sg-tbg-${uid}`;
    const glowId = `sg-tglow-${uid}`;
    const branch = String(area || '').toLowerCase();
    const id = String(techId || '').toLowerCase();

    const palette = branch === 'physics'
      ? {c: '#64b8ff', hi: '#c7e7ff', bg1: '#153b66', bg2: '#08182b', rim: '#3f84c9'}
      : branch === 'society'
      ? {c: '#4be098', hi: '#c9ffe4', bg1: '#114434', bg2: '#071c16', rim: '#2fa872'}
      : {c: '#ffb45c', hi: '#ffe4bf', bg1: '#4d2f11', bg2: '#1b1107', rim: '#c78030'};

    const {c, hi, bg1, bg2, rim} = palette;
    let glyph;

    if (/arkship|waystation|wayline|nomad/.test(id)) {
      glyph = `<ellipse cx="32" cy="32" rx="19" ry="11" fill="${c}" fill-opacity="0.2" stroke="${c}" stroke-width="2.1"/><ellipse cx="32" cy="32" rx="9" ry="5" fill="${hi}" fill-opacity="0.28" stroke="${hi}" stroke-width="1.3"/><circle cx="32" cy="32" r="2.6" fill="${hi}"/><path d="M16 45 L22 39 M48 45 L42 39" stroke="${c}" stroke-width="2" stroke-linecap="round"/>`;
    } else if (/galactic_hall|ideolog|willpower|tenet|fanatic|authority|monument|heritage/.test(id)) {
      glyph = `<path d="M16 48 H48 M20 44 V27 M28 44 V27 M36 44 V27 M44 44 V27 M15 26 L32 14 L49 26 Z" fill="${c}" fill-opacity="0.18" stroke="${c}" stroke-width="2" stroke-linejoin="round"/><circle cx="32" cy="21" r="2.5" fill="${hi}"/>`;
    } else if (/mega_engineering|dyson|ring_world|ringworld|matter_decompressor|arc_furnace|habitat|orbital_ring|megastructure|gateway/.test(id)) {
      glyph = `<circle cx="32" cy="32" r="17" fill="none" stroke="${c}" stroke-width="2.4" stroke-dasharray="9 4"/><circle cx="32" cy="32" r="9" fill="${c}" fill-opacity="0.25" stroke="${hi}" stroke-width="1.6"/><circle cx="32" cy="32" r="3.2" fill="${hi}"/>`;
    } else if (/starbase|starhold|starfortress|citadel|defense_platform|orbital/.test(id)) {
      glyph = `<polygon points="32,11 49,21 49,43 32,53 15,43 15,21" fill="${c}" fill-opacity="0.18" stroke="${c}" stroke-width="2.1"/><polygon points="32,20 41,26 41,38 32,44 23,38 23,26" fill="${hi}" fill-opacity="0.2" stroke="${hi}" stroke-width="1.4"/><circle cx="32" cy="32" r="3" fill="${hi}"/>`;
    } else if (/battleship|titan|juggernaut|colossus|cruiser|stinger|harbinger/.test(id)) {
      glyph = `<path d="M32 10 L44 24 L50 42 L32 37 L14 42 L20 24 Z" fill="${c}" fill-opacity="0.24" stroke="${c}" stroke-width="2.1"/><path d="M32 14 V38 M24 31 H40" stroke="${hi}" stroke-width="1.8" stroke-linecap="round"/><path d="M24 44 V52 M32 42 V54 M40 44 V52" stroke="${c}" stroke-width="2.2" stroke-linecap="round"/>`;
    } else if (/corvette|destroyer|frigate|mauler|weaver|ship_hull/.test(id)) {
      glyph = `<path d="M32 11 L45 43 L32 36 L19 43 Z" fill="${c}" fill-opacity="0.26" stroke="${c}" stroke-width="2.1"/><path d="M32 18 L36 33 L32 30 L28 33 Z" fill="${hi}" opacity="0.85"/><path d="M25 44 V52 M39 44 V52" stroke="${c}" stroke-width="2.2" stroke-linecap="round"/>`;
    } else if (/strike_craft|hangar|carrier|amoeba|fighter/.test(id)) {
      glyph = `<path d="M32 13 L41 28 L32 25 L23 28 Z M19 32 L26 45 L19 42 L12 45 Z M45 32 L52 45 L45 42 L38 45 Z" fill="${c}" fill-opacity="0.26" stroke="${c}" stroke-width="1.8" stroke-linejoin="round"/>`;
    } else if (/torpedo|missile|swarmer|explosive|devastator/.test(id)) {
      glyph = `<path d="M46 18 L24 40 L18 46 L24 46 L46 24 C49 21 49 15 46 18 Z" fill="${c}" fill-opacity="0.3" stroke="${c}" stroke-width="2"/><path d="M38 18 L46 26 M20 34 L14 34 L20 40 M30 44 L30 50 L24 44" stroke="${hi}" stroke-width="1.8" stroke-linecap="round"/>`;
    } else if (/point_defense|flak|pd_/.test(id)) {
      glyph = `<circle cx="32" cy="34" r="15" fill="none" stroke="${c}" stroke-width="1.8" stroke-dasharray="4 3"/><path d="M32 46 V24 M23 30 L32 21 L41 30" fill="none" stroke="${hi}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>`;
    } else if (/plasma|disruptor|arc_emitter|neutron|energy_lance|tachyon/.test(id)) {
      glyph = `<circle cx="32" cy="32" r="10" fill="${c}" fill-opacity="0.32" stroke="${hi}" stroke-width="2"/><path d="M14 32 H22 M42 32 H50 M32 14 V22 M32 42 V50 M19 19 L25 25 M39 39 L45 45 M45 19 L39 25 M25 39 L19 45" stroke="${c}" stroke-width="2.2" stroke-linecap="round"/>`;
    } else if (/laser|beam|xray|gamma/.test(id)) {
      glyph = `<path d="M14 48 L48 14" stroke="${hi}" stroke-width="3.2" stroke-linecap="round"/><path d="M14 48 L48 14" stroke="${c}" stroke-width="6" stroke-opacity="0.3" stroke-linecap="round"/><circle cx="46" cy="16" r="5" fill="${hi}"/><path d="M14 40 L24 50" stroke="${c}" stroke-width="2.4" stroke-linecap="round"/>`;
    } else if (/mass_driver|railgun|kinetic|autocannon|gauss|artillery/.test(id)) {
      glyph = `<path d="M14 42 H36 L48 32 L36 22 H14 Z" fill="${c}" fill-opacity="0.24" stroke="${c}" stroke-width="2"/><path d="M22 28 H36 M22 36 H36 M48 32 H54" stroke="${hi}" stroke-width="2.2" stroke-linecap="round"/>`;
    } else if (/shield|deflector|capacitor|hardening/.test(id)) {
      glyph = `<path d="M32 11 L49 18 V32 C49 44 41 51 32 55 C23 51 15 44 15 32 V18 Z" fill="${c}" fill-opacity="0.22" stroke="${c}" stroke-width="2.2"/><path d="M32 17 L43 22 V32 C43 40 38 45 32 48" fill="none" stroke="${hi}" stroke-width="1.6" opacity="0.8"/>`;
    } else if (/armor|plating|hull|crystal/.test(id)) {
      glyph = `<polygon points="20,16 44,16 50,32 44,48 20,48 14,32" fill="${c}" fill-opacity="0.24" stroke="${c}" stroke-width="2.2"/><path d="M22 24 H42 M20 32 H44 M22 40 H42" stroke="${hi}" stroke-width="1.8" stroke-linecap="round"/>`;
    } else if (/hyper_drive|jump_drive|wormhole|hyper_relay|ftl|subspace/.test(id)) {
      glyph = `<circle cx="32" cy="32" r="16" fill="none" stroke="${c}" stroke-width="2"/><path d="M16 32 Q32 16 48 32 Q32 48 16 32 Z" fill="${c}" fill-opacity="0.22" stroke="${hi}" stroke-width="1.8"/><circle cx="32" cy="32" r="3.5" fill="${hi}"/>`;
    } else if (/thruster|afterburner|engine|sublight/.test(id)) {
      glyph = `<path d="M24 14 H40 L44 34 H20 Z" fill="${c}" fill-opacity="0.25" stroke="${c}" stroke-width="2"/><path d="M25 36 L22 51 M32 36 V54 M39 36 L42 51" stroke="${hi}" stroke-width="2.4" stroke-linecap="round"/>`;
    } else if (/sensor|cloak|detection|radar|spy|espionage|intel|cipher|encryption|decryption/.test(id)) {
      glyph = `<path d="M13 32 Q32 15 51 32 Q32 49 13 32 Z" fill="${c}" fill-opacity="0.18" stroke="${c}" stroke-width="2.1"/><circle cx="32" cy="32" r="6.5" fill="${c}" fill-opacity="0.35" stroke="${hi}" stroke-width="1.8"/><circle cx="32" cy="32" r="2.2" fill="${hi}"/>`;
    } else if (/power|energy|reactor|fusion|antimatter|zero_point|dark_matter/.test(id)) {
      glyph = `<path d="M36 10 L17 35 H31 L27 54 L47 28 H33 Z" fill="${c}" fill-opacity="0.32" stroke="${hi}" stroke-width="2" stroke-linejoin="round"/>`;
    } else if (/mineral|mining|excavation|strip_mining|purification|geothermal/.test(id)) {
      glyph = `<polygon points="32,14 48,26 42,48 22,48 16,26" fill="${c}" fill-opacity="0.24" stroke="${c}" stroke-width="2.1"/><path d="M32 14 L26 48 M32 14 L38 48 M16 26 H48" stroke="${hi}" stroke-width="1.3" opacity="0.75"/>`;
    } else if (/alloy|foundry|industrial|construction|assembly|nanite|mega_forge/.test(id)) {
      glyph = `<path d="M16 46 H48 V36 L38 30 V20 H26 V30 L16 36 Z" fill="${c}" fill-opacity="0.25" stroke="${c}" stroke-width="2"/><path d="M22 40 H42 M29 14 H35" stroke="${hi}" stroke-width="2" stroke-linecap="round"/>`;
    } else if (/trade|market|commercial|megacorp|wealth|luxur|consumer|economy/.test(id)) {
      glyph = `<circle cx="32" cy="32" r="16" fill="${c}" fill-opacity="0.18" stroke="${c}" stroke-width="2.1"/><path d="M24 38 L32 22 L40 38 M26 34 H38" fill="none" stroke="${hi}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>`;
    } else if (/food|hydroponic|farming|agri|nutri|eco_simulation/.test(id)) {
      glyph = `<path d="M32 12 C44 20 46 37 32 51 C18 37 20 20 32 12 Z" fill="${c}" fill-opacity="0.24" stroke="${c}" stroke-width="2.1"/><path d="M32 19 V49 M32 30 L40 24 M32 37 L24 31" stroke="${hi}" stroke-width="1.8" stroke-linecap="round"/>`;
    } else if (/robot|droid|synth|machine|positronic|sapient|ai_|computing|combat_computers|research_lab|basic_science/.test(id)) {
      glyph = `<rect x="20" y="20" width="24" height="24" rx="4" fill="${c}" fill-opacity="0.22" stroke="${c}" stroke-width="2.1"/><rect x="27" y="27" width="10" height="10" rx="2" fill="${hi}" opacity="0.8"/><path d="M26 12 V20 M38 12 V20 M26 44 V52 M38 44 V52 M12 26 H20 M12 38 H20 M44 26 H52 M44 38 H52" stroke="${c}" stroke-width="2" stroke-linecap="round"/>`;
    } else if (/colon|terraform|climate|habitability|blocker|clearing|planetary|gaia|tomb/.test(id)) {
      glyph = `<circle cx="32" cy="32" r="16" fill="${c}" fill-opacity="0.22" stroke="${c}" stroke-width="2.1"/><path d="M18 27 Q32 20 46 27 M18 37 Q32 44 46 37 M32 16 V48" fill="none" stroke="${hi}" stroke-width="1.4" opacity="0.8"/>`;
    } else if (/gene|biolog|cloning|vitality|epigenetic|fauna|beast|evolution|genome|bio/.test(id)) {
      glyph = `<path d="M22 14 C42 22 22 42 42 50 M42 14 C22 22 42 42 22 50" fill="none" stroke="${c}" stroke-width="2.3" stroke-linecap="round"/><path d="M25 22 H39 M24 32 H40 M25 42 H39" stroke="${hi}" stroke-width="1.6" stroke-linecap="round"/>`;
    } else if (/psionic|shroud|telepath|zro|precog|mind/.test(id)) {
      glyph = `<polygon points="32,12 48,32 32,52 16,32" fill="${c}" fill-opacity="0.22" stroke="${c}" stroke-width="2.1"/><circle cx="32" cy="32" r="6" fill="${hi}" fill-opacity="0.35" stroke="${hi}" stroke-width="1.8"/><circle cx="32" cy="32" r="2" fill="#ffffff"/>`;
    } else if (/archaeo|relic|precursor|secrets_|astral|rift|anomaly/.test(id)) {
      glyph = `<path d="M32 12 L48 46 H16 Z" fill="${c}" fill-opacity="0.22" stroke="${c}" stroke-width="2.1" stroke-linejoin="round"/><circle cx="32" cy="34" r="5" fill="${hi}" fill-opacity="0.35" stroke="${hi}" stroke-width="1.6"/>`;
    } else if (/admin|government|council|unity|doctrine|fleet_size|navy|leader|bureaucracy|diplomacy|federation|edict|galactic/.test(id)) {
      glyph = `<polygon points="32,12 37,24 50,25 40,34 43,47 32,40 21,47 24,34 14,25 27,24" fill="${c}" fill-opacity="0.25" stroke="${hi}" stroke-width="1.8" stroke-linejoin="round"/>`;
    } else if (branch === 'physics') {
      glyph = `<ellipse cx="32" cy="32" rx="19" ry="8" fill="none" stroke="${c}" stroke-width="2" transform="rotate(30 32 32)"/><ellipse cx="32" cy="32" rx="19" ry="8" fill="none" stroke="${c}" stroke-width="2" transform="rotate(-30 32 32)"/><circle cx="32" cy="32" r="4.5" fill="${hi}"/>`;
    } else if (branch === 'society') {
      glyph = `<path d="M32 13 C43 20 45 36 32 50 C19 36 21 20 32 13 Z" fill="${c}" fill-opacity="0.24" stroke="${c}" stroke-width="2.1"/><path d="M32 19 V48 M32 30 L40 24 M32 37 L24 31" stroke="${hi}" stroke-width="1.8" stroke-linecap="round"/>`;
    } else {
      glyph = `<circle cx="32" cy="32" r="11" fill="${c}" fill-opacity="0.22" stroke="${c}" stroke-width="2.3"/><circle cx="32" cy="32" r="4" fill="${hi}"/><path d="M32 11 V18 M32 46 V53 M11 32 H18 M46 32 H53 M17 17 L22 22 M42 42 L47 47 M47 17 L42 22 M22 42 L17 47" stroke="${c}" stroke-width="2.6" stroke-linecap="round"/>`;
    }

    return `<svg class="sg-svg-art sg-tech-svg" viewBox="0 0 64 64" aria-hidden="true"><defs>`
      + `<radialGradient id="${bgId}" cx="35%" cy="28%" r="75%"><stop offset="0%" stop-color="${bg1}"/><stop offset="100%" stop-color="${bg2}"/></radialGradient>`
      + `<radialGradient id="${glowId}" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="${c}" stop-opacity="0.26"/><stop offset="100%" stop-color="${c}" stop-opacity="0"/></radialGradient>`
      + `</defs><rect x="1.5" y="1.5" width="61" height="61" rx="9" fill="url(#${bgId})" stroke="${rim}" stroke-opacity="0.72" stroke-width="1.6"/>`
      + `<path d="M8 5 H56" stroke="${hi}" stroke-opacity="0.35" stroke-width="1.4" stroke-linecap="round"/>`
      + `<circle cx="32" cy="32" r="24" fill="url(#${glowId})"/>`
      + `${glyph}</svg>`;
  }

  function flagDataUrl(flag) {
    const colors = Array.isArray(flag?.colors) ? flag.colors : [];
    const c0 = String(colors[0] || '').toLowerCase();
    const c1 = String(colors[1] || '').toLowerCase();
    const primary = Object.hasOwn(FLAG_COLORS, c0) ? FLAG_COLORS[c0] : '#1e4e79';
    const secondary = Object.hasOwn(FLAG_COLORS, c1) ? FLAG_COLORS[c1] : '#0c1f36';
    const accent = '#70e1d6';
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">`
      + `<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="${primary}"/><stop offset="100%" stop-color="${secondary}"/></linearGradient></defs>`
      + `<rect width="64" height="64" rx="10" fill="url(#bg)"/>`
      + `<path d="M32 10 L50 22 L44 48 L32 55 L20 48 L14 22 Z" fill="none" stroke="${accent}" stroke-width="2.2" opacity="0.85"/>`
      + `<polygon points="32,18 36,28 46,28 38,34 41,44 32,38 23,44 26,34 18,28 28,28" fill="#eef6fb" opacity="0.92"/>`
      + `</svg>`;
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  }

  window.StellarisArt = {shipSvg, planetSvg, techSvg, flagDataUrl};
})();
