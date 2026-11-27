const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function makeElement(id = '') {
  const listeners = new Map();
  const childrenBySelector = new Map();
  const el = {
    id,
    className: '',
    hidden: false,
    open: false,
    value: '',
    textContent: '',
    dataset: {},
    style: {},
    _html: '',
    classList: {
      _set: new Set(),
      toggle(name, force) {
        if (force === undefined) {
          if (this._set.has(name)) this._set.delete(name); else this._set.add(name);
        } else if (force) this._set.add(name); else this._set.delete(name);
      },
      contains(name) { return this._set.has(name); },
    },
    set innerHTML(val) { this._html = String(val); },
    get innerHTML() { return this._html; },
    insertAdjacentHTML(_pos, html) { this._html += String(html); },
    setAttribute(k, v) { this[k] = v; },
    addEventListener(type, fn) {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(fn);
    },
    dispatch(type, ev = {}) {
      for (const fn of (listeners.get(type) || [])) fn(ev);
    },
    closest() { return null; },
    querySelector(sel) {
      if (!childrenBySelector.has(sel)) childrenBySelector.set(sel, makeElement(sel));
      return childrenBySelector.get(sel);
    },
    querySelectorAll() { return []; },
  };
  return el;
}

const storageMap = new Map();
const byId = new Map();
const doc = {
  readyState: 'loading',
  body: {
    appendChild(el) { if (el.id) byId.set(el.id, el); },
  },
  getElementById(id) { return byId.get(id) || null; },
  createElement() { return makeElement(); },
  addEventListener() {},
};

const win = {
  location: {search: ''},
  addEventListener() {},
  StellarisArt: {techSvg: () => '<svg></svg>'},
};
const context = {
  window: win,
  document: doc,
  localStorage: {
    getItem: k => storageMap.has(k) ? storageMap.get(k) : null,
    setItem: (k, v) => storageMap.set(k, String(v)),
  },
  fetch: async () => ({
    ok: true,
    json: async () => ({
      presets: [{id: 'une-452', label: 'UNE'}],
      dlcs: [],
      states: {
        'une-452': {
          status: 'ready',
          demo_preset: 'une-452',
          snapshot: {campaign: {id: 'demo-camp-1'}, version: '4.6.0', date: '2277.10.01'},
          advice: {goals: []},
        },
      },
    }),
  }),
  Worker: class FakeWorker {
    addEventListener() {}
    postMessage() {}
  },
  URL: {createObjectURL: () => 'blob:mock'},
  Blob: class {},
  console,
  setTimeout,
  clearTimeout,
};
win.window = win;
vm.createContext(context);
vm.runInContext(fs.readFileSync('static/web-runtime.js', 'utf8'), context);

(async () => {
  const api = win.STELLARIS_API;
  assert.ok(api && typeof api.openTechRouteModal === 'function');
  const origPost = api.post;
  api.post = async (path, body) => {
    if (path === '/api/tech-route') {
      return {
        route: {
          target_id: body.target,
          name: 'Mega Engineering',
          area: 'engineering',
          tier: 5,
          state: 'unmet',
          next_check: 'Check prerequisites.',
          reason: 'Exported 4.6.0 graph.',
          steps: [{id: 'tech_mega_engineering', name: 'Mega Engineering', area: 'engineering', tier: 5, state: 'unmet'}],
          one_of: [],
          next_unlocks: [],
          dlc: [],
          tier_gate: {tier: 5, required_previous_tier: 6, researched_previous_tier: 2, status: 'not_met'},
        },
        targets: [
          {id: 'tech_mega_engineering', name: 'Mega Engineering', area: 'engineering', tier: 5, state: 'unmet', required_dlc: ['utopia']},
          {id: 'tech_galactic_halls', name: 'Galactic Halls', area: 'society', tier: 3, state: 'researched', required_dlc: ['willpower']},
        ],
      };
    }
    return origPost(path, body);
  };

  await api.openTechRouteModal('tech_mega_engineering');
  const overlay = doc.getElementById('web-tech-route-overlay');
  assert.ok(overlay, 'modal overlay created');
  assert.equal(overlay.querySelector('#web-route-title').textContent, 'Mega Engineering · Tier 5');
  assert.match(overlay.querySelector('#web-route-body').innerHTML, /Prerequisite path/);
  assert.match(overlay.querySelector('#web-route-browser').innerHTML, /Galactic Halls/);
  assert.match(overlay.querySelector('#web-route-watchlist').innerHTML, /Watchlist empty/);

  // Toggle watchlist add and verify persistence under campaignIdOf (no ReferenceError).
  overlay.querySelector('#web-route-watch-toggle').dispatch('click');
  assert.equal(overlay.querySelector('#web-route-watch-toggle').textContent, '★ Watching');
  assert.match(overlay.querySelector('#web-route-watchlist').innerHTML, /Mega Engineering/);
  const savedWatch = JSON.parse(storageMap.get('sg_web_tech_watchlist_v1'));
  assert.deepEqual(savedWatch['demo-camp-1'], ['tech_mega_engineering']);

  // Live search narrows tech list.
  overlay.querySelector('#web-route-search').dispatch('input', {target: {value: 'halls'}});
  assert.match(overlay.querySelector('#web-route-browser').innerHTML, /Galactic Halls/);
  assert.doesNotMatch(overlay.querySelector('#web-route-browser').innerHTML, /Mega Engineering/);

  // Toggle off removes from watchlist.
  overlay.querySelector('#web-route-watch-toggle').dispatch('click');
  assert.match(overlay.querySelector('#web-route-watchlist').innerHTML, /Watchlist empty/);
  console.log('Web runtime tech route modal, search, and watchlist passed');
})().catch(err => {
  console.error(err);
  process.exit(1);
});
