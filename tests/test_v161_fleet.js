const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const root = {innerHTML: '', querySelector: () => null, querySelectorAll: () => []};
const context = {
  $: id => { assert.equal(id, 'fleet-dashboard'); return root; },
  esc: value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char])),
  showNotice: () => {},
  post: async () => ({fleet_limit: 140}),
  encodeURIComponent,
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('static/fleet.js', 'utf8'), context);

const snapshot = {
  date: '2277.10.01', version: '4.5.2', campaign: {id: 'aaaaaaaaaaaaaaaa', mods: []},
  player: {naval_used: 166, military: 2320, stock: {alloys: 13049}, net: {alloys: 43.4}},
  contacts: [],
  ship_builds: {
    usage_status: 'matches_saved_total', class_usage: {corvette: 70, frigate: 96},
    fleets: [{id: 3, name: '3rd Fleet', power: 265, size: 24, planned_size: 48,
      ship_count: 3, classes: {frigate: 3}, location: 'Sirius'}],
    designs: [{id: 10, name: '<Fox>', size_key: 'frigate', size: 'Frigate', role: 'Explosive',
      naval_usage: 8, slots: [{slot: 'TORPEDO_01', component: 'TORPEDO_1'}]}],
    policy_details: [],
  },
};
context.renderFleet(snapshot, {fleet_limit: null});
assert.match(root.innerHTML, /Rebuild 3rd Fleet/);
assert.match(root.innerHTML, /24 of 48 on its saved Fleet Manager plan/);
assert.match(root.innerHTML, /Used capacity or maximum unavailable/);
assert.match(root.innerHTML, /&lt;Fox&gt;/);
assert.doesNotMatch(root.innerHTML, /<Fox>/);
let totals = context.fleetPlanTotals(snapshot.ship_builds.designs, {10: 2}, 166, null, snapshot.ship_builds.fleets[0]);
assert.equal(totals.added, 16);
assert.equal(totals.planAfter, 40);
assert.equal(totals.overLimit, false);

context.renderFleet(snapshot, {fleet_limit: 140});
assert.match(root.innerHTML, /Raise naval capacity before adding ships/);
assert.match(root.innerHTML, /26 above the 140 limit you entered/);
totals = context.fleetPlanTotals(snapshot.ship_builds.designs, {10: 2}, 166, 140, snapshot.ship_builds.fleets[0]);
assert.equal(totals.overLimit, true);

context.renderFleet({date: '2280.01.01', campaign: {id: 'bbbbbbbbbbbbbbbb'}, player: {}, ship_builds: {}}, {fleet_limit: null});
assert.match(root.innerHTML, /No owned military fleet could be read/);
assert.match(root.innerHTML, /No saved combat designs/);
assert.match(root.innerHTML, /No owned military fleets found/);
assert.match(root.innerHTML, /Add a saved design to estimate naval use/);
assert.doesNotMatch(root.innerHTML, /empire 0 → 0/);
const partial = {...snapshot, player: {...snapshot.player, naval_used: null},
  ship_builds: {...snapshot.ship_builds, fleets: [{...snapshot.ship_builds.fleets[0],
    size: null, ship_count: 4, classes_complete: false}]}};
context.renderFleet(partial, {fleet_limit: null});
assert.match(root.innerHTML, /4 ships · class mix partial/);
assert.match(root.innerHTML, /Size unknown/);
assert.doesNotMatch(root.innerHTML, /empire 0 → 0/);
vm.runInContext('fleetPlan[10] = 1', context);
context.renderFleet(partial, {fleet_limit: null});
assert.match(root.innerHTML, /empire total unknown/);
console.log('Fleet render, planning, over-limit and missing-data cases passed');
