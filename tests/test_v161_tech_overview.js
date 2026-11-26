const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const techBranches = {innerHTML: '', querySelectorAll: () => []};
const context = {
  $: id => { assert.equal(id, 'tech-branches'); return techBranches; },
  esc: value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;'),
  number: value => String(value),
  encodeURIComponent,
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('static/tech-overview.js', 'utf8'), context);

context.renderTechOverview({technology: {
  branches: {engineering: {
    current_id: 'tech_current', current: 'Current', alternatives: ['Powered Exoskeletons'],
    alternative_ids: ['tech_powered_exoskeletons'], recommendation: 'Powered Exoskeletons',
  }},
  overview: {
    labels: {tech_current: 'Localized Current', tech_powered_exoskeletons: 'Localized Exoskeletons'},
    gates: {engineering: {status: 'unverified', count: 0, required: 0, display_count: 0}},
  },
}});
assert.match(techBranches.innerHTML, /Localized Exoskeletons/);
assert.match(techBranches.innerHTML, /research-option suggested/);
assert.match(techBranches.innerHTML, /aria-label="Explore route for Localized Exoskeletons"/);
assert.match(techBranches.innerHTML, /No base-game count needed · verify mods/);

context.renderTechOverview({technology: {branches: {}, overview: {}}});
assert.match(techBranches.innerHTML, /Tier rule unavailable/);
assert.match(techBranches.innerHTML, /No alternatives could be read/);
console.log('Tech overview success and missing-data cases passed');
