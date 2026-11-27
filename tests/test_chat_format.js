const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Extract appendInlineText + renderFormattedMessage from static/app.js in an isolated DOM mock.
const appSrc = fs.readFileSync(path.join(__dirname, '..', 'static', 'app.js'), 'utf8');
const start = appSrc.indexOf('function appendInlineText(');
const end = appSrc.indexOf('function addMessage(');
assert.ok(start > 0 && end > start, 'Expected formatter functions in static/app.js');
const snippet = appSrc.slice(start, end);

class MockNode {
  constructor(tag) {
    this.tag = tag;
    this.className = '';
    this.children = [];
    this._text = '';
  }
  get textContent() {
    return this._text + this.children.map(c => c.textContent).join('');
  }
  set textContent(v) {
    this._text = String(v ?? '');
    this.children = [];
  }
  appendChild(child) {
    this.children.push(child);
    return child;
  }
}

const document = {
  createElement: tag => new MockNode(tag),
  createTextNode: text => {
    const n = new MockNode('#text');
    n._text = String(text ?? '');
    return n;
  },
};

const ctx = vm.createContext({document});
vm.runInContext(snippet, ctx);

// 1. Structured guide card renders title, bullet list with bold labels, inline **bold**, and muted Check footer.
const card = document.createElement('div');
ctx.renderFormattedMessage(
  card,
  'Prosperity (Tradition Tree)\n- Your save: Not adopted yet (**1/7** slots).\n- Key picks: -10% cost & **+5% job output**.\nCheck: Verify prerequisites in Traditions & Relics.',
  'assistant'
);
assert.equal(card.children.length, 3, 'Expected title + ul + check note');
assert.equal(card.children[0].className, 'msg-title');
assert.equal(card.children[0].textContent, 'Prosperity (Tradition Tree)');
assert.equal(card.children[1].tag, 'ul');
assert.equal(card.children[1].className, 'msg-list');
assert.equal(card.children[1].children.length, 2);
const li0 = card.children[1].children[0];
assert.equal(li0.children[0].tag, 'strong');
assert.equal(li0.children[0].className, 'msg-label');
assert.equal(li0.children[0].textContent, 'Your save: ');
assert.ok(li0.children.some(c => c.tag === 'strong' && c.textContent === '1/7'));
assert.equal(card.children[2].className, 'msg-note');
assert.equal(card.children[2].textContent, 'Check: Verify prerequisites in Traditions & Relics.');

// 2. User and warning messages stay raw plain text (never parsed as bullets or bold).
const userMsg = document.createElement('div');
ctx.renderFormattedMessage(userMsg, '- **test** <script>alert(1)</script>', 'user');
assert.equal(userMsg.children.length, 0);
assert.equal(userMsg.textContent, '- **test** <script>alert(1)</script>');

const warnMsg = document.createElement('div');
ctx.renderFormattedMessage(warnMsg, '- **Warning:** raw error', 'warning');
assert.equal(warnMsg.children.length, 0);
assert.equal(warnMsg.textContent, '- **Warning:** raw error');

// 3. XSS payload inside assistant text stays literal text nodes (zero script/img elements created).
const xssBox = document.createElement('div');
ctx.renderFormattedMessage(
  xssBox,
  'Title <img src=x onerror=alert(1)>\n- Alert: **<script>evil()</script>**',
  'assistant'
);
function walkTags(node, out = []) {
  out.push(node.tag);
  for (const child of node.children) walkTags(child, out);
  return out;
}
const tags = walkTags(xssBox);
assert.ok(!tags.includes('img') && !tags.includes('script'), `Unexpected HTML tags created: ${tags}`);
assert.ok(xssBox.textContent.includes('<img src=x onerror=alert(1)>'));
assert.ok(xssBox.textContent.includes('<script>evil()</script>'));

console.log('Chat formatted message & XSS safety tests passed');
