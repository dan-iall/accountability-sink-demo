// workflow_challenger_harness.js - Part 1: Mock DOM and VM environment
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const indexPath = path.join(__dirname, '../index.html');
const html = fs.readFileSync(indexPath, 'utf-8');

const scriptMatch = html.match(/<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>[\s\r\n]*<\/body>/i);
if (!scriptMatch) {
  console.error("Could not extract inline script from index.html");
  process.exit(1);
}
const scriptContent = scriptMatch[1];

function getStaticElementInfo(id) {
  const re = new RegExp('<([a-zA-Z0-9]+)[^>]+id=[\"\']' + id + '[\"\'][^>]*>', 'i');
  const m = html.match(re);
  if (!m) return { classes: '', text: '' };
  const classMatch = m[0].match(/class=[\"\']([^\"\']*)[\"\']/i);
  const classes = classMatch ? classMatch[1] : '';
  const tag = m[1];
  const start = m.index + m[0].length;
  const end = html.indexOf('</' + tag + '>', start);
  const text = (end > start) ? html.substring(start, end).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim() : '';
  return { classes, text };
}

function createMockElement(id) {
  const classes = new Set();
  const staticInfo = getStaticElementInfo(id);
  if (staticInfo.classes) {
    staticInfo.classes.split(/\s+/).filter(Boolean).forEach(c => classes.add(c));
  }
  return {
    id: id,
    textContent: staticInfo.text || '',
    innerHTML: '',
    value: '',
    checked: false,
    disabled: false,
    style: {
      width: '',
      filter: '',
      setProperty: function(k, v) { this[k] = v; }
    },
    classList: {
      add: function(...names) { names.forEach(n => classes.add(n)); },
      remove: function(...names) { names.forEach(n => classes.delete(n)); },
      contains: function(name) { return classes.has(name); },
      toggle: function(name, force) {
        if (force === undefined) {
          if (classes.has(name)) classes.delete(name); else classes.add(name);
        } else if (force) classes.add(name);
        else classes.delete(name);
      }
    },
    get className() {
      return Array.from(classes).join(' ');
    },
    set className(val) {
      classes.clear();
      if (val && typeof val === 'string') {
        val.split(/\s+/).filter(Boolean).forEach(c => classes.add(c));
      }
    },
    _attributes: {},
    addEventListener: function(evt, fn) {
      if (!this._listeners) this._listeners = {};
      this._listeners[evt] = fn;
    },
    removeEventListener: function() {},
    setAttribute: function(k, v) {
      if (!this._attributes) this._attributes = {};
      this._attributes[k] = String(v);
    },
    getAttribute: function(k) {
      return (this._attributes && this._attributes[k] !== undefined) ? this._attributes[k] : (k === 'id' ? this.id : '');
    },
    closest: function(sel) {
      if (sel && sel.includes('[data-aoi]')) {
        return this.getAttribute('data-aoi') ? this : null;
      }
      return this;
    },
    getBoundingClientRect: function() {
      return { x: 50, y: 50, width: 200, height: 100, top: 50, left: 50, right: 250, bottom: 150 };
    },
    offsetParent: {}
  };
}

function createHarnessContext(initialTime = 1000000) {
  let currentTime = initialTime;
  let perfTime = 0.0;
  const elements = {};

  function getElement(id) {
    if (!elements[id]) {
      elements[id] = createMockElement(id);
    }
    return elements[id];
  }

  const mockLocation = { search: '', href: 'http://localhost/' };
  const mockWindow = {
    addEventListener: function() {},
    innerWidth: 1920,
    innerHeight: 1080,
    location: mockLocation
  };

  const timerCallbacks = [];

  class MockDate extends Date {
    constructor(...args) {
      if (args.length === 0) super(currentTime);
      else super(...args);
    }
    static now() {
      return currentTime;
    }
  }

  const sandbox = {
    window: mockWindow,
    location: mockLocation,
    URLSearchParams: URLSearchParams,
    document: {
      getElementById: getElement,
      _listeners: {},
      querySelectorAll: function(sel) {
        if (sel === '[data-aoi]') {
          return Object.values(elements).filter(el => el.getAttribute && el.getAttribute('data-aoi'));
        }
        return [];
      },
      addEventListener: function(evt, fn) {
        if (!this._listeners) this._listeners = {};
        if (!this._listeners[evt]) this._listeners[evt] = [];
        this._listeners[evt].push(fn);
      },
      dispatchEvent: function(event) {
        const type = event.type || 'click';
        if (this._listeners && this._listeners[type]) {
          this._listeners[type].forEach(fn => fn(event));
        }
      },
      body: createMockElement('body')
    },
    localStorage: {
      store: {},
      getItem: function(k) { return this.store[k] !== undefined ? this.store[k] : null; },
      setItem: function(k, v) { this.store[k] = String(v); },
      removeItem: function(k) { delete this.store[k]; }
    },
    sessionStorage: {
      store: { 'study_auth_validated': '1' },
      getItem: function(k) { return this.store[k] !== undefined ? this.store[k] : null; },
      setItem: function(k, v) { this.store[k] = String(v); }
    },
    navigator: {
      clipboard: { writeText: function() { return Promise.resolve(); } }
    },
    fetch: function() { return Promise.resolve({ ok: true, json: () => Promise.resolve({}) }); },
    setInterval: function(fn, ms) {
      const id = timerCallbacks.length + 1;
      timerCallbacks.push({ id, fn, ms, active: true });
      return id;
    },
    clearInterval: function(id) {
      const t = timerCallbacks.find(item => item.id === id);
      if (t) t.active = false;
    },
    setTimeout: function(fn) { fn(); return 1; },
    clearTimeout: function() {},
    Date: MockDate,
    performance: {
      now: function() { return perfTime; }
    },
    Math: Math,
    console: console,
    Blob: function(parts, opts) { this.parts = parts; this.opts = opts; },
    URL: { createObjectURL: () => 'blob:mock', revokeObjectURL: () => {} }
  };

  const context = vm.createContext(sandbox);
  vm.runInContext(scriptContent, context);

  return {
    context,
    sandbox,
    getElement,
    advanceTime: function(ms) {
      currentTime += ms;
      perfTime += ms;
    },
    tickIntervals: function(count = 1) {
      for (let i = 0; i < count; i++) {
        for (const t of timerCallbacks) {
          if (t.active) t.fn();
        }
      }
    }
  };
}

module.exports = { createHarnessContext, createMockElement };

// Part 2: Workflow Runners for S1, S1B, and S2A
function runS1NavigationScenario({ arm = 3, navigationSteps = [], timeDwellPerStepMs = 250 }) {
  const h = createHarnessContext();
  const state = vm.runInContext('state', h.context);
  h.context.initSession();
  state.session.arm = arm;
  h.context.renderS1Step();

  const stepHistory = [state.currentS1Step];
  for (const target of navigationSteps) {
    h.advanceTime(timeDwellPerStepMs);
    h.context.nextS1Step(target);
    stepHistory.push(state.currentS1Step);
  }

  const pill6 = h.getElement('s1PillStep6');
  const btnStep5Next = h.getElement('btnStep5Next');
  const btnS1Complete = h.getElement('btnS1Complete');

  return {
    arm,
    stepHistory,
    finalStep: state.currentS1Step,
    dwells: JSON.parse(JSON.stringify(state.session.s1_onboarding || {})),
    pill6Hidden: pill6.classList.contains('hidden'),
    btnStep5NextHidden: btnStep5Next.classList.contains('hidden'),
    btnS1CompleteHidden: btnS1Complete.classList.contains('hidden')
  };
}

function runS1BCase2Scenario({ tabSequence = [], action = 'QUICK_APPROVE', tabDwellsMs = {} }) {
  const h = createHarnessContext();
  const state = vm.runInContext('state', h.context);
  h.context.initSession();
  state.session.arm = 3;
  h.context.showScreen('screenS1B');
  h.context.launchCase2();

  for (const tab of tabSequence) {
    const dwell = tabDwellsMs[tab] || 300;
    h.advanceTime(dwell);
    h.context.switchCase2Tab(tab);
  }

  h.advanceTime(500);
  if (action === 'QUICK_APPROVE') {
    h.context.quickApproveCase2();
  } else {
    h.context.escalateCase2();
  }

  const m1 = h.getElement('kpiCase1Metric').textContent;
  const m2 = h.getElement('kpiCase2Metric').textContent;
  const s1b = state.session.s1b_floor;

  return {
    action,
    m1,
    m2,
    case2ActionRecorded: s1b.case2Action,
    visitedTabs: s1b.case2PagesVisited,
    unopenedTabs: s1b.case2PagesUnopened,
    visitedCount: s1b.case2PagesVisitedCount,
    totalDwellSec: s1b.case2TotalDwellSec
  };
}

function runS2APolicyScenario({ preClickAttempt = true, selectedOption = null }) {
  const h = createHarnessContext();
  const state = vm.runInContext('state', h.context);
  h.context.initSession();
  h.context.showScreen('screenS2A');
  h.context.renderScreen2A();

  const radio1 = h.getElement('radioSla1');
  const radio2 = h.getElement('radioSla2');
  const radio3 = h.getElement('radioSla3');
  const btnLock = h.getElement('btnLockShift');
  const emptyNotice = h.getElement('s2aProjEmptyNotice');
  const metricsGrid = h.getElement('s2aProjMetrics');
  const lblBonus = h.getElement('lblProjBonus');

  const initialState = {
    radio1Checked: radio1.checked,
    radio2Checked: radio2.checked,
    radio3Checked: radio3.checked,
    selectedSlaSec: state.s2a.selectedSlaSec,
    btnDisabled: btnLock.disabled,
    btnHasPointerEventsNone: btnLock.className.includes('pointer-events-none'),
    btnHasOpacity50: btnLock.className.includes('opacity-50'),
    emptyNoticeHidden: emptyNotice.classList.contains('hidden'),
    metricsGridHidden: metricsGrid.classList.contains('hidden'),
    lblBonusText: lblBonus.textContent
  };

  let preLockAttemptRecorded = false;
  if (preClickAttempt) {
    h.context.lockSlaPolicy();
    preLockAttemptRecorded = (state.session.initialSlaPreferenceSec !== undefined);
  }

  let postSelectState = null;
  if (selectedOption !== null) {
    h.context.selectSlaOption(selectedOption);
    const radioSelected = h.getElement(`radioSla${selectedOption}`);
    const lblProjSla = h.getElement('lblProjSla');
    const lblProjCases = h.getElement('lblProjCases');
    const lblProjPts = h.getElement('lblProjPts');
    const lblProjBonusPost = h.getElement('lblProjBonus');

    postSelectState = {
      radioChecked: radioSelected.checked,
      selectedSlaSec: state.s2a.selectedSlaSec,
      selectedArchetype: state.s2a.selectedArchetype,
      btnDisabled: btnLock.disabled,
      btnCursorPointer: btnLock.className.includes('cursor-pointer'),
      lblProjSlaText: lblProjSla.textContent,
      lblProjCasesText: lblProjCases.textContent,
      lblProjPtsText: lblProjPts.textContent,
      lblProjBonusText: lblProjBonusPost.textContent
    };

    h.context.lockSlaPolicy();
  }

  return {
    initialState,
    preLockAttemptRecorded,
    postSelectState,
    sessionInitialSlaSec: state.session.initialSlaPreferenceSec !== undefined ? state.session.initialSlaPreferenceSec : null,
    s2aPolicyRecorded: JSON.parse(JSON.stringify(state.session.s2a_policy || {}))
  };
}

// Part 3: Workflow Runners for S2B (Shift 2), Shift 3, and Screen 4
function runS2BShift2Scenario({ directive = 'A' }) {
  const h = createHarnessContext();
  const state = vm.runInContext('state', h.context);
  h.context.initSession();
  state.session.s2b_shifts = { shift1Pts: 360, shift1Cases: 36 };

  // Trigger directive
  h.context.chooseDirective(directive);

  // Complete Shift 2 by advancing simulated performance time to finish interval
  // In index.html: halfSec = totalSec * 0.5. At 1x speed, halfSec = 12.5s.
  // Advance time by 13.0s (13000ms) and tick intervals:
  h.advanceTime(13000);
  h.tickIntervals(5);

  const lblDir = h.getElement('lblShift2DirectiveLogged').textContent;
  const lblPts = h.getElement('lblShift2PtsAwarded').textContent;
  const lblCum = h.getElement('lblShift2CumulativePts').textContent;
  const excStatus = h.getElement('shift2ExceptionStatus');
  const excStatusHidden = excStatus.classList.contains('hidden');
  const excStatusText = excStatus.textContent || '';
  const modalShift2Done = h.getElement('modalShift2Done');

  return {
    directive,
    shift2Pts: state.session.s2b_shifts.shift2Pts,
    shift2DirectiveLogged: state.session.s2b_shifts.shift2Directive,
    lblDir,
    lblPts,
    lblCum,
    excStatusHidden,
    excStatusText,
    modalDoneHidden: modalShift2Done.classList.contains('hidden'),
    casesCleared: state.s2b.casesCleared
  };
}

function runShift3CounterScenario() {
  const h = createHarnessContext();
  const state = vm.runInContext('state', h.context);
  h.context.initSession();
  state.session.s2b_shifts = { shift1Pts: 360, shift2Pts: 360 };

  h.context.startShift3();

  const casesEl = h.getElement('hudCasesCleared');
  const progEl = h.getElement('s2bProgress');
  const initialText = casesEl.textContent;
  const initialWidth = progEl.style.width;

  // Track counter text and progress width at various time increments up to crash at 75%
  // totalSec = 25.0s. 75% is 18.75s (18750ms).
  const snapshots = [];
  const testPointsSec = [2.0, 5.0, 10.0, 15.0, 18.0, 19.0];

  let elapsedSoFar = 0;
  for (const t of testPointsSec) {
    const delta = (t * 1000) - elapsedSoFar;
    h.advanceTime(delta);
    elapsedSoFar = t * 1000;
    h.tickIntervals(1);
    snapshots.push({
      timeSec: t,
      counterText: casesEl.textContent,
      casesCleared: state.s2b.casesCleared,
      progressWidth: progEl.style.width
    });
  }

  const modalCrash = h.getElement('modalCrash');
  const b2 = h.getElement('badgeStation2');
  const qStatus = h.getElement('st2QueueStatus');

  return {
    initialText,
    initialWidth,
    snapshots,
    modalCrashHidden: modalCrash.classList.contains('hidden'),
    st2BadgeText: b2.textContent,
    st2BadgeClass: b2.className,
    st2QueueStatus: qStatus.textContent,
    preCrashPts: state.session.s2b_shifts.shift3PreCrashPts,
    provisionalHoldPts: state.session.s2b_shifts.provisionalHoldPts
  };
}

function runScreen4DisciplinaryScenario({ directive = 'A', task2Selection = null, task4Selection = null }) {
  const h = createHarnessContext();
  const state = vm.runInContext('state', h.context);
  h.context.initSession();

  // Set up shifts state reflecting directive A or B
  const s2Directive = directive === 'A' ? 'A_TRUST_AI' : 'B_SLOW_FLOOR';
  const s2Pts = directive === 'A' ? 360 : 320;
  state.session.s2b_shifts = {
    shift1Pts: 360,
    shift2Directive: s2Directive,
    shift2Pts: s2Pts,
    shift3PreCrashPts: 270,
    provisionalHoldPts: -300
  };

  h.context.showScreen('screenS4');
  h.context.renderScreen4();

  const s4Hdr = h.getElement('s4ManagerPtsHeader');
  const hdrLiveScore = h.getElement('hdrLiveScore');
  const sb1 = h.getElement('t2Opt1SubBadge');
  const sb2 = h.getElement('t2Opt2SubBadge');

  const unselectedState = {
    headerText: s4Hdr.textContent,
    liveScoreText: hdrLiveScore.textContent,
    opt1SubBadgeText: sb1.textContent,
    opt2SubBadgeText: sb2.textContent
  };

  let postTask2State = null;
  if (task2Selection !== null) {
    h.context.selectTask2Fork(task2Selection);
    postTask2State = {
      headerText: s4Hdr.textContent,
      liveScoreText: hdrLiveScore.textContent
    };
  }

  let postTask4State = null;
  if (task4Selection !== null) {
    h.context.selectTask4Reform(task4Selection);
    postTask4State = {
      headerText: s4Hdr.textContent,
      liveScoreText: hdrLiveScore.textContent
    };
  }

  return {
    directive,
    unselectedState,
    postTask2State,
    postTask4State
  };
}

module.exports = {
  createHarnessContext,
  createMockElement,
  runS1NavigationScenario,
  runS1BCase2Scenario,
  runS2APolicyScenario,
  runS2BShift2Scenario,
  runShift3CounterScenario,
  runScreen4DisciplinaryScenario
};
