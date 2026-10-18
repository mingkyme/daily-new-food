import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import vm from 'node:vm';

const source = new URL('./clarity-client.js', import.meta.url);
function run(id = '', saved = null) {
  const requests = [], cookies = [], listeners = {};
  const buttons = Object.fromEntries(['grant', 'deny'].map(k => [k, { addEventListener: (_, fn) => listeners[k] = fn }]));
  const status = { textContent: '' };
  const panel = { dataset: { clarityProjectId: id }, querySelector: s => s === '[role="status"]' ? status : buttons[s.includes('grant') ? 'grant' : 'deny'] };
  const storage = new Map(saved ? [['food-clarity-consent-v1', saved]] : []);
  const document = { querySelector: () => panel, createElement: () => ({ remove() { this.removed = true; } }), head: { append: s => requests.push(s) }, set cookie(v) { cookies.push(v); } };
  let reloads = 0;
  const window = { location: { hostname: 'food.mingky.me', search: '', hash: '', reload: () => reloads++ }, addEventListener: (k, fn) => listeners[k] = fn, localStorage: { getItem: k => storage.get(k), setItem: (k,v) => storage.set(k,v) } };
  assert.ok(existsSync(source), 'Clarity optional client must exist');
  vm.runInNewContext(readFileSync(source, 'utf8'), { window, document, Date });
  return { requests, cookies, listeners, window, storage, status, reloads: () => reloads };
}
test('opt-in loads once only after explicit grant with ads denied', () => {
  const r = run('testonly'); // Mock-only ID; no real network in this VM.
  assert.equal(r.requests.length, 0);
  assert.equal(r.window.clarity, undefined);
  assert.equal(typeof r.listeners.grant, 'function');
  r.listeners.grant();
  r.listeners.grant();
  assert.equal(r.requests.length, 1);
  assert.equal(r.requests[0].src, 'https://www.clarity.ms/tag/testonly');
  assert.deepEqual(JSON.parse(JSON.stringify(r.window.clarity.q[0])), ['consentv2', { analytics_Storage: 'granted', ad_Storage: 'denied' }]);
});
test('deny sends no requests; revoke denies both categories, clears cookies and reloads', () => {
  const r = run('testonly');
  assert.equal(typeof r.listeners.deny, 'function');
  r.listeners.deny();
  assert.equal(r.requests.length, 0);
  r.listeners.grant();
  r.listeners.deny();
  assert.deepEqual(JSON.parse(JSON.stringify(r.window.clarity.q.at(-1))), ['consentv2', { analytics_Storage: 'denied', ad_Storage: 'denied' }]);
  assert.ok(r.cookies.some(v => v.startsWith('_clck=;')));
  assert.ok(r.cookies.some(v => v.startsWith('_clsk=;')));
  assert.equal(r.requests[0].removed, true);
  assert.equal(r.reloads(), 1);
  assert.equal(JSON.parse(r.storage.get('food-clarity-consent-v1')).granted, false);
});
test('saved fresh consent loads, stale or denied consent does not', () => {
  assert.equal(run('testonly', JSON.stringify({ granted: true, at: Date.now() })).requests.length, 1);
  for (const saved of ['garbage', JSON.stringify({ granted: false, at: Date.now() }), JSON.stringify({ granted: true, at: 1 })]) {
    assert.equal(run('testonly', saved).requests.length, 0);
  }
});
test('saved consent is not silently renewed; other tabs can revoke it', () => {
  const saved = JSON.stringify({ granted: true, at: Date.now() - 1000 });
  const r = run('testonly', saved);
  assert.equal(r.storage.get('food-clarity-consent-v1'), saved);
  r.storage.delete('food-clarity-consent-v1');
  r.listeners.storage({ key: 'food-clarity-consent-v1' });
  assert.equal(r.reloads(), 1);
});
test('shared layout wires conditional UI and masks all body content', () => {
  const layout = readFileSync(new URL('../layouts/BaseLayout.astro', import.meta.url), 'utf8');
  assert.match(layout, /<ClarityConsent\s*\/>/);
  assert.match(layout, /<body data-clarity-mask="True">/);
});
test('cross-tab denial does not rewrite storage and cause an event loop', () => {
  const r = run('testonly');
  const denied = JSON.stringify({ granted: false, at: 1 });
  r.storage.set('food-clarity-consent-v1', denied);
  r.listeners.storage({ key: 'food-clarity-consent-v1' });
  assert.equal(r.storage.get('food-clarity-consent-v1'), denied);
});
test('failed consent write removes old grant rather than resurrecting it on reload', () => {
  const r = run('testonly', JSON.stringify({ granted: true, at: Date.now() }));
  r.window.localStorage.setItem = () => { throw new Error('quota'); };
  r.window.localStorage.removeItem = k => r.storage.delete(k);
  r.listeners.deny();
  assert.equal(r.storage.has('food-clarity-consent-v1'), false);
  assert.equal(r.reloads(), 1);
});
test('missing configuration is completely inert even with saved consent', () => {
  const result = run('', JSON.stringify({ granted: true, at: Date.now() }));
  assert.equal(result.requests.length, 0);
  assert.equal(result.cookies.length, 0);
  assert.equal(result.window.clarity, undefined);
  assert.deepEqual(Object.keys(result.listeners), []);
});
