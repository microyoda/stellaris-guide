const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor(tag = 'div') {
    this.tag = tag; this.children = []; this.hidden = false; this.textContent = '';
    this.listeners = {}; this.classList = {toggle() {}};
  }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children = items; }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  setAttribute(name, value) { this[name] = value; }
}
const elements = new Map();
const document = {
  getElementById(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },
  createElement(tag) { return new Element(tag); },
  querySelectorAll() { return []; },
};
const context = {document, URLSearchParams, location: {search: ''}, encodeURIComponent, console};
vm.createContext(context);
const source = fs.readFileSync('static/tech-route.js', 'utf8');
vm.runInContext(source.split("$('target-search').addEventListener")[0], context);
const opportunity = {id: 'tech_far', name: 'Future Discovery', distance: 4, relation: 'direct', state: 'unmet',
  path: [{name: 'Root Discovery'}, {name: 'Next Discovery'}, {name: 'Later Discovery'},
    {name: 'Distant Discovery'}, {name: 'Future Discovery'}],
  description: 'In-game description.', benefit: 'Required for later research.',
  dlc: [{status: 'not_listed'}], draw_conditions_unverified: true};
context.renderFuture({steps: [{state: 'unmet'}], future_opportunities: [opportunity]});
assert.equal(elements.get('future-section').hidden, false);
const card = elements.get('future-list').children[0];
assert.equal(card.tag, 'button');
assert.match(card.children[1].children[3].textContent, /Root Discovery.*Future Discovery/);
assert.match(card.children[1].children[5].textContent, /Required DLC unconfirmed/);
assert.equal(card.children[0].children[0].src, '/api/tech-icon?id=tech_far');
assert.ok(card.listeners.click);
context.renderFuture({steps: [{state: 'unmet'}], future_opportunities: [{...opportunity, state: 'saved_option'}]});
assert.match(elements.get('future-list').children[0].children[1].children[5].textContent,
  /Observed in selected save/);
context.renderFuture({steps: [{state: 'unmet'}], future_opportunities: []});
assert.equal(elements.get('future-section').hidden, true);
console.log('Tech future route cards and empty state passed.');
