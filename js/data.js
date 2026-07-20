/* ════════════════════════════════════════════════════════════════
   TITAN MERIDIAN CAPITAL — data layer
   Deterministic simulated fund & market data (seeded RNG so every
   session sees the same track record). All figures are fictional.
   ════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* seeded PRNG (mulberry32) + gaussian */
  function rng(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function gauss(r) {
    let u = 0, v = 0;
    while (u === 0) u = r();
    while (v === 0) v = r();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  /* trading days (weekdays) from 2023-01-02 through 2026-07-03 */
  const START = new Date(2026, 6, 3); // reference "as of" date: Fri Jul 3 2026
  function tradingDays() {
    const days = [];
    const d = new Date(2023, 0, 2);
    while (d <= START) {
      const wd = d.getDay();
      if (wd !== 0 && wd !== 6) days.push(new Date(d));
      d.setDate(d.getDate() + 1);
    }
    return days;
  }
  const DAYS = tradingDays();

  /* regime segments: [fromYYYYMM, drift bp/day, vol bp/day] — shapes the narrative */
  const FUND_SEG = [
    [202301, 3.0, 36], [202304, 5.5, 33], [202401, 4.0, 34],
    [202404, -3.0, 40], [202408, 8.0, 36], [202501, 7.0, 31],
    [202507, 2.0, 30], [202511, 6.0, 33], [202602, -1.5, 40], [202604, 7.0, 31],
  ];
  const B6040_SEG = [
    [202301, 2.6, 52], [202404, -8.0, 66], [202408, 5.5, 52],
    [202501, 4.0, 46], [202602, -6.0, 62], [202604, 4.5, 48],
  ];
  const MACRO_SEG = [
    [202301, 2.2, 26], [202404, -2.5, 33], [202408, 3.4, 26], [202602, 0.5, 30], [202604, 3.0, 26],
  ];
  function segFor(segs, ym) {
    let cur = segs[0];
    for (const s of segs) { if (ym >= s[0]) cur = s; }
    return cur;
  }
  function genSeries(seed, segs, shared, corr) {
    const r = rng(seed);
    const out = [];
    let nav = 1000;
    DAYS.forEach((d, i) => {
      const ym = d.getFullYear() * 100 + (d.getMonth() + 1);
      const [, drift, vol] = segFor(segs, ym);
      const zOwn = gauss(r);
      const z = shared ? corr * shared[i] + Math.sqrt(1 - corr * corr) * zOwn : zOwn;
      nav *= 1 + (drift + vol * z) / 10000;
      out.push({ d, v: nav });
    });
    return out;
  }

  const sharedShocks = (() => { const r = rng(777); return DAYS.map(() => gauss(r)); })();

  /* nudge each calendar year onto a target return so the realized path
     matches the published track record regardless of random draws */
  function calibrateYears(series, targets) {
    const bounds = {}; // year -> [firstIdx, lastIdx]
    series.forEach((p, i) => {
      const y = p.d.getFullYear();
      if (!bounds[y]) bounds[y] = [i, i];
      bounds[y][1] = i;
    });
    const delta = {};
    Object.keys(bounds).forEach(y => {
      const [a, b] = bounds[y];
      const start = a === 0 ? series[0].v : series[a - 1].v;
      const realized = series[b].v / start - 1;
      const t = targets[y];
      delta[y] = t == null ? 0 : Math.pow((1 + t) / (1 + realized), 1 / (b - a + 1)) - 1;
    });
    const out = [{ d: series[0].d, v: series[0].v }];
    let nav = series[0].v;
    for (let i = 1; i < series.length; i++) {
      const r = series[i].v / series[i - 1].v - 1;
      nav *= (1 + r) * (1 + delta[series[i].d.getFullYear()]);
      out.push({ d: series[i].d, v: nav });
    }
    return out;
  }

  /* the fund's published monthly track record (%) — dailies are shaped to land
     exactly on these, so every view reconciles with the letters & flash notes */
  const FUND_MONTHLY = {
    2023: [1.2, -0.4, 1.8, 0.9, -0.6, 1.4, 0.8, -1.1, 1.6, 2.1, 1.9, 1.3],
    2024: [0.8, 1.1, 0.6, -1.8, -2.4, -1.6, 0.4, 1.9, 2.2, 1.4, 1.8, 1.2],
    2025: [1.6, 0.9, 1.7, 1.2, 0.8, 1.5, -0.7, 0.6, -0.9, 1.1, 2.4, 2.6],
    2026: [1.9, -1.4, 1.9, 1.6, 1.4, 0.83, 0.5],
  };
  function calibrateMonths(series, monthly) {
    const bounds = {}; // ym -> [firstIdx, lastIdx]
    series.forEach((p, i) => {
      const ym = p.d.getFullYear() * 100 + p.d.getMonth();
      if (!bounds[ym]) bounds[ym] = [i, i];
      bounds[ym][1] = i;
    });
    const delta = {};
    Object.keys(bounds).forEach(ym => {
      const [a, b] = bounds[ym];
      const y = Math.floor(ym / 100), m = ym % 100;
      const t = monthly[y] && monthly[y][m] != null ? monthly[y][m] / 100 : null;
      const start = a === 0 ? series[0].v : series[a - 1].v;
      const realized = series[b].v / start - 1;
      delta[ym] = t == null ? 0 : Math.pow((1 + t) / (1 + realized), 1 / (b - a + 1)) - 1;
    });
    const out = [{ d: series[0].d, v: series[0].v }];
    let nav = series[0].v;
    for (let i = 1; i < series.length; i++) {
      const r = series[i].v / series[i - 1].v - 1;
      const ym = series[i].d.getFullYear() * 100 + series[i].d.getMonth();
      nav *= (1 + r) * (1 + delta[ym]);
      out.push({ d: series[i].d, v: nav });
    }
    return out;
  }

  const FUND = calibrateMonths(genSeries(41, FUND_SEG, sharedShocks, 0.30), FUND_MONTHLY);
  const B6040 = calibrateYears(genSeries(97, B6040_SEG, sharedShocks, 0.55),
    { 2023: 0.124, 2024: -0.018, 2025: 0.082, 2026: 0.041 });
  const MACRO = calibrateYears(genSeries(53, MACRO_SEG, sharedShocks, 0.25),
    { 2023: 0.064, 2024: 0.021, 2025: 0.076, 2026: 0.032 });
  /* SOFR + 400 — smooth cash-plus benchmark following the easing path */
  const CASHP = (() => {
    const out = []; let nav = 1000;
    DAYS.forEach(d => {
      const y = d.getFullYear();
      const ann = y === 2023 ? 0.093 : y === 2024 ? 0.094 : y === 2025 ? 0.086 : 0.079;
      nav *= Math.pow(1 + ann, 1 / 252);
      out.push({ d, v: nav });
    });
    return out;
  })();

  /* client account: $18.5M subscribed at inception + $2.0M added Jul-2024 */
  const CONTRIBS = [
    { d: new Date(2023, 0, 2), amt: 18500000 },
    { d: new Date(2024, 6, 1), amt: 2000000 },
  ];
  function clientSeries() {
    let units = 0, ci = 0;
    const out = [];
    FUND.forEach(p => {
      while (ci < CONTRIBS.length && p.d >= CONTRIBS[ci].d) {
        units += CONTRIBS[ci].amt / p.v; ci++;
      }
      out.push({ d: p.d, v: units * p.v });
    });
    return out;
  }
  const CLIENT = clientSeries();

  /* monthly returns derived from the daily fund series */
  function monthlyReturns(series) {
    const out = []; // {y, m, r}
    let prev = series[0].v, curY = series[0].d.getFullYear(), curM = series[0].d.getMonth(), last = prev;
    series.forEach(p => {
      const y = p.d.getFullYear(), m = p.d.getMonth();
      if (y !== curY || m !== curM) {
        out.push({ y: curY, m: curM, r: last / prev - 1 });
        prev = last; curY = y; curM = m;
      }
      last = p.v;
    });
    out.push({ y: curY, m: curM, r: last / prev - 1 });
    return out;
  }

  function metrics(series, bench) {
    const mr = monthlyReturns(series);
    const n = mr.length;
    const mean = mr.reduce((s, x) => s + x.r, 0) / n;
    const sd = Math.sqrt(mr.reduce((s, x) => s + (x.r - mean) ** 2, 0) / (n - 1));
    const volAnn = sd * Math.sqrt(12);
    const total = series[series.length - 1].v / series[0].v - 1;
    const years = (series[series.length - 1].d - series[0].d) / 31557600000;
    const cagr = Math.pow(1 + total, 1 / years) - 1;
    const rf = 0.042;
    const sharpe = (cagr - rf) / volAnn;
    /* max drawdown from dailies */
    let peak = -Infinity, mdd = 0;
    series.forEach(p => { peak = Math.max(peak, p.v); mdd = Math.min(mdd, p.v / peak - 1); });
    /* beta vs benchmark monthlies */
    const br = monthlyReturns(bench);
    const bm = br.reduce((s, x) => s + x.r, 0) / br.length;
    let cov = 0, varb = 0;
    for (let i = 0; i < Math.min(n, br.length); i++) {
      cov += (mr[i].r - mean) * (br[i].r - bm); varb += (br[i].r - bm) ** 2;
    }
    const beta = cov / varb;
    const best = Math.max(...mr.map(x => x.r)), worst = Math.min(...mr.map(x => x.r));
    const hit = mr.filter(x => x.r > 0).length / n;
    const downMonths = mr.filter(x => x.r < 0);
    const downDev = Math.sqrt(downMonths.reduce((s, x) => s + x.r ** 2, 0) / Math.max(1, downMonths.length)) * Math.sqrt(12);
    const sortino = (cagr - rf) / downDev;
    return { total, cagr, volAnn, sharpe, sortino, mdd, beta, best, worst, hit, months: n, monthly: mr };
  }

  function drawdownSeries(series) {
    let peak = -Infinity;
    return series.map(p => { peak = Math.max(peak, p.v); return { d: p.d, v: p.v / peak - 1 }; });
  }

  /* ── static institutional data (hand-authored, plausible) ── */

  const ALLOCATION = [
    { name: 'Global Rates & Duration', pct: 28, color: '#C6A468' },
    { name: 'Equity Index & Sectors',  pct: 22, color: '#8FA8C8' },
    { name: 'Foreign Exchange',        pct: 14, color: '#6FBF97' },
    { name: 'Commodities',             pct: 12, color: '#C97B6F' },
    { name: 'Credit & Spread',         pct: 9,  color: '#9C8AC2' },
    { name: 'Volatility & Convexity',  pct: 6,  color: '#5E96A8' },
    { name: 'Cash & T-Bills',          pct: 9,  color: '#5E6B80' },
  ];

  const RISK_CONTRIB = [
    { name: 'Rates', pct: 34 }, { name: 'Equity', pct: 26 }, { name: 'FX', pct: 16 },
    { name: 'Commodities', pct: 13 }, { name: 'Credit', pct: 7 }, { name: 'Volatility', pct: 4 },
  ];

  const FACTORS = [
    { name: 'Portfolio Duration', val: '+2.8 yrs', pct: 62, dir: 1, desc: 'Long duration via US 10Y, Bunds short offsets' },
    { name: 'Equity Beta', val: '+0.31', pct: 41, dir: 1, desc: 'Net long via index futures & sector RV' },
    { name: 'USD Exposure', val: '−0.22', pct: 34, dir: -1, desc: 'Short dollar vs EUR, JPY baskets' },
    { name: 'Commodity Beta', val: '+0.18', pct: 27, dir: 1, desc: 'Gold & copper longs, energy neutral' },
    { name: 'Credit Spread Dur.', val: '+0.6 yrs', pct: 15, dir: 1, desc: 'IG carry, HY protection overlay' },
    { name: 'Net Vega', val: '+0.12', pct: 18, dir: 1, desc: 'Long convexity in rates & FX vol' },
  ];

  const HOLDINGS = [
    { inst: 'US 10Y Treasury Futures', sleeve: 'Rates', dir: 'LONG', w: 14.2, mtd: +42 },
    { inst: 'SOFR Dec-26 Futures', sleeve: 'Rates', dir: 'LONG', w: 9.8, mtd: +18 },
    { inst: 'S&P 500 E-mini Futures', sleeve: 'Equity', dir: 'LONG', w: 9.1, mtd: +31 },
    { inst: 'EUR/USD Forwards', sleeve: 'FX', dir: 'LONG', w: 7.4, mtd: +12 },
    { inst: 'Gold Futures (COMEX)', sleeve: 'Commodities', dir: 'LONG', w: 6.9, mtd: +24 },
    { inst: 'JPY/USD Forwards', sleeve: 'FX', dir: 'LONG', w: 5.6, mtd: -8 },
    { inst: 'German Bund Futures', sleeve: 'Rates', dir: 'SHORT', w: 5.2, mtd: +9 },
    { inst: 'Nikkei 225 Futures', sleeve: 'Equity', dir: 'LONG', w: 4.8, mtd: +15 },
    { inst: 'Copper Futures (LME)', sleeve: 'Commodities', dir: 'LONG', w: 4.1, mtd: -6 },
    { inst: 'CDX HY Protection', sleeve: 'Credit', dir: 'SHORT', w: 3.6, mtd: +4 },
  ];

  /* heat maps: rows × [1D, 1W, 1M, 3M, YTD, 1Y] % returns (as of Jul 3 2026) */
  const HM_PERIODS = ['1D', '1W', '1M', '3M', 'YTD', '1Y'];
  const HM_SECTORS = [
    { name: 'Information Technology', sub: 'XLK', v: [0.6, 1.4, 3.8, 7.2, 11.2, 21.4] },
    { name: 'Communication Services', sub: 'XLC', v: [0.4, 0.9, 2.6, 5.1, 8.9, 17.8] },
    { name: 'Financials', sub: 'XLF', v: [0.2, 0.7, 1.9, 3.4, 6.4, 14.2] },
    { name: 'Industrials', sub: 'XLI', v: [0.3, 1.1, 2.2, 4.6, 7.8, 12.6] },
    { name: 'Consumer Discretionary', sub: 'XLY', v: [0.5, 0.4, 1.6, 3.9, 5.6, 9.8] },
    { name: 'Materials', sub: 'XLB', v: [-0.2, 0.6, 1.1, 2.8, 4.2, 6.1] },
    { name: 'Utilities', sub: 'XLU', v: [0.3, 1.2, 2.9, 5.8, 9.4, 15.3] },
    { name: 'Consumer Staples', sub: 'XLP', v: [0.1, 0.3, 0.8, 1.6, 2.1, 4.7] },
    { name: 'Real Estate', sub: 'XLRE', v: [0.4, 1.0, 2.4, 4.2, 3.0, 5.2] },
    { name: 'Health Care', sub: 'XLV', v: [-0.3, -0.8, -1.2, 0.6, -1.8, -3.4] },
    { name: 'Energy', sub: 'XLE', v: [-0.6, -1.9, -3.2, -4.8, -3.1, -8.6] },
  ];
  const HM_MACRO = [
    { name: 'US Equities', sub: 'S&P 500', v: [0.4, 1.1, 2.9, 5.6, 8.1, 16.2] },
    { name: 'European Equities', sub: 'STOXX 600', v: [0.3, 0.8, 1.8, 3.2, 9.6, 13.1] },
    { name: 'Japanese Equities', sub: 'NIKKEI 225', v: [0.7, 1.6, 3.4, 6.8, 12.4, 19.7] },
    { name: 'Emerging Markets', sub: 'MSCI EM', v: [0.5, 1.3, 2.6, 4.9, 10.8, 14.6] },
    { name: 'US 10Y Treasury', sub: 'PRICE', v: [0.2, 0.6, 1.4, 2.7, 4.6, 7.2] },
    { name: 'German Bunds', sub: 'PRICE', v: [0.1, 0.2, 0.4, 0.9, 1.8, 2.4] },
    { name: 'US Dollar', sub: 'DXY', v: [-0.2, -0.7, -1.6, -3.1, -6.4, -9.2] },
    { name: 'Gold', sub: 'COMEX', v: [0.3, 1.8, 4.1, 8.6, 18.2, 27.4] },
    { name: 'Copper', sub: 'LME', v: [-0.4, 0.9, 2.2, 5.4, 11.6, 15.8] },
    { name: 'Crude Oil', sub: 'WTI', v: [-0.8, -2.4, -4.6, -7.2, -9.8, -14.2] },
    { name: 'IG Credit', sub: 'CDX IG', v: [0.1, 0.2, 0.6, 1.3, 2.8, 5.1] },
    { name: 'High Yield', sub: 'CDX HY', v: [0.1, 0.4, 0.9, 2.1, 4.2, 8.4] },
  ];

  const INDICES = [
    { name: 'S&P 500', px: 6412.58, chg: +0.42 },
    { name: 'NASDAQ 100', px: 23118.44, chg: +0.61 },
    { name: 'DOW JONES', px: 46284.19, chg: +0.28 },
    { name: 'US 10Y YIELD', px: 3.62, chg: -0.04, unit: '%' },
    { name: 'DXY', px: 96.84, chg: -0.22 },
    { name: 'GOLD', px: 3845.20, chg: +0.31, unit: '$' },
    { name: 'WTI CRUDE', px: 71.42, chg: -0.83, unit: '$' },
    { name: 'EUR/USD', px: 1.1920, chg: +0.18 },
    { name: 'VIX', px: 13.86, chg: -2.10 },
  ];

  const WATCH_UNIVERSE = [
    { sym: 'SPX', name: 'S&P 500 Index', px: 6412.58, chg: +0.42 },
    { sym: 'NDX', name: 'NASDAQ 100', px: 23118.44, chg: +0.61 },
    { sym: 'US10Y', name: 'US 10Y Yield', px: 3.62, chg: -1.09 },
    { sym: 'GC', name: 'Gold Futures', px: 3845.20, chg: +0.31 },
    { sym: 'CL', name: 'WTI Crude Oil', px: 71.42, chg: -0.83 },
    { sym: 'EURUSD', name: 'Euro / US Dollar', px: 1.1920, chg: +0.18 },
    { sym: 'USDJPY', name: 'US Dollar / Yen', px: 138.42, chg: -0.36 },
    { sym: 'HG', name: 'Copper Futures', px: 5.12, chg: -0.41 },
    { sym: 'DXY', name: 'US Dollar Index', px: 96.84, chg: -0.22 },
    { sym: 'VIX', name: 'CBOE Volatility', px: 13.86, chg: -2.10 },
    { sym: 'BTC', name: 'Bitcoin', px: 118240, chg: +1.24 },
    { sym: 'NKY', name: 'Nikkei 225', px: 48312, chg: +0.74 },
  ];

  const NEWS = [
    { date: '2026-07-03', cat: 'MARKETS', title: 'U.S. markets close early ahead of Independence Day',
      sum: 'Equity and bond markets closed at 1:00 PM ET Friday; all U.S. markets are closed Saturday, July 4. Portfolio data reflects the July 3 early close.',
      full: 'Liquidity was thin into the holiday weekend with volumes roughly 40% below the 20-day average. The desk carried risk unchanged into the close. Systematic signals are refreshed nightly; the next full trading session is Monday, July 6. Overnight risk is monitored by our 24-hour coverage rotation.' },
    { date: '2026-07-02', cat: 'FIRM', title: 'June flash estimate: +0.83% net; first half closes at +6.9%',
      sum: 'Preliminary June performance is estimated at +0.83% net of all fees, bringing YTD to approximately +6.9%. Final figures will be released with the administrator’s NAV.',
      full: 'Gains were led by the rates sleeve as the front end repriced toward three cuts by year-end, with additional contribution from long gold and short dollar expressions. Equity RV detracted modestly. The administrator’s final NAV pack and capital account statements are expected on or about July 18.' },
    { date: '2026-07-01', cat: 'MACRO', title: 'Regime monitor: disinflation intact, easing cycle broadening',
      sum: 'Our composite regime score continues to map to "Disinflation → Easing." Growth nowcasts are stable while core inflation momentum decelerates across DM.',
      full: 'The framework’s four-state classifier has held in the easing quadrant for nine consecutive weeks — the longest stretch since inception. Historically this state has favored duration, gold, and selective EM FX carry, which is reflected in current positioning. The primary invalidation risk is a re-acceleration in shelter and services inflation; we monitor trimmed-mean momentum weekly.' },
    { date: '2026-06-27', cat: 'OPERATIONS', title: 'Q2 statements and capital account summaries: e-delivery July 18',
      sum: 'Quarterly capital account statements, the administrator’s NAV pack, and the Q2 letter will be delivered via the portal document center on July 18.',
      full: 'Statements are prepared by our independent administrator and reviewed prior to release. LPs enrolled in e-delivery will receive a secure notification; hard-copy delivery remains available on request to investor relations.' },
    { date: '2026-06-24', cat: 'MACRO', title: 'Positioning note: adding duration into the supply concession',
      sum: 'We used the pre-refunding concession to extend US duration, funded partly by closing the remaining short in Bunds.',
      full: 'The rates sleeve added roughly 0.6 years of duration between 3.70% and 3.78% on tens. Cross-market, the US–Germany spread has compressed toward our 18-month target, reducing the marginal carry in the Bund short. Convexity remains long via receiver structures expiring Q4.' },
    { date: '2026-06-18', cat: 'MARKETS', title: 'FOMC recap: dots shift dovish; curve steepeners extended',
      sum: 'The June SEP moved the median 2026 dot 25bp lower. We extended 2s10s steepeners on the announcement.',
      full: 'Chair guidance emphasized that policy is "meaningfully restrictive" relative to a falling neutral estimate. Front-end pricing now embeds three cuts by January. The fund’s steepener book was extended by 15% of its risk budget at an average entry of −18bp on 2s10s.' },
    { date: '2026-06-10', cat: 'FIRM', title: 'Capacity review complete: strategy remains comfortably open',
      sum: 'Following June 1 subscriptions, the GP completed its scheduled capacity review. The strategy remains well inside the soft-close thresholds set out in the LPA.',
      full: 'Capacity discipline is a structural commitment of the strategy. The investment committee’s standing analysis indicates utilization of roughly 55% across the most liquidity-constrained sleeves (LME metals, JGB basis). Existing LPs retain priority allocation rights under the side letter framework.' },
    { date: '2026-06-05', cat: 'OPERATIONS', title: 'Updated Form ADV Part 2A available in the document center',
      sum: 'The annual amendment to Form ADV Part 2A has been filed and is available for download. No material changes to strategy, fees, or personnel.',
      full: 'Routine updates cover AUM figures, an expanded conflicts disclosure related to the affiliated managed-account platform, and refreshed service-provider listings. Questions may be directed to compliance@thetitanmarketsllc.com.' },
    { date: '2026-05-30', cat: 'MACRO', title: 'Mid-year outlook: late-cycle disinflation, easing ahead',
      sum: 'Our H2 outlook: DM disinflation persists, the easing cycle broadens, and the dollar’s structural downtrend continues — with fatter left tails than markets price.',
      full: 'The full 18-page outlook is available in the document center. Key calls: long duration into Q3, gold as the primary regime hedge, EM local-currency carry in selected markets, and maintained protection against a services-inflation re-acceleration, which remains the principal threat to the easing path.' },
  ];

  const DOCS = [
    { name: 'Q2 2026 Quarterly Letter', sub: 'Expected July 15, 2026', date: null, pending: true },
    { name: 'Q1 2026 Quarterly Letter', sub: 'Published April 15, 2026 · PDF · 14 pp', date: '2026-04-15' },
    { name: 'H2 2026 Macro Outlook', sub: 'Published May 30, 2026 · PDF · 18 pp', date: '2026-05-30' },
    { name: '2025 Annual Report & Audited Financials', sub: 'Published March 2, 2026 · PDF · 46 pp', date: '2026-03-02' },
    { name: 'Form ADV Part 2A (2026 Annual Amendment)', sub: 'Filed June 5, 2026 · PDF · 32 pp', date: '2026-06-05' },
    { name: 'Due Diligence Questionnaire (DDQ)', sub: 'Updated May 12, 2026 · PDF · 28 pp', date: '2026-05-12' },
    { name: 'Subscription Documents & LPA', sub: 'Current as of January 2026 · PDF', date: '2026-01-05' },
  ];

  /* letter body used for the document preview modal */
  const LETTER = {
    title: 'Q1 2026 Quarterly Letter',
    date: 'April 15, 2026',
    body: [
      'Dear Limited Partners,',
      'Titan Meridian Capital returned +2.4% net for the first quarter, against +1.1% for the global 60/40 composite. Since inception the fund has compounded at a double-digit annual rate with roughly one-third of equity-market volatility and a maximum drawdown of under 7%.',
      'The quarter rewarded patience more than prediction. February’s volatility episode — a 6% equity drawdown compressed into nine sessions — was the first genuine test of the easing-regime thesis this year. Our framework treated it as noise within an intact regime rather than a state change, and the discipline of that distinction was worth roughly 180 basis points of avoided whipsaw.',
      'Positioning enters Q2 with long US duration, a structurally short dollar, long gold as the primary regime hedge, and a modest net-long equity stance concentrated in rate-sensitive sectors.',
      'We remain, as always, invested alongside you.',
      '— The Investment Committee, Titan Meridian Capital',
    ],
  };

  const REGIMES = [
    { name: 'Reflation', desc: 'Growth ↑ · Inflation ↑ — commodities, cyclicals, short duration' },
    { name: 'Overheat', desc: 'Growth ↓ · Inflation ↑ — real assets, defensives, vol' },
    { name: 'Disinflation · Easing', desc: 'Growth stable · Inflation ↓ — duration, gold, carry', active: true },
    { name: 'Contraction', desc: 'Growth ↓ · Inflation ↓ — bonds, quality, USD' },
  ];

  window.TMC_DATA = {
    ASOF: START,
    DAYS, FUND, B6040, MACRO, CASHP, CLIENT, CONTRIBS,
    monthlyReturns, metrics, drawdownSeries,
    ALLOCATION, RISK_CONTRIB, FACTORS, HOLDINGS,
    HM_PERIODS, HM_SECTORS, HM_MACRO, INDICES, WATCH_UNIVERSE,
    NEWS, DOCS, LETTER, REGIMES,
    rng, gauss,
  };
})();
