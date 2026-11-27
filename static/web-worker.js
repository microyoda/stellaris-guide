/* Pyodide Web Worker: serialized execution of pure-Python stellaris_guide modules in-browser. */
const PYODIDE_INDEX = 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/';
const PYTHON_FILES = [
  '__init__.py',
  'dlcs.py',
  'saves.py',
  'strategy.py',
  'playbooks.py',
  'playbooks.json',
  'guide_knowledge.py',
  'guide_knowledge.json',
  'traditions_data.py',
  'question_context.py',
  'advice.py',
  'tech_graph.json',
  'web_bridge.py',
];

let pyodide = null;
let readyPromise = null;
let messageQueue = Promise.resolve();

async function ensureReady() {
  if (readyPromise) return readyPromise;
  readyPromise = (async () => {
    try {
      self.postMessage({type: 'status', message: 'Loading in-browser Python engine…'});
      importScripts(`${PYODIDE_INDEX}pyodide.js`);
      pyodide = await loadPyodide({indexURL: PYODIDE_INDEX});
      pyodide.FS.mkdirTree('/app/stellaris_guide');
      const workerBuildId = (() => {
        try {
          return new URL(self.location.href).searchParams.get('v') || '';
        } catch {
          return '';
        }
      })();
      const suffix = workerBuildId ? `?v=${encodeURIComponent(workerBuildId)}` : '';
      await Promise.all(PYTHON_FILES.map(async name => {
        const response = await fetch(`./py/stellaris_guide/${name}${suffix}`, {cache: 'no-store'});
        if (!response.ok) throw new Error(`Missing bundled module ${name}`);
        const text = await response.text();
        pyodide.FS.writeFile(`/app/stellaris_guide/${name}`, text, {encoding: 'utf8'});
      }));
      await pyodide.runPythonAsync(`
import sys, json
if "/app" not in sys.path:
    sys.path.insert(0, "/app")
from stellaris_guide import web_bridge

def _dispatch_parse(raw_buf, filename, modified, plan_json, spoilers, campaign_label):
    data = bytes(raw_buf.to_py())
    res = web_bridge.analyze_save_archive(
        data,
        filename,
        modified=modified,
        plan=json.loads(plan_json),
        spoilers_active=spoilers,
        campaign_label=campaign_label,
    )
    return json.dumps(res, ensure_ascii=False)

def _dispatch_reproject(spoilers):
    return json.dumps(web_bridge.reproject_current_save(spoilers_active=spoilers), ensure_ascii=False)

def _dispatch_demo(preset, dlcs_json, spoilers):
    dlcs = json.loads(dlcs_json)
    return json.dumps(web_bridge.build_demo_state(preset, enabled_dlc_ids=dlcs, spoilers_active=spoilers), ensure_ascii=False)

def _dispatch_ask(question, snapshot_json, advice_json):
    return json.dumps(web_bridge.ask_builtin(question, json.loads(snapshot_json), json.loads(advice_json)), ensure_ascii=False)

def _dispatch_tech_route(snapshot_json, target):
    snap = json.loads(snapshot_json)
    return json.dumps({
        "route": web_bridge.web_route_for_target(snap, target),
        "targets": web_bridge.web_route_targets(snap),
    }, ensure_ascii=False)
`);
      self.postMessage({type: 'status', message: 'In-browser engine ready'});
      return pyodide;
    } catch (error) {
      readyPromise = null;
      pyodide = null;
      throw error;
    }
  })();
  return readyPromise;
}

async function handleMessage(event) {
  const {id, action, payload} = event.data || {};
  try {
    const py = await ensureReady();
    let result;
    if (action === 'init') {
      result = {ok: true};
    } else if (action === 'parse_save') {
      const fn = py.globals.get('_dispatch_parse');
      const bytes = new Uint8Array(payload.buffer);
      try {
        const out = fn(
          bytes,
          String(payload.filename || 'autosave.sav'),
          Number(payload.modified || Date.now() / 1000),
          JSON.stringify(payload.plan || {}),
          Boolean(payload.spoilers_active),
          String(payload.campaign_label || ''),
        );
        result = JSON.parse(out);
      } finally {
        fn.destroy();
      }
    } else if (action === 'reproject') {
      const fn = py.globals.get('_dispatch_reproject');
      try {
        result = JSON.parse(fn(Boolean(payload.spoilers_active)));
      } finally {
        fn.destroy();
      }
    } else if (action === 'demo_state') {
      const fn = py.globals.get('_dispatch_demo');
      try {
        const out = fn(
          String(payload.preset || 'une-452'),
          payload.dlc_ids ? JSON.stringify(payload.dlc_ids) : 'null',
          Boolean(payload.spoilers_active),
        );
        result = JSON.parse(out);
      } finally {
        fn.destroy();
      }
    } else if (action === 'ask') {
      const fn = py.globals.get('_dispatch_ask');
      try {
        const out = fn(
          String(payload.question || ''),
          JSON.stringify(payload.snapshot || {}),
          JSON.stringify(payload.advice || {}),
        );
        result = JSON.parse(out);
      } finally {
        fn.destroy();
      }
    } else if (action === 'tech_route') {
      const fn = py.globals.get('_dispatch_tech_route');
      try {
        const out = fn(
          JSON.stringify(payload.snapshot || {}),
          String(payload.target || ''),
        );
        result = JSON.parse(out);
      } finally {
        fn.destroy();
      }
    } else {
      throw new Error(`Unknown worker action: ${action}`);
    }
    self.postMessage({id, ok: true, result});
  } catch (error) {
    self.postMessage({id, ok: false, error: String(error?.message || error)});
  }
}

self.onmessage = event => {
  messageQueue = messageQueue.then(() => handleMessage(event));
};
