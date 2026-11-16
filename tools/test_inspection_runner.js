const fs = require('fs');
const path = require('path');
const vm = require('vm');

const indexPath = path.join(__dirname, '../index.html');
const html = fs.readFileSync(indexPath, 'utf-8');

// Extract the main script content from index.html
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>[\s\r\n]*<\/body>/i);
if (!scriptMatch) {
  console.error("Could not extract script from index.html");
  process.exit(1);
}
const scriptContent = scriptMatch[1];

function createMockElement(id) {
  return {
    id: id,
    textContent: '',
    className: '',
    classList: {
      add: function() {},
      remove: function() {},
      contains: function() { return false; }
    },
    style: {
      setProperty: function() {}
    },
    checked: false,
    value: '',
    disabled: false,
    addEventListener: function() {},
    setAttribute: function() {},
    getAttribute: function() { return ''; }
  };
}

function runScenario(tabSequence, action = 'QUICK_APPROVE', options = {}) {
  const elements = {};
  function getElement(id) {
    if (!elements[id]) elements[id] = createMockElement(id);
    return elements[id];
  }

  const mockLocation = { search: '?token=PHD2026', href: 'http://localhost/' };
  const mockWindow = {
    addEventListener: function() {},
    innerWidth: 1920,
    innerHeight: 1080,
    location: mockLocation
  };

  const sandbox = {
    window: mockWindow,
    location: mockLocation,
    URLSearchParams: URLSearchParams,
    document: {
      getElementById: getElement,
      querySelectorAll: function() { return []; },
      addEventListener: function() {},
      body: createMockElement('body')
    },
    localStorage: {
      getItem: function() { return null; },
      setItem: function() {},
      removeItem: function() {}
    },
    sessionStorage: {
      getItem: function(k) { if (k === 'tum_auth_validated') return '1'; return null; },
      setItem: function() {},
      removeItem: function() {}
    },
    navigator: {
      clipboard: {
        writeText: function() { return Promise.resolve(); }
      }
    },
    fetch: function() { return Promise.resolve({ ok: true, json: () => Promise.resolve({}) }); },
    setInterval: function() { return 1; },
    clearInterval: function() {},
    setTimeout: function(fn) { fn(); return 1; },
    clearTimeout: function() {},
    Date: Date,
    Math: Math,
    console: console,
    Blob: function(parts, opts) { this.parts = parts; this.opts = opts; },
    URL: { createObjectURL: function() { return 'blob:mock'; }, revokeObjectURL: function() {} }
  };

  const context = vm.createContext(sandbox);
  vm.runInContext(scriptContent, context);

  // Initialize session
  context.initSession();

  // Optional: run Case 1 sequence
  if (options.case1Sequence !== undefined) {
    context.launchCase1();
    for (const tab of options.case1Sequence) {
      context.switchCase1Tab(tab);
    }
    if (options.case1Action === 'REJECT') {
      context.confirmCase1Discrepancy();
    } else {
      context.approveCase1();
    }
  }

  // Launch Case 2
  context.launchCase2();

  // Execute tab sequence (e.g. [2] or [3] or [2, 3])
  for (const tab of tabSequence) {
    context.switchCase2Tab(tab);
  }

  if (options.case2TimedOut) {
    const sObj = vm.runInContext('state', context);
    sObj.session.s1b_floor.case2TimedOut = true;
  }

  // Finish Case 2
  if (action === 'QUICK_APPROVE') {
    context.quickApproveCase2();
  } else {
    context.escalateCase2();
  }

  // Optional: inject legacy floor state to test backwards compatibility
  if (options.legacyFloorState) {
    const sObj = vm.runInContext('state', context);
    sObj.session.s1b_floor = Object.assign({}, options.legacyFloorState);
    context.renderScorecard();
  }

  const kpiCase1Metric = getElement('kpiCase1Metric').textContent;
  const kpiMetric = getElement('kpiCase2Metric').textContent;
  const stateObj = vm.runInContext('state', context);
  const s1b = stateObj.session.s1b_floor;

  // Render Screen 3 under Arm 3 for recall card verification
  stateObj.session.arm = options.arm || 3;
  context.renderScreen3();
  const arm3BenchmarkQuotaStatus = getElement('arm3BenchmarkQuotaStatus').textContent;
  const arm3BenchmarkClass = getElement('arm3BenchmarkQuotaStatus').className;

  // Capture CSV and JSON content
  let capturedCsv = '';
  let capturedJson = '';
  sandbox.document.createElement = function(tag) {
    const el = createMockElement(tag);
    if (tag === 'a') {
      el.click = function() {};
    }
    return el;
  };
  sandbox.Blob = function(parts, opts) {
    if (opts && opts.type && opts.type.includes('csv')) {
      capturedCsv = parts.join('');
    }
    if (opts && opts.type && opts.type.includes('json')) {
      capturedJson = parts.join('');
    }
  };
  context.exportParticipantCsv();
  context.exportParticipantJson();

  return {
    kpiCase1Metric: kpiCase1Metric,
    kpiMetric: kpiMetric,
    arm3BenchmarkQuotaStatus: arm3BenchmarkQuotaStatus,
    arm3BenchmarkClass: arm3BenchmarkClass,
    s1b: s1b,
    csv: capturedCsv,
    jsonExport: capturedJson,
    sessionJson: JSON.parse(JSON.stringify(stateObj.session))
  };
}

module.exports = { runScenario };
