// Pure browser pin behavior, run with: node tests/test_v16_pins.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '..', 'static', 'app.js'), 'utf8');
const prefix = source.slice(0, source.indexOf('const viewCopy ='));
function loadBrowser() {
  const context = vm.createContext({});
  vm.runInContext(prefix + '\nthis.pinApi = {campaignPinId, pinnedGoal, goalDisplay, criticalResources};', context);
  return context.pinApi;
}

const first = {campaign:{id:'aaaaaaaaaaaaaaaa'}, empire:'Same name'};
const second = {campaign:{id:'bbbbbbbbbbbbbbbb'}, empire:'Same name'};
const goals = ['a','b','c','d','e'].map(key => ({key, title:key}));
const late = {key:'late', title:'Late goal'};
let api = loadBrowser();
const pin = {campaign_id:'aaaaaaaaaaaaaaaa', key:'late', title:'Late goal'};
assert.deepEqual(Array.from(api.goalDisplay(null, {goals}).goals), []);
assert.equal(api.goalDisplay(first, {goals, goal_catalog:[...goals, late]}, pin).goals[0].key, 'late');
assert.equal(api.criticalResources({...first, resource_runway:{food:{urgency:'urgent', months:2}}}).length, 1);
assert.equal(api.goalDisplay(second, {goals, goal_catalog:[...goals, late]}, pin).goals[0].key, 'a');
assert.equal(api.goalDisplay(first, {goals}, pin).dormant, true);
assert.equal(api.goalDisplay(first, {goals}, pin).goals[0].key, 'a');
api = loadBrowser(); // a new browser page receives the same pin from the server
assert.equal(api.goalDisplay(first, {goals, goal_catalog:[...goals, late]}, pin).goals[0].key, 'late');
assert.equal(api.goalDisplay(first, {goals}, null).dormant, false);
assert.equal(api.pinnedGoal({campaign:{id:'invalid'}}, pin), null);

// Dynamic save-driven quick-ask chips react to crises, revolts, deficits, and year milestones.
const quickEnd = source.indexOf('function number(value)');
const quickCtx = vm.createContext({});
vm.runInContext(source.slice(0, quickEnd) + '\nthis.dynamicQuickQuestions = dynamicQuickQuestions;', quickCtx);
const liveChips = quickCtx.dynamicQuickQuestions(
  {
    date: '2225.10.01', version: '4.6.0',
    campaign: {save_version: '4.6.0', dlc_summary: {active_ids: ['willpower']}},
    player: {net: {consumer_goods: -25, energy: 40}, net_known: {consumer_goods: true}, starbase_used: 7, starbase_capacity: 6, profile: {}},
    planets: [{name: 'Alpha Centauri Prime', stability: 22}],
    contacts: [],
  },
  {benchmark: {year: 2225, contacted_crises: [{preset: 'prethoryn', label: 'Prethoryn Scourge'}]}},
  'main',
);
assert.equal(liveChips[0].text, 'How to counter Prethoryn Scourge?');
assert.equal(liveChips[0].urgent, true);
assert.equal(liveChips[1].text, 'How do I stop Alpha Centauri Prime revolt?');
assert.equal(liveChips[2].text, 'How to increase consumer goods?');
assert.equal(liveChips[3].text, 'How to increase starbase capacity?');
assert.ok(liveChips.length <= 5);
console.log('Phase 3 browser pin & dynamic quick-ask cases passed');
