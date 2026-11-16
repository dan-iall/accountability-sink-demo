const fs = require('fs');
const path = require('path');
const vm = require('vm');

const adminPath = path.join(__dirname, '../admin.html');
const adminHtml = fs.readFileSync(adminPath, 'utf8');

const scriptMatch = adminHtml.match(/<script>([\s\S]*?)<\/script>[\s\r\n]*<\/body>/i);
if (!scriptMatch) {
  console.error("Could not extract script from admin.html");
  process.exit(1);
}
const adminScript = scriptMatch[1];

function createMockElement(id) {
  return {
    id: id,
    textContent: '',
    innerHTML: '',
    value: '',
    checked: false,
    disabled: false,
    className: '',
    classList: {
      _classes: new Set(),
      add: function(...cls) { cls.forEach(c => this._classes.add(c)); },
      remove: function(...cls) { cls.forEach(c => this._classes.delete(c)); },
      contains: function(c) { return this._classes.has(c); }
    },
    style: { setProperty: function() {} },
    querySelectorAll: function() { return []; },
    querySelector: function() { return null; },
    addEventListener: function(evt, fn) {
      if (!this._listeners) this._listeners = {};
      this._listeners[evt] = fn;
    },
    click: function() {
      if (this._listeners && this._listeners['click']) {
        this._listeners['click']();
      }
    },
    setAttribute: function() {},
    getAttribute: function() { return ''; },
    appendChild: function(child) {
      if (!this.children) this.children = [];
      this.children.push(child);
    },
    removeChild: function(child) {
      if (this.children) {
        const idx = this.children.indexOf(child);
        if (idx !== -1) this.children.splice(idx, 1);
      }
    }
  };
}

function createAdminEnvironment(initialStorage = {}) {
  const elements = {};
  function getElement(id) {
    if (!elements[id]) elements[id] = createMockElement(id);
    return elements[id];
  }

  const localStorageStore = Object.assign({}, initialStorage);
  const mockLocalStorage = {
    getItem: function(key) { return localStorageStore.hasOwnProperty(key) ? localStorageStore[key] : null; },
    setItem: function(key, val) { localStorageStore[key] = String(val); },
    removeItem: function(key) { delete localStorageStore[key]; },
    clear: function() { Object.keys(localStorageStore).forEach(k => delete localStorageStore[k]); }
  };

  const sessionStorageStore = { tum_auth_validated: '1' };
  const mockSessionStorage = {
    getItem: function(key) { return sessionStorageStore[key] || null; },
    setItem: function(key, val) { sessionStorageStore[key] = String(val); },
    removeItem: function(key) { delete sessionStorageStore[key]; }
  };

  const mockDocument = {
    body: createMockElement('body'),
    getElementById: getElement,
    querySelector: function(sel) {
      if (sel.startsWith('#')) return getElement(sel.slice(1));
      if (sel.includes('name="armSelect"')) return { value: 'auto' };
      if (sel.includes('name="speedSelect"')) return { value: '1' };
      return createMockElement('dummy');
    },
    querySelectorAll: function() { return []; },
    createElement: function(tag) { return createMockElement(tag); },
    addEventListener: function() {}
  };

  const mockWindow = {
    location: { origin: 'http://localhost:8000', pathname: '/admin.html', search: '?access=tum2026' },
    localStorage: mockLocalStorage,
    sessionStorage: mockSessionStorage,
    document: mockDocument,
    navigator: { clipboard: { writeText: function() { return Promise.resolve(); } } },
    URLSearchParams: URLSearchParams,
    btoa: function(str) { return Buffer.from(str, 'binary').toString('base64'); },
    atob: function(b64) { return Buffer.from(b64, 'base64').toString('binary'); }
  };

  const sandbox = {
    window: mockWindow,
    document: mockDocument,
    localStorage: mockLocalStorage,
    sessionStorage: mockSessionStorage,
    URLSearchParams: URLSearchParams,
    btoa: mockWindow.btoa,
    atob: mockWindow.atob,
    Buffer: Buffer,
    console: console,
    Date: Date,
    Math: Math,
    parseInt: parseInt,
    parseFloat: parseFloat,
    isNaN: isNaN,
    isFinite: isFinite,
    Number: Number,
    String: String,
    Array: Array,
    Object: Object,
    JSON: JSON,
    Set: Set,
    encodeURIComponent: encodeURIComponent,
    decodeURIComponent: decodeURIComponent,
    escape: escape,
    unescape: unescape,
    Blob: function(parts, opts) { this.parts = parts; this.opts = opts; },
    URL: { createObjectURL: () => 'blob:mock', revokeObjectURL: () => {} }
  };

  const context = vm.createContext(sandbox);
  vm.runInContext(adminScript, context);

  return { context, sandbox, elements, localStorageStore };
}

module.exports = { createAdminEnvironment };
