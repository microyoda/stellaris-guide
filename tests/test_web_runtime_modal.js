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

  // Feedback endpoint: explicit empty override tests local GitHub Issue fallback mode.
  win.STELLARIS_FEEDBACK_ENDPOINT = '';
  const fbFallback = await origPost('/api/feedback', {
    rating: 'useful', reason: 'helpful', comment: 'Great 4.6 guide!', view: 'tech',
    attachment: {name: 'shot.png', type: 'image/png', size: 12, data_base64: 'AAAA'},
  });
  assert.equal(fbFallback.ok, true);
  assert.equal(fbFallback.mode, 'local_fallback');
  assert.match(fbFallback.github_issue_url, /github\.com\/microyoda\/stellaris-guide\/issues\/new/);
  const storedFb = JSON.parse(storageMap.get('sg_web_feedback_v1'));
  assert.equal(storedFb[0].attachment_name, 'shot.png');
  assert.equal(storedFb[0].data_base64, undefined);

  // Default configured Google Apps Script Web App endpoint sends JSON POST cleanly.
  delete win.STELLARIS_FEEDBACK_ENDPOINT;
  let defaultPostedUrl = '';
  context.fetch = async (url) => {
    defaultPostedUrl = url;
    return {ok: true, status: 200, text: async () => JSON.stringify({ok: true})};
  };
  const fbDefault = await origPost('/api/feedback', {rating: 'useful', comment: 'Default live endpoint works'});
  assert.equal(fbDefault.mode, 'google_sheet');
  assert.match(defaultPostedUrl, /^https:\/\/script\.google\.com\/macros\/s\/[A-Za-z0-9_-]+\/exec$/);

  // Reject unsafe file extensions (.svg, .exe, .html) and oversized files.
  await assert.rejects(() => origPost('/api/feedback', {
    rating: 'useful', attachment: {name: 'evil.svg', type: 'image/svg+xml', size: 10, data_base64: 'AAAA'},
  }), /Unsupported attachment type/);
  await assert.rejects(() => origPost('/api/feedback', {
    rating: 'useful', attachment: {name: 'huge.png', type: 'image/png', size: 5 * 1024 * 1024, data_base64: 'AAAA'},
  }), /4 MB/);

  // Reject non-Apps-Script endpoint URL and query-string URLs; reject HTML auth error pages.
  win.STELLARIS_FEEDBACK_ENDPOINT = 'https://evil.example.com/steal';
  await assert.rejects(() => origPost('/api/feedback', {rating: 'useful', comment: 'hi'}), /Invalid feedback endpoint/);
  win.STELLARIS_FEEDBACK_ENDPOINT = 'https://script.google.com/macros/s/AKfycbTest/exec?foo=bar';
  await assert.rejects(() => origPost('/api/feedback', {rating: 'useful', comment: 'hi'}), /Invalid feedback endpoint/);

  context.fetch = async () => ({ok: true, status: 200, text: async () => '<html>Sign in</html>'});
  win.STELLARIS_FEEDBACK_ENDPOINT = 'https://script.google.com/macros/s/AKfycbTestDeploy123/exec';
  await assert.rejects(() => origPost('/api/feedback', {rating: 'useful', comment: 'hi'}), /unexpected response/);

  let postedBody = null;
  context.fetch = async (url, opts) => {
    postedBody = {url, headers: opts.headers, body: JSON.parse(opts.body)};
    return {ok: true, status: 200, text: async () => JSON.stringify({ok: true})};
  };
  win.STELLARIS_FEEDBACK_ENDPOINT = 'https://script.google.com/macros/s/AKfycbTestDeploy123/exec';
  const fbSent = await origPost('/api/feedback', {
    rating: 'not_useful', reason: 'incorrect', comment: 'Check revolt step', view: 'main',
    attachment: {name: 'revolt.jpg', type: 'image/jpeg', size: 128, data_base64: 'AQID'},
  });
  assert.equal(fbSent.mode, 'google_sheet');
  assert.equal(postedBody.headers['Content-Type'], 'text/plain;charset=utf-8');
  assert.equal(postedBody.body.attachment.name, 'revolt.jpg');
  delete win.STELLARIS_FEEDBACK_ENDPOINT;

  console.log('Web runtime tech route modal, search, watchlist, and Google Sheet feedback passed');
})().catch(err => {
  console.error(err);
  process.exit(1);
});
