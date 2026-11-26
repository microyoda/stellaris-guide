/* Original inline SVG artwork for Stellaris Guide (zero copyrighted game assets).
   Used directly in Web mode and as rich fallbacks when local Steam art is unavailable. */
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
    const hullId = `sg-hull-${id}`;
    const bioId = `sg-bio-${id}`;
    const key = String(sizeKey || '').toLowerCase();
    const shapes = {
      corvette: `<path d="M32 8 L43 38 L32 33 L21 38 Z" fill="url(#${hullId})" stroke="#7ce8e2" stroke-width="1.6"/><path d="M32 15 L36 30 L32 27 L28 30 Z" fill="#bdf7f4"/><path d="M25 38 L25 46 M39 38 L39 46" stroke="#ffad54" stroke-width="2" stroke-linecap="round"/>`,
      frigate: `<path d="M32 7 L42 22 L45 41 L32 36 L19 41 L22 22 Z" fill="url(#${hullId})" stroke="#f0b668" stroke-width="1.6"/><circle cx="32" cy="18" r="3" fill="#ffad54"/><path d="M27 40 L27 49 M37 40 L37 49" stroke="#ffad54" stroke-width="2.2" stroke-linecap="round"/>`,
      destroyer: `<path d="M32 6 L40 20 L48 36 L44 43 L32 38 L20 43 L16 36 L24 20 Z" fill="url(#${hullId})" stroke="#a69bff" stroke-width="1.6"/><rect x="29" y="18" width="6" height="14" rx="2" fill="#d3ceff"/><path d="M24 42 L24 51 M32 40 L32 52 M40 42 L40 51" stroke="#7ce8e2" stroke-width="2" stroke-linecap="round"/>`,
      cruiser: `<path d="M32 5 L41 16 L44 26 L51 35 L47 45 L32 41 L17 45 L13 35 L20 26 L23 16 Z" fill="url(#${hullId})" stroke="#55d8aa" stroke-width="1.6"/><path d="M27 17 H37 V36 H27 Z" fill="#9bf2d1" opacity="0.8"/><path d="M22 45 L22 54 M32 43 L32 55 M42 45 L42 54" stroke="#55d8aa" stroke-width="2.2" stroke-linecap="round"/>`,
      battleship: `<path d="M32 4 L40 13 L45 20 L53 31 L50 47 L39 44 L32 48 L25 44 L14 47 L11 31 L19 20 L24 13 Z" fill="url(#${hullId})" stroke="#e2829e" stroke-width="1.6"/><path d="M27 12 H37 V39 H27 Z" fill="#f7b9cb" opacity="0.75"/><circle cx="20" cy="34" r="2.5" fill="#7ce8e2"/><circle cx="44" cy="34" r="2.5" fill="#7ce8e2"/><path d="M21 47 L21 56 M32 49 L32 57 M43 47 L43 56" stroke="#ffad54" stroke-width="2.4" stroke-linecap="round"/>`,
      titan: `<path d="M32 3 L38 11 L43 16 L46 27 L55 37 L51 50 L39 47 L32 52 L25 47 L13 50 L9 37 L18 27 L21 16 L26 11 Z" fill="url(#${hullId})" stroke="#e6cf75" stroke-width="1.7"/><path d="M32 6 V44" stroke="#ffe794" stroke-width="2.4"/><circle cx="32" cy="24" r="5" fill="#ffe794" opacity="0.85"/><path d="M19 50 L19 58 M32 53 L32 59 M45 50 L45 58" stroke="#e6cf75" stroke-width="2.4" stroke-linecap="round"/>`,
      arkship: `<ellipse cx="32" cy="30" rx="22" ry="15" fill="url(#${hullId})" stroke="#58ded7" stroke-width="1.8"/><ellipse cx="32" cy="30" rx="12" ry="7" fill="#18475a" stroke="#9cf5f0" stroke-width="1.2"/><circle cx="32" cy="30" r="3.5" fill="#58ded7"/><path d="M18 44 L22 54 M32 46 L32 56 M46 44 L42 54" stroke="#58ded7" stroke-width="2.2" stroke-linecap="round"/>`,
      mauler: `<path d="M32 8 C42 14 48 26 44 42 C38 38 35 45 32 50 C29 45 26 38 20 42 C16 26 22 14 32 8 Z" fill="url(#${bioId})" stroke="#70e19a" stroke-width="1.7"/><circle cx="32" cy="24" r="4" fill="#c7ffd8"/><path d="M24 28 Q32 34 40 28" fill="none" stroke="#c7ffd8" stroke-width="1.4"/>`,
    };
    const aliases = {
      military_arkship: 'arkship', juggernaut: 'titan', colossus: 'titan',
      weaver: 'mauler', harbinger: 'mauler', stinger: 'mauler',
    };
    const resolvedKey = Object.hasOwn(shapes, key) ? key : (Object.hasOwn(aliases, key) ? aliases[key] : 'corvette');
    const body = shapes[resolvedKey];
    return `<svg class="sg-svg-art" viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="${hullId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3a6e85"/><stop offset="100%" stop-color="#13293d"/></linearGradient><linearGradient id="${bioId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#2c7a5b"/><stop offset="100%" stop-color="#113328"/></linearGradient></defs>${body}</svg>`;
  }

  function planetSvg(classKey) {
    const gradId = `sg-planet-${++svgUid}`;
    const key = String(classKey || '').toLowerCase();
    let c1 = '#4ea5d9', c2 = '#1d5b4c', c3 = '#0d263b', ring = false;
    if (/gaia/.test(key)) { c1 = '#6de8a8'; c2 = '#2f9fd6'; c3 = '#134a4b'; }
    else if (/ocean|aquatic/.test(key)) { c1 = '#5ec6ff'; c2 = '#1f6fb8'; c3 = '#0c2852'; }
    else if (/desert|arid|savannah/.test(key)) { c1 = '#e8b36b'; c2 = '#a9622e'; c3 = '#4a2612'; }
    else if (/arctic|alpine|tundra/.test(key)) { c1 = '#d8f0ff'; c2 = '#6ca2c8'; c3 = '#1f3e59'; }
    else if (/machine|city|ecumenopolis|relic/.test(key)) { c1 = '#90b4c8'; c2 = '#395264'; c3 = '#14202b'; ring = true; }
    else if (/hive|infested/.test(key)) { c1 = '#97cf5c'; c2 = '#4e6f2c'; c3 = '#1e2c12'; }
    else if (/nuked|tomb/.test(key)) { c1 = '#a49b8f'; c2 = '#5e5248'; c3 = '#231e1b'; }
    else if (/habitat|ringworld/.test(key)) { c1 = '#6be8e0'; c2 = '#256c78'; c3 = '#0d2433'; ring = true; }
    return `<svg class="sg-svg-art sg-planet-svg" viewBox="0 0 64 64" aria-hidden="true">
      <defs><radialGradient id="${gradId}" cx="34%" cy="30%" r="68%">
        <stop offset="0%" stop-color="${c1}"/><stop offset="55%" stop-color="${c2}"/><stop offset="100%" stop-color="${c3}"/>
      </radialGradient></defs>
      ${ring ? '<ellipse cx="32" cy="33" rx="28" ry="9" fill="none" stroke="#85dce0" stroke-width="2" opacity="0.55" transform="rotate(-18 32 33)"/>' : ''}
      <circle cx="32" cy="32" r="20" fill="url(#${gradId})" stroke="${c1}" stroke-opacity="0.45" stroke-width="1.2"/>
      <path d="M17 27 Q27 22 36 27 T49 26" fill="none" stroke="#ffffff" stroke-opacity="0.22" stroke-width="3" stroke-linecap="round"/>
      <path d="M19 38 Q30 34 44 39" fill="none" stroke="#000000" stroke-opacity="0.22" stroke-width="3" stroke-linecap="round"/>
    </svg>`;
  }

  function techSvg(area, techId = '') {
    const branch = String(area || '').toLowerCase();
    const id = String(techId || '').toLowerCase();
    const color = branch === 'physics' ? '#5aaeff' : branch === 'society' ? '#45d38e' : '#ffad54';
    let glyph;
    if (/laser|plasma|weapon|torpedo|missile|kinetic|rail|lance/.test(id)) {
      glyph = `<path d="M14 48 L48 14 M36 14 H48 V26" fill="none" stroke="${color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="22" cy="40" r="5" fill="${color}" opacity="0.35"/>`;
    } else if (/shield|armor|hull|deflector|bastion/.test(id)) {
      glyph = `<path d="M32 10 L48 18 V33 C48 44 40 50 32 54 C24 50 16 44 16 33 V18 Z" fill="${color}" fill-opacity="0.2" stroke="${color}" stroke-width="2.2"/>`;
    } else if (/corvette|destroyer|cruiser|battleship|titan|arkship|stinger|mauler|starbase|citadel/.test(id)) {
      glyph = `<path d="M32 12 L44 44 L32 38 L20 44 Z" fill="${color}" fill-opacity="0.25" stroke="${color}" stroke-width="2.2"/>`;
    } else if (/power|energy|reactor|fusion|zero_point/.test(id)) {
      glyph = `<path d="M35 10 L18 35 H31 L27 54 L46 28 H33 Z" fill="${color}" fill-opacity="0.28" stroke="${color}" stroke-width="2" stroke-linejoin="round"/>`;
    } else if (branch === 'physics') {
      glyph = `<ellipse cx="32" cy="32" rx="18" ry="8" fill="none" stroke="${color}" stroke-width="2" transform="rotate(30 32 32)"/><ellipse cx="32" cy="32" rx="18" ry="8" fill="none" stroke="${color}" stroke-width="2" transform="rotate(-30 32 32)"/><circle cx="32" cy="32" r="4" fill="${color}"/>`;
    } else if (branch === 'society') {
      glyph = `<path d="M32 12 C42 20 44 36 32 50 C20 36 22 20 32 12 Z" fill="${color}" fill-opacity="0.22" stroke="${color}" stroke-width="2.2"/><path d="M32 18 V48 M32 30 L40 24 M32 36 L24 30" stroke="${color}" stroke-width="1.8" stroke-linecap="round"/>`;
    } else {
      glyph = `<circle cx="32" cy="32" r="11" fill="${color}" fill-opacity="0.2" stroke="${color}" stroke-width="2.4"/><path d="M32 12 V18 M32 46 V52 M12 32 H18 M46 32 H52 M18 18 L22 22 M42 42 L46 46 M46 18 L42 22 M22 42 L18 46" stroke="${color}" stroke-width="2.6" stroke-linecap="round"/>`;
    }
    return `<svg class="sg-svg-art" viewBox="0 0 64 64" aria-hidden="true">${glyph}</svg>`;
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
