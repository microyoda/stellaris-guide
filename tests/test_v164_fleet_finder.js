const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const root = {innerHTML: '', querySelector: () => null, querySelectorAll: () => []};
const context = {
  $: () => root, esc: value => String(value ?? '').replace(/[&<>"']/g, ''),
  showNotice: () => {}, post: async () => ({}), encodeURIComponent,
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('static/fleet.js', 'utf8'), context);

const laser = {id: 1, name: 'Laser Screen', size_key: 'corvette', role: 'General',
  slots: [{slot: 'SMALL_GUN', component: 'SMALL_LASER_1'}, {slot: 'UTILITY', component: 'ARMOR_1'}],
  component_evidence: [], naval_usage: 1};
const laserTie = {...laser, id: 2, name: 'Laser Wing'};
const gun = {...laser, id: 3, name: 'Gun Screen', slots: [{slot: 'SMALL_GUN', component: 'SMALL_MASS_DRIVER_1'}]};
const missing = {...laser, id: 4, name: 'Unknown Kit', slots: []};
const locked = {...laser, id: 5, name: 'Research Gap', component_evidence: [
  {component: 'SMALL_LASER_1', unresearched_tech: ['tech_lasers_2']}],
};
const mixed = {...laser, id: 6, name: 'Mixed Wing', slots: [
  {slot: 'SMALL_GUN_1', component: 'SMALL_LASER_1'},
  {slot: 'SMALL_GUN_2', component: 'SMALL_MASS_DRIVER_1'}]};
const shielded = {...laser, id: 11, name: 'Shield Wing', slots: [
  {slot: 'SMALL_GUN', component: 'SMALL_LASER_1'}, {slot: 'UTILITY', component: 'SHIELD_1'}]};
const designs = [missing, gun, laserTie, locked, laser];
const find = (goal, defense = 'unknown', weapons = 'unknown', list = designs, extras = {}) =>
  context.fleetFinder(list, 'corvette', goal, defense, weapons, extras);

let result = find('damage');
assert.equal(result.top.design.name, 'Gun Screen');
assert.equal(result.tied, true);
assert.equal(result.candidates.at(-1).status, 'blocked');
assert.equal(result.candidates.find(item => item.design.id === 4).fit, 'insufficient');
assert.equal(find('balanced', 'shield').top.design.name, 'Gun Screen');
assert.equal(find('balanced', 'armor').top.design.name, 'Laser Screen');
assert.equal(find('balanced', 'unknown', 'kinetic', [laser, shielded]).top.design.name, 'Laser Screen');
assert.equal(find('balanced', 'unknown', 'energy', [laser, shielded]).top.design.name, 'Shield Wing');
assert.equal(find('balanced').top, undefined);
assert.match(context.fleetConcept('destroyer', 'survival', 'explosive'), /point-defense escort/);
const policyOne = context.fleetAssess(laser, 'damage', 'unknown', 'unknown', {policies: [
  {key: 'fleet_doctrine', policy_label: 'Fleet Doctrine', selected_label: 'Phalanx'}]});
const policyTwo = context.fleetAssess(laser, 'damage', 'unknown', 'unknown', {policies: [
  {key: 'fleet_doctrine', policy_label: 'Fleet Doctrine', selected_label: 'Battle Line'}]});
assert.notEqual(policyOne.policyFit, policyTwo.policyFit);
assert.equal(context.fleetAssess(mixed, 'balanced', 'shield', 'unknown').offense, 'mixed');
assert.equal(context.fleetAssess(mixed, 'balanced', 'armor', 'unknown').fit, 'fitting');
const crowded = [locked, {...locked, id: 7, name: 'A Locked'},
  {...locked, id: 8, name: 'B Locked'}, {...locked, id: 9, name: 'C Locked'},
  {...locked, id: 10, name: 'D Locked'}, laser];
assert.equal(find('damage', 'unknown', 'unknown', crowded).candidates[0].design.name, 'Laser Screen');
assert.equal(find('low-cost').top, undefined);
assert.equal(find('low-cost', 'armor', 'kinetic').top, undefined);
assert.equal(find('mobility', 'shield').top, undefined);
assert.equal(find('screening', 'unknown', 'explosive').top, undefined);
assert.equal(find('damage', 'unknown', 'unknown', [locked]).top, undefined);
assert.equal(context.fleetAssess(locked, 'damage', 'unknown', 'unknown').status, 'blocked');
assert.match(context.fleetAssess(laser, 'damage', 'unknown', 'unknown', {mods: ['test mod']}).reasons.join(' '), /modified fitting rules/);
assert.match(context.fleetAssess(laser, 'damage', 'unknown', 'unknown', {version: '4.6.0'}).reasons.join(' '), /outside the verified 4.5/);
assert.doesNotMatch(context.fleetAssess(laser, 'damage', 'unknown', 'unknown', {version: 'Cygnus v4.5.2'}).reasons.join(' '), /outside the verified 4.5/);

const snapshot = {date: '2277.10.01', version: '4.5.2', campaign: {id: 'abc', mods: []},
  player: {naval_used: 4, military: 100, stock: {alloys: 50}, net: {alloys: 2}},
  contacts: [], ship_builds: {designs, fleets: [], class_usage: {}, policy_details: [],
    hidden_enemy_design: 'SECRET_TACHYON_LOADOUT'}};
context.renderFleet(snapshot, {});
assert.match(root.innerHTML, /What should I build/);
assert.match(root.innerHTML, /Enemy defenses you saw/);
assert.match(root.innerHTML, /conditional/);
assert.match(root.innerHTML, /Compare 5 saved Corvette designs/);
assert.match(root.innerHTML, /fleet-finder-choices" open/);
assert.doesNotMatch(root.innerHTML, /SECRET_TACHYON_LOADOUT/);
let focused = 0;
const goalButton = {dataset: {fleetGoal: 'damage'}, addEventListener: (name, fn) => {
  if (name === 'click') goalButton.click = fn;
}};
root.querySelectorAll = selector => selector === '[data-fleet-goal]' ? [goalButton] : [];
root.querySelector = selector => selector === '[data-fleet-goal="damage"]' ? {focus: () => focused++} : null;
context.renderFleet(snapshot, {});
goalButton.click();
assert.equal(focused, 1);
assert.match(root.innerHTML, /data-fleet-goal="damage" aria-pressed="true"/);
const close = {focus: () => focused++, addEventListener: (name, fn) => { if (name === 'click') close.click = fn; }};
const panel = {hidden: false, insertAdjacentHTML: () => {},
  querySelector: selector => selector === '.fleet-compare-close' ? close : null,
  addEventListener: () => {}};
const toggle = {focus: () => focused++, setAttribute: (key, value) => { toggle[key] = value; },
  addEventListener: (name, fn) => { if (name === 'click') toggle.click = fn; }};
let moved = false;
root.querySelectorAll = () => [];
root.querySelector = selector => selector === '.fleet-compare' ? panel :
  selector === '[data-open-compare]' ? toggle :
  selector === '.fleet-finder' ? {insertAdjacentElement: () => { moved = true; }} : null;
context.renderFleet(snapshot, {});
assert.equal(panel.hidden, true);
assert.equal(moved, true);
toggle.click();
assert.equal(panel.hidden, false);
assert.equal(toggle['aria-expanded'], 'true');
close.click();
assert.equal(panel.hidden, true);
assert.equal(toggle['aria-expanded'], 'false');
console.log('Fleet finder evidence, ties, unknowns, and spoiler isolation passed');
