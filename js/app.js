/* ════════════════════════════════════════════════════════════════
   TITAN MERIDIAN CAPITAL — client portal application
   Auth (demo account, remember-me) · hash router · six views ·
   guided tutorial · save/update workspace · toasts · transitions.
   ════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';
  const D = window.TMC_DATA, C = window.TMC_CHARTS;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ────────────────────── icons ────────────────────── */
  const I = {
    overview: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/></svg>',
    performance: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M3.5 17.5 9 11.5l3.5 3.5 7.5-8"/><path d="M15.5 7h4.5v4.5"/></svg>',
    analytics: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><circle cx="12" cy="12" r="8.5"/><path d="M12 3.5V12l6 6"/></svg>',
    markets: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.7 2.4 4 5.4 4 8.5s-1.3 6.1-4 8.5c-2.7-2.4-4-5.4-4-8.5s1.3-6.1 4-8.5z"/></svg>',
    insights: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M5 4.5h11a2 2 0 0 1 2 2v11a2 2 0 0 0 2 2H7a2 2 0 0 1-2-2v-13z"/><path d="M8.5 8.5h5M8.5 12h5M8.5 15.5h3"/></svg>',
    settings: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M4 8h10M18 8h2M4 16h2M10 16h10"/><circle cx="16" cy="8" r="2.2"/><circle cx="8" cy="16" r="2.2"/></svg>',
    refresh: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 3.5V8h-4.5"/></svg>',
    save: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M5 4.5h11l3.5 3.5v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-13.5a1 1 0 0 1 1-1z"/><path d="M8 4.5V9h7V4.5M8 20v-6h8v6"/></svg>',
    help: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><circle cx="12" cy="12" r="8.5"/><path d="M9.6 9.3a2.5 2.5 0 1 1 3.4 2.9c-.8.4-1 1-1 1.8"/><circle cx="12" cy="16.8" r=".4" fill="currentColor"/></svg>',
    doc: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><path d="M6 3.5h8L19 8.5v12H6z"/><path d="M13.5 3.5V9H19"/></svg>',
    check: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.9"><path d="M4.5 12.5l5 5 10-11"/></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7"><circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5"/><circle cx="12" cy="7.8" r=".4" fill="currentColor"/></svg>',
    eye: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/></svg>',
    eyeOff: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 4l16 16M9.9 5.9A8.8 8.8 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-3 3.8M6 8.2A16 16 0 0 0 2.5 12S6 18.5 12 18.5a9 9 0 0 0 3.5-.7"/></svg>',
  };

  const fmtMoney = v => '$' + Math.round(v).toLocaleString('en-US');
  const fmtMoneyC = v => v >= 1e9 ? '$' + (v / 1e9).toFixed(1) + 'B' : v >= 1e6 ? '$' + (v / 1e6).toFixed(1) + 'M' : fmtMoney(v);
  const fmtPct = (v, dp) => (v > 0 ? '+' : '') + (v * 100).toFixed(dp == null ? 1 : dp) + '%';
  const fmtPctU = (v, dp) => (v * 100).toFixed(dp == null ? 1 : dp) + '%';
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const fmtD = d => ('0' + d.getDate()).slice(-2) + ' ' + MON[d.getMonth()] + ' ' + d.getFullYear();
  const cls = v => v >= 0 ? 'pos' : 'neg';

  /* ────────────────────── accounts / session ────────────────────── */
  const ACCOUNTS = [
    { id: 'demo', email: 'demo@titanmeridian.com', pass: 'meridian', name: 'Demo Family Office', first: '', legal: 'Demo Family Office Holdings, LLC', role: 'Limited Partner · Demo', initials: 'DF', demo: true },
    { id: 'principal', email: 'matthiusd@thetitanmarketsllc.com', pass: 'titan2026', name: 'Matthius D.', first: 'Matthius', legal: 'Titan Markets LLC', role: 'Founding Partner', initials: 'MD' },
  ];
  const SKEY = 'tmc.session';

  function getSession() {
    try {
      const raw = localStorage.getItem(SKEY) || sessionStorage.getItem(SKEY);
      if (!raw) return null;
      const s = JSON.parse(raw);
      return ACCOUNTS.find(a => a.id === s.id) ? s : null;
    } catch (e) { return null; }
  }
  function setSession(id, remember) {
    const raw = JSON.stringify({ id, remember, ts: Date.now() });
    if (remember) localStorage.setItem(SKEY, raw); else sessionStorage.setItem(SKEY, raw);
  }
  function clearSession() { localStorage.removeItem(SKEY); sessionStorage.removeItem(SKEY); }

  /* ────────────────────── state ────────────────────── */
  const State = {
    user: null,
    prefs: null,
    dirty: false,
    route: 'overview',
    live: null,          // jittered market snapshot (update feature)
    asOf: 'Data as of 03 Jul 2026 · 1:00 PM ET (early close)',
    chartRedraws: [],
    hmMode: 'sectors',
    hmSel: null,
    perfRange: 'ALL',
    newsFilter: 'ALL',
  };
  const DEFAULT_PREFS = {
    benchmark: 'B6040', netGross: 'net', edelivery: true, twofa: true,
    notifyPerf: true, notifyMacro: true, notifyOps: false,
    watchlist: ['SPX', 'US10Y', 'GC', 'EURUSD'],
    notes: '', tutorialDone: false, savedAt: null,
  };
  const BENCH = {
    B6040: { label: 'Global 60/40', series: () => D.B6040 },
    MACRO: { label: 'Macro Peer Index', series: () => D.MACRO },
    CASHP: { label: 'SOFR + 400bp', series: () => D.CASHP },
  };

  function prefsKey() { return 'tmc.prefs.' + State.user.id; }
  function loadPrefs() {
    try {
      const raw = localStorage.getItem(prefsKey());
      State.prefs = Object.assign({}, DEFAULT_PREFS, raw ? JSON.parse(raw) : {});
    } catch (e) { State.prefs = Object.assign({}, DEFAULT_PREFS); }
  }
  function persistPrefs(silent) {
    State.prefs.savedAt = Date.now();
    localStorage.setItem(prefsKey(), JSON.stringify(State.prefs));
    setDirty(false);
    if (!silent) {
      const t = new Date();
      toast('Workspace saved', 'Preferences, notes and watchlist stored on this device · ' +
        t.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }), 'good', I.check);
    }
  }
  function setDirty(v) {
    State.dirty = v;
    $('#save-dot').hidden = !v;
  }

  /* live market snapshot — refreshed by the Update action */
  function makeLive(jitter) {
    const r = D.rng(jitter ? Date.now() % 100000 : 4242);
    const j = (v, scale) => +(v + D.gauss(r) * scale).toFixed(2);
    return {
      dayBps: Math.round(34 + (jitter ? D.gauss(r) * 6 : 0)),
      indices: D.INDICES.map(x => ({ ...x, chg: j(x.chg, jitter ? 0.06 : 0), px: +(x.px * (1 + (jitter ? D.gauss(r) * 0.0006 : 0))).toFixed(x.px < 10 ? 4 : 2) })),
      watch: D.WATCH_UNIVERSE.map(x => ({ ...x, chg: j(x.chg, jitter ? 0.08 : 0), px: +(x.px * (1 + (jitter ? D.gauss(r) * 0.0006 : 0))).toFixed(x.px < 10 ? 4 : 2) })),
    };
  }

  /* ────────────────────── toasts / modal ────────────────────── */
  function toast(title, sub, kind, icon) {
    const root = $('#toast-root');
    const t = document.createElement('div');
    t.className = 'toast' + (kind ? ' ' + kind : '');
    t.innerHTML = `<span class="t-ic">${icon || I.info}</span><span class="t-msg"><b>${title}</b>${sub ? `<span>${sub}</span>` : ''}</span>`;
    root.appendChild(t);
    setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 380); }, 4200);
  }

  function openModal(html) {
    const root = $('#modal-root');
    root.innerHTML = `<div class="modal-veil"><div class="modal" role="dialog" aria-modal="true">
      <button class="modal-x" aria-label="Close">✕</button>${html}</div></div>`;
    const veil = $('.modal-veil', root);
    const close = () => { root.innerHTML = ''; document.removeEventListener('keydown', onKey); };
    const onKey = e => { if (e.key === 'Escape') close(); };
    veil.addEventListener('click', e => { if (e.target === veil) close(); });
    $('.modal-x', root).addEventListener('click', close);
    document.addEventListener('keydown', onKey);
    return close;
  }

  /* ────────────────────── reveal & count animations ────────────────────── */
  let observer = null;
  function bindReveals(scope) {
    if (!observer) {
      observer = new IntersectionObserver(entries => {
        entries.forEach(en => {
          if (en.isIntersecting) { en.target.classList.add('in'); observer.unobserve(en.target); }
        });
      }, { threshold: 0.1, rootMargin: '0px 0px -4% 0px' });
    }
    $$('.reveal', scope).forEach((el2, i) => {
      el2.style.transitionDelay = Math.min(i * 55, 440) + 'ms';
      observer.observe(el2);
    });
  }
  function runCountups(scope) {
    $$('[data-count]', scope).forEach(el2 => {
      const target = parseFloat(el2.dataset.count);
      const kind = el2.dataset.fmt || 'money';
      const dp = el2.dataset.dp ? +el2.dataset.dp : 1;
      const fmt = v => kind === 'money' ? fmtMoney(v)
        : kind === 'pct' ? fmtPct(v, dp)
        : kind === 'pctu' ? fmtPctU(v, dp)
        : kind === 'num' ? v.toFixed(dp) : v;
      if (REDUCED) { el2.textContent = fmt(target); return; }
      const t0 = performance.now(), dur = 950, from = target * 0.9;
      (function tick(t) {
        const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
        el2.textContent = fmt(from + (target - from) * e);
        if (p < 1) requestAnimationFrame(tick);
      })(t0);
    });
  }

  /* ────────────────────── series helpers ────────────────────── */
  function sliceRange(series, range) {
    const n = series.length;
    if (range === '1M') return series.slice(-23);
    if (range === '3M') return series.slice(-66);
    if (range === '1Y') return series.slice(-253);
    if (range === 'YTD') {
      const i = series.findIndex(p => p.d.getFullYear() === 2026);
      return series.slice(Math.max(0, i - 1));
    }
    return series;
  }
  function rebasePct(series) {
    const v0 = series[0].v;
    return series.map(p => ({ d: p.d, v: (p.v / v0 - 1) * 100 }));
  }
  function rebaseMoney(series, base) {
    const v0 = series[0].v;
    return series.map(p => ({ d: p.d, v: p.v / v0 * base }));
  }
  function retBetween(series, fromIdx) {
    return series[series.length - 1].v / series[fromIdx].v - 1;
  }
  function idxAtMonthEnd(series, y, m) { // last idx with date <= end of (y,m)
    const cut = new Date(y, m + 1, 1);
    let idx = 0;
    series.forEach((p, i) => { if (p.d < cut) idx = i; });
    return idx;
  }

  const PERF = {
    get fund() { return D.metrics(D.FUND, D.B6040); },
  };
  let METRICS = null; // computed once at boot

  /* ══════════════════════ VIEWS ══════════════════════ */
  const VIEWS = {
    overview: { title: 'Overview', render: renderOverview },
    performance: { title: 'Performance', render: renderPerformance },
    analytics: { title: 'Analytics', render: renderAnalytics },
    markets: { title: 'Markets', render: renderMarkets },
    insights: { title: 'Insights', render: renderInsights },
    settings: { title: 'Preferences', render: renderSettings },
  };
  const NAV_ORDER = ['overview', 'performance', 'analytics', 'markets', 'insights', 'settings'];
  const NAV_MOBILE = ['overview', 'performance', 'analytics', 'markets', 'insights'];

  function kpiCard(label, valueHTML, subHTML, sparkVals, sparkColor) {
    const sid = 'sp' + Math.random().toString(36).slice(2, 8);
    setTimeout(() => {
      const el2 = document.getElementById(sid);
      if (el2 && sparkVals) C.spark(el2, sparkVals, sparkColor || '#C6A468', { fill: true });
    }, 30);
    return `<div class="card kpi hoverable reveal">
      <div class="eyebrow">${label}</div>
      <div class="kpi-val num">${valueHTML}</div>
      <div class="kpi-sub">${subHTML}</div>
      ${sparkVals ? `<div class="kpi-spark" id="${sid}"></div>` : ''}
    </div>`;
  }

  /* ── OVERVIEW ── */
  function renderOverview(root) {
    const client = D.CLIENT, fund = D.FUND;
    const val = client[client.length - 1].v;
    const iJun = idxAtMonthEnd(fund, 2026, 5);
    const iDec = idxAtMonthEnd(fund, 2025, 11);
    const mtd = retBetween(fund, iJun);
    const ytd = retBetween(fund, iDec);
    const cum = fund[fund.length - 1].v / fund[0].v - 1;
    const dayBps = State.live.dayBps;
    const dayUsd = val * dayBps / 10000;
    const contrib = D.CONTRIBS.reduce((s, c) => s + c.amt, 0);
    const gain = val - contrib;
    const bench = BENCH[State.prefs.benchmark];

    root.innerHTML = `
      <div class="view-head reveal">
        <div class="eyebrow">CAPITAL ACCOUNT · ${State.user.legal.toUpperCase()}</div>
        <h2 class="serif view-title">Good ${new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'}${State.user.first ? ', ' + State.user.first : ''}.</h2>
        <p class="view-sub">Your capital account with Titan Meridian Capital, L.P. — performance shown net of all fees. U.S. markets are closed July 4 for Independence Day.</p>
      </div>

      <div class="grid g-kpi" id="kpi-row">
        ${kpiCard('Capital Account Value', `<span data-count="${val}" data-fmt="money">$0</span>`,
          `<span class="chg ${dayBps >= 0 ? 'up' : 'down'} ${cls(dayBps)}">${fmtPct(dayBps / 10000, 2)}</span><span>·</span><span class="${cls(dayUsd)} num">${(dayUsd >= 0 ? '+' : '−') + fmtMoney(Math.abs(dayUsd)).slice(1)} today</span>`,
          client.slice(-90).map(p => p.v), '#C6A468')}
        ${kpiCard('Month to Date', `<span data-count="${mtd}" data-fmt="pct" data-dp="2">0%</span>`,
          `<span>July 2026 · 3 sessions</span>`, fund.slice(iJun).map(p => p.v), '#8FA8C8')}
        ${kpiCard('Year to Date', `<span data-count="${ytd}" data-fmt="pct" data-dp="1">0%</span>`,
          `<span>vs ${bench.label} <b class="${cls(ytd - 0.041)} num">${fmtPct(retBetween(bench.series(), idxAtMonthEnd(bench.series(), 2025, 11)))}</b></span>`,
          fund.slice(iDec).map(p => p.v), '#6FBF97')}
        ${kpiCard('Since Inception', `<span data-count="${cum}" data-fmt="pct" data-dp="1">0%</span>`,
          `<span>Net gain <b class="pos num">+${fmtMoney(gain).slice(1)}</b></span>`, fund.filter((_, i) => i % 6 === 0).map(p => p.v), '#C6A468')}
      </div>

      <div class="grid g-2 mt">
        <div class="card reveal" id="ov-chart-card">
          <div class="card-head">
            <div><div class="card-title">Cumulative Performance</div>
            <div class="card-note">Titan Meridian Capital vs ${bench.label} · net of fees</div></div>
            <div class="seg" id="ov-range">
              ${['1M', '3M', 'YTD', '1Y', 'ALL'].map(r => `<button data-r="${r}" class="${State.perfRange === r ? 'active' : ''}">${r}</button>`).join('')}
            </div>
          </div>
          <div id="ov-chart"></div>
          <div class="chart-legend">
            <span class="lg"><i style="background:#C6A468"></i>TITAN MERIDIAN (NET)</span>
            <span class="lg"><i style="background:#5E7B9E"></i>${bench.label.toUpperCase()}</span>
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:16px;min-width:0">
          <div class="card reveal" id="regime-card">
            <div class="card-head"><div><div class="card-title">Regime Monitor</div>
            <div class="card-note">Proprietary four-state macro classifier</div></div></div>
            <div class="regime-grid">
              ${D.REGIMES.map(r => `<div class="regime-q ${r.active ? 'active' : ''}"><div class="rq-name">${r.name}</div><div class="rq-desc">${r.desc}</div></div>`).join('')}
            </div>
            <div class="regime-conf"><span>Signal confidence</span>
              <div class="hbar-track"><div class="hbar-fill" style="background:#C6A468" data-w="78%"></div></div><b class="num">78%</b>
            </div>
          </div>

          <div class="card reveal">
            <div class="card-head"><div><div class="card-title">Latest From the Desk</div></div>
              <a href="#/insights" style="font-size:10px;letter-spacing:.18em;font-weight:600">ALL UPDATES →</a></div>
            <div class="wire">
              ${D.NEWS.slice(0, 3).map(n => {
                const d = new Date(n.date + 'T12:00:00');
                return `<div class="wire-item"><span class="wire-date">${MON[d.getMonth()].toUpperCase()} ${('0' + d.getDate()).slice(-2)}</span>
                <span class="wire-txt" data-goto-news="${n.date}">${n.title}</span></div>`;
              }).join('')}
            </div>
          </div>
        </div>
      </div>

      <div class="grid g-2e mt">
        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Account Summary</div>
          <div class="card-note">Prepared from administrator records · unaudited</div></div></div>
          <div class="tbl-wrap"><table class="tbl" style="min-width:0">
            <tbody>
              <tr><td class="dim">Investor</td><td class="r">${State.user.legal}</td></tr>
              <tr><td class="dim">Share class</td><td class="r">Founders · Class A</td></tr>
              <tr><td class="dim">Net contributions</td><td class="r num">${fmtMoney(contrib)}</td></tr>
              <tr><td class="dim">Investment gain since inception</td><td class="r num pos">+${fmtMoney(gain).slice(1)}</td></tr>
              <tr><td class="dim">Current value</td><td class="r num" style="font-weight:700;color:var(--ivory-bright)">${fmtMoney(val)}</td></tr>
              <tr><td class="dim">Next dealing date</td><td class="r">01 Oct 2026 · 45 days’ notice</td></tr>
            </tbody>
          </table></div>
        </div>

        <div class="card reveal" id="notes-card">
          <div class="card-head"><div><div class="card-title">Family Office Notes</div>
          <div class="card-note">Private to this device — persists with Save</div></div></div>
          <textarea class="notes-ta" id="notes-ta" placeholder="Record questions for the IR team, allocation reminders, meeting notes…">${State.prefs.notes || ''}</textarea>
          <div class="notes-meta"><span id="notes-count"></span><span id="notes-saved"></span></div>
        </div>
      </div>`;

    drawOverviewChart();
    $('#ov-range').addEventListener('click', e => {
      const b = e.target.closest('button[data-r]');
      if (!b) return;
      State.perfRange = b.dataset.r;
      $$('#ov-range button').forEach(x => x.classList.toggle('active', x === b));
      drawOverviewChart();
    });
    const ta = $('#notes-ta');
    const nc = () => { $('#notes-count').textContent = ta.value.length ? ta.value.length + ' characters' : 'Empty'; };
    nc();
    $('#notes-saved').textContent = State.prefs.savedAt ? 'Last saved ' + new Date(State.prefs.savedAt).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'Not yet saved';
    ta.addEventListener('input', () => { State.prefs.notes = ta.value; nc(); setDirty(true); });
    root.addEventListener('click', e => {
      const w = e.target.closest('[data-goto-news]');
      if (w) location.hash = '#/insights';
    });
    setTimeout(() => $$('.hbar-fill', root).forEach(f => { f.style.width = f.dataset.w; }), 120);
  }

  function drawOverviewChart() {
    const el2 = $('#ov-chart'); if (!el2) return;
    const bench = BENCH[State.prefs.benchmark];
    const f = rebasePct(sliceRange(D.FUND, State.perfRange));
    const b = rebasePct(sliceRange(bench.series(), State.perfRange));
    C.lineChart(el2, {
      height: Math.min(340, Math.max(240, window.innerHeight * 0.32)),
      series: [
        { label: 'Titan Meridian', color: '#C6A468', points: f },
        { label: bench.label, color: '#5E7B9E', points: b, area: false },
      ],
      fmt: v => (v > 0 ? '+' : '') + v.toFixed(0) + '%',
      fmtTip: v => (v > 0 ? '+' : '') + v.toFixed(2) + '%',
    });
    registerRedraw(drawOverviewChart);
  }

  /* ── PERFORMANCE ── */
  function renderPerformance(root) {
    const m = METRICS;
    const bench = BENCH[State.prefs.benchmark];
    root.innerHTML = `
      <div class="view-head reveal">
        <div class="eyebrow">TRACK RECORD · SINCE JANUARY 2023</div>
        <h2 class="serif view-title">Performance</h2>
        <p class="view-sub">All figures net of management and incentive fees. Monthly data is derived from the administrator’s official NAV; the current month reflects the manager’s flash estimate.</p>
      </div>

      <div class="grid g-3">
        ${kpiCard('Annualized Return', `<span data-count="${m.cagr}" data-fmt="pct" data-dp="1">0</span>`, `<span>Cumulative ${fmtPct(m.total, 0)}</span>`)}
        ${kpiCard('Sharpe Ratio', `<span data-count="${m.sharpe}" data-fmt="num" data-dp="2">0</span>`, `<span>Sortino ${m.sortino.toFixed(2)} · rf 4.2%</span>`)}
        ${kpiCard('Max Drawdown', `<span data-count="${m.mdd}" data-fmt="pct" data-dp="1">0</span>`, `<span>Annualized vol ${fmtPctU(m.volAnn)}</span>`)}
      </div>

      <div class="card mt reveal">
        <div class="card-head">
          <div><div class="card-title">Growth of $1,000,000</div>
          <div class="card-note">Since inception vs ${bench.label} — change benchmark in Preferences</div></div>
        </div>
        <div id="perf-chart"></div>
        <div class="chart-legend">
          <span class="lg"><i style="background:#C6A468"></i>TITAN MERIDIAN (NET)</span>
          <span class="lg"><i style="background:#5E7B9E"></i>${bench.label.toUpperCase()}</span>
          <span class="lg"><i style="background:#4E5B70"></i>SOFR + 400</span>
        </div>
      </div>

      <div class="grid g-2 mt">
        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Monthly Returns</div>
          <div class="card-note">Net of fees · % — current month is a flash estimate</div></div></div>
          <div class="tbl-wrap">${monthlyMatrix(m.monthly)}</div>
        </div>
        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Risk Profile</div></div></div>
          <div class="tbl-wrap"><table class="tbl" style="min-width:0"><tbody>
            <tr><td class="dim">Best month</td><td class="r num pos">${fmtPct(m.best, 2)}</td></tr>
            <tr><td class="dim">Worst month</td><td class="r num neg">${fmtPct(m.worst, 2)}</td></tr>
            <tr><td class="dim">Positive months</td><td class="r num">${Math.round(m.hit * 100)}% of ${m.months}</td></tr>
            <tr><td class="dim">Beta vs ${bench.label}</td><td class="r num">${m.beta.toFixed(2)}</td></tr>
            <tr><td class="dim">Correlation to equities</td><td class="r num">0.31</td></tr>
            <tr><td class="dim">1-day VaR (99%)</td><td class="r num">0.9%</td></tr>
          </tbody></table></div>
          <div style="margin-top:18px">
            <div class="card-title" style="font-size:15px;margin-bottom:10px">Drawdown History</div>
            <div id="dd-chart"></div>
          </div>
        </div>
      </div>`;

    drawPerfCharts();
  }
  function drawPerfCharts() {
    const el2 = $('#perf-chart');
    if (el2) {
      const bench = BENCH[State.prefs.benchmark];
      C.lineChart(el2, {
        height: 330, padL: 74,
        series: [
          { label: 'Titan Meridian', color: '#C6A468', points: rebaseMoney(D.FUND, 1e6) },
          { label: bench.label, color: '#5E7B9E', points: rebaseMoney(bench.series(), 1e6), area: false },
          { label: 'SOFR + 400', color: '#4E5B70', points: rebaseMoney(D.CASHP, 1e6), area: false, dash: '4 5', width: 1.2 },
        ],
        fmt: v => '$' + (v / 1e6).toFixed(2) + 'M',
        fmtTip: v => fmtMoney(v),
      });
    }
    const dd = $('#dd-chart');
    if (dd) C.drawdownChart(dd, D.drawdownSeries(D.FUND).filter((_, i) => i % 2 === 0), { height: 170 });
    registerRedraw(drawPerfCharts);
  }
  function monthlyMatrix(monthly) {
    const years = [...new Set(monthly.map(x => x.y))];
    const map = {};
    monthly.forEach(x => { map[x.y + '-' + x.m] = x.r; });
    let html = '<table class="mret"><thead><tr><th style="text-align:left">YEAR</th>' +
      MON.map(mn => `<th>${mn[0]}</th>`).join('') + '<th>YTD</th></tr></thead><tbody>';
    years.forEach(y => {
      let ytd = 1; let row = `<tr><td class="yr">${y}</td>`;
      for (let mI = 0; mI < 12; mI++) {
        const r = map[y + '-' + mI];
        if (r == null) { row += '<td style="color:var(--muted-2)">·</td>'; continue; }
        ytd *= 1 + r;
        const a = Math.min(0.55, Math.abs(r) / 0.03 * 0.5 + 0.06);
        const bg = r >= 0 ? `rgba(46,125,91,${a})` : `rgba(160,74,63,${a})`;
        row += `<td style="background:${bg}">${(r * 100).toFixed(1)}</td>`;
      }
      row += `<td class="tot ${cls(ytd - 1)}">${fmtPct(ytd - 1, 1)}</td></tr>`;
      html += row;
    });
    return html + '</tbody></table>';
  }

  /* ── ANALYTICS ── */
  function renderAnalytics(root) {
    root.innerHTML = `
      <div class="view-head reveal">
        <div class="eyebrow">PORTFOLIO CONSTRUCTION · AS OF 03 JUL 2026</div>
        <h2 class="serif view-title">Analytics</h2>
        <p class="view-sub">Sleeve allocation, factor posture and risk decomposition for the master fund. Exposures are expressed as a percentage of net asset value.</p>
      </div>

      <div class="grid g-kpi">
        ${kpiCard('Gross Exposure', '<span data-count="2.85" data-fmt="num" data-dp="2">0</span>×', '<span>Notional / NAV</span>')}
        ${kpiCard('Net Exposure', '<span data-count="0.64" data-fmt="num" data-dp="2">0</span>×', '<span>Directional tilt</span>')}
        ${kpiCard('Margin to Equity', '<span data-count="14" data-fmt="num" data-dp="0">0</span>%', '<span>Futures & FX margin</span>')}
        ${kpiCard('Positions', '<span data-count="42" data-fmt="num" data-dp="0">0</span>', '<span>Across 6 sleeves · 14 markets</span>')}
      </div>

      <div class="grid g-2 mt">
        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Strategy Allocation</div>
          <div class="card-note">Risk capital by sleeve</div></div></div>
          <div class="alloc-grid" id="alloc-grid">
            <div id="alloc-donut"></div>
            <div>
              ${D.ALLOCATION.map(a => `
                <div class="alloc-row">
                  <span class="alloc-dot" style="background:${a.color}"></span>
                  <div><div class="alloc-name">${a.name}</div>
                  <div class="alloc-track"><div class="alloc-fill" style="background:${a.color}" data-w="${a.pct}%"></div></div></div>
                  <span class="alloc-pct">${a.pct}%</span>
                </div>`).join('')}
            </div>
          </div>
        </div>
        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Risk Contribution</div>
          <div class="card-note">Share of portfolio variance</div></div></div>
          ${D.RISK_CONTRIB.map(x => `
            <div class="hbar"><div class="hbar-top"><span class="hbar-name">${x.name}</span><span class="hbar-val num">${x.pct}%</span></div>
            <div class="hbar-track"><div class="hbar-fill" style="background:linear-gradient(90deg,#8E7548,#C6A468)" data-w="${x.pct * 2.4}%"></div></div></div>`).join('')}
          <div class="card-note" style="margin-top:14px">Diversification ratio 1.9× · 1-day VaR (99%) 0.9% of NAV · Expected shortfall 1.4%</div>
        </div>
      </div>

      <div class="grid g-2 mt">
        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Principal Exposures</div>
          <div class="card-note">Ten largest by margin consumption</div></div></div>
          <div class="tbl-wrap"><table class="tbl">
            <thead><tr><th>Instrument</th><th>Sleeve</th><th>Direction</th><th class="r">% NAV</th><th class="r">MTD (bps)</th></tr></thead>
            <tbody>${D.HOLDINGS.map(h => `
              <tr><td>${h.inst}</td><td class="dim">${h.sleeve}</td>
              <td><span class="pill ${h.dir === 'LONG' ? 'long' : 'short'}">${h.dir}</span></td>
              <td class="r num">${h.w.toFixed(1)}</td>
              <td class="r num ${cls(h.mtd)}">${h.mtd > 0 ? '+' : ''}${h.mtd}</td></tr>`).join('')}
            </tbody>
          </table></div>
        </div>
        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Factor Posture</div>
          <div class="card-note">Key macro sensitivities</div></div></div>
          ${D.FACTORS.map(f => `
            <div class="hbar"><div class="hbar-top"><span class="hbar-name">${f.name} <span style="color:var(--muted-2)">— ${f.desc}</span></span>
            <span class="hbar-val num ${f.dir > 0 ? 'pos' : 'neg'}">${f.val}</span></div>
            <div class="hbar-track"><div class="hbar-fill" style="background:${f.dir > 0 ? 'linear-gradient(90deg,#2E7D5B,#6FBF97)' : 'linear-gradient(90deg,#A04A3F,#C97B6F)'}" data-w="${f.pct}%"></div></div></div>`).join('')}
        </div>
      </div>`;

    C.donut($('#alloc-donut'), D.ALLOCATION, ['100%', 'RISK CAPITAL']);
    setTimeout(() => $$('.alloc-fill,.hbar-fill', root).forEach(f => { f.style.width = f.dataset.w; }), 150);
    registerRedraw(() => { const d = $('#alloc-donut'); if (d) C.donut(d, D.ALLOCATION, ['100%', 'RISK CAPITAL']); });
  }

  /* ── MARKETS / HEAT MAP ── */
  function heatColor(v, colMax) {
    const t = Math.min(1, Math.abs(v) / (colMax || 1));
    const from = [23, 37, 58];
    const to = v >= 0 ? [46, 125, 91] : [160, 74, 63];
    const mix = from.map((c, i) => Math.round(c + (to[i] - c) * (0.18 + 0.82 * t)));
    return `rgb(${mix[0]},${mix[1]},${mix[2]})`;
  }
  function renderMarkets(root) {
    const rows = State.hmMode === 'sectors' ? D.HM_SECTORS : D.HM_MACRO;
    root.innerHTML = `
      <div class="view-head reveal">
        <div class="eyebrow">MARKET INTELLIGENCE · ${State.asOf.replace('Data as of ', '').toUpperCase()}</div>
        <h2 class="serif view-title">Institutional Heat Map</h2>
        <p class="view-sub">Cross-asset and sector performance across horizons, colour-scaled within each column. Select any cell for detail. Data is indicative and delayed.</p>
      </div>

      <div class="idx-strip reveal" id="idx-strip">
        ${State.live.indices.map(x => `
          <div class="idx"><span class="idx-name">${x.name}</span>
          <span class="idx-px">${x.unit === '%' ? x.px.toFixed(2) + '%' : x.px.toLocaleString('en-US')}</span>
          <span class="idx-chg ${cls(x.chg)}">${x.chg > 0 ? '▲' : '▼'} ${Math.abs(x.chg).toFixed(2)}%</span></div>`).join('')}
      </div>

      <div class="card reveal" id="hm-card">
        <div class="card-head">
          <div><div class="card-title">Performance Matrix</div>
          <div class="card-note">${State.hmMode === 'sectors' ? 'S&P 500 GICS sectors' : 'Global cross-asset complex'} · total return %</div></div>
          <div class="seg" id="hm-mode">
            <button data-m="sectors" class="${State.hmMode === 'sectors' ? 'active' : ''}">EQUITY SECTORS</button>
            <button data-m="macro" class="${State.hmMode === 'macro' ? 'active' : ''}">GLOBAL MACRO</button>
          </div>
        </div>
        <div class="hm-scroll">
          <div class="hm" id="hm-grid" style="grid-template-columns:172px repeat(${D.HM_PERIODS.length},1fr)"></div>
        </div>
        <div class="hm-legend"><span>UNDERPERFORM</span><span class="bar"></span><span>OUTPERFORM</span><span style="margin-left:auto">SCALED PER HORIZON</span></div>
        <div class="hm-detail" id="hm-detail"></div>
      </div>

      <div class="grid g-2 mt">
        <div class="card reveal" id="wl-card">
          <div class="card-head"><div><div class="card-title">Watchlist</div>
          <div class="card-note">Yours — persists with Save</div></div></div>
          <div id="wl-rows"></div>
          <div class="wl-add">
            <select id="wl-select"></select>
            <button id="wl-add-btn">ADD</button>
          </div>
        </div>
        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Desk Colour</div>
          <div class="card-note">What the committee is watching</div></div></div>
          <div class="modal-body" style="font-size:13px">
            <p><b style="color:var(--ivory)">Rates.</b> Front-end pricing now embeds three cuts by January; the desk sees the risk skewed toward a faster path if shelter disinflation persists.</p>
            <p><b style="color:var(--ivory)">Dollar.</b> DXY’s −6.4% YTD trend remains the cleanest expression of the easing regime; positioning is short via EUR and JPY.</p>
            <p><b style="color:var(--ivory)">Gold.</b> +18.2% YTD. Still the portfolio’s primary regime hedge; we would add on any real-rate backup.</p>
            <p><b style="color:var(--ivory)">Energy.</b> Crude’s persistent weakness (−9.8% YTD) keeps headline inflation on the easing path — supportive, but we hold no directional position.</p>
          </div>
        </div>
      </div>`;

    drawHeatmap();
    renderWatchlist();
    $('#hm-mode').addEventListener('click', e => {
      const b = e.target.closest('button[data-m]'); if (!b) return;
      State.hmMode = b.dataset.m; State.hmSel = null;
      renderMarkets(root); bindReveals(root); runCountups(root);
    });
    $('#wl-add-btn').addEventListener('click', () => {
      const sel = $('#wl-select');
      if (!sel.value) return;
      State.prefs.watchlist.push(sel.value);
      setDirty(true); renderWatchlist();
      toast('Added to watchlist', sel.value + ' — remember to Save', null, I.check);
    });
  }
  function drawHeatmap() {
    const grid = $('#hm-grid'); if (!grid) return;
    const rows = State.hmMode === 'sectors' ? D.HM_SECTORS : D.HM_MACRO;
    const colMax = D.HM_PERIODS.map((_, ci) => Math.max(...rows.map(r => Math.abs(r.v[ci]))));
    let html = '<div class="hm-corner"></div>' + D.HM_PERIODS.map(p => `<div class="hm-collab">${p}</div>`).join('');
    rows.forEach((r, ri) => {
      html += `<div class="hm-rowlab"><b>${r.name}</b><span>${r.sub}</span></div>`;
      r.v.forEach((v, ci) => {
        const sel = State.hmSel && State.hmSel[0] === ri && State.hmSel[1] === ci;
        html += `<div class="hm-cell ${sel ? 'sel' : ''}" data-ri="${ri}" data-ci="${ci}" style="background:${heatColor(v, colMax[ci])}" title="${r.name} · ${D.HM_PERIODS[ci]}">${v > 0 ? '+' : ''}${v.toFixed(1)}</div>`;
      });
    });
    grid.innerHTML = html;
    grid.onclick = e => {
      const c = e.target.closest('.hm-cell'); if (!c) return;
      const ri = +c.dataset.ri, ci = +c.dataset.ci;
      State.hmSel = [ri, ci];
      $$('.hm-cell', grid).forEach(x => x.classList.remove('sel'));
      c.classList.add('sel');
      const row = rows[ri], v = row.v[ci], per = D.HM_PERIODS[ci];
      const det = $('#hm-detail');
      det.classList.add('show');
      det.innerHTML = `
        <div class="hm-detail-head">
          <span class="hm-detail-name">${row.name} <span style="color:var(--muted-2);font-size:12px">${row.sub}</span></span>
          <span class="num ${cls(v)}" style="font-size:18px;font-weight:600">${v > 0 ? '+' : ''}${v.toFixed(1)}% <span style="color:var(--muted-2);font-size:10px;letter-spacing:.16em">${per}</span></span>
        </div>
        <div style="height:56px;margin-top:12px" id="hm-spark"></div>
        <div class="card-note" style="margin-top:10px">${v >= 0 ? 'Outperforming' : 'Underperforming'} on the ${per} horizon ·
        ranks ${rows.filter(rr => rr.v[ci] > v).length + 1} of ${rows.length} in complex · horizons: ${row.v.map((x, i) => D.HM_PERIODS[i] + ' ' + (x > 0 ? '+' : '') + x.toFixed(1) + '%').join(' · ')}</div>`;
      const r = D.rng((ri + 3) * 991 + ci * 57);
      const vals = []; let acc = 100;
      for (let i = 0; i < 40; i++) { acc *= 1 + (v / 100 / 40) + D.gauss(r) * 0.004; vals.push(acc); }
      C.spark($('#hm-spark'), vals, v >= 0 ? '#6FBF97' : '#C97B6F', { fill: true });
    };
  }
  function renderWatchlist() {
    const wrap = $('#wl-rows'); if (!wrap) return;
    const list = State.prefs.watchlist.map(sym => State.live.watch.find(w => w.sym === sym)).filter(Boolean);
    wrap.innerHTML = list.length ? list.map(w => `
      <div class="wl-row"><div><div class="wl-sym">${w.sym}</div><div class="wl-name">${w.name}</div></div>
      <div class="wl-right"><div><div class="wl-px num">${w.px.toLocaleString('en-US')}</div>
      <div class="wl-px num ${cls(w.chg)}" style="font-size:11px">${w.chg > 0 ? '+' : ''}${w.chg.toFixed(2)}%</div></div>
      <button class="wl-del" data-sym="${w.sym}" title="Remove">×</button></div></div>`).join('')
      : '<div class="card-note" style="padding:14px 0">No instruments yet — add from the list below.</div>';
    const sel = $('#wl-select');
    const avail = D.WATCH_UNIVERSE.filter(w => !State.prefs.watchlist.includes(w.sym));
    sel.innerHTML = avail.length ? avail.map(w => `<option value="${w.sym}">${w.sym} — ${w.name}</option>`).join('') : '<option value="">Universe fully added</option>';
    $$('.wl-del', wrap).forEach(b => b.addEventListener('click', () => {
      State.prefs.watchlist = State.prefs.watchlist.filter(s => s !== b.dataset.sym);
      setDirty(true); renderWatchlist();
    }));
  }

  /* ── INSIGHTS ── */
  function renderInsights(root) {
    const cats = ['ALL', 'FIRM', 'MACRO', 'MARKETS', 'OPERATIONS'];
    const items = D.NEWS.filter(n => State.newsFilter === 'ALL' || n.cat === State.newsFilter);
    root.innerHTML = `
      <div class="view-head reveal">
        <div class="eyebrow">DESK NOTES · LETTERS · OPERATIONS</div>
        <h2 class="serif view-title">Insights &amp; Updates</h2>
        <p class="view-sub">Commentary from the investment committee, firm announcements, and your document centre. Select an item to expand it.</p>
      </div>

      <div class="grid g-2">
        <div class="card reveal">
          <div class="card-head">
            <div><div class="card-title">The Wire</div><div class="card-note">${items.length} item${items.length === 1 ? '' : 's'}</div></div>
            <div class="chips" id="news-chips">
              ${cats.map(c2 => `<button class="chip ${State.newsFilter === c2 ? 'active' : ''}" data-c="${c2}">${c2}</button>`).join('')}
            </div>
          </div>
          <div id="news-list">
            ${items.map((n, i) => {
              const d = new Date(n.date + 'T12:00:00');
              return `<div class="news-item reveal" data-i="${i}">
                <div class="news-date"><b>${('0' + d.getDate()).slice(-2)}</b><span>${MON[d.getMonth()]} ${String(d.getFullYear()).slice(2)}</span></div>
                <div class="news-body">
                  <div class="news-cat"><span class="pill ${n.cat === 'FIRM' ? 'gold' : ''}">${n.cat}</span></div>
                  <div class="news-title">${n.title}</div>
                  <div class="news-sum">${n.sum}</div>
                  <div class="news-full"><div class="news-full-inner">${n.full}</div></div>
                  <div class="news-more">READ MORE +</div>
                </div>
              </div>`;
            }).join('')}
          </div>
        </div>

        <div class="card reveal" style="align-self:start">
          <div class="card-head"><div><div class="card-title">Document Centre</div>
          <div class="card-note">Statements arrive via secure e-delivery</div></div></div>
          ${D.DOCS.map((doc, i) => `
            <div class="doc-row">
              <span class="doc-ic">${I.doc}</span>
              <div class="doc-meta"><div class="doc-name">${doc.name}</div><div class="doc-sub">${doc.sub}</div></div>
              <button class="doc-act" data-doc="${i}" ${doc.pending ? 'disabled' : ''}>${doc.pending ? 'IN PREPARATION' : 'VIEW'}</button>
            </div>`).join('')}
          <div class="card-note" style="margin-top:14px">Personalised capital statements are never stored in the browser. Contact <a href="mailto:ir@thetitanmarketsllc.com">investor relations</a> for certified copies.</div>
        </div>
      </div>`;

    $('#news-chips').addEventListener('click', e => {
      const b = e.target.closest('.chip'); if (!b) return;
      State.newsFilter = b.dataset.c;
      renderInsights(root); bindReveals(root);
    });
    $('#news-list').addEventListener('click', e => {
      const it = e.target.closest('.news-item'); if (!it) return;
      it.classList.toggle('open');
      $('.news-more', it).textContent = it.classList.contains('open') ? 'COLLAPSE −' : 'READ MORE +';
    });
    root.addEventListener('click', e => {
      const b = e.target.closest('.doc-act'); if (!b || b.disabled) return;
      openDocModal(D.DOCS[+b.dataset.doc]);
    });
  }
  function openDocModal(doc) {
    const isLetter = doc.name === D.LETTER.title;
    const body = isLetter
      ? D.LETTER.body.map(p => `<p>${p}</p>`).join('')
      : `<p>This document is available in full through secure e-delivery and the administrator’s LP portal.
         A watermarked copy can be issued to your advisors on request.</p>
         <h4>CONTENTS</h4><p>${doc.name} · ${doc.sub}</p>`;
    openModal(`
      <div class="eyebrow">DOCUMENT PREVIEW</div>
      <div class="modal-title">${doc.name}</div>
      <div class="modal-body">${isLetter ? `<p style="color:var(--muted-2);font-size:11px;letter-spacing:.12em">${D.LETTER.date} · CONFIDENTIAL — LP USE ONLY</p>` : ''}${body}</div>
      <div class="modal-actions">
        <button class="btn btn-solid" id="doc-dl" style="padding:11px 22px">DOWNLOAD COPY</button>
      </div>`);
    $('#doc-dl').addEventListener('click', () => {
      const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${doc.name}</title>
<style>body{font-family:Georgia,serif;max-width:680px;margin:60px auto;padding:0 24px;color:#1a1a1a;line-height:1.7}
h1{font-size:22px;letter-spacing:.04em}p.meta{color:#777;font-size:12px;letter-spacing:.1em}hr{border:none;border-top:1px solid #ddd;margin:24px 0}</style></head>
<body><h1>TITAN MERIDIAN CAPITAL, L.P.</h1><p class="meta">${doc.name.toUpperCase()} · CONFIDENTIAL — FOR LIMITED PARTNER USE ONLY</p><hr>
${isLetter ? D.LETTER.body.map(p => `<p>${p}</p>`).join('') : `<p>${doc.name} (${doc.sub}). The complete document is delivered through the administrator’s secure channel.</p>`}
<hr><p class="meta">© 2026 TITAN MARKETS LLC · CHICAGO, ILLINOIS</p></body></html>`;
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([html], { type: 'text/html' }));
      a.download = doc.name.replace(/[^a-z0-9]+/gi, '-').toLowerCase() + '.html';
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 4000);
      toast('Download started', doc.name, 'good', I.check);
    });
  }

  /* ── SETTINGS ── */
  function renderSettings(root) {
    const p = State.prefs, u = State.user;
    const row = (name, desc, control) => `
      <div class="set-row"><div class="set-info"><div class="set-name">${name}</div><div class="set-desc">${desc}</div></div>${control}</div>`;
    const sw = (id, on) => `<label class="switch"><input type="checkbox" id="${id}" ${on ? 'checked' : ''}><span class="track"></span></label>`;
    root.innerHTML = `
      <div class="view-head reveal">
        <div class="eyebrow">ACCOUNT · PREFERENCES · SECURITY</div>
        <h2 class="serif view-title">Preferences</h2>
        <p class="view-sub">Workspace settings are stored on this device when you Save. Account and entity changes are handled by investor relations.</p>
      </div>

      <div class="grid g-2e">
        <div class="card reveal">
          <div class="profile-head">
            <div class="profile-avatar">${u.initials}</div>
            <div><div class="profile-name">${u.name}</div>
            <div class="profile-sub">${u.legal} · ${u.role.toUpperCase()}</div></div>
          </div>
          <div class="tbl-wrap"><table class="tbl" style="min-width:0"><tbody>
            <tr><td class="dim">Email on file</td><td class="r">${u.email}</td></tr>
            <tr><td class="dim">Share class</td><td class="r">Founders · Class A</td></tr>
            <tr><td class="dim">Fee terms</td><td class="r">1.5% / 15% · HWM</td></tr>
            <tr><td class="dim">Liquidity</td><td class="r">Quarterly · 45 days’ notice</td></tr>
            <tr><td class="dim">Relationship manager</td><td class="r">A. Whitmore · <a href="mailto:ir@thetitanmarketsllc.com">ir@…</a></td></tr>
          </tbody></table></div>
        </div>

        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Workspace</div></div></div>
          ${row('Comparison benchmark', 'Used across performance charts',
            `<select id="set-bench">${Object.keys(BENCH).map(k => `<option value="${k}" ${p.benchmark === k ? 'selected' : ''}>${BENCH[k].label}</option>`).join('')}</select>`)}
          ${row('Performance display', 'Figures are always audited net; gross shown for reference', `<select id="set-ng"><option value="net" ${p.netGross === 'net' ? 'selected' : ''}>Net of fees</option><option value="gross" ${p.netGross === 'gross' ? 'selected' : ''}>Gross (indicative)</option></select>`)}
          ${row('Restart guided tour', 'Replay the walkthrough for new users', `<button class="doc-act" id="set-tour">START</button>`)}
          ${row('Reset demo workspace', 'Clears saved notes, watchlist and preferences on this device', `<button class="doc-act" id="set-reset" style="color:var(--neg);border-color:rgba(201,123,111,.4)">RESET</button>`)}
        </div>
      </div>

      <div class="grid g-2e mt">
        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Notifications</div><div class="card-note">Delivered to your email on file</div></div></div>
          ${row('Monthly flash estimates', 'Performance estimate on the second business day', sw('set-nperf', p.notifyPerf))}
          ${row('Macro desk notes', 'Regime monitor changes and positioning notes', sw('set-nmacro', p.notifyMacro))}
          ${row('Operational notices', 'Statements, documents, and administrative items', sw('set-nops', p.notifyOps))}
        </div>
        <div class="card reveal">
          <div class="card-head"><div><div class="card-title">Security &amp; Delivery</div></div></div>
          ${row('Two-factor authentication', 'Required for all limited partners', sw('set-2fa', p.twofa))}
          ${row('Secure e-delivery', 'Statements and K-1s via the document centre', sw('set-edel', p.edelivery))}
          ${row('Session', 'You are signed in' + (getSession() && getSession().remember ? ' · remembered on this device' : ' · this tab only'), `<button class="doc-act" id="set-logout">SIGN OUT</button>`)}
        </div>
      </div>

      <div class="card mt reveal" style="display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap">
        <div><div class="card-title">Save your workspace</div>
        <div class="card-note" id="set-saved-note">${p.savedAt ? 'Last saved ' + new Date(p.savedAt).toLocaleString() : 'Never saved on this device'}</div></div>
        <button class="btn btn-solid" id="set-save" style="padding:12px 28px">SAVE CHANGES</button>
      </div>`;

    $('#set-bench').addEventListener('change', e => { p.benchmark = e.target.value; setDirty(true); toast('Benchmark updated', BENCH[p.benchmark].label + ' now shown across charts'); });
    $('#set-ng').addEventListener('change', e => { p.netGross = e.target.value; setDirty(true); });
    [['set-nperf', 'notifyPerf'], ['set-nmacro', 'notifyMacro'], ['set-nops', 'notifyOps'], ['set-2fa', 'twofa'], ['set-edel', 'edelivery']]
      .forEach(([id, key]) => { const el2 = $('#' + id); el2 && el2.addEventListener('change', () => { p[key] = el2.checked; setDirty(true); }); });
    $('#set-tour').addEventListener('click', () => Tutorial.start());
    $('#set-save').addEventListener('click', () => { persistPrefs(); $('#set-saved-note').textContent = 'Last saved ' + new Date(p.savedAt).toLocaleString(); });
    $('#set-logout').addEventListener('click', logout);
    $('#set-reset').addEventListener('click', () => {
      const close = openModal(`
        <div class="eyebrow">CONFIRM</div><div class="modal-title">Reset demo workspace?</div>
        <div class="modal-body"><p>This clears saved notes, watchlist and preferences for <b>${u.name}</b> on this device. Fund data is unaffected.</p></div>
        <div class="modal-actions"><button class="btn btn-solid" id="rst-y" style="padding:11px 22px">RESET WORKSPACE</button>
        <button class="btn btn-ghost" id="rst-n" style="padding:11px 22px">CANCEL</button></div>`);
      $('#rst-y').addEventListener('click', () => {
        localStorage.removeItem(prefsKey()); loadPrefs(); setDirty(false); close();
        renderRoute(); toast('Workspace reset', 'Defaults restored', 'good', I.check);
      });
      $('#rst-n').addEventListener('click', close);
    });
  }

  /* ══════════════════════ ROUTER / SHELL ══════════════════════ */
  function registerRedraw(fn) {
    if (!State.chartRedraws.includes(fn)) State.chartRedraws.push(fn);
  }
  function currentRoute() {
    const h = (location.hash || '').replace('#/', '');
    return VIEWS[h] ? h : 'overview';
  }
  function renderRoute() {
    State.route = currentRoute();
    State.chartRedraws = [];
    const view = VIEWS[State.route];
    $('#crumb-view').textContent = view.title;
    $('#crumb-asof').textContent = State.asOf;
    $$('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.view === State.route));
    const root = $('#view');
    root.classList.remove('view-enter');
    void root.offsetWidth;
    root.classList.add('view-enter');
    view.render(root);
    bindReveals(root);
    runCountups(root);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }

  function buildNav() {
    const mk = key => {
      const b = document.createElement('button');
      b.className = 'nav-item'; b.dataset.view = key;
      b.innerHTML = I[key === 'settings' ? 'settings' : key] + `<span class="nav-lb">${VIEWS[key].title}</span>`;
      b.addEventListener('click', () => { location.hash = '#/' + key; });
      return b;
    };
    const side = $('#side-nav');
    NAV_ORDER.forEach(k => side.appendChild(mk(k)));
    const bottom = $('#bottomnav');
    NAV_MOBILE.forEach(k => bottom.appendChild(mk(k)));
  }

  /* update (market data refresh) */
  function doUpdate() {
    const btn = $('#btn-update');
    if (btn.classList.contains('working')) return;
    btn.classList.add('working');
    document.body.classList.add('updating');
    setTimeout(() => {
      State.live = makeLive(true);
      const now = new Date();
      State.asOf = 'Updated ' + fmtD(now) + ' · ' + now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) + ' local';
      btn.classList.remove('working');
      document.body.classList.remove('updating');
      renderRoute();
      toast('Market data updated', 'Indicative quotes refreshed · U.S. markets closed July 4', 'good', I.refresh);
    }, 900);
  }

  function logout() {
    clearSession();
    location.hash = '';
    location.reload();
  }

  /* ══════════════════════ TUTORIAL ══════════════════════ */
  const Tutorial = (() => {
    let idx = 0, active = false;
    const steps = () => [
      { title: 'Welcome to your portal', body: 'This is the private client portal of Titan Meridian Capital — a live view of your capital account, the fund’s positioning, and the desk’s thinking. This short tour shows you around.', center: true, tag: 'WELCOME' },
      { sel: () => visibleNav(), title: 'Navigate the portal', body: 'Six sections: Overview, Performance, Analytics, Markets, Insights and Preferences. On a phone these live in the bar at the bottom of the screen.', tag: 'NAVIGATION' },
      { sel: () => $('#kpi-row'), title: 'Your capital account', body: 'Headline value, month-to-date, year-to-date and since-inception performance — always net of fees, with today’s indicative move.', tag: 'OVERVIEW', route: 'overview' },
      { sel: () => $('#ov-chart-card'), title: 'Performance, in context', body: 'Cumulative returns against your chosen benchmark. Hover or touch for exact figures; switch horizons with the range control.', tag: 'CHARTS', route: 'overview' },
      { sel: () => $('#btn-update'), title: 'Update', body: 'Refreshes indicative market data and re-stamps the portal. Official numbers always come from the administrator’s NAV.', tag: 'DATA' },
      { sel: () => $('#btn-save'), title: 'Save', body: 'Notes, watchlist and preferences persist on this device when you Save. The bronze dot means you have unsaved changes. ⌘S works too.', tag: 'WORKSPACE' },
      { sel: () => visibleNavItem('markets'), title: 'Institutional heat map', body: 'Cross-asset and sector performance across six horizons, colour-scaled per column — plus your personal watchlist.', tag: 'MARKETS' },
      { sel: () => $('#user-chip'), title: 'You’re in control', body: 'Profile, preferences, security and this tutorial live under your name. That’s the tour — welcome to Titan Meridian.', tag: 'FINISH' },
    ];
    function visibleNav() {
      const bn = $('#bottomnav');
      return getComputedStyle(bn).display !== 'none' ? bn : $('#side-nav');
    }
    function visibleNavItem(key) {
      const items = $$(`.nav-item[data-view="${key}"]`);
      return items.find(x => x.offsetParent !== null) || items[0];
    }
    function render() {
      const root = $('#tutorial-root');
      const st = steps()[idx];
      if (st.route && State.route !== st.route) { location.hash = '#/' + st.route; }
      root.innerHTML = `
        <div class="tut-veil"></div>
        <div class="tut-hole" id="tut-hole"></div>
        <div class="tut-card" id="tut-card">
          <button class="tut-skip" id="tut-skip">SKIP ✕</button>
          <div class="tut-step">${st.tag} · ${idx + 1} / ${steps().length}</div>
          <div class="tut-title serif">${st.title}</div>
          <div class="tut-body">${st.body}</div>
          <div class="tut-nav">
            <div class="tut-dots">${steps().map((_, i) => `<span class="tut-dot ${i === idx ? 'on' : ''}"></span>`).join('')}</div>
            <div class="tut-btns">
              ${idx > 0 ? '<button class="tut-btn ghost" id="tut-back">BACK</button>' : ''}
              <button class="tut-btn primary" id="tut-next">${idx === steps().length - 1 ? 'FINISH' : 'NEXT'}</button>
            </div>
          </div>
        </div>`;
      $('#tut-skip').addEventListener('click', end);
      $('#tut-next').addEventListener('click', () => { if (idx === steps().length - 1) end(true); else { idx++; render(); } });
      const back = $('#tut-back');
      back && back.addEventListener('click', () => { idx--; render(); });
      setTimeout(position, st.route && State.route !== st.route ? 420 : 60);
    }
    function position() {
      if (!active) return;
      const st = steps()[idx];
      const hole = $('#tut-hole'), card = $('#tut-card');
      if (!hole || !card) return;
      const target = st.center ? null : (st.sel && st.sel());
      if (!target) {
        hole.style.cssText = 'width:0;height:0;left:50%;top:40%;box-shadow:0 0 0 9999px rgba(4,8,14,.82)';
        card.style.left = Math.max(16, (innerWidth - card.offsetWidth) / 2) + 'px';
        card.style.top = Math.max(20, innerHeight * 0.36 - card.offsetHeight / 2) + 'px';
        return;
      }
      target.scrollIntoView({ block: 'center', behavior: REDUCED ? 'auto' : 'smooth' });
      setTimeout(() => {
        const r = target.getBoundingClientRect(), pad = 9;
        hole.style.cssText = `left:${r.left - pad}px;top:${r.top - pad}px;width:${r.width + pad * 2}px;height:${r.height + pad * 2}px;`;
        const cw = card.offsetWidth, ch = card.offsetHeight;
        let top = r.bottom + pad + 14;
        if (top + ch > innerHeight - 16) top = r.top - pad - ch - 14;
        if (top < 16) top = Math.min(innerHeight - ch - 16, Math.max(16, r.top));
        let left = Math.max(16, Math.min(innerWidth - cw - 16, r.left));
        if (top >= r.top - pad && top <= r.bottom + pad) { // beside the target
          left = r.right + 20 + cw <= innerWidth - 16 ? r.right + 20 : Math.max(16, r.left - cw - 20);
        }
        card.style.left = left + 'px';
        card.style.top = top + 'px';
      }, REDUCED ? 30 : 360);
    }
    function start() {
      idx = 0; active = true;
      if (State.route !== 'overview') location.hash = '#/overview';
      setTimeout(render, 120);
    }
    function end(done) {
      active = false;
      $('#tutorial-root').innerHTML = '';
      State.prefs.tutorialDone = true;
      persistPrefs(true);
      if (done) toast('Tour complete', 'Replay it anytime from Preferences or the ? button', 'good', I.check);
    }
    window.addEventListener('resize', () => active && position());
    window.addEventListener('scroll', () => active && position(), true);
    return { start };
  })();

  function offerTutorial() {
    const close = openModal(`
      <div class="eyebrow">FIRST VISIT</div>
      <div class="modal-title">Welcome${State.user.demo ? ' to the demo environment' : ''}${State.user.first ? ', ' + State.user.first : ''}.</div>
      <div class="modal-body">
        <p>You’re viewing the client portal of <b style="color:var(--ivory)">Titan Meridian Capital, L.P.</b>${State.user.demo ? ' with a simulated family-office capital account — every figure here is illustrative.' : '.'}</p>
        <p>A ninety-second guided tour covers performance, analytics, the institutional heat map, and how to save your workspace.</p>
      </div>
      <div class="modal-actions">
        <button class="btn btn-solid" id="wel-tour" style="padding:12px 24px">TAKE THE TOUR</button>
        <button class="btn btn-ghost" id="wel-skip" style="padding:12px 24px">EXPLORE ON MY OWN</button>
      </div>`);
    $('#wel-tour').addEventListener('click', () => { close(); Tutorial.start(); });
    $('#wel-skip').addEventListener('click', () => {
      close(); State.prefs.tutorialDone = true; persistPrefs(true);
      toast('Tour available anytime', 'Use the ? button in the top bar', null, I.help);
    });
  }

  /* ══════════════════════ BOOT ══════════════════════ */
  function bootApp(user) {
    State.user = user;
    loadPrefs();
    State.live = makeLive(false);
    METRICS = D.metrics(D.FUND, D.B6040);

    $('#login').style.display = 'none';
    const app = $('#app');
    app.hidden = false;

    $('#user-name').textContent = user.name;
    $('#user-role').textContent = user.role;
    $('#user-avatar').textContent = user.initials;

    if (!$('#side-nav').children.length) buildNav();
    $('#update-ic').innerHTML = I.refresh;
    $('#save-ic').innerHTML = I.save;
    $('#help-ic').innerHTML = I.help;

    renderRoute();
    if (!State.prefs.tutorialDone) setTimeout(offerTutorial, 650);
  }

  function bindShell() {
    window.addEventListener('hashchange', () => { if (State.user) renderRoute(); });
    window.addEventListener('scroll', () => {
      const tb = $('#topbar'); tb && tb.classList.toggle('scrolled', scrollY > 8);
    }, { passive: true });
    let rT;
    window.addEventListener('resize', () => {
      clearTimeout(rT);
      rT = setTimeout(() => State.chartRedraws.forEach(fn => fn()), 240);
    });
    $('#btn-update').addEventListener('click', doUpdate);
    $('#btn-save').addEventListener('click', () => persistPrefs());
    $('#btn-help').addEventListener('click', () => Tutorial.start());
    $('#btn-logout-side').addEventListener('click', logout);
    document.addEventListener('keydown', e => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's' && State.user) {
        e.preventDefault(); persistPrefs();
      }
    });
    const chip = $('#user-chip'), menu = $('#user-menu');
    chip.addEventListener('click', e => { e.stopPropagation(); menu.hidden = !menu.hidden; });
    document.addEventListener('click', () => { menu.hidden = true; });
    menu.addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      menu.hidden = true;
      if (b.dataset.menu === 'settings') location.hash = '#/settings';
      if (b.dataset.menu === 'tour') Tutorial.start();
      if (b.dataset.menu === 'logout') logout();
    });
  }

  function bindLogin() {
    const form = $('#login-form'), errBox = $('#login-error');
    const email = $('#login-email'), pass = $('#login-pass');
    $('#pass-toggle').innerHTML = I.eye;
    $('#pass-toggle').addEventListener('click', () => {
      const show = pass.type === 'password';
      pass.type = show ? 'text' : 'password';
      $('#pass-toggle').innerHTML = show ? I.eyeOff : I.eye;
    });
    $('#btn-demo').addEventListener('click', () => {
      email.value = 'demo@titanmeridian.com';
      pass.value = 'meridian';
      form.requestSubmit();
    });
    form.addEventListener('submit', e => {
      e.preventDefault();
      errBox.hidden = true;
      const btn = $('#btn-signin');
      btn.classList.add('loading');
      setTimeout(() => {
        btn.classList.remove('loading');
        const acct = ACCOUNTS.find(a =>
          a.email.toLowerCase() === email.value.trim().toLowerCase() && a.pass === pass.value);
        if (!acct) {
          errBox.textContent = 'Credentials not recognised. Client access is provisioned by your relationship manager — or explore the demo account below.';
          errBox.hidden = false;
          const card = $('.login-card');
          card.classList.remove('shake'); void card.offsetWidth; card.classList.add('shake');
          return;
        }
        setSession(acct.id, $('#login-remember').checked);
        bootApp(acct);
      }, 650);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    bindLogin();
    bindShell();
    const sess = getSession();
    if (sess) {
      const acct = ACCOUNTS.find(a => a.id === sess.id);
      if (acct) bootApp(acct);
    }
  });
})();
